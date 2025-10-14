import asyncio
import base64
import json
import logging
import random
import urllib.parse
import urllib.request
from io import BytesIO
from typing import Optional

import aiohttp
import websocket  # NOTE: websocket-client (https://github.com/websocket-client/websocket-client)
from cerebraui.env import SRC_LOG_LEVELS
from pydantic import BaseModel

log = logging.getLogger(__name__)
log.setLevel(SRC_LOG_LEVELS["COMFYUI"])

default_headers = {"User-Agent": "Mozilla/5.0"}


def queue_prompt(prompt, client_id, base_url, api_key):
    log.info("queue_prompt")
    p = {"prompt": prompt, "client_id": client_id}
    data = json.dumps(p).encode("utf-8")
    log.debug(f"queue_prompt data: {data}")
    try:
        req = urllib.request.Request(
            f"{base_url}/prompt",
            data=data,
            headers={**default_headers, "Authorization": f"Bearer {api_key}"},
        )
        response = urllib.request.urlopen(req).read()
        return json.loads(response)
    except Exception as e:
        log.exception(f"Error while queuing prompt: {e}")
        raise e


def get_image(filename, subfolder, folder_type, base_url, api_key):
    log.info("get_image")
    data = {"filename": filename, "subfolder": subfolder, "type": folder_type}
    url_values = urllib.parse.urlencode(data)
    req = urllib.request.Request(
        f"{base_url}/view?{url_values}",
        headers={**default_headers, "Authorization": f"Bearer {api_key}"},
    )
    with urllib.request.urlopen(req) as response:
        return response.read()


def get_image_url(filename, subfolder, folder_type, base_url):
    log.info("get_image")
    data = {"filename": filename, "subfolder": subfolder, "type": folder_type}
    url_values = urllib.parse.urlencode(data)
    return f"{base_url}/view?{url_values}"


def get_history(prompt_id, base_url, api_key):
    log.info("get_history")

    req = urllib.request.Request(
        f"{base_url}/history/{prompt_id}",
        headers={**default_headers, "Authorization": f"Bearer {api_key}"},
    )
    with urllib.request.urlopen(req) as response:
        return json.loads(response.read())


def get_images(ws, prompt, client_id, base_url, api_key):
    prompt_id = queue_prompt(prompt, client_id, base_url, api_key)["prompt_id"]
    output_images = []
    while True:
        out = ws.recv()
        if isinstance(out, str):
            message = json.loads(out)
            if message["type"] == "executing":
                data = message["data"]
                if data["node"] is None and data["prompt_id"] == prompt_id:
                    break  # Execution is done
        else:
            continue  # previews are binary data

    history = get_history(prompt_id, base_url, api_key)[prompt_id]
    for o in history["outputs"]:
        for node_id in history["outputs"]:
            node_output = history["outputs"][node_id]
            if "images" in node_output:
                for image in node_output["images"]:
                    url = get_image_url(
                        image["filename"], image["subfolder"], image["type"], base_url
                    )
                    output_images.append({"url": url})
    return {"data": output_images}


class ComfyUINodeInput(BaseModel):
    type: Optional[str] = None
    node_ids: list[str] = []
    key: Optional[str] = "text"
    value: Optional[str] = None


class ComfyUIWorkflow(BaseModel):
    workflow: str
    nodes: list[ComfyUINodeInput]


class ComfyUIGenerateImageForm(BaseModel):
    workflow: ComfyUIWorkflow

    prompt: str
    negative_prompt: Optional[str] = None
    width: int
    height: int
    n: int = 1

    steps: Optional[int] = None
    seed: Optional[int] = None

    # Image-to-image fields
    image: Optional[str] = None  # base64 or URL or file path
    strength: Optional[float] = None


async def upload_image_to_comfyui(image_data: str, base_url: str, api_key: str):
    """Upload image to ComfyUI server and return the filename"""
    log.info("upload_image_to_comfyui")

    # Parse image data
    img_bytes = None
    if image_data.startswith("data:image"):
        # base64 format: data:image/png;base64,iVBORw0KGg...
        header, encoded = image_data.split(",", 1)
        img_bytes = base64.b64decode(encoded)
    elif image_data.startswith("http://") or image_data.startswith("https://"):
        # URL format - download the image
        headers = {}
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"

        async with aiohttp.ClientSession() as session:
            async with session.get(image_data, headers=headers) as resp:
                if resp.status == 200:
                    img_bytes = await resp.read()
                else:
                    raise Exception(f"Failed to download image from URL: {resp.status}")
    else:
        # Assume it's already a filename or file path
        # In this case, we might need to read from the local file system
        # For now, we'll treat it as base64 without header
        try:
            img_bytes = base64.b64decode(image_data)
        except Exception as e:
            raise Exception(f"Unsupported image format or invalid data: {e}")

    if not img_bytes:
        raise Exception("Failed to process image data")

    # Upload to ComfyUI
    form = aiohttp.FormData()
    form.add_field('image', BytesIO(img_bytes), filename='input_image.png', content_type='image/png')

    headers = {**default_headers}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"

    async with aiohttp.ClientSession() as session:
        async with session.post(f"{base_url}/upload/image", data=form, headers=headers) as resp:
            if resp.status == 200:
                result = await resp.json()
                log.info(f"Image uploaded successfully: {result}")
                return result["name"]  # Return the uploaded filename
            else:
                error_text = await resp.text()
                raise Exception(f"Failed to upload image to ComfyUI: {resp.status} - {error_text}")


async def comfyui_generate_image(
    model: str, payload: ComfyUIGenerateImageForm, client_id, base_url, api_key
):
    ws_url = base_url.replace("http://", "ws://").replace("https://", "wss://")
    workflow = json.loads(payload.workflow.workflow)

    # If image is provided, upload it to ComfyUI first
    uploaded_image_name = None
    if payload.image:
        uploaded_image_name = await upload_image_to_comfyui(
            payload.image, base_url, api_key
        )
        log.info(f"Uploaded image: {uploaded_image_name}")

    for node in payload.workflow.nodes:
        if node.type:
            if node.type == "model":
                for node_id in node.node_ids:
                    workflow[node_id]["inputs"][node.key] = model
            elif node.type == "prompt":
                for node_id in node.node_ids:
                    workflow[node_id]["inputs"][
                        node.key if node.key else "text"
                    ] = payload.prompt
            elif node.type == "negative_prompt":
                for node_id in node.node_ids:
                    workflow[node_id]["inputs"][
                        node.key if node.key else "text"
                    ] = payload.negative_prompt
            elif node.type == "width":
                for node_id in node.node_ids:
                    workflow[node_id]["inputs"][
                        node.key if node.key else "width"
                    ] = payload.width
            elif node.type == "height":
                for node_id in node.node_ids:
                    workflow[node_id]["inputs"][
                        node.key if node.key else "height"
                    ] = payload.height
            elif node.type == "n":
                for node_id in node.node_ids:
                    workflow[node_id]["inputs"][
                        node.key if node.key else "batch_size"
                    ] = payload.n
            elif node.type == "steps":
                for node_id in node.node_ids:
                    workflow[node_id]["inputs"][
                        node.key if node.key else "steps"
                    ] = payload.steps
            elif node.type == "seed":
                seed = (
                    payload.seed
                    if payload.seed
                    else random.randint(0, 1125899906842624)
                )
                for node_id in node.node_ids:
                    workflow[node_id]["inputs"][node.key] = seed
            elif node.type == "image":
                # For image-to-image: set the uploaded image filename
                if uploaded_image_name:
                    for node_id in node.node_ids:
                        workflow[node_id]["inputs"][
                            node.key if node.key else "image"
                        ] = uploaded_image_name
            elif node.type == "strength":
                # For image-to-image: set the strength parameter
                if payload.strength is not None:
                    for node_id in node.node_ids:
                        workflow[node_id]["inputs"][
                            node.key if node.key else "strength"
                        ] = payload.strength
        else:
            for node_id in node.node_ids:
                workflow[node_id]["inputs"][node.key] = node.value

    try:
        ws = websocket.WebSocket()
        headers = {"Authorization": f"Bearer {api_key}"}
        ws.connect(f"{ws_url}/ws?clientId={client_id}", header=headers)
        log.info("WebSocket connection established.")
    except Exception as e:
        log.exception(f"Failed to connect to WebSocket server: {e}")
        return None

    try:
        log.info("Sending workflow to WebSocket server.")
        log.info(f"Workflow: {workflow}")
        images = await asyncio.to_thread(
            get_images, ws, workflow, client_id, base_url, api_key
        )
    except Exception as e:
        log.exception(f"Error while receiving images: {e}")
        images = None

    ws.close()

    return images

# backend/cerebraui/routers/deepresearch.py
import asyncio
import json
import logging
import os
from typing import Any, AsyncGenerator, Dict, Optional
from uuid import uuid4

import httpx
from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse
# from cerebraui.utils.auth import get_verified_user  # TODO: enable when authentication is required

# 统一前缀：/ai/deepresearch
router = APIRouter(prefix="/ai/deepresearch", tags=["deepresearch"])

logger = logging.getLogger(__name__)

LANGFLOW_BASE_URL = os.getenv("DEEPRESEARCH_LANGFLOW_BASE_URL", os.getenv("LANGFLOW_BASE_URL", "http://langflow:7860"))
LANGFLOW_FLOW_ID = os.getenv("DEEPRESEARCH_LANGFLOW_FLOW_ID", os.getenv("LANGFLOW_FLOW_ID"))
LANGFLOW_API_KEY = os.getenv("DEEPRESEARCH_LANGFLOW_API_KEY", os.getenv("LANGFLOW_API_KEY"))
LANGFLOW_TIMEOUT = float(os.getenv("DEEPRESEARCH_LANGFLOW_TIMEOUT", "300"))

_tweaks_env = os.getenv("DEEPRESEARCH_LANGFLOW_TWEAKS", "{}")
try:
    LANGFLOW_TWEAKS = json.loads(_tweaks_env) if _tweaks_env else {}
except json.JSONDecodeError:
    logger.warning("Invalid JSON in DEEPRESEARCH_LANGFLOW_TWEAKS – defaulting to empty config")
    LANGFLOW_TWEAKS = {}


class LangflowConfigurationError(RuntimeError):
    """Raised when Langflow integration is not configured."""


def _encode_sse(payload: Dict[str, Any]) -> str:
    return f"data: {json.dumps(payload, ensure_ascii=False)}\n\n"

# —— 你后面把这里替换为 Langflow 的真实流 —— #
async def _mock_stream(query: str) -> AsyncGenerator[str, None]:
    """演示用：按阶段逐段输出（SSE 要求每条以空行结尾）"""
    stages = [
        ("PLAN",   "breaking down the problem…"),
        ("GATHER", "collecting sources…"),
        ("TRIAGE", "filtering noise…"),
        ("SYNTH",  "combining insights…"),
        ("CITE",   "generating citations…"),
    ]
    for stage, msg in stages:
        yield _encode_sse({"stage": stage, "text": msg, "done": False})
        await asyncio.sleep(0.25)
    yield _encode_sse({"done": True})

@router.get("/stream")
async def stream(req: Request, q: str):
    """SSE 流：前端用 EventSource('/ai/deepresearch/stream?q=...') 订阅"""

    async def gen():
        try:
            async for chunk in _langflow_stream(q):
                yield chunk
        except LangflowConfigurationError:
            logger.info("Langflow not configured; falling back to mock response")
            async for chunk in _mock_stream(q):
                yield chunk
        except Exception as exc:  # pylint: disable=broad-except
            logger.exception("DeepResearch Langflow stream failed: %s", exc)
            yield _encode_sse({"stage": "ERROR", "text": str(exc), "done": False})
            yield _encode_sse({"done": True})

    return StreamingResponse(gen(), media_type="text/event-stream")


async def _langflow_stream(query: str) -> AsyncGenerator[str, None]:
    if not LANGFLOW_FLOW_ID:
        raise LangflowConfigurationError("LANGFLOW_FLOW_ID is not configured")

    base_url = LANGFLOW_BASE_URL.rstrip("/")
    url = f"{base_url}/api/v1/run/{LANGFLOW_FLOW_ID}"

    headers = {"accept": "text/event-stream"}
    if LANGFLOW_API_KEY:
        headers["x-api-key"] = LANGFLOW_API_KEY

    payload: Dict[str, Any] = {
        "input_value": query,
        "stream": True,
        "session_id": str(uuid4()),
        "input_type": "chat",
        "output_type": "chat",
    }
    if LANGFLOW_TWEAKS:
        payload["tweaks"] = LANGFLOW_TWEAKS

    timeout = httpx.Timeout(LANGFLOW_TIMEOUT, read=LANGFLOW_TIMEOUT)
    done_sent = False
    progress_seen = False

    async with httpx.AsyncClient(timeout=timeout) as client:
        try:
            async with client.stream("POST", url, json=payload, params={"stream": "true"}, headers=headers) as response:
                response.raise_for_status()

                async for line in response.aiter_lines():
                    if not line:
                        continue

                    if line.startswith(":") or line.startswith("event:"):
                        continue

                    data_str = line[5:].strip() if line.startswith("data:") else line.strip()
                    if not data_str:
                        continue

                    event = _normalize_langflow_payload(data_str)
                    if not event:
                        continue

                    if event.get("done"):
                        done_sent = True

                    if event.get("done") or event.get("stage") not in {"ADD_MESSAGE"}:
                        progress_seen = True
                    elif event.get("text"):
                        text = str(event["text"]).strip()
                        if text and text.lower() != query.strip().lower():
                            progress_seen = True

                    yield _encode_sse(event)
        except httpx.HTTPStatusError as exc:
            message = _extract_langflow_error_message(exc.response.text) or str(exc)
            yield _encode_sse({"stage": "ERROR", "text": message, "done": False})
            yield _encode_sse({"done": True})
            return
        except httpx.RequestError as exc:
            message = await _fallback_langflow_error(client, url, payload, headers) or str(exc)
            yield _encode_sse({"stage": "ERROR", "text": message, "done": False})
            yield _encode_sse({"done": True})
            return
        if not done_sent:
            if not progress_seen:
                message = await _fallback_langflow_error(client, url, payload, headers)
                if message:
                    yield _encode_sse({"stage": "ERROR", "text": message, "done": False})
                    yield _encode_sse({"done": True})
                    return

            yield _encode_sse({"done": True})


def _normalize_langflow_payload(payload: str) -> Optional[Dict[str, Any]]:
    try:
        raw = json.loads(payload)
    except json.JSONDecodeError:
        return {"stage": "TOKEN", "text": payload, "done": False}

    if isinstance(raw, dict):
        event: Dict[str, Any] = {"done": False}
        meta: Dict[str, Any] = {}

        stage = _extract_stage(raw)
        if stage:
            event["stage"] = stage

        text = _extract_text(raw)
        if text is not None:
            event["text"] = text

        run_id = raw.get("run_id") or raw.get("id") or raw.get("meta", {}).get("run_id")
        if run_id:
            meta["run_id"] = run_id

        progress = raw.get("progress") or raw.get("meta", {}).get("progress")
        if isinstance(progress, (int, float)):
            meta["progress"] = progress

        sources = raw.get("sources") or raw.get("meta", {}).get("sources")
        if sources:
            meta["sources"] = sources

        status = str(raw.get("status", "")).lower()
        if raw.get("done") or stage in {"DONE", "END"} or status in {"complete", "completed", "finished", "success"}:
            event["done"] = True
            event.setdefault("stage", "DONE")

        error_text = raw.get("error") or raw.get("detail")
        if error_text:
            event["stage"] = "ERROR"
            event["text"] = text or _stringify(error_text)
            event["done"] = False

        outputs = raw.get("outputs")
        if outputs is not None and "text" not in event:
            event["text"] = _stringify(outputs)

        if meta:
            event["meta"] = meta

        event.setdefault("stage", "UPDATE")

        if "text" not in event and not event.get("done"):
            return None

        return event

    if isinstance(raw, list):
        return {"stage": "LIST", "text": _stringify(raw), "done": False}

    return {"stage": "TOKEN", "text": _stringify(raw), "done": False}


def _extract_stage(raw: Dict[str, Any]) -> Optional[str]:
    candidates = [
        raw.get("stage"),
        raw.get("event"),
        raw.get("type"),
        raw.get("status"),
    ]

    data = raw.get("data")
    if isinstance(data, dict):
        candidates.extend([data.get("stage"), data.get("event"), data.get("type")])

    for candidate in candidates:
        if isinstance(candidate, str) and candidate.strip():
            return candidate.strip().upper()

    return None


def _extract_text(raw: Dict[str, Any]) -> Optional[str]:
    for key in ("text", "message", "chunk", "content", "output", "result", "delta"):
        if key in raw:
            value = raw[key]
            if isinstance(value, (str, list, dict)):
                stringified = _stringify(value)
                if stringified.strip():
                    return stringified
                # If the selected key exists but is empty, continue searching deeper.

    data = raw.get("data")
    if isinstance(data, dict):
        nested = _extract_text(data)
        if nested is not None:
            return nested

    blocks = raw.get("content_blocks")
    if isinstance(blocks, list):
        pieces = []
        for block in blocks:
            if not isinstance(block, dict):
                continue
            contents = block.get("contents")
            if isinstance(contents, list):
                for entry in contents:
                    if isinstance(entry, dict):
                        text_value = entry.get("text")
                        if text_value:
                            pieces.append(_stringify(text_value))
        if pieces:
            return "\n\n".join(pieces)

    return None


def _stringify(value: Any) -> str:
    if isinstance(value, str):
        return value
    if isinstance(value, (dict, list)):
        return json.dumps(value, ensure_ascii=False)
    return str(value)


async def _fallback_langflow_error(
    client: httpx.AsyncClient,
    url: str,
    payload: Dict[str, Any],
    headers: Dict[str, str],
) -> Optional[str]:
    """Attempt a non-streaming request to retrieve a detailed error message."""
    fallback_payload = dict(payload)
    fallback_payload["stream"] = False

    try:
        response = await client.post(url, json=fallback_payload, params={"stream": "false"}, headers=headers)
    except Exception as exc:  # pylint: disable=broad-except
        return f"{exc.__class__.__name__}: {exc}"

    text = response.text
    if response.status_code >= 400:
        message = _extract_langflow_error_message(text)
        if message:
            return message
        return f"{response.status_code} {response.reason_phrase}"

    # Even when status is 200, Langflow encodes errors inside the payload.
    return _extract_langflow_error_message(text)


def _extract_langflow_error_message(raw: Optional[str]) -> Optional[str]:
    if not raw:
        return None

    raw = raw.strip()
    if not raw:
        return None

    try:
        payload = json.loads(raw)
    except json.JSONDecodeError:
        return raw

    if isinstance(payload, dict):
        detail = payload.get("detail")
        if isinstance(detail, str):
            nested = _extract_langflow_error_message(detail)
            return nested or detail
        if isinstance(detail, dict):
            return detail.get("message") or _stringify(detail)

        message = payload.get("message")
        if isinstance(message, dict):
            return message.get("message") or _stringify(message)
        if isinstance(message, str):
            return message

        error_info = payload.get("error")
        if isinstance(error_info, dict):
            return error_info.get("message") or _stringify(error_info)
        if isinstance(error_info, str):
            return error_info

    return _stringify(payload)

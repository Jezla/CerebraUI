# ComfyUI Image-to-Image Complete Setup Guide

This guide will help you configure and use ComfyUI's image-to-image functionality, including solutions to all known issues.

## Table of Contents

1. [Feature Overview](#feature-overview)
2. [Configuration Steps](#configuration-steps)
3. [Chat Interface Usage](#chat-interface-usage)
4. [API Usage](#api-usage)
5. [Vision Model Compatibility](#vision-model-compatibility)
6. [Troubleshooting](#troubleshooting)
7. [Technical Implementation](#technical-implementation)

---

## Feature Overview

The system now supports two ComfyUI workflows:

1. **Text-to-Image**: Generate images from text descriptions
2. **Image-to-Image**: Generate modified images based on input images and text descriptions

### Core Features

- ✅ **Automatic Workflow Selection**: System automatically selects the appropriate workflow based on whether an image is provided
- ✅ **Chat Interface Integration**: Upload images in chat and request modifications, AI automatically uses img2img workflow
- ✅ **Multiple Image Format Support**: base64, URL, file path
- ✅ **Vision Model Compatibility**: Automatically handles non-vision models to avoid errors
- ✅ **Smart Message Handling**: AI provides concise confirmations in img2img scenarios without saying "cannot manipulate images"

---

## Configuration Steps

### 1. Prepare Workflow Files

#### Text-to-Image Workflow Example

```json
{
  "1": {
    "inputs": {
      "prompt": "",
      "width": 1024,
      "height": 1024,
      "num_inference_steps": 28,
      "guidance_scale": 3.5,
      "num_images": 1,
      "enable_safety_checker": true,
      "seed": 1120526409805421
    },
    "class_type": "FalAPIFluxDevNode",
    "_meta": {
      "title": "Fal API Flux Dev"
    }
  },
  "3": {
    "inputs": {
      "filename_prefix": "ComfyUI",
      "images": ["1", 0]
    },
    "class_type": "SaveImage",
    "_meta": {
      "title": "Save Image"
    }
  }
}
```

#### Image-to-Image Workflow Example

```json
{
  "2": {
    "inputs": {
      "prompt": "make the picture brighter",
      "width": 1024,
      "height": 1024,
      "num_inference_steps": 28,
      "guidance_scale": 3.5,
      "num_images": 1,
      "enable_safety_checker": true,
      "strength": 0.5,
      "seed": 253939441688607,
      "image": ["5", 0]
    },
    "class_type": "FalAPIFluxDevImageToImageNode",
    "_meta": {
      "title": "Fal API Flux Dev Image-to-Image"
    }
  },
  "3": {
    "inputs": {
      "images": ["2", 0]
    },
    "class_type": "PreviewImage",
    "_meta": {
      "title": "Preview Image"
    }
  },
  "5": {
    "inputs": {
      "image": "IMG_6187.JPG"
    },
    "class_type": "LoadImage",
    "_meta": {
      "title": "Load Image"
    }
  }
}
```

**Important**: When exporting workflows, select "API Format (JSON)".

### 2. Configure in Admin Interface

#### Step 1: Access Settings Page
- Log in to admin panel
- Navigate to **Settings > Images**

#### Step 2: Configure ComfyUI Connection
- **ComfyUI Base URL**: `http://your-comfyui-server:8188`
- **API Key**: (if ComfyUI authentication is enabled)

#### Step 3: Configure Text-to-Image Workflow

1. **Upload Workflow**
   - Click "Click here to upload a workflow.json file."
   - Select your text-to-image workflow JSON file

2. **Configure Node Mapping**

   | Node Type | Key | Node IDs | Description |
   |-----------|-----|----------|-------------|
   | prompt* | text/prompt | 1 | Prompt input node (required) |
   | model | ckpt_name | 1 | Model selection node |
   | width | width | 1 | Width parameter node |
   | height | height | 1 | Height parameter node |
   | steps | steps/num_inference_steps | 1 | Steps parameter node |
   | seed | seed | 1 | Random seed node |

   **Note**: Node IDs should be the actual IDs of corresponding nodes in your workflow.

#### Step 4: Configure Image-to-Image Workflow

1. **Upload Workflow**
   - Click "Click here to upload image-to-image workflow.json file."
   - Select your image-to-image workflow JSON file

2. **Configure Node Mapping**

   | Node Type | Key | Node IDs | Description |
   |-----------|-----|----------|-------------|
   | prompt* | text/prompt | 2 | Prompt input node (required) |
   | model | ckpt_name | 2 | Model selection node |
   | width | width | 2 | Width parameter node |
   | height | height | 2 | Height parameter node |
   | steps | steps/num_inference_steps | 2 | Steps parameter node |
   | seed | seed | 2 | Random seed node |
   | **image*** | **image** | **5** | **LoadImage node ID (required)** |
   | **strength** | **strength** | **2** | **Strength parameter node (optional)** |

   **Key Node Explanations**:
   - **image**: Must point to the `LoadImage` node's ID
   - **strength**: Points to the node ID that supports strength parameter (usually the ImageToImage node)

#### Step 5: Save Configuration
- Click "Save" button at the bottom of the page

---

## Chat Interface Usage

### Text-to-Image

**User Action**:
```
User: Generate an image of a sunset
```

**System Behavior**:
1. AI recognizes image generation request
2. Status shows: "Generating an image"
3. Uses text-to-image workflow
4. Returns generated image
5. AI confirms briefly: "I've generated an image of a sunset for you."

### Image-to-Image

**User Action**:
```
User: [Uploads an image]
User: Make this image brighter
```

**System Behavior**:
1. System extracts user's uploaded image
2. Status shows: "Generating an image"
3. Automatically selects image-to-image workflow
4. Uploads original image to ComfyUI server
5. Uses img2img workflow to generate modified image
6. Returns new image
7. AI confirms briefly: "I've made the image brighter as requested."

**Backend Logs**:
```
INFO: Found input image in chat: data:image/jpeg;base64,/9j/...
INFO: Using image-to-image generation with input image
INFO: Uploaded image: input_image_xxxxx.png
INFO: Using image-to-image workflow
```

### Smart Message Handling

System intelligently adjusts AI responses based on scenario:

**Image-to-Image Scenario**:
- ✅ AI provides brief confirmation that image was modified
- ✅ Won't say "I don't have the capability to manipulate images"
- ✅ System message explicitly tells AI that image modification is complete

**Text-to-Image Scenario**:
- ✅ AI confirms image generation
- ✅ May briefly describe generated content

---

## API Usage

### Text-to-Image API Request

```bash
curl -X POST http://your-server/api/images/generations \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "model": "flux-dev",
    "prompt": "a beautiful sunset over mountains",
    "size": "1024x1024",
    "n": 1
  }'
```

### Image-to-Image API Request

#### Using Base64 Image

```bash
curl -X POST http://your-server/api/images/generations \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "model": "flux-dev",
    "prompt": "make the picture brighter",
    "image": "data:image/png;base64,iVBORw0KGgoAAAANS...",
    "strength": 0.5,
    "size": "1024x1024",
    "n": 1
  }'
```

#### Using URL Image

```bash
curl -X POST http://your-server/api/images/generations \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "model": "flux-dev",
    "prompt": "make the picture brighter",
    "image": "http://your-server/files/abc123",
    "strength": 0.8,
    "size": "1024x1024",
    "n": 1
  }'
```

### Parameter Description

#### Required Parameters
- `prompt`: Text description
- `image`: (img2img only) Input image, supports base64, URL, or file path

#### Optional Parameters
- `strength`: (default 0.8) Image modification strength, range 0.0-1.0
  - `0.0`: Completely preserve original image
  - `0.5`: Medium modification
  - `1.0`: Complete regeneration
- `size`: Image dimensions, e.g., "1024x1024" or "512x512"
- `n`: Number of images to generate (default 1)
- `negative_prompt`: Negative prompt

---

## Vision Model Compatibility

### Background

When continuing conversation after generating images with ComfyUI, some non-vision models (like `gpt-4-0613`) receive messages containing images, causing 400 errors:

```
400: Invalid content type. image_url is only supported by certain models.
```

### Solution

System implements **automatic content filtering** that detects if models support vision and processes message content accordingly.

### Supported Vision Models

The following models support receiving image content:
- `gpt-4-vision`
- `gpt-4o` (recommended)
- `gpt-4o-mini`
- `gpt-4-turbo`
- `claude-3` (all variants)
- `gemini-1.5-pro-vision`
- `gemini-pro-vision`

### How It Works

#### Scenario 1: Using Non-Vision Model (e.g., gpt-4-0613)

**Before Filtering**:
```json
{
  "messages": [
    {
      "role": "user",
      "content": [
        {"type": "text", "text": "Make this image brighter"},
        {"type": "image_url", "image_url": {"url": "http://..."}}
      ]
    }
  ]
}
```

**After Filtering**:
```json
{
  "messages": [
    {
      "role": "user",
      "content": "Make this image brighter"
    }
  ]
}
```

- ✅ No 400 error
- ✅ AI receives pure text message
- ✅ User still sees image in interface

#### Scenario 2: Using Vision-Supported Model (e.g., gpt-4o)

- ✅ Image content passed normally to AI
- ✅ AI can "see" and analyze images
- ✅ No additional configuration needed

### Adding More Vision Models

To support more vision models, edit `backend/cerebraui/routers/openai.py`:

```python
vision_supported_models = [
    "gpt-4-vision",
    "gpt-4o",
    "gpt-4-turbo",
    "claude-3",
    "gemini-1.5-pro-vision",
    "gemini-pro-vision",
    # Add new model names (partial match)
    "your-new-vision-model",
]
```

---

## Troubleshooting

### 1. Image Upload Failed

**Symptoms**:
- Error: "Failed to upload image to ComfyUI"
- Logs show upload 500 or other errors

**Solutions**:
1. Check if ComfyUI server is running: `curl http://your-comfyui-server:8188`
2. Verify `/upload/image` endpoint is accessible
3. Check if API Key is correct
4. Verify image format is supported (PNG, JPEG)

### 2. Workflow Not Auto-Switching

**Symptoms**:
- Logs show "Using text-to-image workflow" but should use img2img
- Generated image unrelated to uploaded one

**Solutions**:
1. Confirm image-to-image workflow is uploaded and not empty
2. Check Node IDs configuration is correct
3. Verify `image` parameter has value: look for "Found input image in chat" in logs
4. Check if frontend correctly passes image data

### 3. Node Mapping Error

**Symptoms**:
- Error: Node ID not found
- Image generation fails

**Solutions**:
1. Use "Save (API Format)" when exporting workflow in ComfyUI
2. Check if Node IDs match keys in workflow JSON
3. Confirm LoadImage node's class_type is "LoadImage"
4. Verify node key names (e.g., "image", "strength", "prompt")

### 4. AI Still Says Cannot Manipulate Images

**Symptoms**:
- Image generates normally but AI responds "I cannot manipulate images"

**Solutions**:
1. Restart backend service to ensure latest code is effective
2. Check logs to confirm system message is correct:
   ```
   INFO: Using image-to-image generation with input image
   ```
3. Confirm `chat_image_generation_handler` is updated

### 5. Vision Model Not Receiving Images

**Symptoms**:
- Using gpt-4o but AI says can't see image

**Solutions**:
1. Check if model name contains vision keywords
2. Manually add model to `vision_supported_models` list
3. Check logs to confirm filtering logic isn't misidentifying

### 6. Uploaded Image in Chat Not Extracted

**Symptoms**:
- User uploaded image
- But logs don't show "Found input image in chat"

**Solutions**:
1. Check if frontend adds image to message.files array
2. Verify message format is correct
3. Confirm `chat_image_generation_handler` logic is correct

---

## How It Works

### Complete Flow Diagram

```
User uploads image + text request
        ↓
Chat interface triggers image generation
        ↓
chat_image_generation_handler extracts image
        ↓
Calls /api/images/generations (with image parameter)
        ↓
Backend selects img2img workflow
        ↓
Uploads image to ComfyUI server
        ↓
Sets filename to LoadImage node
        ↓
Executes ComfyUI workflow
        ↓
Gets generated image
        ↓
Returns to user
        ↓
AI briefly confirms modification complete
```

### Key Components

#### 1. Chat Integration (`backend/cerebraui/utils/middleware.py`)

`chat_image_generation_handler()` function:
- Extracts most recent user image from chat history
- Supports two formats:
  - `message.files[].url` (primary format)
  - `message.content[].image_url` (OpenAI format)
- Passes image data to image generation API
- Sets default strength to 0.7

#### 2. Workflow Selection (`backend/cerebraui/routers/images.py`)

```python
use_img2img = (
    form_data.image
    and request.app.state.config.COMFYUI_WORKFLOW_IMG2IMG
    and request.app.state.config.COMFYUI_WORKFLOW_IMG2IMG.strip() != ""
)
```

- Checks if `image` parameter is provided
- Checks if img2img workflow is configured
- Automatically selects corresponding workflow

#### 3. Image Upload (`backend/cerebraui/utils/images/comfyui.py`)

`upload_image_to_comfyui()` function:
- Parses base64, URL, or file path
- Uploads to ComfyUI's `/upload/image` endpoint
- Returns server-side filename

#### 4. Vision Content Filtering (`backend/cerebraui/routers/openai.py`)

`filter_vision_content_for_non_vision_models()` function:
- Detects if model supports vision
- Filters image_url content for unsupported models
- Maintains full content for supported models

---

## Technical Implementation

### Modified Files

#### Backend Files

1. **`backend/cerebraui/config.py`**
   - Added `COMFYUI_WORKFLOW_IMG2IMG` configuration
   - Added `COMFYUI_WORKFLOW_IMG2IMG_NODES` configuration

2. **`backend/cerebraui/main.py`**
   - Exported img2img configuration to app.state

3. **`backend/cerebraui/utils/images/comfyui.py`**
   - Added `upload_image_to_comfyui()` function
   - Extended `ComfyUIGenerateImageForm` to support image and strength
   - Modified `comfyui_generate_image()` to handle image upload and new node types

4. **`backend/cerebraui/routers/images.py`**
   - Extended `ComfyUIConfigForm` to support img2img configuration
   - Extended `GenerateImageForm` to support image and strength parameters
   - Added automatic workflow selection logic

5. **`backend/cerebraui/routers/openai.py`**
   - Added `filter_vision_content_for_non_vision_models()` function
   - Applied filtering in `generate_chat_completion()`

6. **`backend/cerebraui/utils/middleware.py`**
   - Modified `chat_image_generation_handler()` to extract images from chat
   - Smart system messages: concise confirmation in img2img scenarios

#### Frontend Files

1. **`src/lib/components/admin/Settings/Images.svelte`**
   - Added img2img workflow upload interface
   - Added img2img node configuration form
   - Added image and strength node types

### New Features

- ✅ Dual workflow architecture (text-to-image + image-to-image)
- ✅ Automatic workflow selection
- ✅ Image upload to ComfyUI
- ✅ Chat interface image extraction
- ✅ Vision model automatic compatibility
- ✅ Smart AI response handling
- ✅ Multiple image format support

### Database Configuration

Configuration stored in `config` table:

```
image_generation.comfyui.workflow          # Text-to-Image workflow JSON
image_generation.comfyui.nodes             # Text-to-Image node mapping
image_generation.comfyui.workflow_img2img  # Image-to-Image workflow JSON
image_generation.comfyui.nodes_img2img     # Image-to-Image node mapping
```

---

## Supported Image Formats

### Base64 Format
```
data:image/png;base64,iVBORw0KGgoAAAANS...
data:image/jpeg;base64,/9j/4AAQSkZJRgABAQ...
```

### URL Format
```
http://example.com/image.png
https://example.com/image.jpg
http://your-server/api/v1/files/abc123/content
```

### File Path Format
```
/path/to/image.png
uploads/image_123.jpg
```

---

## Log Examples

### Successful Image-to-Image Generation

```
INFO: Found input image in chat: data:image/jpeg;base64,/9j/4AAQSkZ...
INFO: Using image-to-image generation with input image
INFO: upload_image_to_comfyui
INFO: Image uploaded successfully: {'name': 'input_image_20240114_123456.png'}
INFO: Uploaded image: input_image_20240114_123456.png
INFO: Using image-to-image workflow
INFO: queue_prompt
INFO: WebSocket connection established.
INFO: Sending workflow to WebSocket server.
```

### Text-to-Image Generation

```
INFO: Using text-to-image workflow
INFO: queue_prompt
INFO: WebSocket connection established.
INFO: Sending workflow to WebSocket server.
```

### Vision Content Filtering

```
DEBUG: Filtering vision content for non-vision model: gpt-4-0613
DEBUG: Removed 1 image_url content items
```

---

## Changelog

### Version 1.2.0 (Latest)
- ✅ Fixed chat interface image extraction
- ✅ Smart AI responses: concise confirmation in img2img scenarios
- ✅ Improved log output

### Version 1.1.0
- ✅ Added vision model automatic compatibility
- ✅ Fixed 400 error for non-vision models
- ✅ Support for all mainstream vision models

### Version 1.0.0
- ✅ Multi-workflow configuration support
- ✅ Automatic workflow selection
- ✅ Image upload to ComfyUI
- ✅ Support for base64, URL, file path formats
- ✅ Frontend configuration interface
- ✅ Added image and strength node types

---

## Testing Recommendations

### Basic Functionality Tests

1. **Text-to-Image Test**
   ```
   User: Generate an image of a cat
   Expected: Image generated successfully, AI confirms generation
   ```

2. **Image-to-Image Test**
   ```
   User: [Uploads image]
   User: Make this image brighter
   Expected: Brighter image generated successfully, AI briefly confirms modification
   ```

3. **Vision Model Test**
   ```
   # Using gpt-4o
   User: [After image generation] What's in this image?
   Expected: AI can see and describe image content
   ```

4. **Non-Vision Model Test**
   ```
   # Using gpt-4-0613
   User: [After image generation] Continue conversation
   Expected: No errors, conversation proceeds normally
   ```

## Frequently Asked Questions (FAQ)

### Q: How to determine which workflow the system used?
**A**: Check backend logs, it will show:
- `INFO: Using text-to-image workflow` or
- `INFO: Using image-to-image workflow`

### Q: How does the strength parameter affect results?
**A**:
- `0.0-0.3`: Minor modifications, preserves most original features
- `0.4-0.6`: Medium modifications, balances original and new features
- `0.7-1.0`: Major modifications, may completely change image

### Q: Does it support batch generation?
**A**: Yes, set `n` parameter greater than 1, but workflow must support batch_size.

### Q: Can I use custom ComfyUI nodes?
**A**: Yes, as long as nodes accept standard parameter inputs, just configure node mapping correctly.

### Q: How to debug node mapping issues?
**A**:
1. Export workflow as API Format JSON
2. Check node IDs and parameter names
3. Fill in precisely in admin interface
4. Check backend logs to confirm parameter passing

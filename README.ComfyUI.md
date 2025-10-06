# ComfyUI-Docker Setup Guide (CPU / GPU)

This guide explains how to prepare the **ComfyUI-Docker** environment, add **comfyui-fal-api-flux**, and configure the container properly.

---

## 🧩 Step 1. Prepare Directories

Before running the container, create the required directories.

Open **PowerShell** and run the following commands:

```powershell
$base = Join-Path $PWD 'comfyui'
$dirs = @(
  "$base\custom_nodes",
  "$base\storage-user\input",
  "$base\storage-user\output",
  "$base\storage-user\workflows"
)
$dirs | % { New-Item -ItemType Directory -Path $_ -Force | Out-Null }
```

## 📁 Step 2. Add Custom Node
Download comfyui-fal-api-flux and place it under the custom_nodes/ directory, as shown below:
```bash
comfyui/cpu/custom_nodes/comfyui-fal-api-flux/
```

## ⚙️ Step 3. Configure Docker
Once your Docker container (CPU or GPU version) is built and running, open another PowerShell window and execute the following commands:
```bash
# Install or update fal-client
docker exec -it comfyui-cpu bash -lc "python3 -m pip install --no-cache-dir -U fal-client"
```

## 🌐 Step 4. Access ComfyUI Web Interface
1. Open ComfyUI in your web browser.

2. Click Manager on the top-right bar.

3. Select Custom Nodes Manager.

4. Search for “fal api flux” and install it.

The model is ComfyUI-Fal-API-Flux, installation link is https://github.com/yhayano-ponotech/ComfyUI-Fal-API-Flux

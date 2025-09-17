# Open WebUI Microservices Architecture Deployment

Deploy Open WebUI as a flexible and scalable microservices architecture with frontend-backend separation.

## Architecture Overview

The microservices architecture consists of eight core services:

1. **Frontend Service**: Nginx-based Svelte static file service responsible for providing the user interface.
2. **Backend Service**: Python FastAPI-based core application that handles business logic, API requests, and orchestrates other services.
3. **AI Model Service (Ollama)**: Responsible for running and providing large language model inference services.
4. **Cache Service (Redis)**: Provides high-performance caching and message queue support to optimize application performance.
5. **AI Workflow Service (Langflow)**: Visual AI workflow builder for creating and managing complex AI pipelines and chatbots.
6. **Image Generation Service (ComfyUI)**: A powerful and modular node-based GUI for image generation, integrated directly with the backend.
7. **Model Context Protocol Server (MCP Server)**: Provides AI models with a standardized set of tools (e.g., memory, time, web search) to enhance their capabilities.
8. **Observability Service (Grafana)**: Collects telemetry data (traces, metrics) from the backend for monitoring and performance analysis.

```mermaid
graph TD
    subgraph "Client Side"
        User("👤 User/Browser")
    end

    subgraph "Docker Network (openwebui-network)"
        Frontend["Frontend (Nginx)<br>Port: 3000"]
        Backend["Backend (FastAPI)<br>Port: 8080"]
        Langflow["Langflow (AI Workflow)<br>Port: 7860"]
        ComfyUI["ComfyUI (Image Generation)<br>Port: 8188"]
        MCPServer["MCP Server (AI Tools)<br>Port: 8000"]
        Grafana["Grafana (Observability)<br>Port: 3001"]
        Ollama["Ollama (AI Model Service)"]
        Redis["Redis (Cache Service)"]
    end

    User -- "HTTPS Request" --> Frontend
    User -- "Manage Workflows" --> Langflow
    User -- "Direct Access" --> ComfyUI
    User -- "View Dashboards" --> Grafana
    
    Frontend -- "Proxy /api/" --> Backend
    
    Backend -- "Direct API Call" --> Ollama
    Backend -- "Data Cache/Read" --> Redis
    Backend -- "Image Generation API Call" --> ComfyUI
    Backend -- "Sends Telemetry Data (OTLP)" --> Grafana
    Backend -- "Can use tools via" --> MCPServer

    MCPServer -- "Proxies to" --> Langflow
```

## Quick Start

Follow these steps to quickly start and run the Open WebUI microservices.

### 1. Environment Configuration

The project manages environment variables through the `.env` file. You can start by creating your own configuration from the template file:

```bash
# Copy the microservices environment configuration file
# You can modify port settings and other configurations in the .env file as needed
cp .env.example .env
```

### 2. Start Services

Use Docker Compose to start all services with one command:

```bash
# Start all microservices in background mode and rebuild if necessary
docker compose -f docker-compose.microservices.yaml up -d --build

# Check the status of all running services
docker-compose -f docker-compose.microservices.yaml ps
```

### 3. Access Services

After the services start, you can access them through the following addresses:

- **Web Interface**: `http://localhost:3000`
- **Backend API**: `http://localhost:8080`
- **API Documentation**: `http://localhost:8080/docs`
- **Langflow Interface**: `http://localhost:7860`
- **ComfyUI Interface**: `http://localhost:8188`
- **MCP Server API**: `http://localhost:8000`
- **Ollama Service**: `http://localhost:11434` (within container network)
- **Redis Service**: `localhost:6379`
- **Grafana Dashboard**: `http://localhost:3001`

## Service Configuration

### Core Environment Variables

You can customize the exposed ports of services in the `.env` file. The core behavior of the backend service is configured through environment variables in `docker-compose.yml`:

- `OLLAMA_BASE_URL`: Address of the Ollama service (`http://ollama:11434`).
- `WEBUI_SECRET_KEY`: Key for protecting session security.
- `ENABLE_SIGNUP`: Whether to allow user registration.
- `REDIS_URL`: Redis service address (`redis://redis:6379/0`).
- `LANGFLOW_DATABASE_URL`: PostgreSQL database connection string for Langflow data persistence. Example: `postgresql://username:password@host:port/database?sslmode=require`
- `ENABLE_IMAGE_GENERATION`: Set to `True` to enable the native image generation feature in Open WebUI.
- `COMFYUI_BASE_URL`: The internal network address of the ComfyUI service. In this setup, it's `http://comfyui:8188`.

### ComfyUI Integration (Image Generation)

The integration is enabled via environment variables. Follow these steps to configure it:

**Step 1: Prepare Directories for ComfyUI**

ComfyUI requires specific host directories to be mounted for storing models and user data. Create them before starting the services:

```
# Create the necessary directories for ComfyUI volumes
mkdir -p storage
mkdir -p storage-models/models
mkdir -p storage-models/hf-hub
mkdir -p storage-models/torch-hub
mkdir -p storage-user/input
mkdir -p storage-user/output
mkdir -p storage-user/workflows
```

**Step 2: Place Model Files**
 Place your downloaded model files (e.g., FLUX.1, VAEs, CLIPs) into the corresponding host directories, which are mounted into the ComfyUI container. For example:

- **Checkpoints**: Place in `./comfyui/storage-models/models/checkpoints/` and `./comfyui/storage-models/models/unet/`.
- **VAE Models**: Place in `./comfyui/storage-models/models/vae/`.
- **CLIP Models**: Place in `./comfyui/storage-models/models/clip/`.

**Step 3: Configure in Open WebUI**

1. Navigate to the **Admin Panel** > **Settings** > **Images** tab in Open WebUI.
2. The **Image Generation Engine** should be set to `ComfyUI`, and the **API URL** (`http://comfyui:8188`) should be pre-filled.
3. Click **Verify Connection**. Once successful, enable the **Image Generation (Experimental)** toggle.
4. In ComfyUI, enable **Dev Mode** (gear icon) and save your workflow using the **Save (API Format)** button to get a `workflow_api.json` file.
5. Return to Open WebUI and upload this `workflow_api.json` file.
6. Map the **ComfyUI Workflow Nodes** according to your imported workflow's node IDs and save the settings.

### MCP Server Configuration (AI Tools)

The tools available to the AI model are defined in the `mcp-config.json` file, which is mounted into the `mcpo-server` container. You can add, remove, or configure tools by editing this file. Currently configured tools include:

- `time`: Provides current time information.
- `memory`: A simple key-value store for short-term memory.
- `lf-starter_project`: A proxy to a specific Langflow project.

**Core Concept: Proxy Chain**
 For services that don't natively speak MCP, like Langflow, we use a proxy chain:
 `Open WebUI` → `mcpo-server (OpenAPI)` → `mcp-proxy (stdio)` → `Langflow (SSE)`

The `mcp-proxy` tool translates Langflow's SSE stream into the MCP protocol that the `mcpo-server` understands.

**Configuration Steps (Example: Adding a Langflow tool):**

1. **Edit `mcp-config.json`**: Add a new entry for your tool. The key is to use the Docker service name (e.g., `langflow`) instead of `localhost` for communication between containers.

   ```json
   {
     "mcpServers": {
       "time": { ... },
       "memory": { ... },
       "lf-starter_project": {
         "command": "uvx",
         "args": [
           "mcp-proxy",
           "http://langflow:7860/api/v1/mcp/project/<YOUR_PROJECT_ID>/sse"
         ]
       }
     }
   }
   ```

   Remember to replace `<YOUR_PROJECT_ID>` with the actual ID from your Langflow project's URL.

2. **Restart the MCP Service**: Since only the configuration file was changed, you only need to restart the `mcpo-server`:

   ```bash
   docker compose -f docker-compose.microservices.yaml up -d --force-recreate mcpo-server
   ```

3. **Add Tool in Open WebUI**: Go to **Admin Panel** > **Tools** and click **Add Tool Server**. Enter the URL corresponding to your new tool, using the key you defined in the config file:
    `http://mcpo-server:8000/your_langflow_tool`



## Network Communication

- **User → Frontend**: Users access the frontend Nginx service through browsers.
- **Frontend → Backend**: Frontend communicates with the backend API through a proxy (e.g., `/api/`).
- **Backend → Ollama**: Backend directly communicates with the Ollama service (`http://ollama:11434`) for language model inference.
- **Backend → Redis**: Backend connects to the Redis service for data caching.
- **Backend → ComfyUI**: For the native image generation feature, the backend makes API calls directly to the ComfyUI service (`http://comfyui:8188`).
- **Backend → Grafana**: The backend is configured as an OpenTelemetry (OTEL) client and sends tracing/metrics data to Grafana for monitoring.
- **Backend → MCP Server**: The AI model, running via the backend, can be configured to use tools provided by the MCP Server.
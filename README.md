# CerebraUI 👋

![GitHub stars](https://img.shields.io/github/stars/Jezla/CerebraUI?style=social)
![GitHub forks](https://img.shields.io/github/forks/Jezla/CerebraUI?style=social)
![GitHub watchers](https://img.shields.io/github/watchers/Jezla/CerebraUI?style=social)
![GitHub repo size](https://img.shields.io/github/repo-size/Jezla/CerebraUI)
![GitHub language count](https://img.shields.io/github/languages/count/Jezla/CerebraUI)
![GitHub top language](https://img.shields.io/github/languages/top/Jezla/CerebraUI)
![GitHub last commit](https://img.shields.io/github/last-commit/Jezla/CerebraUI?color=red)
![Hits](https://hits.seeyoufarm.com/api/count/incr/badge.svg?url=https%3A%2F%2Fgithub.com%2FJezla%2FCerebraUI&count_bg=%2379C83D&title_bg=%23555555&icon=&icon_color=%23E7E7E7&title=hits&edge_flat=false)
[![Discord](https://img.shields.io/badge/Discord-cerebra-ui-blue?logo=discord&logoColor=white)](https://discord.gg/5rJgQTnV4s)

**CerebraUI is an advanced, extensible, and feature-rich self-hosted AI platform built upon OpenWebUI and enhanced with cutting-edge microservices architecture.** Designed to operate entirely offline while supporting distributed deployments, it integrates various LLM runners like **Ollama** and **OpenAI-compatible APIs**, with **built-in inference engine** for RAG, **Redis caching**, **AI agent workflows**, and **ComfyUI pipeline support**.

![CerebraUI Demo](./demo.gif)

> [!NOTE]
> **CerebraUI is a fork of OpenWebUI** with significant enhancements including microservices architecture, Redis caching, AI agent workflows, enhanced security features, and ComfyUI integration. All core OpenWebUI functionality is preserved while adding powerful new capabilities.

## ✨ New CerebraUI Features

### 🆕 Major Enhancements

- **🏗️ Microservices Architecture**: Complete containerized deployment with separate services for frontend, backend, Redis, LangFlow, and ComfyUI
- **⚡ Redis Cache Integration**: Intelligent caching for selected reads/writes with TTL support and fallback mechanisms, significantly improving response times under load
- **🤖 AI Agent Workflow Integration**: Deep Research capabilities via LangFlow SSE streaming with start/stop controls and comprehensive logging
- **🔍 Enhanced Web Search**: Stabilized `/api/crawl` endpoint with standardized JSON output and async multi-URL crawling from the UI
- **🛡️ Enhanced Security**: Email verification, token-based password reset, Cloudflare Turnstile integration, and fixed 405/sign-up bypass issues
- **🎨 ComfyUI Pipeline API Support**: Containerized ComfyUI with txt2img/img2img workflows, auto-selection by input type, and integrated testing
- **🔄 Complete Rebranding**: Updated names, logos, assets, and documentation throughout the platform

## 🔧 Architecture Overview

CerebraUI introduces a true microservices architecture:

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │     Backend     │    │     Redis       │
│   (Nginx)       │◄──►│   (FastAPI)     │◄──►│    (Cache)      │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         │                       ▼                       │
         │              ┌─────────────────┐              │
         │              │    LangFlow     │              │
         │              │ (AI Workflows)  │              │
         │              └─────────────────┘              │
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│     ComfyUI     │    │     Ollama      │    │  External APIs  │
│ (Image Gen.)    │    │   (LLMs)        │    │ (OpenAI/etc.)   │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## 🚀 Installation

### Prerequisites

- Docker & Docker Compose
- At least 4GB RAM (8GB+ recommended for full stack)
- Optional: NVIDIA GPU with CUDA support for accelerated inference

### Quick Start with Microservices

1. **Clone the Repository**:
   ```bash
   git clone https://github.com/Jezla/CerebraUI.git
   cd CerebraUI
   ```

2. **Configure Environment**:
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

3. **Start All Services**:
   ```bash
   docker-compose up -d
   ```

4. **Access CerebraUI**:
   - Main Interface: http://localhost:3000
   - API Documentation: http://localhost:8080/docs
   - ComfyUI: http://localhost:8188
   - LangFlow: http://localhost:7860

### Installation Options

#### **Standard Installation (Ollama Integration)**
```bash
docker-compose up -d
```
Starts all services including Ollama for local model management.

#### **GPU-Accelerated Installation**
```bash
docker-compose -f docker-compose.gpu.yaml up -d
```
Utilizes NVIDIA GPUs for accelerated inference (requires NVIDIA container toolkit).

#### **API-Only Installation**
```bash
docker-compose -f docker-compose.api.yaml up -d
```
For use with external API providers (OpenAI, Claude, etc.) without local Ollama.

#### **Development Installation**
```bash
docker-compose -f docker-compose.playwright.yaml up -d
```
Includes development tools and hot-reload capabilities.

## ⚙️ Configuration

### Environment Variables

Key environment variables in `.env`:

```bash
# Core Configuration
CEREBRAUI_PORT=3000
OLLAMA_BASE_URL=http://ollama:11434
REDIS_URL=redis://redis:6379

# Security
JWT_SECRET_KEY=your-secret-key
ENABLE_EMAIL_VERIFICATION=true
CLOUDFLARE_TURNSTILE_SITE_KEY=your-site-key
CLOUDFLARE_TURNSTILE_SECRET_KEY=your-secret-key

# External Services
OPENAI_API_KEY=your-openai-key
LANGFLOW_URL=http://langflow:7860
COMFYUI_URL=http://comfyui:8188

# Cache Configuration
REDIS_TTL=3600
ENABLE_CACHE=true
CACHE_READ_PATTERNS="chat*,model*,user*"
```

### Service Health Checks

All services include comprehensive health checks:

```bash
# Check service status
docker-compose ps

# View logs
docker-compose logs -f [service-name]

# Health check endpoints
curl http://localhost:8080/health  # Backend
curl http://localhost:3000/health  # Frontend
```

## 🎯 Feature Deep Dive

### **Redis Cache Integration**

- **Selective Caching**: Only cache-read patterns that benefit from caching
- **TTL Support**: Configurable time-to-live for cached data
- **Fallback Mechanism**: Automatic fallback to database if cache fails
- **Performance**: Significant latency improvement under moderate load

```bash
# Monitor Redis cache
docker-compose exec redis redis-cli monitor
```

### **AI Agent Workflows (Deep Research)**

- **LangFlow Integration**: Advanced AI agent workflows via LangFlow
- **SSE Streaming**: Real-time progress updates via EventSource
- **Start/Stop Controls**: User-controlled workflow execution
- **Comprehensive Logging**: Detailed execution logs and replay capabilities

```bash
# Access LangFlow interface
http://localhost:7860
```

### **ComfyUI Pipeline Support**

- **Automatic Workflow Selection**: txt2img for text prompts, img2img for image inputs
- **Containerized Service**: Isolated ComfyUI environment with GPU support
- **API Integration**: Seamless integration with chat interface
- **Testing Framework**: Built-in smoke tests and validation

```bash
# Access ComfyUI interface
http://localhost:8188
```

### **Enhanced Security**

- **Email Verification**: Required email verification for new users
- **Token Reset**: Secure password reset via email tokens
- **Cloudflare Turnstile**: Bot protection and rate limiting
- **Fixed Vulnerabilities**: Resolved 405 bypass and signup security issues

## 🔍 Core Features (Inherited from OpenWebUI)

### **LLM Integration**
- 🤝 **Ollama/OpenAI API Integration**: Support for Ollama models and OpenAI-compatible APIs
- 🔧 **Model Builder**: Create and customize Ollama models via Web UI
- ⚙️ **Multi-Model Conversations**: Engage with multiple models simultaneously

### **User Experience**
- 📱 **Responsive Design**: Seamless experience across desktop, tablet, and mobile
- 📱 **PWA Support**: Native app-like experience on mobile devices
- 🌐🌍 **Multilingual Support**: Available in 30+ languages
- 🎤📹 **Voice/Video Calls**: Integrated communication features

### **Content & Tools**
- ✒️🔢 **Markdown & LaTeX**: Full support for rich text and mathematical expressions
- 📚 **Local RAG**: Built-in Retrieval Augmented Generation with document upload
- 🔍 **Web Search**: Integrated web search via multiple providers
- 🌐 **Web Browsing**: Direct website integration via `#URL` command
- 🐍 **Python Function Calling**: Native Python tool integration

### **Administration**
- 🔐 **Role-Based Access Control**: Granular permissions and user groups
- 🧩 **Plugin Support**: Extensible architecture via Pipelines Plugin Framework
- 📊 **Usage Monitoring**: Built-in analytics and usage tracking

## 🛠️ Development

### **Local Development Setup**

1. **Install Dependencies**:
   ```bash
   # Frontend
   cd src && npm install

   # Backend
   cd backend && pip install -r requirements.txt
   ```

2. **Start Development Services**:
   ```bash
   # Start supporting services
   docker-compose up -d redis ollama

   # Start backend
   cd backend && python -m uvicorn cerebraui.main:app --reload --port 8080

   # Start frontend
   cd src && npm run dev
   ```

### **Building Images**

```bash
# Build all services
docker-compose build

# Build specific service
docker-compose build backend
docker-compose build frontend
```

### **Running Tests**

```bash
# Backend tests
cd backend && python -m pytest

# Frontend tests
npm run test

# E2E tests
npm run test:e2e
```

## 🔧 Troubleshooting

### **Common Issues**

#### **Service Connection Errors**
```bash
# Check service connectivity
docker-compose exec backend ping redis
docker-compose exec frontend ping backend
```

#### **Cache Issues**
```bash
# Clear Redis cache
docker-compose exec redis redis-cli FLUSHALL
```

#### **GPU Not Detected**
```bash
# Check GPU availability
nvidia-docker ps
docker run --rm --gpus all nvidia/cuda:11.0-base nvidia-smi
```

### **Performance Optimization**

- **Redis Configuration**: Adjust `REDIS_TTL` and cache patterns based on usage
- **GPU Settings**: Configure `CUDA_VISIBLE_DEVICES` for multi-GPU setups
- **Resource Limits**: Set appropriate memory/CPU limits in docker-compose

### **Monitoring**

```bash
# View resource usage
docker stats

# Monitor logs
docker-compose logs -f --tail=100 [service]

# Health status
curl http://localhost:8080/health
```

## 🆙 Updating

### **Standard Update**
```bash
# Pull latest changes
git pull origin main

# Rebuild and restart services
docker-compose down
docker-compose build --pull
docker-compose up -d
```

### **Data Migration**
```bash
# Backup data before major updates
docker-compose exec backend python -m alembic upgrade head
```

## 🗺️ Roadmap

Upcoming features for CerebraUI:

- [ ] Advanced workflow orchestration
- [ ] Multi-tenant support
- [ ] Advanced analytics dashboard
- [ ] Plugin marketplace
- [ ] Enhanced model management
- [ ] Distributed training support

## 📜 License

This project is licensed under the [BSD-3-Clause License](LICENSE) - see the [LICENSE](LICENSE) file for details. 📄

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for details.

### **Development Areas**

- **Frontend**: SvelteKit applications and components
- **Backend**: FastAPI services and database models
- **DevOps**: Docker, Kubernetes, and deployment scripts
- **AI/ML**: Model integration and workflow optimization
- **Documentation**: Guides, API docs, and tutorials

## 💬 Support

- **Issues**: [GitHub Issues](https://github.com/Jezla/CerebraUI/issues)
- **Discussions**: [GitHub Discussions](https://github.com/Jezla/CerebraUI/discussions)
- **Discord**: [CerebraUI Discord](https://discord.gg/5rJgQTnV4s)
- **Documentation**: [CerebraUI Docs](https://docs.cerebraui.com)

## 🙏 Acknowledgments

- **OpenWebUI**: Foundation and core functionality
- **Ollama**: Local LLM management
- **LangFlow**: AI workflow orchestration
- **ComfyUI**: Image generation pipelines
- **Redis**: Caching and performance optimization

## Star History

<a href="https://star-history.com/#Jezla/CerebraUI&Date">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="https://api.star-history.com/svg?repos=Jezla/CerebraUI&type=Date&theme=dark" />
    <source media="(prefers-color-scheme: light)" srcset="https://api.star-history.com/svg?repos=Jezla/CerebraUI&type=Date" />
    <img alt="Star History Chart" src="https://api.star-history.com/svg?repos=Jezla/CerebraUI&type=Date" />
  </picture>
</a>

---

Let's build the future of AI interfaces together with CerebraUI! 💪✨
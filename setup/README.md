# 🛠️ ChronoVision AI — Setup & Deployment Hub

Welcome to the **ChronoVision AI** setup documentation. This directory contains detailed, step-by-step guides for installing, configuring, and running the platform across different operating systems and containerized environments.

---

## 🧭 Choose Your Setup Method

Select the guide that matches your operating system and preferred environment:

| Guide | Description | Best For |
| :--- | :--- | :--- |
| [**Windows Setup Guide**](WINDOWS_SETUP.md) | Step-by-step guide with direct links to Git, Docker Desktop, and a one-click automated batch script. | Beginners & Windows Developers |
| [**Linux & macOS Setup Guide**](LINUX_MAC_SETUP.md) | Terminal commands for Ubuntu/Debian/macOS (Docker and Bare-Metal Python venv). | Linux / macOS Developers |
| [**Docker Production Deployment**](DOCKER_SETUP.md) | Multi-container Docker Compose orchestration with GPU reservations and healthchecks. | DevOps & Production Deployments |
| [**Environment Variable Reference**](ENVIRONMENT.md) | Complete dictionary of all `.env` configuration keys, models, and fallback options. | All Developers |

---

## ⚡ Quick Start Summary

If you already have Docker installed and running:

```bash
# 1. Clone repository
git clone https://github.com/aaryanmax/sih.git
cd sih

# 2. Copy environment file
cp .env.example .env

# 3. Launch full stack via Docker Compose
docker compose up -d
```

### 🌐 Default Service Endpoints

Once running, access the services:
- **Next.js Web Dashboard**: [http://localhost:3001](http://localhost:3001)
- **FastAPI Backend Swagger**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **Qdrant Vector Database**: [http://localhost:6333/dashboard](http://localhost:6333/dashboard)
- **vLLM Engine Health**: [http://localhost:8001/health](http://localhost:8001/health)

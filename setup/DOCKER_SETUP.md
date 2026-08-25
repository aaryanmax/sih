# 🐳 Docker Production Deployment Guide

ChronoVision AI uses a containerized, production-grade microservice architecture defined in [`docker-compose.yml`](../docker-compose.yml).

---

## 🏗️ Architecture Services

```
┌─────────────────────────────────────────────────────────────┐
│                    Docker Compose Cluster                   │
│                                                             │
│   ┌───────────────┐     ┌───────────────┐     ┌───────────┐ │
│   │ Next.js Web   │────▶│ FastAPI API   │────▶│ Qdrant DB │ │
│   │ (Port: 3001)  │     │ (Port: 8000)  │     │ (Port:6333│ │
│   └───────────────┘     └───────┬───────┘     └───────────┘ │
│                                 │                           │
│                                 ▼                           │
│                         ┌───────────────┐                   │
│                         │ vLLM Engine   │                   │
│                         │ (Port: 8001)  │                   │
│                         └───────────────┘                   │
└─────────────────────────────────────────────────────────────┘
```

| Service | Container Name | Image / Build Context | Port Mapping | Healthcheck |
| :--- | :--- | :--- | :--- | :--- |
| `qdrant` | `sih_qdrant_storage` | `qdrant/qdrant:v1.14.0` | `6333:6333`, `6334:6334` | TCP probe on port 6333 |
| `vlm-engine`| `sih_vlm_engine` | `packages/vlm_engine/Dockerfile` | `8001:8001` | HTTP `/health` |
| `api` | `sih_fastapi_backend` | `apps/api/Dockerfile` | `8000:8000` | HTTP `/health` |
| `web` | `sih_nextjs_frontend` | `apps/web/Dockerfile` | `3001:3000` | N/A |

---

## 🚀 Lifecycle Commands

### Starting the Cluster
```bash
# Build images and start in background
docker compose up -d --build

# View real-time aggregated logs
docker compose logs -f
```

### Checking Health & Container Status
```bash
docker compose ps
```

### Viewing Individual Service Logs
```bash
docker compose logs -f api
docker compose logs -f web
docker compose logs -f vlm-engine
docker compose logs -f qdrant
```

### Stopping and Cleaning Up
```bash
# Stop containers without losing vector database storage
docker compose down

# Stop containers and wipe data volumes (Full Reset)
docker compose down -v
```

---

## 🎮 GPU Acceleration Configuration

In `docker-compose.yml`, the `vlm-engine` container is configured to request all available NVIDIA GPUs via `deploy.resources.reservations`:

```yaml
deploy:
  resources:
    reservations:
      devices:
        - driver: nvidia
          count: all
          capabilities: [gpu]
```

To run on systems without a dedicated NVIDIA GPU:
1. Docker Compose will automatically fall back to CPU emulation.
2. The FastAPI backend defaults to local CPU embedding (`vidore/colqwen2-v1.0` with `torch.bfloat16` on CPU).

# 🐧 Linux & macOS Setup Guide

This guide covers installing and running **ChronoVision AI** on Linux (Ubuntu, Debian, Fedora, Arch) and macOS (Apple Silicon / Intel).

---

## 📋 System Requirements

- **Linux**: Ubuntu 22.04 LTS / 24.04 LTS or newer
- **macOS**: macOS 13 (Ventura) or newer
- **Python**: 3.14+ (or 3.11+)
- **Node.js**: 24+ LTS (or 20+)
- **Docker**: Engine 24+ & Docker Compose v2.20+
- **NVIDIA GPU** *(Optional)*: CUDA 12.1+ and `nvidia-container-toolkit` for accelerated VLM serving.

---

## 🚀 Option A: Docker Compose Deployment (Recommended)

### 1. Install Docker & Docker Compose
```bash
# Ubuntu / Debian
sudo apt update
sudo apt install -y docker.io docker-compose-plugin
sudo usermod -aG docker $USER
newgrp docker

# macOS (via Homebrew)
brew install --cask docker
```

### 2. Clone & Launch
```bash
# Clone repository
git clone https://github.com/aaryanmax/sih.git
cd sih

# Configure environment
cp .env.example .env

# Launch services in background
docker compose up -d

# View real-time logs
docker compose logs -f
```

---

## 🛠️ Option B: Local Bare-Metal Setup (Development Mode)

### 1. Install System Dependencies & FFmpeg
```bash
# Ubuntu / Debian
sudo apt update
sudo apt install -y python3 python3-pip python3-venv ffmpeg git curl

# macOS
brew install python@3.14 node ffmpeg
```

### 2. Python Environment Setup
```bash
# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Upgrade pip & install packages
pip install --upgrade pip
pip install -r requirements.txt
pip install -r apps/api/requirements.txt
```

### 3. Frontend Setup
```bash
cd apps/web
npm install
cd ../..
```

### 4. Run Vector DB (Qdrant)
```bash
docker run -d --name qdrant_local \
  -p 6333:6333 -p 6334:6334 \
  -v $(pwd)/data:/qdrant/storage \
  qdrant/qdrant:v1.14.0
```

### 5. Start Backend & Frontend
```bash
# Terminal 1: Backend
python3 -m uvicorn apps.api.main:app --host 0.0.0.0 --port 8000 --reload

# Terminal 2: Frontend
npm --prefix apps/web run dev
```

---

## 🧪 Testing & Verification

```bash
# Run backend unit tests
python3 tests/run_tests.py

# Run offline smoke tests
python3 scripts/smoke_test.py --offline

# Run code linter
ruff check apps/ packages/ scripts/ tests/
```

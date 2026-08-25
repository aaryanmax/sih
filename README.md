<div align="center">

# ⚡ ChronoVision AI: Multi-Modal Video Retrieval Engine
### *Sub-Second Temporal Video Search via ColPali Late-Interaction, YOLO Object Detection, OCR, & Gemini Dual-Model Reranking*

[![License: Apache-2.0](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)
[![Python 3.14+](https://img.shields.io/badge/Python-3.14+-3776AB.svg?logo=python&logoColor=white)](https://python.org)
[![Node.js 24](https://img.shields.io/badge/Node.js-24+-black.svg?logo=node.js&logoColor=white)](https://nodejs.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-009688.svg?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![Next.js 14](https://img.shields.io/badge/Next.js-14.2-black.svg?logo=next.js&logoColor=white)](https://nextjs.org)
[![Qdrant](https://img.shields.io/badge/Qdrant-v1.14.0-red.svg?logo=qdrant&logoColor=white)](https://qdrant.tech)
[![Qwen2-VL](https://img.shields.io/badge/VLM-Qwen2--VL--7B-purple.svg)](https://github.com/QwenLM/Qwen2-VL)
[![ColPali](https://img.shields.io/badge/Retrieval-ColPali_MaxSim-indigo.svg)](https://github.com/illuin-tech/colpali)

<p align="center">
  <strong>Search raw, unstructured video archives through fine-grained token-to-patch late interaction, speech acoustic transcripts, visual OCR overlay text, YOLO object keyword boosting, and dual Gemini explainability & reranking.</strong>
</p>

[**🚀 Quick Setup Guide**](setup/README.md) • [**🪟 Windows 1-Click Setup**](setup/WINDOWS_SETUP.md) • [**🐧 Linux/macOS Guide**](setup/LINUX_MAC_SETUP.md) • [**🐳 Docker Deployment**](setup/DOCKER_SETUP.md) • [**📖 Technical Audit**](docs/CHRONOVISION_REPORT.md)

</div>

---

## 🌟 Overview & Key Innovations

Traditional video search compresses entire frames or video clips into single dense pooled vectors, losing granular spatio-temporal details (such as specific text on a terminal screen, an object in a corner, or momentary actions).

**ChronoVision AI** solves this through a unified **Multi-Modal Late-Interaction (ColPali / ColBERT paradigm)** retrieval architecture combined with a high-throughput Vision-Language Model (VLM):

1. **Token-to-Patch Multi-Vector Alignment (ColPali MaxSim)**: Queries are tokenized and scored against 64+ visual patch embeddings per keyframe using native Qdrant `MultiVectorConfig(comparator=MAX_SIM)` or in-memory FAISS.
2. **Real-Time YOLO Object Detection & Query Filtering**: Frame-level object detection using Ultralytics YOLO with 80 COCO classes. Supports natural-language query keyword extraction with hard `filter` mode and soft `boost` (+0.5 score) mode.
3. **Parallel Multithreaded OCR Text Intelligence**: OCR text extraction across frames using `ThreadPoolExecutor` and lexical token overlap scoring (`text_match_score`).
4. **OpenCV & decord Temporal Frame Sampling**: Chunks and seeks raw `.mp4` / `.mov` / `.avi` streams at customizable intervals (e.g. 2.0s) with microsecond timestamp tracking.
5. **Dual-Model Gemini Reranker & Explainability**: Leverages **Gemini 3.5 Flash-Lite** as the primary engine with **Gemini 3.1 Flash-Lite** as automatic circuit-breaker fallback, providing one-sentence natural language rationale.
6. **Zero-Docker Offline Search Mode (FAISS)**: Works 100% offline on any laptop using in-memory FAISS with sub-10ms CPU search — ideal for live stage demos without running Docker or databases.
7. **Interactive Cross-Attention Heatmaps & Temporal Scrubber**: Visualizes token-to-patch attention maps and timeline sparkline heatmaps directly on top of the video player.

---

## 🏛️ Architecture & System Map

```
                             ┌───────────────────────────┐
                             │    Raw Video (.mp4)       │
                             └─────────────┬─────────────┘
                                           │
         ┌───────────────────┬─────────────┴─────────────┬───────────────────┐
         ▼                   ▼                           ▼                   ▼
  ┌───────────────┐   ┌───────────────┐           ┌───────────────┐   ┌───────────────┐
  │ OpenCV Loader │   │ Whisper Audio │           │ Tesseract OCR │   │ YOLO Detector │
  │ Frame Sampler │   │ Transcription │           │ Multithreaded │   │ COCO 80-Class │
  └───────┬───────┘   └───────┬───────┘           └───────┬───────┘   └───────┬───────┘
          │ (RGB Frames)      │ (Transcripts)             │ (Text)            │ (Object Labels)
          ▼                   │                           │                   │
  ┌───────────────┐           │                           │                   │
  │    ColPali    │           │                           │                   │
  │ Qwen2-VL 128d │           │                           │                   │
  └───────┬───────┘           │                           │                   │
          │ (Multi-Vectors)   │                           │                   │
          └─────────┬─────────┴─────────────┬─────────────┴───────────────────┘
                    │                       │
                    ▼                       ▼
      ┌──────────────────────────┐    ┌──────────────────────────┐
      │  Docker / Online Mode    │    │  Zero-Docker Offline     │
      │  Qdrant Multi-Vector     │    │  FAISS HNSW Indexer      │
      │  Collection: video_frames│    │  Two-Stage Candidate ANN │
      └─────────────┬────────────┘    └─────────────┬────────────┘
                    │                               │
                    └───────────────┬───────────────┘
                                    │
                                    ▼
      ┌──────────────────────────────────────────────────────────┐
      │               FastAPI Central Backend                    │
      │  - ColPali / ColQwen2 Multi-Vector Query Encoder         │
      │  - Tri-Modal Hybrid Fusion (Visual + Audio + OCR + YOLO) │
      │  - Gemini 3.5 Flash-Lite (with 3.1 Flash-Lite Fallback)  │
      └─────────────────────────────┬────────────────────────────┘
                                    │
                                    ▼
      ┌──────────────────────────────────────────────────────────┐
      │              Next.js Interactive Dashboard               │
      │  - Smart Journey Player & Timeline Heatmap Scrubber      │
      │  - Token-to-Patch Attention Grid & Instant Video Seek    │
      └──────────────────────────────────────────────────────────┘
```

---

## 📦 Directory Structure

```
chronovision-ai/
├── apps/
│   ├── api/                     # FastAPI backend (endpoints, explainability, search)
│   └── web/                     # Next.js frontend (Smart Journey Player, search UI, /reels)
├── packages/
│   ├── audio_ocr/               # Whisper speech & OCR processors
│   ├── embeddings/              # Qwen2-VL PatchEncoder & QueryEncoder
│   ├── late_interaction/        # Qdrant late-interaction pipeline & scoring
│   ├── multi_search/            # Hierarchical multi-intent planner & ranking
│   ├── pipeline/                # Batch indexer & video analyzer
│   ├── pipeline_engine/         # Standalone local pipeline engine (FAISS, YOLO, OCR)
│   ├── retrieval/               # Hybrid search & Qdrant seeding
│   ├── vllm_inference/          # vLLM inference microservice
│   └── vlm_engine/              # Video chunker & inference server
├── setup/                       # Complete cross-platform setup guides & scripts
│   ├── README.md                # Master setup hub
│   ├── WINDOWS_SETUP.md         # Windows beginner setup guide
│   ├── LINUX_MAC_SETUP.md       # Linux and macOS installation guide
│   ├── DOCKER_SETUP.md          # Multi-container Docker deployment guide
│   ├── ENVIRONMENT.md           # Environment variable (.env) dictionary
│   └── setup_windows.bat        # Automated 1-click Windows installer script
├── docs/                        # Architecture reports & technical audits
│   ├── PROJECT_REPORT.md        # Project status report
│   └── CHRONOVISION_REPORT.md   # Deep technical audit & retrieval proof
├── data/                        # Local datasets, Qdrant storage, and models
├── scripts/                     # Ingestion, seeding, and smoke testing utilities
├── tests/                       # Automated pytest test suites
├── setup_windows.bat            # Root delegator for 1-click Windows setup
├── docker-compose.yml           # Multi-container orchestration
├── pyproject.toml               # Python 3.14 configuration (Ruff, Black, Pyright)
└── README.md                    # System documentation
```

---

## 🚀 Quick Start

### 1. One-Click Setup (Windows)

Simply double-click [`setup_windows.bat`](setup_windows.bat) or see the [Windows Setup Guide](setup/WINDOWS_SETUP.md).

### 2. Docker Compose (Cross-Platform)

```bash
# Clone the repository
git clone https://github.com/aaryanmax/sih.git
cd sih

# Configure environment variables
cp .env.example .env

# Launch Qdrant, FastAPI backend, and Next.js frontend
docker compose up -d
```

### 3. Local Bare-Metal Setup (Python 3.14 & Node.js 24)

```bash
# Python backend
python -m venv .venv
# On Windows: .venv\Scripts\activate | On Linux/macOS: source .venv/bin/activate
pip install -r requirements.txt
pip install -r apps/api/requirements.txt
python -m uvicorn apps.api.main:app --host 0.0.0.0 --port 8000 --reload

# Next.js frontend (in separate terminal)
cd apps/web && npm install && npm run dev
```

- **Frontend Dashboard**: [http://localhost:3001](http://localhost:3001) (or `http://localhost:3000` via bare metal)
- **FastAPI Documentation**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **Qdrant Dashboard**: [http://localhost:6333/dashboard](http://localhost:6333/dashboard)

---

## 📡 API Reference

### Multimodal Hybrid Search
`POST /api/v1/search/multi-intent`

```json
{
  "query": "person doing yoga on the beach",
  "top_k": 5
}
```

**Response:**
```json
{
  "query": "person doing yoga on the beach",
  "total": 1,
  "results": [
    {
      "video_id": "vid_beach_yoga_01",
      "video_url": "/videos/shorts/yt_bALeYF_5qME.mp4",
      "start_time": 12.0,
      "end_time": 16.0,
      "score": 0.935,
      "visual_score": 0.880,
      "whisper_score": 0.750,
      "ocr_score": 0.0,
      "explanation": "Visual frame shows a person executing yoga postures on a sandy coastline at sunrise.",
      "dataset_source": "Live Ingest"
    }
  ]
}
```

---

## 🧪 Testing & Verification

Run the automated test suites:
```bash
# Run backend pytest suite
python tests/run_tests.py

# Run offline smoke test suite
python scripts/smoke_test.py --offline

# Run code linter
ruff check apps/ packages/ scripts/ tests/
```

---

## 📄 License
This project is licensed under the **Apache License 2.0**.

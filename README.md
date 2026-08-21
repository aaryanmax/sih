<div align="center">

# ⚡ ChronoVision AI
### Deep Multimodal Semantic Video Intelligence & Late-Interaction Retrieval Platform

[![License: Apache-2.0](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)
[![Python 3.11+](https://img.shields.io/badge/Python-3.11+-3776AB.svg?logo=python&logoColor=white)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-009688.svg?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![Next.js 14](https://img.shields.io/badge/Next.js-14.2-black.svg?logo=next.js&logoColor=white)](https://nextjs.org)
[![Qdrant](https://img.shields.io/badge/Qdrant-v1.12.1-red.svg?logo=qdrant&logoColor=white)](https://qdrant.tech)
[![Qwen2-VL](https://img.shields.io/badge/VLM-Qwen2--VL--7B-purple.svg)](https://github.com/QwenLM/Qwen2-VL)
[![ColPali](https://img.shields.io/badge/Retrieval-ColPali_MaxSim-indigo.svg)](https://github.com/illuin-tech/colpali)

<p align="center">
  <strong>Search raw, unstructured video archives through fine-grained token-to-patch late interaction, speech acoustic transcripts, visual OCR overlay text, and temporal AI causal explainability.</strong>
</p>

</div>

---

## 🌟 Overview & Key Innovations

Traditional video search compresses entire frames or video clips into single dense pooled vectors, losing granular spatio-temporal details (such as specific text on a terminal screen, an object in a corner, or momentary actions).

**ChronoVision AI** solves this through a unified **Multi-Modal Late-Interaction (ColPali / ColBERT paradigm)** retrieval architecture combined with a high-throughput Vision-Language Model (VLM):

1. **Token-to-Patch Multi-Vector Alignment (ColPali MaxSim)**: Queries are tokenized and scored against 64+ visual patch embeddings per keyframe using native Qdrant `MultiVectorConfig(comparator=MAX_SIM)`.
2. **Temporal Context Video Slicing**: Chunks raw `.mp4` streams into 2-second overlapping tensor windows via `decord` and PyTorch hardware pipelines.
3. **Tri-Modal Hybrid Scoring**: Combines Visual Patch MaxSim ($60\%$), Whisper Audio Transcript alignment ($25\%$), and Keyframe OCR overlay text ($15\%$).
4. **Sub-300ms Causal Explainability**: Leverages **Gemini 1.5 Flash** with an asynchronous fallback circuit breaker to output natural language rationale explaining *why* each retrieved segment matches the query.
5. **Interactive Cross-Attention Heatmaps & Temporal Scrubber**: Visualizes token-to-patch attention maps and timeline sparkline heatmaps directly on top of the video player.

---

## 🏛️ Architecture & Module Map

```
                     ┌───────────────────────────┐
                     │    Raw Video (.mp4)       │
                     └─────────────┬─────────────┘
                                   │
         ┌─────────────────────────┼─────────────────────────┐
         ▼                         ▼                         ▼
  ┌───────────────┐        ┌───────────────┐        ┌───────────────┐
  │ M1: vLM Engine│        │ M3: Whisper   │        │ M3: PaddleOCR │
  │ Video Chunker │        │ Transcription │        │ Text Detector │
  └───────┬───────┘        └───────┬───────┘        └───────┬───────┘
          │ (Tensor Chunks)        │ (Transcripts)          │ (Text Bounding)
          ▼                        │                        │
  ┌───────────────┐                │                        │
  │ M2: ColPali   │                │                        │
  │ Patch Encoder │                │                        │
  └───────┬───────┘                │                        │
          │ (Multi-Vectors: 64x128)│                        │
          └────────────────┬───────┴────────────────────────┘
                           │
                           ▼
          ┌───────────────────────────────────┐
          │ M2 / Qdrant Multi-Vector Storage  │
          │ (sih_video_keyframes collection)  │
          └─────────────────┬─────────────────┘
                            │
                            ▼
          ┌───────────────────────────────────┐
          │ M4: FastAPI Central Backend       │
          │ - Query Multi-Vector Encoder      │
          │ - Hybrid Retrieval (MaxSim + BM25)│
          │ - Gemini 1.5 Flash Explainability │
          └─────────────────┬─────────────────┘
                            │
                            ▼
          ┌───────────────────────────────────┐
          │ M5: Next.js Interactive Dashboard │
          │ - Timeline Heatmap Scrubber       │
          │ - Token-to-Patch Attention Grid   │
          │ - Instant Video Seek Playback     │
          └───────────────────────────────────┘
```

### Module Breakdown

| Module | Identifier | Directory | Primary Responsibilities |
| :--- | :---: | :--- | :--- |
| **vLM Engine** | `M1` | [`packages/vlm-engine/`](packages/vlm-engine) | Temporal video slicing (`video_chunker.py`) & Qwen2-VL GPU inference server (`inference_server.py`). |
| **Embeddings & ColPali** | `M2` | [`packages/embeddings/`](packages/embeddings) & [`packages/late-interaction/`](packages/late-interaction) | Patch multi-vector extraction (`patch_encoder.py`), query embedding (`query_encoder.py`), and Qdrant MaxSim scoring (`maxsim_scorer.py`). |
| **Acoustic & OCR Intelligence** | `M3` | [`packages/audio-ocr/`](packages/audio-ocr) | Faster-Whisper timestamp transcription (`whisper_processor.py`) & keyframe OCR extraction (`ocr_processor.py`). |
| **Central Backend API** | `M4` | [`apps/api/`](apps/api) | FastAPI search router (`routes/search.py`) & Gemini causal explainability (`services/explainability.py`). |
| **Interactive Frontend** | `M5` | [`apps/web/`](apps/web) & [`src/`](src) | Next.js search interface & interactive Late-Interaction Heatmap playground. |
| **Orchestration & DevOps** | `M6` | [`docker-compose.yml`](docker-compose.yml) & [`Makefile`](Makefile) | One-click containerized cluster with GPU resource reservations and healthchecks. |

---

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- Node.js 20+
- Docker & Docker Compose (v2.20+)
- NVIDIA GPU with CUDA 12.1+ (optional, fallback CPU mode supported)

### 1. Clone & Setup Environment

```bash
# Clone the repository
git clone https://github.com/your-org/chronovision-ai.git
cd chronovision-ai

# Copy environment variables
cp .env.example .env
```

### 2. Launch Full Stack with Docker

```bash
# Launch Qdrant, FastAPI, vLLM Engine, and Next.js
docker compose up -d

# Check service logs
docker compose logs -f
```

- **Frontend Dashboard**: [http://localhost:3001](http://localhost:3001) (or `http://localhost:3000` via Vite)
- **FastAPI Documentation**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **Qdrant Dashboard**: [http://localhost:6333/dashboard](http://localhost:6333/dashboard)

### 3. Run Ingestion Pipeline

```bash
# Ingest and index raw video files in batch mode
make index-batch
```

---

## 📡 API Reference

### Multimodal Hybrid Search
`POST /api/v1/search`

```json
{
  "query": "ColPali late interaction MaxSim formula",
  "top_k": 5
}
```

**Response:**
```json
{
  "query": "ColPali late interaction MaxSim formula",
  "results": [
    {
      "video_id": "vid_colpali_overview",
      "timestamp_s": 165.0,
      "score": 0.942,
      "explanation": "Visual frame shows mathematical slide highlighting token-to-patch scoring matrix alongside audio transcript discussing multi-vector retention.",
      "transcript_text": "Notice how late interaction retains fine-grained patch tokens without single vector loss.",
      "ocr_text": "Score = sum(max(q_i * d_j)) over all query tokens",
      "keyframe_url": "/storage/frames/colpali_165.jpg"
    }
  ]
}
```

---

## 🧪 Testing & Verification

```bash
# Run linting across Python packages and backend
ruff check apps/api packages/
black --check apps/api packages/

# Run frontend linting & type checks
npm run lint
```

---

## 📄 License
This project is licensed under the **Apache License 2.0**.

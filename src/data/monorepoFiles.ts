import { MonorepoNode } from '../types';

export const monorepoTreeData: MonorepoNode = {
  id: 'root',
  name: 'sih-advanced-video-search',
  type: 'folder',
  path: '/',
  children: [
    {
      id: 'github',
      name: '.github',
      type: 'folder',
      path: '/.github',
      children: [
        {
          id: 'github-workflows',
          name: 'workflows',
          type: 'folder',
          path: '/.github/workflows',
          children: [
            {
              id: 'ci-yml',
              name: 'ci.yml',
              type: 'file',
              path: '/.github/workflows/ci.yml',
              language: 'yaml',
              description: 'GitHub Actions workflow for Python/Node linting and Docker compose validation',
              content: `name: SIH Advanced Video Search CI

on:
  push:
    branches: [ main, master, develop ]
  pull_request:
    branches: [ main, master ]

jobs:
  lint-and-typecheck:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Set up Python 3.11
        uses: actions/setup-python@v5
        with:
          python-version: "3.11"
      - name: Install Linters
        run: pip install ruff black mypy
      - name: Lint Backend & Packages
        run: ruff check apps/api packages/`
            }
          ]
        }
      ]
    },
    {
      id: 'apps',
      name: 'apps',
      type: 'folder',
      path: '/apps',
      children: [
        {
          id: 'apps-web',
          name: 'web',
          type: 'folder',
          path: '/apps/web',
          milestone: 'M5',
          description: 'Next.js Frontend for interactive search, timeline player, and visual patch attention maps',
          children: [
            {
              id: 'web-package-json',
              name: 'package.json',
              type: 'file',
              path: '/apps/web/package.json',
              language: 'json',
              content: `{
  "name": "sih-advanced-video-search-web",
  "version": "1.0.0",
  "private": true,
  "scripts": {
    "dev": "next dev",
    "build": "next build",
    "start": "next start"
  },
  "dependencies": {
    "next": "^14.2.15",
    "react": "^18.3.1",
    "react-dom": "^18.3.1",
    "lucide-react": "^0.453.0"
  }
}`
            },
            {
              id: 'web-dockerfile',
              name: 'Dockerfile',
              type: 'file',
              path: '/apps/web/Dockerfile',
              language: 'dockerfile',
              content: `FROM node:20-alpine AS builder
WORKDIR /app
COPY package.json ./
RUN npm install
COPY . .
RUN npm run build

FROM node:20-alpine AS runner
WORKDIR /app
ENV NODE_ENV=production
COPY --from=builder /app/.next ./.next
CMD ["npm", "start"]`
            },
            {
              id: 'web-page-tsx',
              name: 'page.tsx',
              type: 'file',
              path: '/apps/web/src/app/page.tsx',
              language: 'typescript',
              content: `"use client";
import React, { useState } from "react";
import { Search, Video, Sparkles } from "lucide-react";

export default function Home() {
  const [query, setQuery] = useState("ColPali Late Interaction MaxSim");
  return (
    <main className="p-6 max-w-7xl mx-auto space-y-6">
      <h1 className="text-2xl font-bold">SIH Advanced Video Search</h1>
      {/* Search Input & MaxSim Video Player */}
    </main>
  );
}`
            }
          ]
        },
        {
          id: 'apps-api',
          name: 'api',
          type: 'folder',
          path: '/apps/api',
          milestone: 'M4',
          description: 'FastAPI Backend orchestrating late-interaction retrieval, Qdrant index, and Qwen-VL reasoning',
          children: [
            {
              id: 'api-main-py',
              name: 'main.py',
              type: 'file',
              path: '/apps/api/main.py',
              language: 'python',
              content: `from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI(title="SIH Advanced Video Search API")

class SearchQuery(BaseModel):
    query: str
    top_k: int = 10

@app.post("/api/v1/search/multimodal")
async def search_multimodal(payload: SearchQuery):
    # Runs ColPali MaxSim late-interaction across video frame tokens
    return {"results": []}`
            },
            {
              id: 'api-requirements',
              name: 'requirements.txt',
              type: 'file',
              path: '/apps/api/requirements.txt',
              language: 'text',
              content: `fastapi>=0.115.0
uvicorn[standard]>=0.30.0
pydantic>=2.8.0
qdrant-client>=1.12.0
numpy>=1.26.0
httpx>=0.27.0`
            },
            {
              id: 'api-dockerfile',
              name: 'Dockerfile',
              type: 'file',
              path: '/apps/api/Dockerfile',
              language: 'dockerfile',
              content: `FROM python:3.11-slim
WORKDIR /app
RUN apt-get update && apt-get install -y ffmpeg libgl1
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]`
            }
          ]
        }
      ]
    },
    {
      id: 'packages',
      name: 'packages',
      type: 'folder',
      path: '/packages',
      children: [
        {
          id: 'pkg-vllm',
          name: 'vllm-inference',
          type: 'folder',
          path: '/packages/vllm-inference',
          milestone: 'M1',
          description: 'High-throughput Qwen-VL Vision-Language model serving via vLLM engine',
          children: [
            {
              id: 'vllm-service-py',
              name: 'inference_service.py',
              type: 'file',
              path: '/packages/vllm-inference/inference_service.py',
              language: 'python',
              content: `from pydantic import BaseModel
from typing import List

class FrameQueryRequest(BaseModel):
    query: str
    image_urls: List[str]
    temperature: float = 0.2

class QwenVLInferenceEngine:
    def __init__(self, endpoint_url="http://localhost:8000/v1"):
        self.endpoint_url = endpoint_url

    async def analyze_frame(self, request: FrameQueryRequest):
        # Sends frame patches to Qwen2-VL for scene captioning & QA
        pass`
            },
            {
              id: 'vllm-dockerfile',
              name: 'Dockerfile',
              type: 'file',
              path: '/packages/vllm-inference/Dockerfile',
              language: 'dockerfile',
              content: `FROM vllm/vllm-openai:v0.6.3
ENV MODEL_NAME="Qwen/Qwen2-VL-7B-Instruct"
CMD python3 -m vllm.entrypoints.openai.api_server --model \${MODEL_NAME}`
            },
            {
              id: 'vllm-requirements',
              name: 'requirements.txt',
              type: 'file',
              path: '/packages/vllm-inference/requirements.txt',
              language: 'text',
              content: `vllm>=0.6.3
torch>=2.4.0
transformers>=4.45.0
qwen-vl-utils>=0.0.8`
            }
          ]
        },
        {
          id: 'pkg-late-interaction',
          name: 'late-interaction',
          type: 'folder',
          path: '/packages/late-interaction',
          milestone: 'M2',
          description: 'ColPali multi-vector embedding pipeline & MaxSim late-interaction scoring',
          children: [
            {
              id: 'scoring-py',
              name: 'scoring.py',
              type: 'file',
              path: '/packages/late-interaction/scoring.py',
              language: 'python',
              content: `import numpy as np

def compute_maxsim_score(query_embeddings: np.ndarray, doc_embeddings: np.ndarray) -> float:
    """
    MaxSim formula: Score = sum_{q in Query} max_{d in Doc} (q . d)
    """
    q_norm = query_embeddings / np.linalg.norm(query_embeddings, axis=-1, keepdims=True)
    d_norm = doc_embeddings / np.linalg.norm(doc_embeddings, axis=-1, keepdims=True)
    sim_matrix = np.dot(q_norm, d_norm.T)
    return float(np.sum(np.max(sim_matrix, axis=1)))`
            },
            {
              id: 'embedder-py',
              name: 'embedder.py',
              type: 'file',
              path: '/packages/late-interaction/embedder.py',
              language: 'python',
              content: `class ColPaliEmbedder:
    def __init__(self, model_name="vidore/colpali-v1.2"):
        self.embedding_dim = 128

    def embed_frame(self, image_path: str):
        # Returns (num_patches, 128) multi-vector patch embeddings
        pass`
            },
            {
              id: 'qdrant-pipeline-py',
              name: 'qdrant_pipeline.py',
              type: 'file',
              path: '/packages/late-interaction/qdrant_pipeline.py',
              language: 'python',
              content: `from qdrant_client import QdrantClient
from qdrant_client.http import models

class VideoVectorStore:
    def initialize_schema(self):
        # Configures Qdrant MultiVectorConfig with MAX_SIM comparator
        pass`
            }
          ]
        },
        {
          id: 'pkg-audio-ocr',
          name: 'audio-ocr',
          type: 'folder',
          path: '/packages/audio-ocr',
          milestone: 'M3',
          description: 'Whisper speech transcription, keyframe OCR detection, and scene sampler',
          children: [
            {
              id: 'whisper-py',
              name: 'whisper_processor.py',
              type: 'file',
              path: '/packages/audio-ocr/whisper_processor.py',
              language: 'python',
              content: `from faster_whisper import WhisperModel

class WhisperAudioProcessor:
    def __init__(self, model_size="base"):
        self.model = WhisperModel(model_size)

    def transcribe_video_audio(self, video_path: str):
        segments, _ = self.model.transcribe(video_path, word_timestamps=True)
        return list(segments)`
            },
            {
              id: 'ocr-py',
              name: 'ocr_processor.py',
              type: 'file',
              path: '/packages/audio-ocr/ocr_processor.py',
              language: 'python',
              content: `from paddleocr import PaddleOCR

class OCRProcessor:
    def __init__(self):
        self.ocr = PaddleOCR(use_angle_cls=True, lang='en')

    def process_frame(self, frame_path: str):
        result = self.ocr.ocr(frame_path, cls=True)
        return result`
            },
            {
              id: 'frame-sampler-py',
              name: 'frame_sampler.py',
              type: 'file',
              path: '/packages/audio-ocr/frame_sampler.py',
              language: 'python',
              content: `import cv2

class VideoFrameSampler:
    def sample_video(self, video_path: str, interval_sec: float = 2.0):
        # Extracts keyframes at scene transitions & regular intervals
        pass`
            }
          ]
        }
      ]
    },
    {
      id: 'docker-compose',
      name: 'docker-compose.yml',
      type: 'file',
      path: '/docker-compose.yml',
      milestone: 'M6',
      language: 'yaml',
      description: 'Container orchestration for Qdrant, vLLM Qwen-VL, FastAPI backend, and Next.js frontend',
      content: `version: '3.8'

services:
  qdrant:
    image: qdrant/qdrant:v1.12.1
    ports: ["6333:6333", "6334:6334"]
    volumes: [qdrant_storage:/qdrant/storage]

  vllm-inference:
    build: ./packages/vllm-inference
    ports: ["8001:8000"]
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: all
              capabilities: [gpu]

  api:
    build: ./apps/api
    ports: ["8000:8000"]
    depends_on: [qdrant]
    environment:
      - QDRANT_HOST=qdrant
      - VLLM_HOST=http://vllm-inference:8000/v1

  web:
    build: ./apps/web
    ports: ["3001:3000"]
    depends_on: [api]

volumes:
  qdrant_storage:
  api_video_storage:`
    },
    {
      id: 'gitignore',
      name: '.gitignore',
      type: 'file',
      path: '/.gitignore',
      language: 'text',
      description: 'Explicit ignore rules blocking heavy weights (*.pt), video datasets (*.mp4), node_modules, and /qdrant_storage',
      content: `# Dependencies
node_modules/

# Python cache & envs
__pycache__/
.venv/

# Heavy binary models & video datasets (CRITICAL)
*.pt
*.pth
*.bin
*.safetensors
*.mp4
*.mkv
*.avi

# Database and vector storage
/qdrant_storage/
data/raw_videos/
data/extracted_frames/

# Frontend builds
.next/
dist/
build/`
    }
  ]
};

export const modulesData = [
  {
    id: 'm1',
    code: 'M1' as const,
    name: 'vLLM Inference Engine (Qwen-VL)',
    path: 'packages/vllm-inference',
    techStack: ['vLLM', 'Qwen2-VL-7B', 'PyTorch', 'CUDA', 'OpenAI API Spec'],
    role: 'Provides high-throughput multi-modal inference and reasoning over keyframes.',
    keyFiles: ['inference_service.py', 'Dockerfile', 'requirements.txt'],
    inputs: 'Sampled Video Keyframes (PNG/JPEG) + Natural Language Question',
    outputs: 'Fine-grained scene captioning, spatial bounding explanations, visual QA answers',
    status: 'Ready' as const
  },
  {
    id: 'm2',
    code: 'M2' as const,
    name: 'Late-Interaction Pipeline (ColPali)',
    path: 'packages/late-interaction',
    techStack: ['ColPali', 'ColBERT', 'Qdrant Multi-Vector', 'MaxSim', 'NumPy'],
    role: 'Generates patch-level multi-vectors for video frames and computes token MaxSim scores.',
    keyFiles: ['scoring.py', 'embedder.py', 'qdrant_pipeline.py'],
    inputs: 'Text Query Tokens + Frame Visual Patches (8x8 grid, 128-d per patch)',
    outputs: 'MaxSim rank scores, token-patch cross-attention heatmaps',
    status: 'Ready' as const
  },
  {
    id: 'm3',
    code: 'M3' as const,
    name: 'Audio & OCR Multi-Modal Processing',
    path: 'packages/audio-ocr',
    techStack: ['Faster-Whisper', 'PaddleOCR', 'OpenCV', 'PySceneDetect', 'FFmpeg'],
    role: 'Extracts spoken audio transcripts with timestamps and recognizes on-screen text/code.',
    keyFiles: ['whisper_processor.py', 'ocr_processor.py', 'frame_sampler.py'],
    inputs: 'Raw Video MP4 Stream',
    outputs: 'Time-aligned audio transcripts, keyframe bounding boxes, scene transition cuts',
    status: 'Ready' as const
  },
  {
    id: 'm4',
    code: 'M4' as const,
    name: 'FastAPI Backend & Orchestrator',
    path: 'apps/api',
    techStack: ['FastAPI', 'Uvicorn', 'Pydantic v2', 'AsyncIO', 'HTTPX'],
    role: 'Exposes unified REST and WebSocket endpoints orchestrating search, indexing, and QA.',
    keyFiles: ['main.py', 'Dockerfile', 'requirements.txt'],
    inputs: 'REST search queries, video upload multi-part streams',
    outputs: 'Aggregated ranked timestamp matches, snippet cards, explainability payloads',
    status: 'Ready' as const
  },
  {
    id: 'm5',
    code: 'M5' as const,
    name: 'Next.js Interactive Web App',
    path: 'apps/web',
    techStack: ['Next.js 14', 'React 18', 'Tailwind CSS', 'Lucide Icons'],
    role: 'Frontend UI for timestamp search, video playback synchronization, and heatmap display.',
    keyFiles: ['src/app/page.tsx', 'src/app/layout.tsx', 'package.json', 'Dockerfile'],
    inputs: 'User search query, modality filters, timestamp scrub position',
    outputs: 'Synchronized video playback, visual patch overlay, transcript highlights',
    status: 'Ready' as const
  },
  {
    id: 'm6',
    code: 'M6' as const,
    name: 'Docker Compose Orchestration',
    path: 'docker-compose.yml',
    techStack: ['Docker Compose', 'Qdrant Vector DB', 'NVIDIA Container Toolkit'],
    role: 'Coordinates Qdrant vector database, vLLM service, FastAPI backend, and Next.js frontend.',
    keyFiles: ['docker-compose.yml', '.gitignore'],
    inputs: 'Environment variables, network bridging, GPU device reservations',
    outputs: 'Fully containerized local & cloud production deployment',
    status: 'Ready' as const
  }
];

# SIH Advanced Video Search - Project Status Report

## Executive Summary
The project is a state-of-the-art **Multimodal Video Search Engine** built for the SIH (Smart India Hackathon). It implements a Late-Interaction retrieval architecture (inspired by ColPali) to allow users to search through raw video files using natural language. Instead of relying on single pooled vectors, it aligns text query tokens directly against visual patch tokens extracted from a Vision-Language Model (VLM), supplemented by audio transcripts and OCR.

## Current Project State & Accomplishments

The entire end-to-end architecture has been successfully scaffolded and implemented across four primary phases:

### 1. Infrastructure & Orchestration
*   **Dockerized Stack:** Configured a comprehensive `docker-compose.yml` that orchestrates Qdrant (Vector DB), FastAPI (Backend), Next.js (Frontend), and a GPU-accelerated `vlm-engine`.
*   **One-Click Setup:** Developed a `Makefile` (`make setup`, `make up`, `make index-batch`) to completely abstract away complex Docker/GPU commands for the development team.

### 2. Video Processing & vLM Engine
*   **High-Speed Temporal Chunker:** Implemented `video_chunker.py` using `decord` (with an ffmpeg fallback) to slice raw `.mp4` files into chronological 2-second windows natively in PyTorch tensors, avoiding slow OpenCV frame extraction.
*   **GPU Inference Server:** Built an isolated `inference_server.py` using `vLLM` to host **Qwen2-VL-7B**. It includes strict memory safeguards (`gpu_memory_utilization`, `max_model_len`) to prevent CUDA Out of Memory (OOM) errors during heavy video ingestion.

### 3. Late-Interaction Embeddings & Qdrant Integration
*   **Patch Encoder:** Engineered `patch_encoder.py` to extract distinct patch-level tokens (multi-vectors) from the VLM's hidden states, projecting them down to 128 dimensions and L2-normalizing them for ColPali-style late interaction.
*   **Query Encoder:** Implemented `query_encoder.py` to tokenize and embed natural language user queries into the identical multi-vector projection space.
*   **Qdrant MaxSim Schema:** Configured `maxsim_scorer.py` to initialize Qdrant collections natively supporting `MultiVectorConfig(comparator=MAX_SIM)`, enabling mathematical similarity calculations directly within the database layer.

### 4. Ingestion Pipeline & Hybrid Retrieval
*   **Batch Ingestion Orchestrator:** Created `batch_indexer.py` to process directories of raw videos. It combines VLM visual patches, Whisper audio transcripts, and OCR text into a unified Qdrant payload and performs fast batch insertions.
*   **Hybrid Search Engine:** Developed `hybrid_search.py` to compute a blended relevance score:
    *   60% Visual MaxSim
    *   25% Whisper Audio Keyword Match
    *   15% OCR Overlay Keyword Match

### 5. API Backend & AI Explainability
*   **FastAPI Search Route:** Implemented the primary `/api/v1/search` endpoint connecting the query encoder, hybrid search, and formatting the strict JSON contract.
*   **Causal Explainability:** Integrated `explainability.py` using **Gemini 1.5 Flash**. It analyzes the top-ranked temporal chunk and dynamically generates a 1-sentence explanation of *why* the video matches the query. It includes a strict **300ms timeout** with a rule-based fallback to guarantee zero latency lag during demonstrations.

### 6. Next.js Frontend Visualization
*   **Search Playground UI:** Finalized the interactive search interface in `SearchPlayground.tsx`.
*   **Timeline Heatmap Engine:** Engineered a visual sparkline overlay above the video player scrubber. This heatmap dynamically reads the chunk scoring data (`timelineHeatmap`) to show exactly where the optimal temporal alignment resides across the video's full length, allowing users to instantly seek to peak match locations.

## Next Steps / Pending Capabilities
*   **Model Weights:** The ColPali/Qwen projection weights are currently simulated/randomized for architectural completeness. The actual trained LoRA/projection weights need to be loaded into the `patch_encoder` and `query_encoder`.
*   **Live Whisper/OCR Endpoints:** The batch indexer references Whisper and OCR modules (`whisper_processor`, `ocr_processor`) which assume the existence of local ML models or API endpoints to generate the respective lexical payloads.
*   **Production Deployment:** Transitioning from the local `docker-compose` environment to a managed cloud deployment (e.g., Google Cloud Run / GKE) for live hackathon judging.

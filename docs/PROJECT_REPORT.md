# SIH Advanced Video Search — Project Status Report

## Executive Summary
The project is a state-of-the-art **Multimodal Video Search Engine** built for the SIH (Smart India Hackathon). It implements a Late-Interaction retrieval architecture (inspired by ColPali) to allow users to search through raw video files using natural language. Instead of relying on single pooled vectors, it aligns text query tokens directly against visual patch tokens extracted from a Vision-Language Model (VLM), supplemented by audio transcripts and OCR.

## Current Project State & Accomplishments

The entire end-to-end architecture has been successfully scaffolded and implemented across four primary phases:

### 1. Infrastructure & Orchestration
*   **Dockerized Stack:** Configured a comprehensive `docker-compose.yml` that orchestrates Qdrant (Vector DB v1.14.0), FastAPI (Backend with Python 3.14), Next.js (Frontend with Node.js 24), and a GPU-accelerated `vlm_engine`.
*   **One-Click Setup:** Developed automated setup scripts in `/setup` (`setup_windows.bat`, `setup/README.md`) and a `Makefile` (`make setup`, `make up`, `make index-batch`) to abstract away complex commands.

### 2. Video Processing & vLM Engine
*   **High-Speed Temporal Chunker:** Implemented `video_chunker.py` using `decord` (with an ffmpeg fallback) to slice raw `.mp4` files into chronological 2-second windows natively in PyTorch tensors, avoiding slow OpenCV frame extraction.
*   **GPU Inference Server:** Built an isolated `inference_server.py` using `vLLM` to host **Qwen2-VL-7B**. It includes strict memory safeguards (`gpu_memory_utilization`, `max_model_len`) to prevent CUDA Out of Memory (OOM) errors during heavy video ingestion.

### 3. Late-Interaction Embeddings & Qdrant Integration
*   **Patch Encoder:** Engineered `patch_encoder.py` to extract distinct patch-level tokens (multi-vectors) from the VLM's hidden states, projecting them down to 128 dimensions and L2-normalizing them for ColPali-style late interaction.
*   **Query Encoder:** Implemented `query_encoder.py` (`packages/embeddings/`) to tokenize and embed natural language user queries into the identical multi-vector projection space.
*   **Qdrant MaxSim Schema:** Configured `maxsim_scorer.py` to initialize Qdrant collections (`video_frames`) natively supporting `MultiVectorConfig(comparator=MAX_SIM)`, enabling mathematical similarity calculations directly within the database layer.

### 4. Ingestion Pipeline & Hybrid Retrieval
*   **Batch Ingestion Orchestrator:** Created `batch_indexer.py` (`packages/pipeline/`) to process directories of raw videos. It combines VLM visual patches, Whisper audio transcripts, and OCR text into a unified Qdrant payload and performs fast batch insertions.
*   **Hybrid Search Engine:** Developed `hybrid_search.py` (`packages/retrieval/`) to compute a blended relevance score:
    *   60% Visual MaxSim
    *   25% Whisper Audio Keyword Match
    *   15% OCR Overlay Keyword Match

### 5. API Backend & AI Explainability
*   **FastAPI Search Route:** Implemented the primary `/api/v1/search` and `/api/v1/search/multi-intent` endpoints connecting the query encoder, hybrid search, and taxonomy planner.
*   **Causal Explainability:** Integrated `explainability.py` using **Gemini 3.5 Flash-Lite** with an automatic circuit-breaker fallback to **Gemini 3.1 Flash-Lite**. It analyzes retrieved temporal chunks and dynamically generates natural language rationale explaining *why* the video matches the query.

### 6. Next.js Frontend Visualization
*   **Search Playground UI:** Finalized the interactive search interface in `apps/web/src/components/SearchPlayground.tsx` and the TikTok/Reels feed in `apps/web/src/app/reels/page.tsx`.
*   **Timeline Heatmap Engine:** Engineered a visual sparkline overlay above the video player scrubber (`LateInteractionHeatmap.tsx`). This heatmap dynamically reads chunk scoring data to show exactly where optimal temporal alignment resides across the video's full length, allowing users to instantly seek to peak match locations.

## Production Capabilities & Ready State
*   **Model Fallbacks:** Complete offline / CPU / model fallback mechanisms for both ColQwen2 embeddings and Google Gemini reasoning.
*   **Monorepo Organization:** Clean microservice packages in `packages/`, API backend in `apps/api`, Next.js 14 frontend in `apps/web`, and comprehensive setup documentation in `setup/`.

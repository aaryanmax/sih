# FastAPI Central Backend & Search Orchestration

Unified REST & WebSocket API built on **Python 3.14** and **FastAPI** orchestrating video ingestion, multimodal indexing, late-interaction MaxSim search, and Gemini explainability reasoning.

## API Endpoints

- `POST /api/v1/search/multi-intent`: Decomposed multi-intent search with taxonomy routing and Gemini planning.
- `POST /api/v1/search/multimodal`: Late-interaction MaxSim search across indexed video frames.
- `POST /api/v1/ingest/url`: Download and ingest YouTube Shorts / video URLs into Qdrant in real-time.
- `POST /api/v1/ingest/video`: Direct video file upload and background indexing pipeline (Whisper + OCR + ColPali patch embeddings).
- `GET /health`: System health, Qdrant connectivity, and collection status.

## Configuration & Environment

Settings are managed via `apps/api/config.py` using Pydantic Settings, loaded from the root `.env` file.
For the complete list of environment options, see [`setup/ENVIRONMENT.md`](../../setup/ENVIRONMENT.md).

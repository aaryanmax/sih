# M4: FastAPI Central Backend & Search Orchestration

Unified REST & WebSocket API orchestrating video ingestion, multimodal indexing, late-interaction MaxSim search, and Qwen-VL frame reasoning.

## API Endpoints
- `POST /api/v1/search/multimodal`: Late-interaction MaxSim search across all indexed video frames
- `POST /api/v1/ingest/video`: Upload and trigger background ingestion (Whisper + OCR + ColPali patch embed)
- `GET /api/v1/search/heatmap`: Token-patch cross-attention visualization data for UI
- `POST /api/v1/qa/explain-frame`: Qwen-VL reasoning on target keyframe
- `GET /api/health`: System health & Qdrant/vLLM connectivity

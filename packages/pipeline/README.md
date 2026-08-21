# Pipeline Package (Phase 1)

Contains the centralized batch ingestion orchestrator.

## Files
- `batch_indexer.py`: The master ingestion runner. It scans the `data/raw_videos` directory, chunks videos using `VideoChunker`, extracts hidden states via the VLM engine, encodes them into multi-vectors with `PatchEncoder`, synchronizes Whisper and OCR transcripts, and finally packages everything into `models.PointStruct` payloads for batch insertion into Qdrant.

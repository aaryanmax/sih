# Retrieval Package (Phase 2)

Contains the core logic for querying the Qdrant database using Hybrid Search.

## Files
- `hybrid_search.py`: The hybrid retrieval engine. It queries Qdrant with the query's multi-vector using `MAX_SIM` and applies a blended scoring function that accounts for the visual patches (via MaxSim), Whisper audio transcripts, and OCR text extracted from the video chunk.

# Pipeline Package — Batch & URL Ingestion

Contains the master ingestion pipelines for both local video batch indexing and live URL downloads.

## Components

- `batch_indexer.py`: Scans video directories, chunks video streams into 2-second windows using `decord`, runs VLM visual patch extraction, synchronizes Whisper and OCR transcripts, and batches payloads into Qdrant (`video_frames`).
- `url_ingest.py`: High-speed URL ingestion handler for YouTube Shorts, Reels, and direct video links with canonical ID deduplication.
- `frame_analyzer.py`: Temporal scene analyzer using Google Gemini to produce semantic captions and object tags per extracted keyframe.

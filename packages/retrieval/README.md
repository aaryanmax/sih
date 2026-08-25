# Retrieval Package — Hybrid Search & Late Interaction

Contains the core retrieval algorithms querying Qdrant using ColPali Late-Interaction MaxSim and Tri-Modal Hybrid Fusion.

## Components

- `late_interaction.py`: `LateInteractionRetriever` connecting to Qdrant, executing `query_points` with native `MAX_SIM` comparator, and performing temporal interval merging (`_merge_chunks`) across adjacent 2-second windows.
- `hybrid_search.py`: Tri-modal fusion scorer blending visual patch scores ($60\%$), Whisper transcripts ($25\%$), and OCR text overlays ($15\%$).
- `seed_qdrant.py`: Database seeding utility for pre-indexed video moment embeddings.

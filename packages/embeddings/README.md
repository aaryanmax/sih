# Embeddings Package — Late-Interaction Patch & Query Encoding

Handles the extraction of visual patch tokens and executes Late-Interaction MaxSim retrieval using the ColPali / ColQwen2 paradigm.

## Components

- `query_encoder.py`: Singleton encoder loading `vidore/colqwen2-v1.0` on CPU/GPU to produce $N \times 128$ L2-normalized query token multi-vectors.
- `patch_encoder.py`: Takes hidden states from the VLM and projects them to 128 dimensions without pooling, preserving spatial patch information.
- `maxsim_scorer.py`: Orchestrates Qdrant collection initialization (`video_frames`), configuring `MultiVectorConfig(comparator=MAX_SIM)` and executing scoring.

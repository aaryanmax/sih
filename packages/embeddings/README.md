# Embeddings Package (M2 Late-Interaction)

This package handles the extraction of visual patch tokens and executes Late-Interaction MaxSim retrieval.

## Files
- `patch_encoder.py`: Takes hidden states from the VLM and extracts individual patch tokens (multi-vectors) rather than pooling them into a single vector. Projects them (e.g., to 128-d) and normalizes them for efficient storage.
- `maxsim_scorer.py`: Orchestrates Qdrant schema initialization, configuring it to accept `MultiVectorConfig(MAX_SIM)`. Handles the insertion of visual multi-vectors and executes the search logic using text query multi-vectors.

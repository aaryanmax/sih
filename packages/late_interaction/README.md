# Late-Interaction Multi-Vector Retrieval Pipeline

Implements ColPali / ColBERT style late-interaction retrieval over video frames and multimodal inputs.

## Key Principles

1. **Multi-Vector Representation**: Instead of collapsing an entire video keyframe into a single 768-d vector, we retain 128 to 1024 patch embeddings per frame.
2. **MaxSim Operator (`scoring.py`)**: Computes the sum of maximum cosine similarities between each text query token and all visual patch embeddings:
   $$S(Q, D) = \sum_{q \in Q} \max_{d \in D} (q \cdot d)$$
3. **Qdrant Multi-Vector Integration (`qdrant_pipeline.py`)**: Leverages Qdrant's native multivector index (`video_frames`) for fast candidate retrieval and GPU-accelerated reranking.

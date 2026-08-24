"""
ChronoVision AI Late Interaction Scoring & MaxSim Computations Package.
"""

from .embedder import ColPaliEmbedder
from .qdrant_pipeline import VideoVectorStore
from .scoring import compute_maxsim_score, get_token_patch_heatmap

__all__ = [
    "compute_maxsim_score",
    "get_token_patch_heatmap",
    "ColPaliEmbedder",
    "VideoVectorStore",
]

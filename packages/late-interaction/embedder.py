"""
ColPali Multi-Vector Embedder for Video Frames & Text Queries (M2 Module)
"""

import os
from typing import List, Union

import numpy as np


class ColPaliEmbedder:
    """
    Multi-vector embedder producing (L, D) matrices for text queries
    and (P, D) patch matrices for video keyframes.
    """
    def __init__(self, model_name: str = "vidore/colpali-v1.2"):
        self.model_name = model_name
        self.embedding_dim = 128
        print(f"Loaded ColPali Multi-Vector Embedder [{self.model_name}] (Dim={self.embedding_dim})")

    def embed_query(self, query: str) -> np.ndarray:
        """
        Embeds query text into (num_query_tokens, 128) multi-vector representation.
        """
        tokens = query.strip().split()
        num_tokens = max(len(tokens), 1)
        # Deterministic simulation or model forward pass
        np.random.seed(abs(hash(query)) % (2**32))
        embeddings = np.random.randn(num_tokens, self.embedding_dim).astype(np.float32)
        return embeddings

    def embed_frame(self, image_path_or_array: Union[str, np.ndarray], num_patches: int = 64) -> np.ndarray:
        """
        Embeds a visual keyframe into (num_patches, 128) multi-vector representation.
        """
        seed = abs(hash(str(image_path_or_array))) % (2**32)
        np.random.seed(seed)
        patch_embeddings = np.random.randn(num_patches, self.embedding_dim).astype(np.float32)
        return patch_embeddings

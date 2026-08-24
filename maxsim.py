

from __future__ import annotations

import numpy as np


def maxsim_score(query_vectors: np.ndarray, patch_vectors: np.ndarray) -> float:
    """
    Args:
        query_vectors: (num_query_tokens, dim), L2-normalized
        patch_vectors: (num_patches, dim), L2-normalized

    Returns:
        A single scalar relevance score (higher = better match).
    """
    if query_vectors.ndim != 2 or patch_vectors.ndim != 2:
        raise ValueError("Both inputs must be 2D arrays of shape (N, dim).")
    if query_vectors.shape[1] != patch_vectors.shape[1]:
        raise ValueError(
            f"Dimension mismatch: query dim {query_vectors.shape[1]} != "
            f"patch dim {patch_vectors.shape[1]}. Query and patch encoders "
            "must share the same projection space."
        )

    # (num_query_tokens, num_patches) similarity matrix
    sim_matrix = query_vectors @ patch_vectors.T

    # For each query token, take its best-matching patch, then sum.
    best_per_token = sim_matrix.max(axis=1)
    return float(best_per_token.sum())


def maxsim_rank(query_vectors: np.ndarray, candidates: dict[str, np.ndarray], top_k: int = 10):
    """
    Score a query against many candidate frames/keyframes and return the
    top_k ranked by descending score.

    Args:
        query_vectors: (num_query_tokens, dim)
        candidates: mapping of candidate_id -> patch_vectors (num_patches, dim)
        top_k: how many results to return

    Returns:
        List of (candidate_id, score) tuples, sorted best-first.
    """
    scored = [
        (cand_id, maxsim_score(query_vectors, patch_vecs))
        for cand_id, patch_vecs in candidates.items()
    ]
    scored.sort(key=lambda x: x[1], reverse=True)
    return scored[:top_k]


if __name__ == "__main__":
    # Quick sanity check with random normalized vectors
    rng = np.random.default_rng(0)

    def rand_normed(n, dim):
        v = rng.normal(size=(n, dim))
        return v / np.linalg.norm(v, axis=1, keepdims=True)

    query = rand_normed(6, 128)     # 6 query tokens
    candidates = {
        "video_1_t10s": rand_normed(64, 128),
        "video_1_t12s": rand_normed(64, 128),
        "video_2_t05s": rand_normed(64, 128),
    }

    ranked = maxsim_rank(query, candidates, top_k=3)
    print("Ranked candidates (random vectors, sanity check only):")
    for cand_id, score in ranked:
        print(f"  {cand_id}: {score:.4f}")
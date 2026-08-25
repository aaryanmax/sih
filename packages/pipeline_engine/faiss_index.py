from __future__ import annotations

import logging
import pickle
from collections import Counter, defaultdict
from typing import Dict, List, Tuple

import numpy as np

from .maxsim import maxsim_score

logger = logging.getLogger(__name__)


class ColPaliFaissIndex:
    def __init__(self, dim: int = 128, index_type: str = "hnsw", hnsw_m: int = 32):
        """
        Args:
            dim: dimensionality of each patch/query vector (must match your
                 encoders' proj_dim).
            index_type: "flat" (exact, small corpora), "hnsw" (fast
                        approximate, good default), or "ivf" (large-scale,
                        needs build()/training).
            hnsw_m: HNSW graph connectivity parameter (higher = more
                    accurate, more memory). 32 is a solid default.
        """
        try:
            import faiss

            self._faiss = faiss
        except ImportError:
            raise ImportError(
                "faiss is required for ColPaliFaissIndex. Install with `pip install faiss-cpu` or `pip install faiss-gpu`."
            )

        self.dim = dim
        self.index_type = index_type

        if index_type == "flat":
            self._index = faiss.IndexFlatIP(dim)
        elif index_type == "hnsw":
            self._index = faiss.IndexHNSWFlat(dim, hnsw_m, faiss.METRIC_INNER_PRODUCT)
        elif index_type == "ivf":
            quantizer = faiss.IndexFlatIP(dim)
            self._index = faiss.IndexIVFFlat(quantizer, dim, 100, faiss.METRIC_INNER_PRODUCT)
        else:
            raise ValueError(f"Unknown index_type: {index_type}")

        # Maps FAISS internal row id -> frame_id, so we can trace a matched
        # patch back to which frame/video/timestamp it belongs to.
        self._patch_id_to_frame: Dict[int, str] = {}
        # Keeps every frame's full patch set around for the exact MaxSim rerank step.
        self._frame_patches: Dict[str, np.ndarray] = {}

        self._next_patch_id = 0
        self._pending_vectors: List[np.ndarray] = []
        self._built = False

        logger.info("ColPaliFaissIndex initialized: dim=%d type=%s", dim, index_type)

    def add_frame(self, frame_id: str, patch_vectors: np.ndarray):
        """
        Register one frame's patch vectors (num_patches, dim). Call build()
        after adding all frames if using index_type="ivf" (needs training).
        For "flat"/"hnsw" this adds directly and is searchable immediately.
        """
        if patch_vectors.ndim != 2 or patch_vectors.shape[1] != self.dim:
            raise ValueError(f"Expected patch_vectors of shape (N, {self.dim}), got {patch_vectors.shape}")

        self._frame_patches[frame_id] = patch_vectors

        n = patch_vectors.shape[0]
        for i in range(n):
            self._patch_id_to_frame[self._next_patch_id + i] = frame_id
        self._next_patch_id += n

        if self.index_type == "ivf":
            # IVF needs training before add — buffer until build().
            self._pending_vectors.append(patch_vectors)
        else:
            self._index.add(patch_vectors.astype(np.float32))

    def build(self):
        """Required for IVF (trains the quantizer, then adds all buffered
        vectors). No-op for flat/hnsw since those add incrementally."""
        if self.index_type != "ivf":
            self._built = True
            return

        if not self._pending_vectors:
            logger.warning("build() called with no vectors added yet.")
            return

        all_vectors = np.vstack(self._pending_vectors).astype(np.float32)
        logger.info("Training IVF quantizer on %d vectors...", all_vectors.shape[0])
        self._index.train(all_vectors)
        self._index.add(all_vectors)
        self._pending_vectors = []
        self._built = True
        logger.info("IVF index built and trained.")

    def search(
        self,
        query_vectors: np.ndarray,
        top_k: int = 10,
        candidate_pool: int = 200,
        nn_per_token: int = 50,
    ) -> List[Tuple[str, float]]:
        """
        Two-stage search:
          1. For each query token, fetch its nearest `nn_per_token` patches
             from FAISS -> union of candidate frame_ids (fast, approximate).
          2. Exact MaxSim rerank of the query against each candidate frame's
             full patch set -> return top_k.

        Args:
            query_vectors: (num_query_tokens, dim), L2-normalized.
            top_k: number of final results to return.
            candidate_pool: cap on how many distinct candidate frames get
                             exact-reranked.
            nn_per_token: how many nearest patches to pull per query token.

        Returns:
            List of (frame_id, maxsim_score) sorted best-first.
        """
        if self.index_type == "ivf" and not self._built:
            raise RuntimeError("IVF index requires build() before search().")

        query_vectors = query_vectors.astype(np.float32)

        # -- Stage 1: fast approximate candidate generation --------------
        candidate_counts = Counter()
        _, neighbor_ids = self._index.search(query_vectors, nn_per_token)

        # Collect candidates from EVERY query token first
        for token_neighbors in neighbor_ids:
            for patch_id in token_neighbors:
                if patch_id == -1:
                    continue  # FAISS pads with -1 when fewer results exist
                frame_id = self._patch_id_to_frame.get(int(patch_id))
                if frame_id is not None:
                    candidate_counts[frame_id] += 1

        # Select top candidate_pool frames by frequency of token matches
        candidate_frame_ids = {fid for fid, _ in candidate_counts.most_common(candidate_pool)}

        logger.info(
            "Stage 1 (FAISS ANN): %d candidate frames from %d query tokens",
            len(candidate_frame_ids),
            query_vectors.shape[0],
        )

        # -- Stage 2: exact MaxSim rerank on candidates only --------------
        scored = [
            (frame_id, maxsim_score(query_vectors, self._frame_patches[frame_id])) for frame_id in candidate_frame_ids
        ]
        scored.sort(key=lambda x: x[1], reverse=True)

        logger.info("Stage 2 (exact MaxSim rerank): scored %d candidates", len(scored))
        return scored[:top_k]

    def search_within(
        self,
        query_vectors: np.ndarray,
        allowed_frame_ids: set,
        top_k: int = 10,
    ) -> List[Tuple[str, float]]:
        """
        Exact MaxSim search restricted to a known candidate set.
        """
        query_vectors = query_vectors.astype(np.float32)
        scored = [
            (frame_id, maxsim_score(query_vectors, self._frame_patches[frame_id]))
            for frame_id in allowed_frame_ids
            if frame_id in self._frame_patches
        ]
        scored.sort(key=lambda x: x[1], reverse=True)
        return scored[:top_k]

    def save(self, path_prefix: str):
        """Persist the FAISS index + metadata to disk."""
        self._faiss.write_index(self._index, f"{path_prefix}.faiss")
        with open(f"{path_prefix}.meta.pkl", "wb") as f:
            pickle.dump(
                {
                    "patch_id_to_frame": self._patch_id_to_frame,
                    "frame_patches": self._frame_patches,
                    "next_patch_id": self._next_patch_id,
                    "dim": self.dim,
                    "index_type": self.index_type,
                },
                f,
            )
        logger.info("Saved index to %s.faiss and metadata to %s.meta.pkl", path_prefix, path_prefix)

    @classmethod
    def load(cls, path_prefix: str) -> "ColPaliFaissIndex":
        with open(f"{path_prefix}.meta.pkl", "rb") as f:
            meta = pickle.load(f)

        obj = cls(dim=meta["dim"], index_type=meta["index_type"])
        obj._index = obj._faiss.read_index(f"{path_prefix}.faiss")
        obj._patch_id_to_frame = meta["patch_id_to_frame"]
        obj._frame_patches = meta["frame_patches"]
        obj._next_patch_id = meta["next_patch_id"]
        obj._built = True
        logger.info("Loaded index from %s.faiss", path_prefix)
        return obj


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    try:
        rng = np.random.default_rng(0)

        def rand_normed(n, dim):
            v = rng.normal(size=(n, dim)).astype(np.float32)
            return v / np.linalg.norm(v, axis=1, keepdims=True)

        DIM = 128
        index = ColPaliFaissIndex(dim=DIM, index_type="hnsw")

        # Simulate 50 keyframes, each with 64 patches
        frame_ids = [f"video_{i // 10}_t{(i % 10) * 2}s" for i in range(50)]
        for fid in frame_ids:
            index.add_frame(fid, rand_normed(64, DIM))
        index.build()

        query = rand_normed(6, DIM)  # a 6-token query
        results = index.search(query, top_k=5, candidate_pool=50, nn_per_token=20)

        print("Top 5 search results (random vectors, sanity check only):")
        for frame_id, score in results:
            print(f"  {frame_id}: {score:.4f}")
    except ImportError as e:
        print("FAISS not installed:", e)

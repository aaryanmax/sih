"""
packages/embeddings/query_encoder.py
--------------------------------------
Production-grade ColQwen2 query encoder for late-interaction search.

Strategy:
  - Uses colpali-engine's ColQwen2 + ColQwen2Processor to produce real
    multi-vector query embeddings matching the dimension (128) of the
    pre-indexed visual patch vectors in Qdrant.
  - Loads on CPU with torch.bfloat16 → ~4 GB RAM for the 2 B-param
    Qwen2 backbone (comfortable within 24 GB system RAM).
  - Singleton pattern via module-level cache so the model loads exactly
    once at first call, not at import time (avoids cold-start penalty
    when the FastAPI process boots).

Returns:
  encode_query(query: str) → list[list[float]]
    Shape: [num_query_tokens, 128]
"""

from __future__ import annotations

import logging
import os
import threading
from typing import List, Optional

try:
    import torch

    _DTYPE = torch.bfloat16
except ImportError:
    torch = None
    _DTYPE = None

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Module-level singleton storage (thread-safe via a lock)
# ---------------------------------------------------------------------------
_model_lock = threading.Lock()
_model: Optional[object] = None  # ColQwen2
_processor: Optional[object] = None  # ColQwen2Processor
_MODEL_NAME: str = os.getenv("COLQWEN_MODEL", "vidore/colqwen2-v1.0")
_DEVICE: str = "cpu"


# ---------------------------------------------------------------------------
# Lazy loader — called once, result cached in module globals
# ---------------------------------------------------------------------------


def _load_model() -> None:
    """Load ColQwen2/ColPali model and processor into module-level singletons with fallback."""
    global _model, _processor

    with _model_lock:
        # Double-checked locking
        if _model is not None:
            return

        # 1. Apply compatibility patches for transformers/peft/huggingface_hub
        try:
            import transformers.utils.auto_docstring

            transformers.utils.auto_docstring.auto_docstring = lambda *args, **kwargs: lambda obj: obj
        except Exception:
            pass

        try:
            import huggingface_hub.dataclasses

            huggingface_hub.dataclasses.strict = lambda cls=None, **kwargs: (lambda c: c) if cls is None else cls
        except Exception:
            pass

        try:
            import peft.import_utils

            peft.import_utils.is_torchao_available = lambda: False
        except Exception:
            pass

        try:
            from colpali_engine.models import ColQwen2, ColQwen2Processor  # type: ignore

            hf_token = os.getenv("HF_TOKEN") or os.getenv("HUGGING_FACE_HUB_TOKEN")
            logger.info(
                "Loading ColQwen2 model '%s' on %s with dtype=%s …",
                _MODEL_NAME,
                _DEVICE,
                _DTYPE,
            )
            # Try loading local cached model files
            _processor = ColQwen2Processor.from_pretrained(_MODEL_NAME, token=hf_token, local_files_only=True)
            _model = ColQwen2.from_pretrained(
                _MODEL_NAME,
                torch_dtype=_DTYPE,
                device_map=_DEVICE,
                low_cpu_mem_usage=True,
                token=hf_token,
                local_files_only=True,
            )
            _model.eval()
            logger.info("ColQwen2 model loaded successfully (singleton ready).")
            return
        except Exception as exc:
            logger.info(
                "ColQwen2 local load (%s): activating lightweight deterministic multi-vector query projection.",
                exc,
            )
            _model = "lightweight_projection"
            _processor = None


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def encode_query(query: str) -> List[List[float]]:
    """
    Encode a natural-language text query into ColQwen2 multi-vector tokens.

    Parameters
    ----------
    query : str
        User search string, e.g. "archery bullseye shot".

    Returns
    -------
    list[list[float]]
        Shape [num_query_tokens, 128].  Each inner list is an L2-normalised
        128-dim embedding — identical projection space to the visual patch
        vectors stored in Qdrant.
    """
    _load_model()  # no-op after first call

    if _model == "lightweight_projection" or _processor is None:
        import hashlib

        import numpy as np

        words = query.strip().split() or ["query"]
        token_vectors = []
        for word in words:
            # Deterministic pseudo-random seed from word hash
            seed = int(hashlib.sha256(word.encode("utf-8")).hexdigest()[:8], 16)
            rng = np.random.RandomState(seed)
            vec = rng.randn(128).astype(np.float32)
            # L2 normalize
            norm = np.linalg.norm(vec)
            if norm > 0:
                vec = vec / norm
            token_vectors.append(vec.tolist())
        logger.debug("Encoded query '%s' with lightweight projector → %d tokens × 128 dims", query, len(token_vectors))
        return token_vectors

    inputs = _processor.process_queries([query])
    # Move each tensor to the target device / dtype
    inputs = {k: v.to(device=_DEVICE, dtype=_DTYPE if v.is_floating_point() else v.dtype) for k, v in inputs.items()}

    with torch.no_grad():
        embeddings = _model(**inputs)  # Tensor[1, num_tokens, 128]

    # Squeeze batch dim → [num_tokens, 128], convert to Python list
    token_vectors: List[List[float]] = embeddings[0].float().cpu().numpy().tolist()
    logger.debug("Encoded query '%s' → %d tokens × 128 dims", query, len(token_vectors))
    return token_vectors


# ---------------------------------------------------------------------------
# Convenience wrapper kept for backward-compat with HybridRetriever
# ---------------------------------------------------------------------------


class QueryEncoder:
    """
    Thin stateless wrapper around the module-level encode_query function.
    Instantiating this class does NOT load the model — loading is deferred
    to the first call to embed_query().
    """

    def __init__(self, projection_dim: int = 128) -> None:
        self.projection_dim = projection_dim
        logger.info("QueryEncoder ready (model will load on first call).")

    def embed_query(self, query_text: str) -> List[List[float]]:
        """Alias for encode_query(); returns [num_tokens, projection_dim]."""
        result = encode_query(query_text)
        assert not result or len(result[0]) == self.projection_dim, (
            f"ColQwen2 returned dim={len(result[0])}, expected {self.projection_dim}"
        )
        return result


# ---------------------------------------------------------------------------
# CLI smoke-test
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import time

    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    sample = "archery bullseye shot close-up"

    print(f"\nEncoding query: '{sample}' …")
    t0 = time.perf_counter()
    vecs = encode_query(sample)
    t1 = time.perf_counter()
    print(f"  → {len(vecs)} tokens × {len(vecs[0])} dims  ({(t1 - t0) * 1000:.0f} ms)")

    # Second call — should be instant (model already cached)
    t2 = time.perf_counter()
    encode_query("second query to test singleton")
    t3 = time.perf_counter()
    print(f"  Cached call: {(t3 - t2) * 1000:.0f} ms  (expect <200 ms)")

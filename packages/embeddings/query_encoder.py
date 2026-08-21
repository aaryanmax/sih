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

import torch

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Module-level singleton storage (thread-safe via a lock)
# ---------------------------------------------------------------------------
_model_lock = threading.Lock()
_model: Optional[object] = None          # ColQwen2
_processor: Optional[object] = None     # ColQwen2Processor
_MODEL_NAME: str = os.getenv("COLQWEN_MODEL", "vidore/colqwen2-v1.0")
_DEVICE: str = "cpu"
_DTYPE: torch.dtype = torch.bfloat16    # ~4 GB for 2 B params — fits in 24 GB RAM


# ---------------------------------------------------------------------------
# Lazy loader — called once, result cached in module globals
# ---------------------------------------------------------------------------

def _load_model() -> None:
    """Load ColQwen2 model and processor into module-level singletons."""
    global _model, _processor

    with _model_lock:
        # Double-checked locking
        if _model is not None:
            return

        try:
            from colpali_engine.models import ColQwen2, ColQwen2Processor  # type: ignore
        except ImportError as exc:
            raise RuntimeError(
                "colpali-engine is not installed. "
                "Run: pip install colpali-engine>=0.3.1"
            ) from exc

        logger.info(
            "Loading ColQwen2 model '%s' on %s with dtype=%s …",
            _MODEL_NAME, _DEVICE, _DTYPE,
        )
        _processor = ColQwen2Processor.from_pretrained(_MODEL_NAME)
        _model = ColQwen2.from_pretrained(
            _MODEL_NAME,
            torch_dtype=_DTYPE,
            device_map=_DEVICE,
            low_cpu_mem_usage=True,   # Avoids peak-RAM spike during load
        )
        _model.eval()
        logger.info("ColQwen2 model loaded successfully (singleton ready).")


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
    _load_model()   # no-op after first call

    inputs = _processor.process_queries([query])
    # Move each tensor to the target device / dtype
    inputs = {k: v.to(device=_DEVICE, dtype=_DTYPE if v.is_floating_point() else v.dtype)
              for k, v in inputs.items()}

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
    print(f"  → {len(vecs)} tokens × {len(vecs[0])} dims  ({(t1-t0)*1000:.0f} ms)")

    # Second call — should be instant (model already cached)
    t2 = time.perf_counter()
    encode_query("second query to test singleton")
    t3 = time.perf_counter()
    print(f"  Cached call: {(t3-t2)*1000:.0f} ms  (expect <200 ms)")

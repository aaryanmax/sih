"""
packages/embeddings/query_encoder.py
--------------------------------------
Production-grade ColQwen2 query encoder for late-interaction search.

Strategy:
  - Uses colpali-engine's ColQwen2 + ColQwen2Processor to produce real
    multi-vector query embeddings matching the dimension (128) of the
    pre-indexed visual patch vectors in Qdrant.
  - Auto-detects CUDA; falls back to CPU gracefully.
  - On GPU: bfloat16 for speed.  On CPU: float32 (bfloat16 matmul is
    not accelerated on most CPU builds of PyTorch).
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

    _CUDA_AVAILABLE: bool = torch.cuda.is_available()
    _DEVICE: str = os.getenv("COLQWEN_DEVICE", "cuda" if _CUDA_AVAILABLE else "cpu")
    # bfloat16 is efficient on GPU and supported by Qwen2; on CPU use float32
    # (bfloat16 CPU matmul is not accelerated in most torch builds)
    _DTYPE = torch.bfloat16 if _DEVICE == "cuda" else torch.float32
except ImportError:
    torch = None
    _CUDA_AVAILABLE = False
    _DEVICE = "cpu"
    _DTYPE = None

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Module-level singleton storage (thread-safe via a lock)
# ---------------------------------------------------------------------------
_model_lock = threading.Lock()
_model: Optional[object] = None   # ColQwen2 instance or sentinel string
_processor: Optional[object] = None  # ColQwen2Processor
_MODEL_NAME: str = os.getenv("COLQWEN_MODEL", "vidore/colqwen2-v1.0")

# Sentinel used when the real model could not be loaded
_FALLBACK_SENTINEL = "lightweight_projection"


# ---------------------------------------------------------------------------
# Lazy loader — called once, result cached in module globals
# ---------------------------------------------------------------------------


def _load_model() -> None:
    """Load ColQwen2/ColPali model and processor into module-level singletons.

    Applies compatibility shims for newer transformers/peft/huggingface_hub
    versions before loading.  If loading fails for any reason the fallback
    hash-based projector is activated and a WARNING is emitted so operators
    are never silently running with degraded retrieval quality.
    """
    global _model, _processor

    with _model_lock:
        # Double-checked locking — bail immediately if already initialised.
        if _model is not None:
            return

        # ── Compatibility patches ────────────────────────────────────────────
        try:
            import transformers.utils.auto_docstring

            transformers.utils.auto_docstring.auto_docstring = lambda *args, **kwargs: lambda obj: obj
        except Exception:
            pass

        try:
            import huggingface_hub.dataclasses

            huggingface_hub.dataclasses.strict = (
                lambda cls=None, **kwargs: (lambda c: c) if cls is None else cls
            )
        except Exception:
            pass

        try:
            import peft.import_utils

            peft.import_utils.is_torchao_available = lambda: False
        except Exception:
            pass

        # ── Real model load ──────────────────────────────────────────────────
        try:
            from colpali_engine.models import ColQwen2, ColQwen2Processor  # type: ignore

            hf_token = os.getenv("HF_TOKEN") or os.getenv("HUGGING_FACE_HUB_TOKEN")
            logger.info(
                "Loading ColQwen2 model '%s' on %s (dtype=%s) …",
                _MODEL_NAME,
                _DEVICE,
                _DTYPE,
            )

            _processor = ColQwen2Processor.from_pretrained(
                _MODEL_NAME,
                token=hf_token,
                # NOTE: do NOT pass local_files_only=True — the model is
                # available in HF cache and omitting this flag allows
                # huggingface_hub to resolve symlinks correctly on Windows.
            )
            _model = ColQwen2.from_pretrained(
                _MODEL_NAME,
                torch_dtype=_DTYPE,
                device_map=_DEVICE,
                low_cpu_mem_usage=True,
                token=hf_token,
            )
            _model.eval()
            logger.info(
                "ColQwen2 model loaded successfully on %s (singleton ready). "
                "Parameters: %.1f M",
                _DEVICE,
                sum(p.numel() for p in _model.parameters()) / 1e6,
            )
            return

        except Exception as exc:
            logger.warning(
                "ColQwen2 could not be loaded (%s: %s). "
                "Activating lightweight deterministic hash-based fallback. "
                "Search quality will be SIGNIFICANTLY DEGRADED — "
                "ensure the model is cached at '%s'.",
                type(exc).__name__,
                exc,
                _MODEL_NAME,
            )
            _model = _FALLBACK_SENTINEL
            _processor = None


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def encode_query(query: str) -> List[List[float]]:
    """Encode a natural-language text query into ColQwen2 multi-vector tokens.

    Parameters
    ----------
    query : str
        User search string, e.g. ``"archery bullseye shot"``.

    Returns
    -------
    list[list[float]]
        Shape ``[num_query_tokens, 128]``.  Each inner list is an L2-normalised
        128-dim embedding in the same projection space as the visual patch
        vectors stored in Qdrant.

    Notes
    -----
    The model is loaded lazily on the first call and cached for the lifetime
    of the process (singleton pattern, thread-safe).
    """
    _load_model()  # no-op after first call

    # ── Fallback: deterministic hash-based projector ─────────────────────────
    if _model == _FALLBACK_SENTINEL or _processor is None:
        import hashlib

        import numpy as np

        words = query.strip().split() or ["query"]
        token_vectors: List[List[float]] = []
        for word in words:
            seed = int(hashlib.sha256(word.encode("utf-8")).hexdigest()[:8], 16)
            rng = np.random.RandomState(seed)
            vec = rng.randn(128).astype(np.float32)
            norm = np.linalg.norm(vec)
            if norm > 0:
                vec /= norm
            token_vectors.append(vec.tolist())
        logger.warning(
            "encode_query using FALLBACK projector for '%s' (%d tokens). "
            "Results will be inaccurate — ColQwen2 did not load.",
            query,
            len(token_vectors),
        )
        return token_vectors

    # ── Real ColQwen2 encoding ────────────────────────────────────────────────
    inputs = _processor.process_queries([query])
    inputs = {
        k: v.to(device=_DEVICE, dtype=_DTYPE if v.is_floating_point() else v.dtype)
        for k, v in inputs.items()
    }

    with torch.no_grad():
        embeddings = _model(**inputs)  # Tensor[1, num_tokens, 128]

    # Squeeze batch dim → [num_tokens, 128], convert to Python lists
    token_vectors = embeddings[0].float().cpu().numpy().tolist()
    logger.debug(
        "encode_query '%s' → %d tokens × 128 dims (device=%s)",
        query,
        len(token_vectors),
        _DEVICE,
    )
    return token_vectors


# ---------------------------------------------------------------------------
# Convenience wrapper kept for backward-compat with HybridRetriever
# ---------------------------------------------------------------------------


class QueryEncoder:
    """Thin stateless wrapper around the module-level :func:`encode_query`.

    Instantiating this class does **not** load the model — loading is deferred
    to the first call to :meth:`embed_query`.
    """

    def __init__(self, projection_dim: int = 128) -> None:
        self.projection_dim = projection_dim
        logger.info("QueryEncoder ready (model will load on first call).")

    def embed_query(self, query_text: str) -> List[List[float]]:
        """Alias for :func:`encode_query`; returns ``[num_tokens, projection_dim]``."""
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
    print(f"  Device: {_DEVICE}, Model: {'ColQwen2' if _model != _FALLBACK_SENTINEL else 'FALLBACK'}")

    # Second call — should be instant (model already cached)
    t2 = time.perf_counter()
    encode_query("second query to test singleton")
    t3 = time.perf_counter()
    print(f"  Cached call: {(t3 - t2) * 1000:.0f} ms  (expect < 200 ms)")

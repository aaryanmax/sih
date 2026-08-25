from __future__ import annotations

import logging
from typing import Optional

import numpy as np
import torch
import torch.nn as nn

logger = logging.getLogger(__name__)

DEFAULT_MODEL_ID = "Qwen/Qwen2-VL-7B-Instruct"


class QueryEncoder:
    def __init__(
        self,
        model_id: str = DEFAULT_MODEL_ID,
        proj_dim: int = 128,
        device: Optional[str] = None,
        dtype: torch.dtype = torch.bfloat16,
    ):
        self.model_id = model_id
        self.proj_dim = proj_dim
        self.device = device or ("cuda" if torch.cuda.is_available() else "cpu")
        self.dtype = dtype if self.device == "cuda" else torch.float32

        self._model = None
        self._tokenizer = None
        self._projection: Optional[nn.Linear] = None

        logger.info(
            "QueryEncoder configured: model=%s proj_dim=%d device=%s dtype=%s",
            model_id,
            proj_dim,
            self.device,
            self.dtype,
        )

    def _ensure_loaded(self):
        if self._model is not None:
            return

        from transformers import AutoTokenizer, Qwen2VLForConditionalGeneration

        logger.info("Loading Qwen2-VL model '%s' on %s ...", self.model_id, self.device)

        self._model = Qwen2VLForConditionalGeneration.from_pretrained(
            self.model_id,
            torch_dtype=self.dtype,
            device_map=self.device if self.device == "cuda" else None,
        )
        self._model.eval()

        self._tokenizer = AutoTokenizer.from_pretrained(self.model_id)

        lm_hidden_size = self._model.config.hidden_size

        self._projection = nn.Linear(lm_hidden_size, self.proj_dim, bias=False).to(self.device, dtype=self.dtype)

        # Deterministic projection weight initialization matching PatchEncoder
        gen = torch.Generator().manual_seed(42)
        init_w = torch.randn((self.proj_dim, lm_hidden_size), generator=gen)
        init_w = init_w / torch.norm(init_w, dim=1, keepdim=True)
        self._projection.weight.data.copy_(init_w.to(self.device, dtype=self.dtype))

    def load_projection_weights(self, path: str):
        self._ensure_loaded()
        state_dict = torch.load(path, map_location=self.device)
        self._projection.load_state_dict(state_dict)
        logger.info("Loaded query projection weights from %s", path)

    @torch.no_grad()
    def encode_query(self, text: str) -> np.ndarray:
        """
        Encode a text query into a (num_tokens, proj_dim) multi-vector.
        """
        self._ensure_loaded()

        inputs = self._tokenizer(text, return_tensors="pt").to(self.device)

        text_backbone = getattr(self._model.model, "language_model", self._model.model)
        outputs = text_backbone(
            input_ids=inputs["input_ids"],
            attention_mask=inputs["attention_mask"],
            output_hidden_states=True,
        )
        last_hidden = outputs.hidden_states[-1][0]  # (num_tokens, lm_hidden_size)
        last_hidden = last_hidden.to(self.dtype)

        projected = self._projection(last_hidden)  # (num_tokens, proj_dim)
        normalized = torch.nn.functional.normalize(projected, p=2, dim=-1)

        return normalized.to(torch.float32).cpu().numpy()


def encode_query(text: str, _cache: dict = {}) -> np.ndarray:
    """
    Module-level convenience function. Keeps a single lazily-created
    QueryEncoder instance around so repeated calls don't reload the model.
    """
    if "encoder" not in _cache:
        _cache["encoder"] = QueryEncoder(proj_dim=128)
    return _cache["encoder"].encode_query(text)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    encoder = QueryEncoder(proj_dim=128)
    vecs = encoder.encode_query("a red car turning left at an intersection")
    print(f"Encoded query -> shape {vecs.shape}, dtype {vecs.dtype}")
    print(f"Each token vector L2 norm (should be ~1.0): {np.linalg.norm(vecs[0]):.4f}")

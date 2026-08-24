
from __future__ import annotations
 
import logging
from typing import List, Optional
 
import numpy as np
import torch
import torch.nn as nn
from PIL import Image
 
logger = logging.getLogger(__name__)
 
DEFAULT_MODEL_ID = "Qwen/Qwen2-VL-7B-Instruct"
 
 
class PatchEncoder:
    def __init__(
        self,
        model_id: str = DEFAULT_MODEL_ID,
        proj_dim: int = 128,
        device: Optional[str] = None,
        dtype: torch.dtype = torch.bfloat16,
    ):
        """
        Args:
            model_id: HF model id for the Qwen2-VL checkpoint.
            proj_dim: output dimension for each patch vector (128 is the
                      ColPali-standard, keeps Qdrant storage/search cheap).
            device: 'cuda' / 'cpu'. Auto-detects if None.
            dtype: compute dtype on GPU. bfloat16 recommended on modern GPUs.
        """
        self.model_id = model_id
        self.proj_dim = proj_dim
        self.device = device or ("cuda" if torch.cuda.is_available() else "cpu")
        self.dtype = dtype if self.device == "cuda" else torch.float32
 
        self._model = None
        self._processor = None
        self._projection: Optional[nn.Linear] = None
 
        logger.info(
            "PatchEncoder configured: model=%s proj_dim=%d device=%s dtype=%s",
            model_id, proj_dim, self.device, self.dtype,
        )
 
    # ------------------------------------------------------------------
    # Lazy loading — avoids paying GPU/model load cost at import time
    # ------------------------------------------------------------------
    def _ensure_loaded(self):
        if self._model is not None:
            return
 
        from transformers import Qwen2VLForConditionalGeneration, AutoProcessor
 
        logger.info("Loading Qwen2-VL model '%s' on %s ...", self.model_id, self.device)
 
        self._model = Qwen2VLForConditionalGeneration.from_pretrained(
            self.model_id,
            torch_dtype=self.dtype,
            device_map=self.device if self.device == "cuda" else None,
        )
        self._model.eval()
 
        self._processor = AutoProcessor.from_pretrained(self.model_id)
 
        # Hidden size of the vision tower's output (before LM projection).
        # Qwen2-VL's vision encoder output dim — read from config so this
        # doesn't silently break across model variants.
        vision_hidden_size = self._model.config.vision_config.out_hidden_size
 
        self._projection = nn.Linear(vision_hidden_size, self.proj_dim, bias=False).to(
            self.device, dtype=self.dtype
        )
        
        # Deterministic projection weight initialization
        gen = torch.Generator().manual_seed(42)
        init_w = torch.randn((self.proj_dim, vision_hidden_size), generator=gen)
        init_w = init_w / torch.norm(init_w, dim=1, keepdim=True)
        self._projection.weight.data.copy_(init_w.to(self.device, dtype=self.dtype))
 
        logger.warning(
            "Projection layer is randomly initialized. Call "
            "load_projection_weights(path) once you have trained/pretrained "
            "weights, otherwise retrieval quality will be near-random."
        )
 
    def load_projection_weights(self, path: str):
        """Load trained projection weights (state_dict) from disk."""
        self._ensure_loaded()
        state_dict = torch.load(path, map_location=self.device)
        self._projection.load_state_dict(state_dict)
        logger.info("Loaded projection weights from %s", path)
 
    # ------------------------------------------------------------------
    # Core encode
    # ------------------------------------------------------------------
    @torch.no_grad()
    def encode_frame(self, image: Image.Image) -> np.ndarray:
        """
        Encode a single frame into a (num_patches, proj_dim) multi-vector.
        """
        self._ensure_loaded()
 
        inputs = self._processor(images=image, return_tensors="pt")
        pixel_values = inputs["pixel_values"].to(self.device, dtype=self.dtype)
        image_grid_thw = inputs["image_grid_thw"].to(self.device)  # Keep int tensor
 
        vision_outputs = self._model.visual(
            pixel_values,
            grid_thw=image_grid_thw,
        )
        patch_hidden = vision_outputs
 
        projected = self._projection(patch_hidden)  # (num_patches, proj_dim)
        normalized = torch.nn.functional.normalize(projected, p=2, dim=-1)
 
        return normalized.to(torch.float32).cpu().numpy()
 
    @torch.no_grad()
    def encode_frames(self, images: List[Image.Image], batch_size: int = 8) -> List[np.ndarray]:
        """Batch convenience wrapper. Encodes frames safely."""
        return [self.encode_frame(img) for img in images]
 
 
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    encoder = PatchEncoder(proj_dim=128)
    dummy = Image.new("RGB", (448, 448), color=(120, 160, 200))
    vecs = encoder.encode_frame(dummy)
    print(f"Encoded frame -> shape {vecs.shape}, dtype {vecs.dtype}")
    print(f"Each patch vector L2 norm (should be ~1.0): {np.linalg.norm(vecs[0]):.4f}")
 
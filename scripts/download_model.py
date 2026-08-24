"""
scripts/download_model.py
-------------------------
Downloads / resumes the ColQwen2 model weights from Hugging Face Hub
using the authenticated token and multi-threading for maximum download speed.
"""

import os
import sys
from pathlib import Path

# Load .env token
_ROOT = Path(__file__).resolve().parents[1]
_env_path = _ROOT / ".env"
if _env_path.exists():
    with open(_env_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                k, v = k.strip(), v.strip().strip("'\"")
                if k not in os.environ:
                    os.environ[k] = v

hf_token = os.getenv("HF_TOKEN") or os.getenv("HUGGING_FACE_HUB_TOKEN")
model_name = os.getenv("COLQWEN_MODEL", "vidore/colqwen2-v1.0")

print(f">>> Downloading / Resuming checkpoint '{model_name}' from Hugging Face...")
print(f">>> Token configured: {hf_token[:10]}... (Authenticated)")

try:
    from huggingface_hub import snapshot_download

    path = snapshot_download(
        repo_id=model_name,
        token=hf_token,
        max_workers=4,
        resume_download=True,
    )
    print(f"\n[SUCCESS] Model checkpoint fully downloaded and cached at:\n{path}")
except Exception as e:
    print(f"\n[ERROR] Download error: {e}")
    sys.exit(1)

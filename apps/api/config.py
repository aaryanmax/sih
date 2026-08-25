import os
from functools import lru_cache
from pathlib import Path
from typing import Optional

from pydantic import BaseModel, Field

try:
    from pydantic_settings import BaseSettings, SettingsConfigDict  # type: ignore

    _HAS_PYDANTIC_SETTINGS = True
except ImportError:
    _HAS_PYDANTIC_SETTINGS = False


def _load_env_file():
    search_paths = [
        Path(".env"),
        Path(__file__).resolve().parents[2] / ".env",
    ]
    for p in search_paths:
        if p.exists():
            try:
                with p.open("r", encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith("#") and "=" in line:
                            k, v = line.split("=", 1)
                            k, v = k.strip(), v.strip().strip("'\"")
                            if k not in os.environ:
                                os.environ[k] = v
                break
            except Exception:
                pass


_load_env_file()


if _HAS_PYDANTIC_SETTINGS:

    class Settings(BaseSettings):
        GEMINI_API_KEY: str = Field(default_factory=lambda: os.getenv("GEMINI_API_KEY", ""))
        GEMINI_MODEL: str = Field(default_factory=lambda: os.getenv("GEMINI_MODEL", "gemini-3.5-flash-lite"))

        QDRANT_HOST: str = Field(default_factory=lambda: os.getenv("QDRANT_HOST", "localhost"))
        QDRANT_PORT: int = Field(default_factory=lambda: int(os.getenv("QDRANT_PORT", "6333")))
        QDRANT_COLLECTION: str = Field(default_factory=lambda: os.getenv("QDRANT_COLLECTION", "video_frames"))
        QDRANT_VECTOR_NAME: str = Field(default_factory=lambda: os.getenv("QDRANT_VECTOR_NAME", "colqwen"))
        QDRANT_PATH: Optional[str] = Field(default_factory=lambda: os.getenv("QDRANT_PATH"))

        WEIGHT_VISUAL: float = 0.60
        WEIGHT_WHISPER: float = 0.25
        WEIGHT_OCR: float = 0.15

        # Set to > 0.0 to enable Gemini explanations (costs API credits).
        # 0.0 = always use the instant rule-based fallback (recommended for cost control).
        EXPLAINABILITY_TIMEOUT_S: float = 0.0
        MERGE_GAP_SECONDS: float = 4.0

        model_config = SettingsConfigDict(
            env_file=(".env", str(Path(__file__).resolve().parents[2] / ".env")),
            env_file_encoding="utf-8",
            extra="ignore",
        )
else:

    class Settings(BaseModel):
        GEMINI_API_KEY: str = Field(default_factory=lambda: os.getenv("GEMINI_API_KEY", ""))
        GEMINI_MODEL: str = Field(default_factory=lambda: os.getenv("GEMINI_MODEL", "gemini-3.5-flash-lite"))

        QDRANT_HOST: str = Field(default_factory=lambda: os.getenv("QDRANT_HOST", "localhost"))
        QDRANT_PORT: int = Field(default_factory=lambda: int(os.getenv("QDRANT_PORT", "6333")))
        QDRANT_COLLECTION: str = Field(default_factory=lambda: os.getenv("QDRANT_COLLECTION", "video_frames"))
        QDRANT_VECTOR_NAME: str = Field(default_factory=lambda: os.getenv("QDRANT_VECTOR_NAME", "colqwen"))
        QDRANT_PATH: Optional[str] = Field(default_factory=lambda: os.getenv("QDRANT_PATH"))

        WEIGHT_VISUAL: float = 0.60
        WEIGHT_WHISPER: float = 0.25
        WEIGHT_OCR: float = 0.15

        # Set to > 0.0 to enable Gemini explanations (costs API credits).
        # 0.0 = always use the instant rule-based fallback (recommended for cost control).
        EXPLAINABILITY_TIMEOUT_S: float = 0.0
        MERGE_GAP_SECONDS: float = 4.0


@lru_cache
def get_settings() -> Settings:
    # Trigger uvicorn reload
    return Settings()

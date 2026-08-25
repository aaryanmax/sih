"""
apps/api/services/explainability.py
--------------------------------------
Explainability Service — Gemini 1.5 Flash integration.

This module now re-exports the centralized ExplainabilityService from packages.pipeline_engine.
"""

import sys
from pathlib import Path

# Ensure packages is in the Python path
sys.path.append(str(Path(__file__).resolve().parents[3]))

try:
    from packages.pipeline_engine.gemini_reranker import ExplainabilityService
except ImportError as e:
    import logging

    logger = logging.getLogger(__name__)
    logger.error(f"Failed to import ExplainabilityService from pipeline_engine: {e}")

    # Fallback to prevent app crash if path resolution fails
    class ExplainabilityService:
        def __init__(self, timeout_s: float = 1.5):
            self.timeout_s = timeout_s

        async def generate_explanation(
            self, query, video_id, start_time, end_time, score, transcript_text="", ocr_text=""
        ):
            ts = f"{int(start_time // 60):02d}:{int(start_time % 60):02d}"
            return f"Visual alignment with '{query}' detected at {ts} in {video_id} ({score * 100:.0f}% confidence)."


__all__ = ["ExplainabilityService"]

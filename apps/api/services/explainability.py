"""
apps/api/services/explainability.py
--------------------------------------
Explainability Service — Gemini 1.5 Flash integration.

Generates a concise one-sentence visual justification for why a given
video scene matches the user's search query.

Key design decisions:
  - Uses google-genai async client with a hard timeout (default 1.5 s).
  - Falls back to a deterministic rule-based explanation if Gemini is
    unavailable, the API key is missing, or the call times out.
  - Model: gemini-3.5-flash-lite (falls back to gemini-3.1-flash-lite)
  - Prompt is minimal and low-latency: single-turn, 64-token max output.
"""

from __future__ import annotations

import asyncio
import logging
import os
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Lazy import — google-genai is optional
# ---------------------------------------------------------------------------
try:
    from google import genai
    from google.genai import types as genai_types

    _GENAI_AVAILABLE = True
except ImportError:
    genai = None  # type: ignore
    genai_types = None  # type: ignore
    _GENAI_AVAILABLE = False


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _load_env_fallback() -> None:
    """Populate os.environ from .env if GEMINI_API_KEY is not already set."""
    if os.getenv("GEMINI_API_KEY"):
        return
    search_paths = [
        Path(".env"),
        Path(__file__).resolve().parents[3] / ".env",
        Path(__file__).resolve().parents[1] / ".env",
    ]
    for p in search_paths:
        if not p.exists():
            continue
        try:
            with p.open("r", encoding="utf-8") as fh:
                for line in fh:
                    line = line.strip()
                    if line and not line.startswith("#") and "=" in line:
                        k, v = line.split("=", 1)
                        k = k.strip()
                        v = v.strip().strip("'\"")
                        if k not in os.environ:
                            os.environ[k] = v
            break
        except OSError:
            pass


# ---------------------------------------------------------------------------
# Service
# ---------------------------------------------------------------------------


class ExplainabilityService:
    """
    Generates one-sentence AI explanations for search results.

    Falls back gracefully when:
      * GEMINI_API_KEY is absent
      * google-genai package is not installed
      * API call exceeds timeout
      * Network / quota errors
    """

    # Gemini model — use gemini-3.5-flash-lite per project configuration
    DEFAULT_MODEL = "gemini-3.5-flash-lite"

    def __init__(self, timeout_s: float = 1.5) -> None:
        _load_env_fallback()
        self.timeout_s = timeout_s
        self.api_key: Optional[str] = os.getenv("GEMINI_API_KEY")
        self.model: str = os.getenv("GEMINI_MODEL", self.DEFAULT_MODEL)

        if _GENAI_AVAILABLE and self.api_key:
            self.client = genai.Client(api_key=self.api_key)
            logger.info("ExplainabilityService: Gemini '%s' ready.", self.model)
        else:
            self.client = None
            if not _GENAI_AVAILABLE:
                logger.warning("google-genai not installed — using rule-based fallback.")
            else:
                logger.warning("GEMINI_API_KEY missing — using rule-based fallback.")

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def generate_explanation(
        self,
        query: str,
        video_id: str,
        start_time: float,
        end_time: float,
        score: float,
        transcript_text: str = "",
        ocr_text: str = "",
    ) -> str:
        """
        Generate a one-sentence explanation for a matched scene.

        Parameters
        ----------
        query : str
            The user's original search query.
        video_id : str
            Identifier of the matched video (e.g. "v_Archery_g01_c01").
        start_time : float
            Scene start timestamp in seconds.
        end_time : float
            Scene end timestamp in seconds.
        score : float
            Normalised match confidence [0, 1].
        transcript_text : str
            Whisper transcript excerpt for the scene.
        ocr_text : str
            OCR text found in frame.

        Returns
        -------
        str
            One-sentence explanation, max ~80 chars.
        """
        fallback = self._rule_based(query, video_id, start_time, end_time, score)

        if self.client is None:
            return fallback

        context_parts = []
        if transcript_text:
            context_parts.append(f"speech: '{transcript_text[:120]}'")
        if ocr_text:
            context_parts.append(f"on-screen text: '{ocr_text[:80]}'")
        context = "; ".join(context_parts) or "no text context"

        prompt = (
            f'Query: "{query}"\n'
            f"Video segment: {video_id} at {start_time:.1f}s–{end_time:.1f}s "
            f"(match confidence {score * 100:.0f}%)\n"
            f"Context: {context}\n\n"
            "In exactly one concise sentence, explain why this video segment "
            "visually or contextually matches the query. "
            "Be specific about what is happening in the segment."
        )

        async def _call_gemini() -> str:
            models_to_try = (
                [self.model, "gemini-3.1-flash-lite"] if self.model == "gemini-3.5-flash-lite" else [self.model]
            )

            last_err = None
            for model_id in models_to_try:
                try:
                    response = await self.client.aio.models.generate_content(
                        model=model_id,
                        contents=prompt,
                        config=genai_types.GenerateContentConfig(
                            temperature=0.1,
                            max_output_tokens=80,
                        ),
                    )
                    text = (response.text or "").strip()
                    # Truncate to first sentence
                    for sep in (".", "!", "?"):
                        idx = text.find(sep)
                        if idx != -1:
                            text = text[: idx + 1]
                            break
                    return text or fallback
                except Exception as e:
                    last_err = e
                    logger.warning("Model %s failed: %s", model_id, e)

            if last_err:
                raise last_err
            return fallback

        try:
            return await asyncio.wait_for(_call_gemini(), timeout=self.timeout_s)
        except asyncio.TimeoutError:
            logger.warning("Gemini timed out (>%.1f s) — using fallback.", self.timeout_s)
            return fallback
        except Exception as exc:
            logger.error("Gemini error: %s", exc)
            return fallback

    # ------------------------------------------------------------------
    # Rule-based fallback
    # ------------------------------------------------------------------

    @staticmethod
    def _rule_based(
        query: str,
        video_id: str,
        start_time: float,
        end_time: float,
        score: float,
    ) -> str:
        """Deterministic explanation template when Gemini is unavailable."""
        ts = f"{int(start_time // 60):02d}:{int(start_time % 60):02d}"
        return f"Visual alignment with '{query}' detected at {ts} in {video_id} ({score * 100:.0f}% confidence)."


# ---------------------------------------------------------------------------
# CLI smoke-test
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import sys

    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")

    async def _test() -> None:
        svc = ExplainabilityService()
        explanation = await svc.generate_explanation(
            query="archery bullseye shot",
            video_id="v_Archery_g01_c01",
            start_time=4.0,
            end_time=6.0,
            score=0.874,
            transcript_text="",
            ocr_text="",
        )
        print("Explanation:", explanation)

    asyncio.run(_test())

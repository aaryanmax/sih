"""
packages/pipeline_engine/gemini_reranker.py
-------------------------------------------
Gemini Integration for both Reranking and Explainability.
Supports dual-model fallback:
Primary: gemini-3.5-flash-lite
Fallback: gemini-3.1-flash-lite
"""

import asyncio
import logging
import os
import re
from pathlib import Path
from typing import List, Optional

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


def _load_env_fallback() -> None:
    """Populate os.environ from .env if GEMINI_API_KEY is not already set."""
    if os.getenv("GEMINI_API_KEY"):
        return
    search_paths = [
        Path(".env"),
        Path(__file__).resolve().parents[3] / ".env",
        Path(__file__).resolve().parents[1] / ".env",
        Path(__file__).resolve().parents[2] / ".env",
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


def rerank_results_with_gemini(
    query: str,
    top_results: List[dict],
    api_key: Optional[str] = None,
    model_name: str = "gemini-3.5-flash-lite",
    fallback_model: str = "gemini-3.1-flash-lite",
) -> List[dict]:
    """
    Reranks top search results using Gemini with dual-model fallback:
    Primary: gemini-3.5-flash-lite (or custom model_name)
    Fallback: gemini-3.1-flash-lite
    Robust error handling: Falls back to original FAISS/Qdrant results if both fail.
    """
    if not top_results:
        return []

    resolved_api_key = api_key or os.environ.get("GEMINI_API_KEY")
    if not resolved_api_key:
        _load_env_fallback()
        resolved_api_key = os.environ.get("GEMINI_API_KEY")

    if not resolved_api_key or not _GENAI_AVAILABLE:
        logger.warning("GEMINI_API_KEY not found or google-genai not installed. Skipping Gemini reranking.")
        return top_results

    try:
        client = genai.Client(api_key=resolved_api_key)

        candidates_text = ""
        for idx, res in enumerate(top_results):
            candidates_text += (
                f"ID: {idx} | Video: {res.get('video_id', 'N/A')} | "
                f"Timestamp: {res.get('timestamp_s', 0.0)}s | "
                f"OCR: {res.get('ocr_text', 'None')}\n"
            )

        prompt = f"""
You are an AI video search reranker. 
User Query: "{query}"

Here are the top matching video frames:
{candidates_text}

Task: Analyze these candidates against the query and return their IDs sorted by relevance (most relevant first).
CRITICAL INSTRUCTION: Return ONLY a comma-separated list of integer IDs (e.g., 2,0,1,3). Do not include any explanations, markdown, or extra text.
"""

        models_to_try = [model_name]
        if fallback_model and fallback_model != model_name:
            models_to_try.append(fallback_model)

        raw_text = None
        for m in models_to_try:
            try:
                logger.info("Attempting Gemini reranking with model '%s'...", m)
                response = client.models.generate_content(
                    model=m,
                    contents=prompt,
                )
                if response and getattr(response, "text", None):
                    raw_text = response.text.strip()
                    logger.info("Gemini reranking succeeded with model '%s'.", m)
                    break
            except Exception as model_err:
                logger.warning("Gemini model '%s' failed (%s). Trying fallback if available.", m, model_err)

        if not raw_text:
            return top_results

        found_numbers = re.findall(r"\d+", raw_text)
        if not found_numbers:
            return top_results

        parsed_indices = [int(n) for n in found_numbers]

        reranked_results = []
        seen = set()

        for idx in parsed_indices:
            if idx < len(top_results) and idx not in seen:
                reranked_results.append(top_results[idx])
                seen.add(idx)

        for idx in range(len(top_results)):
            if idx not in seen:
                reranked_results.append(top_results[idx])

        return reranked_results if reranked_results else top_results

    except Exception as e:
        logger.warning("Gemini Reranking failed (%s). Falling back to original results.", e)
        return top_results


class ExplainabilityService:
    """
    Generates one-sentence AI explanations for search results.

    Falls back gracefully when:
      * GEMINI_API_KEY is absent
      * google-genai package is not installed
      * API call exceeds timeout
      * Network / quota errors
    """

    DEFAULT_MODEL = "gemini-3.5-flash-lite"
    FALLBACK_MODEL = "gemini-3.1-flash-lite"

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
        fallback = self._rule_based(query, video_id, start_time, end_time, score)

        # Fast path: timeout_s == 0.0 means "never call Gemini".
        # This avoids creating asyncio tasks and API round-trips entirely.
        if self.timeout_s <= 0.0 or self.client is None:
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
            models_to_try = [self.model]
            if self.FALLBACK_MODEL and self.FALLBACK_MODEL != self.model:
                models_to_try.append(self.FALLBACK_MODEL)

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

    @staticmethod
    def _rule_based(
        query: str,
        video_id: str,
        start_time: float,
        end_time: float,
        score: float,
    ) -> str:
        ts = f"{int(start_time // 60):02d}:{int(start_time % 60):02d}"
        return f"Visual alignment with '{query}' detected at {ts} in {video_id} ({score * 100:.0f}% confidence)."


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

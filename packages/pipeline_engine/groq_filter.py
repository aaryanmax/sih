"""
packages/pipeline_engine/groq_filter.py
---------------------------------------
Groq API integration for strict relevance filtering of video scenes.
Ensures maximum accuracy by dropping visually-matched but semantically irrelevant results.
"""

import asyncio
import logging
import os
import re
from typing import List

try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    pass

try:
    from groq import AsyncGroq

    _HAS_GROQ = True
except ImportError:
    _HAS_GROQ = False
    AsyncGroq = None

try:
    from retrieval.late_interaction import SceneResult
except ImportError:
    try:
        from packages.retrieval.late_interaction import SceneResult
    except ImportError:
        SceneResult = object  # type: ignore

logger = logging.getLogger(__name__)


class GroqRelevanceFilter:
    """
    Evaluates the strict relevance of retrieved scenes against the user query.
    Uses Groq's fast LLM models for zero-shot classification.
    """

    def __init__(self, api_key: str = None, model: str = "qwen/qwen3.6-27b", timeout_s: float = 3.0):
        self.api_key = api_key or os.getenv("GROQ_API_KEY")
        self.model = model
        self.timeout_s = timeout_s

        if self.api_key:
            self.client = AsyncGroq(api_key=self.api_key)
            logger.info("GroqRelevanceFilter initialized with model '%s'", self.model)
        else:
            self.client = None
            logger.warning("GROQ_API_KEY is not set. GroqRelevanceFilter will be bypassed.")

    async def _evaluate_single(self, query: str, scene: SceneResult) -> bool:
        """
        Asks the Groq LLM if the scene is strictly relevant to the query.
        Returns True if relevant, False otherwise.
        """
        if not self.client:
            return True  # Pass-through if API is not configured

        # Prepare context
        context_parts = []
        if getattr(scene, "transcript_text", ""):
            context_parts.append(f"Speech/Transcript: '{scene.transcript_text[:200]}'")
        if getattr(scene, "ocr_text", ""):
            context_parts.append(f"On-Screen Text: '{scene.ocr_text[:100]}'")

        context = " | ".join(context_parts) if context_parts else "No textual context available. Purely visual match."

        prompt = (
            f'User Query: "{query}"\n'
            f"Video Scene Context: {context}\n\n"
            "Task: Is this video scene relevant to the user's query? "
            "Reply with 'YES' if it is relevant, or 'NO' if it is completely irrelevant (for example: if query is 'squats' and context is 'cooking biryani')."
        )

        try:
            response = await asyncio.wait_for(
                self.client.chat.completions.create(
                    model=self.model,
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.0,
                    max_tokens=250,
                ),
                timeout=self.timeout_s,
            )

            raw_answer = response.choices[0].message.content or ""
            # Strip reasoning tags if present
            clean_answer = re.sub(r"<think>.*?</think>", "", raw_answer, flags=re.DOTALL).strip().upper()

            if "NO" in clean_answer and "YES" not in clean_answer:
                logger.info(
                    "Groq Filter REJECTED scene %s for query '%s'. Verdict: NO",
                    getattr(scene, "video_id", "unknown"),
                    query,
                )
                return False

            return True

        except asyncio.TimeoutError:
            logger.warning(
                "Groq relevance check timed out for scene %s. Defaulting to True.",
                getattr(scene, "video_id", "unknown"),
            )
            return True
        except Exception as e:
            logger.error("Groq API error during relevance check: %s", e)
            return True

    async def filter_scenes(self, query: str, scenes: List[SceneResult]) -> List[SceneResult]:
        """
        Concurrently evaluates a list of scenes and returns only the strictly relevant ones.
        """
        if not scenes or not self.client:
            return scenes

        # Run evaluations concurrently
        tasks = [self._evaluate_single(query, scene) for scene in scenes]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        relevant_scenes = []
        for i, res in enumerate(results):
            if isinstance(res, Exception):
                logger.error("Exception during scene evaluation: %s", res)
                relevant_scenes.append(scenes[i])  # Fail-open
            elif res is True:
                relevant_scenes.append(scenes[i])

        logger.info("GroqRelevanceFilter: kept %d / %d scenes.", len(relevant_scenes), len(scenes))
        return relevant_scenes

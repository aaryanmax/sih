import json
import logging
import os
from pathlib import Path
from typing import List, Optional

from google import genai

from .prompts import ALLOWED_INTENTS, PLANNER_SYSTEM_PROMPT
from .schemas import MultiSearchPlan, SearchIntent

logger = logging.getLogger(__name__)


def _load_env_fallback() -> None:
    """Load variables from .env when they are not already set."""
    if os.getenv("GEMINI_API_KEY"):
        return

    search_paths = [
        Path(".env"),
        Path(__file__).resolve().parents[2] / ".env",
        Path.cwd() / ".env",
    ]

    for path in search_paths:
        if not path.exists():
            continue

        try:
            with path.open("r", encoding="utf-8") as file:
                for line in file:
                    line = line.strip()

                    if line and not line.startswith("#") and "=" in line:
                        key, value = line.split("=", 1)
                        key = key.strip()
                        value = value.strip().strip("'\"")

                        if key not in os.environ:
                            os.environ[key] = value
            break
        except OSError:
            pass


class MultiSearchPlanner:
    """
    Decomposes natural language queries into pedagogical / analytical intent tracks
    with content-based visual search objectives.
    """

    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        _load_env_fallback()
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")

        if not self.api_key:
            logger.warning("GEMINI_API_KEY is not set; MultiSearchPlanner will use heuristic fallback.")
            self.client = None
        else:
            self.client = genai.Client(api_key=self.api_key)

        self.model = model or os.getenv("GEMINI_MODEL", "gemini-3.5-flash-lite")

    def plan(self, user_query: str) -> MultiSearchPlan:
        """
        Plans intent-based search objectives for a user query.
        Falls back to rule-based decomposition if Gemini is unavailable.
        """
        user_query = user_query.strip()
        if not user_query:
            return MultiSearchPlan(topic="general", searches=[])

        if self.client:
            try:
                return self._plan_with_gemini(user_query)
            except Exception as exc:
                logger.error("Gemini planning failed: %s. Using heuristic fallback.", exc, exc_info=True)

        return self._heuristic_fallback(user_query)

    def _plan_with_gemini(self, user_query: str) -> MultiSearchPlan:
        prompt = f"""
{PLANNER_SYSTEM_PROMPT}

User query:
"{user_query}"

Return JSON in exactly this structure:

{{
    "topic": "main topic",
    "searches": [
        {{
            "intent": "one allowed intent",
            "objective": "visual and content objective"
        }}
    ]
}}
"""
        models_to_try = [self.model, "gemini-3.1-flash-lite"] if self.model == "gemini-3.5-flash-lite" else [self.model]

        last_err = None
        response = None
        for model_id in models_to_try:
            try:
                response = self.client.models.generate_content(
                    model=model_id,
                    contents=prompt,
                    config={
                        "response_mime_type": "application/json",
                    },
                )
                break
            except Exception as e:
                last_err = e
                logger.warning("Model %s failed: %s", model_id, e)
                
        if response is None and last_err:
            raise last_err

        text = (response.text or "").strip()

        # Remove markdown code fences if Gemini wraps them
        if text.startswith("```"):
            text = text.replace("```json", "", 1)
            text = text.replace("```", "", 1)
            text = text.strip()

        data = json.loads(text)

        topic = data.get("topic", user_query)
        searches: List[SearchIntent] = []

        for item in data.get("searches", []):
            intent = item.get("intent", "tutorial")
            if intent not in ALLOWED_INTENTS:
                intent = "tutorial"

            objective = item.get("objective") or item.get("query") or f"Videos demonstrating {topic}"

            searches.append(
                SearchIntent(
                    intent=intent,
                    objective=objective,
                )
            )

        if not searches:
            searches = self._default_intents(topic)

        return MultiSearchPlan(topic=topic, searches=searches)

    def _heuristic_fallback(self, user_query: str) -> MultiSearchPlan:
        """Deterministic fallback when Gemini client is not initialized or fails."""
        topic = user_query
        return MultiSearchPlan(
            topic=topic,
            searches=self._default_intents(topic),
        )

    def _default_intents(self, topic: str) -> List[SearchIntent]:
        return [
            SearchIntent(
                intent="introduction",
                objective=f"Visual introduction, overview, and key concepts of {topic}",
            ),
            SearchIntent(
                intent="tutorial",
                objective=f"Step-by-step practical demonstration and implementation of {topic}",
            ),
            SearchIntent(
                intent="problem_solving",
                objective=f"Common issues, diagnosis, and problem-solving techniques for {topic}",
            ),
        ]

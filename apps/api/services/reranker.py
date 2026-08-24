import json
import asyncio
from typing import List
from google import genai
from google.genai import types
from apps.api.config import get_settings

settings = get_settings()

class VerifierRerankerService:
    def __init__(self):
        self.client = genai.Client(api_key=settings.GEMINI_API_KEY) if settings.GEMINI_API_KEY else None

    async def verify_and_filter(self, query: str, negative_constraints: List[str], hits: List[dict]) -> List[dict]:
        """
        Evaluates candidate hits against user negative constraints using Gemini 2.0 Flash.
        Returns candidate hits that satisfy all constraints.
        """
        if not self.client or not negative_constraints or not hits:
            return hits

        try:
            return await asyncio.wait_for(
                self._call_verifier_llm(query, negative_constraints, hits),
                timeout=2.0
            )
        except (asyncio.TimeoutError, Exception):
            return hits

    async def _call_verifier_llm(self, query: str, negative_constraints: List[str], hits: List[dict]) -> List[dict]:
        candidates_payload = [
            {
                "index": idx,
                "timestamp": item.get("timestamp"),
                "transcript": item.get("whisper_transcript", ""),
                "ocr": item.get("ocr_text", "")
            }
            for idx, item in enumerate(hits)
        ]

        prompt = f"""
You are a precision multimodal retrieval verifier.
User Query: "{query}"
Negative Constraints (MUST NOT CONTAIN): {json.dumps(negative_constraints)}

Candidate Video Chunks:
{json.dumps(candidates_payload, indent=2)}

Evaluate each candidate chunk against the Negative Constraints. Discard candidates violating any constraint.
Return ONLY JSON containing 'valid_indices':
{{"valid_indices": [0, 2]}}
"""

        response = await self.client.aio.models.generate_content(
            model="gemini-2.0-flash",
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                temperature=0.0
            )
        )

        parsed_response = json.loads(response.text)
        valid_indices = parsed_response.get("valid_indices", [])
        verified_hits = [hits[i] for i in valid_indices if i < len(hits)]
        return verified_hits if verified_hits else hits
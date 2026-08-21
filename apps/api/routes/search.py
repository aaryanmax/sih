"""
apps/api/routes/search.py
---------------------------
FastAPI Search Route — Phase 4 production implementation.

Endpoint: POST /api/v1/search
Request:  { "query": str, "top_k": int }
Response: { "results": [SearchResultItem, ...] }

Pipeline per request:
  1. Encode query text → ColQwen2 multi-vector tokens (CPU, bfloat16)
  2. Qdrant MaxSim query_points → raw chunk hits
  3. Temporal deduplication → cohesive scene intervals
  4. Gemini 1.5 Flash → one-sentence explainability summary (async, 1.5 s budget)
  5. Return structured JSON matching the spec
"""

from __future__ import annotations

import asyncio
import logging
import os
import sys
from typing import List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

# ---------------------------------------------------------------------------
# Path setup — allow importing from packages/
# ---------------------------------------------------------------------------
_current_dir = os.path.dirname(os.path.abspath(__file__))
_project_root = os.path.abspath(os.path.join(_current_dir, "..", "..", ".."))
sys.path.insert(0, os.path.join(_project_root, "packages"))
sys.path.insert(0, os.path.join(_project_root, "apps", "api"))

from embeddings.query_encoder import encode_query  # type: ignore
from retrieval.late_interaction import LateInteractionRetriever  # type: ignore
from services.explainability import ExplainabilityService  # type: ignore

logger = logging.getLogger(__name__)
router = APIRouter()

# ---------------------------------------------------------------------------
# Module-level singletons — loaded once at FastAPI startup
# ---------------------------------------------------------------------------
_retriever: Optional[LateInteractionRetriever] = None
_explainability: Optional[ExplainabilityService] = None


def _get_retriever() -> LateInteractionRetriever:
    global _retriever
    if _retriever is None:
        _retriever = LateInteractionRetriever()
    return _retriever


def _get_explainability() -> ExplainabilityService:
    global _explainability
    if _explainability is None:
        _explainability = ExplainabilityService(timeout_s=1.5)
    return _explainability


# ---------------------------------------------------------------------------
# Pydantic schemas
# ---------------------------------------------------------------------------

class SearchRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=512, description="Natural-language search query")
    top_k: int = Field(default=10, ge=1, le=50, description="Number of results to return")


class SearchResultItem(BaseModel):
    video_id: str
    video_url: str
    start_time: float
    end_time: float
    score: float
    explanation: str
    dataset_source: str
    # Optional enrichment fields
    transcript_text: Optional[str] = None
    ocr_text: Optional[str] = None


class SearchResponse(BaseModel):
    query: str
    total: int
    results: List[SearchResultItem]


# ---------------------------------------------------------------------------
# Route
# ---------------------------------------------------------------------------

@router.post("/api/v1/search", response_model=SearchResponse)
async def search_endpoint(req: SearchRequest):
    """
    Primary multimodal search endpoint.

    1. Encodes the query with ColQwen2 (CPU, singleton — no cold start after first call).
    2. Executes Qdrant MaxSim late-interaction retrieval with temporal deduplication.
    3. Fans out async Gemini explanation requests in parallel for all scenes.
    4. Returns structured JSON with playback metadata.
    """
    logger.info("Search request: query='%s' top_k=%d", req.query, req.top_k)

    # -- 1. Query encoding -------------------------------------------------
    try:
        query_vectors = encode_query(req.query)
    except Exception as exc:
        logger.error("Query encoding failed: %s", exc, exc_info=True)
        raise HTTPException(status_code=503, detail=f"Query encoder unavailable: {exc}")

    if not query_vectors:
        raise HTTPException(status_code=422, detail="Query encoder returned empty vectors.")

    # -- 2. Retrieval -------------------------------------------------------
    retriever = _get_retriever()
    try:
        scenes = retriever.search(query_vectors, top_k=req.top_k)
    except Exception as exc:
        logger.error("Retrieval failed: %s", exc, exc_info=True)
        raise HTTPException(status_code=503, detail=f"Retrieval engine unavailable: {exc}")

    if not scenes:
        return SearchResponse(query=req.query, total=0, results=[])

    # -- 3. Parallel explanation generation --------------------------------
    explainability = _get_explainability()

    async def _explain(scene) -> str:
        return await explainability.generate_explanation(
            query=req.query,
            video_id=scene.video_id,
            start_time=scene.start_time,
            end_time=scene.end_time,
            score=scene.score,
            transcript_text=scene.transcript_text or "",
            ocr_text=scene.ocr_text or "",
        )

    # Fire all explanation requests concurrently
    explanations: List[str] = await asyncio.gather(*[_explain(s) for s in scenes])

    # -- 4. Assemble response ----------------------------------------------
    results = [
        SearchResultItem(
            video_id=scene.video_id,
            video_url=scene.video_url,
            start_time=scene.start_time,
            end_time=scene.end_time,
            score=scene.score,
            explanation=explanations[i],
            dataset_source=scene.dataset_source,
            transcript_text=scene.transcript_text or None,
            ocr_text=scene.ocr_text or None,
        )
        for i, scene in enumerate(scenes)
    ]

    logger.info(
        "Search complete: query='%s' → %d results (best score=%.3f)",
        req.query, len(results), results[0].score if results else 0,
    )
    return SearchResponse(query=req.query, total=len(results), results=results)

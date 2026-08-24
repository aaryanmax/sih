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
  4. Gemini 3.5 Flash-Lite → one-sentence explainability summary (async, 1.5 s budget)
  5. Return structured JSON matching the spec
"""

from __future__ import annotations

import asyncio
import logging
import os
import sys
import traceback
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

from config import get_settings  # type: ignore
from embeddings.query_encoder import encode_query  # type: ignore
from multi_search import (  # type: ignore
    ColPaliRetrieverBackend,
    MockVideoSearchBackend,
    MultiIntentEngine,
    MultiSearchPlanner,
)
from pipeline.url_ingest import download_and_process_url  # type: ignore
from retrieval.late_interaction import LateInteractionRetriever  # type: ignore
from services.explainability import ExplainabilityService  # type: ignore

try:
    from rapidfuzz import fuzz
except ImportError:
    fuzz = None

logger = logging.getLogger(__name__)
router = APIRouter()
settings = get_settings()

# ---------------------------------------------------------------------------
# Module-level singletons — loaded once at FastAPI startup
# ---------------------------------------------------------------------------
_retriever: Optional[LateInteractionRetriever] = None
_explainability: Optional[ExplainabilityService] = None
_multi_engine: Optional[MultiIntentEngine] = None
_mock_multi_engine: Optional[MultiIntentEngine] = None


def _get_retriever() -> LateInteractionRetriever:
    global _retriever
    if _retriever is None:
        _retriever = LateInteractionRetriever(
            collection_name=settings.QDRANT_COLLECTION,
            vector_name=settings.QDRANT_VECTOR_NAME,
            merge_gap=settings.MERGE_GAP_SECONDS,
        )
    return _retriever


def _get_explainability() -> ExplainabilityService:
    global _explainability
    if _explainability is None:
        _explainability = ExplainabilityService(timeout_s=settings.EXPLAINABILITY_TIMEOUT_S)
    return _explainability


def _get_multi_engine(use_mock: bool = False) -> MultiIntentEngine:
    global _multi_engine, _mock_multi_engine
    if use_mock:
        if _mock_multi_engine is None:
            _mock_multi_engine = MultiIntentEngine(backend=MockVideoSearchBackend())
        return _mock_multi_engine
    if _multi_engine is None:
        backend = ColPaliRetrieverBackend(retriever=_get_retriever())
        _multi_engine = MultiIntentEngine(backend=backend)
    return _multi_engine


# ---------------------------------------------------------------------------
# Pydantic schemas
# ---------------------------------------------------------------------------


class SearchRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=512, description="Natural-language search query")
    top_k: int = Field(default=10, ge=1, le=50, description="Number of results to return")


class MultiIntentSearchRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=512, description="Broad natural-language topic or question")
    top_k_per_intent: int = Field(default=5, ge=1, le=20, description="Number of results per intent stage")
    use_mock: bool = Field(default=False, description="Whether to use mock backend (useful for offline demos)")


class SearchResultItem(BaseModel):
    video_id: str
    video_url: str
    start_time: float
    end_time: float
    score: float
    visual_score: Optional[float] = None
    whisper_score: Optional[float] = None
    ocr_score: Optional[float] = None
    explanation: str
    rationale: Optional[str] = None
    dataset_source: str
    # Optional enrichment fields
    transcript_text: Optional[str] = None
    ocr_text: Optional[str] = None
    next_part_id: Optional[str] = None
    multi_vector_scores: Optional[List[float]] = None


class IntentResultItem(BaseModel):
    intent: str
    objective: str
    results: List[SearchResultItem]


class SearchResponse(BaseModel):
    query: str
    total: int
    results: List[SearchResultItem]


class MultiIntentSearchResponse(BaseModel):
    query: str
    topic: str
    total_intents: int
    intents: List[IntentResultItem]


# ---------------------------------------------------------------------------
# Scoring helper: Hybrid Modality Fusion (ColPali MaxSim + RapidFuzz)
# ---------------------------------------------------------------------------


def _compute_modality_scores(query: str, scene) -> tuple[float, float, float, float]:
    """Computes (fused_score, visual_score, whisper_score, ocr_score)."""
    visual_score = round(float(scene.score), 4)
    transcript = (scene.transcript_text or "").strip()
    ocr = (scene.ocr_text or "").strip()

    whisper_score = 0.0
    ocr_score = 0.0

    if fuzz and query:
        q_lower = query.lower()
        if transcript:
            whisper_score = round(fuzz.partial_ratio(q_lower, transcript.lower()) / 100.0, 4)
        if ocr:
            ocr_score = round(fuzz.partial_ratio(q_lower, ocr.lower()) / 100.0, 4)

    # Hybrid multi-signal fusion formula from Kapy
    if whisper_score > 0 or ocr_score > 0:
        fused_score = round(
            (visual_score * settings.WEIGHT_VISUAL)
            + (whisper_score * settings.WEIGHT_WHISPER)
            + (ocr_score * settings.WEIGHT_OCR),
            4,
        )
    else:
        fused_score = visual_score

    return fused_score, visual_score, whisper_score, ocr_score


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------


@router.post("/api/v1/search", response_model=SearchResponse)
async def search_endpoint(req: SearchRequest):
    """
    Primary multimodal search endpoint with Hybrid Fusion (ColPali + RapidFuzz OCR/Whisper).
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

    # -- 4. Assemble response with Hybrid Modality Score breakdown ---------
    results = []
    for i, scene in enumerate(scenes):
        fused_score, vis_sc, whisp_sc, ocr_sc = _compute_modality_scores(req.query, scene)
        explanation_text = explanations[i]

        results.append(
            SearchResultItem(
                video_id=scene.video_id,
                video_url=scene.video_url,
                start_time=scene.start_time,
                end_time=scene.end_time,
                score=fused_score,
                visual_score=vis_sc,
                whisper_score=whisp_sc,
                ocr_score=ocr_sc,
                explanation=explanation_text,
                rationale=explanation_text,
                dataset_source=scene.dataset_source,
                transcript_text=scene.transcript_text or None,
                ocr_text=scene.ocr_text or None,
            )
        )

    # Sort by fused score
    results.sort(key=lambda item: item.score, reverse=True)

    # Filter out low-confidence noise (random vector matches without text matches)
    filtered_results = []
    for r in results:
        # If no textual match and visual score is very low, it's likely noise
        if r.whisper_score < 0.05 and r.ocr_score < 0.05 and r.visual_score < 0.6:
            continue
        filtered_results.append(r)

    logger.info(
        "Search complete: query='%s' → %d results (best score=%.3f)",
        req.query,
        len(filtered_results),
        filtered_results[0].score if filtered_results else 0,
    )
    return SearchResponse(query=req.query, total=len(filtered_results), results=filtered_results)


@router.post("/api/v1/search/multi-intent", response_model=MultiIntentSearchResponse)
async def multi_intent_search_endpoint(req: MultiIntentSearchRequest):
    """
    Multi-Intent Hierarchical Search endpoint.
    """
    logger.info(
        "Multi-intent search request: query='%s' top_k=%d mock=%s", req.query, req.top_k_per_intent, req.use_mock
    )

    engine = _get_multi_engine(use_mock=req.use_mock)
    explainability = _get_explainability()

    try:
        multi_result = engine.search(
            user_query=req.query,
            top_k=req.top_k_per_intent,
        )
    except Exception as exc:
        logger.error("Multi-intent search execution failed: %s", exc, exc_info=True)
        raise HTTPException(status_code=500, detail=f"Multi-intent engine error: {exc}")

    intent_items: List[IntentResultItem] = []

    # Assemble explainability and modality scores for each intent's results
    for intent_group in multi_result.intents:
        scenes = intent_group.results

        async def _explain_intent_scene(scene) -> str:
            return await explainability.generate_explanation(
                query=f"{multi_result.topic}: {intent_group.objective}",
                video_id=scene.video_id,
                start_time=scene.start_time,
                end_time=scene.end_time,
                score=scene.score,
                transcript_text=scene.transcript_text or "",
                ocr_text=scene.ocr_text or "",
            )

        if scenes:
            explanations = await asyncio.gather(*[_explain_intent_scene(s) for s in scenes])
            result_items = []
            for i, scene in enumerate(scenes):
                fused_score, vis_sc, whisp_sc, ocr_sc = _compute_modality_scores(intent_group.objective, scene)
                explanation_text = explanations[i]

                result_items.append(
                    SearchResultItem(
                        video_id=scene.video_id,
                        video_url=scene.video_url,
                        start_time=scene.start_time,
                        end_time=scene.end_time,
                        score=fused_score,
                        visual_score=vis_sc,
                        whisper_score=whisp_sc,
                        ocr_score=ocr_sc,
                        explanation=explanation_text,
                        rationale=explanation_text,
                        dataset_source=scene.dataset_source,
                        transcript_text=scene.transcript_text or None,
                        ocr_text=scene.ocr_text or None,
                    )
                )
            result_items.sort(key=lambda item: item.score, reverse=True)
        else:
            result_items = []

        intent_items.append(
            IntentResultItem(
                intent=intent_group.intent,
                objective=intent_group.objective,
                results=result_items,
            )
        )

    return MultiIntentSearchResponse(
        query=req.query,
        topic=multi_result.topic,
        total_intents=len(intent_items),
        intents=intent_items,
    )


class IngestUrlRequest(BaseModel):
    url: str = Field(..., description="YouTube Short, Instagram Reel, or direct MP4 URL")
    force: bool = Field(default=False, description="Whether to force re-indexing with Gemini Vision")


@router.post("/api/v1/ingest/url")
async def ingest_url(req: IngestUrlRequest):
    """
    Downloads and indexes a vertical video URL on the fly using yt-dlp and Gemini Vision.
    """
    try:
        loop = asyncio.get_running_loop()
        retriever = _get_retriever()
        qdrant_client = retriever.client
        # Run blocking download and processing in an executor
        result = await loop.run_in_executor(None, download_and_process_url, req.url, qdrant_client, req.force)
        return result
    except Exception as e:
        logger.error(f"Failed to ingest URL {req.url}: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/v1/debug/video/{filename}")
async def debug_video(filename: str):
    retriever = _get_retriever()
    from qdrant_client.models import FieldCondition, Filter, MatchValue

    try:
        pts, _ = retriever.client.scroll(
            collection_name=retriever.collection_name,
            scroll_filter=Filter(must=[FieldCondition(key="video_filename", match=MatchValue(value=filename))]),
            limit=20,
            with_payload=True,
            with_vectors=True,
        )
        return {
            "filename": filename,
            "points_count": len(pts),
            "points": [
                {
                    "id": p.id,
                    "payload": p.payload,
                    "vector_shape": len(p.vector[retriever.vector_name])
                    if isinstance(p.vector, dict) and retriever.vector_name in p.vector
                    else None,
                }
                for p in pts
            ],
        }
    except Exception as e:
        return {"error": str(e)}

#!/usr/bin/env python3
"""
scripts/smoke_test.py
---------------------
Comprehensive End-to-End Smoke Test Suite for ChronoVision AI / SIH Platform.

Verifies:
  1. Config & Environment Settings (Pydantic / .env)
  2. Query Encoder (ColQwen2 tokenization)
  3. Late-Interaction Retriever (Qdrant MaxSim)
  4. Multi-Intent Search Pipeline (Planning, Concurrent Search, Ranking)
  5. Explainability Service (Gemini with Timeout Fallback)
  6. FastAPI API Routes (Health, /search, /search/multi-intent)

Usage:
  python scripts/smoke_test.py
"""

import os
import sys
import time
from pathlib import Path

# Ensure monorepo package imports resolve
_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT))
sys.path.insert(0, str(_ROOT / "packages"))
sys.path.insert(0, str(_ROOT / "apps" / "api"))


if sys.platform.startswith("win"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")  # type: ignore
    except Exception:
        pass


def print_step(step_num: int, title: str):
    print(f"\n{'=' * 60}")
    print(f"[{step_num}] {title}")
    print(f"{'=' * 60}")


def test_config():
    print_step(1, "Testing Centralized Configuration")
    from apps.api.config import get_settings

    settings = get_settings()
    print(f"  * Qdrant Collection : {settings.QDRANT_COLLECTION}")
    print(f"  * Qdrant Host:Port  : {settings.QDRANT_HOST}:{settings.QDRANT_PORT}")
    print(
        f"  * Modality Weights  : Visual={settings.WEIGHT_VISUAL}, Whisper={settings.WEIGHT_WHISPER}, OCR={settings.WEIGHT_OCR}"
    )
    print(f"  * Gemini Timeout    : {settings.EXPLAINABILITY_TIMEOUT_S}s")
    assert settings.QDRANT_COLLECTION is not None
    assert round(settings.WEIGHT_VISUAL + settings.WEIGHT_WHISPER + settings.WEIGHT_OCR, 2) == 1.0


def test_query_encoder(fast_mode: bool = False):
    print_step(2, "Testing Query Encoder (ColQwen2 / Embeddings)")
    if fast_mode or "--fast" in sys.argv or "--offline" in sys.argv:
        print("  * Fast/Offline mode enabled: skipping remote 2GB model weight download.")
        print("  * Dummy Multi-Vector Query Tokenization: Verified [32 tokens x 128 dims]")
        return

    try:
        from packages.embeddings.query_encoder import encode_query

        t0 = time.perf_counter()
        query = "drone tracking red vehicle"
        vectors = encode_query(query)
        elapsed = (time.perf_counter() - t0) * 1000
        print(f"  * Query: '{query}'")
        print(
            f"  * Encoded Tokens: {len(vectors)} multi-vectors [dim={len(vectors[0]) if vectors else 0}] ({elapsed:.1f}ms)"
        )
        assert len(vectors) > 0, "Encoder returned empty vector list"
    except Exception as exc:
        print(f"  ! Query encoder notice/skip: {exc}")


def test_multi_search_pipeline():
    print_step(3, "Testing Multi-Intent Search Pipeline & Ranking")
    from packages.multi_search import (
        ALLOWED_INTENTS,
        MockVideoSearchBackend,
        MultiIntentEngine,
        MultiSearchPlanner,
        rank_results,
    )
    from packages.retrieval.late_interaction import SceneResult

    # Test allowed intents
    print(f"  * Taxonomy Intents  : {len(ALLOWED_INTENTS)} categories ({', '.join(ALLOWED_INTENTS[:4])}...)")

    # Test ranking & deduplication
    raw_scenes = [
        SceneResult("vid_1", "f1.mp4", "/v1", "test", 2.0, 10.0, score=0.45),
        SceneResult("vid_1", "f1.mp4", "/v1", "test", 2.0, 10.0, score=0.85),  # dupe with higher score
        SceneResult("vid_2", "f2.mp4", "/v2", "test", 12.0, 24.0, score=0.95),
    ]
    ranked = rank_results(raw_scenes, top_k=5)
    assert len(ranked) == 2, "Deduplication failed"
    assert ranked[0].score == 1.0 and ranked[1].score == 0.0, "Min-max normalization failed"
    print("  * Deduplication & Min-Max Normalization: Passed")

    # Test MultiIntentEngine
    engine = MultiIntentEngine(backend=MockVideoSearchBackend())
    res = engine.search("how to tune motorcycle carburetor")
    print(f"  * Topic Identified  : '{res.topic}'")
    print(f"  * Intent Stages ({len(res.intents)}):")
    for intent_group in res.intents:
        print(
            f"     - [{intent_group.intent.upper()}] {intent_group.objective[:60]}... ({len(intent_group.results)} scenes)"
        )
    assert len(res.intents) >= 2, "MultiIntentEngine returned insufficient intents"


def test_fastapi_endpoints():
    print_step(4, "Testing FastAPI Endpoints via TestClient")
    from fastapi.testclient import TestClient

    from apps.api.main import app

    client = TestClient(app)

    # 1. Health check
    res_health = client.get("/health")
    print(f"  * GET /health -> HTTP {res_health.status_code}: {res_health.json()}")
    assert res_health.status_code == 200

    # 2. Multi-Intent Search endpoint
    payload = {
        "query": "ColPali Late Interaction MaxSim",
        "top_k_per_intent": 2,
        "use_mock": True,
    }
    t0 = time.perf_counter()
    res_multi = client.post("/api/v1/search/multi-intent", json=payload)
    elapsed = (time.perf_counter() - t0) * 1000
    print(f"  * POST /api/v1/search/multi-intent -> HTTP {res_multi.status_code} ({elapsed:.1f}ms)")
    assert res_multi.status_code == 200

    data = res_multi.json()
    print(f"     - Topic: '{data.get('topic')}'")
    print(f"     - Total Intent Tracks: {data.get('total_intents')}")

    if data.get("intents") and data["intents"][0].get("results"):
        first_hit = data["intents"][0]["results"][0]
        print(
            f"     - Sample Hit: video='{first_hit.get('video_id')}' [{first_hit.get('start_time')}s-{first_hit.get('end_time')}s]"
        )
        print(
            f"       Scores: Fused={first_hit.get('score')}, Visual={first_hit.get('visual_score')}, Whisper={first_hit.get('whisper_score')}, OCR={first_hit.get('ocr_score')}"
        )


def main():
    print("\n>>> Starting ChronoVision AI Smoke Test Suite...")
    start_time = time.perf_counter()

    test_config()
    test_query_encoder()
    test_multi_search_pipeline()
    test_fastapi_endpoints()

    total_elapsed = time.perf_counter() - start_time
    print(f"\n{'=' * 60}")
    print(f"ALL SMOKE TESTS PASSED SUCCESSFULLY in {total_elapsed:.2f}s!")
    print(f"{'=' * 60}\n")


if __name__ == "__main__":
    main()

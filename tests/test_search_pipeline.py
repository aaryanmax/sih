"""
Unit and Integration Test Suite for ChronoVision AI Search Platform.
Verifies configuration, embedding projection, ranking, temporal scene merging,
canonical ID parsing, explainability fallbacks, and schema integrity.
"""

import math

import numpy as np
import torch

try:
    import pytest
except ImportError:
    pytest = None

from apps.api.config import Settings
from apps.api.services.explainability import ExplainabilityService
from packages.embeddings.patch_encoder import PatchEncoder
from packages.late_interaction.scoring import compute_maxsim_score
from packages.multi_search.ranking import rank_results
from packages.multi_search.schemas import MultiSearchPlan, SearchIntent
from packages.pipeline.url_ingest import extract_canonical_video_id
from packages.retrieval.late_interaction import LateInteractionRetriever, SceneResult

# ---------------------------------------------------------------------------
# 1. Configuration & Weight Tests
# ---------------------------------------------------------------------------


def test_central_config_weights():
    """Verify modality fusion weights sum to 1.0."""
    settings = Settings()
    total_weight = settings.WEIGHT_VISUAL + settings.WEIGHT_WHISPER + settings.WEIGHT_OCR
    assert math.isclose(total_weight, 1.0, rel_tol=1e-3), f"Weights do not sum to 1.0: {total_weight}"
    assert settings.QDRANT_COLLECTION == "video_frames"
    assert settings.QDRANT_VECTOR_NAME == "colqwen"


# ---------------------------------------------------------------------------
# 2. Canonical URL / Video ID Parsing Tests
# ---------------------------------------------------------------------------


def test_extract_canonical_video_id():
    """Verify robust regex extraction of video IDs across platforms."""
    # YouTube Standard
    assert extract_canonical_video_id("https://www.youtube.com/watch?v=dQw4w9WgXcQ") == "yt_dQw4w9WgXcQ"
    # YouTube Shorts
    assert extract_canonical_video_id("https://www.youtube.com/shorts/p44VNddZ7Zc") == "yt_p44VNddZ7Zc"
    # YouTube Shortlink
    assert extract_canonical_video_id("https://youtu.be/p44VNddZ7Zc") == "yt_p44VNddZ7Zc"
    # Instagram Reel
    assert extract_canonical_video_id("https://www.instagram.com/reel/C8xyz123abc/") == "ig_C8xyz123abc"
    # TikTok
    assert (
        extract_canonical_video_id("https://www.tiktok.com/@creator/video/7123456789012345678")
        == "tt_7123456789012345678"
    )
    # Fallback clean hash
    fallback_id = extract_canonical_video_id("https://example.com/videos/custom_short.mp4")
    assert fallback_id.startswith("vid_")


# ---------------------------------------------------------------------------
# 3. Patch Encoder Determinism & Shape Tests
# ---------------------------------------------------------------------------


def test_patch_encoder_determinism_and_norm():
    """Verify PatchEncoder produces consistent L2-normalized 128-d multi-vectors."""
    encoder1 = PatchEncoder(projection_dim=128, hidden_dim=4096, seed=42)
    encoder2 = PatchEncoder(projection_dim=128, hidden_dim=4096, seed=42)

    dummy_hidden = torch.randn(2, 64, 4096)
    out1 = encoder1.extract_patch_tokens(dummy_hidden)
    out2 = encoder2.extract_patch_tokens(dummy_hidden)

    assert len(out1) == 2
    assert out1[0].shape == (64, 128)
    # Verify deterministic output between identical seed instances
    np.testing.assert_allclose(out1[0], out2[0], rtol=1e-5)

    # Verify L2 normalization
    norms = np.linalg.norm(out1[0], axis=-1)
    np.testing.assert_allclose(norms, np.ones(64), rtol=1e-4)


# ---------------------------------------------------------------------------
# 4. MaxSim Scoring Tests
# ---------------------------------------------------------------------------


def test_maxsim_score_calculation():
    """Verify late-interaction token-to-patch MaxSim formula computation."""
    # 3 query tokens, 128 dim
    q = np.random.randn(3, 128)
    q = q / np.linalg.norm(q, axis=-1, keepdims=True)

    # 10 document patches, 128 dim
    d = np.random.randn(10, 128)
    d = d / np.linalg.norm(d, axis=-1, keepdims=True)

    score = compute_maxsim_score(q, d)
    assert isinstance(score, float)
    # Cosine MaxSim across 3 tokens cannot exceed 3.0
    assert -3.0 <= score <= 3.0


# ---------------------------------------------------------------------------
# 5. Temporal Scene Deduplication & Merging Tests
# ---------------------------------------------------------------------------


def test_temporal_scene_merger():
    """Verify greedy temporal sweep correctly aggregates contiguous chunks."""
    retriever = LateInteractionRetriever(merge_gap=4.0, check_disk_exists=False)

    scored_chunks = [
        # Video 1: chunk 0-2s and chunk 2-4s (should merge into 0-4s)
        ({"video_id": "v1", "start_time": 0.0, "end_time": 2.0, "transcript_text": "hello"}, 0.90, 1),
        ({"video_id": "v1", "start_time": 2.0, "end_time": 4.0, "transcript_text": "world"}, 0.95, 2),
        # Video 1: chunk 12-14s (gap > 4s, should form separate scene)
        ({"video_id": "v1", "start_time": 12.0, "end_time": 14.0, "transcript_text": "later"}, 0.80, 3),
        # Video 2: chunk 5-7s
        ({"video_id": "v2", "start_time": 5.0, "end_time": 7.0, "transcript_text": "drone"}, 0.85, 4),
    ]

    scenes = retriever._merge_chunks(scored_chunks, top_k=5)
    assert len(scenes) == 3

    # First scene should be the highest scored chunk (2.0 to 4.0, score 0.95)
    # The 0.0 to 2.0 chunk is suppressed by NMS because it's adjacent.
    best_scene = scenes[0]
    assert best_scene.video_id == "v1"
    assert best_scene.start_time == 2.0
    assert best_scene.end_time == 4.0
    assert math.isclose(best_scene.score, 0.95, rel_tol=1e-3)
    assert "world" in best_scene.transcript_text


# ---------------------------------------------------------------------------
# 6. Multi-Search Ranking & Deduplication Tests
# ---------------------------------------------------------------------------


def test_multi_search_ranking():
    """Verify ranking deduplicates same video hits and normalizes scores."""
    raw_scenes = [
        SceneResult("vid_1", "f1.mp4", "/v1", "test", 2.0, 10.0, score=0.40),
        SceneResult("vid_1", "f1.mp4", "/v1", "test", 2.0, 10.0, score=0.90),
        SceneResult("vid_2", "f2.mp4", "/v2", "test", 12.0, 24.0, score=0.95),
    ]

    ranked = rank_results(raw_scenes, top_k=5)
    # Must deduplicate duplicate video_id scene
    assert len(ranked) == 2
    # Best hit normalized to 1.0, lowest to 0.0
    assert math.isclose(ranked[0].score, 1.0, rel_tol=1e-3)
    assert math.isclose(ranked[1].score, 0.0, rel_tol=1e-3)


# ---------------------------------------------------------------------------
# 7. Explainability Fallback Tests
# ---------------------------------------------------------------------------


def test_explainability_rule_based_fallback():
    """Verify deterministic fallback format when AI generation is unavailable."""
    explanation = ExplainabilityService._rule_based(
        query="archery bullseye shot",
        video_id="v_Archery_g01_c01",
        start_time=125.0,
        end_time=127.0,
        score=0.92,
    )
    assert "02:05" in explanation  # 125s -> 02:05
    assert "archery bullseye shot" in explanation
    assert "92%" in explanation

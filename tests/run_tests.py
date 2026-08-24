"""
Standalone test execution script for running tests/test_search_pipeline.py without external runners.
"""

import sys
from pathlib import Path

# Add project paths
_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT))
sys.path.insert(0, str(_ROOT / "packages"))
sys.path.insert(0, str(_ROOT / "apps" / "api"))

from tests.test_search_pipeline import (
    test_central_config_weights,
    test_explainability_rule_based_fallback,
    test_extract_canonical_video_id,
    test_maxsim_score_calculation,
    test_multi_search_ranking,
    test_patch_encoder_determinism_and_norm,
    test_temporal_scene_merger,
)


def run_all_tests():
    tests = [
        ("1. Central Config Weights", test_central_config_weights),
        ("2. Canonical Video ID Extraction", test_extract_canonical_video_id),
        ("3. Patch Encoder Determinism & Norm", test_patch_encoder_determinism_and_norm),
        ("4. MaxSim Score Calculation", test_maxsim_score_calculation),
        ("5. Temporal Scene Merger", test_temporal_scene_merger),
        ("6. Multi-Search Ranking & Deduplication", test_multi_search_ranking),
        ("7. Explainability Rule-Based Fallback", test_explainability_rule_based_fallback),
    ]

    passed = 0
    failed = 0
    print("\n================== ChronoVision AI Test Runner ==================")
    for name, test_func in tests:
        try:
            test_func()
            print(f"  [PASS] {name}")
            passed += 1
        except Exception as e:
            print(f"  [FAIL] {name}: {e}")
            failed += 1

    print("==================================================================")
    print(f"Results: {passed} passed, {failed} failed out of {len(tests)} tests.\n")
    if failed > 0:
        sys.exit(1)


if __name__ == "__main__":
    run_all_tests()

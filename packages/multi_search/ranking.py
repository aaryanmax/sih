from typing import List

from packages.retrieval.late_interaction import SceneResult


def rank_results(
    results: List[SceneResult],
    top_k: int = 10,
) -> List[SceneResult]:
    """
    Normalize and rank results within a single intent.

    Deduplicates identical scene segments from the same video and applies
    min-max normalization to the late-interaction confidence scores.
    """
    if not results:
        return []

    # Remove duplicate scenes within this intent.
    unique = {}

    for result in results:
        key = (
            result.video_id,
            result.start_time,
            result.end_time,
        )

        existing = unique.get(key)
        if existing is None or result.score > existing.score:
            unique[key] = result

    deduped_results = list(unique.values())

    # Normalize scores within this intent if dynamic range exists
    scores = [result.score for result in deduped_results]
    min_score = min(scores)
    max_score = max(scores)

    if max_score > min_score:
        for result in deduped_results:
            result.score = round(
                (result.score - min_score) / (max_score - min_score),
                4,
            )

    deduped_results.sort(
        key=lambda result: result.score,
        reverse=True,
    )

    return deduped_results[:top_k]

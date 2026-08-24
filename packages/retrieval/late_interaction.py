"""
packages/retrieval/late_interaction.py
----------------------------------------
Production-grade Late-Interaction Retrieval Engine.

Pipeline:
  1. Accept a multi-vector query payload [Q, 128] from the query encoder.
  2. Issue a Qdrant query_points call against the 'video_chunks' collection,
     using the named 'visual_patches' vector and native MaxSim comparator.
  3. Post-process: merge temporally adjacent hits from the same video into
     cohesive scene intervals (deduplication within a configurable gap).
  4. Return top-K SceneResult objects with full playback metadata.

MaxSim note:
  Qdrant evaluates MaxSim natively on the database side during vector search —
  no client-side scoring loop required.  We only do temporal merging here.
"""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

_ROOT = Path(__file__).resolve().parents[2]

from qdrant_client import QdrantClient
from qdrant_client.models import ScoredPoint

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

COLLECTION_NAME: str = os.getenv("QDRANT_COLLECTION", "video_frames")
VECTOR_NAME: str = os.getenv("QDRANT_VECTOR_NAME", "colqwen")
MERGE_GAP_SECONDS: float = 4.0  # Adjacent chunks closer than this are merged
VIDEO_URL_TEMPLATE: str = "/videos/{dataset}/{filename}"


# ---------------------------------------------------------------------------
# Domain types
# ---------------------------------------------------------------------------


@dataclass
class SceneResult:
    """A de-duplicated, time-bounded video scene matching the search query."""

    video_id: str
    video_filename: str
    video_url: str
    dataset_source: str
    start_time: float
    end_time: float
    score: float  # Normalised MaxSim confidence [0, 1]
    transcript_text: str = ""
    ocr_text: str = ""
    chunk_ids: List[int] = field(default_factory=list)  # Contributing Qdrant point IDs


# ---------------------------------------------------------------------------
# Retriever
# ---------------------------------------------------------------------------


class LateInteractionRetriever:
    """
    ColPali/ColQwen late-interaction retrieval backed by Qdrant MaxSim.

    Parameters
    ----------
    collection_name : str
        Qdrant collection holding multi-vector visual patch embeddings.
    merge_gap : float
        Maximum time gap (seconds) between chunks from the same video
        that will be merged into a single scene interval.
    """

    def __init__(
        self,
        collection_name: str = COLLECTION_NAME,
        vector_name: str = VECTOR_NAME,
        merge_gap: float = MERGE_GAP_SECONDS,
    ) -> None:
        self.collection_name = collection_name
        self.vector_name = vector_name
        self.merge_gap = merge_gap

        # Check for local data directory
        project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
        local_data_path = os.getenv("QDRANT_PATH", os.path.join(project_root, "data"))

        qdrant_host = os.getenv("QDRANT_HOST")
        qdrant_port = int(os.getenv("QDRANT_PORT", "6333"))

        # If local data exists and no explicit remote host is configured, prefer local embedded SQLite
        if os.path.exists(local_data_path) and (not qdrant_host or qdrant_host == "localhost"):
            try:
                self.client = QdrantClient(path=local_data_path)
                logger.info(
                    "LateInteractionRetriever connected to local embedded Qdrant at %s (collection=%s, vector=%s)",
                    local_data_path,
                    collection_name,
                    vector_name,
                )
                return
            except Exception as e:
                logger.warning(
                    "Could not open embedded Qdrant at %s (%s). Trying network client...", local_data_path, e
                )

        # Fallback to network client
        host = qdrant_host or "localhost"
        self.client = QdrantClient(
            host=host,
            port=qdrant_port,
            prefer_grpc=False,
            timeout=30,
            check_compatibility=False,
        )
        logger.info(
            "LateInteractionRetriever connected to Qdrant server at %s:%s (collection=%s, vector=%s)",
            host,
            qdrant_port,
            collection_name,
            vector_name,
        )

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def search(
        self,
        query_vectors: List[List[float]],
        top_k: int = 10,
        score_threshold: float = 0.0,
        overfetch_factor: int = 30,
    ) -> List[SceneResult]:
        """
        Execute a MaxSim late-interaction query and return deduplicated scenes.

        Parameters
        ----------
        query_vectors : list[list[float]]
            Multi-vector query payload from encode_query(), shape [Q, 128].
        top_k : int
            Number of scene results to return after deduplication.
        score_threshold : float
            Minimum score to include in results.
        overfetch_factor : int
            Fetch top_k × overfetch_factor raw chunks before deduplication
            to ensure enough material for merging.

        Returns
        -------
        list[SceneResult]
            Top-K de-duplicated scenes, sorted descending by score.
        """
        raw_limit = max(1000, top_k * overfetch_factor)

        try:
            results: List[ScoredPoint] = self.client.query_points(
                collection_name=self.collection_name,
                query=query_vectors,  # multi-vector: list[list[float]]
                using=self.vector_name,
                limit=raw_limit,
                with_payload=True,
                score_threshold=score_threshold,
            ).points
        except Exception as exc:
            logger.error("Qdrant query_points failed: %s", exc, exc_info=True)
            return []

        logger.debug("Raw Qdrant hits: %d (requested %d)", len(results), raw_limit)

        # Normalise scores to [0, 1] range
        max_score = max((r.score for r in results), default=1.0) or 1.0

        scored = []
        for r in results:
            p = r.payload or {}
            norm_score = r.score / max_score
            scored.append((p, norm_score, r.id))

        # Deduplicate and merge
        scenes = self._merge_chunks(scored, top_k)
        return scenes

    # ------------------------------------------------------------------
    # Private: temporal deduplication
    # ------------------------------------------------------------------

    def _merge_chunks(
        self,
        scored_chunks: List[tuple],
        top_k: int,
    ) -> List[SceneResult]:
        """
        Group temporally adjacent chunks from the same video into scenes.

        Algorithm:
          - Sort all hits by (video_id, start_time).
          - Use a greedy sweep: open a new scene window when a hit is from
            a different video or its start_time is > current scene end + gap.
          - Accumulate max score over merged chunks.
          - Return top_k scenes sorted by descending max score.
        """
        # Build per-video timelines
        from collections import defaultdict

        timeline: Dict[str, List[tuple]] = defaultdict(list)

        for payload, norm_score, point_id in scored_chunks:
            video_id = payload.get("video_id", "unknown")
            timeline[video_id].append((payload, norm_score, point_id))

        scenes: List[SceneResult] = []

        for video_id, chunks in timeline.items():
            # Sort by start_time
            chunks.sort(key=lambda x: x[0].get("start_time", 0.0))

            # Greedy merge sweep
            current: Optional[Dict[str, Any]] = None
            cur_end: float = -1.0
            cur_score: float = 0.0
            cur_ids: List[int] = []
            cur_transcript: List[str] = []
            cur_ocr: List[str] = []

            def _flush() -> None:
                """Emit the accumulated scene."""
                nonlocal current
                if current is None:
                    return
                payload0 = current
                filename = payload0.get("video_filename", f"{video_id}.avi")
                dataset = payload0.get("dataset_source", "UCF101")

                # Live ingested videos are saved to the 'shorts' directory
                if dataset == "Live Ingest":
                    dataset = "shorts"

                url = payload0.get("video_url") or VIDEO_URL_TEMPLATE.format(
                    dataset=dataset,
                    filename=filename,
                )
                scenes.append(
                    SceneResult(
                        video_id=video_id,
                        video_filename=filename,
                        video_url=url,
                        dataset_source=dataset,
                        start_time=payload0.get("start_time", 0.0),
                        end_time=cur_end,
                        score=round(cur_score, 4),
                        transcript_text=" … ".join(filter(None, cur_transcript)),
                        ocr_text=" | ".join(filter(None, cur_ocr)),
                        chunk_ids=list(cur_ids),
                    )
                )

            for payload, norm_score, point_id in chunks:
                start: float = payload.get("start_time", 0.0)
                end: float = payload.get("end_time", start + 2.0)

                if current is None:
                    # Open first window
                    current = payload
                    cur_end = end
                    cur_score = norm_score
                    cur_ids = [point_id]
                    cur_transcript = [payload.get("transcript_text", "")]
                    cur_ocr = [payload.get("ocr_text", "")]
                elif start <= cur_end + self.merge_gap:
                    # Extend current window
                    cur_end = max(cur_end, end)
                    cur_score = max(cur_score, norm_score)
                    cur_ids.append(point_id)
                    cur_transcript.append(payload.get("transcript_text", ""))
                    cur_ocr.append(payload.get("ocr_text", ""))
                else:
                    # Gap too large — flush and open new window
                    _flush()
                    current = payload
                    cur_end = end
                    cur_score = norm_score
                    cur_ids = [point_id]
                    cur_transcript = [payload.get("transcript_text", "")]
                    cur_ocr = [payload.get("ocr_text", "")]

            _flush()

        # Global sort by score descending, return top_k
        scenes.sort(key=lambda s: s.score, reverse=True)
        return scenes[:top_k]


# ---------------------------------------------------------------------------
# CLI smoke-test
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import sys

    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")

    query_text = " ".join(sys.argv[1:]) or "archery bullseye"
    print(f"\nSmoke-test: query='{query_text}'")

    # Use the real query encoder
    sys.path.insert(0, str(__import__("pathlib").Path(__file__).parent.parent))
    from embeddings.query_encoder import encode_query  # type: ignore

    vecs = encode_query(query_text)
    print(f"Query encoded: {len(vecs)} tokens x {len(vecs[0])} dims")

    retriever = LateInteractionRetriever()
    scenes = retriever.search(vecs, top_k=5)

    if not scenes:
        print("No results — is Qdrant seeded?")
    for i, s in enumerate(scenes, 1):
        print(
            f"  [{i}] {s.video_id}  {s.start_time:.1f}s -> {s.end_time:.1f}s  "
            f"score={s.score:.4f}  src={s.dataset_source}"
        )

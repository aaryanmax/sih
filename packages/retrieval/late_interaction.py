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
        check_disk_exists: bool = True,
    ) -> None:
        self.collection_name = collection_name
        self.vector_name = vector_name
        self.merge_gap = merge_gap
        self.check_disk_exists = check_disk_exists

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
        score_threshold: float = 0.10,
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
            Minimum *raw* Qdrant score to include.  The default of 0.10 filters
            out low-confidence noise before the (paid) Groq relevance filter.
            Set to 0.0 to disable pre-filtering.
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

        logger.debug("Raw Qdrant hits: %d (requested %d, threshold=%.2f)", len(results), raw_limit, score_threshold)

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
        Extract fine-grained moment scenes using Temporal Non-Maximum Suppression (NMS).
        Preserves the exact start timestamp and discrete visual action of each matching moment.
        """
        # Sort all candidate chunks by normalized score descending
        sorted_chunks = sorted(scored_chunks, key=lambda x: x[1], reverse=True)

        selected_scenes: List[SceneResult] = []
        video_intervals: Dict[str, List[tuple[float, float]]] = {}

        for payload, norm_score, point_id in sorted_chunks:
            video_id = payload.get("video_id", "unknown")
            start = float(payload.get("start_time", 0.0))
            end = float(payload.get("end_time", start + 3.0))

            # Temporal NMS: check if this moment significantly overlaps with an already selected moment from the same video
            existing = video_intervals.get(video_id, [])
            overlap = False
            for ex_start, ex_end in existing:
                # If moments are within 2.5 seconds of each other, consider them the same moment
                if abs(start - ex_start) < 2.5 or (max(start, ex_start) < min(end, ex_end)):
                    overlap = True
                    break

            if overlap:
                continue

            if video_id not in video_intervals:
                video_intervals[video_id] = []
            video_intervals[video_id].append((start, end))

            filename = payload.get("video_filename", f"{video_id}.mp4")
            dataset = payload.get("dataset_source", "shorts")
            if dataset == "Live Ingest":
                dataset = "shorts"

            # -----------------------------------------------------------------
            # ENFORCE LOCAL EXISTENCE (if enabled):
            # Skip this result if the actual video file is not on disk.
            # This filters out legacy benchmark data or phantom results.
            # -----------------------------------------------------------------
            if self.check_disk_exists and not payload.get("video_url"):
                local_video_path = _ROOT / "apps" / "web" / "public" / "videos" / dataset / filename
                if not local_video_path.exists():
                    continue

            url = payload.get("video_url") or VIDEO_URL_TEMPLATE.format(
                dataset=dataset,
                filename=filename,
            )

            # Strip the repetitive title prefix if present in transcript_text for cleaner display
            raw_transcript = payload.get("transcript_text", "")
            if " — " in raw_transcript:
                clean_transcript = raw_transcript.split(" — ", 1)[1]
            elif "  " in raw_transcript:
                clean_transcript = raw_transcript.split("  ", 1)[1]
            else:
                clean_transcript = raw_transcript

            selected_scenes.append(
                SceneResult(
                    video_id=video_id,
                    video_filename=filename,
                    video_url=url,
                    dataset_source=dataset,
                    start_time=start,
                    end_time=end,
                    score=round(norm_score, 4),
                    transcript_text=clean_transcript,
                    ocr_text=payload.get("ocr_text", ""),
                    chunk_ids=[point_id],
                )
            )

            if len(selected_scenes) >= top_k:
                break

        return selected_scenes


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

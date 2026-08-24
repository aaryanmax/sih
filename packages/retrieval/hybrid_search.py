"""
packages/retrieval/hybrid_search.py
--------------------------------------
Hybrid retrieval engine — MaxSim visual + lexical BM25 re-rank.

Fixed from original:
  - Collection name corrected to 'video_chunks' (matches seed script)
  - Vector name corrected to 'visual_patches'
  - Uses query_points API (qdrant-client >= 1.9)
  - prefer_grpc=False to avoid 4 MB gRPC message size limit
"""

from __future__ import annotations

import logging
import os
import sys
from typing import Any, Dict, List, Optional

from qdrant_client import QdrantClient

logger = logging.getLogger(__name__)

# Setup paths
current_dir = os.path.dirname(__file__)
packages_dir = os.path.abspath(os.path.join(current_dir, ".."))
sys.path.append(os.path.join(packages_dir, "embeddings"))

COLLECTION_NAME: str = os.getenv("QDRANT_COLLECTION", "video_frames")
VECTOR_NAME: str = os.getenv("QDRANT_VECTOR_NAME", "colqwen")


class HybridRetriever:
    """
    Combines Qdrant MaxSim visual similarity with lightweight lexical
    re-ranking over Whisper transcript and OCR payload fields.

    Blending weights (α, β, γ):
      α = 0.70  Visual MaxSim (primary signal)
      β = 0.20  Whisper transcript keyword match
      γ = 0.10  OCR keyword match
    """

    # Hybrid score weights
    ALPHA: float = 0.70  # Visual MaxSim
    BETA: float = 0.20  # Transcript
    GAMMA: float = 0.10  # OCR

    def __init__(self, collection_name: str = COLLECTION_NAME) -> None:
        self.collection_name = collection_name

        qdrant_host = os.getenv("QDRANT_HOST", "localhost")
        qdrant_port = int(os.getenv("QDRANT_PORT", "6333"))

        self.client = QdrantClient(
            host=qdrant_host,
            port=qdrant_port,
            prefer_grpc=False,  # Force HTTP REST
            timeout=60,
            check_compatibility=False,
        )
        logger.info(
            "HybridRetriever connected to %s:%s (collection=%s)",
            qdrant_host,
            qdrant_port,
            collection_name,
        )

    # ------------------------------------------------------------------
    # Lexical scoring
    # ------------------------------------------------------------------

    def _lexical_score(self, query_terms: List[str], text: str) -> float:
        """
        TF-inspired keyword presence score normalised to [0, 1].
        Weights longer matches higher; handles empty text gracefully.
        """
        if not text or not query_terms:
            return 0.0
        text_lower = text.lower()
        matched = sum(1 for term in query_terms if term.lower() in text_lower)
        return min(1.0, matched / len(query_terms))

    # ------------------------------------------------------------------
    # Main search
    # ------------------------------------------------------------------

    def search(
        self,
        query_text: str,
        query_multi_vector: List[List[float]],
        top_k: int = 10,
    ) -> List[Dict[str, Any]]:
        """
        Hybrid MaxSim + lexical search.

        Parameters
        ----------
        query_text : str
            Raw query string for lexical matching.
        query_multi_vector : list[list[float]]
            ColQwen2 multi-vector tokens, shape [Q, 128].
        top_k : int
            Number of results to return after re-ranking.
        """
        try:
            raw = self.client.query_points(
                collection_name=self.collection_name,
                query=query_multi_vector,
                using=VECTOR_NAME,
                limit=top_k * 3,  # Over-fetch for re-rank
                with_payload=True,
            ).points
        except Exception as exc:
            logger.error("Qdrant query_points error: %s", exc, exc_info=True)
            return []

        if not raw:
            return []

        # Normalise MaxSim scores
        max_score = max(p.score for p in raw) or 1.0
        query_terms = query_text.strip().split()
        blended: List[Dict[str, Any]] = []

        for point in raw:
            payload = point.payload or {}
            visual_score = point.score / max_score
            audio_score = self._lexical_score(query_terms, payload.get("transcript_text", ""))
            ocr_score = self._lexical_score(query_terms, payload.get("ocr_text", ""))

            blended_score = self.ALPHA * visual_score + self.BETA * audio_score + self.GAMMA * ocr_score

            blended.append(
                {
                    "point_id": point.id,
                    "video_id": payload.get("video_id"),
                    "video_filename": payload.get("video_filename"),
                    "dataset_source": payload.get("dataset_source", "UCF101"),
                    "start_time": payload.get("start_time", 0.0),
                    "end_time": payload.get("end_time", 2.0),
                    "transcript_text": payload.get("transcript_text", ""),
                    "ocr_text": payload.get("ocr_text", ""),
                    "keyframe_url": payload.get("keyframe_url", ""),
                    "visual_maxsim": round(visual_score, 4),
                    "audio_score": round(audio_score, 4),
                    "ocr_score": round(ocr_score, 4),
                    "blended_score": round(blended_score, 4),
                }
            )

        blended.sort(key=lambda x: x["blended_score"], reverse=True)
        return blended[:top_k]


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    r = HybridRetriever()
    print(f"HybridRetriever ready  α={r.ALPHA}  β={r.BETA}  γ={r.GAMMA}")

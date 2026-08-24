import logging
from typing import List, Optional

from packages.retrieval.late_interaction import LateInteractionRetriever, SceneResult
from packages.embeddings.query_encoder import encode_query
from .backend import VideoSearchBackend

logger = logging.getLogger(__name__)


class ColPaliRetrieverBackend(VideoSearchBackend):
    """
    Production video search backend backed by ColQwen2 multi-vector query encoding
    and Qdrant native MaxSim late-interaction retrieval with temporal deduplication.
    """

    def __init__(self, retriever: Optional[LateInteractionRetriever] = None):
        self.retriever = retriever or LateInteractionRetriever()

    def search(
        self,
        objective: str,
        video_source=None,
        top_k: int = 10,
    ) -> List[SceneResult]:
        """
        Encodes the visual objective text into ColQwen2 multi-vectors
        and executes MaxSim search on Qdrant.
        """
        try:
            query_vectors = encode_query(objective)
            if not query_vectors:
                logger.warning("Empty query vectors for objective: %s", objective)
                return []

            scenes = self.retriever.search(query_vectors, top_k=top_k)
            return scenes
        except Exception as exc:
            logger.error("ColPaliRetrieverBackend search failed for '%s': %s", objective, exc, exc_info=True)
            return []

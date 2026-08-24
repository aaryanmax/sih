from abc import ABC, abstractmethod
from typing import List, Optional

from packages.retrieval.late_interaction import SceneResult


class VideoSearchBackend(ABC):
    """
    Interface between Multi-Intent Search and the core
    video understanding/search system.

    Multi-Intent does not depend directly on Qdrant,
    embeddings, or a specific model implementation.
    """

    @abstractmethod
    def search(
        self,
        objective: str,
        video_source=None,
        top_k: int = 10,
    ) -> List[SceneResult]:
        """
        Search video content for a semantic objective.

        Parameters
        ----------
        objective:
            What type of video content we want to find.

        video_source:
            Raw video, collection of videos, or another
            video source supplied by the core system.

        top_k:
            Maximum number of results.

        Returns
        -------
        List[SceneResult]:
            Ranked relevant video scenes.
        """
        raise NotImplementedError

from typing import List

from packages.retrieval.late_interaction import SceneResult
from .backend import VideoSearchBackend


class MockVideoSearchBackend(VideoSearchBackend):
    """
    Mock backend used to test Multi-Intent orchestration
    and offline demonstration without GPU / Qdrant live instances.
    """

    def search(
        self,
        objective: str,
        video_source=None,
        top_k: int = 10,
    ) -> List[SceneResult]:
        # Return realistic mock scenes matching the objective
        return [
            SceneResult(
                video_id="mock_video_001",
                video_filename="mock_video.mp4",
                video_url="/videos/UCF101/lecture_colpali_part1.mp4",
                dataset_source="UCF101",
                start_time=2.0,
                end_time=14.0,
                score=0.96,
                transcript_text=f"Scene demonstrating {objective}",
                ocr_text="ColPali Multi-Vector Visual Matrix",
                chunk_ids=[1, 2],
            ),
            SceneResult(
                video_id="mock_video_002",
                video_filename="mock_video_2.mp4",
                video_url="/videos/UCF101/lecture_colpali_part2.mp4",
                dataset_source="UCF101",
                start_time=15.0,
                end_time=28.0,
                score=0.89,
                transcript_text=f"Detailed analysis of {objective}",
                ocr_text="Qdrant Native MaxSim Query Index",
                chunk_ids=[3, 4],
            ),
        ][:top_k]

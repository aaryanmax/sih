from __future__ import annotations

import logging
import os
import time
from pathlib import Path
from typing import Dict, List, Optional, Set

import numpy as np
from PIL import Image

from .faiss_index import ColPaliFaissIndex
from .gemini_reranker import rerank_results_with_gemini
from .ocr_extractor import OcrExtractor, text_match_score
from .video_loader import extract_frames_from_video, scan_video_directory
from .yolo_detector import YoloDetector, extract_object_keywords, object_boost_score

logger = logging.getLogger(__name__)


class ColPaliSearchPipeline:
    def __init__(
        self,
        proj_dim: int = 128,
        index_type: str = "hnsw",
        mode: str = "real",  # "real" -> Qwen2-VL encoders, "dummy" -> random vectors for plumbing tests
        use_yolo: bool = True,
        use_ocr: bool = True,
        yolo_boost: float = 0.5,
        ocr_boost: float = 0.3,
    ):
        self.proj_dim = proj_dim
        self.mode = mode
        self.index = ColPaliFaissIndex(dim=proj_dim, index_type=index_type)

        self.use_yolo = use_yolo
        self.use_ocr = use_ocr
        self.yolo_boost = yolo_boost
        self.ocr_boost = ocr_boost

        # Per-frame side signals collected at ingest time, used to
        # boost/re-rank at query time (object labels, OCR text).
        self._frame_object_labels: Dict[str, Set[str]] = {}
        self._frame_ocr_text: Dict[str, str] = {}

        self._patch_encoder = None
        self._query_encoder = None
        # In dummy mode we skip loading real YOLO/OCR models (no GPU/
        # downloads needed for plumbing tests) — frame_object_labels/
        # frame_ocr_text just stay empty, which the boost logic already
        # handles gracefully (falls back to 0 boost).
        self._yolo = YoloDetector() if (use_yolo and mode == "real") else None
        self._ocr = OcrExtractor() if (use_ocr and mode == "real") else None

        if mode == "real":
            from patch_encoder import PatchEncoder
            from query_encoder import QueryEncoder

            self._patch_encoder = PatchEncoder(proj_dim=proj_dim)
            self._query_encoder = QueryEncoder(proj_dim=proj_dim)
        elif mode != "dummy":
            raise ValueError("mode must be 'real' or 'dummy'")

        logger.info(
            "ColPaliSearchPipeline initialized: mode=%s proj_dim=%d yolo=%s ocr=%s",
            mode,
            proj_dim,
            use_yolo,
            use_ocr,
        )

    # ------------------------------------------------------------------
    def _encode_frame(self, image: Image.Image) -> np.ndarray:
        if self.mode == "dummy":
            n_patches = 64
            v = np.random.default_rng().normal(size=(n_patches, self.proj_dim)).astype(np.float32)
            return v / np.linalg.norm(v, axis=1, keepdims=True)
        return self._patch_encoder.encode_frame(image)

    def _encode_query(self, text: str) -> np.ndarray:
        if self.mode == "dummy":
            n_tokens = max(3, len(text.split()))
            v = np.random.default_rng().normal(size=(n_tokens, self.proj_dim)).astype(np.float32)
            return v / np.linalg.norm(v, axis=1, keepdims=True)
        return self._query_encoder.encode_query(text)

    # ------------------------------------------------------------------
    def ingest_video(
        self,
        video_id: str,
        frames: List[Image.Image],
        timestamps_s: Optional[List[float]] = None,
    ):
        """
        Encode and index every frame of a video.

        Args:
            video_id: identifier for the source video.
            frames: list of PIL frames (already extracted at ~2s intervals).
            timestamps_s: optional matching timestamps; defaults to
                          index * 2.0 seconds if not given.
        """
        if timestamps_s is None:
            timestamps_s = [i * 2.0 for i in range(len(frames))]

        t0 = time.time()

        # Parallel OCR extraction if enabled and in real mode
        ocr_texts = []
        if self.use_ocr and self._ocr is not None and self.mode == "real":
            logger.info("Extracting OCR text across %d frames in parallel...", len(frames))
            ocr_texts = self._ocr.extract_text_parallel(frames, max_workers=4)

        for idx, (frame, ts) in enumerate(zip(frames, timestamps_s)):
            frame_id = f"{video_id}_t{ts:g}s"
            patch_vectors = self._encode_frame(frame)
            self.index.add_frame(frame_id, patch_vectors)

            if self.use_yolo and self._yolo is not None:
                self._frame_object_labels[frame_id] = self._yolo.detect_labels(frame)

            if ocr_texts and idx < len(ocr_texts):
                self._frame_ocr_text[frame_id] = ocr_texts[idx]
            elif self.use_ocr and self._ocr is not None:
                self._frame_ocr_text[frame_id] = self._ocr.extract_text(frame)

        logger.info(
            "Ingested video '%s': %d frames in %.2fs",
            video_id,
            len(frames),
            time.time() - t0,
        )

    def ingest_video_file(
        self,
        video_path: str,
        video_id: Optional[str] = None,
        interval_sec: float = 2.0,
        save_thumbnails_dir: Optional[str] = None,
    ):
        """
        Extracts frames and timestamps from a real video file (.mp4, etc.) using OpenCV
        and indexes them end-to-end.
        """
        if video_id is None:
            video_id = Path(video_path).stem

        frames, timestamps = extract_frames_from_video(
            video_path=video_path,
            interval_sec=interval_sec,
            save_thumbnails_dir=save_thumbnails_dir,
        )

        self.ingest_video(video_id=video_id, frames=frames, timestamps_s=timestamps)

    def ingest_directory(
        self,
        directory_path: str,
        interval_sec: float = 2.0,
        save_thumbnails: bool = False,
    ):
        """
        Scans a directory for all video files (.mp4, .avi, etc.) and ingests each one.
        """
        video_files = scan_video_directory(directory_path)
        logger.info("Found %d video files in '%s'", len(video_files), directory_path)

        for v_path in video_files:
            thumb_dir = os.path.join(directory_path, "thumbnails", Path(v_path).stem) if save_thumbnails else None
            self.ingest_video_file(
                video_path=v_path,
                interval_sec=interval_sec,
                save_thumbnails_dir=thumb_dir,
            )

    def finalize_index(self):
        """Call once after all videos are ingested (required for IVF index
        type; harmless no-op for flat/hnsw)."""
        self.index.build()

    def search(
        self,
        query_text: str,
        top_k: int = 10,
        candidate_pool: int = 200,
        object_mode: str = "boost",  # "boost" | "filter" | "off"
        use_gemini: bool = False,
        gemini_api_key: Optional[str] = None,
        primary_model: str = "gemini-3.5-flash-lite",
        fallback_model: str = "gemini-3.1-flash-lite",
    ):
        """
        Search the indexed corpus for the given natural-language query.

        If the query mentions a COCO object (e.g. "red car", "dog"):
          - object_mode="filter": only frames where YOLO detected that
            object are searched at all.
          - object_mode="boost" (default): all frames are searched, but
            matching YOLO labels and OCR text add a score bonus.
          - object_mode="off": ignore YOLO/OCR signals entirely.

        Returns:
            List of dicts: {"frame_id", "video_id", "timestamp_s", "score",
                             "colpali_score", "object_boost", "ocr_boost", "ocr_text"}
        """
        t0 = time.time()
        query_vectors = self._encode_query(query_text)

        # -- Optional YOLO pre-filter (shrinks search space further) -----
        if self.use_yolo and object_mode == "filter" and self._frame_object_labels:
            keywords = extract_object_keywords(query_text)
            if keywords:
                allowed_frames = {fid for fid, labels in self._frame_object_labels.items() if keywords.issubset(labels)}
                logger.info(
                    "Object pre-filter active: %d/%d frames match %s",
                    len(allowed_frames),
                    len(self._frame_object_labels),
                    keywords,
                )
                raw_results = self.index.search_within(query_vectors, allowed_frames, top_k=candidate_pool)
            else:
                raw_results = self.index.search(query_vectors, top_k=candidate_pool, candidate_pool=candidate_pool)
        else:
            raw_results = self.index.search(query_vectors, top_k=candidate_pool, candidate_pool=candidate_pool)

        # -- Apply boosts, then re-sort, then trim to top_k ---------------
        results = []
        for frame_id, colpali_score in raw_results:
            video_id, _, ts_part = frame_id.rpartition("_t")
            timestamp_s = float(ts_part.rstrip("s")) if ts_part else 0.0

            obj_boost = 0.0
            ocr_boost_val = 0.0
            ocr_text = self._frame_ocr_text.get(frame_id, "")
            if object_mode == "boost":
                if self.use_yolo:
                    labels = self._frame_object_labels.get(frame_id, set())
                    obj_boost = object_boost_score(query_text, labels, boost=self.yolo_boost)
                if self.use_ocr:
                    ocr_boost_val = self.ocr_boost * text_match_score(query_text, ocr_text)

            final_score = colpali_score + obj_boost + ocr_boost_val
            results.append(
                {
                    "frame_id": frame_id,
                    "video_id": video_id,
                    "timestamp_s": timestamp_s,
                    "score": final_score,
                    "colpali_score": colpali_score,
                    "object_boost": obj_boost,
                    "ocr_boost": ocr_boost_val,
                    "ocr_text": ocr_text,
                }
            )

        results.sort(key=lambda r: r["score"], reverse=True)
        results = results[:top_k]

        # -- Optional Stage 3: Gemini Multimodal LLM Reranking -----------
        if use_gemini and results:
            results = rerank_results_with_gemini(
                query=query_text,
                top_results=results,
                api_key=gemini_api_key,
                model_name=primary_model,
                fallback_model=fallback_model,
            )

        elapsed_ms = (time.time() - t0) * 1000

        logger.info(
            "Search '%s' (object_mode=%s, use_gemini=%s) -> %d results in %.1fms",
            query_text,
            object_mode,
            use_gemini,
            len(results),
            elapsed_ms,
        )
        return results

    def save(self, path_prefix: str):
        import pickle

        self.index.save(path_prefix)
        with open(f"{path_prefix}.pipeline_meta.pkl", "wb") as f:
            pickle.dump(
                {
                    "use_yolo": self.use_yolo,
                    "use_ocr": self.use_ocr,
                    "yolo_boost": self.yolo_boost,
                    "ocr_boost": self.ocr_boost,
                    "frame_object_labels": self._frame_object_labels,
                    "frame_ocr_text": self._frame_ocr_text,
                },
                f,
            )

    @classmethod
    def load(cls, path_prefix: str, proj_dim: int = 128, mode: str = "real") -> "ColPaliSearchPipeline":
        import pickle

        obj = cls.__new__(cls)
        obj.proj_dim = proj_dim
        obj.mode = mode
        obj.index = ColPaliFaissIndex.load(path_prefix)
        obj._patch_encoder = None
        obj._query_encoder = None

        # Restore YOLO/OCR settings + collected labels/text.
        with open(f"{path_prefix}.pipeline_meta.pkl", "rb") as f:
            meta = pickle.load(f)
        obj.use_yolo = meta["use_yolo"]
        obj.use_ocr = meta["use_ocr"]
        obj.yolo_boost = meta["yolo_boost"]
        obj.ocr_boost = meta["ocr_boost"]
        obj._frame_object_labels = meta["frame_object_labels"]
        obj._frame_ocr_text = meta["frame_ocr_text"]
        obj._yolo = None  # lazy-loaded on demand if needed later
        obj._ocr = None

        if mode == "real":
            from patch_encoder import PatchEncoder
            from query_encoder import QueryEncoder

            obj._patch_encoder = PatchEncoder(proj_dim=proj_dim)
            obj._query_encoder = QueryEncoder(proj_dim=proj_dim)
        return obj


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    # Dummy mode: verifies the full ingest -> index -> search plumbing
    # without needing GPU / model downloads. Switch mode="real" once you're
    # ready to run against actual Qwen2-VL + real video frames.
    pipeline = ColPaliSearchPipeline(proj_dim=128, index_type="hnsw", mode="dummy")

    # Simulate ingesting 3 short videos, 10 frames (~20s) each
    for vid_idx in range(3):
        fake_frames = [Image.new("RGB", (224, 224)) for _ in range(10)]
        pipeline.ingest_video(f"video_{vid_idx}", fake_frames)

    pipeline.finalize_index()

    results = pipeline.search("a person walking a dog in a park", top_k=5)
    print("\nTop 5 results:")
    for r in results:
        print(f"  {r['video_id']} @ {r['timestamp_s']}s -> score={r['score']:.4f}")



from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import List, Optional, Tuple

import cv2
from PIL import Image

logger = logging.getLogger(__name__)

SUPPORTED_VIDEO_EXTENSIONS = {".mp4", ".avi", ".mov", ".mkv", ".webm", ".flv"}


def extract_frames_from_video(
    video_path: str,
    interval_sec: float = 2.0,
    max_frames: Optional[int] = None,
    save_thumbnails_dir: Optional[str] = None,
) -> Tuple[List[Image.Image], List[float]]:
    """
    Extracts frames from a video file at specified second intervals.

    Args:
        video_path: Path to the .mp4 or other video file.
        interval_sec: Interval in seconds between extracted frames (default 2.0s).
        max_frames: Optional maximum number of frames to extract.
        save_thumbnails_dir: Optional directory path to save JPG thumbnails of extracted frames.

    Returns:
        tuple (frames_list, timestamps_list) where:
            frames_list: List of PIL.Image (RGB) objects
            timestamps_list: List of float timestamps in seconds
    """
    if not os.path.exists(video_path):
        raise FileNotFoundError(f"Video file not found: {video_path}")

    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise ValueError(f"Could not open video file: {video_path}")

    fps = cap.get(cv2.CAP_PROP_FPS)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    duration_s = total_frames / fps if fps > 0 else 0.0

    if fps <= 0 or total_frames <= 0:
        cap.release()
        raise ValueError(f"Invalid video metadata (fps={fps}, total_frames={total_frames}) for {video_path}")

    logger.info(
        "Loading video '%s': duration=%.1fs, total_frames=%d, fps=%.2f, interval=%.1fs",
        os.path.basename(video_path),
        duration_s,
        total_frames,
        fps,
        interval_sec,
    )

    frame_step = max(1, int(round(fps * interval_sec)))

    frames: List[Image.Image] = []
    timestamps: List[float] = []

    if save_thumbnails_dir:
        os.makedirs(save_thumbnails_dir, exist_ok=True)

    current_frame_idx = 0
    extracted_count = 0

    while True:
        # Set exact frame position for fast seeking
        cap.set(cv2.CAP_PROP_POS_FRAMES, current_frame_idx)
        ret, bgr_frame = cap.read()

        if not ret or bgr_frame is None:
            break

        timestamp_s = round(current_frame_idx / fps, 2)

        # Convert BGR (OpenCV) to RGB (PIL)
        rgb_frame = cv2.cvtColor(bgr_frame, cv2.COLOR_BGR2RGB)
        pil_img = Image.fromarray(rgb_frame)

        frames.append(pil_img)
        timestamps.append(timestamp_s)

        if save_thumbnails_dir:
            thumb_path = os.path.join(save_thumbnails_dir, f"frame_{extracted_count:04d}_{timestamp_s:g}s.jpg")
            pil_img.save(thumb_path, "JPEG", quality=85)

        extracted_count += 1
        if max_frames and extracted_count >= max_frames:
            break

        current_frame_idx += frame_step
        if current_frame_idx >= total_frames:
            break

    cap.release()
    logger.info(
        "Extracted %d frames from '%s' (timestamps from %.1fs to %.1fs)",
        len(frames),
        os.path.basename(video_path),
        timestamps[0] if timestamps else 0.0,
        timestamps[-1] if timestamps else 0.0,
    )

    return frames, timestamps


def scan_video_directory(directory_path: str) -> List[str]:
    """
    Finds all supported video files within a directory.
    """
    if not os.path.exists(directory_path):
        return []

    video_files = []
    for root, _, files in os.walk(directory_path):
        for f in files:
            ext = Path(f).suffix.lower()
            if ext in SUPPORTED_VIDEO_EXTENSIONS:
                video_files.append(os.path.join(root, f))

    video_files.sort()
    return video_files

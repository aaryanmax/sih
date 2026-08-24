"""
packages/pipeline/url_ingest.py
-------------------------------
Live URL ingestion pipeline.
Downloads a YouTube Short, Instagram Reel, or TikTok using yt-dlp,
extracts multimodal visual features using AI frame analysis, and indexes them into Qdrant.
Includes deduplication so existing videos are never re-downloaded or re-indexed.
"""

from __future__ import annotations

import hashlib
import json
import logging
import os
import re
import subprocess
import sys
import uuid
from pathlib import Path
from typing import Optional

# Add project root to sys path
_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(_ROOT))

import shutil

from qdrant_client import QdrantClient
from qdrant_client.models import FieldCondition, Filter, MatchValue, PointStruct

from packages.embeddings.query_encoder import encode_query
from packages.pipeline.frame_analyzer import analyze_video_frames
from packages.retrieval.seed_qdrant import COLLECTION_NAME, VECTOR_NAME, get_data_dir

logger = logging.getLogger(__name__)


# Cross-platform yt-dlp executable discovery with fallbacks
def _find_yt_dlp() -> str:
    # 1. Environment variable override
    env_path = os.getenv("YT_DLP_PATH")
    if env_path and (os.path.exists(env_path) or shutil.which(env_path)):
        return env_path
    # 2. System PATH
    found = shutil.which("yt-dlp") or shutil.which("yt-dlp.exe")
    if found:
        return found
    # 3. Common Windows tool paths
    for fallback in [r"C:\tools\YT-DLP\yt-dlp.exe", r"C:\Program Files\yt-dlp\yt-dlp.exe"]:
        if os.path.exists(fallback):
            return fallback
    # 4. Default fallback
    return "yt-dlp"


YT_DLP_PATH = _find_yt_dlp()


def extract_canonical_video_id(url: str) -> str:
    """
    Extracts a clean, canonical video ID from YouTube, Instagram Reels, TikTok, or generic URLs.
    Example:
      - https://www.youtube.com/watch?v=p44VNddZ7Zc -> yt_p44VNddZ7Zc
      - https://www.youtube.com/shorts/p44VNddZ7Zc  -> yt_p44VNddZ7Zc
      - https://www.instagram.com/reel/C8xyz123/   -> ig_C8xyz123
      - https://www.tiktok.com/@user/video/1234567 -> tt_1234567
    """
    url = url.strip()

    # YouTube (Watch, Shorts, youtu.be, Embed)
    yt_m = re.search(r"(?:v=|\/shorts\/|youtu\.be\/|embed\/)([a-zA-Z0-9_-]{11})", url)
    if yt_m:
        return f"yt_{yt_m.group(1)}"

    # Instagram Reels / Posts
    ig_m = re.search(r"instagram\.com\/(?:reel|reels|p)\/([a-zA-Z0-9_-]+)", url)
    if ig_m:
        return f"ig_{ig_m.group(1)}"

    # TikTok
    tt_m = re.search(r"tiktok\.com\/@[^/]+\/video\/(\d+)", url)
    if tt_m:
        return f"tt_{tt_m.group(1)}"

    # Generic fallback: deterministic SHA-256 hash of the cleaned URL
    clean_url = url.split("?")[0].rstrip("/")
    url_hash = hashlib.sha256(clean_url.encode("utf-8")).hexdigest()[:12]
    return f"vid_{url_hash}"


def download_video(url: str, output_dir: Path, canonical_id: str) -> tuple[str, str]:
    """
    Downloads a video from a URL using yt-dlp and returns (filename, video_title).
    Ensures universal web compatibility with H.264 video and AAC audio in an MP4 container.
    """
    output_template = str((output_dir / f"{canonical_id}.%(ext)s").resolve())

    # First get video title
    video_title = "Short Video"
    try:
        title_res = subprocess.run(
            [YT_DLP_PATH, url, "--print", "%(title)s", "--no-playlist"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        if title_res.returncode == 0 and title_res.stdout.strip():
            video_title = title_res.stdout.strip()
    except Exception as e:
        logger.warning(f"Could not retrieve video title: {e}")

    cmd = [
        YT_DLP_PATH,
        url,
        "-f",
        "bestvideo[vcodec^=avc1][ext=mp4]+bestaudio[acodec^=mp4a]/best[vcodec^=avc1][ext=mp4]/18/best",
        "-o",
        output_template,
        "--no-playlist",
    ]

    logger.info("Downloading short video '%s' (ID: %s) from %s...", video_title, canonical_id, url)
    try:
        subprocess.run(cmd, check=True, capture_output=True, text=True)
        downloaded_files = list(output_dir.glob(f"{canonical_id}.*"))
        if not downloaded_files:
            raise FileNotFoundError("Video downloaded but file not found.")
        return downloaded_files[0].name, video_title
    except subprocess.CalledProcessError as e:
        logger.error("yt-dlp download failed: %s", e.stderr)
        raise RuntimeError(f"Failed to download video: {e.stderr}")


def is_video_indexed(filename: str, client: Optional[QdrantClient] = None) -> bool:
    """Checks if points for the given filename already exist in Qdrant."""
    if client is None:
        return False
    try:
        points, _ = client.scroll(
            collection_name=COLLECTION_NAME,
            scroll_filter=Filter(must=[FieldCondition(key="video_filename", match=MatchValue(value=filename))]),
            limit=1,
        )
        return len(points) > 0
    except Exception as e:
        logger.warning(f"Could not check existing Qdrant points for {filename}: {e}")
        return False


def process_and_index_video(
    filename: str, video_dir: Path, video_title: str = "Short Video", client: Optional[QdrantClient] = None
) -> str:
    """
    Analyzes visual keyframes and indexes fine-grained temporal moments into Qdrant.
    """
    video_path = video_dir / filename
    if not video_path.exists():
        raise FileNotFoundError(f"Video file {video_path} does not exist.")

    logger.info("Processing short video %s ('%s') with AI visual frame analysis...", filename, video_title)
    video_id = str(uuid.uuid5(uuid.NAMESPACE_URL, filename))

    # Extract AI visual temporal scenes
    scenes = analyze_video_frames(video_path, video_title=video_title)

    # Connect to Qdrant if not provided
    if client is None:
        data_dir = get_data_dir()
        client = QdrantClient(path=str(data_dir))

    points_buffer = []

    for idx, sc in enumerate(scenes):
        start_time = float(sc.get("start_time", idx * 3.0))
        end_time = float(sc.get("end_time", start_time + 3.0))
        action_text = sc.get("action", f"Scene {idx + 1}")
        keywords = sc.get("keywords", action_text)

        # Build multi-vector representation from action + synonyms
        prompt = f"{video_title} {action_text} {keywords}"
        multi_vec = encode_query(prompt)

        point_id = int(uuid.uuid4().int >> 64)
        point_id = abs(point_id) or 1

        payload = {
            "video_id": video_id,
            "video_filename": filename,
            "video_title": video_title,
            "dataset_source": "Live Ingest",
            "start_time": start_time,
            "end_time": end_time,
            "transcript_text": f"{video_title} — {action_text}",
            "ocr_text": keywords,
        }

        points_buffer.append(
            PointStruct(
                id=point_id,
                vector={VECTOR_NAME: multi_vec},
                payload=payload,
            )
        )

    client.upsert(
        collection_name=COLLECTION_NAME,
        points=points_buffer,
    )
    logger.info("Successfully indexed %d visual moments for %s ('%s').", len(points_buffer), filename, video_title)
    return video_id


def download_and_process_url(url: str, client: Optional[QdrantClient] = None, force: bool = False) -> dict:
    """
    End-to-end ingestion pipeline with canonical naming and deduplication:
    1. Extracts canonical video ID from URL (e.g. yt_p44VNddZ7Zc, ig_C8xyz123).
    2. If the video is already downloaded and indexed, returns cached result immediately (unless force=True).
    3. If the video file exists on disk but is not indexed, indexes it without re-downloading.
    4. If the video does not exist, downloads it cleanly and indexes all visual moments.
    """
    output_dir = _ROOT / "apps" / "web" / "public" / "videos" / "shorts"
    output_dir.mkdir(parents=True, exist_ok=True)

    canonical_id = extract_canonical_video_id(url)
    target_filename = f"{canonical_id}.mp4"
    target_filepath = output_dir / target_filename

    # ── Step 1: Check if already downloaded ──
    if target_filepath.exists() and target_filepath.stat().st_size > 0:
        if not force and is_video_indexed(target_filename, client=client):
            logger.info("Video '%s' is already downloaded and indexed. Skipping duplicate work.", target_filename)
            return {
                "status": "success",
                "message": "Video already downloaded and indexed (cached)",
                "video_id": str(uuid.uuid5(uuid.NAMESPACE_URL, target_filename)),
                "video_title": canonical_id,
                "filename": target_filename,
                "public_url": f"/videos/shorts/{target_filename}",
                "cached": True,
            }
        else:
            # File exists on disk -> index directly with Gemini Vision
            logger.info("Video file '%s' exists on disk. Skipping download, indexing directly...", target_filename)
            video_title = canonical_id
            try:
                title_res = subprocess.run(
                    [YT_DLP_PATH, url, "--print", "%(title)s", "--no-playlist"],
                    capture_output=True,
                    text=True,
                    timeout=10,
                )
                if title_res.returncode == 0 and title_res.stdout.strip():
                    video_title = title_res.stdout.strip()
            except Exception:
                pass
            video_id = process_and_index_video(target_filename, output_dir, video_title=video_title, client=client)
            return {
                "status": "success",
                "video_id": video_id,
                "video_title": canonical_id,
                "filename": target_filename,
                "public_url": f"/videos/shorts/{target_filename}",
                "cached_download": True,
            }

    # ── Step 2: Download video with canonical ID ──
    filename, video_title = download_video(url, output_dir, canonical_id=canonical_id)
    video_id = process_and_index_video(filename, output_dir, video_title=video_title, client=client)

    return {
        "status": "success",
        "video_id": video_id,
        "video_title": video_title,
        "filename": filename,
        "public_url": f"/videos/shorts/{filename}",
    }


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python url_ingest.py <youtube_or_instagram_url>")
        sys.exit(1)

    result = download_and_process_url(sys.argv[1])
    print(f"Ingestion complete: {result}")

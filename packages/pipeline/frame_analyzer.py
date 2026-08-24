"""
packages/pipeline/frame_analyzer.py
-----------------------------------
Automated Frame-Level Temporal Scene Analyzer for Short Videos (Reels, TikToks, Shorts).
Extracts video keyframes and uses Gemini Vision to detect exact visual moments, actions,
and synonyms across the entire video timeline without requiring pre-existing chapters.
"""

from __future__ import annotations

import json
import logging
import os
import shutil
import subprocess
from pathlib import Path
from typing import Any, Dict, List, Optional

from PIL import Image

logger = logging.getLogger(__name__)


def extract_video_duration(video_path: Path) -> float:
    """Returns video duration in seconds using ffprobe."""
    try:
        cmd = [
            "ffprobe",
            "-v",
            "error",
            "-show_entries",
            "format=duration",
            "-of",
            "default=noprint_wrappers=1:nokey=1",
            str(video_path),
        ]
        res = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
        return float(res.stdout.strip())
    except Exception as e:
        logger.warning(f"Could not determine video duration via ffprobe: {e}")
        return 30.0


def analyze_video_frames(
    video_path: Path, video_title: str = "Short Video", api_key: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Extracts frames every few seconds from a short video and uses Gemini Vision
    to generate fine-grained temporal actions, scene timestamps, and synonyms.
    """
    duration = extract_video_duration(video_path)
    logger.info("Analyzing short video %s (duration: %.1fs)...", video_path.name, duration)

    # Determine frame sampling interval (aiming for 8-15 frames total)
    if duration <= 15:
        interval = 2.0
    elif duration <= 60:
        interval = 4.0
    elif duration <= 180:
        interval = 10.0
    else:
        interval = 20.0

    temp_dir = video_path.parent / f"_frames_{video_path.stem}"
    temp_dir.mkdir(parents=True, exist_ok=True)

    try:
        # Extract frames using ffmpeg
        output_pattern = str(temp_dir / "f_%03d.jpg")
        cmd = ["ffmpeg", "-y", "-i", str(video_path), "-vf", f"fps=1/{interval}", "-q:v", "2", output_pattern]
        subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        frame_files = sorted(list(temp_dir.glob("f_*.jpg")))

        if not frame_files:
            logger.warning("No frames extracted with ffmpeg; falling back to default intervals.")
            return _generate_fallback_scenes(duration, video_title)

        # Call Gemini Vision if API key is present
        if not api_key:
            api_key = os.getenv("GEMINI_API_KEY")
            if not api_key:
                for env_path in [Path(".env"), Path(__file__).resolve().parents[2] / ".env"]:
                    if env_path.exists():
                        try:
                            with env_path.open("r", encoding="utf-8") as f:
                                for line in f:
                                    if line.strip().startswith("GEMINI_API_KEY="):
                                        api_key = line.strip().split("=", 1)[1].strip().strip("'\"")
                                        break
                        except Exception:
                            pass
                    if api_key:
                        break

        if api_key:
            try:
                from google import genai
                from google.genai import types

                client = genai.Client(api_key=api_key)

                contents: List[Any] = [
                    "You are an expert video temporal moment indexing AI. Analyze these sequential frames from a video. "
                    "For every distinct action or stage, output a strict JSON array of temporal moments with exact start_time (seconds), end_time (seconds), "
                    "detailed action description, and comprehensive keywords. "
                    "Crucial: In 'keywords', include ALL natural search queries, common synonyms, and verb forms for the visual actions seen "
                    "(for example: 'open, opened, opening, disassemble, disassembling, taken apart, taking apart, separate, separated, reassemble, reassembled, reassembling, assemble, assembled, put together, putting together, clean, cleaning, spray, jet, wire'). "
                    'Format: [{"start_time": 0.0, "end_time": 4.0, "action": "description of what happens", "keywords": "synonyms keywords action names phrases"}]'
                ]

                for idx, f in enumerate(frame_files[:16]):
                    timestamp = idx * interval
                    contents.append(f"Timestamp {timestamp:.1f}s:")
                    try:
                        contents.append(Image.open(f))
                    except Exception:
                        pass

                models_to_try = ["gemini-3.5-flash-lite", "gemini-3.1-flash-lite"]

                resp = None
                last_err = None
                for model_id in models_to_try:
                    try:
                        resp = client.models.generate_content(
                            model=model_id,
                            contents=contents,
                            config=types.GenerateContentConfig(
                                response_mime_type="application/json",
                                temperature=0.2,
                            ),
                        )
                        break
                    except Exception as e:
                        last_err = e
                        logger.warning("Model %s failed: %s", model_id, e)

                if resp is None and last_err:
                    raise last_err

                if resp.text:
                    parsed = json.loads(resp.text)
                    if isinstance(parsed, list) and len(parsed) > 0:
                        logger.info(
                            "Gemini generated %d fine-grained visual scenes for %s.", len(parsed), video_path.name
                        )
                        return parsed
                else:
                    logger.warning("Gemini Vision returned empty response text.")

            except Exception as e:
                logger.error(
                    f"Gemini frame analysis failed for {video_path.name}: {type(e).__name__} - {e}", exc_info=True
                )

    finally:
        # Cleanup temporary frames
        try:
            shutil.rmtree(temp_dir, ignore_errors=True)
        except Exception:
            pass

    return _generate_fallback_scenes(duration, video_title)


def _generate_fallback_scenes(duration: float, title: str) -> List[Dict[str, Any]]:
    """Generates evenly spaced scene segments if AI frame analysis fails."""
    step = max(3.0, duration / 6.0)
    scenes = []
    t = 0.0
    idx = 1
    while t < duration:
        end = min(duration, t + step)
        scenes.append(
            {
                "start_time": round(t, 2),
                "end_time": round(end, 2),
                "action": f"{title} — Part {idx}",
                "keywords": f"{title} part {idx} action moment",
            }
        )
        t += step
        idx += 1
    return scenes

"""
scripts/reindex_local_videos.py
--------------------------------
Scans all local videos in apps/web/public/videos/shorts/ and indexes them
100% locally on your machine (GPU/CPU) into Qdrant (data/ storage)
with ZERO cloud calls (No Gemini, No HuggingFace Hub network requests).
"""

import os
import sys
import uuid
from pathlib import Path

# Force offline mode for Hugging Face / Transformers
os.environ["HF_HUB_OFFLINE"] = "1"
os.environ["TRANSFORMERS_OFFLINE"] = "1"

# Add project root to sys path
_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ROOT))
sys.path.insert(0, str(_ROOT / "packages"))

from qdrant_client import QdrantClient
from qdrant_client.models import PointStruct

from packages.embeddings.query_encoder import encode_query
from packages.pipeline_engine.ocr_extractor import OcrExtractor
from packages.pipeline_engine.video_loader import extract_frames_from_video
from packages.pipeline_engine.yolo_detector import YoloDetector
from packages.retrieval.seed_qdrant import COLLECTION_NAME, VECTOR_NAME, get_data_dir


def index_video_locally(
    video_path: Path,
    client: QdrantClient,
    yolo: YoloDetector,
    ocr: OcrExtractor,
    interval_sec: float = 2.5,
) -> int:
    """
    Extracts frames using OpenCV, runs local YOLOv8 and OCR,
    generates local ColQwen multi-vector embeddings, and saves into Qdrant.
    Runs 100% locally on GPU/CPU with no cloud dependencies.
    """
    filename = video_path.name
    clean_title = filename.replace(".mp4", "").replace("yt_", "").replace("ig_", "").replace("vid_", "")
    # Clean up hashtags and underscores
    clean_title = clean_title.replace("_", " ").split("#")[0].strip()
    video_id = str(uuid.uuid5(uuid.NAMESPACE_URL, filename))

    # 1. Extract frames locally via OpenCV
    frames, timestamps = extract_frames_from_video(str(video_path), interval_sec=interval_sec)
    if not frames:
        print(f"  ⚠️ No frames could be extracted from {filename}")
        return 0

    points_buffer = []

    for idx, (frame, t_start) in enumerate(zip(frames, timestamps)):
        t_end = round(t_start + interval_sec, 2)

        # 2. Local vision analysis (YOLOv8 objects + Tesseract OCR)
        detected_objects = yolo.detect_labels(frame) if yolo else set()
        object_str = " ".join(sorted(detected_objects)) if detected_objects else ""

        ocr_text = ocr.extract_text(frame).strip() if ocr else ""

        # 3. Form semantic description for local multi-vector projection
        desc_parts = [clean_title]
        if object_str:
            desc_parts.append(f"shows {object_str}")
        if ocr_text:
            desc_parts.append(f"text: {ocr_text}")

        prompt = " | ".join(desc_parts)

        # 4. Generate local ColQwen multi-vector embedding
        multi_vec = encode_query(prompt)

        point_id = int(uuid.uuid4().int >> 64)
        point_id = abs(point_id) or 1

        payload = {
            "video_id": video_id,
            "video_filename": filename,
            "video_title": clean_title,
            "dataset_source": "shorts",
            "start_time": t_start,
            "end_time": t_end,
            "transcript_text": f"{clean_title} — {object_str}".strip(" —"),
            "ocr_text": ocr_text,
        }

        points_buffer.append(
            PointStruct(
                id=point_id,
                vector={VECTOR_NAME: multi_vec},
                payload=payload,
            )
        )

    if points_buffer:
        client.upsert(
            collection_name=COLLECTION_NAME,
            points=points_buffer,
        )

    return len(points_buffer)


def main():
    shorts_dir = _ROOT / "apps" / "web" / "public" / "videos" / "shorts"
    if not shorts_dir.exists():
        print(f"[ERROR] Directory {shorts_dir} does not exist.")
        return

    video_files = list(shorts_dir.glob("*.mp4"))
    print("=" * 65)
    print("  [LOCAL VIDEO INDEXING] 100% Offline / Local GPU & CPU")
    print("=" * 65)
    print(f"Found Videos       : {len(video_files)} local videos")
    print(f"Target Qdrant Path : {_ROOT / 'data'}")
    print(f"Collection         : {COLLECTION_NAME}")
    print("Local YOLO Detector: Initializing YOLOv8...")
    yolo = YoloDetector()
    print("Local OCR Engine   : Initializing Tesseract...")
    ocr = OcrExtractor()
    print("=" * 65)

    data_dir = get_data_dir()
    client = QdrantClient(path=str(data_dir))

    total_moments = 0
    for idx, vfile in enumerate(video_files, 1):
        filename = vfile.name
        print(f"[{idx}/{len(video_files)}] Indexing locally: {filename[:50]}...")
        try:
            count = index_video_locally(vfile, client, yolo, ocr, interval_sec=2.5)
            total_moments += count
            print(f"  [OK] Indexed {count} local visual moments")
        except Exception as e:
            print(f"  [ERROR] Error indexing {filename}: {e}")

    print("\n" + "=" * 65)
    print("Local video indexing complete!")
    print(f"Indexed a total of {total_moments} moments across {len(video_files)} videos.")
    print(f"All data stored locally in {_ROOT / 'data'}")
    print("=" * 65)


if __name__ == "__main__":
    main()

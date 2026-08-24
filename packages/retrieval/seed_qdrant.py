"""
packages/retrieval/seed_qdrant.py
---------------------------------
High-speed batch seeder that loads pre-indexed video multi-vector records
from data/qdrant_payload_500.json into the local Qdrant collection ('video_frames').
"""

import json
import logging
import os
import sys
import uuid
from pathlib import Path
from typing import Any, Dict, List

from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance,
    MultiVectorComparator,
    MultiVectorConfig,
    PointStruct,
    VectorParams,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)

COLLECTION_NAME = os.getenv("QDRANT_COLLECTION", "video_frames")
VECTOR_NAME = os.getenv("QDRANT_VECTOR_NAME", "colqwen")
VECTOR_DIM = 128
BATCH_SIZE = 100


def get_data_dir() -> Path:
    current = Path(__file__).resolve()
    # Go up from packages/retrieval/seed_qdrant.py to project root
    root = current.parents[2]
    return root / "data"


def seed_qdrant(force_recreate: bool = False) -> int:
    data_dir = get_data_dir()
    payload_file = data_dir / "qdrant_payload_500.json"

    if not payload_file.exists():
        raise FileNotFoundError(f"Payload file not found at: {payload_file}")

    logger.info("Connecting to local Qdrant embedded store at: %s", data_dir)
    client = QdrantClient(path=str(data_dir))

    collections = [c.name for c in client.get_collections().collections]
    logger.info("Found existing collections: %s", collections)

    collection_exists = COLLECTION_NAME in collections

    if force_recreate or not collection_exists:
        if collection_exists:
            logger.info("Recreating collection '%s'...", COLLECTION_NAME)
            client.delete_collection(collection_name=COLLECTION_NAME)

        logger.info(
            "Creating collection '%s' with vector '%s' (dim=%d, MaxSim)...", COLLECTION_NAME, VECTOR_NAME, VECTOR_DIM
        )
        client.create_collection(
            collection_name=COLLECTION_NAME,
            vectors_config={
                VECTOR_NAME: VectorParams(
                    size=VECTOR_DIM,
                    distance=Distance.DOT,
                    multivector_config=MultiVectorConfig(comparator=MultiVectorComparator.MAX_SIM),
                )
            },
        )
    else:
        existing_count = client.count(collection_name=COLLECTION_NAME).count
        logger.info("Collection '%s' already exists with %d points.", COLLECTION_NAME, existing_count)
        if existing_count > 0 and not force_recreate:
            logger.info("Collection already populated. Skipping ingestion (use force_recreate=True to overwrite).")
            return existing_count

    logger.info("Reading JSON payload from %s...", payload_file)
    with open(payload_file, "r", encoding="utf-8") as f:
        records = json.load(f)

    total_records = len(records)
    logger.info("Loaded %d records. Beginning batch upsert (batch_size=%d)...", total_records, BATCH_SIZE)

    points_buffer: List[PointStruct] = []
    total_upserted = 0

    for idx, item in enumerate(records):
        multi_vec = item.get("visual_multi_vector")
        if not multi_vec:
            continue

        point_id = idx + 1  # Integer ID for fast indexing
        payload = {
            "video_id": item.get("video_id", f"video_{idx}"),
            "video_filename": item.get("video_filename", f"video_{idx}.avi"),
            "dataset_source": item.get("dataset_source", "MSVD"),
            "timestamp": float(item.get("timestamp", 0.0)),
            "start_time": float(item.get("start_time", 0.0)),
            "end_time": float(item.get("end_time", 2.0)),
            "transcript_text": item.get("transcript_text", ""),
            "ocr_text": item.get("ocr_text", ""),
        }

        points_buffer.append(
            PointStruct(
                id=point_id,
                vector={VECTOR_NAME: multi_vec},
                payload=payload,
            )
        )

        if len(points_buffer) >= BATCH_SIZE:
            client.upsert(
                collection_name=COLLECTION_NAME,
                points=points_buffer,
            )
            total_upserted += len(points_buffer)
            logger.info(
                "Upserted %d / %d points (%.1f%%)...",
                total_upserted,
                total_records,
                (total_upserted / total_records) * 100,
            )
            points_buffer = []

    if points_buffer:
        client.upsert(
            collection_name=COLLECTION_NAME,
            points=points_buffer,
        )
        total_upserted += len(points_buffer)

    final_count = client.count(collection_name=COLLECTION_NAME).count
    logger.info("✅ Finished! Total points in collection '%s': %d", COLLECTION_NAME, final_count)
    return final_count


if __name__ == "__main__":
    force = "--force" in sys.argv or "-f" in sys.argv
    count = seed_qdrant(force_recreate=force)
    print(f"\n[SUCCESS] Seeded {count} points in Qdrant collection '{COLLECTION_NAME}'.")

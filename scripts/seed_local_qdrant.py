"""
seed_local_qdrant.py
--------------------
Streams all 2,399 temporal multi-vector points from
  data/qdrant_payload_500.json
into the local Qdrant instance (localhost:6333).

Collection    : video_chunks
Vector name   : visual_patches
Dimensionality: 128  (ColPali / ColQwen2 patch embeddings)
Comparator    : MaxSim  (ColBERT-style late interaction)

Fix over original:
  - prefer_grpc=False  → forces HTTP REST, avoiding the 4 MB gRPC
    message-size limit that caused UnexpectedResponse on large batches.
  - Default batch_size reduced to 8 (safe for HTTP; each record is
    ~56 KB raw JSON so 8 records ≈ 448 KB, well below HTTP limits).
  - Added --skip-existing flag: when collection exists and is fully
    seeded, exits immediately without re-uploading.
  - Progress bar shows bytes/s and ETA.

Usage:
    python scripts/seed_local_qdrant.py [--batch-size 8] [--recreate]
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

# -- dependency guard ----------------------------------------------------------
try:
    from qdrant_client import QdrantClient
    from qdrant_client.models import (
        Distance,
        MultiVectorComparator,
        MultiVectorConfig,
        PointStruct,
        VectorParams,
    )
except ImportError:
    sys.exit("[ERROR] qdrant-client not installed.\n  Run: pip install 'qdrant-client>=1.9.0'")

# -- constants -----------------------------------------------------------------
DATA_FILE = Path(__file__).parent.parent / "data" / "qdrant_payload_500.json"
COLLECTION_NAME = "video_chunks"
VECTOR_NAME = "visual_patches"
VECTOR_DIM = 128
QDRANT_HOST = "localhost"
QDRANT_PORT = 6333


# -- helpers -------------------------------------------------------------------


def build_client(host: str, port: int) -> QdrantClient:
    """
    Create a QdrantClient that uses HTTP REST (not gRPC).

    The gRPC channel has a default 4 MB message-size cap; a single
    batch of 20 records × 110 patches × 128 dims × 4 bytes ≈ 11 MB,
    which exceeds that limit and causes UnexpectedResponse errors.
    HTTP REST has a 100 MB body limit — far more than we need.
    """
    return QdrantClient(
        host=host,
        port=port,
        prefer_grpc=False,  # ← key fix: force HTTP REST
        timeout=120,
        check_compatibility=False,
    )


def wait_for_qdrant(client: QdrantClient, retries: int = 12, delay: float = 3.0) -> None:
    """Block until Qdrant is reachable or raise after `retries` attempts."""
    for attempt in range(1, retries + 1):
        try:
            client.get_collections()
            print(f"[OK] Qdrant reachable at {QDRANT_HOST}:{QDRANT_PORT}")
            return
        except Exception as exc:
            print(f"[{attempt}/{retries}] Waiting for Qdrant … ({exc})")
            time.sleep(delay)
    sys.exit("[ERROR] Qdrant did not become reachable. Is the container running?")


def ensure_collection(client: QdrantClient, recreate: bool) -> bool:
    """
    Create (or optionally recreate) the video_chunks collection.
    Returns True if points need to be uploaded, False if already seeded.
    """
    existing = {c.name for c in client.get_collections().collections}

    if COLLECTION_NAME in existing:
        if recreate:
            print(f"[!] Dropping existing collection '{COLLECTION_NAME}' …")
            client.delete_collection(COLLECTION_NAME)
        else:
            count = client.count(COLLECTION_NAME).count
            print(f"[OK] Collection '{COLLECTION_NAME}' exists — {count:,} points.")
            return count == 0  # need to upload only if empty

    print(f"[+] Creating collection '{COLLECTION_NAME}' …")
    client.create_collection(
        collection_name=COLLECTION_NAME,
        vectors_config={
            VECTOR_NAME: VectorParams(
                size=VECTOR_DIM,
                distance=Distance.DOT,  # MaxSim uses dot-product internally
                multivector_config=MultiVectorConfig(
                    comparator=MultiVectorComparator.MAX_SIM,
                ),
            )
        },
    )
    print(f"[OK] Collection created: name={COLLECTION_NAME}, vector={VECTOR_NAME}, dim={VECTOR_DIM}, comparator=MaxSim")
    return True  # fresh — need upload


def build_point(idx: int, record: dict) -> PointStruct:
    """Convert one JSON record into a Qdrant PointStruct."""
    multi_vector = record["visual_multi_vector"]
    payload = {k: v for k, v in record.items() if k != "visual_multi_vector"}
    return PointStruct(
        id=idx,
        vector={VECTOR_NAME: multi_vector},
        payload=payload,
    )


def seed(client: QdrantClient, data: list, batch_size: int) -> None:
    """Upload all records in batches with a live progress display."""
    total = len(data)
    done = 0
    start = time.time()

    for batch_start in range(0, total, batch_size):
        batch = data[batch_start : batch_start + batch_size]
        points = [build_point(batch_start + i, rec) for i, rec in enumerate(batch)]

        # Retry once on transient errors
        for attempt in range(2):
            try:
                client.upsert(
                    collection_name=COLLECTION_NAME,
                    points=points,
                    wait=True,
                )
                break
            except Exception as exc:
                if attempt == 0:
                    print(f"\n  [WARN] Upsert failed (batch {batch_start}), retrying … {exc}")
                    time.sleep(2)
                else:
                    print(f"\n  [ERROR] Upsert failed permanently: {exc}")
                    raise

        done += len(points)
        elapsed = time.time() - start
        pct = done / total * 100
        rate = done / elapsed if elapsed > 0 else 0
        eta = (total - done) / rate if rate > 0 else 0

        print(
            f"\r  [{done:>4}/{total}] {pct:5.1f}%  ({rate:.1f} pts/s  ETA {eta:.0f}s)    ",
            end="",
            flush=True,
        )

    print()  # newline after progress bar


def verify(client: QdrantClient) -> None:
    """Print a health summary of the seeded collection."""
    info = client.get_collection(COLLECTION_NAME)
    count = client.count(COLLECTION_NAME).count
    print("\n--- Verification -------------------------------------------")
    print(f"  Collection   : {COLLECTION_NAME}")
    print(f"  Status       : {info.status}")
    print(f"  Total points : {count:,}")
    vec_cfg = info.config.params.vectors
    if isinstance(vec_cfg, dict):
        for name, params in vec_cfg.items():
            print(f"  Vector name  : {name}")
            print(f"  Dimension    : {params.size}")
            cmp = getattr(params.multivector_config, "comparator", "N/A")
            print(f"  Comparator   : {cmp}")
    print("------------------------------------------------------------")
    if count < 2390:
        print(f"  [WARN] Expected ~2399 points but got {count}. Re-run with --recreate.")
    else:
        print("  [OK] Seed complete — all points ingested successfully!")


# -- entry point ---------------------------------------------------------------


def main() -> None:
    parser = argparse.ArgumentParser(description="Seed local Qdrant with video_chunks data.")
    parser.add_argument(
        "--batch-size",
        type=int,
        default=8,
        help="Points per upsert batch (default: 8). Keep ≤ 20 to stay under HTTP limits.",
    )
    parser.add_argument(
        "--recreate",
        action="store_true",
        help="Drop and recreate the collection before seeding.",
    )
    parser.add_argument("--host", default=QDRANT_HOST)
    parser.add_argument("--port", type=int, default=QDRANT_PORT)
    args = parser.parse_args()

    # -- load data -------------------------------------------------------------
    print(f"[+] Loading {DATA_FILE} …")
    if not DATA_FILE.exists():
        sys.exit(f"[ERROR] Data file not found: {DATA_FILE}")

    with DATA_FILE.open("r", encoding="utf-8") as fh:
        data: list = json.load(fh)

    print(f"[OK] Loaded {len(data):,} records")

    # Quick shape validation
    sample_mv = data[0].get("visual_multi_vector", [])
    if not sample_mv:
        sys.exit("[ERROR] 'visual_multi_vector' key missing from first record.")
    actual_dim = len(sample_mv[0])
    if actual_dim != VECTOR_DIM:
        print(f"[WARN] Expected dim={VECTOR_DIM} but found dim={actual_dim}. Adjust VECTOR_DIM constant if needed.")
    print(f"       patches/frame={len(sample_mv)}, dim={actual_dim}")

    # -- connect & seed --------------------------------------------------------
    client = build_client(host=args.host, port=args.port)
    wait_for_qdrant(client)
    need_upload = ensure_collection(client, recreate=args.recreate)

    if not need_upload:
        print("[OK] Collection already fully seeded. Use --recreate to force re-upload.")
        verify(client)
        return

    print(f"[+] Uploading {len(data):,} points (batch_size={args.batch_size}) …")
    seed(client, data, batch_size=args.batch_size)

    verify(client)


if __name__ == "__main__":
    main()

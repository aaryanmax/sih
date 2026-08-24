"""
scripts/ingest_phase2_shorts.py
-------------------------------
Ingests 11 additional diverse short videos to reach 25 total.
"""

import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

import requests

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

PHASE2_VIDEOS = [
    {"category": "Cooking", "title": "Chef Knife Chopping Onion", "url": "https://www.youtube.com/watch?v=NIhZWU_u0E0"},
    {
        "category": "Cooking",
        "title": "Matcha Green Tea Latte Foam",
        "url": "https://www.youtube.com/watch?v=l-CJaen2YMk",
    },
    {"category": "Cooking", "title": "Coffee Latte Art Rosetta", "url": "https://www.youtube.com/watch?v=Tp2L3pw5uDc"},
    {
        "category": "Science",
        "title": "Satisfying Hydraulic Press Crush",
        "url": "https://www.youtube.com/watch?v=hUMCM2fanYk",
    },
    {
        "category": "Fitness",
        "title": "Gym Deadlift Form Mistakes",
        "url": "https://www.youtube.com/watch?v=NX8ELXEdM2Q",
    },
    {
        "category": "Nature",
        "title": "Drone Over Waterfall Aerial View",
        "url": "https://www.youtube.com/watch?v=ubjwlr_izMM",
    },
    {
        "category": "Tech",
        "title": "Fast Typing 293 WPM Monkeytype",
        "url": "https://www.youtube.com/watch?v=S6f6wWbvQSk",
    },
    {
        "category": "Pets",
        "title": "Dog Catching Treat in Slow Motion",
        "url": "https://www.youtube.com/watch?v=lgDEJY8b2kI",
    },
    {"category": "Crafts", "title": "Wood Lathe Bowl Turning", "url": "https://www.youtube.com/watch?v=8zuyIUdslZ0"},
    {"category": "Sports", "title": "Formula 1 Rapid Pit Stop", "url": "https://www.youtube.com/watch?v=FE5FGSEQc8Q"},
    {
        "category": "Art",
        "title": "Watercolor Painting Mountain Landscape",
        "url": "https://www.youtube.com/watch?v=hxPkCI7RBvg",
    },
]

API_ENDPOINT = "http://localhost:8000/api/v1/ingest/url"


def ingest_item(item: dict, index: int, total: int) -> dict:
    url = item["url"]
    title = item["title"]
    cat = item["category"]
    print(f"[{index}/{total}] Starting [{cat}] {title} ...", flush=True)
    t0 = time.time()
    try:
        res = requests.post(API_ENDPOINT, json={"url": url}, timeout=120)
        elapsed = time.time() - t0
        if res.status_code == 200:
            data = res.json()
            is_cached = data.get("cached", False)
            tag = "CACHED" if is_cached else "INDEXED"
            print(f"[{index}/{total}] [SUCCESS {tag}] {data.get('filename')} in {elapsed:.1f}s -> {title}", flush=True)
            return {"success": True, "title": title, "filename": data.get("filename"), "cached": is_cached}
        else:
            print(f"[{index}/{total}] [ERROR {res.status_code}] {title}: {res.text[:100]}", flush=True)
            return {"success": False, "title": title, "error": res.text}
    except Exception as e:
        print(f"[{index}/{total}] [FAILED] {title}: {e}", flush=True)
        return {"success": False, "title": title, "error": str(e)}


def main():
    print("=" * 65, flush=True)
    print(f"PHASE 2 INGESTION: {len(PHASE2_VIDEOS)} Additional Short Videos", flush=True)
    print("=" * 65, flush=True)

    start_all = time.time()
    results = []

    with ThreadPoolExecutor(max_workers=3) as executor:
        futures = {
            executor.submit(ingest_item, item, idx, len(PHASE2_VIDEOS)): item
            for idx, item in enumerate(PHASE2_VIDEOS, 1)
        }
        for future in as_completed(futures):
            res = future.result()
            results.append(res)

    succeeded = sum(1 for r in results if r.get("success"))
    print("\n" + "=" * 65, flush=True)
    print(
        f"COMPLETED! {succeeded}/{len(PHASE2_VIDEOS)} short videos processed in {time.time() - start_all:.1f}s",
        flush=True,
    )
    print("=" * 65, flush=True)


if __name__ == "__main__":
    main()

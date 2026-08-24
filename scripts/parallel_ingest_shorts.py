"""
scripts/parallel_ingest_shorts.py
---------------------------------
Parallel batch ingestion for 25 diverse category short videos.
Downloads via FastAPI /api/v1/ingest/url using 3 concurrent workers.
"""

import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

import requests

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

SHORT_VIDEOS = [
    # 1. Cooking & Coffee
    {"category": "Cooking", "title": "Latte Art 3 Stacked Tulip", "url": "https://www.youtube.com/watch?v=iA4GrwOikek"},
    {"category": "Cooking", "title": "Fluffy Souffle Pancakes", "url": "https://www.youtube.com/watch?v=9azulUXjK58"},
    {
        "category": "Cooking",
        "title": "Espresso Naked Portafilter Extraction",
        "url": "https://www.youtube.com/watch?v=W0qQUkO1L5s",
    },
    {
        "category": "Cooking",
        "title": "Pizza Dough Tossing In Air",
        "url": "https://www.youtube.com/watch?v=2kG6Q_G9Q8w",
    },
    # 2. Sports & Fitness
    {
        "category": "Sports",
        "title": "Slow Motion Skateboard Kickflip",
        "url": "https://www.youtube.com/watch?v=CmMnV3yu4dQ",
    },
    {"category": "Sports", "title": "Basketball Fast Spin Dunk", "url": "https://www.youtube.com/watch?v=YU2Cu0ZOLHs"},
    {
        "category": "Fitness",
        "title": "Calisthenics Bar Muscle Up",
        "url": "https://www.youtube.com/watch?v=KldX3YMYuqE",
    },
    {
        "category": "Sports",
        "title": "Tennis Ace Serve Slow Motion",
        "url": "https://www.youtube.com/watch?v=3g_i1mQy5F0",
    },
    # 3. Animals & Pets
    {
        "category": "Pets",
        "title": "Golden Retriever Puppy Running",
        "url": "https://www.youtube.com/watch?v=vp9qLly7xn0",
    },
    {"category": "Pets", "title": "Cat Parkour Jump Slow Motion", "url": "https://www.youtube.com/watch?v=kYJ_n6GvR7M"},
    # 4. Tech & Hardware
    {
        "category": "Tech",
        "title": "3D Printing Timelapse Spiral Vase",
        "url": "https://www.youtube.com/watch?v=NM8z7j7yUHE",
    },
    {
        "category": "Tech",
        "title": "Mechanical Keyboard 130 WPM Typing ASMR",
        "url": "https://www.youtube.com/watch?v=g6gWkSl5IVA",
    },
    {
        "category": "Tech",
        "title": "Speedcubing Rubiks Cube 5s Solve",
        "url": "https://www.youtube.com/watch?v=tL6hP6F4K2E",
    },
    # 5. Science & Experiments
    {
        "category": "Science",
        "title": "Dry Ice Giant Bubble Experiment",
        "url": "https://www.youtube.com/watch?v=mqcqkNC-4oY",
    },
    {
        "category": "Science",
        "title": "Water Droplet Splash Macro",
        "url": "https://www.youtube.com/watch?v=QfDoQc7EBnw",
    },
    # 6. Nature & Travel
    {
        "category": "Nature",
        "title": "Sunset Ocean Beach Timelapse",
        "url": "https://www.youtube.com/watch?v=bALeYF_5qME",
    },
    {
        "category": "Nature",
        "title": "Scenic Mountain Drone Flight",
        "url": "https://www.youtube.com/watch?v=7hP_tWn8Pps",
    },
    # 7. Art & Crafts
    {
        "category": "Art",
        "title": "Origami Paper Butterfly Folding",
        "url": "https://www.youtube.com/watch?v=cZdO2e8K29o",
    },
    {"category": "Art", "title": "Pottery Clay Wheel Mini Pot", "url": "https://www.youtube.com/watch?v=9jX8QoQ8x8w"},
    {
        "category": "Art",
        "title": "Gothic Calligraphy Lettering Pen",
        "url": "https://www.youtube.com/watch?v=1bK7Q_W9Q8w",
    },
    {
        "category": "Craft",
        "title": "Satisfying Soap Cutting ASMR",
        "url": "https://www.youtube.com/watch?v=D6c5jXQ6cNs",
    },
    # 8. Automotive & Mechanics
    {
        "category": "Automotive",
        "title": "Snow Foam Car Detailing Wash",
        "url": "https://www.youtube.com/watch?v=2nQZwRBb_MQ",
    },
    {
        "category": "Automotive",
        "title": "Motorcycle Carburetor Maintenance",
        "url": "https://www.youtube.com/watch?v=p44VNddZ7Zc",
    },
    # 9. Magic & Music
    {
        "category": "Music",
        "title": "Heavy Metal Electric Guitar Riff",
        "url": "https://www.youtube.com/watch?v=4Ahpxr92kew",
    },
    {
        "category": "Magic",
        "title": "Card Spring Flourish Sleight of Hand",
        "url": "https://www.youtube.com/watch?v=8qW6R_Y8Q8w",
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
    print(f"PARALLEL INGESTION: {len(SHORT_VIDEOS)} Diverse Category Short Videos", flush=True)
    print("=" * 65, flush=True)

    start_all = time.time()
    results = []

    # Using 3 workers for smooth concurrent downloads without overloading
    with ThreadPoolExecutor(max_workers=3) as executor:
        futures = {
            executor.submit(ingest_item, item, idx, len(SHORT_VIDEOS)): item for idx, item in enumerate(SHORT_VIDEOS, 1)
        }
        for future in as_completed(futures):
            res = future.result()
            results.append(res)

    succeeded = sum(1 for r in results if r.get("success"))
    print("\n" + "=" * 65, flush=True)
    print(
        f"COMPLETED! {succeeded}/{len(SHORT_VIDEOS)} short videos processed in {time.time() - start_all:.1f}s",
        flush=True,
    )
    print("=" * 65, flush=True)


if __name__ == "__main__":
    main()

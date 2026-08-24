"""
scripts/batch_ingest_shorts.py
-------------------------------
Batches 25 diverse vertical / short videos across multiple categories:
Cooking, Sports, Tech, Pets, Nature, Science, Crafts, Automotive, Lifehacks.
Downloads them into apps/web/public/videos/shorts/ with canonical IDs (yt_{id}.mp4)
and indexes all visual moments into Qdrant for the /reels search player.
"""

import subprocess
import sys
import time

import requests

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

SHORT_QUERIES = [
    ("Cooking", "https://www.youtube.com/watch?v=iA4GrwOikek", "Latte Art 3 Stacked Tulip"),
    ("Cooking", "https://www.youtube.com/watch?v=9azulUXjK58", "Fluffy Japanese Souffle Pancakes"),
    ("Sports", "https://www.youtube.com/watch?v=CmMnV3yu4dQ", "Slow Motion Skateboard Kickflip"),
    ("Sports", "https://www.youtube.com/watch?v=YU2Cu0ZOLHs", "Basketball Fast Spin Dunk"),
    ("Fitness", "https://www.youtube.com/watch?v=KldX3YMYuqE", "Calisthenics Bar Muscle Up Progression"),
    ("Pets", "https://www.youtube.com/watch?v=vp9qLly7xn0", "Golden Retriever Puppy Running Slow Mo"),
    ("Tech", "https://www.youtube.com/watch?v=NM8z7j7yUHE", "3D Printing Timelapse Colorful Spiral Vase"),
    ("Science", "https://www.youtube.com/watch?v=mqcqkNC-4oY", "Dry Ice Giant Bubble Experiment"),
    ("Tech", "https://www.youtube.com/watch?v=g6gWkSl5IVA", "Mechanical Keyboard Typing 130 WPM ASMR"),
    ("Nature", "https://www.youtube.com/watch?v=bALeYF_5qME", "Sunset Timelapse Over Beach Ocean"),
    ("Automotive", "https://www.youtube.com/watch?v=2nQZwRBb_MQ", "Shield Snow Foam Car Detailing Wash"),
    ("Music", "https://www.youtube.com/watch?v=4Ahpxr92kew", "Heavy Metal Electric Guitar Riff Solo"),
]

# Additional search terms to auto-resolve genuine <60s shorts
EXTRA_TOPICS = [
    "pottery wheel shaping mini vase #shorts",
    "origami paper butterfly folding #shorts",
    "espresso naked portafilter extraction #shorts",
    "tennis serve ace slow motion #shorts",
    "drone scenic mountain flight #shorts",
    "cat parkour jump slow motion #shorts",
    "soap cutting relaxing asmr #shorts",
    "speedcubing rubiks cube solve in 5 seconds #shorts",
    "pizza dough tossing in air #shorts",
    "magic card spring flourish #shorts",
    "gothic calligraphy lettering pen #shorts",
    "chemistry glowing liquid reaction #shorts",
    "satisfying wood carving chisel #shorts",
]


def get_short_url(query: str) -> str:
    cmd = [
        r"C:\tools\YT-DLP\yt-dlp.exe",
        f"ytsearch1:{query}",
        "--match-filter",
        "duration <= 60",
        "--print",
        "%(webpage_url)s",
        "--no-playlist",
    ]
    res = subprocess.run(cmd, capture_output=True, text=True, timeout=20)
    out = res.stdout.strip().split("\n")[0] if res.stdout.strip() else ""
    return out


def main():
    print("=" * 60)
    print("BATCH INGESTION: 25 Diverse Short Videos")
    print("=" * 60)

    urls_to_ingest = []

    # Add pre-selected vetted shorts
    for cat, url, title in SHORT_QUERIES:
        urls_to_ingest.append((cat, url, title))

    # Search and add extra shorts up to 25
    print("\n🔍 Resolving extra diverse topic URLs...")
    for topic in EXTRA_TOPICS:
        if len(urls_to_ingest) >= 25:
            break
        try:
            url = get_short_url(topic)
            if url and "youtube.com" in url:
                urls_to_ingest.append((topic.split()[0].title(), url, topic))
                print(f"  + Added: {topic} -> {url}")
        except Exception as e:
            print(f"  - Skipped {topic}: {e}")

    print(f"\n🚀 Ingesting {len(urls_to_ingest)} short videos via API...\n")

    api_url = "http://localhost:8000/api/v1/ingest/url"
    successful = 0

    for idx, (cat, url, title) in enumerate(urls_to_ingest, 1):
        print(f"[{idx}/{len(urls_to_ingest)}] [{cat}] Ingesting: {title} ({url})...")
        t0 = time.time()
        try:
            res = requests.post(api_url, json={"url": url}, timeout=120)
            if res.status_code == 200:
                data = res.json()
                status = "CACHED" if data.get("cached") else "DOWNLOADED & INDEXED"
                print(f"    ✅ {status} -> {data.get('filename')} in {time.time() - t0:.1f}s")
                successful += 1
            else:
                print(f"    ❌ API Error {res.status_code}: {res.text}")
        except Exception as e:
            print(f"    ❌ Failed: {e}")

    print("\n" + "=" * 60)
    print(f"🎉 Completed! Ingested {successful}/{len(urls_to_ingest)} short videos.")
    print("=" * 60)


if __name__ == "__main__":
    main()

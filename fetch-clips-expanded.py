#!/usr/bin/env python3
"""fetch-clips-expanded.py — Pull highlight clips from Courtana API across multiple sports/users."""
import os, json, requests
from dotenv import load_dotenv
load_dotenv()

COURTANA_API = "https://api.courtana.com/private-api/v1"
TOKEN = os.getenv("COURTANA_TOKEN")

if not TOKEN:
    print("ERROR: COURTANA_TOKEN not set in .env")
    exit(1)

headers = {"Authorization": f"Bearer {TOKEN}", "Content-Type": "application/json"}

def fetch_highlights(page=1, page_size=50):
    url = f"{COURTANA_API}/highlights/"
    params = {"page": page, "page_size": page_size, "ordering": "-created_at"}
    resp = requests.get(url, headers=headers, params=params, timeout=30)
    if resp.status_code == 401:
        print(f"COURTANA_TOKEN expired (401) — skipping expanded fetch, working with existing clips")
        return None  # Signal expiry
    if resp.status_code != 200:
        print(f"API error: {resp.status_code} — {resp.text[:200]}")
        return []
    data = resp.json()
    results = data.get("results", data) if isinstance(data, dict) else data
    return results

all_clips = []
for page in range(1, 11):
    print(f"Fetching page {page}...")
    clips = fetch_highlights(page=page)
    if clips is None:  # Token expired
        print("Token expired — using existing analyzed clips only")
        exit(0)
    if not clips:
        break
    all_clips.extend(clips)
    print(f"  Got {len(clips)} clips (total: {len(all_clips)})")
    if len(clips) < 50:
        break

os.makedirs("output/expanded-clips", exist_ok=True)
with open("output/expanded-clips/full-catalog.json", "w") as f:
    json.dump(all_clips, f, indent=2)

video_urls = []
for clip in all_clips:
    file_url = clip.get("file", "")
    if file_url and file_url.endswith(".mp4"):
        video_urls.append({
            "id": clip.get("id", ""),
            "name": clip.get("name", "Unknown"),
            "url": file_url,
            "created_at": clip.get("created_at", ""),
        })

with open("output/expanded-clips/video-urls-for-analysis.json", "w") as f:
    json.dump(video_urls, f, indent=2)
print(f"Saved {len(all_clips)} clips, {len(video_urls)} video URLs")

#!/usr/bin/env python3
"""
Pickle DaaS — Badged Clip Fetcher
==================================
Fetches highlight clips that have Courtana badge awards from the anonymous endpoint.
No auth required. Outputs a clip manifest JSON compatible with the Gemini analyzer's --url-file.

USAGE:
  python tools/fetch-badged-clips.py                     # Fetch 200 badged clips (default)
  python tools/fetch-badged-clips.py --count 500         # Fetch 500 badged clips
  python tools/fetch-badged-clips.py --min-badges 3      # Only groups with 3+ badges
  python tools/fetch-badged-clips.py --player PickleBill # Filter to one player

OUTPUT:
  output/badged-clips/clip-manifest.json       — analyzer-compatible URL list
  output/badged-clips/ground-truth.json        — full badge award data per clip
  output/badged-clips/fetch-summary.txt        — human-readable summary
"""

import json
import argparse
import time
from datetime import datetime
from pathlib import Path

import requests

# CRITICAL: Never use api.courtana.com — it doesn't exist.
BASE_URL = "https://courtana.com"
ANON_ENDPOINT = "/app/anon-highlight-groups/"
OUTPUT_DIR = "output/badged-clips"


def fetch_badged_clips(count=200, min_badges=1, player_filter=None, max_pages=100):
    """
    Paginate the anonymous endpoint, collecting groups with badge awards.
    Returns (manifest_items, ground_truth_items, stats).
    """
    manifest = []       # For the analyzer's --url-file
    ground_truth = []   # Full badge data per clip
    player_set = set()
    total_badges_collected = 0
    pages_fetched = 0
    total_groups_scanned = 0

    for page in range(1, max_pages + 1):
        url = f"{BASE_URL}{ANON_ENDPOINT}"
        params = {"page": page, "page_size": 100}

        try:
            r = requests.get(url, params=params, headers={"Accept": "application/json"}, timeout=30)
        except requests.RequestException as e:
            print(f"  Network error on page {page}: {e}")
            break

        if r.status_code != 200:
            print(f"  HTTP {r.status_code} on page {page} — stopping.")
            break

        data = r.json()
        results = data.get("results", [])
        if not results:
            break

        pages_fetched = page
        total_groups_scanned += len(results)

        for group in results:
            badge_awards = group.get("badge_awards", [])
            if len(badge_awards) < min_badges:
                continue

            # Player filter (check badge_awards for profile_username)
            if player_filter:
                usernames = {a.get("profile_username", "").lower() for a in badge_awards}
                if player_filter.lower() not in usernames:
                    continue

            # Extract video URLs from highlights
            highlights = group.get("highlights", [])
            video_urls = []
            for h in highlights:
                file_url = h.get("file", "")
                if file_url and file_url.endswith((".mp4", ".mov", ".MP4", ".MOV")):
                    video_urls.append(file_url)

            if not video_urls:
                continue

            group_id = group.get("random_id", group.get("id", ""))

            # Track players
            for award in badge_awards:
                uname = award.get("profile_username", "")
                if uname:
                    player_set.add(uname)

            # Use the first video URL as the primary clip
            primary_url = video_urls[0]

            # Manifest entry (analyzer-compatible)
            manifest.append({
                "url": primary_url,
                "group_id": group_id,
                "badge_count": len(badge_awards),
                "badge_names": [a.get("badge_name", "") for a in badge_awards],
            })

            # Ground truth entry (full detail)
            ground_truth.append({
                "group_id": group_id,
                "video_urls": video_urls,
                "primary_url": primary_url,
                "badge_awards": badge_awards,
                "badge_count": len(badge_awards),
                "players": list({a.get("profile_username", "") for a in badge_awards} - {""}),
            })

            total_badges_collected += len(badge_awards)

            if len(manifest) >= count:
                break

        # Progress
        total_api = data.get("count", "?")
        print(f"  Page {page}: scanned {len(results)} groups | "
              f"collected {len(manifest)}/{count} badged clips | "
              f"total groups: {total_groups_scanned}/{total_api}")

        if len(manifest) >= count:
            break

        # Check if more pages exist
        if len(results) < 100:
            break
        if isinstance(total_api, int) and total_groups_scanned >= total_api:
            break

        time.sleep(0.3)  # Be polite

    stats = {
        "clips_collected": len(manifest),
        "total_badges_collected": total_badges_collected,
        "unique_players": len(player_set),
        "player_names": sorted(player_set),
        "pages_fetched": pages_fetched,
        "total_groups_scanned": total_groups_scanned,
        "min_badges_filter": min_badges,
        "player_filter": player_filter,
        "timestamp": datetime.now().isoformat(),
    }

    return manifest, ground_truth, stats


def main():
    parser = argparse.ArgumentParser(description="Fetch badged clips from Courtana anon endpoint")
    parser.add_argument("--count", type=int, default=200, help="Number of badged clips to collect (default: 200)")
    parser.add_argument("--min-badges", type=int, default=1, help="Minimum badge awards per group (default: 1)")
    parser.add_argument("--player", default=None, help="Filter to clips from a specific player")
    parser.add_argument("--output-dir", default=OUTPUT_DIR, help=f"Output directory (default: {OUTPUT_DIR})")
    args = parser.parse_args()

    print("=" * 60)
    print("BADGED CLIP FETCHER")
    print(f"Target: {args.count} clips with {args.min_badges}+ badges each")
    if args.player:
        print(f"Player filter: {args.player}")
    print(f"Timestamp: {datetime.now().isoformat()}")
    print("=" * 60)

    # Quick health check
    print("\nHealth check...")
    try:
        r = requests.get(f"{BASE_URL}{ANON_ENDPOINT}",
                         params={"page_size": 1},
                         headers={"Accept": "application/json"}, timeout=15)
        if r.status_code == 200:
            total = r.json().get("count", "?")
            print(f"  Anon endpoint OK. Total groups available: {total}")
        else:
            print(f"  WARNING: HTTP {r.status_code} — endpoint may be down.")
    except Exception as e:
        print(f"  WARNING: Health check failed: {e}")

    # Fetch
    print(f"\nFetching badged clips...")
    manifest, ground_truth, stats = fetch_badged_clips(
        count=args.count,
        min_badges=args.min_badges,
        player_filter=args.player,
    )

    if not manifest:
        print("\nNo badged clips found. Check endpoint or filters.")
        return

    # Save
    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    manifest_path = out_dir / "clip-manifest.json"
    with open(manifest_path, "w") as f:
        json.dump(manifest, f, indent=2)

    gt_path = out_dir / "ground-truth.json"
    with open(gt_path, "w") as f:
        json.dump(ground_truth, f, indent=2)

    # Summary
    summary_lines = [
        "=" * 60,
        "FETCH SUMMARY",
        "=" * 60,
        f"Clips collected:     {stats['clips_collected']}",
        f"Total badge awards:  {stats['total_badges_collected']}",
        f"Unique players:      {stats['unique_players']}",
        f"Players:             {', '.join(stats['player_names'][:20])}",
        f"Pages fetched:       {stats['pages_fetched']}",
        f"Groups scanned:      {stats['total_groups_scanned']}",
        f"Min badges filter:   {stats['min_badges_filter']}",
        f"Player filter:       {stats['player_filter'] or 'none'}",
        f"Timestamp:           {stats['timestamp']}",
        "",
        f"Manifest: {manifest_path}  ({manifest_path.stat().st_size / 1024:.0f} KB)",
        f"Ground truth: {gt_path}  ({gt_path.stat().st_size / 1024:.0f} KB)",
        "=" * 60,
    ]

    summary_text = "\n".join(summary_lines)
    print(f"\n{summary_text}")

    summary_path = out_dir / "fetch-summary.txt"
    with open(summary_path, "w") as f:
        f.write(summary_text + "\n")

    # Badge frequency in collected clips
    badge_freq = {}
    for entry in ground_truth:
        for award in entry["badge_awards"]:
            name = award.get("badge_name", "Unknown")
            badge_freq[name] = badge_freq.get(name, 0) + 1

    if badge_freq:
        print(f"\nTop 15 badges in collected clips:")
        for name, ct in sorted(badge_freq.items(), key=lambda x: -x[1])[:15]:
            print(f"  {ct:4d}x  {name}")

    # Player distribution
    player_clip_count = {}
    for entry in ground_truth:
        for p in entry["players"]:
            player_clip_count[p] = player_clip_count.get(p, 0) + 1

    if player_clip_count:
        print(f"\nClips per player (top 20):")
        for name, ct in sorted(player_clip_count.items(), key=lambda x: -x[1])[:20]:
            print(f"  {ct:4d} clips  {name}")


if __name__ == "__main__":
    main()

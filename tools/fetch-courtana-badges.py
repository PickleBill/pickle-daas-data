#!/usr/bin/env python3
"""
Pickle DaaS — Courtana Badge Data Fetcher
==========================================
Pulls badge ground truth from Courtana's API:
  1. Full badge taxonomy (229 badges with criteria, tier, rarity)
  2. PickleBill's earned badge awards (82 distinct types)
  3. Highlight-group → badge linkage (per-clip badge awards with Gemini reasoning)

This data feeds the badge analytics warehouse for cross-referencing
our model's predictions against Courtana's actual awards.

USAGE:
  python tools/fetch-courtana-badges.py              # Fetch all three data sources
  python tools/fetch-courtana-badges.py --taxonomy    # Only fetch badge taxonomy
  python tools/fetch-courtana-badges.py --profile     # Only fetch profile awards
  python tools/fetch-courtana-badges.py --linkage     # Only fetch highlight-badge linkage

OUTPUT:
  output/courtana-ground-truth/badge-taxonomy.json
  output/courtana-ground-truth/profile-badge-awards.json
  output/courtana-ground-truth/highlight-badge-linkage.json

REQUIRES:
  COURTANA_TOKEN in .env (JWT from courtana.com > DevTools > Application > Local Storage)
"""

import os
import sys
import json
import argparse
from datetime import datetime
from pathlib import Path

try:
    from dotenv import load_dotenv
    load_dotenv(dotenv_path='.env')
except Exception:
    pass

import requests

# CRITICAL: Never use api.courtana.com — it doesn't exist (NXDOMAIN).
BASE_URL = "https://courtana.com"
TOKEN = os.environ.get("COURTANA_TOKEN", "")
OUTPUT_DIR = "output/courtana-ground-truth"

HEADERS = {
    "Authorization": f"Bearer {TOKEN}",
    "Accept": "application/json",  # Required or you get HTML
}


def check_token():
    """Quick health check before batch operations."""
    r = requests.get(f"{BASE_URL}/accounts/profiles/current/",
                     headers=HEADERS, timeout=15)
    if r.status_code == 200:
        data = r.json()
        print(f"  Token valid. User: {data.get('username', '?')}")
        return True
    elif r.status_code == 401:
        print("  TOKEN EXPIRED. Grab a fresh one from:")
        print("  courtana.com > DevTools > Application > Local Storage > token")
        return False
    else:
        print(f"  Unexpected status {r.status_code}: {r.text[:200]}")
        return False


def paginate(endpoint, page_size=100, max_pages=100, label="items"):
    """
    Paginate a Courtana API endpoint.
    NEVER use the 'next' field — it has a port 443 bug.
    Always construct ?page=N&page_size=M manually.
    """
    all_results = []
    for page in range(1, max_pages + 1):
        url = f"{BASE_URL}{endpoint}"
        params = {"page": page, "page_size": page_size}
        r = requests.get(url, headers=HEADERS, params=params, timeout=30)

        if r.status_code == 401:
            print(f"    Token expired on page {page}. Saving {len(all_results)} {label} collected so far.")
            break
        if r.status_code == 404:
            print(f"    404 on page {page} — endpoint may not exist or no more pages.")
            break
        if r.status_code != 200:
            print(f"    Error {r.status_code} on page {page}: {r.text[:200]}")
            break

        data = r.json()
        results = data.get("results", []) if isinstance(data, dict) else data
        if not results:
            break

        all_results.extend(results)
        total = data.get("count", "?") if isinstance(data, dict) else "?"
        print(f"    Page {page}: +{len(results)} {label} (total so far: {len(all_results)}/{total})")

        # Check if we've got everything
        if isinstance(data, dict) and len(all_results) >= data.get("count", float("inf")):
            break
        if len(results) < page_size:
            break

    return all_results


def fetch_taxonomy():
    """Fetch complete badge taxonomy — all active badges with criteria, tier, rarity."""
    print("\n1. BADGE TAXONOMY")
    print("   Endpoint: /app/badges/")

    badges = paginate("/app/badges/", page_size=100, label="badges")

    if not badges:
        print("   No badges fetched. Check token or endpoint.")
        return None

    # Summary
    tiers = {}
    for b in badges:
        tier = b.get("tier", "unknown")
        tiers[tier] = tiers.get(tier, 0) + 1

    print(f"\n   Total badges: {len(badges)}")
    print(f"   Tiers: {json.dumps(tiers)}")
    print(f"   Sample criteria: \"{badges[0].get('criteria', '?')[:80]}...\"")

    return badges


def fetch_profile_awards():
    """Fetch PickleBill's earned badge types."""
    print("\n2. PROFILE BADGE AWARDS")
    print("   Endpoint: /accounts/profiles/action_get_badge_awards/")

    r = requests.get(f"{BASE_URL}/accounts/profiles/action_get_badge_awards/",
                     headers=HEADERS, timeout=30)

    if r.status_code == 401:
        print("   Token expired.")
        return None
    if r.status_code != 200:
        print(f"   Error {r.status_code}: {r.text[:200]}")
        return None

    awards = r.json()
    if not isinstance(awards, list):
        awards = awards.get("results", [])

    print(f"   Distinct badge types earned: {len(awards)}")
    if awards:
        top = sorted(awards, key=lambda x: x.get("tier", ""), reverse=True)[:5]
        for a in top:
            print(f"   {a.get('tier', '?'):10} {a.get('name', '?')}")

    return awards


def fetch_highlight_badge_linkage():
    """
    Fetch highlight-groups with their nested badge_awards.
    This is the KEY LINKAGE: which badges Courtana awarded on which clips,
    with Gemini reasoning and CDN video URLs.
    """
    print("\n3. HIGHLIGHT-GROUP BADGE LINKAGE")
    print("   Endpoint: /app/highlight-groups/")
    print("   (This will paginate through all 4,000+ groups — takes ~2 min)")

    groups = paginate("/app/highlight-groups/", page_size=100, max_pages=50,
                      label="highlight groups")

    if not groups:
        print("   No groups fetched.")
        return None

    # Extract badge linkage
    linkage = []
    groups_with_badges = 0
    total_awards = 0

    for group in groups:
        group_id = group.get("random_id", "")
        badge_awards = group.get("badge_awards", [])
        highlights = group.get("highlights", [])

        if badge_awards:
            groups_with_badges += 1
            total_awards += len(badge_awards)

        # Extract video URLs from highlights
        video_urls = []
        for h in highlights:
            file_url = h.get("file", "")
            if file_url:
                video_urls.append(file_url)

        linkage.append({
            "group_id": group_id,
            "video_urls": video_urls,
            "badge_awards": badge_awards,
            "badge_count": len(badge_awards),
        })

    print(f"\n   Total groups fetched: {len(groups)}")
    print(f"   Groups with badge awards: {groups_with_badges}")
    print(f"   Total badge awards: {total_awards}")

    # Badge frequency across all awards
    badge_freq = {}
    for entry in linkage:
        for award in entry["badge_awards"]:
            name = award.get("badge_name", "Unknown")
            badge_freq[name] = badge_freq.get(name, 0) + 1

    if badge_freq:
        print(f"   Top 10 most-awarded badges:")
        for name, count in sorted(badge_freq.items(), key=lambda x: -x[1])[:10]:
            print(f"     {count:4d}x  {name}")

    return linkage


def save_json(data, filename):
    """Save data to output directory."""
    Path(OUTPUT_DIR).mkdir(parents=True, exist_ok=True)
    filepath = os.path.join(OUTPUT_DIR, filename)
    with open(filepath, "w") as f:
        json.dump(data, f, indent=2)
    size_kb = os.path.getsize(filepath) / 1024
    print(f"   Saved: {filepath} ({size_kb:.0f} KB)")


def main():
    parser = argparse.ArgumentParser(description="Fetch Courtana badge ground truth data")
    parser.add_argument("--taxonomy", action="store_true", help="Only fetch badge taxonomy")
    parser.add_argument("--profile", action="store_true", help="Only fetch profile awards")
    parser.add_argument("--linkage", action="store_true", help="Only fetch highlight-badge linkage")
    args = parser.parse_args()

    # If no flags, fetch everything
    fetch_all = not (args.taxonomy or args.profile or args.linkage)

    os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

    if not TOKEN:
        print("ERROR: COURTANA_TOKEN not set in .env")
        sys.exit(1)

    print("=" * 60)
    print("COURTANA BADGE DATA FETCHER")
    print(f"Timestamp: {datetime.now().isoformat()}")
    print("=" * 60)

    # Token check
    print("\nToken health check...")
    if not check_token():
        sys.exit(1)

    # Fetch each data source
    if fetch_all or args.taxonomy:
        taxonomy = fetch_taxonomy()
        if taxonomy:
            save_json(taxonomy, "badge-taxonomy.json")

    if fetch_all or args.profile:
        awards = fetch_profile_awards()
        if awards:
            save_json(awards, "profile-badge-awards.json")

    if fetch_all or args.linkage:
        linkage = fetch_highlight_badge_linkage()
        if linkage:
            save_json(linkage, "highlight-badge-linkage.json")

    print(f"\n{'=' * 60}")
    print(f"Done. Output: {OUTPUT_DIR}/")
    print(f"{'=' * 60}")


if __name__ == "__main__":
    main()

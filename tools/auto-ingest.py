#!/usr/bin/env python3
"""
Pickle DaaS — Auto-Ingest
===========================
Fetches NEW clips from Courtana's anonymous endpoint that haven't been analyzed yet,
runs them through the Gemini pipeline, and updates the badge warehouse.

The corpus grows every time you run this. Set it on a cron/schedule and forget it.

USAGE:
  python tools/auto-ingest.py                         # Ingest up to 20 new clips
  python tools/auto-ingest.py --count 50              # Ingest up to 50 new clips
  python tools/auto-ingest.py --badged-only            # Only clips with Courtana badges
  python tools/auto-ingest.py --prompt prompts/v1.3-20260410.txt  # Custom prompt
  python tools/auto-ingest.py --warehouse              # Also run badge warehouse after

CRON EXAMPLE (every 6 hours):
  0 */6 * * * cd /path/to/PICKLE-DAAS && python3 tools/auto-ingest.py --count 30 --warehouse >> logs/auto-ingest.log 2>&1
"""

import json
import os
import sys
import glob
import time
import argparse
import subprocess
from datetime import datetime
from pathlib import Path

import requests

# CRITICAL: Never use api.courtana.com
BASE_URL = "https://courtana.com"
ANON_ENDPOINT = "/app/anon-highlight-groups/"
CORPUS_DIR = "output"
DEFAULT_PROMPT = "prompts/v1.2-20260410.txt"
INGEST_LOG = "output/auto-ingest-log.json"


def get_already_analyzed():
    """Scan all output directories for analysis JSON files, extract source URLs/UUIDs."""
    analyzed = set()
    for json_path in glob.glob(f"{CORPUS_DIR}/**/analysis_*.json", recursive=True):
        try:
            with open(json_path) as f:
                data = json.load(f)
            src = data.get("_source_url", "")
            # Extract UUID from URL: .../uuid.mp4
            if src:
                uuid = src.split("/")[-1].replace(".mp4", "")
                analyzed.add(uuid)
        except (json.JSONDecodeError, KeyError):
            continue
    return analyzed


def fetch_new_clips(count=20, badged_only=False, already_analyzed=None):
    """Fetch clips from anon endpoint, skipping already-analyzed ones."""
    if already_analyzed is None:
        already_analyzed = set()

    new_clips = []
    pages_scanned = 0

    for page in range(1, 200):
        url = f"{BASE_URL}{ANON_ENDPOINT}"
        params = {"page": page, "page_size": 100}

        try:
            r = requests.get(url, params=params, headers={"Accept": "application/json"}, timeout=30)
        except requests.RequestException as e:
            print(f"  Network error page {page}: {e}")
            break

        if r.status_code != 200:
            break

        data = r.json()
        results = data.get("results", [])
        if not results:
            break

        pages_scanned += 1

        for group in results:
            highlight_file = group.get("highlight_file")
            if not highlight_file:
                continue

            uuid = highlight_file.split("/")[-1].replace(".mp4", "")
            if uuid in already_analyzed:
                continue

            badges = group.get("badge_awards", [])
            if badged_only and not badges:
                continue

            new_clips.append({
                "file": highlight_file,
                "url": highlight_file,
                "uuid": uuid,
                "badge_awards": badges,
                "profile_username": badges[0].get("profile_username", "unknown") if badges else "unknown",
                "badge_count": len(badges),
            })

            if len(new_clips) >= count:
                break

        if len(new_clips) >= count:
            break

        time.sleep(0.3)

    print(f"  Scanned {pages_scanned} pages, found {len(new_clips)} new clips")
    return new_clips


def run_analysis(manifest_path, output_dir, prompt_file, limit):
    """Run the Gemini analyzer on the manifest."""
    cmd = [
        sys.executable, "pickle-daas-gemini-analyzer.py",
        "--url-file", manifest_path,
        "--prompt-file", prompt_file,
        "--output-dir", output_dir,
        "--limit", str(limit),
    ]
    print(f"\n  Running: {' '.join(cmd[:6])}...")
    result = subprocess.run(cmd, capture_output=False)
    return result.returncode


def run_warehouse():
    """Run badge warehouse to update cross-references."""
    cmd = [sys.executable, "tools/badge-warehouse.py", "all"]
    print(f"\n  Running badge warehouse...")
    result = subprocess.run(cmd, capture_output=False)
    return result.returncode


def log_ingest(new_count, output_dir, prompt_file):
    """Append to the ingest log for tracking."""
    entry = {
        "timestamp": datetime.now().isoformat(),
        "new_clips": new_count,
        "output_dir": output_dir,
        "prompt": prompt_file,
    }
    log = []
    if Path(INGEST_LOG).exists():
        try:
            with open(INGEST_LOG) as f:
                log = json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            log = []
    log.append(entry)
    with open(INGEST_LOG, "w") as f:
        json.dump(log, f, indent=2)


def main():
    parser = argparse.ArgumentParser(description="Pickle DaaS — Auto-Ingest new clips")
    parser.add_argument("--count", type=int, default=20, help="Max new clips to ingest (default: 20)")
    parser.add_argument("--badged-only", action="store_true", help="Only ingest clips with Courtana badge awards")
    parser.add_argument("--prompt", default=DEFAULT_PROMPT, help=f"Prompt file (default: {DEFAULT_PROMPT})")
    parser.add_argument("--warehouse", action="store_true", help="Run badge warehouse after analysis")
    parser.add_argument("--dry-run", action="store_true", help="Find new clips but don't analyze")
    args = parser.parse_args()

    print(f"{'='*60}")
    print(f"Pickle DaaS Auto-Ingest — {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print(f"{'='*60}")

    # 1. Scan existing corpus
    print("\n[1/4] Scanning existing corpus...")
    already = get_already_analyzed()
    print(f"  Already analyzed: {len(already)} clips")

    # 2. Fetch new clips
    print(f"\n[2/4] Fetching up to {args.count} new clips...")
    new_clips = fetch_new_clips(
        count=args.count,
        badged_only=args.badged_only,
        already_analyzed=already,
    )

    if not new_clips:
        print("\n  No new clips found. Corpus is up to date.")
        return

    print(f"  Found {len(new_clips)} new clips to analyze")
    if args.badged_only:
        total_badges = sum(c["badge_count"] for c in new_clips)
        print(f"  Total badge awards in new clips: {total_badges}")

    if args.dry_run:
        print("\n  [DRY RUN] Would analyze these clips:")
        for c in new_clips[:10]:
            print(f"    {c['uuid'][:12]}... ({c['profile_username']}, {c['badge_count']} badges)")
        if len(new_clips) > 10:
            print(f"    ... and {len(new_clips) - 10} more")
        return

    # 3. Write manifest and run analysis
    timestamp = datetime.now().strftime("%Y%m%d-%H%M")
    output_dir = f"output/auto-ingest-{timestamp}"
    manifest_path = f"{output_dir}/manifest.json"

    Path(output_dir).mkdir(parents=True, exist_ok=True)
    with open(manifest_path, "w") as f:
        json.dump(new_clips, f, indent=2)
    print(f"  Manifest: {manifest_path}")

    print(f"\n[3/4] Analyzing {len(new_clips)} clips...")
    rc = run_analysis(manifest_path, output_dir, args.prompt, len(new_clips))

    analyzed_count = len(glob.glob(f"{output_dir}/analysis_*.json"))
    print(f"\n  Completed: {analyzed_count}/{len(new_clips)} clips analyzed")

    # 4. Optional warehouse
    if args.warehouse:
        print(f"\n[4/4] Running badge warehouse...")
        run_warehouse()
    else:
        print(f"\n[4/4] Skipping warehouse (use --warehouse to enable)")

    # Log
    log_ingest(analyzed_count, output_dir, args.prompt)
    print(f"\nDone. Corpus grew by {analyzed_count} clips.")
    print(f"Total corpus: {len(already) + analyzed_count} analyzed clips")


if __name__ == "__main__":
    main()

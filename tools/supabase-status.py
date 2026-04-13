#!/usr/bin/env python3
"""
supabase-status.py — Pickle DaaS Supabase Health Check
========================================================
Single-command visibility into what's actually in Supabase.
Shows row counts, freshness, gaps vs local corpus, and suggests fixes.

Usage:
  python3 tools/supabase-status.py
  python3 tools/supabase-status.py --verbose  # show sample rows
"""

import json
import os
import sys
import argparse
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).parent.parent

# Load .env manually (supports running from any CWD)
env_path = ROOT / ".env"
if env_path.exists():
    for line in env_path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        os.environ.setdefault(k, v.strip())


def color(s, c):
    codes = {"green": "\033[92m", "yellow": "\033[93m", "red": "\033[91m",
             "blue": "\033[94m", "bold": "\033[1m", "end": "\033[0m"}
    return f"{codes.get(c, '')}{s}{codes['end']}"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--verbose", "-v", action="store_true", help="Show sample rows")
    args = parser.parse_args()

    try:
        from supabase import create_client
    except ImportError:
        print(color("ERROR: supabase-py not installed. Run: pip install supabase", "red"))
        sys.exit(1)

    url = os.environ.get("SUPABASE_URL")
    key = os.environ.get("SUPABASE_SERVICE_KEY")
    if not url or not key:
        print(color("ERROR: SUPABASE_URL and SUPABASE_SERVICE_KEY must be in .env", "red"))
        sys.exit(1)

    print(color("=" * 60, "bold"))
    print(color("  PICKLE DAAS — SUPABASE HEALTH CHECK", "bold"))
    print(color("=" * 60, "bold"))
    print(f"  URL:       {url}")
    print(f"  Checked:   {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}")
    print()

    client = create_client(url, key)

    # Check each expected table
    tables = [
        ("pickle_daas_analyses", "Main clip analyses"),
        ("pickle_daas_brands", "Brand detections"),
        ("pickle_daas_players", "Player profiles"),
    ]

    table_status = {}
    for tname, desc in tables:
        try:
            r = client.table(tname).select("*", count="exact").limit(1).execute()
            table_status[tname] = {"exists": True, "count": r.count, "sample": r.data}
        except Exception as e:
            msg = str(e)
            if "does not exist" in msg.lower() or "not found" in msg.lower() or "PGRST205" in msg:
                table_status[tname] = {"exists": False, "error": "Table does not exist"}
            else:
                table_status[tname] = {"exists": False, "error": msg[:100]}

    # Display
    for tname, desc in tables:
        s = table_status[tname]
        if not s["exists"]:
            badge = color("❌ MISSING", "red")
            print(f"  {badge}  {tname}")
            print(f"            {desc}")
            print(f"            Error: {s.get('error', 'unknown')}")
        elif s["count"] == 0:
            badge = color("⚠️  EMPTY ", "yellow")
            print(f"  {badge}  {tname:<30} {s['count']:>5} rows")
            print(f"            {desc} — schema exists but never populated")
        else:
            badge = color("✅ OK    ", "green")
            print(f"  {badge}  {tname:<30} {s['count']:>5} rows")
            print(f"            {desc}")
        print()

    # Gap analysis for main table
    if table_status["pickle_daas_analyses"]["exists"]:
        supabase_count = table_status["pickle_daas_analyses"]["count"]

        # Try gh-pages corpus (source of truth)
        import subprocess
        result = subprocess.run(
            ["git", "show", "gh-pages:corpus-export.json"],
            capture_output=True, text=True, cwd=ROOT
        )
        if result.returncode == 0:
            gh_corpus = json.loads(result.stdout)
            gh_count = len(gh_corpus)
            gap = gh_count - supabase_count

            print(color("  GAP ANALYSIS", "bold"))
            print(f"     gh-pages corpus:  {color(str(gh_count), 'green')} clips (source of truth)")
            print(f"     Supabase:         {color(str(supabase_count), 'blue')} clips")
            if gap > 0:
                print(f"     Gap:              {color(f'{gap} clips missing from Supabase', 'yellow')}")
                print(f"     Fix:              python3 tools/sync-to-supabase.py")
            elif gap < 0:
                print(f"     Gap:              {color(f'{abs(gap)} clips in Supabase but not gh-pages', 'yellow')}")
            else:
                print(f"     Gap:              {color('none — fully synced', 'green')}")
            print()

    # Latest row in Supabase
    if table_status["pickle_daas_analyses"]["exists"] and table_status["pickle_daas_analyses"]["count"] > 0:
        try:
            latest = client.table("pickle_daas_analyses").select("analyzed_at").order("analyzed_at", desc=True).limit(1).execute()
            if latest.data and latest.data[0].get("analyzed_at"):
                print(color("  LATEST ANALYSIS", "bold"))
                print(f"     {latest.data[0]['analyzed_at']}")
                print()
        except Exception:
            pass

    # Verbose: sample rows
    if args.verbose:
        print(color("  SAMPLE ROWS", "bold"))
        try:
            sample = client.table("pickle_daas_analyses").select(
                "video_url,clip_quality_score,viral_potential_score,story_arc,analyzed_at"
            ).limit(3).execute()
            for r in sample.data:
                url = r.get("video_url", "")[-40:] if r.get("video_url") else "none"
                print(f"     {url[:40]}")
                print(f"        quality={r.get('clip_quality_score')} viral={r.get('viral_potential_score')} arc={r.get('story_arc')}")
            print()
        except Exception as e:
            print(f"     Could not fetch samples: {e}")
            print()

    # Recommendations
    print(color("  RECOMMENDATIONS", "bold"))
    recs = []
    if not table_status["pickle_daas_players"]["exists"]:
        recs.append("Create pickle_daas_players table (schema in supabase/SUPABASE-SETUP-GUIDE.md)")
    if table_status["pickle_daas_brands"]["exists"] and table_status["pickle_daas_brands"]["count"] == 0:
        recs.append("Populate pickle_daas_brands table (run tools/sync-to-supabase.py)")
    if table_status["pickle_daas_analyses"]["exists"] and gh_count and gap > 0:
        recs.append(f"Sync {gap} missing clips to Supabase (run tools/sync-to-supabase.py)")

    if not recs:
        print(f"     {color('✅ Everything looks healthy!', 'green')}")
    else:
        for i, r in enumerate(recs, 1):
            print(f"     {i}. {r}")
    print()
    print(color("=" * 60, "bold"))


if __name__ == "__main__":
    main()

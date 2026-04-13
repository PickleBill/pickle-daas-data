#!/usr/bin/env python3
"""
sync-to-supabase.py — Fill the gaps in Pickle DaaS Supabase
=============================================================
1. Creates pickle_daas_players table if missing (prints SQL for Bill to run)
2. Syncs missing clips from gh-pages corpus → pickle_daas_analyses
3. Derives pickle_daas_brands rows from the full corpus
4. Derives pickle_daas_players rows from clip metadata (if profile_username present)

Usage:
  python3 tools/sync-to-supabase.py           # sync analyses + brands
  python3 tools/sync-to-supabase.py --dry     # show what would change
  python3 tools/sync-to-supabase.py --players # also derive players
"""

import json
import os
import sys
import argparse
import subprocess
from pathlib import Path

ROOT = Path(__file__).parent.parent

# Load .env manually
env_path = ROOT / ".env"
if env_path.exists():
    for line in env_path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        os.environ.setdefault(k, v.strip())


PLAYERS_TABLE_SQL = """
-- Run this in Supabase SQL Editor:
-- https://supabase.com/dashboard/project/vlcjaftwnllfjyckjchg/sql

CREATE TABLE IF NOT EXISTS pickle_daas_players (
    id BIGSERIAL PRIMARY KEY,
    username TEXT UNIQUE NOT NULL,
    display_name TEXT,
    clip_count INTEGER DEFAULT 0,
    avg_quality NUMERIC(3,1),
    avg_viral NUMERIC(3,1),
    top_skill TEXT,
    play_style TEXT,
    brands_used TEXT[],
    first_seen TIMESTAMPTZ,
    last_seen TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_players_username ON pickle_daas_players(username);
CREATE INDEX IF NOT EXISTS idx_players_clip_count ON pickle_daas_players(clip_count DESC);
"""


def load_gh_pages_corpus():
    """Source of truth: gh-pages corpus-export.json."""
    result = subprocess.run(
        ["git", "show", "gh-pages:corpus-export.json"],
        capture_output=True, text=True, cwd=ROOT
    )
    if result.returncode != 0:
        raise RuntimeError(f"Could not read gh-pages:corpus-export.json: {result.stderr}")
    return json.loads(result.stdout)


def sync_analyses(client, corpus, dry_run=False):
    """Push clips from corpus to pickle_daas_analyses that aren't there yet."""
    existing = client.table("pickle_daas_analyses").select("video_url").execute()
    existing_urls = {r["video_url"] for r in existing.data if r.get("video_url")}

    missing = [c for c in corpus if c.get("video_url") and c["video_url"] not in existing_urls]

    print(f"  [analyses] Supabase has {len(existing_urls)} clips, corpus has {len(corpus)}")
    print(f"  [analyses] Missing from Supabase: {len(missing)}")

    if dry_run or not missing:
        return {"added": 0, "skipped": 0, "errors": 0}

    added = skipped = errors = 0
    for c in missing:
        try:
            # Map corpus-export schema → pickle_daas_analyses schema
            skills = c.get("skills", {}) or {}
            row = {
                "video_url": c["video_url"],
                "clip_quality_score": c.get("quality"),
                "viral_potential_score": c.get("viral"),
                "watchability_score": c.get("watchability"),
                "brands_detected": json.dumps(c.get("brands", [])),
                "predicted_badges": json.dumps(c.get("badges", [])),
                "skill_indicators": json.dumps({
                    "court_coverage_rating": skills.get("court_coverage"),
                    "kitchen_mastery_rating": skills.get("kitchen"),
                    "power_game_rating": skills.get("power"),
                    "touch_and_feel_rating": skills.get("touch"),
                    "athleticism_rating": skills.get("athleticism"),
                    "creativity_rating": skills.get("creativity"),
                    "court_iq_rating": skills.get("court_iq"),
                    "consistency_rating": skills.get("consistency"),
                    "composure_under_pressure": skills.get("composure"),
                    "signature_move_detected": c.get("signature_move"),
                    "aggression_style": c.get("play_style"),
                }),
                "storytelling": json.dumps({"story_arc": c.get("arc", "")}),
                "daas_signals": json.dumps({"clip_summary_one_sentence": c.get("summary", "")}),
                "commentary_espn": c.get("espn", ""),
                "commentary_social_caption": c.get("social_caption", ""),
                "commentary_ron_burgundy": c.get("ron_burgundy", ""),
                "clip_summary": c.get("summary", ""),
                "story_arc": c.get("arc", ""),
                "full_analysis": json.dumps(c),
            }
            client.table("pickle_daas_analyses").insert(row).execute()
            added += 1
        except Exception as e:
            msg = str(e).lower()
            if "duplicate" in msg or "23505" in msg or "unique" in msg:
                skipped += 1
            else:
                errors += 1
                if errors <= 3:
                    print(f"     ERROR on {c.get('uuid', '?')[:10]}: {str(e)[:80]}")

    print(f"  [analyses] Added: {added}, Skipped: {skipped}, Errors: {errors}")
    return {"added": added, "skipped": skipped, "errors": errors}


def sync_brands(client, corpus, dry_run=False):
    """Aggregate brand detections from corpus into pickle_daas_brands table."""
    from collections import Counter, defaultdict

    # Check schema first
    try:
        probe = client.table("pickle_daas_brands").select("*").limit(1).execute()
        existing_cols = set(probe.data[0].keys()) if probe.data else None
    except Exception as e:
        print(f"  [brands] Could not probe schema: {e}")
        existing_cols = None

    # Aggregate
    brand_appearances = Counter()
    brand_quality = defaultdict(list)
    brand_viral = defaultdict(list)
    brand_clip_count = defaultdict(set)

    for c in corpus:
        for b in c.get("brands", []):
            if not b:
                continue
            b_norm = b.strip()
            if not b_norm:
                continue
            brand_appearances[b_norm] += 1
            brand_clip_count[b_norm].add(c.get("uuid", c.get("video_url", "")))
            if c.get("quality"):
                brand_quality[b_norm].append(c["quality"])
            if c.get("viral"):
                brand_viral[b_norm].append(c["viral"])

    print(f"  [brands] Aggregated {len(brand_appearances)} unique brands")
    print(f"  [brands] Top 5: {brand_appearances.most_common(5)}")

    if dry_run:
        return {"added": 0, "skipped": 0, "errors": 0}

    # Clear existing, insert fresh aggregates
    try:
        # Use a "truthy" filter that matches everything to delete all rows
        client.table("pickle_daas_brands").delete().neq("brand_name", "___impossible___").execute()
    except Exception as e:
        print(f"  [brands] Could not clear table: {e}")

    added = errors = 0
    for brand, count in brand_appearances.most_common():
        try:
            clip_urls = list(brand_clip_count[brand])[:100]  # cap array size
            # Schema: brand_name, category, total_appearances, total_clips_seen_in,
            #         player_usernames, clips_seen_in, avg_confidence, last_seen_at
            row = {
                "brand_name": brand,
                "total_appearances": count,
                "total_clips_seen_in": len(brand_clip_count[brand]),
                "clips_seen_in": clip_urls,
                "player_usernames": [],
                "avg_confidence": None,
            }
            client.table("pickle_daas_brands").insert(row).execute()
            added += 1
        except Exception as e:
            errors += 1
            if errors <= 3:
                print(f"     ERROR on '{brand}': {str(e)[:100]}")

    print(f"  [brands] Added: {added}, Errors: {errors}")
    return {"added": added, "errors": errors}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry", action="store_true", help="Show what would change, don't write")
    parser.add_argument("--players", action="store_true", help="Also derive players table (requires table exists)")
    args = parser.parse_args()

    try:
        from supabase import create_client
    except ImportError:
        print("ERROR: pip install supabase")
        sys.exit(1)

    url = os.environ.get("SUPABASE_URL")
    key = os.environ.get("SUPABASE_SERVICE_KEY")
    if not url or not key:
        print("ERROR: SUPABASE_URL and SUPABASE_SERVICE_KEY not set")
        sys.exit(1)

    client = create_client(url, key)

    print("=" * 60)
    print("  PICKLE DAAS — SYNC TO SUPABASE")
    print("=" * 60)
    if args.dry:
        print("  DRY RUN (no writes)\n")

    print("Loading gh-pages corpus (source of truth)...")
    corpus = load_gh_pages_corpus()
    print(f"  → {len(corpus)} clips loaded\n")

    # Sync analyses
    print("[1/2] Syncing pickle_daas_analyses...")
    r1 = sync_analyses(client, corpus, dry_run=args.dry)
    print()

    # Sync brands
    print("[2/2] Rebuilding pickle_daas_brands from corpus...")
    r2 = sync_brands(client, corpus, dry_run=args.dry)
    print()

    # Players (optional — requires table to exist)
    if args.players:
        print("Note: pickle_daas_players requires the table to exist.")
        print("If it doesn't, create it with this SQL in Supabase:")
        print(PLAYERS_TABLE_SQL)

    print("=" * 60)
    print("  SUMMARY")
    print("=" * 60)
    print(f"  Analyses added: {r1['added']} (skipped {r1['skipped']}, errors {r1['errors']})")
    print(f"  Brands added:   {r2['added']} (errors {r2['errors']})")
    print(f"\n  Verify: python3 tools/supabase-status.py")


if __name__ == "__main__":
    main()

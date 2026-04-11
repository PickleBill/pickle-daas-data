#!/usr/bin/env python3
"""
Pickle DaaS — Push Gemini Analysis to Supabase
================================================
Reads analysis JSON files from a batch output directory and pushes
each one to the Supabase pickle_daas_analyses table.

USAGE:
  python supabase/push-analysis-to-db.py output/picklebill-batch-20260410/
  python supabase/push-analysis-to-db.py output/batch-30-daas/ output/picklebill-batch-001/

REQUIRES (in .env or environment):
  SUPABASE_URL           - Your Supabase project URL
  SUPABASE_SERVICE_KEY   - Service role key (not anon key)
"""

import os
import sys
import json
import glob
from pathlib import Path

try:
    from dotenv import load_dotenv
    load_dotenv(dotenv_path=Path(__file__).parent.parent / '.env')
except ImportError:
    pass

try:
    from supabase import create_client
except ImportError:
    print("ERROR: supabase not installed. Run: pip install supabase")
    sys.exit(1)


def flatten_analysis(data: dict) -> dict:
    """Convert a Gemini analysis JSON into the Supabase row format."""
    meta = data.get('clip_meta', {})
    story = data.get('storytelling', {})
    daas = data.get('daas_signals', {})
    comment = data.get('commentary', {})
    badge = data.get('badge_intelligence', {})
    brands = data.get('brand_detection', {})

    return {
        # Source info
        'video_url': data.get('_source_url', ''),
        'analyzed_at': data.get('analyzed_at'),

        # Scores
        'clip_quality_score': meta.get('clip_quality_score'),
        'viral_potential_score': meta.get('viral_potential_score'),
        'watchability_score': meta.get('watchability_score'),
        'cinematic_score': meta.get('cinematic_score'),

        # Structured data
        'brands_detected': json.dumps(brands.get('brands', [])),
        'predicted_badges': json.dumps(badge.get('predicted_badges', [])),
        'shot_analysis': json.dumps(data.get('shot_analysis', {})),
        'skill_indicators': json.dumps(data.get('skill_indicators', {})),
        'storytelling': json.dumps(story),
        'daas_signals': json.dumps(daas),

        # Commentary (denormalized for fast UI access)
        'commentary_espn': comment.get('neutral_announcer_espn', ''),
        'commentary_hype': comment.get('hype_announcer_charged', ''),
        'commentary_social_caption': comment.get('social_media_caption', ''),
        'commentary_hashtags': json.dumps(comment.get('social_media_hashtags', [])),
        'commentary_ron_burgundy': comment.get('ron_burgundy_voice', ''),
        'commentary_chuck_norris': comment.get('chuck_norris_voice', ''),
        'commentary_tts_clean': comment.get('announcement_text_for_tts', ''),

        # Discovery
        'clip_summary': daas.get('clip_summary_one_sentence', ''),
        'search_tags': json.dumps(daas.get('search_tags', [])),
        'story_arc': story.get('story_arc', ''),
        'highlight_category': daas.get('highlight_category', ''),

        # Full raw output
        'full_analysis': json.dumps(data),
    }


def push_directory(client, directory: str, dry_run: bool = False) -> tuple[int, int]:
    """Push all analysis JSON files from a directory. Returns (success, error) counts."""
    pattern = os.path.join(directory, 'analysis_*.json')
    files = glob.glob(pattern)

    if not files:
        print(f"  No analysis_*.json files found in {directory}")
        return 0, 0

    success = 0
    errors = 0

    for filepath in sorted(files):
        filename = os.path.basename(filepath)
        try:
            with open(filepath) as f:
                data = json.load(f)

            if not data.get('clip_meta'):
                print(f"  ⚠️  {filename[:40]}... — skipped (no clip_meta, likely failed analysis)")
                continue

            quality = data.get('clip_meta', {}).get('clip_quality_score', '?')
            summary = data.get('daas_signals', {}).get('clip_summary_one_sentence', '')[:60]

            if dry_run:
                print(f"  [DRY RUN] Would push: {filename[:40]}... (quality={quality})")
                success += 1
                continue

            row = flatten_analysis(data)
            result = client.table('pickle_daas_analyses').upsert(row, on_conflict='video_url').execute()

            print(f"  ✅ {filename[:40]}... (quality={quality}) — {summary}...")
            success += 1

        except Exception as e:
            print(f"  ❌ {filename[:40]}... ERROR: {e}")
            errors += 1

    return success, errors


def main():
    if len(sys.argv) < 2:
        print("Usage: python push-analysis-to-db.py <dir1> [dir2] ...")
        sys.exit(1)

    dry_run = '--dry-run' in sys.argv
    directories = [d for d in sys.argv[1:] if not d.startswith('--')]

    supabase_url = os.environ.get('SUPABASE_URL')
    supabase_key = os.environ.get('SUPABASE_SERVICE_KEY')

    if not supabase_url or not supabase_key:
        print("ERROR: SUPABASE_URL and SUPABASE_SERVICE_KEY must be set in .env or environment")
        sys.exit(1)

    if dry_run:
        print("DRY RUN MODE — no data will be written\n")
        client = None
    else:
        client = create_client(supabase_url, supabase_key)
        print(f"Connected to Supabase: {supabase_url[:40]}...\n")

    total_success = 0
    total_errors = 0

    for directory in directories:
        if not os.path.isdir(directory):
            print(f"WARNING: {directory} is not a directory, skipping")
            continue

        print(f"Pushing from: {directory}")
        s, e = push_directory(client, directory, dry_run=dry_run)
        total_success += s
        total_errors += e
        print()

    print(f"{'[DRY RUN] ' if dry_run else ''}Done: {total_success} pushed, {total_errors} errors")

    if total_errors > 0:
        sys.exit(1)


if __name__ == '__main__':
    main()

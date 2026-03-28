#!/usr/bin/env python3
"""Push local Gemini analysis JSON files to Supabase."""
import os, sys, json, glob, requests
from dotenv import load_dotenv
load_dotenv()

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_ANON_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    print("ERROR: Set SUPABASE_URL and SUPABASE_ANON_KEY in .env")
    sys.exit(1)

def push_analysis(filepath):
    with open(filepath) as f:
        analysis = json.load(f)

    row = {
        "highlight_id": analysis.get("_highlight_meta", {}).get("id", ""),
        "highlight_name": analysis.get("_highlight_meta", {}).get("name", ""),
        "video_url": analysis.get("_source_url", ""),
        "clip_quality_score": analysis.get("clip_meta", {}).get("clip_quality_score"),
        "viral_potential_score": analysis.get("clip_meta", {}).get("viral_potential_score"),
        "watchability_score": analysis.get("clip_meta", {}).get("watchability_score"),
        "cinematic_score": analysis.get("clip_meta", {}).get("cinematic_score"),
        "brands_detected": json.dumps(analysis.get("brand_detection", {}).get("brands", [])),
        "predicted_badges": json.dumps(analysis.get("badge_intelligence", {}).get("predicted_badges", [])),
        "play_style_tags": json.dumps(analysis.get("skill_indicators", {}).get("play_style_tags", [])),
        "shot_analysis": json.dumps(analysis.get("shot_analysis", {})),
        "skill_indicators": json.dumps(analysis.get("skill_indicators", {})),
        "storytelling": json.dumps(analysis.get("storytelling", {})),
        "commentary_espn": analysis.get("commentary", {}).get("neutral_announcer_espn"),
        "commentary_hype": analysis.get("commentary", {}).get("hype_announcer_charged"),
        "commentary_ron_burgundy": analysis.get("commentary", {}).get("ron_burgundy_voice"),
        "commentary_chuck_norris": analysis.get("commentary", {}).get("chuck_norris_voice"),
        "commentary_tts_clean": analysis.get("commentary", {}).get("announcement_text_for_tts"),
        "clip_summary": analysis.get("daas_signals", {}).get("clip_summary_one_sentence"),
        "search_tags": json.dumps(analysis.get("daas_signals", {}).get("search_tags", [])),
        "story_arc": analysis.get("storytelling", {}).get("story_arc"),
        "highlight_category": analysis.get("daas_signals", {}).get("highlight_category"),
        "full_analysis": json.dumps(analysis),
        "batch_id": analysis.get("_batch_id", ""),
    }

    resp = requests.post(
        f"{SUPABASE_URL}/rest/v1/pickle_daas_analyses",
        json=row,
        headers={
            "apikey": SUPABASE_KEY,
            "Authorization": f"Bearer {SUPABASE_KEY}",
            "Content-Type": "application/json",
            "Prefer": "return=representation"
        }
    )

    if resp.status_code in (200, 201):
        print(f"  ✅ Pushed: {filepath}")
    else:
        print(f"  ❌ Failed ({resp.status_code}): {resp.text[:200]}")

if __name__ == "__main__":
    pattern = sys.argv[1] if len(sys.argv) > 1 else "./output/**/analysis_*.json"
    files = glob.glob(pattern, recursive=True)
    print(f"Found {len(files)} analysis files to push")
    for f in files:
        push_analysis(f)

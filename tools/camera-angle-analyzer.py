#!/usr/bin/env python3
"""
Camera & Venue Quality Analyzer
Extracts camera/venue quality metadata from existing Gemini analysis JSON files.
No API calls — reads only from local output/ directory.

Output: output/discovery/camera-analysis.json
"""

import json
import glob
import os
import re
from datetime import datetime, timezone
from collections import Counter

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUTPUT_DIR = os.path.join(BASE_DIR, "output")
DISCOVERY_DIR = os.path.join(OUTPUT_DIR, "discovery")

# Keywords that suggest indoor vs outdoor
INDOOR_KEYWORDS = [
    "indoor", "gym", "facility", "warehouse", "recreation center",
    "community center", "sports complex", "arena", "court surface",
    "overhead lights", "fluorescent", "ceiling"
]
OUTDOOR_KEYWORDS = [
    "outdoor", "sun", "sunlight", "sunglasses", "shadow", "wind",
    "park", "outside", "natural light", "sky", "grass", "trees"
]

SCOREBOARD_KEYWORDS = [
    "scoreboard", "score", "scorekeeping", "score display",
    "digital score", "flip score"
]


def load_analysis_files():
    """Find and load all analysis_*.json files > 5KB."""
    pattern = os.path.join(OUTPUT_DIR, "**", "analysis_*.json")
    files = glob.glob(pattern, recursive=True)

    results = []
    for fpath in files:
        if os.path.getsize(fpath) < 5000:
            continue
        try:
            with open(fpath, "r") as f:
                data = json.load(f)
            data["_file_path"] = fpath
            results.append(data)
        except (json.JSONDecodeError, IOError) as e:
            print(f"  [SKIP] Could not read {os.path.basename(fpath)}: {e}")
    return results


def extract_clip_id(data):
    """Extract clip ID from source URL or filename."""
    src = data.get("_source_url", "")
    if src:
        # URL pattern: .../clip-uuid.mp4
        basename = src.split("/")[-1].replace(".mp4", "")
        return basename
    fpath = data.get("_file_path", "")
    fname = os.path.basename(fpath)
    # filename pattern: analysis_clip-uuid_timestamp.json
    parts = fname.replace("analysis_", "").replace(".json", "").rsplit("_", 1)
    return parts[0] if parts else fname


def infer_indoor_outdoor(data):
    """Infer indoor/outdoor from apparel, search tags, commentary, and brand data."""
    text_sources = []

    # Apparel descriptions
    for player in data.get("players_detected", []):
        text_sources.append(player.get("apparel_summary", "").lower())

    # Search tags
    tags = data.get("daas_signals", {}).get("search_tags", [])
    text_sources.extend([t.lower() for t in tags])

    # Commentary
    commentary = data.get("commentary", {})
    for key, val in commentary.items():
        if isinstance(val, str):
            text_sources.append(val.lower())

    # Brand detection notes
    brand_det = data.get("brand_detection", {})
    text_sources.append(brand_det.get("unidentified_equipment_notes", "").lower())
    text_sources.append(brand_det.get("unidentified_products_notes", "").lower())
    for b in brand_det.get("brands", []):
        text_sources.append(b.get("color_scheme_noted", "").lower())

    # Storytelling narrative
    storytelling = data.get("storytelling", {})
    text_sources.append(storytelling.get("narrative_arc_summary", "").lower())

    combined = " ".join(text_sources)

    indoor_score = sum(1 for kw in INDOOR_KEYWORDS if kw in combined)
    outdoor_score = sum(1 for kw in OUTDOOR_KEYWORDS if kw in combined)

    if indoor_score > outdoor_score:
        return "indoor"
    elif outdoor_score > indoor_score:
        return "outdoor"
    return "unknown"


def check_scoreboard(data):
    """Check if scoreboard is mentioned anywhere in the analysis."""
    text_sources = []

    commentary = data.get("commentary", {})
    for key, val in commentary.items():
        if isinstance(val, str):
            text_sources.append(val.lower())

    signals = data.get("daas_signals", {})
    text_sources.append(signals.get("clip_summary_one_sentence", "").lower())
    text_sources.extend([t.lower() for t in signals.get("search_tags", [])])

    storytelling = data.get("storytelling", {})
    text_sources.append(storytelling.get("narrative_arc_summary", "").lower())

    combined = " ".join(text_sources)
    return any(kw in combined for kw in SCOREBOARD_KEYWORDS)


def analyze_clip(data):
    """Extract camera/venue quality signals from one analysis file."""
    clip_meta = data.get("clip_meta", {})
    players = data.get("players_detected", [])
    storytelling = data.get("storytelling", {})
    daas = data.get("daas_signals", {})

    clip_id = extract_clip_id(data)
    batch_dir = os.path.basename(os.path.dirname(data.get("_file_path", "")))

    # Camera quality from cinematic_score (1-10)
    cinematic = clip_meta.get("cinematic_score", None)
    camera_quality = None
    if cinematic is not None:
        if cinematic >= 8:
            camera_quality = "high"
        elif cinematic >= 5:
            camera_quality = "medium"
        else:
            camera_quality = "low"

    # Court visibility from player count
    player_count = len(players)
    if player_count >= 4:
        court_visibility = "full_court"
    elif player_count >= 2:
        court_visibility = "partial"
    elif player_count >= 1:
        court_visibility = "limited"
    else:
        court_visibility = "none"

    # Lighting quality from clip_quality_score
    quality_score = clip_meta.get("clip_quality_score", None)
    lighting_quality = None
    if quality_score is not None:
        if quality_score >= 8:
            lighting_quality = "excellent"
        elif quality_score >= 6:
            lighting_quality = "good"
        elif quality_score >= 4:
            lighting_quality = "fair"
        else:
            lighting_quality = "poor"

    # Indoor/outdoor inference
    venue_type = infer_indoor_outdoor(data)

    # Crowd presence
    crowd_present = storytelling.get("crowd_energy_detected", False)

    # Scoreboard visible
    scoreboard_visible = check_scoreboard(data)

    # Extra context
    match_context = daas.get("match_context_inferred", "unknown")
    estimated_rating = daas.get("estimated_player_rating_dupr", "unknown")
    story_arc = storytelling.get("story_arc", "unknown")

    return {
        "clip_id": clip_id,
        "batch": batch_dir,
        "source_url": data.get("_source_url", ""),
        "camera_quality": camera_quality,
        "cinematic_score": cinematic,
        "court_visibility": court_visibility,
        "players_detected": player_count,
        "lighting_quality": lighting_quality,
        "clip_quality_score": quality_score,
        "venue_type": venue_type,
        "crowd_present": crowd_present,
        "scoreboard_visible": scoreboard_visible,
        "match_context": match_context,
        "estimated_dupr": estimated_rating,
        "story_arc": story_arc,
        "analyzed_at": data.get("analyzed_at", ""),
    }


def print_summary(results):
    """Print a human-readable summary."""
    print("\n" + "=" * 60)
    print("CAMERA & VENUE QUALITY ANALYSIS")
    print("=" * 60)
    print(f"\nClips analyzed: {len(results)}")

    # Camera quality distribution
    cam_dist = Counter(r["camera_quality"] for r in results)
    print(f"\nCamera Quality Distribution:")
    for k, v in sorted(cam_dist.items(), key=lambda x: -x[1]):
        print(f"  {k or 'unknown':>10}: {v} clips")

    # Court visibility
    vis_dist = Counter(r["court_visibility"] for r in results)
    print(f"\nCourt Visibility:")
    for k, v in sorted(vis_dist.items(), key=lambda x: -x[1]):
        print(f"  {k:>12}: {v} clips")

    # Lighting
    light_dist = Counter(r["lighting_quality"] for r in results)
    print(f"\nLighting Quality:")
    for k, v in sorted(light_dist.items(), key=lambda x: -x[1]):
        print(f"  {k or 'unknown':>10}: {v} clips")

    # Venue type
    venue_dist = Counter(r["venue_type"] for r in results)
    print(f"\nVenue Type (inferred):")
    for k, v in sorted(venue_dist.items(), key=lambda x: -x[1]):
        print(f"  {k:>10}: {v} clips")

    # Crowd presence
    crowd_count = sum(1 for r in results if r["crowd_present"])
    print(f"\nCrowd Detected: {crowd_count}/{len(results)} clips")

    # Scoreboard
    sb_count = sum(1 for r in results if r["scoreboard_visible"])
    print(f"Scoreboard Mentioned: {sb_count}/{len(results)} clips")

    # Average scores
    cin_scores = [r["cinematic_score"] for r in results if r["cinematic_score"] is not None]
    qual_scores = [r["clip_quality_score"] for r in results if r["clip_quality_score"] is not None]
    if cin_scores:
        print(f"\nAvg Cinematic Score: {sum(cin_scores)/len(cin_scores):.1f}/10")
    if qual_scores:
        print(f"Avg Clip Quality Score: {sum(qual_scores)/len(qual_scores):.1f}/10")

    # Match context
    ctx_dist = Counter(r["match_context"] for r in results)
    print(f"\nMatch Context:")
    for k, v in sorted(ctx_dist.items(), key=lambda x: -x[1]):
        print(f"  {k:>14}: {v} clips")

    print(f"\nOutput written to: output/discovery/camera-analysis.json")
    print("=" * 60)


def main():
    print("Loading analysis files...")
    analyses = load_analysis_files()
    print(f"Found {len(analyses)} analysis files (>5KB)")

    if not analyses:
        print("No analysis files found. Nothing to do.")
        return

    results = []
    for data in analyses:
        result = analyze_clip(data)
        results.append(result)

    # Sort by cinematic score descending
    results.sort(key=lambda r: r.get("cinematic_score") or 0, reverse=True)

    # Write output
    os.makedirs(DISCOVERY_DIR, exist_ok=True)
    output_path = os.path.join(DISCOVERY_DIR, "camera-analysis.json")
    output = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "total_clips": len(results),
        "clips": results,
    }
    with open(output_path, "w") as f:
        json.dump(output, f, indent=2)

    print_summary(results)


if __name__ == "__main__":
    main()

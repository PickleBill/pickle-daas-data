#!/usr/bin/env python3
"""
Match Context Analyzer
Groups clips that likely belong to the same match/session and tracks
skill progression and story arc variety within groups.

Grouping strategy (since _highlight_meta is empty in current data):
  1. Primary: _highlight_meta / highlight_group if populated
  2. Fallback: Same source URL user-segment + same analyzed_at date + similar skill levels
     (clips from the same venue/session tend to share these)
  3. Batch directory as a secondary grouping signal

Output: output/discovery/match-context.json
"""

import json
import glob
import os
from datetime import datetime, timezone
from collections import defaultdict, Counter

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUTPUT_DIR = os.path.join(BASE_DIR, "output")
DISCOVERY_DIR = os.path.join(OUTPUT_DIR, "discovery")

# Skill level ordering for progression tracking
SKILL_ORDER = {
    "beginner": 1,
    "beginner_intermediate": 2,
    "intermediate": 3,
    "advanced_intermediate": 4,
    "advanced": 5,
    "elite": 6,
    "pro": 7,
}


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
        return src.split("/")[-1].replace(".mp4", "")
    fpath = data.get("_file_path", "")
    fname = os.path.basename(fpath)
    parts = fname.replace("analysis_", "").replace(".json", "").rsplit("_", 1)
    return parts[0] if parts else fname


def extract_user_segment(data):
    """Extract user/venue segment from source URL."""
    src = data.get("_source_url", "")
    parts = src.split("/")
    if len(parts) >= 3:
        return parts[-2]
    return "unknown"


def extract_timestamp(data):
    """Extract the numeric timestamp from the filename."""
    fpath = data.get("_file_path", "")
    fname = os.path.basename(fpath)
    parts = fname.replace("analysis_", "").replace(".json", "").rsplit("_", 1)
    if len(parts) == 2:
        try:
            return int(parts[1])
        except ValueError:
            pass
    return 0


def get_dominant_skill(data):
    """Get the dominant (most common) skill level across detected players."""
    players = data.get("players_detected", [])
    if not players:
        return "unknown"
    levels = [p.get("estimated_skill_level", "unknown") for p in players]
    counter = Counter(levels)
    return counter.most_common(1)[0][0]


def get_skill_numeric(level):
    """Convert skill level string to numeric for progression tracking."""
    return SKILL_ORDER.get(level, 0)


def compute_group_key(data):
    """
    Determine a grouping key for the clip.
    Priority:
      1. Explicit highlight_group or _highlight_meta with group info
      2. Fallback: user_segment + analyzed_date + batch_dir
    """
    # Check for explicit group
    highlight_group = data.get("highlight_group", data.get("_highlight_group", ""))
    if highlight_group:
        return f"group:{highlight_group}"

    meta = data.get("_highlight_meta", {})
    if meta and meta.get("group_id"):
        return f"meta:{meta['group_id']}"

    # Fallback grouping: user segment + date + batch
    user_seg = extract_user_segment(data)
    analyzed_at = data.get("analyzed_at", "")
    date_part = analyzed_at[:10] if analyzed_at else "nodate"
    batch_dir = os.path.basename(os.path.dirname(data.get("_file_path", "")))

    return f"session:{user_seg}|{date_part}|{batch_dir}"


def analyze_group(group_key, clips_data):
    """Analyze a group of clips for progression and variety."""
    # Sort by file timestamp for chronological order
    clips_data.sort(key=lambda d: extract_timestamp(d))

    clip_infos = []
    skill_progression = []
    story_arcs = []
    shot_types_all = []
    match_contexts = []

    for data in clips_data:
        clip_id = extract_clip_id(data)
        skill = get_dominant_skill(data)
        skill_num = get_skill_numeric(skill)

        story_arc = data.get("storytelling", {}).get("story_arc", "unknown")
        story_arcs.append(story_arc)

        match_ctx = data.get("daas_signals", {}).get("match_context_inferred", "unknown")
        match_contexts.append(match_ctx)

        # Shot type distribution for this clip
        shots = data.get("shot_analysis", {}).get("shots", [])
        dominant_shot = data.get("shot_analysis", {}).get("dominant_shot_type", "unknown")
        shot_types_all.append(dominant_shot)

        skill_indicators = data.get("skill_indicators", {})

        clip_info = {
            "clip_id": clip_id,
            "timestamp": extract_timestamp(data),
            "skill_level": skill,
            "skill_numeric": skill_num,
            "story_arc": story_arc,
            "dominant_shot": dominant_shot,
            "total_shots": data.get("shot_analysis", {}).get("total_shots_estimated", 0),
            "rally_length": data.get("shot_analysis", {}).get("rally_length_estimated", 0),
            "cinematic_score": data.get("clip_meta", {}).get("cinematic_score"),
            "match_context": match_ctx,
            "kitchen_mastery": skill_indicators.get("kitchen_mastery_rating"),
            "power_game": skill_indicators.get("power_game_rating"),
            "consistency": skill_indicators.get("consistency_rating"),
        }
        clip_infos.append(clip_info)
        skill_progression.append(skill_num)

    # Skill progression analysis
    skill_changed = len(set(skill_progression)) > 1 if skill_progression else False
    skill_trend = "stable"
    if len(skill_progression) >= 2:
        if skill_progression[-1] > skill_progression[0]:
            skill_trend = "improving"
        elif skill_progression[-1] < skill_progression[0]:
            skill_trend = "declining"

    # Story arc variety
    arc_variety = len(set(story_arcs))
    arc_distribution = dict(Counter(story_arcs))

    # Shot variety
    shot_variety = len(set(shot_types_all))
    shot_distribution = dict(Counter(shot_types_all))

    return {
        "group_key": group_key,
        "clip_count": len(clips_data),
        "clips": clip_infos,
        "skill_progression": {
            "levels_seen": list(set(
                get_dominant_skill(d) for d in clips_data
            )),
            "progression_values": skill_progression,
            "skill_changed": skill_changed,
            "trend": skill_trend,
        },
        "story_arc_variety": {
            "unique_arcs": arc_variety,
            "distribution": arc_distribution,
        },
        "shot_variety": {
            "unique_dominant_shots": shot_variety,
            "distribution": shot_distribution,
        },
        "match_context": Counter(match_contexts).most_common(1)[0][0] if match_contexts else "unknown",
    }


def print_summary(groups):
    """Print a human-readable summary."""
    print("\n" + "=" * 60)
    print("MATCH CONTEXT ANALYSIS")
    print("=" * 60)
    print(f"\nTotal groups found: {len(groups)}")

    multi_clip = [g for g in groups if g["clip_count"] > 1]
    single_clip = [g for g in groups if g["clip_count"] == 1]
    print(f"  Multi-clip groups: {len(multi_clip)}")
    print(f"  Single-clip groups: {len(single_clip)}")

    total_clips = sum(g["clip_count"] for g in groups)
    print(f"  Total clips across groups: {total_clips}")

    if multi_clip:
        print(f"\n--- Multi-Clip Groups ---")
        for g in sorted(multi_clip, key=lambda x: -x["clip_count"]):
            print(f"\n  Group: {g['group_key']}")
            print(f"    Clips: {g['clip_count']}")
            print(f"    Skill trend: {g['skill_progression']['trend']}")
            print(f"    Skill changed: {g['skill_progression']['skill_changed']}")
            print(f"    Story arcs: {g['story_arc_variety']['distribution']}")
            print(f"    Shot types: {g['shot_variety']['distribution']}")
            print(f"    Match context: {g['match_context']}")

    # Aggregate stats
    all_arcs = Counter()
    all_shots = Counter()
    all_contexts = Counter()
    for g in groups:
        for arc, cnt in g["story_arc_variety"]["distribution"].items():
            all_arcs[arc] += cnt
        for shot, cnt in g["shot_variety"]["distribution"].items():
            all_shots[shot] += cnt
        all_contexts[g["match_context"]] += g["clip_count"]

    print(f"\n--- Aggregate Stats ---")
    print(f"\nStory Arc Distribution (all clips):")
    for arc, cnt in all_arcs.most_common():
        print(f"  {str(arc or 'unknown'):>25}: {cnt}")

    print(f"\nDominant Shot Type Distribution:")
    for shot, cnt in all_shots.most_common():
        print(f"  {str(shot or 'unknown'):>15}: {cnt}")

    print(f"\nMatch Context Distribution:")
    for ctx, cnt in all_contexts.most_common():
        print(f"  {ctx:>14}: {cnt}")

    # Skill progression summary
    improving = sum(1 for g in groups if g["skill_progression"]["trend"] == "improving")
    declining = sum(1 for g in groups if g["skill_progression"]["trend"] == "declining")
    stable = sum(1 for g in groups if g["skill_progression"]["trend"] == "stable")
    print(f"\nSkill Trends Across Groups:")
    print(f"  Improving: {improving}  |  Stable: {stable}  |  Declining: {declining}")

    print(f"\nOutput written to: output/discovery/match-context.json")
    print("=" * 60)


def main():
    print("Loading analysis files...")
    analyses = load_analysis_files()
    print(f"Found {len(analyses)} analysis files (>5KB)")

    if not analyses:
        print("No analysis files found. Nothing to do.")
        return

    # Group clips
    groups_map = defaultdict(list)
    for data in analyses:
        key = compute_group_key(data)
        groups_map[key].append(data)

    print(f"Identified {len(groups_map)} groups")

    # Analyze each group
    results = []
    for group_key, clips_data in groups_map.items():
        group_result = analyze_group(group_key, clips_data)
        results.append(group_result)

    # Sort by clip count descending
    results.sort(key=lambda g: -g["clip_count"])

    # Write output
    os.makedirs(DISCOVERY_DIR, exist_ok=True)
    output_path = os.path.join(DISCOVERY_DIR, "match-context.json")
    output = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "total_groups": len(results),
        "total_clips": sum(g["clip_count"] for g in results),
        "groups": results,
    }
    with open(output_path, "w") as f:
        json.dump(output, f, indent=2)

    print_summary(results)


if __name__ == "__main__":
    main()

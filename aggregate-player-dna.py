#!/usr/bin/env python3
"""
Pickle DaaS — Player DNA Aggregator
Aggregates multiple Gemini analysis results into a single Player DNA profile.

Usage:
  python aggregate-player-dna.py ./output/picklebill-batch-001/batch_summary_*.json
  python aggregate-player-dna.py ./output/picklebill-batch-001/batch_summary_1234567890.json --player PickleBill
"""

import json
import sys
import glob
from pathlib import Path
from datetime import datetime, timezone
from collections import Counter

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass


def load_batch(path_pattern: str) -> list:
    paths = glob.glob(path_pattern)
    if not paths:
        print(f"ERROR: No files found matching: {path_pattern}")
        sys.exit(1)
    all_results = []
    for p in paths:
        with open(p) as f:
            data = json.load(f)
        if isinstance(data, list):
            all_results.extend(data)
        else:
            all_results.append(data)
    print(f"Loaded {len(all_results)} clips from {len(paths)} file(s)")
    return all_results


def safe_score(result, *keys):
    try:
        obj = result
        for k in keys:
            obj = obj[k]
        return float(obj) if obj is not None else None
    except (KeyError, TypeError, ValueError):
        return None


def aggregate_dna(results: list, player_username: str = "PickleBill") -> dict:
    valid = [r for r in results if r and isinstance(r, dict)]
    total = len(valid)
    if not total:
        print("ERROR: No valid results to aggregate.")
        sys.exit(1)

    # ---- Scores ----
    quality_scores = [s for s in [safe_score(r, "clip_meta", "clip_quality_score") for r in valid] if s]
    viral_scores   = [s for s in [safe_score(r, "clip_meta", "viral_potential_score") for r in valid] if s]
    avg_quality = round(sum(quality_scores) / len(quality_scores), 2) if quality_scores else None
    avg_viral   = round(sum(viral_scores) / len(viral_scores), 2) if viral_scores else None

    # ---- Shot types ----
    all_shot_types = []
    for r in valid:
        sa = r.get("shot_analysis", {})
        dom = sa.get("dominant_shot_type")
        if dom:
            all_shot_types.append(dom)
        for shot in sa.get("shots", []):
            st = shot.get("shot_type")
            if st:
                all_shot_types.append(st)
    shot_counter = Counter(all_shot_types)
    dominant_shot = shot_counter.most_common(1)[0][0] if shot_counter else None

    # ---- Play style tags ----
    all_tags = []
    for r in valid:
        tags = r.get("skill_indicators", {}).get("play_style_tags", [])
        all_tags.extend(tags)
    tag_counter = Counter(all_tags)
    style_tags = [tag for tag, _ in tag_counter.most_common(10)]

    # ---- Skill aggregates ----
    skill_fields = [
        "court_coverage_rating", "kitchen_mastery_rating", "power_game_rating",
        "touch_and_feel_rating", "athleticism_rating", "creativity_rating",
        "court_iq_rating", "consistency_rating", "composure_under_pressure"
    ]
    skill_agg = {}
    for field in skill_fields:
        vals = [safe_score(r, "skill_indicators", field) for r in valid]
        vals = [v for v in vals if v is not None]
        if vals:
            skill_agg[field] = round(sum(vals) / len(vals), 2)

    # ---- Brands ----
    brand_counter = Counter()
    for r in valid:
        for b in r.get("brand_detection", {}).get("brands", []):
            name = b.get("brand_name")
            if name:
                brand_counter[name] += 1
    top_brands = [{"brand": b, "count": c} for b, c in brand_counter.most_common(10)]

    # ---- Badges ----
    badge_counter = Counter()
    for r in valid:
        for b in r.get("badge_intelligence", {}).get("predicted_badges", []):
            name = b.get("badge_name")
            if name:
                badge_counter[name] += 1
    badge_predictions = [{"badge_name": b, "count": c} for b, c in badge_counter.most_common(10)]

    # ---- Signature moves ----
    sig_moves = []
    for r in valid:
        move = r.get("skill_indicators", {}).get("signature_move_detected")
        if move and move not in sig_moves:
            sig_moves.append(move)

    # ---- Top + worst clips ----
    def clip_entry(r):
        return {
            "url": r.get("_source_url") or r.get("_highlight_meta", {}).get("file", ""),
            "name": r.get("_highlight_meta", {}).get("name", "Unknown"),
            "quality_score": safe_score(r, "clip_meta", "clip_quality_score"),
            "caption": r.get("commentary", {}).get("social_media_caption", ""),
            "ron_burgundy": r.get("commentary", {}).get("ron_burgundy_voice", ""),
        }

    sorted_clips = sorted(valid, key=lambda r: safe_score(r, "clip_meta", "clip_quality_score") or 0, reverse=True)
    top_clips    = [clip_entry(r) for r in sorted_clips[:5]]
    worst_clips  = [clip_entry(r) for r in sorted_clips[-3:]]

    # ---- Story arc distribution ----
    arc_counter = Counter()
    for r in valid:
        arc = r.get("storytelling", {}).get("story_arc")
        if arc:
            arc_counter[arc] += 1

    # ---- Commentary highlights ----
    best_clip = sorted_clips[0] if sorted_clips else {}
    commentary_highlights = {
        "top_ron_burgundy": best_clip.get("commentary", {}).get("ron_burgundy_voice", ""),
        "top_social_caption": best_clip.get("commentary", {}).get("social_media_caption", ""),
        "top_espn": best_clip.get("commentary", {}).get("neutral_announcer_espn", ""),
    }

    # ---- Coaching notes (aggregated improvement opportunities) ----
    coaching_raw = []
    for r in valid:
        for note in r.get("skill_indicators", {}).get("improvement_opportunities", []):
            if note:
                coaching_raw.append(note)
    coaching_counter = Counter(coaching_raw)
    coaching_notes = [note for note, _ in coaching_counter.most_common(5)]

    return {
        "player_username": player_username,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "clips_analyzed": total,
        "player_dna": {
            "avg_quality_score": avg_quality,
            "avg_viral_potential": avg_viral,
            "dominant_shot_type": dominant_shot,
            "play_style_tags": style_tags,
            "skill_aggregate": skill_agg,
            "signature_moves": sig_moves[:5],
            "story_arcs_distribution": dict(arc_counter),
        },
        "brand_registry": top_brands,
        "badge_predictions": badge_predictions,
        "top_clips": top_clips,
        "worst_clips": worst_clips,
        "commentary_highlights": commentary_highlights,
        "coaching_notes": coaching_notes,
    }


def main():
    if len(sys.argv) < 2:
        print("Usage: python aggregate-player-dna.py <batch_summary.json> [--player USERNAME]")
        sys.exit(1)

    path_pattern = sys.argv[1]
    player = "PickleBill"
    if "--player" in sys.argv:
        idx = sys.argv.index("--player")
        player = sys.argv[idx + 1]

    results = load_batch(path_pattern)
    dna = aggregate_dna(results, player)

    out_path = Path("./output") / f"{player.lower()}-dna-profile.json"
    out_path.parent.mkdir(exist_ok=True)
    with open(out_path, "w") as f:
        json.dump(dna, f, indent=2)

    print(f"\n{'='*60}")
    print(f"PLAYER DNA — {player}")
    print(f"{'='*60}")
    print(f"  Clips analyzed:    {dna['clips_analyzed']}")
    print(f"  Avg quality:       {dna['player_dna']['avg_quality_score']}")
    print(f"  Dominant shot:     {dna['player_dna']['dominant_shot_type']}")
    print(f"  Top style tags:    {', '.join(dna['player_dna']['play_style_tags'][:4])}")
    print(f"  Top badge:         {dna['badge_predictions'][0]['badge_name'] if dna['badge_predictions'] else 'n/a'}")
    print(f"\nSaved: {out_path}")


if __name__ == "__main__":
    main()

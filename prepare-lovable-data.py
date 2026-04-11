#!/usr/bin/env python3
"""
Pickle DaaS — Lovable Data Prep
Transforms batch_summary + player_dna into clean lovable-dashboard-data.json.

Usage:
  python prepare-lovable-data.py \
    --batch ./output/picklebill-batch-001/batch_summary_*.json \
    --dna ./output/picklebill-dna-profile.json \
    --player PickleBill
"""

import json
import sys
import glob
import argparse
from pathlib import Path
from datetime import datetime, timezone

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# PickleBill hardcoded profile data (from Courtana production)
PICKLEBILL_PROFILE = {
    "username": "PickleBill",
    "rank": 1,
    "xp": 283950,
    "level": 17,
    "rank_tier": "Gold III",
    "avatar_url": "https://cdn.courtana.com/files/production/u/a3c7e1d0-4b2f-4a8e-9f1c-6d5e8b3a2c1f/7d873c1f-ec81-487a-8fe7-97bdb94a6397.png",
    "badges_count": 82,
}


def load_json(path_pattern):
    paths = glob.glob(path_pattern)
    if not paths:
        return None
    results = []
    for p in paths:
        with open(p) as f:
            data = json.load(f)
        if isinstance(data, list):
            results.extend(data)
        else:
            results.append(data)
    return results


def build_highlight_entry(r):
    meta = r.get("_highlight_meta", {})
    cm = r.get("clip_meta", {})
    commentary = r.get("commentary", {})
    bd = r.get("brand_detection", {})
    badges = r.get("badge_intelligence", {})
    storytelling = r.get("storytelling", {})
    daas = r.get("daas_signals", {})

    return {
        "id": meta.get("id") or meta.get("random_id", ""),
        "name": meta.get("name", "Highlight"),
        "thumbnail_url": meta.get("thumbnail_file", ""),
        "video_url": r.get("_source_url") or meta.get("file", ""),
        "quality_score": cm.get("clip_quality_score"),
        "viral_score": cm.get("viral_potential_score"),
        "caption": commentary.get("social_media_caption", ""),
        "hashtags": commentary.get("social_media_hashtags", []),
        "brands": [b.get("brand_name") for b in bd.get("brands", []) if b.get("brand_name")],
        "story_arc": storytelling.get("story_arc"),
        "badges_predicted": [b.get("badge_name") for b in badges.get("predicted_badges", [])[:3]],
        "ron_burgundy_quote": commentary.get("ron_burgundy_voice", ""),
        "espn_commentary": commentary.get("neutral_announcer_espn", ""),
        "clip_summary": daas.get("clip_summary_one_sentence", ""),
        "highlight_category": daas.get("highlight_category"),
    }


def build_skill_radar(dna_data):
    skill = dna_data.get("player_dna", {}).get("skill_aggregate", {}) if dna_data else {}
    return {
        "court_coverage": skill.get("court_coverage_rating", 7.5),
        "kitchen_mastery": skill.get("kitchen_mastery_rating", 8.0),
        "power_game": skill.get("power_game_rating", 6.5),
        "touch_and_feel": skill.get("touch_and_feel_rating", 8.0),
        "athleticism": skill.get("athleticism_rating", 7.8),
        "creativity": skill.get("creativity_rating", 7.9),
        "court_iq": skill.get("court_iq_rating", 8.5),
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--batch",  required=True)
    parser.add_argument("--dna",    default=None)
    parser.add_argument("--player", default="PickleBill")
    args = parser.parse_args()

    batch = load_json(args.batch) or []
    dna_list = load_json(args.dna) if args.dna else None
    dna_data = dna_list[0] if dna_list else None

    # Sort by quality
    sorted_batch = sorted(batch, key=lambda r: r.get("clip_meta", {}).get("clip_quality_score") or 0, reverse=True)
    highlights = [build_highlight_entry(r) for r in sorted_batch]

    # Analytics
    quality_scores = [r.get("clip_meta", {}).get("clip_quality_score") for r in batch if r.get("clip_meta", {}).get("clip_quality_score")]
    viral_scores   = [r.get("clip_meta", {}).get("viral_potential_score") for r in batch if r.get("clip_meta", {}).get("viral_potential_score")]

    from collections import Counter
    arc_counter = Counter(r.get("storytelling", {}).get("story_arc") for r in batch if r.get("storytelling", {}).get("story_arc"))
    brand_counter = Counter()
    for r in batch:
        for b in r.get("brand_detection", {}).get("brands", []):
            if b.get("brand_name"):
                brand_counter[b["brand_name"]] += 1

    shot_counter = Counter()
    for r in batch:
        dom = r.get("shot_analysis", {}).get("dominant_shot_type")
        if dom:
            shot_counter[dom] += 1

    dna_tags = (dna_data or {}).get("player_dna", {}).get("play_style_tags", [])
    dominant_style = dna_tags[0] if dna_tags else "kitchen specialist"

    payload = {
        "player": PICKLEBILL_PROFILE if args.player == "PickleBill" else {"username": args.player},
        "highlights": highlights,
        "analytics": {
            "avg_quality_score": round(sum(quality_scores) / len(quality_scores), 2) if quality_scores else None,
            "avg_viral_score": round(sum(viral_scores) / len(viral_scores), 2) if viral_scores else None,
            "top_shot_type": shot_counter.most_common(1)[0][0] if shot_counter else "dink",
            "dominant_play_style": dominant_style,
            "top_brands": [{"brand": b, "count": c} for b, c in brand_counter.most_common(8)],
            "skill_radar": build_skill_radar(dna_data),
            "story_arc_breakdown": dict(arc_counter),
            "viral_potential_distribution": [v for v in viral_scores[:20]],
            "total_clips_analyzed": len(batch),
        },
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }

    out_path = Path("./output/lovable-dashboard-data.json")
    out_path.parent.mkdir(exist_ok=True)
    with open(out_path, "w") as f:
        json.dump(payload, f, indent=2)

    print(f"\n{'='*60}")
    print(f"LOVABLE DATA PREP — {args.player}")
    print(f"{'='*60}")
    print(f"  Highlights:    {len(highlights)}")
    print(f"  Avg quality:   {payload['analytics']['avg_quality_score']}")
    print(f"  Top brand:     {brand_counter.most_common(1)[0][0] if brand_counter else 'n/a'}")
    print(f"\nSaved: {out_path}")


if __name__ == "__main__":
    main()

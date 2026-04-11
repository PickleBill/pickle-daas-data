#!/usr/bin/env python3
"""
Pickle DaaS — Prompt Quality Evaluator
Reads a batch_summary JSON → scores each field's fill rate → outputs quality report.

Usage:
  python evaluate-prompt-quality.py ./output/picklebill-batch-001/batch_summary_*.json
"""

import json
import sys
import glob
from pathlib import Path
from datetime import datetime, timezone

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# Fields to evaluate with their dot-path and human label
FIELDS_TO_CHECK = [
    # clip_meta
    ("clip_meta.clip_quality_score",       "Quality Score"),
    ("clip_meta.viral_potential_score",    "Viral Potential Score"),
    ("clip_meta.watchability_score",       "Watchability Score"),
    ("clip_meta.cinematic_score",          "Cinematic Score"),
    ("clip_meta.duration_seconds",         "Duration"),
    # players
    ("players_detected",                   "Players Detected (array)"),
    # shot_analysis
    ("shot_analysis.dominant_shot_type",   "Dominant Shot Type"),
    ("shot_analysis.total_shots_estimated","Total Shots Estimated"),
    ("shot_analysis.rally_length_estimated","Rally Length"),
    ("shot_analysis.shots",                "Shots Array"),
    # skill_indicators
    ("skill_indicators.play_style_tags",   "Play Style Tags"),
    ("skill_indicators.court_coverage_rating", "Court Coverage Rating"),
    ("skill_indicators.kitchen_mastery_rating","Kitchen Mastery Rating"),
    ("skill_indicators.signature_move_detected","Signature Move"),
    ("skill_indicators.improvement_opportunities","Improvement Opportunities"),
    # brand_detection
    ("brand_detection.brands",             "Brands Array"),
    ("brand_detection.total_brands_detected","Brands Count"),
    ("brand_detection.sponsorship_whitespace","Sponsorship Whitespace"),
    # storytelling
    ("storytelling.story_arc",             "Story Arc"),
    ("storytelling.emotional_tone",        "Emotional Tone"),
    ("storytelling.narrative_arc_summary", "Narrative Summary"),
    # badge_intelligence
    ("badge_intelligence.predicted_badges","Predicted Badges"),
    ("badge_intelligence.highlight_reel_worthy","Highlight Reel Worthy"),
    # commentary
    ("commentary.neutral_announcer_espn",  "ESPN Commentary"),
    ("commentary.social_media_caption",    "Social Caption"),
    ("commentary.social_media_hashtags",   "Hashtags"),
    ("commentary.ron_burgundy_voice",      "Ron Burgundy"),
    ("commentary.announcement_text_for_tts","TTS Text"),
    # daas_signals
    ("daas_signals.clip_summary_one_sentence","Clip Summary"),
    ("daas_signals.search_tags",           "Search Tags"),
    ("daas_signals.data_richness_score",   "Data Richness Score"),
    ("daas_signals.estimated_player_rating_dupr","DUPR Estimate"),
]


def get_nested(obj, dotpath):
    parts = dotpath.split(".")
    cur = obj
    for p in parts:
        if not isinstance(cur, dict):
            return None
        cur = cur.get(p)
    return cur


def is_filled(val):
    if val is None:
        return False
    if isinstance(val, (list, dict)):
        return len(val) > 0
    if isinstance(val, str):
        return val.strip() not in ("", "null", "unknown", "None")
    if isinstance(val, (int, float)):
        return True
    return bool(val)


def evaluate(results):
    total = len(results)
    if not total:
        return {}

    scores = {}
    for dotpath, label in FIELDS_TO_CHECK:
        filled = sum(1 for r in results if is_filled(get_nested(r, dotpath)))
        pct = round(100 * filled / total)
        scores[dotpath] = {"label": label, "filled": filled, "total": total, "pct": pct}
    return scores


def write_report(scores, total_clips, out_path):
    date_str = datetime.now(timezone.utc).strftime("%B %d, %Y")
    sorted_scores = sorted(scores.values(), key=lambda x: x["pct"])

    weak = [s for s in sorted_scores if s["pct"] < 60]
    strong = [s for s in sorted_scores if s["pct"] >= 80]

    lines = [
        "# Prompt Quality Report",
        f"**Generated:** {date_str}  |  **Clips evaluated:** {total_clips}",
        "",
        "---",
        "",
        "## All Fields — Fill Rate",
        "",
        "| Field | Fill Rate | Filled / Total | Status |",
        "|-------|-----------|----------------|--------|",
    ]
    for s in sorted(scores.values(), key=lambda x: x["pct"], reverse=True):
        status = "✅" if s["pct"] >= 80 else ("⚠️" if s["pct"] >= 50 else "❌")
        lines.append(f"| {s['label']} | {s['pct']}% | {s['filled']}/{s['total']} | {status} |")

    lines += [
        "",
        "---",
        "",
        "## Fields Needing Improvement (< 60% fill rate)",
        "",
    ]
    if weak:
        for s in weak:
            lines.append(f"- ❌ **{s['label']}** — {s['pct']}% fill rate ({s['filled']}/{s['total']} clips)")
        lines += [
            "",
            "### Suggested Prompt Improvements",
            "",
        ]
        for s in weak[:5]:
            lines.append(f"- Add stronger instruction for `{s['label']}` — make it required with explicit example values")
    else:
        lines.append("_All fields above 60% — excellent prompt coverage!_")

    lines += [
        "",
        "---",
        "",
        "## Strongest Fields (≥ 80% fill rate)",
        "",
    ]
    for s in strong:
        lines.append(f"- ✅ **{s['label']}** — {s['pct']}%")

    lines += [
        "",
        "---",
        "",
        "## Prompt Version Recommendation",
        "",
        f"- Current coverage: **{sum(s['pct'] for s in scores.values()) // len(scores)}% avg fill rate**",
        f"- Fields below 60%: **{len(weak)}**",
        "",
        "**Action:** Update weak fields in `ANALYSIS_PROMPT`, bump to next version, re-run on same 5 clips, diff outputs.",
        "",
        "_Report generated by evaluate-prompt-quality.py — Pickle DaaS_",
    ]

    out_path.write_text("\n".join(lines))


def main():
    if len(sys.argv) < 2:
        print("Usage: python evaluate-prompt-quality.py <batch_summary.json>")
        sys.exit(1)

    paths = glob.glob(sys.argv[1])
    if not paths:
        print(f"ERROR: No files found: {sys.argv[1]}")
        sys.exit(1)

    results = []
    for p in paths:
        with open(p) as f:
            data = json.load(f)
        if isinstance(data, list):
            results.extend(data)
        else:
            results.append(data)

    print(f"Evaluating {len(results)} clips...")
    scores = evaluate(results)

    out_path = Path("./output/prompt-quality-report.md")
    out_path.parent.mkdir(exist_ok=True)
    write_report(scores, len(results), out_path)

    avg_fill = sum(s["pct"] for s in scores.values()) // len(scores)
    weak = [s for s in scores.values() if s["pct"] < 60]

    print(f"\nAvg fill rate: {avg_fill}%")
    print(f"Weak fields (<60%): {len(weak)}")
    if weak:
        for s in sorted(weak, key=lambda x: x["pct"])[:5]:
            print(f"  ❌ {s['label']:40s} {s['pct']}%")
    print(f"\nReport: {out_path}")


if __name__ == "__main__":
    main()

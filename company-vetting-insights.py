#!/usr/bin/env python3
"""
=============================================================================
PICKLE DaaS — Company Vetting Insights Generator
=============================================================================
Takes a batch_summary JSON from the Gemini analyzer and outputs B2B intelligence
formatted for three different pitch audiences: sponsors, venues, and investors.

Usage:
  python company-vetting-insights.py ./output/picklebill-batch-001/batch_summary_*.json
  python company-vetting-insights.py --player PickleBill ./output/picklebill-batch-001/batch_summary_*.json
  python company-vetting-insights.py --format investor ./output/batch_summary.json

Output:
  ./output/b2b-vetting-insights.json
  ./output/b2b-vetting-report.md
=============================================================================
"""

import json
import sys
import argparse
from pathlib import Path
from datetime import datetime
from collections import Counter, defaultdict


# ---------------------------------------------------------------------------
# SPONSOR INTELLIGENCE
# ---------------------------------------------------------------------------

def generate_sponsor_pitch_data(batch: list) -> dict:
    """What brands want to know before sponsoring a player or venue."""
    brand_counter = Counter()
    brand_categories = defaultdict(set)
    brand_visibility = defaultdict(list)
    whitespace_counter = Counter()
    total_clips = len(batch)

    for clip in batch:
        bd = clip.get("brand_detection", {})
        for brand in bd.get("brands", []):
            name = brand.get("brand_name", "Unknown")
            cat = brand.get("category", "other")
            vis_secs = brand.get("estimated_visible_seconds") or 0
            brand_counter[name] += 1
            brand_categories[name].add(cat)
            brand_visibility[name].append(vis_secs)

        for ws in bd.get("sponsorship_whitespace", []):
            if ws:
                whitespace_counter[ws] += 1

    dominant_brands = []
    for brand, count in brand_counter.most_common(10):
        avg_vis = sum(brand_visibility[brand]) / len(brand_visibility[brand]) if brand_visibility[brand] else 0
        dominant_brands.append({
            "brand": brand,
            "clips_appeared_in": count,
            "pct_of_clips": round(count / total_clips * 100, 1) if total_clips else 0,
            "avg_visible_seconds": round(avg_vis, 1),
            "categories": list(brand_categories[brand])
        })

    whitespace = [
        {"brand": b, "mentioned_in_clips": c, "opportunity_strength": "high" if c >= 3 else "medium" if c >= 2 else "low"}
        for b, c in whitespace_counter.most_common(10)
    ]

    # Estimate impressions (clips × avg views — placeholder multiplier)
    avg_views_per_clip = 350  # Conservative Courtana average
    total_brand_impressions = sum(brand_counter.values()) * avg_views_per_clip

    # Skill level distribution for demographic signals
    skill_counter = Counter()
    for clip in batch:
        for player in clip.get("players_detected", []):
            lvl = player.get("estimated_skill_level")
            if lvl:
                skill_counter[lvl] += 1

    return {
        "audience": "sponsor",
        "summary": f"Analysis of {total_clips} highlight clips. {len(brand_counter)} distinct brands detected.",
        "dominant_brands_already_present": dominant_brands[:8],
        "whitespace_opportunities": whitespace[:6],
        "estimated_impressions_per_clip": avg_views_per_clip,
        "total_brand_exposure_impressions": total_brand_impressions,
        "avg_brand_visibility_seconds": round(
            sum(sum(v) for v in brand_visibility.values()) /
            max(sum(len(v) for v in brand_visibility.values()), 1), 1
        ),
        "player_skill_demographic": dict(skill_counter.most_common()),
        "pitch_takeaways": [
            f"{dominant_brands[0]['brand']} leads with {dominant_brands[0]['clips_appeared_in']} clip appearances — already the dominant brand." if dominant_brands else "No dominant brand detected yet.",
            f"Top whitespace opportunity: {whitespace[0]['brand']} — high-value brand not yet present." if whitespace else "No clear whitespace brands identified.",
            f"Estimated {total_brand_impressions:,} total brand impressions across this clip set.",
            "All clips are shareable highlights with 3-60 second runtime — ideal for sponsor overlay."
        ]
    }


# ---------------------------------------------------------------------------
# VENUE INTELLIGENCE
# ---------------------------------------------------------------------------

def generate_venue_pitch_data(batch: list) -> dict:
    """What venue owners and operators want to know."""
    total_clips = len(batch)
    quality_scores = []
    viral_scores = []
    shot_type_counter = Counter()
    skill_counter = Counter()
    story_arcs = Counter()
    rally_lengths = []
    coaching_flags = 0

    for clip in batch:
        meta = clip.get("clip_meta", {})
        if meta.get("clip_quality_score"):
            quality_scores.append(meta["clip_quality_score"])
        if meta.get("viral_potential_score"):
            viral_scores.append(meta["viral_potential_score"])

        shot_data = clip.get("shot_analysis", {})
        for shot in shot_data.get("shots", []):
            st = shot.get("shot_type")
            if st:
                shot_type_counter[st] += 1
        if shot_data.get("rally_length_estimated"):
            rally_lengths.append(shot_data["rally_length_estimated"])

        for player in clip.get("players_detected", []):
            lvl = player.get("estimated_skill_level")
            if lvl:
                skill_counter[lvl] += 1

        arc = clip.get("storytelling", {}).get("story_arc")
        if arc:
            story_arcs[arc] += 1

        # Teaching moment = coaching opportunity
        category = clip.get("daas_signals", {}).get("highlight_category")
        if category == "teaching_moment":
            coaching_flags += 1

    avg_quality = round(sum(quality_scores) / len(quality_scores), 2) if quality_scores else None
    avg_viral = round(sum(viral_scores) / len(viral_scores), 2) if viral_scores else None
    avg_rally = round(sum(rally_lengths) / len(rally_lengths), 1) if rally_lengths else None

    most_exciting_shots = [
        {"shot_type": st, "frequency": count}
        for st, count in shot_type_counter.most_common(5)
    ]

    coaching_score = round(coaching_flags / total_clips * 10, 1) if total_clips else 0

    return {
        "audience": "venue",
        "summary": f"{total_clips} clips analyzed from this venue/player. Avg clip quality: {avg_quality}/10.",
        "avg_clip_quality_score": avg_quality,
        "avg_viral_potential_score": avg_viral,
        "avg_rally_length_shots": avg_rally,
        "skill_level_distribution": dict(skill_counter.most_common()),
        "most_exciting_shot_types": most_exciting_shots,
        "story_arc_distribution": dict(story_arcs.most_common()),
        "coaching_opportunity_score": coaching_score,
        "coaching_clips_count": coaching_flags,
        "pitch_takeaways": [
            f"Average clip quality score: {avg_quality}/10 — {'above average for recreational pickleball' if avg_quality and avg_quality >= 7 else 'standard recreational play quality'}.",
            f"Average rally length: {avg_rally} shots — {'long, competitive rallies make great content' if avg_rally and avg_rally >= 8 else 'shorter points typical of competitive play'}." if avg_rally else "Rally length data not available.",
            f"{coaching_flags} clips flagged as coaching teaching moments — potential for premium coaching analysis tier.",
            f"Top play types: {', '.join(s['shot_type'] for s in most_exciting_shots[:3])} — these drive the most social engagement."
        ]
    }


# ---------------------------------------------------------------------------
# INVESTOR INTELLIGENCE
# ---------------------------------------------------------------------------

def generate_investor_pitch_data(batch: list, corpus_size: int = 4097) -> dict:
    """What investors want to see — data richness, scalability signals."""
    total_clips = len(batch)
    richness_scores = []
    total_brands = set()
    total_players_estimated = 0
    fields_filled = []
    badge_counter = Counter()

    KEY_FIELDS = [
        ("clip_meta", "clip_quality_score"),
        ("clip_meta", "viral_potential_score"),
        ("brand_detection", "brands"),
        ("skill_indicators", "play_style_tags"),
        ("commentary", "ron_burgundy_voice"),
        ("commentary", "social_media_caption"),
        ("storytelling", "story_arc"),
        ("badge_intelligence", "predicted_badges"),
        ("daas_signals", "search_tags"),
        ("daas_signals", "estimated_player_rating_dupr"),
    ]

    for clip in batch:
        richness = clip.get("daas_signals", {}).get("data_richness_score", 0)
        if richness:
            richness_scores.append(richness)

        for brand in clip.get("brand_detection", {}).get("brands", []):
            total_brands.add(brand.get("brand_name", ""))

        total_players_estimated += len(clip.get("players_detected", []))

        clip_fill = sum(
            1 for section, field in KEY_FIELDS
            if clip.get(section, {}).get(field) not in (None, [], {}, "")
        )
        fields_filled.append(clip_fill)

        for badge in clip.get("badge_intelligence", {}).get("predicted_badges", []):
            bn = badge.get("badge_name")
            if bn:
                badge_counter[bn] += 1

    avg_richness = round(sum(richness_scores) / len(richness_scores), 2) if richness_scores else None
    avg_insights = round(sum(fields_filled) / len(fields_filled), 1) if fields_filled else None
    total_brands.discard("")

    # Scale projection
    scale_multiplier = corpus_size / max(total_clips, 1)

    return {
        "audience": "investor",
        "corpus_size_current": total_clips,
        "corpus_size_total_platform": corpus_size,
        "scale_multiplier": round(scale_multiplier, 0),
        "data_richness_avg_score": avg_richness,
        "avg_insights_per_clip": avg_insights,
        "unique_brands_detected": len(total_brands),
        "unique_brands_list": sorted(total_brands),
        "estimated_players_in_corpus": total_players_estimated,
        "top_badge_patterns": [{"badge": b, "frequency": c} for b, c in badge_counter.most_common(5)],
        "projected_at_full_corpus": {
            "clips": corpus_size,
            "brand_detections_estimated": int(len(total_brands) * scale_multiplier * 0.7),
            "player_profiles_estimated": int(total_players_estimated * scale_multiplier * 0.4),
            "insights_data_points_estimated": int(avg_insights * corpus_size) if avg_insights else None,
        },
        "value_per_clip_estimate": (
            "Each clip yields ~10 structured data signals: quality score, viral score, brand detections, "
            "skill ratings, badge predictions, commentary variations, search tags, story arc, DUPR estimate, "
            "and coaching notes. At scale, this is the world's largest sports intelligence corpus for pickleball."
        ),
        "moat_signals": [
            f"Only platform capturing brand detection data at point of play (not self-reported)",
            f"Behavioral skill ratings derived from AI video analysis — not self-assessed",
            f"Multi-commentary format (ESPN + hype + social + TTS) unlocks monetization across media types",
            f"{corpus_size:,} highlight corpus growing daily — compounding data advantage",
            f"Badge/achievement system creates player engagement loop that generates more content",
        ],
        "pitch_takeaways": [
            f"Each analyzed clip generates ~{avg_insights} structured data fields — richer than any manual tagging system.",
            f"{len(total_brands)} unique brands already detected across just {total_clips} clips — sponsor data moat forming.",
            f"At {corpus_size:,} clips with {round(scale_multiplier)}x scale, projected {int(avg_insights * corpus_size) if avg_insights else 'N/A'} total data points.",
            "Real-time brand exposure data from every rally = new category of sports media intelligence.",
        ]
    }


# ---------------------------------------------------------------------------
# MARKDOWN REPORT GENERATOR
# ---------------------------------------------------------------------------

def generate_markdown_report(sponsor: dict, venue: dict, investor: dict, clips_analyzed: int) -> str:
    lines = [
        "# Pickle DaaS — B2B Vetting Intelligence Report",
        f"**Generated:** {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}  ",
        f"**Clips Analyzed:** {clips_analyzed}  ",
        f"**Platform:** Courtana (courtana.com)  ",
        "",
        "---",
        "",
        "## 🏷️ Sponsor Intelligence",
        "",
        f"> {sponsor['summary']}",
        "",
        "### Top Brands Already Present",
        "| Brand | Clips | % Coverage | Avg Visible Seconds | Categories |",
        "|-------|-------|-----------|---------------------|------------|",
    ]
    for b in sponsor.get("dominant_brands_already_present", [])[:6]:
        cats = ", ".join(b.get("categories", []))
        lines.append(f"| {b['brand']} | {b['clips_appeared_in']} | {b['pct_of_clips']}% | {b['avg_visible_seconds']}s | {cats} |")

    lines += [
        "",
        "### Sponsorship Whitespace (Opportunity Brands)",
        "| Brand | Clip Mentions | Opportunity Strength |",
        "|-------|--------------|---------------------|",
    ]
    for ws in sponsor.get("whitespace_opportunities", [])[:5]:
        lines.append(f"| {ws['brand']} | {ws['mentioned_in_clips']} | {ws['opportunity_strength'].upper()} |")

    lines += [
        "",
        "### Sponsor Pitch Takeaways",
    ]
    for t in sponsor.get("pitch_takeaways", []):
        lines.append(f"- {t}")

    lines += [
        "",
        "---",
        "",
        "## 🏟️ Venue Intelligence",
        "",
        f"> {venue['summary']}",
        "",
        "| Metric | Value |",
        "|--------|-------|",
        f"| Avg Clip Quality Score | {venue.get('avg_clip_quality_score', 'N/A')}/10 |",
        f"| Avg Viral Potential | {venue.get('avg_viral_potential_score', 'N/A')}/10 |",
        f"| Avg Rally Length | {venue.get('avg_rally_length_shots', 'N/A')} shots |",
        f"| Coaching Opportunity Score | {venue.get('coaching_opportunity_score', 'N/A')}/10 |",
        f"| Teaching Moment Clips | {venue.get('coaching_clips_count', 0)} |",
        "",
        "### Most Exciting Shot Types",
        "| Shot Type | Frequency |",
        "|-----------|-----------|",
    ]
    for s in venue.get("most_exciting_shot_types", []):
        lines.append(f"| {s['shot_type']} | {s['frequency']} |")

    lines += [
        "",
        "### Venue Pitch Takeaways",
    ]
    for t in venue.get("pitch_takeaways", []):
        lines.append(f"- {t}")

    lines += [
        "",
        "---",
        "",
        "## 📈 Investor Intelligence",
        "",
        f"> {investor.get('value_per_clip_estimate', '')}",
        "",
        "### Data Richness Metrics",
        "| Metric | This Batch | At Full Corpus ({:,} clips) |".format(investor.get("corpus_size_total_platform", 0)),
        "|--------|-----------|--------------------------|",
        f"| Clips Analyzed | {investor.get('corpus_size_current', 0)} | {investor.get('corpus_size_total_platform', 0):,} |",
        f"| Avg Data Fields per Clip | {investor.get('avg_insights_per_clip', 'N/A')} | {investor.get('avg_insights_per_clip', 0)} |",
        f"| Unique Brands Detected | {investor.get('unique_brands_detected', 0)} | ~{investor.get('projected_at_full_corpus', {}).get('brand_detections_estimated', 'N/A'):,} |",
        f"| Data Richness Score | {investor.get('data_richness_avg_score', 'N/A')}/10 | — |",
        f"| Total Data Points Est. | — | {investor.get('projected_at_full_corpus', {}).get('insights_data_points_estimated', 'N/A'):,} |",
        "",
        "### Data Moat Signals",
    ]
    for m in investor.get("moat_signals", []):
        lines.append(f"- {m}")

    lines += [
        "",
        "### Investor Pitch Takeaways",
    ]
    for t in investor.get("pitch_takeaways", []):
        lines.append(f"- {t}")

    lines += [
        "",
        "---",
        "",
        "_Report generated by Pickle DaaS — courtana.com_",
    ]

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# MAIN
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Pickle DaaS — B2B Vetting Insights Generator")
    parser.add_argument("batch_file", help="Path to batch_summary JSON file from the analyzer")
    parser.add_argument("--player", default="PickleBill", help="Player username for labeling (default: PickleBill)")
    parser.add_argument("--corpus-size", type=int, default=4097, help="Total platform corpus size for investor projections (default: 4097)")
    parser.add_argument("--output-dir", default="./output", help="Where to save output files (default: ./output)")
    parser.add_argument("--format", choices=["all", "sponsor", "venue", "investor"], default="all", help="Which audience to generate for (default: all)")
    args = parser.parse_args()

    # Load batch
    batch_path = Path(args.batch_file)
    if not batch_path.exists():
        print(f"ERROR: File not found: {batch_path}")
        sys.exit(1)

    print(f"Loading batch: {batch_path}")
    with open(batch_path) as f:
        batch = json.load(f)

    if not isinstance(batch, list):
        # Handle single-clip analysis files
        batch = [batch]

    print(f"Loaded {len(batch)} clips")

    # Generate insights
    print("Generating sponsor pitch data...")
    sponsor = generate_sponsor_pitch_data(batch)

    print("Generating venue pitch data...")
    venue = generate_venue_pitch_data(batch)

    print("Generating investor pitch data...")
    investor = generate_investor_pitch_data(batch, corpus_size=args.corpus_size)

    # Build output
    output = {
        "player": args.player,
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "clips_analyzed": len(batch),
        "sponsor": sponsor,
        "venue": venue,
        "investor": investor,
    }

    # Save JSON
    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    json_path = out_dir / "b2b-vetting-insights.json"
    with open(json_path, "w") as f:
        json.dump(output, f, indent=2)
    print(f"Saved: {json_path}")

    # Save Markdown report
    md_report = generate_markdown_report(sponsor, venue, investor, len(batch))
    md_path = out_dir / "b2b-vetting-report.md"
    with open(md_path, "w") as f:
        f.write(md_report)
    print(f"Saved: {md_path}")

    # Print summary
    print(f"\n{'='*60}")
    print(f"B2B VETTING INSIGHTS COMPLETE")
    print(f"  Clips analyzed:      {len(batch)}")
    print(f"  Brands detected:     {investor.get('unique_brands_detected', 0)}")
    print(f"  Avg data richness:   {investor.get('data_richness_avg_score', 'N/A')}/10")
    print(f"  Sponsor whitespace:  {len(sponsor.get('whitespace_opportunities', []))} opportunities")
    print(f"  JSON: {json_path}")
    print(f"  Report: {md_path}")


if __name__ == "__main__":
    main()

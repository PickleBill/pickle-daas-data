#!/usr/bin/env python3
"""
Pickle DaaS — Brand Intelligence Report
==========================================
Generates a polished, sellable per-brand intelligence report.
Reads all raw analysis JSONs and creates an interactive HTML dashboard.

USAGE:
  python generate-brand-report.py                # All brands
  python generate-brand-report.py --brand JOOLA  # Specific brand
"""

import json
import glob
import os
import argparse
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path

CORPUS_DIR = "output"


def load_analyses():
    files = glob.glob(f"{CORPUS_DIR}/**/analysis_*.json", recursive=True)
    analyses = []
    for f in files:
        try:
            if os.path.getsize(f) < 5000:
                continue
            with open(f) as fh:
                data = json.load(fh)
            if "brand_detection" in data:
                analyses.append(data)
        except (json.JSONDecodeError, KeyError):
            continue
    return analyses


def build_brand_intel(analyses, target_brand=None):
    """Build comprehensive brand intelligence from all analyses."""
    brand_data = defaultdict(lambda: {
        "appearances": 0,
        "clips": [],
        "categories": Counter(),
        "confidence_levels": Counter(),
        "visibility_quality": Counter(),
        "visible_seconds": 0,
        "co_occurring_brands": Counter(),
        "skill_ratings": defaultdict(list),
        "viral_scores": [],
        "quality_scores": [],
        "story_arcs": Counter(),
        "shot_types": Counter(),
        "player_sides": Counter(),
    })

    for a in analyses:
        brands_in_clip = []
        for b in a.get("brand_detection", {}).get("brands", []):
            name = b.get("brand_name", "").upper().strip()
            if not name:
                continue
            brands_in_clip.append(name)

            bd = brand_data[name]
            bd["appearances"] += 1
            bd["categories"][b.get("category", "unknown")] += 1
            bd["confidence_levels"][b.get("confidence", "unknown")] += 1
            bd["visibility_quality"][b.get("visibility_quality", "unknown")] += 1
            bd["player_sides"][b.get("player_side", "unknown")] += 1
            vs = b.get("estimated_visible_seconds")
            if isinstance(vs, (int, float)):
                bd["visible_seconds"] += vs

            # Add clip-level data
            cm = a.get("clip_meta", {})
            viral = cm.get("viral_potential_score")
            quality = cm.get("clip_quality_score")
            if viral:
                bd["viral_scores"].append(viral)
            if quality:
                bd["quality_scores"].append(quality)

            arc = a.get("storytelling", {}).get("story_arc")
            if arc:
                bd["story_arcs"][arc] += 1

            # Skills of players using this brand
            sk = a.get("skill_indicators", {})
            for key in ["court_coverage_rating", "kitchen_mastery_rating", "power_game_rating",
                        "touch_and_feel_rating", "athleticism_rating", "creativity_rating",
                        "court_iq_rating", "consistency_rating"]:
                val = sk.get(key)
                if isinstance(val, (int, float)) and val > 0:
                    bd["skill_ratings"][key].append(val)

            # Dominant shots
            dom = a.get("shot_analysis", {}).get("dominant_shot_type")
            if dom:
                bd["shot_types"][dom] += 1

            # Track clip info
            source = a.get("_source_url", "")
            caption = a.get("commentary", {}).get("social_media_caption", "")
            ron = a.get("commentary", {}).get("ron_burgundy_voice", "")
            bd["clips"].append({
                "url": source,
                "viral": viral or 0,
                "quality": quality or 0,
                "arc": arc or "unknown",
                "caption": caption[:100],
                "ron": ron[:120],
            })

        # Co-occurrence
        unique_brands = list(set(brands_in_clip))
        for b in unique_brands:
            for other in unique_brands:
                if other != b:
                    brand_data[b]["co_occurring_brands"][other] += 1

    # Filter to target brand if specified
    if target_brand:
        target = target_brand.upper()
        if target in brand_data:
            return {target: brand_data[target]}
        else:
            print(f"Brand '{target_brand}' not found. Available: {list(brand_data.keys())}")
            return brand_data

    return brand_data


def generate_report(brand_data, output_path):
    """Generate interactive HTML brand intelligence report."""
    # Sort brands by appearances
    sorted_brands = sorted(brand_data.items(), key=lambda x: x[1]["appearances"], reverse=True)

    brand_cards = ""
    colors = ["#00E676", "#4FC3F7", "#FF6B6B", "#FFD54F", "#BA68C8", "#FF8A65", "#81C784", "#64B5F6"]

    for idx, (brand, data) in enumerate(sorted_brands[:12]):
        color = colors[idx % len(colors)]
        avg_viral = round(sum(data["viral_scores"]) / max(len(data["viral_scores"]), 1), 1)
        avg_quality = round(sum(data["quality_scores"]) / max(len(data["quality_scores"]), 1), 1)
        unique_clips = len(set(c["url"] for c in data["clips"] if c["url"]))
        top_category = data["categories"].most_common(1)[0][0] if data["categories"] else "unknown"
        top_cobrands = data["co_occurring_brands"].most_common(3)

        # Skill radar data
        skill_vals = {}
        for key, vals in data["skill_ratings"].items():
            clean = key.replace("_rating", "").replace("_", " ").title()
            skill_vals[clean] = round(sum(vals) / len(vals), 1)

        # Top clips by viral
        top_clips_html = ""
        best_clips = sorted(data["clips"], key=lambda c: c["viral"], reverse=True)[:3]
        for c in best_clips:
            if c["caption"]:
                top_clips_html += f'<div style="background:#0a0a1a;padding:8px 12px;border-radius:8px;margin:4px 0;font-size:12px"><span style="color:{color};font-weight:700">V:{c["viral"]}</span> {c["caption"]}</div>'

        # Co-brand badges
        cobrand_html = " ".join(f'<span style="background:{color}22;color:{color};padding:2px 8px;border-radius:10px;font-size:11px;margin:2px">{b[0]}</span>' for b in top_cobrands)

        # Skill bars
        skill_bars = ""
        for skill, val in sorted(skill_vals.items(), key=lambda x: x[1], reverse=True)[:6]:
            w = val * 10
            skill_bars += f'<div style="display:flex;align-items:center;gap:6px;margin:3px 0"><span style="width:100px;font-size:10px;color:#888">{skill}</span><div style="background:#222;height:5px;width:80px;border-radius:3px"><div style="background:{color};height:5px;width:{w}%;border-radius:3px"></div></div><span style="font-size:10px;color:{color}">{val}</span></div>'

        brand_cards += f"""
        <div style="background:#1a1a2e;border-radius:16px;padding:24px;border-top:3px solid {color}">
            <div style="display:flex;justify-content:space-between;align-items:flex-start;margin-bottom:16px">
                <div>
                    <div style="font-size:24px;font-weight:800;color:#fff">{brand}</div>
                    <div style="font-size:12px;color:#888;margin-top:2px">Primary: {top_category} | {data['appearances']} appearances in {unique_clips} clips</div>
                </div>
                <div style="text-align:right">
                    <div style="font-size:28px;font-weight:800;color:{color}">{avg_viral}</div>
                    <div style="font-size:10px;color:#888">Avg Viral Score</div>
                </div>
            </div>

            <div style="display:grid;grid-template-columns:1fr 1fr;gap:16px;margin-bottom:16px">
                <div>
                    <div style="font-size:11px;color:#888;text-transform:uppercase;letter-spacing:1px;margin-bottom:8px">Player Skill Profile</div>
                    {skill_bars}
                </div>
                <div>
                    <div style="font-size:11px;color:#888;text-transform:uppercase;letter-spacing:1px;margin-bottom:8px">Key Metrics</div>
                    <div style="display:grid;grid-template-columns:1fr 1fr;gap:8px">
                        <div style="background:#0a0a1a;padding:8px;border-radius:8px;text-align:center">
                            <div style="font-size:18px;font-weight:700;color:#fff">{avg_quality}</div>
                            <div style="font-size:9px;color:#888">Avg Quality</div>
                        </div>
                        <div style="background:#0a0a1a;padding:8px;border-radius:8px;text-align:center">
                            <div style="font-size:18px;font-weight:700;color:#fff">{round(data['visible_seconds'], 0):.0f}s</div>
                            <div style="font-size:9px;color:#888">Total Visibility</div>
                        </div>
                        <div style="background:#0a0a1a;padding:8px;border-radius:8px;text-align:center">
                            <div style="font-size:18px;font-weight:700;color:#fff">{data['confidence_levels'].get('high', 0)}</div>
                            <div style="font-size:9px;color:#888">High-Conf IDs</div>
                        </div>
                        <div style="background:#0a0a1a;padding:8px;border-radius:8px;text-align:center">
                            <div style="font-size:18px;font-weight:700;color:#fff">{data['shot_types'].most_common(1)[0][0] if data['shot_types'] else '—'}</div>
                            <div style="font-size:9px;color:#888">Top Shot Type</div>
                        </div>
                    </div>
                </div>
            </div>

            <div style="margin-bottom:12px">
                <div style="font-size:11px;color:#888;text-transform:uppercase;letter-spacing:1px;margin-bottom:6px">Co-occurring Brands</div>
                {cobrand_html if cobrand_html else '<span style="color:#666;font-size:12px">No co-occurrences</span>'}
            </div>

            <div>
                <div style="font-size:11px;color:#888;text-transform:uppercase;letter-spacing:1px;margin-bottom:6px">Top Viral Clips</div>
                {top_clips_html if top_clips_html else '<span style="color:#666;font-size:12px">No clips with captions</span>'}
            </div>
        </div>"""

    # Summary stats
    total_brands = len(sorted_brands)
    total_appearances = sum(d["appearances"] for _, d in sorted_brands)
    top_brand = sorted_brands[0][0] if sorted_brands else "N/A"
    top_count = sorted_brands[0][1]["appearances"] if sorted_brands else 0

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Pickle DaaS — Brand Intelligence Report</title>
<style>
  * {{ margin:0; padding:0; box-sizing:border-box; }}
  body {{ background:#0a0a1a; color:#e0e0e0; font-family:'Inter','SF Pro',system-ui,sans-serif; padding:20px; }}
  .header {{ text-align:center; padding:40px 20px 20px; }}
  .header h1 {{ font-size:32px; font-weight:800; background:linear-gradient(135deg,#FF6B6B,#FFD54F); -webkit-background-clip:text; -webkit-text-fill-color:transparent; }}
  .header p {{ color:#888; margin-top:6px; font-size:13px; }}
  .kpi-grid {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(160px,1fr)); gap:12px; margin:24px 0; }}
  .kpi {{ background:#1a1a2e; border-radius:12px; padding:16px; text-align:center; }}
  .kpi .num {{ font-size:28px; font-weight:800; color:#FFD54F; }}
  .kpi .label {{ font-size:11px; color:#888; text-transform:uppercase; letter-spacing:1px; margin-top:2px; }}
  .brand-grid {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(400px,1fr)); gap:20px; margin:24px 0; }}
  .pitch {{ background:linear-gradient(135deg,#1a0a28,#0a1a28); border:1px solid #333; border-radius:16px; padding:24px; margin:24px 0; text-align:center; }}
  .pitch h2 {{ font-size:20px; color:#FFD54F; margin-bottom:8px; }}
  .pitch p {{ color:#999; font-size:13px; line-height:1.6; max-width:700px; margin:0 auto; }}
  .watermark {{ text-align:center; padding:30px; color:#444; font-size:12px; }}
</style>
</head>
<body>

<div class="header">
    <h1>Brand Intelligence Report</h1>
    <p>AI-powered brand detection and analysis across {len(sorted_brands)} brands in the Courtana pickleball ecosystem</p>
    <p style="color:#FFD54F;font-size:11px;margin-top:4px">Generated {datetime.now().strftime('%B %d, %Y')} | Pickle DaaS by PickleBill</p>
</div>

<div class="kpi-grid">
    <div class="kpi"><div class="num">{total_brands}</div><div class="label">Brands Detected</div></div>
    <div class="kpi"><div class="num">{total_appearances}</div><div class="label">Total Appearances</div></div>
    <div class="kpi"><div class="num">{top_brand}</div><div class="label">Most Visible Brand</div></div>
    <div class="kpi"><div class="num">{top_count}</div><div class="label">Top Brand Appearances</div></div>
</div>

<div class="brand-grid">
    {brand_cards}
</div>

<div class="pitch">
    <h2>This Is What Brand Intelligence Looks Like</h2>
    <p>Every clip in the Courtana ecosystem is analyzed by AI for brand visibility, player skill profiles, and competitive positioning. Brands can see exactly who uses their equipment, how those players perform, and what content drives the most engagement. This report covers a sample of the corpus — with 4,097+ highlight groups and growing, the intelligence only gets deeper.</p>
    <p style="color:#FFD54F;margin-top:12px;font-weight:600">Interested in a custom brand report? Contact PickleBill.</p>
</div>

<div class="watermark">
    Pickle DaaS Brand Intelligence v1.0 | AI-Analyzed Video Corpus | {datetime.now().strftime('%Y-%m-%d')}
</div>
</body>
</html>"""
    return html


def main():
    parser = argparse.ArgumentParser(description="Pickle DaaS Brand Intelligence Report")
    parser.add_argument("--brand", default=None, help="Generate report for specific brand (e.g. JOOLA)")
    parser.add_argument("--output", default="output/brand-intelligence-report.html")
    args = parser.parse_args()

    print(f"{'='*60}")
    print(f"Pickle DaaS — Brand Intelligence Report")
    print(f"{'='*60}")

    print("\n[1/3] Loading analyses...")
    analyses = load_analyses()
    print(f"  Loaded {len(analyses)} analyses with brand data")

    print("\n[2/3] Building brand intelligence...")
    brand_data = build_brand_intel(analyses, args.brand)
    print(f"  Profiled {len(brand_data)} brands")

    print("\n[3/3] Generating report...")
    html = generate_report(brand_data, args.output)
    with open(args.output, "w") as f:
        f.write(html)
    print(f"  Saved: {args.output}")

    # Also save JSON
    json_path = args.output.replace(".html", ".json")
    json_data = {}
    for brand, data in brand_data.items():
        json_data[brand] = {
            "appearances": data["appearances"],
            "unique_clips": len(set(c["url"] for c in data["clips"] if c["url"])),
            "avg_viral": round(sum(data["viral_scores"]) / max(len(data["viral_scores"]), 1), 1),
            "avg_quality": round(sum(data["quality_scores"]) / max(len(data["quality_scores"]), 1), 1),
            "top_category": data["categories"].most_common(1)[0][0] if data["categories"] else "unknown",
            "skill_profile": {k.replace("_rating", "").replace("_", " ").title(): round(sum(v) / len(v), 1) for k, v in data["skill_ratings"].items() if v},
            "co_brands": dict(data["co_occurring_brands"].most_common(5)),
            "visibility_seconds": round(data["visible_seconds"], 1),
        }
    with open(json_path, "w") as f:
        json.dump(json_data, f, indent=2)
    print(f"  Saved: {json_path}")

    # Summary
    for brand, data in sorted(brand_data.items(), key=lambda x: x[1]["appearances"], reverse=True)[:5]:
        avg_v = round(sum(data["viral_scores"]) / max(len(data["viral_scores"]), 1), 1)
        print(f"  {brand}: {data['appearances']} appearances, avg_viral={avg_v}")


if __name__ == "__main__":
    main()

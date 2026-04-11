#!/usr/bin/env python3
"""
Pickle DaaS — "Pickle Wrapped" Player Cards
=============================================
Spotify Wrapped-style shareable cards for every player in the system.
Each card: skill radar, badges, signature shot, brand loyalty, viral score.

USAGE:
  python generate-pickle-wrapped.py                    # All players
  python generate-pickle-wrapped.py --player PickleBill
"""

import json
import glob
import os
import argparse
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path

CORPUS_DIR = "output"
OUTPUT_DIR = "output/pickle-wrapped"


def load_analyses():
    files = glob.glob(f"{CORPUS_DIR}/**/analysis_*.json", recursive=True)
    analyses = []
    for f in files:
        try:
            if os.path.getsize(f) < 5000:
                continue
            with open(f) as fh:
                data = json.load(fh)
            if "skill_indicators" in data:
                analyses.append(data)
        except (json.JSONDecodeError, KeyError):
            continue
    return analyses


def build_player_profiles(analyses):
    """Build rich player profiles from all analyses."""
    # Also load ground truth for player→clip mapping
    gt_path = "output/badged-clips/ground-truth.json"
    player_clips_gt = defaultdict(set)

    if Path(gt_path).exists():
        with open(gt_path) as f:
            for item in json.load(f):
                for award in item.get("badge_awards", []):
                    username = award.get("profile_username", "")
                    hf = award.get("highlight_file", "")
                    uuid = hf.split("/")[-1].replace(".mp4", "") if hf else ""
                    if username and uuid:
                        player_clips_gt[username].add(uuid)

    # Map analyses by UUID
    analysis_by_uuid = {}
    for a in analyses:
        src = a.get("_source_url", "")
        uuid = src.split("/")[-1].replace(".mp4", "") if src else ""
        if uuid:
            analysis_by_uuid[uuid] = a

    # Also try _highlight_meta
    for a in analyses:
        meta = a.get("_highlight_meta", {})
        username = meta.get("profile_username")
        if username:
            src = a.get("_source_url", "")
            uuid = src.split("/")[-1].replace(".mp4", "") if src else ""
            if uuid:
                player_clips_gt[username].add(uuid)

    # Build profiles
    profiles = {}
    for player, clip_uuids in player_clips_gt.items():
        if not player or player == "unknown":
            continue

        player_analyses = [analysis_by_uuid[u] for u in clip_uuids if u in analysis_by_uuid]
        if not player_analyses:
            continue

        # Aggregate skills
        skills = defaultdict(list)
        brands_detected = Counter()
        badges_detected = Counter()
        viral_scores = []
        quality_scores = []
        shot_types = Counter()
        arcs = Counter()
        captions = []
        ron_quotes = []

        for a in player_analyses:
            sk = a.get("skill_indicators", {})
            for key in ["court_coverage_rating", "kitchen_mastery_rating", "power_game_rating",
                        "touch_and_feel_rating", "athleticism_rating", "creativity_rating",
                        "court_iq_rating", "consistency_rating", "composure_under_pressure",
                        "paddle_control_rating"]:
                val = sk.get(key)
                if isinstance(val, (int, float)) and val > 0:
                    skills[key].append(val)

            for b in a.get("brand_detection", {}).get("brands", []):
                name = b.get("brand_name", "").upper()
                if name:
                    brands_detected[name] += 1

            for badge in a.get("badge_intelligence", {}).get("predicted_badges", []):
                badges_detected[badge.get("badge_name", "unknown")] += 1

            cm = a.get("clip_meta", {})
            if cm.get("viral_potential_score"):
                viral_scores.append(cm["viral_potential_score"])
            if cm.get("clip_quality_score"):
                quality_scores.append(cm["clip_quality_score"])

            dom = a.get("shot_analysis", {}).get("dominant_shot_type")
            if dom:
                shot_types[dom] += 1

            arc = a.get("storytelling", {}).get("story_arc")
            if arc:
                arcs[arc] += 1

            cap = a.get("commentary", {}).get("social_media_caption", "")
            if cap:
                captions.append(cap)

            ron = a.get("commentary", {}).get("ron_burgundy_voice", "")
            if ron:
                ron_quotes.append(ron)

        avg_skills = {}
        for key, vals in skills.items():
            clean = key.replace("_rating", "").replace("_", " ").title()
            avg_skills[clean] = round(sum(vals) / len(vals), 1)

        profiles[player] = {
            "clip_count": len(player_analyses),
            "skills": avg_skills,
            "top_brands": brands_detected.most_common(5),
            "top_badges": badges_detected.most_common(5),
            "avg_viral": round(sum(viral_scores) / max(len(viral_scores), 1), 1),
            "avg_quality": round(sum(quality_scores) / max(len(quality_scores), 1), 1),
            "max_viral": max(viral_scores) if viral_scores else 0,
            "signature_shot": shot_types.most_common(1)[0][0] if shot_types else "unknown",
            "primary_arc": arcs.most_common(1)[0][0] if arcs else "unknown",
            "best_caption": max(captions, key=len) if captions else "",
            "best_ron": max(ron_quotes, key=len) if ron_quotes else "",
        }

    return profiles


def generate_card(player, data, color="#00E676"):
    """Generate a single Pickle Wrapped card as HTML."""
    skills = data["skills"]
    skill_labels = list(skills.keys())[:8]
    skill_values = [skills.get(l, 0) for l in skill_labels]

    # Radar chart data points (SVG polygon)
    import math
    n = len(skill_labels)
    cx, cy, r = 150, 150, 120
    points = []
    label_positions = []
    for i, val in enumerate(skill_values):
        angle = (2 * math.pi * i / n) - math.pi / 2
        px = cx + (val / 10 * r) * math.cos(angle)
        py = cy + (val / 10 * r) * math.sin(angle)
        points.append(f"{px},{py}")
        lx = cx + (r + 20) * math.cos(angle)
        ly = cy + (r + 20) * math.sin(angle)
        label_positions.append((lx, ly, skill_labels[i], skill_values[i]))

    polygon = " ".join(points)

    # Grid lines
    grid_lines = ""
    for level in [2, 4, 6, 8, 10]:
        gpoints = []
        for i in range(n):
            angle = (2 * math.pi * i / n) - math.pi / 2
            gx = cx + (level / 10 * r) * math.cos(angle)
            gy = cy + (level / 10 * r) * math.sin(angle)
            gpoints.append(f"{gx},{gy}")
        grid_lines += f'<polygon points="{" ".join(gpoints)}" fill="none" stroke="#333" stroke-width="0.5"/>\n'

    # Axis lines
    axis_lines = ""
    for i in range(n):
        angle = (2 * math.pi * i / n) - math.pi / 2
        ex = cx + r * math.cos(angle)
        ey = cy + r * math.sin(angle)
        axis_lines += f'<line x1="{cx}" y1="{cy}" x2="{ex}" y2="{ey}" stroke="#333" stroke-width="0.5"/>\n'

    # Labels
    label_svg = ""
    for lx, ly, label, val in label_positions:
        anchor = "middle"
        if lx < cx - 10:
            anchor = "end"
        elif lx > cx + 10:
            anchor = "start"
        label_svg += f'<text x="{lx}" y="{ly}" fill="#888" font-size="9" text-anchor="{anchor}" dominant-baseline="central">{label}</text>\n'
        label_svg += f'<text x="{lx}" y="{ly + 12}" fill="{color}" font-size="10" font-weight="700" text-anchor="{anchor}" dominant-baseline="central">{val}</text>\n'

    # Badges
    badges_html = ""
    for badge_name, count in data["top_badges"][:4]:
        badges_html += f'<span style="background:{color}22;color:{color};padding:3px 10px;border-radius:12px;font-size:11px;font-weight:600;white-space:nowrap">{badge_name}</span> '

    # Brands
    brands_html = ""
    for brand_name, count in data["top_brands"][:3]:
        brands_html += f'<span style="background:#333;color:#fff;padding:3px 10px;border-radius:12px;font-size:11px;font-weight:600">{brand_name} ({count}x)</span> '

    # Overall rating
    overall = round(sum(skill_values) / max(len(skill_values), 1), 1) if skill_values else 0

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<meta property="og:title" content="{player}'s Pickle Wrapped 2026">
<meta property="og:description" content="AI-powered player profile: {data['signature_shot']} specialist, {data['clip_count']} clips analyzed">
<title>{player} — Pickle Wrapped 2026</title>
<style>
  * {{ margin:0; padding:0; box-sizing:border-box; }}
  body {{ background:#0a0a1a; color:#fff; font-family:'Inter','SF Pro',system-ui,sans-serif; display:flex; justify-content:center; align-items:center; min-height:100vh; padding:20px; }}
  .card {{ width:400px; background:linear-gradient(180deg,#111122 0%,#0a0a1a 100%); border-radius:24px; padding:32px; border:1px solid #222; position:relative; overflow:hidden; }}
  .card::before {{ content:''; position:absolute; top:-50%; left:-50%; width:200%; height:200%; background:radial-gradient(circle at 30% 20%, {color}08 0%, transparent 50%); pointer-events:none; }}
  .glow {{ position:absolute; top:0; left:50%; transform:translateX(-50%); width:200px; height:3px; background:linear-gradient(90deg, transparent, {color}, transparent); border-radius:2px; }}
</style>
</head>
<body>
<div class="card">
    <div class="glow"></div>

    <!-- Header -->
    <div style="text-align:center;margin-bottom:20px;position:relative">
        <div style="font-size:10px;color:{color};text-transform:uppercase;letter-spacing:3px;font-weight:600;margin-bottom:8px">Pickle Wrapped 2026</div>
        <div style="font-size:32px;font-weight:800;letter-spacing:-1px">{player}</div>
        <div style="font-size:13px;color:#888;margin-top:4px">{data['signature_shot'].replace('_', ' ').title()} Specialist | {data['clip_count']} Clips Analyzed</div>
    </div>

    <!-- Overall Rating -->
    <div style="text-align:center;margin-bottom:20px">
        <div style="display:inline-block;width:80px;height:80px;border-radius:50%;border:3px solid {color};display:flex;align-items:center;justify-content:center;margin:0 auto">
            <div>
                <div style="font-size:28px;font-weight:800;color:{color};line-height:1">{overall}</div>
                <div style="font-size:8px;color:#888;text-transform:uppercase;letter-spacing:1px">Overall</div>
            </div>
        </div>
    </div>

    <!-- Radar Chart -->
    <div style="text-align:center;margin-bottom:20px">
        <svg width="300" height="300" viewBox="0 0 300 300" style="margin:0 auto">
            {grid_lines}
            {axis_lines}
            <polygon points="{polygon}" fill="{color}22" stroke="{color}" stroke-width="2"/>
            {label_svg}
        </svg>
    </div>

    <!-- Stats Grid -->
    <div style="display:grid;grid-template-columns:repeat(3,1fr);gap:12px;margin-bottom:20px">
        <div style="text-align:center;background:#1a1a2e;padding:12px 8px;border-radius:12px">
            <div style="font-size:22px;font-weight:800;color:{color}">{data['avg_viral']}</div>
            <div style="font-size:9px;color:#888;text-transform:uppercase;letter-spacing:1px">Avg Viral</div>
        </div>
        <div style="text-align:center;background:#1a1a2e;padding:12px 8px;border-radius:12px">
            <div style="font-size:22px;font-weight:800;color:#4FC3F7">{data['avg_quality']}</div>
            <div style="font-size:9px;color:#888;text-transform:uppercase;letter-spacing:1px">Avg Quality</div>
        </div>
        <div style="text-align:center;background:#1a1a2e;padding:12px 8px;border-radius:12px">
            <div style="font-size:22px;font-weight:800;color:#FFD54F">{data['max_viral']}</div>
            <div style="font-size:9px;color:#888;text-transform:uppercase;letter-spacing:1px">Peak Viral</div>
        </div>
    </div>

    <!-- Badges -->
    {'<div style="margin-bottom:16px"><div style="font-size:10px;color:#888;text-transform:uppercase;letter-spacing:1px;margin-bottom:8px">Top Badges</div><div style="display:flex;flex-wrap:wrap;gap:6px">' + badges_html + '</div></div>' if badges_html else ''}

    <!-- Brands -->
    {'<div style="margin-bottom:16px"><div style="font-size:10px;color:#888;text-transform:uppercase;letter-spacing:1px;margin-bottom:8px">Brand DNA</div><div style="display:flex;flex-wrap:wrap;gap:6px">' + brands_html + '</div></div>' if brands_html else ''}

    <!-- Quote -->
    {'<div style="background:#1a1a2e;border-radius:12px;padding:14px;margin-bottom:16px;border-left:2px solid #FF6B6B"><div style="font-size:11px;color:#FF6B6B;margin-bottom:4px;font-weight:600">Ron Burgundy Says:</div><div style="font-size:12px;color:#ccc;line-height:1.4;font-style:italic">' + data["best_ron"][:150] + '</div></div>' if data.get("best_ron") else ''}

    <!-- Footer -->
    <div style="text-align:center;padding-top:12px;border-top:1px solid #222">
        <div style="font-size:9px;color:#666">Powered by Pickle DaaS | AI Video Analysis by Gemini + Claude</div>
        <div style="font-size:9px;color:#444;margin-top:2px">picklebill.github.io/pickle-daas-data</div>
    </div>
</div>
</body>
</html>"""


def main():
    parser = argparse.ArgumentParser(description="Pickle Wrapped Player Cards")
    parser.add_argument("--player", default=None, help="Generate card for specific player")
    args = parser.parse_args()

    print(f"{'='*60}")
    print(f"Pickle Wrapped — Player Card Generator")
    print(f"{'='*60}")

    print("\n[1/3] Loading analyses...")
    analyses = load_analyses()
    print(f"  Loaded {len(analyses)} analyses")

    print("\n[2/3] Building player profiles...")
    profiles = build_player_profiles(analyses)
    print(f"  Built profiles for {len(profiles)} players")

    Path(OUTPUT_DIR).mkdir(parents=True, exist_ok=True)

    player_colors = {
        "PickleBill": "#00E676",
        "Ironvarr": "#4FC3F7",
        "Pmcintosh": "#FF6B6B",
        "Santinofuntila": "#FFD54F",
        "khamille06": "#BA68C8",
        "Daniella": "#FF8A65",
        "David": "#81C784",
        "Riccj": "#64B5F6",
    }

    print("\n[3/3] Generating cards...")
    for player, data in profiles.items():
        if args.player and player.lower() != args.player.lower():
            continue
        color = player_colors.get(player, "#00E676")
        html = generate_card(player, data, color)
        path = Path(OUTPUT_DIR) / f"{player.lower()}-wrapped.html"
        with open(path, "w") as f:
            f.write(html)
        print(f"  {player}: {data['clip_count']} clips, avg_viral={data['avg_viral']}, shot={data['signature_shot']} → {path}")

    # Also generate an index page
    index_cards = ""
    for player, data in sorted(profiles.items(), key=lambda x: x[1]["clip_count"], reverse=True):
        color = player_colors.get(player, "#00E676")
        overall = round(sum(data["skills"].values()) / max(len(data["skills"]), 1), 1) if data["skills"] else 0
        index_cards += f"""
        <a href="{player.lower()}-wrapped.html" style="text-decoration:none;color:inherit">
            <div style="background:#1a1a2e;border-radius:16px;padding:20px;border-left:3px solid {color};transition:transform 0.2s" onmouseover="this.style.transform='scale(1.02)'" onmouseout="this.style.transform='scale(1)'">
                <div style="display:flex;justify-content:space-between;align-items:center">
                    <div>
                        <div style="font-size:20px;font-weight:700">{player}</div>
                        <div style="font-size:12px;color:#888">{data['signature_shot'].replace('_',' ').title()} | {data['clip_count']} clips</div>
                    </div>
                    <div style="text-align:right">
                        <div style="font-size:28px;font-weight:800;color:{color}">{overall}</div>
                        <div style="font-size:10px;color:#888">Overall</div>
                    </div>
                </div>
            </div>
        </a>"""

    index_html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Pickle Wrapped 2026 — All Players</title>
<style>
  * {{ margin:0; padding:0; box-sizing:border-box; }}
  body {{ background:#0a0a1a; color:#fff; font-family:'Inter','SF Pro',system-ui,sans-serif; padding:20px; max-width:600px; margin:0 auto; }}
  h1 {{ font-size:28px; font-weight:800; text-align:center; background:linear-gradient(135deg,#00E676,#4FC3F7); -webkit-background-clip:text; -webkit-text-fill-color:transparent; padding:30px 0 10px; }}
  .subtitle {{ text-align:center; color:#888; font-size:13px; margin-bottom:24px; }}
  .cards {{ display:flex; flex-direction:column; gap:12px; }}
</style>
</head>
<body>
<h1>Pickle Wrapped 2026</h1>
<div class="subtitle">AI-powered player profiles from {sum(d['clip_count'] for d in profiles.values())} analyzed clips</div>
<div class="cards">{index_cards}</div>
<div style="text-align:center;padding:30px;color:#444;font-size:11px">Pickle DaaS by PickleBill | {datetime.now().strftime('%Y-%m-%d')}</div>
</body>
</html>"""
    index_path = Path(OUTPUT_DIR) / "index.html"
    with open(index_path, "w") as f:
        f.write(index_html)
    print(f"\n  Index page: {index_path}")


if __name__ == "__main__":
    main()

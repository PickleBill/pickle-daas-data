#!/usr/bin/env python3
"""
Pickle DaaS — Insight Engine
==============================
Reads ALL raw analysis JSONs from the corpus and extracts cross-cutting
intelligence insights that demonstrate the "art of the possible."

Generates an interactive HTML dashboard with:
- Viral prediction model (what makes clips shareable?)
- Brand-skill correlations (does gear matter?)
- Player archetype clustering
- Shot economy analysis (which shots win rallies?)
- Content strategy intelligence (what should venues film more of?)

USAGE:
  python insight-engine.py                    # Generate dashboard from all analyses
  python insight-engine.py --output my.html   # Custom output path
"""

import json
import glob
import os
import sys
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path

CORPUS_DIR = "output"
OUTPUT_FILE = "output/intelligence-preview.html"


def load_all_analyses():
    """Load all good analysis JSONs from output directories."""
    files = glob.glob(f"{CORPUS_DIR}/**/analysis_*.json", recursive=True)
    analyses = []
    for f in files:
        try:
            if os.path.getsize(f) < 5000:
                continue  # Skip error/empty files
            with open(f) as fh:
                data = json.load(fh)
            if "clip_meta" in data or "skill_indicators" in data:
                data["_file"] = f
                analyses.append(data)
        except (json.JSONDecodeError, KeyError):
            continue
    return analyses


def extract_insights(analyses):
    """Run all insight queries on the corpus."""
    insights = {}

    # === 1. VIRAL PREDICTION: What makes clips shareable? ===
    viral_data = []
    for a in analyses:
        cm = a.get("clip_meta", {})
        viral = cm.get("viral_potential_score")
        quality = cm.get("clip_quality_score")
        watchability = cm.get("watchability_score")
        sa = a.get("shot_analysis", {})
        dom_shot = sa.get("dominant_shot_type", "unknown")
        total_shots = sa.get("total_shots_estimated", 0)
        rally_len = sa.get("rally_length_estimated", 0)
        arc = a.get("storytelling", {}).get("story_arc", "unknown")
        tone = a.get("storytelling", {}).get("emotional_tone", "unknown")
        brands = len(a.get("brand_detection", {}).get("brands", []))
        badges = len(a.get("badge_intelligence", {}).get("predicted_badges", []))

        if viral and quality:
            viral_data.append({
                "viral": viral, "quality": quality, "watchability": watchability or 0,
                "dom_shot": dom_shot, "total_shots": total_shots or 0,
                "rally_length": rally_len or 0, "arc": arc, "tone": tone,
                "brands": brands, "badges": badges
            })

    # Viral correlations
    if viral_data:
        high_viral = [v for v in viral_data if v["viral"] >= 6]
        low_viral = [v for v in viral_data if v["viral"] <= 3]

        def avg(lst, key):
            vals = [x[key] for x in lst if isinstance(x[key], (int, float))]
            return round(sum(vals) / len(vals), 1) if vals else 0

        insights["viral_prediction"] = {
            "total_clips": len(viral_data),
            "high_viral_count": len(high_viral),
            "low_viral_count": len(low_viral),
            "high_viral_avg_quality": avg(high_viral, "quality"),
            "low_viral_avg_quality": avg(low_viral, "quality"),
            "high_viral_avg_rally_length": avg(high_viral, "rally_length"),
            "low_viral_avg_rally_length": avg(low_viral, "rally_length"),
            "high_viral_avg_shots": avg(high_viral, "total_shots"),
            "low_viral_avg_shots": avg(low_viral, "total_shots"),
            "high_viral_top_arcs": Counter(v["arc"] for v in high_viral).most_common(3),
            "low_viral_top_arcs": Counter(v["arc"] for v in low_viral).most_common(3),
            "high_viral_top_shots": Counter(v["dom_shot"] for v in high_viral).most_common(3),
            "high_viral_avg_badges": avg(high_viral, "badges"),
            "low_viral_avg_badges": avg(low_viral, "badges"),
            "viral_distribution": Counter(v["viral"] for v in viral_data),
        }

    # === 2. BRAND-SKILL CORRELATIONS ===
    brand_skills = defaultdict(lambda: defaultdict(list))
    for a in analyses:
        brands = [b.get("brand_name", "").upper() for b in a.get("brand_detection", {}).get("brands", [])
                  if b.get("category") == "paddle"]
        sk = a.get("skill_indicators", {})
        for brand in set(brands):
            if not brand:
                continue
            for skill_key in ["court_coverage_rating", "kitchen_mastery_rating", "power_game_rating",
                              "touch_and_feel_rating", "athleticism_rating", "creativity_rating",
                              "court_iq_rating", "consistency_rating"]:
                val = sk.get(skill_key)
                if isinstance(val, (int, float)) and val > 0:
                    brand_skills[brand][skill_key].append(val)

    brand_profiles = {}
    for brand, skills in brand_skills.items():
        if sum(len(v) for v in skills.values()) < 3:
            continue  # Need at least 3 data points
        profile = {}
        for skill, vals in skills.items():
            clean_name = skill.replace("_rating", "").replace("_", " ").title()
            profile[clean_name] = round(sum(vals) / len(vals), 1)
        profile["_sample_size"] = max(len(v) for v in skills.values())
        brand_profiles[brand] = profile
    insights["brand_skill_correlations"] = brand_profiles

    # === 3. PLAYER ARCHETYPE CLUSTERING ===
    player_clips = defaultdict(list)
    for a in analyses:
        meta = a.get("_highlight_meta", {})
        player = meta.get("profile_username") or "unknown"
        sk = a.get("skill_indicators", {})
        if any(isinstance(sk.get(k), (int, float)) and sk.get(k) > 0
               for k in ["kitchen_mastery_rating", "power_game_rating"]):
            player_clips[player].append(sk)

    player_archetypes = {}
    for player, clips in player_clips.items():
        if len(clips) < 2:
            continue
        avg_skills = {}
        for key in ["court_coverage_rating", "kitchen_mastery_rating", "power_game_rating",
                     "touch_and_feel_rating", "athleticism_rating", "creativity_rating",
                     "court_iq_rating", "consistency_rating", "composure_under_pressure",
                     "paddle_control_rating"]:
            vals = [c.get(key, 0) for c in clips if isinstance(c.get(key), (int, float)) and c.get(key) > 0]
            if vals:
                avg_skills[key.replace("_rating", "").replace("_", " ").title()] = round(sum(vals) / len(vals), 1)

        # Determine archetype
        kitchen = avg_skills.get("Kitchen Mastery", 0)
        power = avg_skills.get("Power Game", 0)
        creativity = avg_skills.get("Creativity", 0)
        athleticism = avg_skills.get("Athleticism", 0)
        consistency = avg_skills.get("Consistency", 0)

        if kitchen >= 7 and power < 5:
            archetype = "Kitchen Specialist"
        elif power >= 7 and kitchen < 6:
            archetype = "Power Player"
        elif creativity >= 7:
            archetype = "Creative Shotmaker"
        elif athleticism >= 7 and power >= 6:
            archetype = "Athletic All-Rounder"
        elif consistency >= 8:
            archetype = "The Wall"
        elif kitchen >= 6 and power >= 6:
            archetype = "Complete Player"
        else:
            archetype = "Developing Player"

        player_archetypes[player] = {
            "archetype": archetype,
            "clip_count": len(clips),
            "skills": avg_skills,
        }
    insights["player_archetypes"] = player_archetypes

    # === 4. SHOT ECONOMY: Which shots win rallies? ===
    shot_outcomes = defaultdict(lambda: Counter())
    shot_wow = defaultdict(list)
    for a in analyses:
        for shot in a.get("shot_analysis", {}).get("shots", []):
            stype = shot.get("shot_type", "unknown")
            outcome = shot.get("outcome", "unknown")
            wow = shot.get("wow_factor")
            quality = shot.get("quality_score")
            shot_outcomes[stype][outcome] += 1
            if isinstance(wow, (int, float)):
                shot_wow[stype].append(wow)

    shot_economy = {}
    for stype, outcomes in shot_outcomes.items():
        total = sum(outcomes.values())
        if total < 5:
            continue
        winners = outcomes.get("winner", 0)
        errors = outcomes.get("error", 0) + outcomes.get("forced_error", 0)
        avg_wow = round(sum(shot_wow.get(stype, [0])) / max(len(shot_wow.get(stype, [1])), 1), 1)
        shot_economy[stype] = {
            "total": total,
            "winner_pct": round(winners / total * 100, 1),
            "error_pct": round(errors / total * 100, 1),
            "avg_wow_factor": avg_wow,
            "win_rate": round((winners - errors) / total * 100, 1),  # net effectiveness
        }
    insights["shot_economy"] = dict(sorted(shot_economy.items(), key=lambda x: x[1]["total"], reverse=True))

    # === 5. CONTENT STRATEGY: What should venues film more? ===
    arc_virality = defaultdict(list)
    for v in viral_data:
        arc_virality[v["arc"]].append(v["viral"])

    content_strategy = {}
    for arc, virals in arc_virality.items():
        if len(virals) < 2:
            continue
        content_strategy[arc] = {
            "clip_count": len(virals),
            "avg_viral": round(sum(virals) / len(virals), 1),
            "max_viral": max(virals),
            "recommendation": "Film more" if sum(virals) / len(virals) > 4.5 else "Good baseline" if sum(virals) / len(virals) > 3 else "Low viral potential"
        }
    insights["content_strategy"] = dict(sorted(content_strategy.items(), key=lambda x: x[1]["avg_viral"], reverse=True))

    # === 6. AGGREGATE STATS ===
    all_skills = defaultdict(list)
    for a in analyses:
        sk = a.get("skill_indicators", {})
        for key in ["court_coverage_rating", "kitchen_mastery_rating", "power_game_rating",
                     "touch_and_feel_rating", "athleticism_rating", "creativity_rating",
                     "court_iq_rating", "consistency_rating"]:
            val = sk.get(key)
            if isinstance(val, (int, float)) and val > 0:
                all_skills[key].append(val)

    insights["aggregate_stats"] = {
        "total_analyses": len(analyses),
        "unique_players": len(player_clips),
        "unique_brands": len(brand_profiles),
        "total_shots_analyzed": sum(len(a.get("shot_analysis", {}).get("shots", [])) for a in analyses),
        "avg_skills": {k.replace("_rating", "").replace("_", " ").title(): round(sum(v) / len(v), 1) for k, v in all_skills.items() if v},
    }

    return insights


def generate_dashboard(insights):
    """Generate interactive HTML dashboard from insights."""
    stats = insights.get("aggregate_stats", {})
    viral = insights.get("viral_prediction", {})
    brands = insights.get("brand_skill_correlations", {})
    archetypes = insights.get("player_archetypes", {})
    shots = insights.get("shot_economy", {})
    content = insights.get("content_strategy", {})

    # Build brand radar data for Chart.js
    brand_labels = list(brands.keys())[:6]
    skill_dims = ["Court Coverage", "Kitchen Mastery", "Power Game", "Touch And Feel", "Athleticism", "Creativity", "Court Iq", "Consistency"]
    brand_datasets = []
    colors = ["#00E676", "#FF6B6B", "#4FC3F7", "#FFD54F", "#BA68C8", "#FF8A65"]
    for i, brand in enumerate(brand_labels):
        vals = [brands[brand].get(dim, 0) for dim in skill_dims]
        brand_datasets.append({
            "label": brand,
            "data": vals,
            "borderColor": colors[i % len(colors)],
            "backgroundColor": colors[i % len(colors)] + "33",
            "pointBackgroundColor": colors[i % len(colors)],
        })

    # Shot economy table rows
    shot_rows = ""
    for stype, data in list(shots.items())[:12]:
        bar_width = min(data["total"] / max(s["total"] for s in shots.values()) * 100, 100)
        net_color = "#00E676" if data["win_rate"] > 0 else "#FF6B6B"
        shot_rows += f"""
        <tr>
            <td style="font-weight:600">{stype.replace('_', ' ').title()}</td>
            <td>{data['total']}</td>
            <td><div style="background:#00E676;height:8px;width:{data['winner_pct']}%;border-radius:4px"></div> {data['winner_pct']}%</td>
            <td><div style="background:#FF6B6B;height:8px;width:{data['error_pct']}%;border-radius:4px"></div> {data['error_pct']}%</td>
            <td style="color:{net_color};font-weight:700">{data['win_rate']:+.1f}%</td>
            <td>{'⭐' * int(data['avg_wow_factor'] / 2)}</td>
        </tr>"""

    # Player archetype cards
    archetype_cards = ""
    archetype_colors = {
        "Kitchen Specialist": "#4FC3F7",
        "Power Player": "#FF6B6B",
        "Creative Shotmaker": "#BA68C8",
        "Athletic All-Rounder": "#FFD54F",
        "The Wall": "#00E676",
        "Complete Player": "#FF8A65",
        "Developing Player": "#90A4AE",
    }
    for player, data in sorted(archetypes.items(), key=lambda x: x[1]["clip_count"], reverse=True):
        color = archetype_colors.get(data["archetype"], "#90A4AE")
        skill_bars = ""
        for skill, val in sorted(data["skills"].items(), key=lambda x: x[1], reverse=True)[:6]:
            width = val * 10
            skill_bars += f'<div style="display:flex;align-items:center;gap:8px;margin:3px 0"><span style="width:120px;font-size:11px;color:#999">{skill}</span><div style="background:{color}33;height:6px;width:100px;border-radius:3px"><div style="background:{color};height:6px;width:{width}%;border-radius:3px"></div></div><span style="font-size:11px;color:{color}">{val}</span></div>'

        archetype_cards += f"""
        <div style="background:#1a1a2e;border-radius:12px;padding:20px;border-left:3px solid {color}">
            <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:12px">
                <div>
                    <div style="font-size:18px;font-weight:700;color:#fff">{player}</div>
                    <div style="font-size:12px;color:{color};font-weight:600;text-transform:uppercase;letter-spacing:1px">{data['archetype']}</div>
                </div>
                <div style="background:{color}22;color:{color};padding:4px 12px;border-radius:20px;font-size:12px;font-weight:600">{data['clip_count']} clips</div>
            </div>
            {skill_bars}
        </div>"""

    # Content strategy rows
    content_rows = ""
    for arc, data in content.items():
        viral_bar = data["avg_viral"] / 10 * 100
        rec_color = "#00E676" if data["recommendation"] == "Film more" else "#FFD54F" if "baseline" in data["recommendation"] else "#FF6B6B"
        content_rows += f"""
        <tr>
            <td style="font-weight:600">{arc.replace('_', ' ').title()}</td>
            <td>{data['clip_count']}</td>
            <td><div style="display:flex;align-items:center;gap:8px"><div style="background:#4FC3F7;height:8px;width:{viral_bar}%;border-radius:4px;min-width:4px"></div> {data['avg_viral']}</div></td>
            <td>{data['max_viral']}</td>
            <td style="color:{rec_color};font-weight:600">{data['recommendation']}</td>
        </tr>"""

    # Viral distribution chart data
    viral_dist = viral.get("viral_distribution", {})
    viral_labels = sorted(viral_dist.keys())
    viral_counts = [viral_dist.get(l, 0) for l in viral_labels]

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Pickle DaaS — Intelligence Preview</title>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4"></script>
<style>
  * {{ margin:0; padding:0; box-sizing:border-box; }}
  body {{ background:#0a0a1a; color:#e0e0e0; font-family:'Inter','SF Pro',system-ui,sans-serif; padding:20px; }}
  .header {{ text-align:center; padding:40px 20px; margin-bottom:30px; }}
  .header h1 {{ font-size:36px; font-weight:800; background:linear-gradient(135deg,#00E676,#4FC3F7); -webkit-background-clip:text; -webkit-text-fill-color:transparent; }}
  .header p {{ color:#888; margin-top:8px; font-size:14px; }}
  .kpi-grid {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(180px,1fr)); gap:16px; margin-bottom:30px; }}
  .kpi {{ background:#1a1a2e; border-radius:12px; padding:20px; text-align:center; }}
  .kpi .number {{ font-size:32px; font-weight:800; color:#00E676; }}
  .kpi .label {{ font-size:12px; color:#888; text-transform:uppercase; letter-spacing:1px; margin-top:4px; }}
  .section {{ background:#111122; border-radius:16px; padding:24px; margin-bottom:24px; }}
  .section h2 {{ font-size:20px; font-weight:700; margin-bottom:16px; display:flex; align-items:center; gap:10px; }}
  .section h2 .emoji {{ font-size:24px; }}
  .grid-2 {{ display:grid; grid-template-columns:1fr 1fr; gap:20px; }}
  .grid-3 {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(280px,1fr)); gap:16px; }}
  table {{ width:100%; border-collapse:collapse; font-size:13px; }}
  th {{ text-align:left; padding:8px 12px; color:#888; font-weight:600; text-transform:uppercase; font-size:11px; letter-spacing:1px; border-bottom:1px solid #333; }}
  td {{ padding:8px 12px; border-bottom:1px solid #1a1a2e; }}
  .insight-card {{ background:#1a1a2e; border-radius:12px; padding:20px; }}
  .insight-card h3 {{ font-size:14px; color:#4FC3F7; margin-bottom:8px; text-transform:uppercase; letter-spacing:1px; }}
  .insight-card .value {{ font-size:24px; font-weight:700; color:#fff; }}
  .insight-card .detail {{ font-size:12px; color:#888; margin-top:4px; }}
  .vs-row {{ display:flex; justify-content:space-between; align-items:center; padding:12px 0; border-bottom:1px solid #222; }}
  .vs-label {{ font-size:12px; color:#888; width:140px; }}
  .vs-bar {{ flex:1; height:8px; background:#222; border-radius:4px; margin:0 12px; position:relative; }}
  .vs-fill {{ height:8px; border-radius:4px; position:absolute; top:0; }}
  @media(max-width:768px) {{ .grid-2,.grid-3 {{ grid-template-columns:1fr; }} }}
  .badge {{ display:inline-block; padding:2px 8px; border-radius:10px; font-size:11px; font-weight:600; }}
  .watermark {{ text-align:center; padding:30px; color:#444; font-size:12px; }}
</style>
</head>
<body>

<div class="header">
    <h1>Pickle DaaS Intelligence Preview</h1>
    <p>Cross-cutting insights from {stats.get('total_analyses', 0)} analyzed clips | Generated {datetime.now().strftime('%B %d, %Y at %I:%M %p')}</p>
    <p style="color:#4FC3F7;margin-top:4px;font-size:12px">This is what your data looks like when AI watches every clip. Imagine 400,000.</p>
</div>

<!-- KPIs -->
<div class="kpi-grid">
    <div class="kpi"><div class="number">{stats.get('total_analyses', 0)}</div><div class="label">Clips Analyzed</div></div>
    <div class="kpi"><div class="number">{stats.get('total_shots_analyzed', 0)}</div><div class="label">Shots Tracked</div></div>
    <div class="kpi"><div class="number">{stats.get('unique_players', 0)}</div><div class="label">Player Profiles</div></div>
    <div class="kpi"><div class="number">{stats.get('unique_brands', 0)}</div><div class="label">Brands Detected</div></div>
    <div class="kpi"><div class="number">{len(shots)}</div><div class="label">Shot Types</div></div>
    <div class="kpi"><div class="number" style="color:#4FC3F7">{viral.get('high_viral_count', 0)}</div><div class="label">High-Viral Clips</div></div>
</div>

<!-- VIRAL PREDICTION -->
<div class="section">
    <h2><span class="emoji">🔥</span> Viral Prediction Intelligence</h2>
    <p style="color:#888;margin-bottom:20px;font-size:13px">What separates clips that go viral from ones that don't? Here's what the data says.</p>
    <div class="grid-2">
        <div>
            <div class="grid-3" style="grid-template-columns:1fr 1fr">
                <div class="insight-card">
                    <h3>High-Viral Clips</h3>
                    <div class="value" style="color:#00E676">{viral.get('high_viral_count', 0)}</div>
                    <div class="detail">Viral score 6+ out of 10</div>
                </div>
                <div class="insight-card">
                    <h3>Avg Quality (Viral)</h3>
                    <div class="value">{viral.get('high_viral_avg_quality', 0)}</div>
                    <div class="detail">vs {viral.get('low_viral_avg_quality', 0)} for low-viral</div>
                </div>
                <div class="insight-card">
                    <h3>Avg Rally Length (Viral)</h3>
                    <div class="value">{viral.get('high_viral_avg_rally_length', 0)}</div>
                    <div class="detail">vs {viral.get('low_viral_avg_rally_length', 0)} for low-viral</div>
                </div>
                <div class="insight-card">
                    <h3>Avg Badges (Viral)</h3>
                    <div class="value">{viral.get('high_viral_avg_badges', 0)}</div>
                    <div class="detail">vs {viral.get('low_viral_avg_badges', 0)} for low-viral</div>
                </div>
            </div>
        </div>
        <div>
            <canvas id="viralDistChart" height="200"></canvas>
        </div>
    </div>
</div>

<!-- BRAND-SKILL CORRELATIONS -->
<div class="section">
    <h2><span class="emoji">🏷️</span> Brand Intelligence: Does Your Gear Matter?</h2>
    <p style="color:#888;margin-bottom:20px;font-size:13px">Skill profiles of players grouped by paddle brand. Each brand attracts a different type of player.</p>
    <div class="grid-2">
        <div>
            <canvas id="brandRadar" height="300"></canvas>
        </div>
        <div>
            <table>
                <tr><th>Brand</th><th>Sample</th><th>Top Skill</th><th>Weakest Skill</th></tr>
                {"".join(f'<tr><td style="font-weight:600;color:{colors[i % len(colors)]}">{brand}</td><td>{data.get("_sample_size", "?")}</td><td style="color:#00E676">{max((k,v) for k,v in data.items() if k != "_sample_size")[0] if len([k for k in data if k != "_sample_size"]) > 0 else "—"}</td><td style="color:#FF6B6B">{min((k,v) for k,v in data.items() if k != "_sample_size")[0] if len([k for k in data if k != "_sample_size"]) > 0 else "—"}</td></tr>' for i, (brand, data) in enumerate(brands.items()))}
            </table>
        </div>
    </div>
</div>

<!-- PLAYER ARCHETYPES -->
<div class="section">
    <h2><span class="emoji">🧬</span> Player DNA Archetypes</h2>
    <p style="color:#888;margin-bottom:20px;font-size:13px">AI-classified player types based on skill patterns across multiple clips. Every player has a unique DNA fingerprint.</p>
    <div class="grid-3">
        {archetype_cards}
    </div>
</div>

<!-- SHOT ECONOMY -->
<div class="section">
    <h2><span class="emoji">🎯</span> Shot Economy: What Wins Rallies?</h2>
    <p style="color:#888;margin-bottom:20px;font-size:13px">Win rate = (winners - errors) / total. Positive = net effective. Negative = risky.</p>
    <table>
        <tr><th>Shot Type</th><th>Total</th><th>Winner %</th><th>Error %</th><th>Net Effect</th><th>Wow Factor</th></tr>
        {shot_rows}
    </table>
</div>

<!-- CONTENT STRATEGY -->
<div class="section">
    <h2><span class="emoji">📊</span> Content Strategy: What Should Venues Film?</h2>
    <p style="color:#888;margin-bottom:20px;font-size:13px">Not all highlight types are created equal. Here's what the data says about what content performs best.</p>
    <table>
        <tr><th>Story Arc</th><th>Clips</th><th>Avg Viral Score</th><th>Max Viral</th><th>Recommendation</th></tr>
        {content_rows}
    </table>
</div>

<!-- WHAT THIS MEANS -->
<div class="section" style="background:linear-gradient(135deg,#0a1628,#1a0a28);border:1px solid #333">
    <h2><span class="emoji">💡</span> What This Means</h2>
    <div class="grid-3">
        <div class="insight-card" style="border-left:3px solid #00E676">
            <h3>For Venues</h3>
            <div class="detail" style="color:#ccc;font-size:13px">Configure cameras to capture more of the high-viral content types. Optimize highlight detection for rally types that perform best on social.</div>
        </div>
        <div class="insight-card" style="border-left:3px solid #4FC3F7">
            <h3>For Brands</h3>
            <div class="detail" style="color:#ccc;font-size:13px">Know exactly which player segments use your gear and how they perform. Target sponsorships at players whose archetype matches your brand identity.</div>
        </div>
        <div class="insight-card" style="border-left:3px solid #FFD54F">
            <h3>For Coaches</h3>
            <div class="detail" style="color:#ccc;font-size:13px">Identify player archetypes instantly. Know which shots have the highest net effectiveness. Build training plans around data, not intuition.</div>
        </div>
    </div>
    <p style="text-align:center;color:#666;margin-top:20px;font-size:13px">This analysis is from <strong>{stats.get('total_analyses', 0)} clips</strong>. The Courtana system has <strong>4,097+ highlight groups</strong> ready to analyze. At 400,000 clips, these insights become statistically unassailable.</p>
</div>

<div class="watermark">
    Pickle DaaS Intelligence Engine v1.0 | Powered by Gemini 2.5 Flash + Claude | {datetime.now().strftime('%Y-%m-%d')}
</div>

<script>
// Viral Distribution Chart
new Chart(document.getElementById('viralDistChart'), {{
    type: 'bar',
    data: {{
        labels: {json.dumps([str(l) for l in viral_labels])},
        datasets: [{{
            label: 'Clips at this viral score',
            data: {json.dumps(viral_counts)},
            backgroundColor: {json.dumps(viral_labels)}.map(v => parseInt(v) >= 6 ? '#00E676' : parseInt(v) <= 3 ? '#FF6B6B44' : '#4FC3F744'),
            borderColor: {json.dumps(viral_labels)}.map(v => parseInt(v) >= 6 ? '#00E676' : parseInt(v) <= 3 ? '#FF6B6B' : '#4FC3F7'),
            borderWidth: 1,
            borderRadius: 4,
        }}]
    }},
    options: {{
        responsive: true,
        plugins: {{ legend: {{ display: false }}, title: {{ display: true, text: 'Viral Score Distribution', color: '#888' }} }},
        scales: {{
            x: {{ grid: {{ color: '#222' }}, ticks: {{ color: '#888' }}, title: {{ display: true, text: 'Viral Score', color: '#888' }} }},
            y: {{ grid: {{ color: '#222' }}, ticks: {{ color: '#888' }}, title: {{ display: true, text: 'Number of Clips', color: '#888' }} }}
        }}
    }}
}});

// Brand Radar Chart
new Chart(document.getElementById('brandRadar'), {{
    type: 'radar',
    data: {{
        labels: {json.dumps(skill_dims)},
        datasets: {json.dumps(brand_datasets)}
    }},
    options: {{
        responsive: true,
        plugins: {{ legend: {{ labels: {{ color: '#888' }} }} }},
        scales: {{
            r: {{
                beginAtZero: true, max: 10,
                grid: {{ color: '#333' }},
                angleLines: {{ color: '#333' }},
                pointLabels: {{ color: '#888', font: {{ size: 10 }} }},
                ticks: {{ color: '#666', backdropColor: 'transparent' }}
            }}
        }}
    }}
}});
</script>
</body>
</html>"""
    return html


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Pickle DaaS Insight Engine")
    parser.add_argument("--output", default=OUTPUT_FILE, help=f"Output HTML path (default: {OUTPUT_FILE})")
    args = parser.parse_args()

    print(f"{'='*60}")
    print(f"Pickle DaaS — Insight Engine")
    print(f"{'='*60}")

    print("\n[1/3] Loading analyses...")
    analyses = load_all_analyses()
    print(f"  Loaded {len(analyses)} analyses")

    print("\n[2/3] Extracting insights...")
    insights = extract_insights(analyses)

    # Save raw insights as JSON too
    insights_path = args.output.replace(".html", ".json")
    with open(insights_path, "w") as f:
        json.dump(insights, f, indent=2, default=str)
    print(f"  Saved insights JSON: {insights_path}")

    print("\n[3/3] Generating dashboard...")
    html = generate_dashboard(insights)
    with open(args.output, "w") as f:
        f.write(html)
    print(f"  Saved: {args.output}")

    # Print key findings
    vp = insights.get("viral_prediction", {})
    print(f"\n{'='*60}")
    print(f"KEY FINDINGS:")
    print(f"  Total clips analyzed: {insights['aggregate_stats']['total_analyses']}")
    print(f"  Shots tracked: {insights['aggregate_stats']['total_shots_analyzed']}")
    print(f"  High-viral clips (6+): {vp.get('high_viral_count', 0)}")
    print(f"  Player archetypes identified: {len(insights['player_archetypes'])}")
    print(f"  Brands profiled: {len(insights['brand_skill_correlations'])}")
    print(f"  Shot types analyzed: {len(insights['shot_economy'])}")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()

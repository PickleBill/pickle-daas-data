#!/usr/bin/env python3
"""
Pickle DaaS — Player Shareable Card Generator
===============================================
Aggregates analysis data per player and generates shareable HTML cards.
Each card shows: skill radar, clip count, brands detected, badges, and top clips.

USAGE:
  python tools/generate-player-cards.py                    # All players
  python tools/generate-player-cards.py --player PickleBill  # Single player
"""

import json
import glob
import argparse
from pathlib import Path
from collections import defaultdict
from datetime import datetime


OUTPUT_DIR = "output/player-cards"


def load_ground_truth():
    """Load player→clips mapping from ground truth badge data."""
    gt_path = "output/badged-clips/ground-truth.json"
    player_clips = defaultdict(list)  # username → list of clip UUIDs
    player_badges = defaultdict(lambda: defaultdict(int))  # username → badge_name → count

    if not Path(gt_path).exists():
        return player_clips, player_badges

    with open(gt_path) as f:
        gt_data = json.load(f)

    for item in gt_data:
        # Get clip UUID from primary_url or from badge award highlight_file
        primary = item.get("primary_url", "")
        clip_uuid = primary.split("/")[-1].replace(".mp4", "") if primary else ""

        for award in item.get("badge_awards", []):
            username = award.get("profile_username", "unknown")
            badge = award.get("badge_name", "unknown")
            player_badges[username][badge] += 1

            if not clip_uuid:
                hf = award.get("highlight_file", "")
                clip_uuid = hf.split("/")[-1].replace(".mp4", "") if hf else ""

            if clip_uuid and clip_uuid not in player_clips[username]:
                player_clips[username].append(clip_uuid)

    return player_clips, player_badges


def load_analyses():
    """Load all analysis JSONs and index by clip UUID."""
    analyses = {}
    for pattern in ["output/fast-batch-*/analysis_*.json", "output/badged-clips-analysis/analysis_*.json",
                     "output/auto-ingest-*/analysis_*.json", "output/scale-*/analysis_*.json"]:
        for path in glob.glob(pattern):
            try:
                with open(path) as f:
                    data = json.load(f)
                src = data.get("_source_url", "")
                uuid = src.split("/")[-1].replace(".mp4", "") if src else ""
                if uuid:
                    analyses[uuid] = data
            except (json.JSONDecodeError, KeyError):
                continue
    return analyses


def aggregate_player(username, clip_uuids, analyses, badges):
    """Build a player profile from their analyzed clips."""
    skills = defaultdict(list)
    brands = defaultdict(int)
    arcs = defaultdict(int)
    clips_data = []
    total_shots = 0

    for uuid in clip_uuids:
        if uuid not in analyses:
            continue
        a = analyses[uuid]

        # Skills from skill_indicators
        si = a.get("skill_indicators", {})
        for key in ["court_coverage", "kitchen_play", "creativity", "athleticism", "court_iq", "power_game"]:
            val = si.get(key)
            if isinstance(val, (int, float)):
                skills[key].append(val)

        # Brands
        for b in a.get("brand_detection", {}).get("brands", []):
            name = b.get("brand_name", str(b)) if isinstance(b, dict) else str(b)
            brands[name] += 1

        # Story arc
        arc = a.get("storytelling", {}).get("story_arc", a.get("clip_meta", {}).get("story_arc", ""))
        if arc:
            arcs[arc] += 1

        # Shot count
        ts = a.get("shot_analysis", {}).get("total_shots", 0)
        if isinstance(ts, (int, float)):
            total_shots += ts

        # Clip summary for card
        cm = a.get("clip_meta", {})
        clips_data.append({
            "uuid": uuid,
            "quality": cm.get("clip_quality_score", 0),
            "arc": a.get("storytelling", {}).get("story_arc", ""),
            "summary": cm.get("clip_summary", a.get("commentary", {}).get("social_media_caption", "")),
            "thumbnail": a.get("_source_url", "").replace(".mp4", ".jpeg"),
        })

    # Compute averages
    avg_skills = {}
    for key, vals in skills.items():
        avg_skills[key] = round(sum(vals) / len(vals), 1) if vals else 0

    clips_data.sort(key=lambda c: c["quality"], reverse=True)

    return {
        "username": username,
        "clips_analyzed": len([u for u in clip_uuids if u in analyses]),
        "clips_total": len(clip_uuids),
        "avg_skills": avg_skills,
        "brands": dict(sorted(brands.items(), key=lambda x: -x[1])),
        "badges": dict(sorted(badges.items(), key=lambda x: -x[1])[:15]),
        "arcs": dict(arcs),
        "total_shots": total_shots,
        "top_clips": clips_data[:6],
        "generated": datetime.now().isoformat(),
    }


def generate_card_html(profile):
    """Generate a shareable HTML card for a player."""
    u = profile["username"]
    skills = profile["avg_skills"]
    skill_names = {
        "court_coverage": "Court Coverage",
        "kitchen_play": "Kitchen",
        "creativity": "Creativity",
        "athleticism": "Athleticism",
        "court_iq": "Court IQ",
        "power_game": "Power",
    }

    # Skill bars HTML
    skill_bars = ""
    for key, label in skill_names.items():
        val = skills.get(key, 0)
        pct = val * 10 if val <= 10 else min(val, 100)
        skill_bars += f"""
      <div class="skill-row">
        <span class="skill-label">{label}</span>
        <div class="skill-track"><div class="skill-fill" style="width:{pct}%"></div></div>
        <span class="skill-val">{val}</span>
      </div>"""

    # Badge pills
    badge_pills = ""
    for badge, count in list(profile["badges"].items())[:8]:
        badge_pills += f'<span class="badge-pill">{badge} <span class="badge-count">{count}x</span></span>\n'

    # Brand pills
    brand_pills = ""
    for brand, count in list(profile["brands"].items())[:6]:
        brand_pills += f'<span class="brand-pill">{brand}</span>\n'

    # Top clips
    clips_html = ""
    for clip in profile["top_clips"][:3]:
        clips_html += f"""
      <div class="clip-mini">
        <img src="{clip['thumbnail']}" alt="{clip['arc']}" onerror="this.style.background='oklch(92% 0.01 240)'" loading="lazy">
        <div class="clip-mini-meta">
          <span class="clip-mini-score">{clip['quality']}/10</span>
          <span class="clip-mini-arc">{clip['arc']}</span>
        </div>
      </div>"""

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{u} — Pickle DaaS Player Card</title>
<meta property="og:title" content="{u} — AI Pickleball DNA">
<meta property="og:description" content="{profile['clips_analyzed']} clips analyzed · {len(profile['badges'])} badge types · Powered by Pickle DaaS">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Bricolage+Grotesque:opsz,wght@12..96,400;12..96,600;12..96,700;12..96,800&family=Literata:opsz,wght@7..72,400;7..72,500&family=Azeret+Mono:wght@400;500&display=swap" rel="stylesheet">
<style>
:root {{
  --bg: oklch(97% 0.008 240);
  --surface: oklch(100% 0 0);
  --border: oklch(88% 0.012 240);
  --text: oklch(18% 0.015 240);
  --text-sec: oklch(44% 0.016 240);
  --text-muted: oklch(62% 0.01 240);
  --accent: oklch(52% 0.185 250);
  --accent-bg: oklch(95.5% 0.04 250);
  --accent-border: oklch(86% 0.06 250);
  --positive: oklch(50% 0.14 160);
  --positive-bg: oklch(96% 0.04 160);
  --ff-display: 'Bricolage Grotesque', system-ui, sans-serif;
  --ff-body: 'Literata', Georgia, serif;
  --ff-mono: 'Azeret Mono', monospace;
  --radius: 14px;
}}
*, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}
body {{ background: var(--bg); font-family: var(--ff-body); color: var(--text); padding: 32px; display: flex; justify-content: center; }}
.card {{
  background: var(--surface); border: 1px solid var(--border);
  border-radius: var(--radius); max-width: 560px; width: 100%;
  box-shadow: 0 4px 16px oklch(0% 0 0 / 0.08);
  overflow: hidden;
}}
.card-header {{
  padding: 32px 32px 24px;
  border-bottom: 1px solid var(--border);
}}
.player-name {{
  font-family: var(--ff-display); font-size: 2rem; font-weight: 800;
  letter-spacing: -0.03em; color: var(--text); line-height: 1;
  margin-bottom: 8px;
}}
.player-stats {{
  display: flex; gap: 24px;
  font-family: var(--ff-display); font-size: 0.82rem;
  color: var(--text-muted);
}}
.player-stats strong {{ color: var(--accent); font-weight: 700; }}
.card-section {{
  padding: 24px 32px;
  border-bottom: 1px solid var(--border);
}}
.card-section:last-child {{ border-bottom: none; }}
.section-label {{
  font-family: var(--ff-display); font-size: 0.7rem; font-weight: 600;
  letter-spacing: 0.08em; text-transform: uppercase;
  color: var(--text-muted); margin-bottom: 16px;
}}
.skill-row {{
  display: flex; align-items: center; gap: 12px;
  margin-bottom: 10px;
}}
.skill-label {{
  font-family: var(--ff-display); font-size: 0.82rem; font-weight: 500;
  color: var(--text-sec); width: 100px; flex-shrink: 0;
}}
.skill-track {{
  flex: 1; height: 6px; background: var(--border);
  border-radius: 3px; overflow: hidden;
}}
.skill-fill {{
  height: 100%; background: var(--accent);
  border-radius: 3px; transition: width 0.6s ease;
}}
.skill-val {{
  font-family: var(--ff-mono); font-size: 0.78rem; font-weight: 500;
  color: var(--text); width: 32px; text-align: right;
}}
.pills {{ display: flex; flex-wrap: wrap; gap: 6px; }}
.badge-pill {{
  font-family: var(--ff-display); font-size: 0.7rem; font-weight: 600;
  padding: 4px 10px; border-radius: 999px;
  background: var(--accent-bg); border: 1px solid var(--accent-border);
  color: var(--accent);
}}
.badge-count {{ font-weight: 400; color: var(--text-muted); margin-left: 2px; }}
.brand-pill {{
  font-family: var(--ff-display); font-size: 0.7rem; font-weight: 600;
  padding: 4px 10px; border-radius: 999px;
  background: var(--positive-bg); border: 1px solid oklch(86% 0.06 160);
  color: var(--positive);
}}
.clips-grid {{ display: grid; grid-template-columns: repeat(3, 1fr); gap: 8px; }}
.clip-mini {{ border-radius: 8px; overflow: hidden; border: 1px solid var(--border); }}
.clip-mini img {{ width: 100%; aspect-ratio: 16/9; object-fit: cover; display: block; background: var(--bg); }}
.clip-mini-meta {{
  padding: 6px 8px; display: flex; justify-content: space-between;
  font-family: var(--ff-display); font-size: 0.68rem;
}}
.clip-mini-score {{ font-weight: 700; color: var(--positive); }}
.clip-mini-arc {{ color: var(--text-muted); font-weight: 500; }}
.card-footer {{
  padding: 16px 32px;
  background: var(--bg);
  font-family: var(--ff-display); font-size: 0.72rem;
  color: var(--text-muted);
  display: flex; justify-content: space-between;
}}
.card-footer a {{ color: var(--accent); }}
</style>
</head>
<body>
<div class="card">
  <div class="card-header">
    <div class="player-name">{u}</div>
    <div class="player-stats">
      <span><strong>{profile['clips_analyzed']}</strong> clips analyzed</span>
      <span><strong>{len(profile['badges'])}</strong> badge types</span>
      <span><strong>{profile['total_shots']}</strong> total shots</span>
    </div>
  </div>

  <div class="card-section">
    <div class="section-label">Skill Profile</div>
    {skill_bars}
  </div>

  <div class="card-section">
    <div class="section-label">Courtana Badges</div>
    <div class="pills">
      {badge_pills if badge_pills else '<span style="font-size:0.82rem; color:var(--text-muted)">No badge data available for this player</span>'}
    </div>
  </div>

  <div class="card-section">
    <div class="section-label">Brands Detected</div>
    <div class="pills">
      {brand_pills if brand_pills else '<span style="font-size:0.82rem; color:var(--text-muted)">No brands detected yet</span>'}
    </div>
  </div>

  {"<div class='card-section'><div class='section-label'>Top Clips</div><div class='clips-grid'>" + clips_html + "</div></div>" if clips_html else ""}

  <div class="card-footer">
    <span>Generated {datetime.now().strftime('%b %d, %Y')} by Pickle DaaS</span>
    <a href="mailto:bill@courtana.com">bill@courtana.com</a>
  </div>
</div>
</body>
</html>"""


def main():
    parser = argparse.ArgumentParser(description="Generate player shareable cards")
    parser.add_argument("--player", help="Generate card for a specific player only")
    args = parser.parse_args()

    Path(OUTPUT_DIR).mkdir(parents=True, exist_ok=True)

    print("Loading ground truth...")
    player_clips, player_badges = load_ground_truth()
    print(f"  {len(player_clips)} players in ground truth")

    print("Loading analyses...")
    analyses = load_analyses()
    print(f"  {len(analyses)} analyzed clips loaded")

    players_to_process = [args.player] if args.player else list(player_clips.keys())

    generated = 0
    for username in players_to_process:
        if username == "unknown":
            continue
        clips = player_clips.get(username, [])
        badges = player_badges.get(username, {})

        profile = aggregate_player(username, clips, analyses, badges)
        if profile["clips_analyzed"] == 0:
            continue

        html = generate_card_html(profile)
        safe_name = username.lower().replace(" ", "-")
        out_path = Path(OUTPUT_DIR) / f"{safe_name}.html"
        out_path.write_text(html)

        # Also save JSON profile
        json_path = Path(OUTPUT_DIR) / f"{safe_name}.json"
        json_path.write_text(json.dumps(profile, indent=2, default=str))

        print(f"  {username}: {profile['clips_analyzed']} clips, {len(profile['badges'])} badges → {out_path}")
        generated += 1

    print(f"\nGenerated {generated} player cards in {OUTPUT_DIR}/")


if __name__ == "__main__":
    main()

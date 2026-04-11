#!/usr/bin/env python3
"""
Pickle DaaS Deliverable Generator
Produces: creative-badges.json, creative-badges.html, leaderboards.html, brand-report-joola.html
"""

import json
import os
from collections import Counter, defaultdict
from datetime import datetime

OUTPUT_DIR = "output"

# ── Load corpus ──────────────────────────────────────────────────────────
with open(os.path.join(OUTPUT_DIR, "enriched-corpus.json")) as f:
    clips = json.load(f)

print(f"Loaded {len(clips)} clips")

# ── Shared HTML scaffolding ──────────────────────────────────────────────

FONTS_LINK = '<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin><link href="https://fonts.googleapis.com/css2?family=Bricolage+Grotesque:opsz,wght@12..96,400;12..96,600;12..96,700&family=Literata:opsz,wght@7..72,400;7..72,500;7..72,600&display=swap" rel="stylesheet">'

BASE_CSS = """
:root {
    --bg: oklch(97% 0.008 240);
    --bg-card: oklch(99% 0.004 240);
    --accent: oklch(52% 0.185 250);
    --accent-light: oklch(92% 0.04 250);
    --text: oklch(18% 0.015 240);
    --text-muted: oklch(45% 0.02 240);
    --border: oklch(88% 0.015 240);
    --gold: oklch(75% 0.15 85);
    --silver: oklch(70% 0.02 240);
    --bronze: oklch(65% 0.1 55);
    --green: oklch(55% 0.17 150);
    --red: oklch(55% 0.2 25);
}
*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
body {
    font-family: 'Literata', Georgia, serif;
    background: var(--bg);
    color: var(--text);
    line-height: 1.6;
    padding: 2rem;
    max-width: 1200px;
    margin: 0 auto;
}
h1, h2, h3, h4 {
    font-family: 'Bricolage Grotesque', system-ui, sans-serif;
    line-height: 1.2;
}
h1 { font-size: 2.2rem; font-weight: 700; margin-bottom: 0.5rem; }
h2 { font-size: 1.5rem; font-weight: 600; margin: 2rem 0 1rem; color: var(--accent); }
h3 { font-size: 1.15rem; font-weight: 600; margin-bottom: 0.5rem; }
.subtitle { color: var(--text-muted); font-size: 1.05rem; margin-bottom: 2rem; }
.card {
    background: var(--bg-card);
    border: 1px solid var(--border);
    border-radius: 12px;
    padding: 1.25rem;
    margin-bottom: 1rem;
    transition: box-shadow 0.2s;
}
.card:hover { box-shadow: 0 4px 16px oklch(18% 0.015 240 / 0.08); }
.grid { display: grid; gap: 1rem; }
.grid-2 { grid-template-columns: repeat(auto-fill, minmax(340px, 1fr)); }
.grid-3 { grid-template-columns: repeat(auto-fill, minmax(260px, 1fr)); }
.badge-pill {
    display: inline-block;
    padding: 0.2rem 0.65rem;
    border-radius: 99px;
    font-size: 0.8rem;
    font-weight: 500;
    font-family: 'Bricolage Grotesque', system-ui, sans-serif;
}
.accent-pill { background: var(--accent-light); color: var(--accent); }
.stat { font-size: 2rem; font-weight: 700; font-family: 'Bricolage Grotesque', system-ui, sans-serif; color: var(--accent); }
.stat-label { font-size: 0.85rem; color: var(--text-muted); }
.stat-row { display: flex; gap: 2rem; flex-wrap: wrap; margin-bottom: 1.5rem; }
.stat-box { text-align: center; }
table { width: 100%; border-collapse: collapse; margin: 1rem 0; }
th, td { text-align: left; padding: 0.6rem 0.8rem; border-bottom: 1px solid var(--border); }
th { font-family: 'Bricolage Grotesque', system-ui, sans-serif; font-weight: 600; font-size: 0.85rem; color: var(--text-muted); text-transform: uppercase; letter-spacing: 0.05em; }
.thumb { width: 120px; height: 68px; border-radius: 6px; object-fit: cover; background: var(--border); }
.thumb-placeholder { width: 120px; height: 68px; border-radius: 6px; background: var(--accent-light); display: flex; align-items: center; justify-content: center; font-size: 1.5rem; }
a { color: var(--accent); text-decoration: none; }
a:hover { text-decoration: underline; }
.footer {
    margin-top: 3rem;
    padding-top: 1.5rem;
    border-top: 1px solid var(--border);
    text-align: center;
    font-size: 0.85rem;
    color: var(--text-muted);
}
.bar-bg { background: var(--accent-light); border-radius: 4px; height: 22px; position: relative; overflow: hidden; }
.bar-fill { background: var(--accent); height: 100%; border-radius: 4px; min-width: 2px; }
.bar-label { position: absolute; right: 6px; top: 2px; font-size: 0.75rem; font-weight: 600; color: var(--text); }
.rank-num { font-family: 'Bricolage Grotesque', system-ui, sans-serif; font-weight: 700; font-size: 1.3rem; width: 2rem; }
.gold { color: var(--gold); }
.silver { color: var(--silver); }
.bronze { color: var(--bronze); }
"""

FOOTER_HTML = """
<div class="footer">
    Powered by <strong>Pickle DaaS</strong> &middot; bill@courtana.com<br>
    <span style="font-size:0.78rem;">Generated {date}</span>
</div>
""".format(date=datetime.now().strftime("%B %d, %Y"))


def html_page(title, body_html):
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{title}</title>
{FONTS_LINK}
<style>{BASE_CSS}</style>
</head>
<body>
{body_html}
{FOOTER_HTML}
</body>
</html>"""


# ── Helper: Build per-player stats ──────────────────────────────────────

def build_player_stats():
    stats = defaultdict(lambda: {
        "clips": [], "qualities": [], "virals": [], "watches": [],
        "brands": set(), "arcs": set(), "shots": Counter(),
        "brand_list": []
    })
    for c in clips:
        p = c["player"]
        stats[p]["clips"].append(c)
        stats[p]["qualities"].append(c["quality"])
        stats[p]["virals"].append(c["viral"])
        stats[p]["watches"].append(c["watchability"])
        stats[p]["brands"].update(set(c["brands"]))
        stats[p]["brand_list"].extend(c["brands"])
        stats[p]["arcs"].add(c["arc"])
        stats[p]["shots"][c["dominant_shot"]] += 1
    return stats

player_stats = build_player_stats()


# ══════════════════════════════════════════════════════════════════════════
# DELIVERABLE 1: Creative Badge Discovery
# ══════════════════════════════════════════════════════════════════════════

def discover_badges():
    badges = []

    # 1. Highlight Factory — 5+ clips rated quality >= 7
    for p, s in player_stats.items():
        hq = [c for c in s["clips"] if c["quality"] >= 7]
        if len(hq) >= 5:
            badges.append({"badge": "Highlight Factory", "player": p, "clip_count": len(hq),
                           "criteria": "5+ clips with quality >= 7", "clips": [c["uuid"] for c in hq]})

    # 2. Brand Magnet — appeared with 3+ different brands
    for p, s in player_stats.items():
        if len(s["brands"]) >= 3:
            badges.append({"badge": "Brand Magnet", "player": p, "clip_count": len(s["clips"]),
                           "criteria": "Featured alongside 3+ unique brands",
                           "brands": sorted(s["brands"]), "brand_count": len(s["brands"])})

    # 3. Dink Master — dominant_shot = dink in 10+ clips
    for p, s in player_stats.items():
        dc = s["shots"].get("dink", 0)
        if dc >= 10:
            badges.append({"badge": "Dink Master", "player": p, "clip_count": dc,
                           "criteria": "Dominant shot is dink in 10+ clips"})

    # 4. The Grinder — 10+ grind_rally arc clips
    for p, s in player_stats.items():
        gc = sum(1 for c in s["clips"] if c["arc"] == "grind_rally")
        if gc >= 10:
            badges.append({"badge": "The Grinder", "player": p, "clip_count": gc,
                           "criteria": "10+ clips with grind_rally arc"})

    # 5. Viral Sensation — any clip with viral >= 7
    for p, s in player_stats.items():
        vc = [c for c in s["clips"] if c["viral"] >= 7]
        if vc:
            badges.append({"badge": "Viral Sensation", "player": p, "clip_count": len(vc),
                           "criteria": "At least 1 clip with viral score >= 7",
                           "clips": [c["uuid"] for c in vc]})

    # 6. Drive Specialist — dominant_shot = drive in 3+ clips
    for p, s in player_stats.items():
        dc = s["shots"].get("drive", 0)
        if dc >= 3:
            badges.append({"badge": "Drive Specialist", "player": p, "clip_count": dc,
                           "criteria": "Dominant shot is drive in 3+ clips"})

    # 7. Camera Magnet — 15+ total clips
    for p, s in player_stats.items():
        if len(s["clips"]) >= 15:
            badges.append({"badge": "Camera Magnet", "player": p, "clip_count": len(s["clips"]),
                           "criteria": "Appeared in 15+ clips"})

    # 8. Arc Chameleon — appeared in 3+ different story arcs
    for p, s in player_stats.items():
        real_arcs = {a for a in s["arcs"] if a}
        if len(real_arcs) >= 3:
            badges.append({"badge": "Arc Chameleon", "player": p, "clip_count": len(s["clips"]),
                           "criteria": "Featured in 3+ different story arcs",
                           "arcs": sorted(real_arcs)})

    # 9. JOOLA Ambassador — appeared in 5+ clips with JOOLA
    for p, s in player_stats.items():
        jc = sum(1 for c in s["clips"] if "JOOLA" in c["brands"])
        if jc >= 5:
            badges.append({"badge": "JOOLA Ambassador", "player": p, "clip_count": jc,
                           "criteria": "Featured in 5+ clips containing JOOLA branding"})

    # 10. Watchability King — average watchability >= 5.5 across 8+ clips (sustained audience engagement)
    for p, s in player_stats.items():
        if len(s["clips"]) >= 8 and sum(s["watches"]) / len(s["watches"]) >= 5.5:
            avg = round(sum(s["watches"]) / len(s["watches"]), 1)
            badges.append({"badge": "Watchability King", "player": p, "clip_count": len(s["clips"]),
                           "criteria": f"Average watchability >= 5.5 across 8+ clips (avg: {avg})"})

    # 11. Volley Sniper — dominant_shot = volley in 2+ clips
    for p, s in player_stats.items():
        vc = s["shots"].get("volley", 0)
        if vc >= 2:
            badges.append({"badge": "Volley Sniper", "player": p, "clip_count": vc,
                           "criteria": "Dominant shot is volley in 2+ clips"})

    # 12. Pure Fun Vibes — 2+ clips in pure_fun arc
    for p, s in player_stats.items():
        fc = sum(1 for c in s["clips"] if c["arc"] == "pure_fun")
        if fc >= 2:
            badges.append({"badge": "Pure Fun Vibes", "player": p, "clip_count": fc,
                           "criteria": "2+ clips with pure_fun arc"})

    # 13. Error Analyst — 2+ error_highlight clips (learning from mistakes)
    for p, s in player_stats.items():
        ec = sum(1 for c in s["clips"] if c["arc"] == "error_highlight")
        if ec >= 2:
            badges.append({"badge": "Error Analyst", "player": p, "clip_count": ec,
                           "criteria": "2+ clips analyzing errors (error_highlight arc)"})

    # 14. Athletic Freak — any athletic_highlight clip with quality >= 7
    for p, s in player_stats.items():
        ac = [c for c in s["clips"] if c["arc"] == "athletic_highlight" and c["quality"] >= 7]
        if ac:
            badges.append({"badge": "Athletic Freak", "player": p, "clip_count": len(ac),
                           "criteria": "Athletic highlight clip with quality >= 7",
                           "clips": [c["uuid"] for c in ac]})

    # 15. Consistency Machine — all clips quality >= 6 with 5+ clips
    for p, s in player_stats.items():
        if len(s["clips"]) >= 5 and all(c["quality"] >= 6 for c in s["clips"]):
            badges.append({"badge": "Consistency Machine", "player": p, "clip_count": len(s["clips"]),
                           "criteria": "All clips rated quality >= 6 with 5+ clips"})

    # 16. Nike Warrior — appeared with Nike branding 3+ times
    for p, s in player_stats.items():
        nc = sum(1 for c in s["clips"] if "Nike" in c["brands"])
        if nc >= 3:
            badges.append({"badge": "Nike Warrior", "player": p, "clip_count": nc,
                           "criteria": "Featured in 3+ clips with Nike branding"})

    # 17. Multi-Brand MVP — appeared with 5+ unique brands
    for p, s in player_stats.items():
        if len(s["brands"]) >= 5:
            badges.append({"badge": "Multi-Brand MVP", "player": p, "clip_count": len(s["clips"]),
                           "criteria": "Featured alongside 5+ unique brands",
                           "brands": sorted(s["brands"]), "brand_count": len(s["brands"])})

    # 18. Shot Variety Pack — used 3+ different dominant shots
    for p, s in player_stats.items():
        real_shots = {sh for sh in s["shots"] if sh and sh != "other"}
        if len(real_shots) >= 3:
            badges.append({"badge": "Shot Variety Pack", "player": p, "clip_count": len(s["clips"]),
                           "criteria": "3+ different dominant shot types across clips",
                           "shots": sorted(real_shots)})

    # 19. Clutch Performer — any clutch_moment clip
    for p, s in player_stats.items():
        cc = [c for c in s["clips"] if c["arc"] == "clutch_moment"]
        if cc:
            badges.append({"badge": "Clutch Performer", "player": p, "clip_count": len(cc),
                           "criteria": "Featured in a clutch_moment arc clip"})

    # 20. Triple Threat Score — quality + viral + watchability >= 22 on any clip
    for p, s in player_stats.items():
        tt = [c for c in s["clips"] if c["quality"] + c["viral"] + c["watchability"] >= 22]
        if tt:
            best = max(tt, key=lambda c: c["quality"] + c["viral"] + c["watchability"])
            score = best["quality"] + best["viral"] + best["watchability"]
            badges.append({"badge": "Triple Threat", "player": p, "clip_count": len(tt),
                           "criteria": f"Quality + Viral + Watchability >= 22 on a single clip (best: {score})",
                           "clips": [c["uuid"] for c in tt]})

    return badges


all_badges = discover_badges()
print(f"Discovered {len(all_badges)} badge awards across {len(set(b['badge'] for b in all_badges))} badge types")

# Save JSON
badge_json_path = os.path.join(OUTPUT_DIR, "creative-badges.json")
with open(badge_json_path, "w") as f:
    json.dump(all_badges, f, indent=2, default=list)
print(f"Wrote {badge_json_path}")

# ── Badge HTML ───────────────────────────────────────────────────────────

BADGE_ICONS = {
    "Highlight Factory": "&#9889;",
    "Brand Magnet": "&#129522;",
    "Dink Master": "&#127955;",
    "The Grinder": "&#128170;",
    "Viral Sensation": "&#128293;",
    "Drive Specialist": "&#127937;",
    "Camera Magnet": "&#127909;",
    "Arc Chameleon": "&#129430;",
    "JOOLA Ambassador": "&#127941;",
    "Watchability King": "&#128081;",
    "Volley Sniper": "&#127919;",
    "Pure Fun Vibes": "&#127881;",
    "Error Analyst": "&#128300;",
    "Athletic Freak": "&#9889;",
    "Consistency Machine": "&#128736;",
    "Nike Warrior": "&#128095;",
    "Multi-Brand MVP": "&#127775;",
    "Shot Variety Pack": "&#127922;",
    "Clutch Performer": "&#129348;",
    "Triple Threat": "&#128142;",
}

def badge_html():
    # Group badges by type
    by_type = defaultdict(list)
    for b in all_badges:
        by_type[b["badge"]].append(b)

    badge_types = sorted(by_type.keys())
    total_awards = len(all_badges)
    unique_players = len(set(b["player"] for b in all_badges))

    cards_html = ""
    for bt in badge_types:
        awards = by_type[bt]
        icon = BADGE_ICONS.get(bt, "&#127942;")
        criteria = awards[0]["criteria"].split(" (")[0]  # strip specifics
        players_list = ", ".join(sorted(set(a["player"] for a in awards)))
        total_clips = sum(a["clip_count"] for a in awards)

        cards_html += f"""
        <div class="card">
            <div style="display:flex;align-items:center;gap:0.75rem;margin-bottom:0.6rem;">
                <span style="font-size:2rem;">{icon}</span>
                <div>
                    <h3 style="margin:0;">{bt}</h3>
                    <span style="font-size:0.85rem;color:var(--text-muted);">{criteria}</span>
                </div>
            </div>
            <div style="display:flex;gap:1.5rem;margin-bottom:0.5rem;">
                <div><span style="font-weight:600;color:var(--accent);">{len(awards)}</span> <span style="font-size:0.82rem;color:var(--text-muted);">earners</span></div>
                <div><span style="font-weight:600;color:var(--accent);">{total_clips}</span> <span style="font-size:0.82rem;color:var(--text-muted);">qualifying clips</span></div>
            </div>
            <div style="font-size:0.9rem;"><strong>Earned by:</strong> {players_list}</div>
        </div>"""

    body = f"""
    <h1>Creative Badge Discovery</h1>
    <p class="subtitle">20 data-driven badges invented from 90 clips across the Pickle DaaS corpus</p>

    <div class="stat-row">
        <div class="stat-box"><div class="stat">{len(badge_types)}</div><div class="stat-label">Badge Types</div></div>
        <div class="stat-box"><div class="stat">{total_awards}</div><div class="stat-label">Total Awards</div></div>
        <div class="stat-box"><div class="stat">{unique_players}</div><div class="stat-label">Unique Earners</div></div>
        <div class="stat-box"><div class="stat">90</div><div class="stat-label">Clips Analyzed</div></div>
    </div>

    <h2>All Badges</h2>
    <div class="grid grid-2">
    {cards_html}
    </div>

    <h2>Leaderboard: Most Badges Per Player</h2>
    <table>
    <tr><th>#</th><th>Player</th><th>Badges Earned</th><th>Badge Types</th></tr>
    """

    player_badge_count = Counter()
    player_badge_types = defaultdict(set)
    for b in all_badges:
        player_badge_count[b["player"]] += 1
        player_badge_types[b["player"]].add(b["badge"])

    for i, (player, count) in enumerate(player_badge_count.most_common()):
        rank_class = ["gold", "silver", "bronze"][i] if i < 3 else ""
        types = ", ".join(sorted(player_badge_types[player]))
        body += f'<tr><td class="rank-num {rank_class}">{i+1}</td><td><strong>{player}</strong></td><td>{count}</td><td style="font-size:0.85rem;">{types}</td></tr>\n'

    body += "</table>"
    return html_page("Creative Badge Discovery | Pickle DaaS", body)

badges_html_path = os.path.join(OUTPUT_DIR, "creative-badges.html")
with open(badges_html_path, "w") as f:
    f.write(badge_html())
print(f"Wrote {badges_html_path}")


# ══════════════════════════════════════════════════════════════════════════
# DELIVERABLE 2: Clip Rankings & Leaderboards
# ══════════════════════════════════════════════════════════════════════════

def get_thumbnail_url(clip):
    """Generate thumbnail URL from clip video URL."""
    return clip["url"].replace(".mp4", "_thumbnail.jpg") if clip.get("url") else ""

def leaderboards_html():
    # ── Top 10 Highest Quality Clips ─────────────────────
    quality_sorted = sorted(clips, key=lambda c: (c["quality"], c["viral"], c["watchability"]), reverse=True)[:10]

    quality_rows = ""
    for i, c in enumerate(quality_sorted):
        rank_class = ["gold", "silver", "bronze"][i] if i < 3 else ""
        brands_str = ", ".join(sorted(set(c["brands"]))) or "None"
        quality_rows += f"""
        <tr>
            <td class="rank-num {rank_class}">{i+1}</td>
            <td><a href="{c['url']}" target="_blank"><div class="thumb-placeholder">&#9654;</div></a></td>
            <td><strong>{c['quality']}</strong></td>
            <td>{c.get('viral', '?')}</td>
            <td>{c.get('watchability', '?')}</td>
            <td><span class="badge-pill accent-pill">{c['arc'] or 'N/A'}</span></td>
            <td style="font-size:0.85rem;">{brands_str}</td>
            <td>{c['player']}</td>
        </tr>"""

    # ── Top 10 Most Brand-Dense Clips ────────────────────
    brand_sorted = sorted(clips, key=lambda c: len(set(c["brands"])), reverse=True)[:10]

    brand_rows = ""
    for i, c in enumerate(brand_sorted):
        rank_class = ["gold", "silver", "bronze"][i] if i < 3 else ""
        unique_brands = sorted(set(c["brands"]))
        brand_rows += f"""
        <tr>
            <td class="rank-num {rank_class}">{i+1}</td>
            <td><a href="{c['url']}" target="_blank"><div class="thumb-placeholder">&#9654;</div></a></td>
            <td><strong>{len(unique_brands)}</strong></td>
            <td style="font-size:0.85rem;">{', '.join(unique_brands)}</td>
            <td>{c['quality']}</td>
            <td><span class="badge-pill accent-pill">{c['arc'] or 'N/A'}</span></td>
            <td>{c['player']}</td>
        </tr>"""

    # ── Player Leaderboard ───────────────────────────────
    player_badge_count = Counter()
    for b in all_badges:
        player_badge_count[b["player"]] += 1

    player_rows_data = []
    for p, s in player_stats.items():
        avg_q = round(sum(s["qualities"]) / len(s["qualities"]), 1)
        player_rows_data.append({
            "player": p, "avg_quality": avg_q, "clip_count": len(s["clips"]),
            "badges": player_badge_count.get(p, 0), "unique_brands": len(s["brands"]),
        })
    player_rows_data.sort(key=lambda x: (x["avg_quality"], x["clip_count"]), reverse=True)

    player_rows = ""
    for i, pr in enumerate(player_rows_data):
        rank_class = ["gold", "silver", "bronze"][i] if i < 3 else ""
        player_rows += f"""
        <tr>
            <td class="rank-num {rank_class}">{i+1}</td>
            <td><strong>{pr['player']}</strong></td>
            <td>{pr['avg_quality']}</td>
            <td>{pr['clip_count']}</td>
            <td>{pr['badges']}</td>
            <td>{pr['unique_brands']}</td>
        </tr>"""

    # ── Arc Distribution ─────────────────────────────────
    arc_counts = Counter(c["arc"] for c in clips if c["arc"])
    max_arc = max(arc_counts.values()) if arc_counts else 1

    arc_bars = ""
    for arc, count in sorted(arc_counts.items(), key=lambda x: -x[1]):
        pct = round(count / max_arc * 100)
        arc_bars += f"""
        <div style="display:flex;align-items:center;gap:0.75rem;margin-bottom:0.6rem;">
            <div style="width:160px;font-weight:500;font-size:0.9rem;">{arc}</div>
            <div class="bar-bg" style="flex:1;">
                <div class="bar-fill" style="width:{pct}%;"></div>
                <div class="bar-label">{count} clips</div>
            </div>
        </div>"""

    # ── Shot Distribution ────────────────────────────────
    shot_counts = Counter(c["dominant_shot"] for c in clips if c.get("dominant_shot"))
    max_shot = max(shot_counts.values()) if shot_counts else 1

    shot_bars = ""
    for shot, count in sorted(shot_counts.items(), key=lambda x: -x[1]):
        pct = round(count / max_shot * 100)
        shot_bars += f"""
        <div style="display:flex;align-items:center;gap:0.75rem;margin-bottom:0.6rem;">
            <div style="width:160px;font-weight:500;font-size:0.9rem;">{shot or 'unknown'}</div>
            <div class="bar-bg" style="flex:1;">
                <div class="bar-fill" style="width:{pct}%;"></div>
                <div class="bar-label">{count}</div>
            </div>
        </div>"""

    body = f"""
    <h1>Clip Rankings & Leaderboards</h1>
    <p class="subtitle">The best clips, players, and patterns from 90 analyzed highlights</p>

    <div class="stat-row">
        <div class="stat-box"><div class="stat">90</div><div class="stat-label">Total Clips</div></div>
        <div class="stat-box"><div class="stat">{round(sum(c['quality'] for c in clips)/len(clips), 1)}</div><div class="stat-label">Avg Quality</div></div>
        <div class="stat-box"><div class="stat">{len(player_stats)}</div><div class="stat-label">Players</div></div>
        <div class="stat-box"><div class="stat">{len(arc_counts)}</div><div class="stat-label">Story Arcs</div></div>
    </div>

    <h2>Top 10 Highest Quality Clips</h2>
    <div style="overflow-x:auto;">
    <table>
    <tr><th>#</th><th>Clip</th><th>Quality</th><th>Viral</th><th>Watch</th><th>Arc</th><th>Brands</th><th>Player</th></tr>
    {quality_rows}
    </table>
    </div>

    <h2>Top 10 Most Brand-Dense Clips</h2>
    <div style="overflow-x:auto;">
    <table>
    <tr><th>#</th><th>Clip</th><th>Brands</th><th>Brand Names</th><th>Quality</th><th>Arc</th><th>Player</th></tr>
    {brand_rows}
    </table>
    </div>

    <h2>Player Leaderboard</h2>
    <div style="overflow-x:auto;">
    <table>
    <tr><th>#</th><th>Player</th><th>Avg Quality</th><th>Clips</th><th>Badges</th><th>Unique Brands</th></tr>
    {player_rows}
    </table>
    </div>

    <h2>Arc Distribution</h2>
    <div class="card" style="padding:1.5rem;">
    {arc_bars}
    </div>

    <h2>Shot Distribution</h2>
    <div class="card" style="padding:1.5rem;">
    {shot_bars}
    </div>
    """

    return html_page("Clip Rankings & Leaderboards | Pickle DaaS", body)

leaderboards_path = os.path.join(OUTPUT_DIR, "leaderboards.html")
with open(leaderboards_path, "w") as f:
    f.write(leaderboards_html())
print(f"Wrote {leaderboards_path}")


# ══════════════════════════════════════════════════════════════════════════
# DELIVERABLE 3: Brand Intelligence Report for JOOLA
# ══════════════════════════════════════════════════════════════════════════

def brand_report_joola_html():
    joola_clips = [c for c in clips if "JOOLA" in c["brands"]]
    non_joola_clips = [c for c in clips if "JOOLA" not in c["brands"]]

    total = len(clips)
    joola_count = len(joola_clips)
    market_share = round(joola_count / total * 100, 1)

    # JOOLA player associations
    joola_players = Counter(c["player"] for c in joola_clips)

    # JOOLA arc distribution
    joola_arcs = Counter(c["arc"] for c in joola_clips if c["arc"])

    # JOOLA avg quality
    joola_avg_q = round(sum(c["quality"] for c in joola_clips) / len(joola_clips), 1) if joola_clips else 0
    overall_avg_q = round(sum(c["quality"] for c in clips) / len(clips), 1)

    # Competitor comparison
    all_brand_counts = Counter()
    for c in clips:
        for b in set(c["brands"]):
            all_brand_counts[b] += 1

    max_brand_count = max(all_brand_counts.values())

    comp_rows = ""
    for i, (brand, count) in enumerate(all_brand_counts.most_common()):
        pct = round(count / total * 100, 1)
        is_joola = brand == "JOOLA"
        style = 'font-weight:700;color:var(--accent);' if is_joola else ''
        bar_color = "var(--accent)" if is_joola else "var(--accent-light)"
        bar_width = round(count / max_brand_count * 100)
        comp_rows += f"""
        <tr style="{style}">
            <td>{i+1}</td>
            <td>{'&#127941; ' if is_joola else ''}{brand}</td>
            <td>{count}</td>
            <td>{pct}%</td>
            <td style="width:200px;">
                <div class="bar-bg" style="height:16px;">
                    <div class="bar-fill" style="width:{bar_width}%;background:{bar_color};"></div>
                </div>
            </td>
        </tr>"""

    # Player association table
    player_rows = ""
    for p, count in joola_players.most_common():
        total_player_clips = len(player_stats[p]["clips"])
        pct = round(count / total_player_clips * 100, 1)
        player_rows += f"<tr><td>{p}</td><td>{count}</td><td>{total_player_clips}</td><td>{pct}%</td></tr>\n"

    # Arc distribution
    all_arcs = Counter(c["arc"] for c in clips if c["arc"])
    arc_rows = ""
    for arc in sorted(all_arcs.keys(), key=lambda a: -all_arcs[a]):
        total_arc = all_arcs[arc]
        joola_arc = joola_arcs.get(arc, 0)
        joola_pct = round(joola_arc / total_arc * 100, 1) if total_arc else 0
        bar_width = round(joola_pct)
        arc_rows += f"""
        <tr>
            <td>{arc}</td>
            <td>{joola_arc}</td>
            <td>{total_arc}</td>
            <td>{joola_pct}%</td>
            <td style="width:180px;">
                <div class="bar-bg" style="height:16px;">
                    <div class="bar-fill" style="width:{bar_width}%;"></div>
                </div>
            </td>
        </tr>"""

    # Whitespace analysis
    whitespace_items = []
    for arc in all_arcs:
        if joola_arcs.get(arc, 0) == 0:
            whitespace_items.append(f"Arc: <strong>{arc}</strong> ({all_arcs[arc]} clips, 0 with JOOLA)")

    for p, s in player_stats.items():
        if p == "unknown":
            continue
        joola_for_player = sum(1 for c in s["clips"] if "JOOLA" in c["brands"])
        if joola_for_player == 0 and len(s["clips"]) >= 3:
            whitespace_items.append(f"Player: <strong>{p}</strong> ({len(s['clips'])} clips, 0 with JOOLA)")

    whitespace_html = ""
    if whitespace_items:
        for item in whitespace_items:
            whitespace_html += f'<div class="card" style="display:flex;align-items:center;gap:0.75rem;padding:0.8rem 1rem;"><span style="color:var(--red);font-size:1.2rem;">&#9888;</span> {item}</div>\n'
    else:
        whitespace_html = '<div class="card" style="padding:1rem;">JOOLA has comprehensive presence across all arcs and active players. No significant whitespace detected.</div>'

    # JOOLA top clips
    joola_top = sorted(joola_clips, key=lambda c: c["quality"], reverse=True)[:5]
    top_clips_html = ""
    for i, c in enumerate(joola_top):
        top_clips_html += f"""
        <tr>
            <td>{i+1}</td>
            <td><a href="{c['url']}" target="_blank">&#9654; Watch</a></td>
            <td>{c['quality']}</td>
            <td><span class="badge-pill accent-pill">{c['arc'] or 'N/A'}</span></td>
            <td>{c['player']}</td>
            <td style="font-size:0.85rem;">{c.get('social_caption', '')[:60]}...</td>
        </tr>"""

    body = f"""
    <div style="display:flex;justify-content:space-between;align-items:flex-start;flex-wrap:wrap;gap:1rem;">
        <div>
            <h1>JOOLA Brand Intelligence Report</h1>
            <p class="subtitle">Market presence, player associations, and whitespace analysis</p>
        </div>
        <div class="card" style="text-align:center;padding:1rem 1.5rem;margin:0;">
            <div style="font-size:0.8rem;color:var(--text-muted);text-transform:uppercase;letter-spacing:0.08em;">Sample Deliverable</div>
            <div style="font-size:0.9rem;font-weight:500;color:var(--accent);margin-top:0.25rem;">Pickle DaaS Monthly Report</div>
        </div>
    </div>

    <div class="stat-row" style="margin-top:1.5rem;">
        <div class="stat-box"><div class="stat">{joola_count}</div><div class="stat-label">JOOLA Clips</div></div>
        <div class="stat-box"><div class="stat">{market_share}%</div><div class="stat-label">Market Share</div></div>
        <div class="stat-box"><div class="stat">{joola_avg_q}</div><div class="stat-label">Avg Quality</div></div>
        <div class="stat-box"><div class="stat">{len(joola_players)}</div><div class="stat-label">Associated Players</div></div>
        <div class="stat-box"><div class="stat">{len(joola_arcs)}</div><div class="stat-label">Arc Coverage</div></div>
    </div>

    <div class="card" style="background:var(--accent-light);border-color:var(--accent);padding:1.25rem;margin:1.5rem 0;">
        <h3 style="color:var(--accent);margin-bottom:0.4rem;">Executive Summary</h3>
        <p style="font-size:0.95rem;">JOOLA dominates the Pickle DaaS highlight corpus with <strong>{market_share}% market share</strong> across {joola_count} of 90 analyzed clips. The brand appears across {len(joola_arcs)} of {len(all_arcs)} story arcs and is associated with {len(joola_players)} unique players. JOOLA clips average a quality score of {joola_avg_q} vs. the corpus average of {overall_avg_q}.</p>
    </div>

    <h2>Competitive Landscape</h2>
    <p style="margin-bottom:1rem;color:var(--text-muted);">Brand appearance frequency across all 90 clips</p>
    <div style="overflow-x:auto;">
    <table>
    <tr><th>#</th><th>Brand</th><th>Clips</th><th>Share</th><th>Distribution</th></tr>
    {comp_rows}
    </table>
    </div>

    <h2>Player Associations</h2>
    <p style="margin-bottom:1rem;color:var(--text-muted);">Players most frequently seen with JOOLA equipment or branding</p>
    <div style="overflow-x:auto;">
    <table>
    <tr><th>Player</th><th>JOOLA Clips</th><th>Total Clips</th><th>JOOLA %</th></tr>
    {player_rows}
    </table>
    </div>

    <h2>Story Arc Penetration</h2>
    <p style="margin-bottom:1rem;color:var(--text-muted);">JOOLA presence across different highlight narrative types</p>
    <div style="overflow-x:auto;">
    <table>
    <tr><th>Arc</th><th>JOOLA Clips</th><th>Total Clips</th><th>JOOLA %</th><th>Penetration</th></tr>
    {arc_rows}
    </table>
    </div>

    <h2>Top JOOLA Clips</h2>
    <p style="margin-bottom:1rem;color:var(--text-muted);">Highest quality clips featuring JOOLA branding</p>
    <div style="overflow-x:auto;">
    <table>
    <tr><th>#</th><th>Watch</th><th>Quality</th><th>Arc</th><th>Player</th><th>Caption</th></tr>
    {top_clips_html}
    </table>
    </div>

    <h2>Whitespace Analysis</h2>
    <p style="margin-bottom:1rem;color:var(--text-muted);">Areas where JOOLA has zero or minimal presence -- opportunities for targeted activation</p>
    {whitespace_html}

    <h2 style="margin-top:2.5rem;">What You Get as a Pickle DaaS Subscriber</h2>
    <div class="grid grid-3">
        <div class="card" style="text-align:center;padding:1.5rem;">
            <div style="font-size:2rem;margin-bottom:0.5rem;">&#128202;</div>
            <h3>Monthly Brand Report</h3>
            <p style="font-size:0.88rem;color:var(--text-muted);">Market share, competitor analysis, and trend tracking delivered monthly</p>
        </div>
        <div class="card" style="text-align:center;padding:1.5rem;">
            <div style="font-size:2rem;margin-bottom:0.5rem;">&#127919;</div>
            <h3>Whitespace Alerts</h3>
            <p style="font-size:0.88rem;color:var(--text-muted);">Real-time detection of arcs, players, and venues where your brand is absent</p>
        </div>
        <div class="card" style="text-align:center;padding:1.5rem;">
            <div style="font-size:2rem;margin-bottom:0.5rem;">&#128279;</div>
            <h3>Clip Library Access</h3>
            <p style="font-size:0.88rem;color:var(--text-muted);">Direct CDN links to every clip featuring your brand for social amplification</p>
        </div>
    </div>
    """

    return html_page("JOOLA Brand Intelligence | Pickle DaaS", body)


joola_path = os.path.join(OUTPUT_DIR, "brand-report-joola.html")
with open(joola_path, "w") as f:
    f.write(brand_report_joola_html())
print(f"Wrote {joola_path}")


# ── Final summary ────────────────────────────────────────────────────────
print("\n=== All deliverables generated ===")
for path in [badge_json_path, badges_html_path, leaderboards_path, joola_path]:
    size = os.path.getsize(path)
    print(f"  {path}: {size:,} bytes")

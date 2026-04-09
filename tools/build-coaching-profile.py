#!/usr/bin/env python3
"""
Pickle DaaS — Coaching Profile Builder
=======================================
Aggregates all analysis JSONs for a player into a longitudinal coaching profile.
Computes trend lines, badge frequency, improvement patterns, and generates
an AI-narrated evolution summary. Outputs JSON profile + shareable HTML card.

USAGE:
  python tools/build-coaching-profile.py
  python tools/build-coaching-profile.py --player "PickleBill" --output output/coaching-profile-picklebill.html
  python tools/build-coaching-profile.py --dirs output/batch-30-daas output/picklebill-batch-001

OUTPUT:
  output/coaching-profile-{player}.json   — Raw profile data
  output/coaching-profile-{player}.html   — Shareable HTML card
"""

import os
import sys
import json
import glob
import argparse
import statistics
from datetime import datetime
from pathlib import Path
from collections import Counter

# Optional: Gemini for AI narrative (falls back to template if not available)
try:
    from dotenv import load_dotenv
    load_dotenv(dotenv_path='.env')
except Exception:
    pass

GEMINI_AVAILABLE = False
try:
    import google.generativeai as genai
    if os.environ.get('GEMINI_API_KEY'):
        genai.configure(api_key=os.environ['GEMINI_API_KEY'])
        GEMINI_AVAILABLE = True
except Exception:
    pass


SKILL_DIMENSIONS = [
    ('kitchen_mastery_rating',    'Kitchen Game'),
    ('court_iq_rating',           'Court IQ'),
    ('athleticism_rating',        'Athleticism'),
    ('power_game_rating',         'Power'),
    ('touch_and_feel_rating',     'Touch & Feel'),
    ('creativity_rating',         'Creativity'),
    ('consistency_rating',        'Consistency'),
    ('composure_under_pressure',  'Composure'),
    ('court_coverage_rating',     'Court Coverage'),
    ('paddle_control_rating',     'Paddle Control'),
]

DEFAULT_DIRS = [
    'output/batch-30-daas',
    'output/picklebill-batch-001',
    'output/picklebill-batch-20260410',
]


def load_analyses(directories):
    """Load all valid analysis JSONs from given directories, sorted by analyzed_at."""
    all_records = []
    for d in directories:
        pattern = os.path.join(d, 'analysis_*.json')
        for filepath in glob.glob(pattern):
            try:
                with open(filepath) as f:
                    data = json.load(f)
                if not data.get('clip_meta') or not data['clip_meta'].get('clip_quality_score'):
                    continue
                data['_filepath'] = filepath
                data['_filename'] = os.path.basename(filepath)
                # Parse timestamp for sorting
                ts_str = data.get('analyzed_at', '')
                data['_sort_ts'] = ts_str if ts_str else filepath  # fallback sort by filename
                all_records.append(data)
            except Exception as e:
                print(f"  WARNING: Could not load {filepath}: {e}")

    all_records.sort(key=lambda x: x['_sort_ts'])
    return all_records


def extract_skill_scores(record):
    """Extract skill dimension scores from a record. Returns dict of dim -> score."""
    si = record.get('skill_indicators', {})
    scores = {}
    for key, _ in SKILL_DIMENSIONS:
        val = si.get(key)
        if isinstance(val, (int, float)) and val > 0:
            scores[key] = float(val)
    return scores


def trend_arrow(before, after):
    """Return ↑ ↓ → based on delta."""
    delta = after - before
    if delta >= 0.5:
        return '↑', delta
    elif delta <= -0.5:
        return '↓', delta
    else:
        return '→', delta


def compute_profile(records, player_name):
    """Compute the full coaching profile from a list of sorted analysis records."""
    n = len(records)
    if n == 0:
        return None

    # Split into first half / second half for trend detection
    mid = max(1, n // 2)
    early_records = records[:mid]
    recent_records = records[mid:] if n > 1 else records

    # --- Skill dimension aggregation ---
    all_scores = {}
    early_scores = {}
    recent_scores = {}

    for dim, _ in SKILL_DIMENSIONS:
        all_vals = [s[dim] for r in records if (s := extract_skill_scores(r)) and dim in s]
        early_vals = [s[dim] for r in early_records if (s := extract_skill_scores(r)) and dim in s]
        recent_vals = [s[dim] for r in recent_records if (s := extract_skill_scores(r)) and dim in s]

        all_scores[dim]    = round(statistics.mean(all_vals), 1)    if all_vals    else None
        early_scores[dim]  = round(statistics.mean(early_vals), 1)  if early_vals  else None
        recent_scores[dim] = round(statistics.mean(recent_vals), 1) if recent_vals else None

    # --- Trend directions ---
    trends = {}
    for dim, label in SKILL_DIMENSIONS:
        e = early_scores.get(dim)
        r = recent_scores.get(dim)
        if e is not None and r is not None:
            arrow, delta = trend_arrow(e, r)
            trends[dim] = {'arrow': arrow, 'delta': round(delta, 1), 'early': e, 'recent': r}
        else:
            trends[dim] = {'arrow': '→', 'delta': 0, 'early': e or 0, 'recent': r or 0}

    # --- Badge frequency ---
    badge_counter = Counter()
    for r in records:
        for b in r.get('badge_intelligence', {}).get('predicted_badges', []):
            badge_counter[b.get('badge_name', '')] += 1
    top_badges = badge_counter.most_common(6)

    # --- Dominant shot types ---
    shot_counter = Counter()
    for r in records:
        ds = r.get('shot_analysis', {}).get('dominant_shot_type')
        if ds:
            shot_counter[ds] += 1
    dominant_shots = shot_counter.most_common(3)

    # --- Improvement opportunities ---
    improvement_counter = Counter()
    for r in records:
        for opp in r.get('skill_indicators', {}).get('improvement_opportunities', []):
            if opp:
                improvement_counter[opp] += 1
    top_improvements = improvement_counter.most_common(5)

    # --- Signature moves (non-null) ---
    signatures = [
        r.get('skill_indicators', {}).get('signature_move_detected')
        for r in records
        if r.get('skill_indicators', {}).get('signature_move_detected')
    ]

    # --- Play style tags ---
    tag_counter = Counter()
    for r in records:
        for tag in r.get('skill_indicators', {}).get('play_style_tags', []):
            tag_counter[tag] += 1
    top_tags = tag_counter.most_common(5)

    # --- DUPR estimate (most recent non-null) ---
    dupr_vals = [
        r.get('daas_signals', {}).get('estimated_player_rating_dupr')
        for r in reversed(records)
        if r.get('daas_signals', {}).get('estimated_player_rating_dupr')
    ]
    dupr_estimate = dupr_vals[0] if dupr_vals else 'Unknown'

    # --- Quality/viral trends ---
    quality_scores  = [r['clip_meta']['clip_quality_score']    for r in records if r.get('clip_meta', {}).get('clip_quality_score')]
    viral_scores    = [r['clip_meta'].get('viral_potential_score', 0) for r in records if r.get('clip_meta')]
    avg_quality     = round(statistics.mean(quality_scores), 1)  if quality_scores  else 0
    avg_viral       = round(statistics.mean(viral_scores), 1)    if viral_scores    else 0

    # --- Story arcs ---
    arc_counter = Counter()
    for r in records:
        arc = r.get('storytelling', {}).get('story_arc')
        if arc:
            arc_counter[arc] += 1
    top_arcs = arc_counter.most_common(3)

    # --- Clip thumbnails (CDN URLs) ---
    thumbnails = []
    for r in sorted(records, key=lambda x: x.get('clip_meta', {}).get('clip_quality_score', 0) or 0, reverse=True)[:3]:
        src = r.get('_source_url', '')
        if src:
            thumb = src.replace('.mp4', '.jpeg')
            clip_id = r['_filename'].split('_')[1][:8] if '_' in r['_filename'] else ''
            quality = r.get('clip_meta', {}).get('clip_quality_score', 0)
            viral   = r.get('clip_meta', {}).get('viral_potential_score', 0)
            caption = r.get('daas_signals', {}).get('clip_summary_one_sentence', '')
            arc     = r.get('storytelling', {}).get('story_arc', 'athletic_highlight')
            thumbnails.append({
                'thumb_url': thumb,
                'clip_id':   clip_id,
                'quality':   quality,
                'viral':     viral,
                'caption':   caption[:80] if caption else '',
                'arc':       arc.replace('_', ' ').title(),
            })

    profile = {
        'player_name':       player_name,
        'generated_at':      datetime.now().isoformat(),
        'total_clips':       n,
        'early_clip_count':  len(early_records),
        'recent_clip_count': len(recent_records),
        'avg_quality':       avg_quality,
        'avg_viral':         avg_viral,
        'dupr_estimate':     dupr_estimate,
        'skill_dimensions':  SKILL_DIMENSIONS,
        'all_scores':        all_scores,
        'early_scores':      early_scores,
        'recent_scores':     recent_scores,
        'trends':            trends,
        'top_badges':        top_badges,
        'dominant_shots':    dominant_shots,
        'top_improvements':  top_improvements,
        'top_tags':          top_tags,
        'signatures':        signatures[:5],
        'top_arcs':          top_arcs,
        'thumbnails':        thumbnails,
        'ai_narrative':      None,  # filled in later
    }

    # Biggest improvement and decline
    profile['biggest_improvement'] = max(
        [(dim, trends[dim]) for dim, _ in SKILL_DIMENSIONS if trends[dim]['delta'] != 0],
        key=lambda x: x[1]['delta'],
        default=(None, {'delta': 0})
    )
    profile['biggest_decline'] = min(
        [(dim, trends[dim]) for dim, _ in SKILL_DIMENSIONS if trends[dim]['delta'] != 0],
        key=lambda x: x[1]['delta'],
        default=(None, {'delta': 0})
    )

    return profile


def generate_ai_narrative(profile):
    """Generate a 3-sentence AI coaching narrative using Gemini."""
    if not GEMINI_AVAILABLE:
        return generate_template_narrative(profile)

    dim_labels = {dim: label for dim, label in profile['skill_dimensions']}
    trends_text = []
    for dim, label in profile['skill_dimensions']:
        t = profile['trends'].get(dim, {})
        if t.get('delta', 0) != 0:
            direction = 'improved' if t['delta'] > 0 else 'declined'
            trends_text.append(f"{label}: {direction} from {t['early']} to {t['recent']}")

    top_badge_names = [b[0] for b in profile['top_badges'][:3]]
    top_improvement = profile['top_improvements'][0][0] if profile['top_improvements'] else 'consistency'
    signature = profile['signatures'][0] if profile['signatures'] else 'patient dink game'

    prompt = f"""You are an expert pickleball coach analyzing a player's evolution across {profile['total_clips']} video clips.

Player summary:
- Estimated DUPR: {profile['dupr_estimate']}
- Average clip quality score: {profile['avg_quality']}/10
- Dominant badges earned: {', '.join(top_badge_names)}
- Signature move: {signature}
- Key skill trends: {'; '.join(trends_text[:5]) if trends_text else 'relatively consistent across clips'}
- Top improvement area: {top_improvement}

Write a 3-sentence coaching observation about this player's evolution. Be specific, reference actual numbers, be encouraging but honest. End with one concrete drill recommendation. Do not use markdown or headers. Just 3 plain sentences."""

    try:
        model = genai.GenerativeModel('gemini-2.5-flash')
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        print(f"  Gemini narrative failed: {e} — using template")
        return generate_template_narrative(profile)


def generate_template_narrative(profile):
    """Fallback template narrative when Gemini is unavailable."""
    clips = profile['total_clips']
    dupr  = profile['dupr_estimate']
    top_badge = profile['top_badges'][0][0] if profile['top_badges'] else 'Kitchen King'

    imp = profile['biggest_improvement']
    if imp[0]:
        dim_label = dict(profile['skill_dimensions']).get(imp[0], imp[0])
        trend = profile['trends'].get(imp[0], {})
        trend_text = f"Most notably, {dim_label} has improved from {trend.get('early', 0)} to {trend.get('recent', 0)} — a clear sign of deliberate practice."
    else:
        trend_text = "The data shows consistent play across all analyzed clips."

    top_opp = profile['top_improvements'][0][0] if profile['top_improvements'] else 'anticipating speed-ups at the kitchen line'

    return (
        f"Across {clips} analyzed clips, this player demonstrates a {dupr} skill profile "
        f"with strong tendencies toward {top_badge.lower()} play patterns. "
        f"{trend_text} "
        f"The primary coaching opportunity is {top_opp} — "
        f"recommended focus: 10-minute speed-up anticipation drills before every session."
    )


def generate_html(profile, player_name, output_path):
    """Generate the shareable coaching profile HTML card."""

    dim_labels = {dim: label for dim, label in profile['skill_dimensions']}

    # Build radar data for Chart.js (6 key dimensions)
    radar_dims = [
        'kitchen_mastery_rating',
        'court_iq_rating',
        'athleticism_rating',
        'power_game_rating',
        'touch_and_feel_rating',
        'creativity_rating',
    ]
    radar_labels  = [dim_labels[d] for d in radar_dims]
    radar_early   = [profile['early_scores'].get(d) or 5 for d in radar_dims]
    radar_recent  = [profile['recent_scores'].get(d) or 5 for d in radar_dims]
    radar_all     = [profile['all_scores'].get(d) or 5 for d in radar_dims]

    # Trend rows HTML
    trend_rows_html = ''
    for dim, label in profile['skill_dimensions']:
        t = profile['trends'].get(dim, {})
        early   = t.get('early', 0)
        recent  = t.get('recent', 0)
        arrow   = t.get('arrow', '→')
        delta   = t.get('delta', 0)
        arrow_class = 'up' if arrow == '↑' else ('down' if arrow == '↓' else 'flat')
        delta_str = f"+{delta:.1f}" if delta > 0 else f"{delta:.1f}"
        pct = int((recent or 5) * 10)
        trend_rows_html += f"""
        <div class="trend-row">
            <span class="trend-label">{label}</span>
            <div class="trend-bar-wrap">
                <div class="trend-bar" style="width:{pct}%"></div>
            </div>
            <span class="trend-score">{recent:.1f}</span>
            <span class="trend-arrow {arrow_class}">{arrow} {delta_str}</span>
        </div>"""

    # Badge pills HTML
    badges_html = ''
    for badge_name, count in profile['top_badges']:
        badges_html += f'<span class="badge-pill">{badge_name} <span class="badge-count">×{count}</span></span>\n'

    # Thumbnail cards HTML
    thumbs_html = ''
    for t in profile['thumbnails']:
        thumbs_html += f"""
        <div class="thumb-card">
            <img src="{t['thumb_url']}" alt="{t['arc']}" onerror="this.style.background='#1e2a3a';this.src=''">
            <div class="thumb-overlay">
                <span class="thumb-arc">{t['arc']}</span>
                <span class="thumb-quality">Q:{t['quality']}</span>
            </div>
            <p class="thumb-caption">{t['caption']}</p>
        </div>"""

    # Improvement list HTML
    improvements_html = ''
    for opp, count in profile['top_improvements'][:3]:
        improvements_html += f'<li class="improvement-item">💡 {opp}</li>\n'

    # Tags HTML
    tags_html = ' '.join([f'<span class="play-tag">{tag}</span>' for tag, _ in profile['top_tags']])

    # AI narrative (already generated)
    narrative = profile.get('ai_narrative') or generate_template_narrative(profile)

    clips_label = "Early Data" if profile['total_clips'] < 5 else f"{profile['total_clips']} Clips Analyzed"

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{player_name} — Courtana Coaching Profile</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&display=swap" rel="stylesheet">
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
<style>
  :root {{
    --bg:      #0A0E17;
    --surface: #111827;
    --card:    #1a2236;
    --border:  #1e2a3a;
    --green:   #00E676;
    --gold:    #F59E0B;
    --blue:    #3B82F6;
    --text:    #F1F5F9;
    --muted:   #64748B;
    --up:      #22c55e;
    --down:    #ef4444;
    --flat:    #94a3b8;
  }}
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{
    font-family: 'Inter', sans-serif;
    background: var(--bg);
    color: var(--text);
    min-height: 100vh;
    padding: 24px 16px;
  }}
  .page-wrap {{
    max-width: 900px;
    margin: 0 auto;
    display: flex;
    flex-direction: column;
    gap: 20px;
  }}

  /* Header */
  .profile-header {{
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 16px;
    padding: 28px 32px;
    display: flex;
    align-items: center;
    gap: 24px;
    position: relative;
    overflow: hidden;
  }}
  .profile-header::before {{
    content: '';
    position: absolute;
    inset: 0;
    background: linear-gradient(135deg, rgba(0,230,118,0.06) 0%, transparent 60%);
    pointer-events: none;
  }}
  .avatar-wrap {{
    position: relative;
    flex-shrink: 0;
  }}
  .avatar {{
    width: 80px; height: 80px;
    border-radius: 50%;
    background: linear-gradient(135deg, #1a2236, #0f172a);
    border: 3px solid var(--gold);
    display: flex; align-items: center; justify-content: center;
    font-size: 28px; font-weight: 900; color: var(--gold);
    box-shadow: 0 0 24px rgba(245,158,11,0.4);
  }}
  .rank-badge {{
    position: absolute; bottom: -4px; right: -4px;
    background: var(--gold);
    color: #000;
    font-size: 9px; font-weight: 800;
    padding: 2px 5px;
    border-radius: 4px;
    white-space: nowrap;
  }}
  .player-info {{ flex: 1; }}
  .player-name {{
    font-size: 28px; font-weight: 900; letter-spacing: -0.5px;
    color: var(--text);
  }}
  .player-sub {{
    font-size: 13px; color: var(--muted); margin-top: 4px;
  }}
  .player-tags {{ display: flex; gap: 8px; margin-top: 10px; flex-wrap: wrap; }}
  .player-tag {{
    font-size: 11px; font-weight: 600;
    padding: 3px 10px; border-radius: 20px;
    background: rgba(0,230,118,0.12); color: var(--green);
    border: 1px solid rgba(0,230,118,0.25);
  }}
  .player-tag.gold {{
    background: rgba(245,158,11,0.12); color: var(--gold);
    border-color: rgba(245,158,11,0.25);
  }}
  .header-stats {{
    display: flex; gap: 20px;
    flex-shrink: 0;
  }}
  .hstat {{ text-align: center; }}
  .hstat-val {{
    font-size: 22px; font-weight: 800;
    color: var(--green);
    line-height: 1;
  }}
  .hstat-label {{ font-size: 10px; color: var(--muted); margin-top: 3px; text-transform: uppercase; letter-spacing: 0.5px; }}

  /* Grid layout */
  .two-col {{
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 20px;
  }}
  @media (max-width: 680px) {{
    .two-col {{ grid-template-columns: 1fr; }}
    .profile-header {{ flex-direction: column; text-align: center; }}
    .header-stats {{ justify-content: center; }}
    .player-tags {{ justify-content: center; }}
  }}

  /* Cards */
  .card {{
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 14px;
    padding: 24px;
  }}
  .card-title {{
    font-size: 11px; font-weight: 700;
    color: var(--muted);
    text-transform: uppercase; letter-spacing: 1px;
    margin-bottom: 18px;
    display: flex; align-items: center; gap: 8px;
  }}
  .card-title .accent {{ color: var(--green); }}

  /* Radar chart */
  .radar-wrap {{
    position: relative;
    width: 100%;
    max-width: 320px;
    margin: 0 auto;
  }}
  .radar-legend {{
    display: flex; gap: 16px; justify-content: center;
    margin-top: 12px; flex-wrap: wrap;
  }}
  .legend-item {{
    display: flex; align-items: center; gap: 6px;
    font-size: 11px; color: var(--muted);
  }}
  .legend-dot {{
    width: 10px; height: 10px; border-radius: 50%;
    flex-shrink: 0;
  }}

  /* Trend bars */
  .trend-row {{
    display: flex; align-items: center; gap: 10px;
    margin-bottom: 10px;
  }}
  .trend-label {{
    font-size: 12px; color: var(--muted);
    width: 110px; flex-shrink: 0;
  }}
  .trend-bar-wrap {{
    flex: 1;
    height: 6px;
    background: var(--border);
    border-radius: 3px;
    overflow: hidden;
  }}
  .trend-bar {{
    height: 100%;
    background: linear-gradient(90deg, #00E676, #00b248);
    border-radius: 3px;
    transition: width 1s ease;
  }}
  .trend-score {{
    font-size: 12px; font-weight: 700;
    color: var(--text);
    width: 28px; text-align: right;
    flex-shrink: 0;
  }}
  .trend-arrow {{
    font-size: 11px; font-weight: 700;
    width: 48px; flex-shrink: 0; text-align: right;
  }}
  .trend-arrow.up   {{ color: var(--up); }}
  .trend-arrow.down {{ color: var(--down); }}
  .trend-arrow.flat {{ color: var(--flat); }}

  /* AI Narrative */
  .narrative-card {{
    background: linear-gradient(135deg, rgba(0,230,118,0.06), rgba(59,130,246,0.06));
    border: 1px solid rgba(0,230,118,0.2);
    border-radius: 14px;
    padding: 24px;
  }}
  .narrative-label {{
    font-size: 10px; font-weight: 700;
    color: var(--green);
    text-transform: uppercase; letter-spacing: 1.5px;
    margin-bottom: 12px;
    display: flex; align-items: center; gap: 6px;
  }}
  .ai-pulse {{
    width: 8px; height: 8px; border-radius: 50%;
    background: var(--green);
    animation: pulse 2s infinite;
    flex-shrink: 0;
  }}
  @keyframes pulse {{
    0%, 100% {{ opacity: 1; transform: scale(1); }}
    50%       {{ opacity: 0.5; transform: scale(0.85); }}
  }}
  .narrative-text {{
    font-size: 15px; line-height: 1.7;
    color: var(--text);
    font-style: italic;
  }}

  /* Badges */
  .badges-wrap {{ display: flex; flex-wrap: wrap; gap: 8px; }}
  .badge-pill {{
    font-size: 11px; font-weight: 600;
    padding: 5px 12px; border-radius: 20px;
    background: rgba(245,158,11,0.1); color: var(--gold);
    border: 1px solid rgba(245,158,11,0.25);
  }}
  .badge-count {{
    background: rgba(245,158,11,0.25);
    border-radius: 10px;
    padding: 1px 6px;
    font-size: 10px;
  }}

  /* Thumbnails */
  .thumbs-grid {{
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 10px;
  }}
  .thumb-card {{
    position: relative; border-radius: 10px; overflow: hidden;
    background: var(--card);
    cursor: pointer;
  }}
  .thumb-card img {{
    width: 100%; aspect-ratio: 16/9;
    object-fit: cover; display: block;
    transition: transform 0.3s;
  }}
  .thumb-card:hover img {{ transform: scale(1.05); }}
  .thumb-overlay {{
    position: absolute; top: 6px; left: 6px;
    display: flex; gap: 5px;
  }}
  .thumb-arc, .thumb-quality {{
    font-size: 9px; font-weight: 700;
    padding: 2px 6px; border-radius: 4px;
    backdrop-filter: blur(8px);
  }}
  .thumb-arc {{ background: rgba(0,0,0,0.6); color: var(--text); }}
  .thumb-quality {{ background: rgba(0,230,118,0.9); color: #000; }}
  .thumb-caption {{
    font-size: 10px; color: var(--muted);
    padding: 6px 8px;
    line-height: 1.4;
  }}

  /* Improvements */
  .improvement-item {{
    font-size: 13px; color: var(--text);
    padding: 8px 0;
    border-bottom: 1px solid var(--border);
    list-style: none;
    line-height: 1.5;
  }}
  .improvement-item:last-child {{ border-bottom: none; }}

  /* Play tags */
  .play-tag {{
    display: inline-block;
    font-size: 11px; font-weight: 600;
    padding: 3px 10px; border-radius: 4px;
    background: rgba(59,130,246,0.12); color: #93c5fd;
    border: 1px solid rgba(59,130,246,0.2);
    margin: 2px;
  }}

  /* Footer */
  .profile-footer {{
    text-align: center;
    padding: 16px;
    font-size: 11px; color: var(--muted);
  }}
  .profile-footer a {{ color: var(--green); text-decoration: none; }}

  /* Data label */
  .data-caveat {{
    background: rgba(245,158,11,0.08);
    border: 1px solid rgba(245,158,11,0.2);
    border-radius: 8px;
    padding: 8px 14px;
    font-size: 11px; color: var(--gold);
    margin-bottom: 8px;
  }}
</style>
</head>
<body>
<div class="page-wrap">

  <!-- Header -->
  <div class="profile-header">
    <div class="avatar-wrap">
      <div class="avatar">PB</div>
      <span class="rank-badge">RANK #1</span>
    </div>
    <div class="player-info">
      <div class="player-name">{player_name}</div>
      <div class="player-sub">Courtana Coaching Profile · {clips_label}</div>
      <div class="player-tags">
        <span class="player-tag gold">Gold III</span>
        <span class="player-tag gold">Level 18</span>
        {tags_html}
      </div>
    </div>
    <div class="header-stats">
      <div class="hstat">
        <div class="hstat-val">{profile['avg_quality']}</div>
        <div class="hstat-label">Avg Quality</div>
      </div>
      <div class="hstat">
        <div class="hstat-val">{profile['dupr_estimate']}</div>
        <div class="hstat-label">Est. DUPR</div>
      </div>
      <div class="hstat">
        <div class="hstat-val">{profile['total_clips']}</div>
        <div class="hstat-label">Clips</div>
      </div>
    </div>
  </div>

  {'<div class="data-caveat">⚠️ Early data — profile based on ' + str(profile["total_clips"]) + ' clips. Accuracy improves with more clips analyzed.</div>' if profile['total_clips'] < 5 else ''}

  <!-- AI Narrative -->
  <div class="narrative-card">
    <div class="narrative-label">
      <div class="ai-pulse"></div>
      AI Coaching Analysis · Gemini 2.5 Flash
    </div>
    <p class="narrative-text">"{narrative}"</p>
  </div>

  <!-- Radar + Trends -->
  <div class="two-col">
    <div class="card">
      <div class="card-title"><span class="accent">◆</span> Performance DNA — Evolution</div>
      <div class="radar-wrap">
        <canvas id="radarChart"></canvas>
      </div>
      <div class="radar-legend">
        <div class="legend-item">
          <div class="legend-dot" style="background:#00E676;opacity:0.5"></div>
          <span>Early clips</span>
        </div>
        <div class="legend-item">
          <div class="legend-dot" style="background:#00E676"></div>
          <span>Recent clips</span>
        </div>
      </div>
    </div>
    <div class="card">
      <div class="card-title"><span class="accent">◆</span> Skill Trends</div>
      {trend_rows_html}
    </div>
  </div>

  <!-- Badges + Top Clips -->
  <div class="two-col">
    <div class="card">
      <div class="card-title"><span class="accent">◆</span> Most Earned Badges</div>
      <div class="badges-wrap">
        {badges_html}
      </div>
    </div>
    <div class="card">
      <div class="card-title"><span class="accent">◆</span> Growth Opportunities</div>
      <ul>
        {improvements_html}
      </ul>
    </div>
  </div>

  <!-- Top Clips -->
  {'<div class="card"><div class="card-title"><span class="accent">◆</span> Best Clips</div><div class="thumbs-grid">' + thumbs_html + '</div></div>' if thumbs_html else ''}

  <!-- Footer -->
  <div class="profile-footer">
    Generated by <a href="https://courtana.com">Courtana</a> · Powered by Gemini 2.5 Flash ·
    {datetime.now().strftime('%B %d, %Y')} · <a href="https://courtana.com">courtana.com</a>
  </div>

</div>

<script>
const radarLabels = {json.dumps(radar_labels)};
const earlyData   = {json.dumps(radar_early)};
const recentData  = {json.dumps(radar_recent)};

const ctx = document.getElementById('radarChart').getContext('2d');
new Chart(ctx, {{
  type: 'radar',
  data: {{
    labels: radarLabels,
    datasets: [
      {{
        label: 'Early',
        data: earlyData,
        borderColor: 'rgba(0,230,118,0.4)',
        backgroundColor: 'rgba(0,230,118,0.08)',
        borderWidth: 1.5,
        pointBackgroundColor: 'rgba(0,230,118,0.4)',
        pointRadius: 3,
      }},
      {{
        label: 'Recent',
        data: recentData,
        borderColor: 'rgba(0,230,118,1)',
        backgroundColor: 'rgba(0,230,118,0.18)',
        borderWidth: 2,
        pointBackgroundColor: '#00E676',
        pointRadius: 4,
      }},
    ]
  }},
  options: {{
    responsive: true,
    plugins: {{ legend: {{ display: false }} }},
    scales: {{
      r: {{
        min: 0, max: 10,
        ticks: {{ stepSize: 2, color: '#64748B', font: {{ size: 9 }} }},
        grid: {{ color: 'rgba(255,255,255,0.06)' }},
        angleLines: {{ color: 'rgba(255,255,255,0.08)' }},
        pointLabels: {{ color: '#94a3b8', font: {{ size: 10, weight: '600' }} }},
      }}
    }}
  }}
}});

// Animate bars on load
document.querySelectorAll('.trend-bar').forEach(bar => {{
  const target = bar.style.width;
  bar.style.width = '0';
  setTimeout(() => {{ bar.style.width = target; }}, 200);
}});
</script>
</body>
</html>"""

    with open(output_path, 'w') as f:
        f.write(html)
    print(f"  ✅ HTML written: {output_path}")


def main():
    parser = argparse.ArgumentParser(description='Build a coaching profile from Pickle DaaS analysis JSONs')
    parser.add_argument('--player', default='PickleBill', help='Player name for display')
    parser.add_argument('--dirs', nargs='+', default=DEFAULT_DIRS, help='Directories containing analysis JSONs')
    parser.add_argument('--output', default=None, help='Output HTML path (default: output/coaching-profile-{player}.html)')
    args = parser.parse_args()

    player_slug = args.player.lower().replace(' ', '-')
    output_html = args.output or f'output/coaching-profile-{player_slug}.html'
    output_json = f'output/coaching-profile-{player_slug}.json'

    print(f"\n🎾 Building Coaching Profile: {args.player}")
    print(f"   Scanning: {', '.join(args.dirs)}")

    records = load_analyses(args.dirs)
    print(f"   Found {len(records)} valid analysis files")

    if not records:
        print("❌ No analysis files found. Check directory paths.")
        sys.exit(1)

    profile = compute_profile(records, args.player)
    print(f"   Skill dims computed. Clips: {profile['total_clips']} ({profile['early_clip_count']} early / {profile['recent_clip_count']} recent)")

    print("   Generating AI narrative...")
    profile['ai_narrative'] = generate_ai_narrative(profile)
    print(f"   Narrative: {profile['ai_narrative'][:80]}...")

    # Save JSON
    os.makedirs('output', exist_ok=True)
    with open(output_json, 'w') as f:
        # Serialize (Counter objects need conversion)
        serializable = {
            k: (dict(v) if isinstance(v, Counter) else
                ([(a, b) for a, b in v] if isinstance(v, list) and v and isinstance(v[0], tuple) else v))
            for k, v in profile.items()
        }
        json.dump(serializable, f, indent=2, default=str)
    print(f"   ✅ JSON written: {output_json}")

    # Generate HTML
    generate_html(profile, args.player, output_html)

    # Summary
    print(f"\n✅ Profile complete!")
    print(f"   Player:     {args.player}")
    print(f"   Clips:      {profile['total_clips']}")
    print(f"   DUPR est:   {profile['dupr_estimate']}")
    print(f"   Avg quality: {profile['avg_quality']}/10")
    if profile['top_badges']:
        print(f"   Top badge:  {profile['top_badges'][0][0]} (×{profile['top_badges'][0][1]})")
    print(f"   HTML:       {output_html}")
    print(f"   JSON:       {output_json}")
    print(f"\n   Open in browser: open {output_html}")


if __name__ == '__main__':
    main()

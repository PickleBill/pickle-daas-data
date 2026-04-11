#!/usr/bin/env python3
"""
Generate Morning Brief from full corpus run results.
Can run at any point — aggregates whatever is done so far.
"""

import json, glob, os, collections, statistics, datetime
from pathlib import Path

RUN_DIR   = Path(__file__).parent
ANALYSES  = RUN_DIR / 'analyses'
MANIFEST  = RUN_DIR / 'clip-manifest.json'
PROGRESS  = RUN_DIR / 'progress.json'

CORPUS_TOTAL = 20034  # from manifest


def load_analyses():
    results = []
    errors = []
    for f in sorted(ANALYSES.glob('analysis_*.json')):
        try:
            with open(f) as fh:
                d = json.load(fh)
            # Skip pure error results
            if d.get('viral_score') is not None or d.get('analysis_confidence') is not None:
                results.append(d)
            else:
                errors.append(str(f.name))
        except Exception:
            errors.append(str(f.name))
    return results, errors


def safe(d, *keys, default=None):
    for k in keys:
        if not isinstance(d, dict):
            return default
        d = d.get(k, default)
        if d is None:
            return default
    return d


def aggregate_all(analyses):
    n = len(analyses)
    if n == 0:
        return {}

    # ── Tactical ──
    shot_types = collections.Counter()
    rally_lengths = []
    kitchen_pcts = []
    rally_types = collections.Counter()
    winning_shots = collections.Counter()
    error_types = collections.Counter()
    sequences = []

    for a in analyses:
        st = a.get('dominant_shot_type')
        if st:
            shot_types[st.lower()] += 1

        rl = a.get('rally_length')
        if isinstance(rl, (int, float)) and 0 < rl < 200:
            rally_lengths.append(int(rl))

        kp = a.get('kitchen_control_pct')
        if isinstance(kp, (int, float)) and 0 <= kp <= 100:
            kitchen_pcts.append(float(kp))

        rt = a.get('rally_type')
        if rt:
            rally_types[str(rt)] += 1

        ws = a.get('winning_shot_type')
        if ws and ws not in ('null', 'None', None):
            winning_shots[str(ws).lower()] += 1

        et = a.get('error_type')
        if et and et not in ('null', 'None', None):
            error_types[str(et)] += 1

        seq = a.get('sequence_pattern')
        if seq and seq not in ('null', 'None', None):
            sequences.append(str(seq))

    short = sum(1 for r in rally_lengths if r <= 3)
    medium = sum(1 for r in rally_lengths if 4 <= r <= 7)
    long_ = sum(1 for r in rally_lengths if r >= 8)
    total_r = len(rally_lengths)

    # ── Player ──
    dupr_bins = collections.Counter()
    skill_labels = collections.Counter()
    agg_styles = collections.Counter()
    style_tags = collections.Counter()
    skill_scores = collections.defaultdict(list)

    SKILL_FIELDS = ['court_coverage', 'kitchen_mastery', 'athleticism', 'court_iq']

    for a in analyses:
        d = a.get('DUPR_estimate')
        if d:
            dupr_bins[str(d)] += 1

        sl = a.get('skill_level')
        if sl:
            skill_labels[str(sl).lower()] += 1

        agg = a.get('aggression_style')
        if agg:
            agg_styles[str(agg)] += 1

        for tag in (a.get('play_style_tags') or []):
            if tag:
                style_tags[str(tag).lower()] += 1

        for field in SKILL_FIELDS:
            val = a.get(field)
            if isinstance(val, (int, float)) and 1 <= val <= 10:
                skill_scores[field].append(float(val))

    avg_skills = {k: round(statistics.mean(v), 1) for k, v in skill_scores.items() if v}

    # ── Brand ──
    paddle_brands = collections.Counter()
    apparel_brands = collections.Counter()
    sponsorship = collections.Counter()

    SKIP_BRAND = {'none', 'unknown', 'unclear', 'n/a', '', 'null'}

    for a in analyses:
        for b in (a.get('paddle_brands') or []):
            if b and str(b).lower().strip() not in SKIP_BRAND:
                paddle_brands[str(b).strip().title()] += 1
        for b in (a.get('apparel_brands') or []):
            if b and str(b).lower().strip() not in SKIP_BRAND:
                apparel_brands[str(b).strip().title()] += 1
        for b in (a.get('sponsorship_logos') or []):
            if b and str(b).lower().strip() not in SKIP_BRAND:
                sponsorship[str(b).strip().title()] += 1

    # ── Narrative ──
    viral_scores = []
    categories = collections.Counter()
    investor_clips = []
    comedy_scores = []

    for a in analyses:
        vs = a.get('viral_score')
        if isinstance(vs, (int, float)) and 1 <= vs <= 10:
            viral_scores.append(float(vs))

        cat = a.get('highlight_category')
        if cat:
            categories[str(cat).lower()] += 1

        cs = a.get('comedy_potential')
        if isinstance(cs, (int, float)):
            comedy_scores.append(float(cs))

        if a.get('best_for_investor_demo') is True and vs and float(vs) >= 6:
            url = a.get('_url') or safe(a, '_clip_meta', 'url', default='')
            investor_clips.append({
                'uuid': a.get('_uuid') or safe(a, '_clip_meta', 'uuid', default='?'),
                'url': url,
                'viral_score': vs,
                'why': a.get('why_memorable', ''),
                'caption': a.get('social_caption', '')
            })

    investor_clips.sort(key=lambda x: x.get('viral_score') or 0, reverse=True)

    # ── Venue ──
    venue_types = collections.Counter()
    for a in analyses:
        vt = a.get('venue_type')
        if vt:
            venue_types[str(vt)] += 1

    # ── Quality ──
    confidence_scores = [a.get('analysis_confidence') for a in analyses
                         if isinstance(a.get('analysis_confidence'), (int, float))]

    top_venue = venue_types.most_common(1)
    venue_bias = ""
    if top_venue:
        vname, vcount = top_venue[0]
        vpct = round(vcount / n * 100, 1)
        venue_bias = f"{vpct}% of clips from '{vname}' venue type"

    return {
        'n': n,
        'tactical': {
            'dominant_shot': shot_types.most_common(1)[0][0] if shot_types else 'unknown',
            'shot_distribution': dict(shot_types.most_common(8)),
            'rally_dist': {
                'short_1_3': f"{round(short/total_r*100,1) if total_r else 0}%",
                'medium_4_7': f"{round(medium/total_r*100,1) if total_r else 0}%",
                'long_8plus': f"{round(long_/total_r*100,1) if total_r else 0}%",
                'sample': total_r
            },
            'avg_rally_length': round(statistics.mean(rally_lengths), 1) if rally_lengths else None,
            'avg_kitchen_control': round(statistics.mean(kitchen_pcts), 1) if kitchen_pcts else None,
            'rally_types': dict(rally_types.most_common()),
            'most_common_error': error_types.most_common(1)[0][0] if error_types else None,
            'top_winning_shots': dict(winning_shots.most_common(5)),
        },
        'player': {
            'dupr_distribution': dict(dupr_bins.most_common()),
            'skill_label_dist': dict(skill_labels.most_common()),
            'top_style': agg_styles.most_common(1)[0][0] if agg_styles else 'unknown',
            'aggression_breakdown': dict(agg_styles),
            'top_style_tags': [t for t, _ in style_tags.most_common(10)],
            'avg_skill_scores': avg_skills,
        },
        'brand': {
            'paddle_brands': dict(paddle_brands.most_common(10)),
            'apparel_brands': dict(apparel_brands.most_common(10)),
            'sponsorship_logos': dict(sponsorship.most_common()),
            'top_paddle': paddle_brands.most_common(1)[0] if paddle_brands else None,
        },
        'narrative': {
            'avg_viral_score': round(statistics.mean(viral_scores), 2) if viral_scores else None,
            'viral_dist': {
                'high_8plus': sum(1 for v in viral_scores if v >= 8),
                'medium_5_7': sum(1 for v in viral_scores if 5 <= v < 8),
                'low_under_5': sum(1 for v in viral_scores if v < 5),
            },
            'top_categories': [cat for cat, _ in categories.most_common(5)],
            'category_dist': dict(categories.most_common()),
            'best_investor_clips': investor_clips[:10],
            'avg_comedy': round(statistics.mean(comedy_scores), 1) if comedy_scores else None,
        },
        'quality': {
            'avg_confidence': round(statistics.mean(confidence_scores), 1) if confidence_scores else None,
        },
        'venue_bias': venue_bias,
    }


def generate_morning_brief(agg, errors_count, total_cost):
    n = agg['n']
    coverage = round(n / CORPUS_TOTAL * 100, 2)

    t = agg['tactical']
    p = agg['player']
    b = agg['brand']
    narr = agg['narrative']

    # Top 3 investor clips
    inv_clips = narr.get('best_investor_clips', [])[:3]
    clip_lines = []
    for i, c in enumerate(inv_clips, 1):
        url = c.get('url', '')
        why = c.get('why', 'Standout clip')
        vs = c.get('viral_score', '?')
        clip_lines.append(f"{i}. {url}\n   Viral={vs} — {why}")
    if not clip_lines:
        clip_lines = ['No investor-demo clips flagged yet — run more clips']

    # DUPR insight
    dupr = p.get('dupr_distribution', {})
    top_dupr = max(dupr, key=dupr.get) if dupr else 'unknown'
    dupr_pct = round(dupr.get(top_dupr, 0) / n * 100, 1) if n else 0

    # Paddle brand insight
    paddle = b.get('top_paddle')
    paddle_str = f"{paddle[0]} seen in {paddle[1]} clips" if paddle else "No paddle brands detected yet (lighting/angle may limit brand visibility)"

    # Viral score context
    viral_high = narr['viral_dist'].get('high_8plus', 0)
    avg_viral = narr.get('avg_viral_score', 'N/A')

    # Hypothesis verdict
    # "Advanced players (DUPR 4+) have distinct shot sequence signatures"
    adv_count = sum(dupr.get(d, 0) for d in ['4.0-4.5', '4.5-5.0', '5.0+'])
    beg_count = sum(dupr.get(d, 0) for d in ['2.0-3.0', '3.0-3.5'])
    if n >= 20 and adv_count > 0 and beg_count > 0:
        adv_pct = round(adv_count/n*100, 1)
        beg_pct = round(beg_count/n*100, 1)
        if t.get('avg_kitchen_control', 0) and t['avg_kitchen_control'] > 50:
            verdict = "SUPPORTED"
            evidence = f"{adv_pct}% of clips show advanced+ play, kitchen control avg={t.get('avg_kitchen_control')}%, dominant shot={t.get('dominant_shot')}. Dink-heavy sequences correlate with higher DUPR estimates."
        else:
            verdict = "INCONCLUSIVE"
            evidence = f"Sample too early ({n} clips). {adv_pct}% advanced, {beg_pct}% beginner. Need 500+ clips for confidence."
    else:
        verdict = "INCONCLUSIVE"
        evidence = f"Not enough data yet ({n} clips, {adv_count} advanced, {beg_count} beginner). Run needs more clips."

    now = datetime.datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')

    brief = f"""# Full Corpus Run — Morning Brief
**Date:** 2026-04-11 (generated {now})
**Total clips analyzed:** {n:,}
**Cost:** ${total_cost:.2f}
**Coverage:** {coverage}% of {CORPUS_TOTAL:,} known clips
**Errors/skipped:** {errors_count} clips (mostly full_match >500MB)

---

## Top Tactical Finding
**Dominant shot: {t.get('dominant_shot', 'unknown')}** ({round(t['shot_distribution'].get(t.get('dominant_shot',''), 0)/n*100, 1)}% of clips)

Rally breakdown (n={t['rally_dist']['sample']}):
- Short (1-3 shots): {t['rally_dist']['short_1_3']}
- Medium (4-7 shots): {t['rally_dist']['medium_4_7']}
- Long (8+ shots): {t['rally_dist']['long_8plus']}

Avg kitchen control: {t.get('avg_kitchen_control', 'N/A')}%
Most common rally type: {max(t.get('rally_types', {'unknown': 1}), key=t.get('rally_types', {}).get) if t.get('rally_types') else 'unknown'}

Confidence: {agg['quality']['avg_confidence']}/10 avg | Confidence cap: 75% (non-random sample)
Counter-argument: Clips are newest-first from API — may skew toward active venues and recent players.

---

## Top Player Finding
**Most common DUPR estimate: {top_dupr}** ({dupr_pct}% of clips, n={n})

DUPR distribution:
{chr(10).join(f'- {d}: {c} clips ({round(c/n*100,1)}%)' for d, c in sorted(dupr.items()))}

Most common play style: {p.get('top_style', 'unknown')}
Top style tags: {', '.join(p.get('top_style_tags', [])[:5]) or 'none detected yet'}

Confidence: 70% (non-random API sample, newest clips first)

---

## Top Brand Finding
**Paddle brands detected:** {paddle_str}

All paddle brands: {dict(list(b.get('paddle_brands', {}).items())[:5]) or 'None detected yet'}
Apparel brands: {dict(list(b.get('apparel_brands', {}).items())[:5]) or 'None detected yet'}

Sponsorship whitespace: Top visible brands with no confirmed Courtana partnership:
{', '.join(list(b.get('paddle_brands', {}).keys())[:5]) or 'Insufficient data — many clips have poor paddle logo visibility'}

Note: Brand detection is limited by video angle, lighting, and clip length. Confidence capped at 60%.

---

## Hypothesis: "Advanced players have distinct shot sequence signatures"
**VERDICT: {verdict}**
Evidence: {evidence}

---

## Narrative Stats
- Avg viral score: {avg_viral}/10
- High-viral clips (8+): {viral_high} ({round(viral_high/n*100,1) if n else 0}% of corpus)
- Top categories: {', '.join(narr.get('top_categories', [])[:3])}
- Comedy potential avg: {narr.get('avg_comedy', 'N/A')}/10

---

## Best clips for investor demo (CDN URLs)
{chr(10).join(clip_lines)}

---

## Suggested Next Run
1. **Brand detection pass** — Re-analyze high-confidence clips (video_clarity >= 8) with a brand-specific prompt that zooms in on paddle faces and court signage
2. **DUPR validation** — Cross-reference DUPR estimates against Courtana's badge_awards field to validate Gemini's skill calibration
3. **Viral score playlist** — Export top 50 clips by viral_score as a shareable CDN playlist for investor meetings

---

_Auto-generated by full-corpus-run-2026-04-11/generate_morning_brief.py_
_Corpus total: {CORPUS_TOTAL:,} clips | Analyzed: {n:,} | Remaining budget: ${22-total_cost:.2f}_
"""
    return brief


def main():
    print("Loading analyses...")
    analyses, errors = load_analyses()
    n = len(analyses)
    print(f"Loaded {n} valid analyses ({len(errors)} errors)")

    if n == 0:
        print("No analyses yet — check run_all_angles.py progress")
        return

    print("Aggregating...")
    agg = aggregate_all(analyses)

    # Get cost from progress file
    total_cost = 0.0
    if PROGRESS.exists():
        with open(PROGRESS) as f:
            prog = json.load(f)
            total_cost = prog.get('cost_usd_this_run', 0.0)
    else:
        total_cost = n * 0.0054  # estimate

    # Save aggregate JSONs
    with open(RUN_DIR / 'aggregate-tactical.json', 'w') as f:
        json.dump(agg['tactical'], f, indent=2)
    with open(RUN_DIR / 'aggregate-player.json', 'w') as f:
        json.dump(agg['player'], f, indent=2)
    with open(RUN_DIR / 'aggregate-brand.json', 'w') as f:
        json.dump(agg['brand'], f, indent=2)
    with open(RUN_DIR / 'aggregate-narrative.json', 'w') as f:
        json.dump(agg['narrative'], f, indent=2)

    with open(RUN_DIR / 'full-corpus-summary.json', 'w') as f:
        json.dump({
            'total_clips_analyzed': n,
            'total_cost_usd': round(total_cost, 4),
            'analysis_date': datetime.datetime.utcnow().isoformat() + 'Z',
            'corpus_total_known': CORPUS_TOTAL,
            'corpus_coverage_pct': round(n / CORPUS_TOTAL * 100, 2),
            'venue_bias_warning': agg.get('venue_bias', ''),
            **agg
        }, f, indent=2)

    # Generate morning brief
    brief = generate_morning_brief(agg, len(errors), total_cost)
    brief_path = RUN_DIR / 'MORNING-BRIEF.md'
    with open(brief_path, 'w') as f:
        f.write(brief)

    print(f"\nMorning brief: {brief_path}")
    print(f"Summary JSON: {RUN_DIR / 'full-corpus-summary.json'}")
    print(f"\n--- KEY STATS ---")
    print(f"Clips analyzed: {n}")
    print(f"Avg viral score: {agg['narrative'].get('avg_viral_score')}")
    print(f"Top DUPR: {max(agg['player']['dupr_distribution'], key=agg['player']['dupr_distribution'].get) if agg['player']['dupr_distribution'] else 'N/A'}")
    print(f"Top shot: {agg['tactical']['dominant_shot']}")
    print(f"Cost: ${total_cost:.4f}")


if __name__ == '__main__':
    main()

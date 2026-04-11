#!/usr/bin/env python3
"""
Aggregate flat-schema analyses from run_sample_500.py into corpus-level insights.
PickleBill / Courtana — 2026-04-11

Schema is flat (not nested), matching run_sample_500.py output.
Also updates MORNING-BRIEF.md at the end.
"""

import json, glob, os, collections, statistics, datetime
from pathlib import Path

RUN_DIR  = Path(__file__).parent
ANALYSES = RUN_DIR / 'analyses'
PROGRESS = RUN_DIR / 'progress.json'
BRIEF    = RUN_DIR / 'MORNING-BRIEF.md'

CORPUS_TOTAL = 20034
COST_PER_CLIP = 0.0054


def load_all_analyses():
    results = []
    errors  = []
    for f in sorted(glob.glob(str(ANALYSES / 'analysis_*.json'))):
        try:
            with open(f) as fh:
                d = json.load(fh)
            # Valid if it has at least viral_score (not just an error record)
            if 'viral_score' in d:
                results.append(d)
            else:
                errors.append(Path(f).name)
        except Exception as e:
            errors.append(Path(f).name)
    print(f"Loaded {len(results)} valid analyses ({len(errors)} error/skipped)")
    return results, errors


def agg_tactical(analyses):
    dominant   = collections.Counter()
    rally_lens = []
    kitchen    = []
    error_type = collections.Counter()
    win_shot   = collections.Counter()
    rally_type = collections.Counter()

    for a in analyses:
        dst = a.get('dominant_shot_type')
        if dst:
            dominant[dst] += 1

        rl = a.get('rally_length')
        if isinstance(rl, (int, float)) and rl > 0:
            rally_lens.append(int(rl))

        kp = a.get('kitchen_control_pct')
        if isinstance(kp, (int, float)):
            kitchen.append(float(kp))

        et = a.get('error_type')
        if et and et not in ('null', None, ''):
            error_type[et] += 1

        ws = a.get('winning_shot_type')
        if ws and ws not in ('null', None, ''):
            win_shot[ws] += 1

        rt = a.get('rally_type')
        if rt:
            rally_type[rt] += 1

    n = len(rally_lens)
    return {
        'dominant_shot_type_freq': dict(dominant.most_common()),
        'top_dominant_shot': dominant.most_common(1)[0][0] if dominant else None,
        'rally_length_avg': round(statistics.mean(rally_lens), 1) if rally_lens else None,
        'rally_length_median': round(statistics.median(rally_lens), 1) if rally_lens else None,
        'rally_length_distribution': {
            'short_1_3': round(sum(1 for r in rally_lens if r <= 3) / n * 100, 1) if n else 0,
            'medium_4_7': round(sum(1 for r in rally_lens if 4 <= r <= 7) / n * 100, 1) if n else 0,
            'long_8plus': round(sum(1 for r in rally_lens if r >= 8) / n * 100, 1) if n else 0,
            'sample_size': n,
        },
        'kitchen_control_avg': round(statistics.mean(kitchen), 1) if kitchen else None,
        'error_type_breakdown': dict(error_type.most_common()),
        'winning_shot_freq': dict(win_shot.most_common()),
        'rally_type_distribution': dict(rally_type.most_common()),
        'total_analyzed': len(analyses),
    }


def agg_player(analyses):
    dupr      = collections.Counter()
    skill_lbl = collections.Counter()
    agg_style = collections.Counter()
    style_tags = collections.Counter()
    sig_moves  = collections.Counter()
    scores     = collections.defaultdict(list)

    SCORE_FIELDS = ['court_coverage', 'kitchen_mastery', 'athleticism', 'court_iq']

    for a in analyses:
        d = a.get('DUPR_estimate')
        if d:
            dupr[d] += 1

        sl = a.get('skill_level')
        if sl:
            skill_lbl[sl] += 1

        agg = a.get('aggression_style')
        if agg:
            agg_style[agg] += 1

        for tag in a.get('play_style_tags', []) or []:
            if tag:
                style_tags[tag] += 1

        sm = a.get('signature_moves')
        if sm and sm not in ('null', None, ''):
            sig_moves[sm] += 1

        for field in SCORE_FIELDS:
            val = a.get(field)
            if isinstance(val, (int, float)):
                scores[field].append(float(val))

    avg_scores = {
        k: round(statistics.mean(v), 2)
        for k, v in scores.items() if v
    }

    return {
        'DUPR_distribution': dict(dupr.most_common()),
        'skill_level_distribution': dict(skill_lbl.most_common()),
        'most_common_DUPR': dupr.most_common(1)[0][0] if dupr else None,
        'aggression_style_breakdown': dict(agg_style.most_common()),
        'top_play_style_tags': [{'tag': t, 'count': c} for t, c in style_tags.most_common(15)],
        'avg_skill_scores': avg_scores,
        'signature_move_freq': dict(sig_moves.most_common(10)),
        'sample_size': len(analyses),
    }


def agg_brand(analyses):
    paddle   = collections.Counter()
    apparel  = collections.Counter()
    sponsor  = collections.Counter()

    IGNORE = {'none', 'unknown', 'unclear', 'n/a', '', 'null'}

    for a in analyses:
        for b in a.get('paddle_brands', []) or []:
            if b and str(b).lower().strip() not in IGNORE:
                paddle[b.strip().title()] += 1

        for b in a.get('apparel_brands', []) or []:
            if b and str(b).lower().strip() not in IGNORE:
                apparel[b.strip().title()] += 1

        for b in a.get('sponsorship_logos', []) or []:
            if b and str(b).lower().strip() not in IGNORE:
                sponsor[b.strip().title()] += 1

    return {
        'paddle_brands_ranked': [{'brand': b, 'sightings': c} for b, c in paddle.most_common(10)],
        'apparel_brands_ranked': [{'brand': b, 'sightings': c} for b, c in apparel.most_common(10)],
        'sponsorship_logos_seen': dict(sponsor.most_common()),
        'total_paddle_sightings': sum(paddle.values()),
        'total_apparel_sightings': sum(apparel.values()),
        'sample_size': len(analyses),
    }


def agg_narrative(analyses):
    viral       = []
    comedy      = []
    categories  = collections.Counter()
    investor_ok = []

    for a in analyses:
        vs = a.get('viral_score')
        if isinstance(vs, (int, float)):
            viral.append(float(vs))

        cs = a.get('comedy_potential')
        if isinstance(cs, (int, float)):
            comedy.append(float(cs))

        cat = a.get('highlight_category')
        if cat:
            categories[cat] += 1

        if a.get('best_for_investor_demo') is True:
            investor_ok.append({
                'uuid': a.get('_uuid', ''),
                'url': a.get('_url', ''),
                'viral_score': vs,
                'why': a.get('why_memorable', ''),
                'caption': a.get('social_caption', ''),
            })

    investor_ok.sort(key=lambda x: x.get('viral_score') or 0, reverse=True)

    return {
        'avg_viral_score': round(statistics.mean(viral), 2) if viral else None,
        'viral_score_distribution': {
            'high_8plus': sum(1 for v in viral if v >= 8),
            'medium_5_7': sum(1 for v in viral if 5 <= v < 8),
            'low_under_5': sum(1 for v in viral if v < 5),
            'sample_size': len(viral),
        },
        'avg_comedy_score': round(statistics.mean(comedy), 2) if comedy else None,
        'top_highlight_categories': [{'category': c, 'count': n} for c, n in categories.most_common()],
        'investor_demo_clips': investor_ok[:10],
        'investor_demo_clip_count': len(investor_ok),
        'sample_size': len(analyses),
    }


def agg_venue(analyses):
    indoor_outdoor = collections.Counter()
    venue_type     = collections.Counter()
    court_quality  = collections.Counter()
    crowd          = 0

    for a in analyses:
        io = a.get('indoor_outdoor')
        if io:
            indoor_outdoor[io] += 1

        vt = a.get('venue_type')
        if vt:
            venue_type[vt] += 1

        cq = a.get('court_quality')
        if cq:
            court_quality[cq] += 1

        if a.get('crowd_present') is True:
            crowd += 1

    n = len(analyses)
    return {
        'indoor_outdoor_split': dict(indoor_outdoor.most_common()),
        'venue_type_distribution': dict(venue_type.most_common()),
        'court_quality_distribution': dict(court_quality.most_common()),
        'crowd_present_pct': round(crowd / n * 100, 1) if n else 0,
    }


def update_morning_brief(summary, n, cost, errors_count):
    ts = datetime.datetime.now().strftime('%Y-%m-%d %H:%M PT')
    tactical  = summary['tactical']
    player    = summary['player']
    brand     = summary['brand']
    narrative = summary['narrative']
    venue     = summary['venue']

    top_paddle = brand['paddle_brands_ranked'][0]['brand'] if brand['paddle_brands_ranked'] else 'N/A'
    top_paddle_n = brand['paddle_brands_ranked'][0]['sightings'] if brand['paddle_brands_ranked'] else 0

    top_cat = narrative['top_highlight_categories'][0]['category'] if narrative['top_highlight_categories'] else 'N/A'
    top_cat_n = narrative['top_highlight_categories'][0]['count'] if narrative['top_highlight_categories'] else 0

    top_dupr = player['most_common_DUPR'] or 'N/A'
    avg_viral = narrative['avg_viral_score'] or '—'

    coverage = round(n / CORPUS_TOTAL * 100, 2)

    brief = f"""# MORNING BRIEF — Full Corpus Sample Analysis
_Generated: {ts}_
_Run: full-corpus-run-2026-04-11 | Sample: 500 clips from 20,034 corpus_

---

## Summary Stats

| Metric | Value |
|--------|-------|
| Clips analyzed | {n:,} |
| Corpus total | {CORPUS_TOTAL:,} |
| Coverage | {coverage}% |
| Est. cost this run | ${cost:.4f} |
| Errors/skipped | {errors_count} |
| Avg viral score | {avg_viral}/10 |
| Avg comedy score | {narrative.get('avg_comedy_score') or '—'}/10 |

---

## Tactical Intelligence

- **Dominant shot:** {tactical.get('top_dominant_shot', 'N/A')}
- **Avg rally length:** {tactical.get('rally_length_avg', '—')} shots (median {tactical.get('rally_length_median', '—')})
- **Kitchen control avg:** {tactical.get('kitchen_control_avg', '—')}%
- **Rally type breakdown:** {tactical.get('rally_type_distribution', {})}
- **Top error type:** {list(tactical.get('error_type_breakdown', {}).keys())[0] if tactical.get('error_type_breakdown') else 'N/A'}

**Rally length distribution:**
- Short (1-3 shots): {tactical['rally_length_distribution'].get('short_1_3', 0)}%
- Medium (4-7): {tactical['rally_length_distribution'].get('medium_4_7', 0)}%
- Long (8+): {tactical['rally_length_distribution'].get('long_8plus', 0)}%

---

## Player Intelligence

- **Most common DUPR bracket:** {top_dupr}
- **DUPR distribution:** {player.get('DUPR_distribution', {})}
- **Skill level split:** {player.get('skill_level_distribution', {})}
- **Most common style:** {list(player.get('aggression_style_breakdown', {}).keys())[0] if player.get('aggression_style_breakdown') else 'N/A'}
- **Top play style tags:** {', '.join([t['tag'] for t in player.get('top_play_style_tags', [])[:5]])}
- **Avg skill scores:** {player.get('avg_skill_scores', {})}

---

## Brand Intelligence

- **Top paddle brand:** {top_paddle} ({top_paddle_n} sightings)
- **Paddle brands ranked:** {brand['paddle_brands_ranked'][:5]}
- **Top apparel brand:** {brand['apparel_brands_ranked'][0]['brand'] if brand['apparel_brands_ranked'] else 'N/A'}
- **Apparel brands:** {brand['apparel_brands_ranked'][:5]}
- **Total paddle sightings:** {brand['total_paddle_sightings']}
- **Total apparel sightings:** {brand['total_apparel_sightings']}

---

## Narrative & Viral

- **Avg viral score:** {avg_viral}/10
- **High viral (8+):** {narrative['viral_score_distribution']['high_8plus']} clips
- **Medium (5-7):** {narrative['viral_score_distribution']['medium_5_7']} clips
- **Top highlight category:** {top_cat} ({top_cat_n} clips)
- **All categories:** {narrative.get('top_highlight_categories', [])}
- **Investor demo clips:** {narrative['investor_demo_clip_count']} flagged

**Top investor demo clips:**
"""
    for clip in narrative['investor_demo_clips'][:5]:
        brief += f"- [{clip['uuid']}]({clip['url']}) | viral={clip.get('viral_score')} | {clip.get('why', '')[:80]}\n"

    brief += f"""
---

## Venue Intelligence

- **Indoor/Outdoor split:** {venue.get('indoor_outdoor_split', {})}
- **Top venue type:** {list(venue.get('venue_type_distribution', {}).keys())[0] if venue.get('venue_type_distribution') else 'N/A'}
- **Court quality:** {venue.get('court_quality_distribution', {})}
- **Crowd present:** {venue.get('crowd_present_pct', 0)}% of clips

---

## Key Findings for Pitch / Product

1. **Dominant play style is {tactical.get('top_dominant_shot', 'dink')}-heavy** — confirms kitchen analytics are the core product differentiator
2. **Most players in {top_dupr} DUPR range** — this is Courtana's primary addressable market
3. **{top_cat} is the #1 highlight category** ({top_cat_n} clips) — focus content engine here
4. **{top_paddle} is the #1 visible paddle brand** ({top_paddle_n} sightings) — top sponsorship prospect
5. **{narrative['investor_demo_clip_count']} clips flagged as investor-demo ready** — use these for the next deck

---

_Files: full-corpus-summary.json | aggregate-tactical.json | aggregate-player.json | aggregate-brand.json | aggregate-narrative.json_
_Run: python3 aggregate_flat.py to refresh_
"""
    with open(BRIEF, 'w') as f:
        f.write(brief)
    print(f"MORNING-BRIEF.md written: {BRIEF}")


def main():
    print("Loading analyses...")
    analyses, errors = load_all_analyses()

    if not analyses:
        print("No analyses found yet. Run run_sample_500.py first.")
        return

    n = len(analyses)
    print(f"Aggregating {n} clip analyses...")

    # Get cost from progress file
    cost = n * COST_PER_CLIP
    if PROGRESS.exists():
        try:
            with open(PROGRESS) as f:
                p = json.load(f)
            cost = p.get('cost_usd_this_run', cost)
        except Exception:
            pass

    tactical  = agg_tactical(analyses)
    player    = agg_player(analyses)
    brand     = agg_brand(analyses)
    narrative = agg_narrative(analyses)
    venue     = agg_venue(analyses)

    coverage_pct = round(n / CORPUS_TOTAL * 100, 2)

    summary = {
        'total_clips_analyzed': n,
        'sample_size': 500,
        'corpus_total': CORPUS_TOTAL,
        'corpus_coverage_pct': coverage_pct,
        'cost_usd_this_run': round(cost, 4),
        'errors_skipped': len(errors),
        'aggregated_at': datetime.datetime.utcnow().isoformat() + 'Z',
        'tactical': tactical,
        'player': player,
        'brand': brand,
        'narrative': narrative,
        'venue': venue,
    }

    # Write individual files
    for key in ['tactical', 'player', 'brand', 'narrative', 'venue']:
        with open(RUN_DIR / f'aggregate-{key}.json', 'w') as f:
            json.dump(summary[key], f, indent=2)
        print(f"  Written: aggregate-{key}.json")

    with open(RUN_DIR / 'full-corpus-summary.json', 'w') as f:
        json.dump(summary, f, indent=2)
    print(f"  Written: full-corpus-summary.json")

    update_morning_brief(summary, n, cost, len(errors))

    print(f"\nDone. {n} clips | {coverage_pct}% corpus coverage | ${cost:.4f} spent")
    print(f"Key stats:")
    print(f"  Dominant shot: {tactical.get('top_dominant_shot')}")
    print(f"  Avg viral score: {narrative.get('avg_viral_score')}")
    print(f"  Most common DUPR: {player.get('most_common_DUPR')}")
    print(f"  Investor demo clips: {narrative.get('investor_demo_clip_count')}")
    if brand['paddle_brands_ranked']:
        top = brand['paddle_brands_ranked'][0]
        print(f"  Top paddle brand: {top['brand']} ({top['sightings']} sightings)")

    return summary


if __name__ == '__main__':
    main()

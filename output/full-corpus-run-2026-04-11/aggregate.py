#!/usr/bin/env python3
"""
Aggregate all-angles analyses into corpus-level insights.
PickleBill / Courtana — 2026-04-11
"""

import json, glob, os, collections, statistics, datetime
from pathlib import Path

RUN_DIR   = Path(__file__).parent
ANALYSES  = RUN_DIR / 'analyses'
MANIFEST  = RUN_DIR / 'clip-manifest.json'
PROGRESS  = RUN_DIR / 'progress.json'

# Also load from previous runs
PREV_ANALYSES = [
    Path(__file__).parent.parent / 'batches/2026-04-11-tactical',
    Path(__file__).parent.parent / 'picklebill-batch-20260410',
    Path(__file__).parent.parent / 'batch-30-daas',
]


def load_all_analyses():
    """Load all analysis JSON files from this run and previous runs."""
    all_results = []
    errors = []

    # This run
    for f in glob.glob(str(ANALYSES / 'analysis_*.json')):
        try:
            with open(f) as fh:
                d = json.load(fh)
                if 'error' not in d or d.get('shot_analysis'):
                    all_results.append(d)
                else:
                    errors.append(f)
        except Exception as e:
            errors.append(f)

    # Previous runs
    for prev_dir in PREV_ANALYSES:
        if prev_dir.is_dir():
            for f in glob.glob(str(prev_dir / 'analysis_*.json')):
                try:
                    with open(f) as fh:
                        d = json.load(fh)
                        if 'error' not in d or d.get('shot_analysis'):
                            all_results.append(d)
                except Exception:
                    pass

    print(f"Loaded {len(all_results)} valid analyses ({len(errors)} errors skipped)")
    return all_results


def safe_get(d, *keys, default=None):
    """Safely navigate nested dicts."""
    for k in keys:
        if not isinstance(d, dict):
            return default
        d = d.get(k, default)
        if d is None:
            return default
    return d


def aggregate_tactical(analyses):
    shot_types = collections.Counter()
    rally_lengths = []
    kitchen_pcts = []
    error_types = collections.Counter()
    winning_shots = collections.Counter()
    sequences = []
    rally_type_dist = collections.Counter()

    for a in analyses:
        sa = a.get('shot_analysis', {})
        if not sa:
            continue

        for shot in sa.get('shots', []):
            st = shot.get('shot_type')
            if st:
                shot_types[st] += 1

        rl = sa.get('rally_length')
        if isinstance(rl, (int, float)) and rl > 0:
            rally_lengths.append(int(rl))

        kp = sa.get('kitchen_control_percentage')
        if isinstance(kp, (int, float)):
            kitchen_pcts.append(float(kp))

        et = sa.get('error_type')
        if et and et != 'null' and et is not None:
            error_types[str(et)] += 1

        ws = sa.get('winning_shot_type')
        if ws and ws != 'null' and ws is not None:
            winning_shots[str(ws)] += 1

        seq = sa.get('sequence_pattern')
        if seq and seq != 'null':
            sequences.append(str(seq))

        rt = sa.get('rally_type')
        if rt:
            rally_type_dist[str(rt)] += 1

    # Rally length distribution
    short = sum(1 for r in rally_lengths if r <= 3)
    medium = sum(1 for r in rally_lengths if 4 <= r <= 7)
    long_ = sum(1 for r in rally_lengths if r >= 8)
    total_rallies = len(rally_lengths)

    # Find winning shot sequences (most common patterns)
    seq_counter = collections.Counter(sequences)
    top_sequences = [{'pattern': p, 'count': c} for p, c in seq_counter.most_common(5)]

    return {
        'shot_type_frequency': dict(shot_types.most_common()),
        'rally_length_distribution': {
            'short_1_3': round(short / total_rallies * 100, 1) if total_rallies else 0,
            'medium_4_7': round(medium / total_rallies * 100, 1) if total_rallies else 0,
            'long_8plus': round(long_ / total_rallies * 100, 1) if total_rallies else 0,
            'sample_size': total_rallies
        },
        'rally_type_distribution': dict(rally_type_dist),
        'kitchen_control_avg': round(statistics.mean(kitchen_pcts), 1) if kitchen_pcts else None,
        'kitchen_control_sample_size': len(kitchen_pcts),
        'most_common_error': error_types.most_common(1)[0][0] if error_types else None,
        'error_type_breakdown': dict(error_types),
        'winning_shot_frequency': dict(winning_shots.most_common()),
        'winning_shot_sequences': top_sequences,
        'total_shots_catalogued': sum(shot_types.values()),
        'dominant_shot_overall': shot_types.most_common(1)[0][0] if shot_types else None,
    }


def aggregate_player(analyses):
    dupr_bins = collections.Counter()
    styles = collections.Counter()
    style_tags = collections.Counter()
    skill_labels = collections.Counter()
    skill_scores = collections.defaultdict(list)
    sig_moves = collections.Counter()

    SKILL_FIELDS = ['court_coverage', 'kitchen_mastery', 'power_game', 'touch_and_feel',
                    'athleticism', 'creativity', 'court_iq', 'consistency', 'composure', 'paddle_control']

    for a in analyses:
        si = a.get('skill_indicators', {})
        if not si:
            continue

        dupr = si.get('DUPR_estimate')
        if dupr:
            dupr_bins[str(dupr)] += 1

        agg = si.get('aggression_style')
        if agg:
            styles[str(agg)] += 1

        for tag in si.get('play_style_tags', []) or []:
            style_tags[str(tag)] += 1

        label = si.get('skill_level_label')
        if label:
            skill_labels[str(label)] += 1

        for field in SKILL_FIELDS:
            val = si.get(field)
            if isinstance(val, (int, float)):
                skill_scores[field].append(float(val))

        for move in si.get('signature_moves_observed', []) or []:
            sig_moves[str(move)] += 1

    avg_scores = {
        field: round(statistics.mean(vals), 2)
        for field, vals in skill_scores.items() if vals
    }

    return {
        'skill_distribution': dict(dupr_bins),
        'skill_label_distribution': dict(skill_labels),
        'most_common_style': styles.most_common(1)[0][0] if styles else None,
        'aggression_style_breakdown': dict(styles),
        'top_play_style_tags': [{'tag': t, 'count': c} for t, c in style_tags.most_common(15)],
        'avg_skill_scores': avg_scores,
        'signature_move_frequency': dict(sig_moves.most_common(10)),
        'sample_size': len(analyses)
    }


def aggregate_brand(analyses):
    paddle_brands = collections.Counter()
    apparel_brands = collections.Counter()
    equipment = collections.Counter()
    sponsorship = collections.Counter()
    court_branding_seen = []

    for a in analyses:
        bd = a.get('brand_detection', {})
        if not bd:
            continue

        for b in bd.get('paddle_brands', []) or []:
            if b and str(b).lower() not in ['none', 'unknown', 'unclear', 'n/a', '']:
                paddle_brands[str(b).strip().title()] += 1

        for b in bd.get('apparel_brands', []) or []:
            if b and str(b).lower() not in ['none', 'unknown', 'unclear', 'n/a', '']:
                apparel_brands[str(b).strip().title()] += 1

        for b in bd.get('equipment_visible', []) or []:
            if b and str(b).lower() not in ['none', 'unknown', 'unclear', '']:
                equipment[str(b).strip()] += 1

        for b in bd.get('sponsorship_logos', []) or []:
            if b and str(b).lower() not in ['none', 'unknown', 'unclear', '']:
                sponsorship[str(b).strip().title()] += 1

        cb = bd.get('court_branding')
        if cb and cb not in ['none', 'None', 'null', None, '']:
            court_branding_seen.append(str(cb))

    # Identify whitespace: common equipment brands not yet partners
    known_paddles = set(paddle_brands.keys())
    # These are theoretical partnerships — flag top visible brands
    top_paddle_list = [{'brand': b, 'appearances': c} for b, c in paddle_brands.most_common(10)]
    top_apparel_list = [{'brand': b, 'appearances': c} for b, c in apparel_brands.most_common(10)]

    return {
        'paddle_brands': dict(paddle_brands.most_common()),
        'apparel_brands': dict(apparel_brands.most_common()),
        'equipment_visible': dict(equipment.most_common()),
        'sponsorship_logos': dict(sponsorship.most_common()),
        'top_paddle_brands_ranked': top_paddle_list,
        'top_apparel_brands_ranked': top_apparel_list,
        'court_branding_notes': court_branding_seen[:10],
        'sponsorship_whitespace': 'Top visible paddle brands with no confirmed Courtana partnership: ' +
            ', '.join([b for b, _ in paddle_brands.most_common(5)]) if paddle_brands else 'Insufficient data',
        'sample_size': len(analyses)
    }


def aggregate_narrative(analyses):
    viral_scores = []
    categories = collections.Counter()
    sponsor_moments = 0
    investor_clips = []
    comedy_scores = []
    story_arcs = []

    for a in analyses:
        narr = a.get('narrative', {})
        if not narr:
            continue

        vs = narr.get('viral_score')
        if isinstance(vs, (int, float)):
            viral_scores.append(float(vs))

        cat = narr.get('highlight_category')
        if cat:
            categories[str(cat)] += 1

        if narr.get('sponsor_pitch_moment') is True:
            sponsor_moments += 1

        cs = narr.get('comedy_potential')
        if isinstance(cs, (int, float)):
            comedy_scores.append(float(cs))

        if narr.get('best_for_investor_demo') is True:
            clip_meta = a.get('_clip_meta', {})
            url = clip_meta.get('url') or safe_get(a, 'clip_url', default='')
            investor_clips.append({
                'uuid': a.get('clip_uuid') or clip_meta.get('uuid', ''),
                'url': url,
                'viral_score': vs,
                'why': narr.get('why_memorable', ''),
                'caption': narr.get('social_caption_draft', '')
            })

        arc = narr.get('story_arc')
        if arc and arc != 'null':
            story_arcs.append(str(arc))

    # Sort investor clips by viral score
    investor_clips.sort(key=lambda x: x.get('viral_score') or 0, reverse=True)

    return {
        'avg_viral_score': round(statistics.mean(viral_scores), 2) if viral_scores else None,
        'viral_score_distribution': {
            'high_8plus': sum(1 for v in viral_scores if v >= 8),
            'medium_5_7': sum(1 for v in viral_scores if 5 <= v < 8),
            'low_under_5': sum(1 for v in viral_scores if v < 5),
            'sample_size': len(viral_scores)
        },
        'avg_comedy_score': round(statistics.mean(comedy_scores), 2) if comedy_scores else None,
        'top_highlight_categories': [{'category': c, 'count': n} for c, n in categories.most_common()],
        'sponsor_pitch_clips_count': sponsor_moments,
        'best_clips_for_showcase': investor_clips[:10],
        'sample_size': len(analyses)
    }


def compute_venue_bias(analyses):
    venue_types = collections.Counter()
    for a in analyses:
        vs = a.get('venue_signals', {})
        if vs:
            vt = vs.get('estimated_venue_type')
            if vt:
                venue_types[str(vt)] += 1

    top_venue = venue_types.most_common(1)
    if top_venue:
        top_name, top_count = top_venue[0]
        pct = round(top_count / len(analyses) * 100, 1) if analyses else 0
        return f"{pct}% of clips appear to be from '{top_name}' venue type — confidence capped accordingly"
    return "Venue distribution unknown"


def main():
    print("Loading analyses...")
    analyses = load_all_analyses()

    if not analyses:
        print("No analyses found. Run run_all_angles.py first.")
        return

    n = len(analyses)
    print(f"Aggregating {n} clip analyses...")

    # Load progress for total cost
    total_cost = 0.0
    corpus_total = 8214
    if PROGRESS.exists():
        with open(PROGRESS) as f:
            prog = json.load(f)
            total_cost = prog.get('total_cost_usd', 0.0)

    print("Computing tactical aggregate...")
    tactical = aggregate_tactical(analyses)

    print("Computing player aggregate...")
    player = aggregate_player(analyses)

    print("Computing brand aggregate...")
    brand = aggregate_brand(analyses)

    print("Computing narrative aggregate...")
    narrative = aggregate_narrative(analyses)

    venue_bias = compute_venue_bias(analyses)
    coverage_pct = round(n / corpus_total * 100, 2)

    # Save individual aggregate files
    with open(RUN_DIR / 'aggregate-tactical.json', 'w') as f:
        json.dump(tactical, f, indent=2)

    with open(RUN_DIR / 'aggregate-player.json', 'w') as f:
        json.dump(player, f, indent=2)

    with open(RUN_DIR / 'aggregate-brand.json', 'w') as f:
        json.dump(brand, f, indent=2)

    with open(RUN_DIR / 'aggregate-narrative.json', 'w') as f:
        json.dump(narrative, f, indent=2)

    # Combined summary
    summary = {
        'total_clips_analyzed': n,
        'total_cost_usd': round(total_cost, 4),
        'analysis_date': datetime.datetime.utcnow().isoformat() + 'Z',
        'corpus_total_known': corpus_total,
        'corpus_coverage_pct': coverage_pct,
        'venue_bias_warning': venue_bias,
        'tactical': tactical,
        'player': player,
        'brand': brand,
        'narrative': narrative
    }

    with open(RUN_DIR / 'full-corpus-summary.json', 'w') as f:
        json.dump(summary, f, indent=2)

    print(f"\nAggregation complete!")
    print(f"  Clips analyzed: {n}")
    print(f"  Coverage: {coverage_pct}% of corpus")
    print(f"  Files written to: {RUN_DIR}")
    print(f"\nKey findings:")
    print(f"  Dominant shot type: {tactical.get('dominant_shot_overall')}")
    print(f"  Avg viral score: {narrative.get('avg_viral_score')}")
    print(f"  Most common DUPR: {player['skill_distribution']}")
    if brand['paddle_brands']:
        top_paddle = list(brand['paddle_brands'].items())[0]
        print(f"  Top paddle brand: {top_paddle[0]} ({top_paddle[1]} sightings)")

    return summary


if __name__ == '__main__':
    main()

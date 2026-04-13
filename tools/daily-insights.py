#!/usr/bin/env python3
"""
daily-insights.py — Generate a daily analytics digest
======================================================
Runs preset queries against the live gh-pages corpus and writes a
Markdown digest to output/daily-insights/YYYY-MM-DD.md.

Intended to be called from the `morning-brief-daily` scheduled task.

Usage:
  python3 tools/daily-insights.py             # write today's digest
  python3 tools/daily-insights.py --stdout    # print to stdout instead
"""

import json
import os
import sys
import argparse
import subprocess
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).parent.parent
OUTDIR = ROOT / "output" / "daily-insights"


def load_gh_pages_corpus():
    """Source of truth: corpus-export.json from gh-pages."""
    result = subprocess.run(
        ["git", "show", "gh-pages:corpus-export.json"],
        capture_output=True, text=True, cwd=ROOT
    )
    if result.returncode != 0:
        raise RuntimeError("Could not read gh-pages:corpus-export.json")
    return json.loads(result.stdout)


def canon_brand(b):
    """Normalize common brand name variants."""
    if not b: return b
    low = b.lower().strip()
    if low == 'joola': return 'JOOLA'
    if low == 'pickleball': return 'Pickleball'
    return b.strip()


def compute_insights(corpus):
    """Compute all the aggregated insights for the digest."""
    n = len(corpus)

    # Brand aggregation
    brand_apps = Counter()
    brand_clips = defaultdict(set)
    brand_quality = defaultdict(list)
    for c in corpus:
        seen_in_clip = set()
        for raw in (c.get('brands') or []):
            if not raw: continue
            b = canon_brand(raw)
            brand_apps[b] += 1
            if b not in seen_in_clip:
                seen_in_clip.add(b)
                brand_clips[b].add(c.get('uuid', c.get('video_url', '')))
                if c.get('quality'):
                    brand_quality[b].append(c['quality'])

    # Arc aggregation
    arc_counts = Counter()
    arc_quality = defaultdict(list)
    arc_viral = defaultdict(list)
    for c in corpus:
        arc = c.get('arc')
        if not arc: continue
        arc_counts[arc] += 1
        if c.get('quality'): arc_quality[arc].append(c['quality'])
        if c.get('viral'): arc_viral[arc].append(c['viral'])

    # Shot aggregation
    shot_counts = Counter()
    shot_quality = defaultdict(list)
    for c in corpus:
        s = c.get('dominant_shot')
        if not s: continue
        shot_counts[s] += 1
        if c.get('quality'): shot_quality[s].append(c['quality'])

    # Quality / viral distributions
    quality_dist = Counter()
    viral_dist = Counter()
    q_sum = q_n = v_sum = v_n = 0
    for c in corpus:
        if c.get('quality'):
            quality_dist[int(c['quality'])] += 1
            q_sum += c['quality']; q_n += 1
        if c.get('viral'):
            viral_dist[int(c['viral'])] += 1
            v_sum += c['viral']; v_n += 1

    # Skills averages
    skill_keys = ['kitchen', 'court_coverage', 'power', 'touch', 'athleticism', 'creativity', 'court_iq', 'consistency', 'composure']
    skill_sums = {k: [] for k in skill_keys}
    for c in corpus:
        sk = c.get('skills') or {}
        for k in skill_keys:
            v = sk.get(k)
            if isinstance(v, (int, float)) and v > 0:
                skill_sums[k].append(v)

    # Top clips by quality + viral
    scored = [
        (c, (c.get('quality', 0) or 0) * 10 + (c.get('viral', 0) or 0))
        for c in corpus
    ]
    top_clips = sorted(scored, key=lambda x: x[1], reverse=True)[:5]

    # Viral standouts
    viral_standouts = sorted(
        [c for c in corpus if (c.get('viral', 0) or 0) >= 7],
        key=lambda c: -c.get('viral', 0)
    )[:5]

    return {
        'n': n,
        'avg_quality': round(q_sum / q_n, 2) if q_n else None,
        'avg_viral': round(v_sum / v_n, 2) if v_n else None,
        'brand_apps': brand_apps,
        'brand_clips': {k: len(v) for k, v in brand_clips.items()},
        'brand_quality': {k: round(sum(v)/len(v), 2) for k, v in brand_quality.items() if v},
        'unique_brands': len(brand_apps),
        'arc_counts': arc_counts,
        'arc_quality_avg': {k: round(sum(v)/len(v), 2) for k, v in arc_quality.items() if v},
        'arc_viral_avg': {k: round(sum(v)/len(v), 2) for k, v in arc_viral.items() if v},
        'shot_counts': shot_counts,
        'shot_quality_avg': {k: round(sum(v)/len(v), 2) for k, v in shot_quality.items() if v},
        'quality_dist': quality_dist,
        'viral_dist': viral_dist,
        'skill_avg': {k: round(sum(v)/len(v), 2) if v else None for k, v in skill_sums.items()},
        'top_clips': [c[0] for c in top_clips],
        'viral_standouts': viral_standouts,
    }


def format_digest(insights, date_str):
    """Format insights as a Markdown digest."""
    n = insights['n']
    lines = []
    lines.append(f"# Pickle DaaS · Daily Insights · {date_str}")
    lines.append("")
    lines.append(f"_Auto-generated from gh-pages `corpus-export.json`_")
    lines.append("")
    lines.append("## Corpus Snapshot")
    lines.append("")
    lines.append(f"- **Total clips analyzed:** {n:,}")
    lines.append(f"- **Unique brands detected:** {insights['unique_brands']}")
    lines.append(f"- **Average quality score:** {insights['avg_quality']} / 10")
    lines.append(f"- **Average viral potential:** {insights['avg_viral']} / 10")
    lines.append(f"- **Total spend (at $0.0054/clip):** ${n * 0.0054:.2f}")
    lines.append("")

    # Top brands
    lines.append("## 🏷️ Top Brands")
    lines.append("")
    lines.append("| Rank | Brand | Appearances | Clips | Share |")
    lines.append("|------|-------|-------------|-------|-------|")
    for i, (brand, apps) in enumerate(insights['brand_apps'].most_common(10), 1):
        clips = insights['brand_clips'].get(brand, 0)
        share = f"{clips / n * 100:.1f}%"
        lines.append(f"| {i} | {brand} | {apps} | {clips} | {share} |")
    lines.append("")

    # Dominant brand callout
    top_brand = insights['brand_apps'].most_common(1)
    if top_brand:
        tb, ta = top_brand[0]
        clips = insights['brand_clips'].get(tb, 0)
        share_pct = clips / n * 100
        lines.append(f"> **Dominant brand:** {tb} appears in **{share_pct:.0f}%** of clips ({clips} of {n})")
        lines.append("")

    # Story arcs
    lines.append("## 📖 Story Arc Distribution")
    lines.append("")
    lines.append("| Arc | Clips | % | Avg Quality | Avg Viral |")
    lines.append("|-----|-------|---|-------------|-----------|")
    for arc, count in insights['arc_counts'].most_common(8):
        pct = f"{count / n * 100:.1f}%"
        q = insights['arc_quality_avg'].get(arc, '—')
        v = insights['arc_viral_avg'].get(arc, '—')
        lines.append(f"| {arc} | {count} | {pct} | {q} | {v} |")
    lines.append("")

    # Shot types
    lines.append("## 🎯 Shot Type Distribution")
    lines.append("")
    lines.append("| Shot | Clips | Avg Quality |")
    lines.append("|------|-------|-------------|")
    for shot, count in insights['shot_counts'].most_common(8):
        q = insights['shot_quality_avg'].get(shot, '—')
        lines.append(f"| {shot} | {count} | {q} |")
    lines.append("")

    # Skills
    lines.append("## 💪 Skill Profile (corpus average)")
    lines.append("")
    lines.append("| Skill | Average |")
    lines.append("|-------|---------|")
    for k, v in insights['skill_avg'].items():
        if v is not None:
            label = k.replace('_', ' ').title()
            lines.append(f"| {label} | {v} |")
    lines.append("")

    # Top clips
    lines.append("## ⭐ Top 5 Clips (quality + viral combined)")
    lines.append("")
    for i, c in enumerate(insights['top_clips'], 1):
        quality = c.get('quality', '—')
        viral = c.get('viral', '—')
        arc = c.get('arc', '—')
        summary = (c.get('summary') or '')[:100]
        url = c.get('video_url', '')
        lines.append(f"{i}. **Quality {quality} / Viral {viral}** · {arc}")
        if summary:
            lines.append(f"   {summary}")
        if url:
            lines.append(f"   [watch]({url})")
        lines.append("")

    # Viral standouts
    if insights['viral_standouts']:
        lines.append("## 🔥 Viral Standouts (viral ≥ 7)")
        lines.append("")
        for c in insights['viral_standouts']:
            viral = c.get('viral')
            quality = c.get('quality', '—')
            caption = (c.get('social_caption') or '').strip()[:150]
            url = c.get('video_url', '')
            lines.append(f"- **Viral {viral}** · Quality {quality}")
            if caption:
                lines.append(f"  > {caption}")
            if url:
                lines.append(f"  [watch]({url})")
        lines.append("")

    # Quality distribution visualization
    lines.append("## 📊 Quality Distribution")
    lines.append("")
    max_count = max(insights['quality_dist'].values()) if insights['quality_dist'] else 1
    for score in sorted(insights['quality_dist'].keys(), reverse=True):
        count = insights['quality_dist'][score]
        bar = '█' * int(count / max_count * 40)
        lines.append(f"- **Quality {score}:** `{bar}` {count}")
    lines.append("")

    # Actionable observations
    lines.append("## 🔍 Observations & Actions")
    lines.append("")
    observations = []

    # Brand dominance signal
    if top_brand:
        tb, ta = top_brand[0]
        share = insights['brand_clips'].get(tb, 0) / n * 100
        if share >= 40:
            observations.append(f"**{tb} market dominance** ({share:.0f}% of clips) → consider a partnership pitch to {tb}.")

    # Viral vs quality gap
    if insights['avg_quality'] and insights['avg_viral']:
        gap = insights['avg_quality'] - insights['avg_viral']
        if gap >= 2:
            observations.append(f"**Quality-viral gap** ({gap:.1f} pts): clips are technically good but not packaging as viral. Consider social editing strategy.")

    # Skill concentration
    skill_vals = [(k, v) for k, v in insights['skill_avg'].items() if v is not None]
    skill_vals.sort(key=lambda x: -x[1])
    if len(skill_vals) >= 2:
        top_sk = skill_vals[0]
        bot_sk = skill_vals[-1]
        observations.append(f"**Skill profile:** players average high on *{top_sk[0].replace('_', ' ')}* ({top_sk[1]}) and low on *{bot_sk[0].replace('_', ' ')}* ({bot_sk[1]}).")

    # Viral standout count
    v_high = sum(1 for c in insights['viral_dist'] if c >= 7) if insights['viral_dist'] else 0
    viral_sum = sum(insights['viral_dist'].get(s, 0) for s in range(7, 11))
    if viral_sum > 0:
        observations.append(f"**{viral_sum} high-viral candidates** ({viral_sum/n*100:.0f}% of corpus) ready for social posting.")

    if not observations:
        observations.append("No standout signals today. Corpus looks healthy.")

    for obs in observations:
        lines.append(f"- {obs}")
    lines.append("")

    # Footer
    lines.append("---")
    lines.append("")
    lines.append(f"_Generated at {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')} · "
                 f"[Live Dashboard](https://picklebill.github.io/pickle-daas-data/dashboards/data-lab.html) · "
                 f"[Query Cookbook](https://github.com/PickleBill/pickle-daas-data/blob/gh-pages/supabase/QUERY-COOKBOOK.md)_")

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--stdout", action="store_true", help="Print digest to stdout instead of writing file")
    parser.add_argument("--date", help="Override date (YYYY-MM-DD)")
    args = parser.parse_args()

    try:
        corpus = load_gh_pages_corpus()
    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(1)

    insights = compute_insights(corpus)
    date_str = args.date or datetime.now().strftime("%Y-%m-%d")
    digest = format_digest(insights, date_str)

    if args.stdout:
        print(digest)
        return

    OUTDIR.mkdir(parents=True, exist_ok=True)
    out_path = OUTDIR / f"{date_str}.md"
    out_path.write_text(digest)

    print(f"✅ Wrote {out_path}")
    print(f"   Corpus: {insights['n']} clips")
    print(f"   Top brand: {next(iter(insights['brand_apps']), '—')}")
    print(f"   Avg quality: {insights['avg_quality']}")


if __name__ == "__main__":
    main()

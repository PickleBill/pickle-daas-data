#!/usr/bin/env python3
"""
Pickle DaaS — Model Quality Monitor
=====================================
Reads all analysis JSONs across batches and computes:
  - Field fill rates per batch (what % of clips have each field populated)
  - Regression detection vs. prior batch
  - Quality score trends
  - Brand detection rates
  - Multi-batch comparison table

Generates:
  output/model-monitor-YYYYMMDD.md   — Text report
  output/model-monitor-dashboard.html — Visual dashboard (open in browser)

USAGE:
  python tools/model-monitor.py
  python tools/model-monitor.py --dirs output/batch-30-daas output/picklebill-batch-001
  python tools/model-monitor.py --since 2026-04-01  (only batches after date)

Add to analyzer post-run hook by appending:
  os.system('python tools/model-monitor.py')
"""

import os
import sys
import json
import glob
import argparse
from datetime import datetime
from pathlib import Path
from collections import defaultdict


# All tracked fields and their "expected type" for fill detection
TRACKED_FIELDS = {
    # clip_meta
    'clip_meta.clip_quality_score':     ('number', 'Clip Quality Score'),
    'clip_meta.viral_potential_score':  ('number', 'Viral Potential Score'),
    'clip_meta.watchability_score':     ('number', 'Watchability Score'),
    # skill_indicators
    'skill_indicators.kitchen_mastery_rating':   ('number', 'Kitchen Mastery'),
    'skill_indicators.court_iq_rating':          ('number', 'Court IQ'),
    'skill_indicators.athleticism_rating':       ('number', 'Athleticism'),
    'skill_indicators.signature_move_detected':  ('string', 'Signature Move ⚡'),
    'skill_indicators.improvement_opportunities':('list',   'Improvement Opps'),
    'skill_indicators.play_style_tags':          ('list',   'Play Style Tags'),
    # badge_intelligence
    'badge_intelligence.predicted_badges':       ('list',   'Predicted Badges ⚡'),
    # commentary
    'commentary.ron_burgundy_voice':             ('string', 'Ron Burgundy Voice ⚡'),
    'commentary.social_media_caption':           ('string', 'Social Caption'),
    'commentary.coaching_breakdown':             ('string', 'Coaching Breakdown'),
    # daas_signals
    'daas_signals.estimated_player_rating_dupr': ('string', 'DUPR Estimate ⚡'),
    'daas_signals.clip_summary_one_sentence':    ('string', 'One-Sentence Summary ⚡'),
    'daas_signals.data_richness_score':          ('number', 'Data Richness'),
    # brand_detection
    'brand_detection.brands':                   ('list',   'Brand Detections'),
    # storytelling
    'storytelling.story_arc':                   ('string', 'Story Arc'),
    'storytelling.narrative_arc_summary':       ('string', 'Narrative Summary'),
}
# ⚡ = previously weak fields fixed in v1.1


BATCH_DIRS = [
    ('batch-30-daas',            'output/batch-30-daas'),
    ('picklebill-batch-001',     'output/picklebill-batch-001'),
    ('picklebill-batch-20260410','output/picklebill-batch-20260410'),
]


def get_nested(data, dotpath):
    """Get a nested value from dict using dot notation. Returns None if missing."""
    keys = dotpath.split('.')
    val = data
    for k in keys:
        if not isinstance(val, dict):
            return None
        val = val.get(k)
    return val


def is_filled(value, expected_type):
    """Return True if a field value counts as 'filled' (not null/empty)."""
    if value is None:
        return False
    if expected_type == 'number':
        return isinstance(value, (int, float)) and value > 0
    if expected_type == 'string':
        return isinstance(value, str) and len(value.strip()) > 3
    if expected_type == 'list':
        return isinstance(value, list) and len(value) > 0
    return bool(value)


def analyze_batch(directory):
    """Analyze all clips in a directory. Returns batch stats dict."""
    pattern = os.path.join(directory, 'analysis_*.json')
    files = sorted(glob.glob(pattern))

    if not files:
        return None

    stats = {
        'directory':   directory,
        'batch_name':  os.path.basename(directory),
        'clip_count':  len(files),
        'field_rates': {},   # field_path -> fill_rate (0.0-1.0)
        'field_counts': {},  # field_path -> filled count
        'quality_scores': [],
        'viral_scores':   [],
        'brand_rates':    [],
        'badge_counts':   [],
        'dupr_values':    [],
        'analyzed_dates': [],
    }

    for filepath in files:
        try:
            with open(filepath) as f:
                data = json.load(f)
        except Exception:
            continue

        if not data.get('clip_meta'):
            continue

        # Track field fills
        for field_path, (ftype, _) in TRACKED_FIELDS.items():
            val = get_nested(data, field_path)
            filled = is_filled(val, ftype)
            stats['field_counts'][field_path] = stats['field_counts'].get(field_path, 0) + (1 if filled else 0)

        # Quality metrics
        q = data.get('clip_meta', {}).get('clip_quality_score')
        if q:
            stats['quality_scores'].append(q)
        v = data.get('clip_meta', {}).get('viral_potential_score')
        if v:
            stats['viral_scores'].append(v)

        # Brands
        brands = data.get('brand_detection', {}).get('brands', [])
        stats['brand_rates'].append(len(brands))

        # Badges
        badges = data.get('badge_intelligence', {}).get('predicted_badges', [])
        stats['badge_counts'].append(len(badges))

        # DUPR
        dupr = data.get('daas_signals', {}).get('estimated_player_rating_dupr')
        if dupr and dupr != 'null':
            stats['dupr_values'].append(dupr)

        # Date
        ts = data.get('analyzed_at', '')
        if ts:
            stats['analyzed_dates'].append(ts[:10])

    # Compute rates
    n = stats['clip_count']
    for field_path in TRACKED_FIELDS:
        count = stats['field_counts'].get(field_path, 0)
        stats['field_rates'][field_path] = round(count / n, 3) if n > 0 else 0

    return stats


def detect_regressions(batches):
    """Compare consecutive batches and flag fields where fill rate dropped >5%."""
    regressions = []
    for i in range(1, len(batches)):
        prev = batches[i-1]
        curr = batches[i]
        for field_path, (_, label) in TRACKED_FIELDS.items():
            prev_rate = prev['field_rates'].get(field_path, 0)
            curr_rate = curr['field_rates'].get(field_path, 0)
            delta = curr_rate - prev_rate
            if delta < -0.05:  # >5% regression
                regressions.append({
                    'field':      field_path,
                    'label':      label,
                    'prev_batch': prev['batch_name'],
                    'curr_batch': curr['batch_name'],
                    'prev_rate':  prev_rate,
                    'curr_rate':  curr_rate,
                    'delta':      delta,
                })
    return regressions


def write_markdown_report(batches, regressions, output_path):
    """Write a human-readable markdown quality report."""
    now = datetime.now().strftime('%Y-%m-%d %H:%M')
    lines = [
        f"# Pickle DaaS — Model Quality Monitor",
        f"**Generated:** {now}",
        f"**Batches analyzed:** {len(batches)}",
        f"**Total clips:** {sum(b['clip_count'] for b in batches)}",
        "",
        "---",
        "",
    ]

    # Regression alerts
    if regressions:
        lines += [
            "## ⚠️ Regressions Detected",
            "",
        ]
        for r in regressions:
            lines.append(f"- **{r['label']}**: {r['prev_batch']} ({r['prev_rate']*100:.0f}%) → {r['curr_batch']} ({r['curr_rate']*100:.0f}%) — dropped {abs(r['delta'])*100:.0f}%")
        lines += ["", "---", ""]
    else:
        lines += ["## ✅ No Regressions Detected", "", "---", ""]

    # Per-batch fill rates table
    batch_names = [b['batch_name'] for b in batches]
    lines += [
        "## Field Fill Rates by Batch",
        "",
        f"| Field | {' | '.join(batch_names)} |",
        f"|{'---|' * (len(batches) + 1)}",
    ]

    for field_path, (_, label) in TRACKED_FIELDS.items():
        cells = []
        for b in batches:
            rate = b['field_rates'].get(field_path, 0)
            pct = f"{rate*100:.0f}%"
            if rate >= 0.90:
                pct = f"✅ {pct}"
            elif rate >= 0.70:
                pct = f"⚠️ {pct}"
            else:
                pct = f"❌ {pct}"
            cells.append(pct)
        lines.append(f"| {label} | {' | '.join(cells)} |")

    lines += ["", "---", ""]

    # Quality metrics
    lines += ["## Quality Metrics by Batch", ""]
    for b in batches:
        qs = b['quality_scores']
        vs = b['viral_scores']
        bs = b['brand_rates']
        bgs = b['badge_counts']
        avg_q = sum(qs)/len(qs) if qs else 0
        avg_v = sum(vs)/len(vs) if vs else 0
        avg_brands = sum(bs)/len(bs) if bs else 0
        avg_badges = sum(bgs)/len(bgs) if bgs else 0
        lines.append(f"**{b['batch_name']}** ({b['clip_count']} clips)")
        lines.append(f"- Avg quality: {avg_q:.1f}/10 | Avg viral: {avg_v:.1f}/10")
        lines.append(f"- Avg brands/clip: {avg_brands:.1f} | Avg badges/clip: {avg_badges:.1f}")
        if b['dupr_values']:
            from collections import Counter
            top_dupr = Counter(b['dupr_values']).most_common(1)[0]
            lines.append(f"- Most common DUPR estimate: {top_dupr[0]} ({top_dupr[1]} clips)")
        lines.append("")

    lines += [
        "---",
        "",
        "## Recommendations",
        "",
        "Fields at <70% fill rate need prompt attention:",
    ]
    for field_path, (_, label) in TRACKED_FIELDS.items():
        # Check if any batch has low fill rate
        for b in batches:
            rate = b['field_rates'].get(field_path, 1.0)
            if rate < 0.70:
                lines.append(f"- **{label}** in `{b['batch_name']}`: {rate*100:.0f}% — add few-shot examples or mark REQUIRED")
                break

    with open(output_path, 'w') as f:
        f.write('\n'.join(lines))


def generate_dashboard_html(batches, regressions):
    """Generate the visual monitoring dashboard HTML."""

    batch_names_js = json.dumps([b['batch_name'] for b in batches])
    clip_counts_js = json.dumps([b['clip_count'] for b in batches])

    # Prepare fill rate data for chart
    # Key fields to highlight
    key_fields = [
        'skill_indicators.signature_move_detected',
        'badge_intelligence.predicted_badges',
        'daas_signals.estimated_player_rating_dupr',
        'commentary.ron_burgundy_voice',
        'daas_signals.clip_summary_one_sentence',
        'skill_indicators.kitchen_mastery_rating',
        'brand_detection.brands',
    ]
    key_labels = [TRACKED_FIELDS[f][1].replace(' ⚡','') for f in key_fields]

    # Dataset per batch
    colors = ['rgba(100,116,139,0.7)', 'rgba(59,130,246,0.8)', 'rgba(0,230,118,0.9)']
    datasets = []
    for i, b in enumerate(batches):
        color = colors[min(i, len(colors)-1)]
        datasets.append({
            'label': b['batch_name'],
            'data': [round(b['field_rates'].get(f, 0) * 100, 1) for f in key_fields],
            'backgroundColor': color,
            'borderColor': color.replace('0.7', '1').replace('0.8', '1').replace('0.9', '1'),
            'borderWidth': 1,
        })

    datasets_js = json.dumps(datasets)
    key_labels_js = json.dumps(key_labels)

    # Quality trends
    quality_by_batch = []
    for b in batches:
        qs = b['quality_scores']
        quality_by_batch.append(round(sum(qs)/len(qs), 1) if qs else 0)
    quality_js = json.dumps(quality_by_batch)

    # Brand rates
    brand_by_batch = []
    for b in batches:
        bs = b['brand_rates']
        brand_by_batch.append(round(sum(bs)/len(bs), 1) if bs else 0)
    brand_js = json.dumps(brand_by_batch)

    # Regression alerts HTML
    if regressions:
        reg_html = ''.join([
            f'<div class="alert">⚠️ <strong>{r["label"]}</strong>: {r["prev_batch"]} ({r["prev_rate"]*100:.0f}%) → {r["curr_batch"]} ({r["curr_rate"]*100:.0f}%) — dropped {abs(r["delta"])*100:.0f}%</div>'
            for r in regressions
        ])
    else:
        reg_html = '<div class="ok">✅ No regressions detected across all batches.</div>'

    # Full field table HTML
    table_rows = ''
    for field_path, (_, label) in TRACKED_FIELDS.items():
        cells = ''
        for b in batches:
            rate = b['field_rates'].get(field_path, 0)
            pct = rate * 100
            cls = 'good' if pct >= 90 else ('warn' if pct >= 70 else 'bad')
            cells += f'<td class="rate {cls}">{pct:.0f}%</td>'
        table_rows += f'<tr><td class="field-name">{label}</td>{cells}</tr>\n'

    batch_header = ''.join([f'<th>{b["batch_name"]}</th>' for b in batches])
    now = datetime.now().strftime('%Y-%m-%d %H:%M')

    total_clips = sum(b['clip_count'] for b in batches)
    total_batches = len(batches)

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Pickle DaaS — Model Quality Monitor</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap" rel="stylesheet">
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
<style>
  :root {{
    --bg: #0A0E17; --surface: #111827; --card: #1a2236;
    --border: #1e2a3a; --green: #00E676; --gold: #F59E0B;
    --red: #ef4444; --blue: #3B82F6; --text: #F1F5F9; --muted: #64748B;
  }}
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{ font-family: 'Inter', sans-serif; background: var(--bg); color: var(--text); padding: 24px 16px; }}
  .wrap {{ max-width: 1100px; margin: 0 auto; }}

  h1 {{ font-size: 22px; font-weight: 800; margin-bottom: 4px; }}
  .subtitle {{ font-size: 12px; color: var(--muted); margin-bottom: 24px; }}

  .kpi-row {{ display: flex; gap: 16px; margin-bottom: 24px; flex-wrap: wrap; }}
  .kpi {{ background: var(--surface); border: 1px solid var(--border); border-radius: 10px;
         padding: 16px 20px; flex: 1; min-width: 120px; }}
  .kpi-val {{ font-size: 28px; font-weight: 800; color: var(--green); line-height: 1; }}
  .kpi-label {{ font-size: 10px; color: var(--muted); margin-top: 4px; text-transform: uppercase; letter-spacing: 0.5px; }}

  .section {{ margin-bottom: 28px; }}
  .section-title {{ font-size: 11px; font-weight: 700; color: var(--muted); text-transform: uppercase;
                   letter-spacing: 1px; margin-bottom: 14px; }}

  .alerts {{ display: flex; flex-direction: column; gap: 8px; margin-bottom: 20px; }}
  .alert {{ background: rgba(239,68,68,0.1); border: 1px solid rgba(239,68,68,0.3);
           border-radius: 8px; padding: 10px 14px; font-size: 12px; color: #fca5a5; }}
  .ok {{ background: rgba(0,230,118,0.08); border: 1px solid rgba(0,230,118,0.2);
        border-radius: 8px; padding: 10px 14px; font-size: 12px; color: var(--green); }}

  .charts-row {{ display: grid; grid-template-columns: 2fr 1fr; gap: 16px; margin-bottom: 24px; }}
  .chart-card {{ background: var(--surface); border: 1px solid var(--border); border-radius: 12px; padding: 20px; }}
  .chart-title {{ font-size: 11px; font-weight: 700; color: var(--muted); text-transform: uppercase;
                 letter-spacing: 1px; margin-bottom: 16px; }}

  table {{ width: 100%; border-collapse: collapse; background: var(--surface);
           border: 1px solid var(--border); border-radius: 12px; overflow: hidden; }}
  th {{ background: var(--card); font-size: 10px; font-weight: 700; color: var(--muted);
       text-transform: uppercase; letter-spacing: 0.5px; padding: 10px 12px; text-align: left; }}
  td {{ padding: 8px 12px; border-bottom: 1px solid var(--border); font-size: 12px; }}
  tr:last-child td {{ border-bottom: none; }}
  .field-name {{ color: var(--text); font-weight: 500; }}
  td.rate {{ text-align: center; font-weight: 700; font-size: 11px; }}
  td.rate.good {{ color: #4ade80; }}
  td.rate.warn {{ color: #fbbf24; }}
  td.rate.bad  {{ color: #f87171; }}

  .footer {{ text-align: center; font-size: 11px; color: var(--muted); margin-top: 24px; }}
  @media (max-width: 600px) {{ .charts-row {{ grid-template-columns: 1fr; }} }}
</style>
</head>
<body>
<div class="wrap">
  <h1>Model Quality Monitor</h1>
  <div class="subtitle">Pickle DaaS · Gemini 2.5 Flash · Generated {now}</div>

  <div class="kpi-row">
    <div class="kpi"><div class="kpi-val">{total_batches}</div><div class="kpi-label">Batches</div></div>
    <div class="kpi"><div class="kpi-val">{total_clips}</div><div class="kpi-label">Total Clips</div></div>
    <div class="kpi"><div class="kpi-val">{len(regressions)}</div><div class="kpi-label">Regressions</div></div>
    <div class="kpi"><div class="kpi-val">{sum(quality_by_batch)/len(quality_by_batch):.1f}</div><div class="kpi-label">Avg Quality</div></div>
  </div>

  <div class="section">
    <div class="section-title">Alerts</div>
    <div class="alerts">{reg_html}</div>
  </div>

  <div class="charts-row">
    <div class="chart-card">
      <div class="chart-title">Key Field Fill Rates by Batch (%)</div>
      <canvas id="fillChart" height="220"></canvas>
    </div>
    <div class="chart-card">
      <div class="chart-title">Avg Quality Score</div>
      <canvas id="qualityChart" height="220"></canvas>
    </div>
  </div>

  <div class="section">
    <div class="section-title">All Field Fill Rates</div>
    <table>
      <thead><tr><th>Field</th>{batch_header}</tr></thead>
      <tbody>{table_rows}</tbody>
    </table>
  </div>

  <div class="footer">
    Pickle DaaS · courtana.com · Run after every batch to track model health
  </div>
</div>

<script>
const batchNames = {batch_names_js};
const datasets   = {datasets_js};
const keyLabels  = {key_labels_js};
const qualityData = {quality_js};
const brandData  = {brand_js};

// Fill rates grouped bar chart
new Chart(document.getElementById('fillChart'), {{
  type: 'bar',
  data: {{ labels: keyLabels, datasets: datasets }},
  options: {{
    responsive: true,
    scales: {{
      x: {{ ticks: {{ color: '#64748b', font: {{ size: 9 }}, maxRotation: 30 }}, grid: {{ color: '#1e2a3a' }} }},
      y: {{ min: 0, max: 100, ticks: {{ color: '#64748b', callback: v => v + '%', font: {{ size: 9 }} }}, grid: {{ color: '#1e2a3a' }} }}
    }},
    plugins: {{ legend: {{ labels: {{ color: '#94a3b8', font: {{ size: 10 }} }} }} }}
  }}
}});

// Quality line chart
new Chart(document.getElementById('qualityChart'), {{
  type: 'line',
  data: {{
    labels: batchNames,
    datasets: [{{
      label: 'Avg Quality',
      data: qualityData,
      borderColor: '#00E676',
      backgroundColor: 'rgba(0,230,118,0.1)',
      pointBackgroundColor: '#00E676',
      tension: 0.3,
      fill: true,
    }}]
  }},
  options: {{
    responsive: true,
    scales: {{
      x: {{ ticks: {{ color: '#64748b', font: {{ size: 9 }}, maxRotation: 20 }}, grid: {{ color: '#1e2a3a' }} }},
      y: {{ min: 0, max: 10, ticks: {{ color: '#64748b', font: {{ size: 9 }} }}, grid: {{ color: '#1e2a3a' }} }}
    }},
    plugins: {{ legend: {{ labels: {{ color: '#94a3b8', font: {{ size: 10 }} }} }} }}
  }}
}});
</script>
</body>
</html>"""

    return html


def main():
    parser = argparse.ArgumentParser(description='Monitor model quality across batches')
    parser.add_argument('--dirs', nargs='+', default=None, help='Override batch directory list')
    args = parser.parse_args()

    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    os.chdir(base_dir)

    batch_list = args.dirs if args.dirs else [d for _, d in BATCH_DIRS]

    print("\n📊 Model Quality Monitor")
    print(f"   Scanning {len(batch_list)} batch directories...")

    batches = []
    for d in batch_list:
        stats = analyze_batch(d)
        if stats:
            batches.append(stats)
            print(f"   {stats['batch_name']:30} {stats['clip_count']} clips")

    if not batches:
        print("❌ No batches found.")
        sys.exit(1)

    regressions = detect_regressions(batches)

    os.makedirs('output', exist_ok=True)
    date_str = datetime.now().strftime('%Y%m%d')

    # Write markdown report
    md_path = f'output/model-monitor-{date_str}.md'
    write_markdown_report(batches, regressions, md_path)
    print(f"\n   ✅ Markdown report: {md_path}")

    # Write dashboard HTML
    html_path = 'output/model-monitor-dashboard.html'
    html = generate_dashboard_html(batches, regressions)
    with open(html_path, 'w') as f:
        f.write(html)
    print(f"   ✅ Dashboard HTML: {html_path}")

    # Console summary
    if regressions:
        print(f"\n   ⚠️  {len(regressions)} regression(s) detected:")
        for r in regressions:
            print(f"      {r['label']}: {r['prev_rate']*100:.0f}% → {r['curr_rate']*100:.0f}%")
    else:
        print(f"\n   ✅ No regressions across {len(batches)} batches")

    total = sum(b['clip_count'] for b in batches)
    print(f"   Total clips analyzed: {total}")
    print(f"\n   Open dashboard: open {html_path}")


if __name__ == '__main__':
    main()

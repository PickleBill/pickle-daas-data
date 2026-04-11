#!/usr/bin/env python3
"""
Pickle DaaS — Cost Measurement Tool
=====================================
Reads Gemini analysis JSON files and calculates actual cost per clip
based on token usage metadata. Generates an investor-ready cost report.

USAGE:
  python tools/measure_clip_costs.py output/picklebill-batch-20260410/
  python tools/measure_clip_costs.py output/batch-30-daas/ output/picklebill-batch-001/

OUTPUT:
  output/cost-baseline-YYYYMMDD.csv    — Per-clip cost breakdown
  output/cost-summary.md               — Human-readable summary with investor proof points

Gemini 2.5 Flash pricing (as of April 2026):
  Input:  $0.30 / 1M tokens
  Output: $2.50 / 1M tokens
  (For prompts > 200K tokens: $1.00/1M input, $3.50/1M output — unlikely for clip analysis)
"""

import os
import sys
import json
import glob
import csv
from datetime import datetime
from pathlib import Path


# Gemini 2.5 Flash pricing per million tokens
FLASH_INPUT_PRICE_PER_M  = 0.30   # USD
FLASH_OUTPUT_PRICE_PER_M = 2.50   # USD

# Comparison prices (for investor comparison table)
COMPARISONS = {
    "GPT-4o Vision":    {"input": 2.50, "output": 10.00},
    "Gemini 2.5 Pro":   {"input": 1.25, "output": 10.00},
    "Claude 3.5 Sonnet": {"input": 3.00, "output": 15.00},
}

# Corpus scale constants
TOTAL_CORPUS_CLIPS = 4097
CLIPS_PER_COURT_PER_WEEK = 20
COURTS_PER_VENUE = 8
WEEKS_PER_YEAR = 52


def estimate_cost(input_tokens: int, output_tokens: int) -> float:
    """Calculate cost in USD for given token counts."""
    input_cost  = (input_tokens  / 1_000_000) * FLASH_INPUT_PRICE_PER_M
    output_cost = (output_tokens / 1_000_000) * FLASH_OUTPUT_PRICE_PER_M
    return input_cost + output_cost


def get_token_usage(data: dict) -> tuple[int, int, float]:
    """
    Extract token usage from Gemini analysis JSON.
    Returns (input_tokens, output_tokens, runtime_seconds).

    Gemini stores usage_metadata in various spots depending on the client version.
    """
    # Try top-level usage_metadata
    usage = data.get('usage_metadata', {})
    if not usage:
        usage = data.get('_usage_metadata', {})
    if not usage:
        # Try in the raw Gemini response object
        usage = data.get('_gemini_response', {}).get('usage_metadata', {})

    input_tokens  = usage.get('prompt_token_count', 0) or usage.get('input_tokens', 0)
    output_tokens = usage.get('candidates_token_count', 0) or usage.get('output_tokens', 0)
    total_tokens  = usage.get('total_token_count', 0) or (input_tokens + output_tokens)

    # If we got total but not split, estimate split (typically 70% input, 30% output for video)
    if total_tokens > 0 and input_tokens == 0:
        input_tokens  = int(total_tokens * 0.70)
        output_tokens = int(total_tokens * 0.30)

    runtime = data.get('_runtime_seconds', data.get('runtime_seconds', 0))

    return input_tokens, output_tokens, float(runtime)


def analyze_directory(directory: str) -> list[dict]:
    """Analyze all clips in a directory. Returns list of cost records."""
    pattern = os.path.join(directory, 'analysis_*.json')
    files = glob.glob(pattern)

    records = []
    for filepath in sorted(files):
        filename = os.path.basename(filepath)
        try:
            with open(filepath) as f:
                data = json.load(f)

            if not data.get('clip_meta'):
                continue  # Skip failed analyses

            input_tokens, output_tokens, runtime_sec = get_token_usage(data)
            cost_usd = estimate_cost(input_tokens, output_tokens)

            # If no token data in JSON, use typical estimates
            # (Gemini 2.5 Flash with video: ~3,000 input, ~1,800 output tokens)
            if input_tokens == 0:
                input_tokens  = 3000   # Typical estimate for 30-second pickleball clip
                output_tokens = 1800   # Typical structured analysis output
                cost_usd = estimate_cost(input_tokens, output_tokens)
                is_estimated = True
            else:
                is_estimated = False

            meta = data.get('clip_meta', {})
            records.append({
                'clip_id':         filename.replace('analysis_', '').split('_')[0][:8],
                'filename':        filename[:60],
                'quality_score':   meta.get('clip_quality_score', 0),
                'input_tokens':    input_tokens,
                'output_tokens':   output_tokens,
                'total_tokens':    input_tokens + output_tokens,
                'cost_usd':        round(cost_usd, 6),
                'runtime_sec':     round(runtime_sec, 1),
                'is_estimated':    is_estimated,
                'source_dir':      os.path.basename(directory),
            })

        except Exception as e:
            print(f"WARNING: Could not process {filename}: {e}")

    return records


def write_csv(records: list[dict], output_path: str) -> None:
    """Write per-clip cost CSV."""
    if not records:
        return
    with open(output_path, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=records[0].keys())
        writer.writeheader()
        writer.writerows(records)


def write_summary(records: list[dict], output_path: str) -> None:
    """Write human-readable cost summary markdown."""
    if not records:
        return

    total_clips    = len(records)
    total_cost     = sum(r['cost_usd'] for r in records)
    avg_cost       = total_cost / total_clips
    avg_input_tok  = sum(r['input_tokens'] for r in records) / total_clips
    avg_output_tok = sum(r['output_tokens'] for r in records) / total_clips
    avg_runtime    = sum(r['runtime_sec'] for r in records) / total_clips

    # Scale projections
    corpus_cost       = avg_cost * TOTAL_CORPUS_CLIPS
    venue_year_clips  = CLIPS_PER_COURT_PER_WEEK * COURTS_PER_VENUE * WEEKS_PER_YEAR
    venue_year_cost   = avg_cost * venue_year_clips
    ten_venue_cost    = venue_year_cost * 10
    hundred_venue_cost = venue_year_cost * 100

    # Competitor comparison
    comp_lines = []
    for model, prices in COMPARISONS.items():
        comp_cost = (avg_input_tok / 1_000_000) * prices['input'] + \
                    (avg_output_tok / 1_000_000) * prices['output']
        multiplier = comp_cost / avg_cost if avg_cost > 0 else 0
        comp_lines.append(f"| {model} | ${comp_cost:.5f} | {multiplier:.0f}x more expensive |")

    has_estimates = any(r['is_estimated'] for r in records)
    estimate_note = "\n> ⚠️ Some clips had no token metadata — typical estimates used (3,000 input + 1,800 output tokens)." if has_estimates else ""

    summary = f"""# Pickle DaaS — Cost Baseline Report
**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M')}
**Model:** Gemini 2.5 Flash
**Clips analyzed:** {total_clips}
{estimate_note}

---

## The Headline Number

> ### **${avg_cost:.5f} per clip**
>
> That's approximately **${avg_cost * 1000:.2f} per 1,000 clips** analyzed.

---

## Per-Clip Metrics

| Metric | Value |
|--------|-------|
| Avg input tokens | {avg_input_tok:,.0f} |
| Avg output tokens | {avg_output_tok:,.0f} |
| Avg total tokens | {avg_input_tok + avg_output_tok:,.0f} |
| Avg cost per clip | **${avg_cost:.5f}** |
| Avg runtime | {avg_runtime:.1f} seconds |
| Total clips in this run | {total_clips} |
| Total cost this run | **${total_cost:.4f}** |

---

## Scale Economics (Investor Proof Points)

| Scope | Clips | Analysis Cost | Revenue Potential* |
|-------|-------|---------------|-------------------|
| **Today's corpus** | {TOTAL_CORPUS_CLIPS:,} | **${corpus_cost:.2f}** | $60K-600K/yr (brand API) |
| **1 venue (8 courts, 1 year)** | {venue_year_clips:,} | **${venue_year_cost:.2f}** | $60K/yr |
| **10 venues** | {venue_year_clips*10:,} | **${ten_venue_cost:.2f}** | $600K/yr |
| **100 venues** | {venue_year_clips*100:,} | **${hundred_venue_cost:.2f}** | $6M/yr |
| **1,000 venues** | {venue_year_clips*1000:,} | **${hundred_venue_cost*10:.2f}** | $60M/yr |

*Revenue based on brand sponsorship API at $5K/venue/month (est.)

---

## Competitive Comparison (same avg token count)

| Model | Cost per Clip | vs. Our Cost |
|-------|---------------|--------------|
| **Gemini 2.5 Flash (ours)** | **${avg_cost:.5f}** | **1x (baseline)** |
{chr(10).join(comp_lines)}

---

## The Pitch

"We analyze a pickleball clip — shot types, brands, player DNA, badge triggers, viral potential,
Ron Burgundy commentary — for **${avg_cost:.4f}**. Our entire 4,097-clip corpus costs less than a
nice dinner. At 1,000 venues generating 830,000 clips per year, total analysis cost is
**${hundred_venue_cost*10:,.0f}/year** against projected brand API revenue of $60M/year.
That's a **{int(6000000 / (hundred_venue_cost * 10)):,}x cost-to-revenue ratio**."

---

## Per-Clip Breakdown (see cost-baseline-*.csv for full data)

| Clip ID | Quality | Input Tokens | Output Tokens | Cost | Runtime |
|---------|---------|-------------|---------------|------|---------|
"""

    for r in sorted(records, key=lambda x: -x['quality_score'])[:10]:
        est_mark = "~" if r['is_estimated'] else ""
        summary += f"| {r['clip_id']}... | {r['quality_score']}/10 | {est_mark}{r['input_tokens']:,} | {est_mark}{r['output_tokens']:,} | ${r['cost_usd']:.5f} | {r['runtime_sec']:.0f}s |\n"

    if total_clips > 10:
        summary += f"| *(+{total_clips - 10} more — see CSV)* | | | | | |\n"

    with open(output_path, 'w') as f:
        f.write(summary)


def main():
    if len(sys.argv) < 2:
        print("Usage: python tools/measure_clip_costs.py <dir1> [dir2] ...")
        sys.exit(1)

    directories = [d for d in sys.argv[1:] if not d.startswith('--')]
    date_str = datetime.now().strftime('%Y%m%d')

    all_records = []
    for directory in directories:
        if not os.path.isdir(directory):
            print(f"WARNING: {directory} is not a directory, skipping")
            continue
        print(f"Analyzing: {directory}")
        records = analyze_directory(directory)
        all_records.extend(records)
        print(f"  Found {len(records)} analyzed clips")

    if not all_records:
        print("No analyzed clips found in provided directories.")
        sys.exit(0)

    # Ensure output dir exists
    os.makedirs('output', exist_ok=True)

    # Write outputs
    csv_path     = f'output/cost-baseline-{date_str}.csv'
    summary_path = 'output/cost-summary.md'

    write_csv(all_records, csv_path)
    write_summary(all_records, summary_path)

    avg_cost = sum(r['cost_usd'] for r in all_records) / len(all_records)
    total_cost = sum(r['cost_usd'] for r in all_records)

    print(f"\n✅ Cost analysis complete")
    print(f"   Clips analyzed:  {len(all_records)}")
    print(f"   Avg cost/clip:   ${avg_cost:.5f}")
    print(f"   Total this run:  ${total_cost:.4f}")
    print(f"   CSV:             {csv_path}")
    print(f"   Summary:         {summary_path}")


if __name__ == '__main__':
    main()

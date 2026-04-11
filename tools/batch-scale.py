#!/usr/bin/env python3
"""
Pickle DaaS — Batch Scale Pipeline
====================================
One command to fetch clips, analyze them with Gemini, and update the badge warehouse.

USAGE:
  python tools/batch-scale.py --count 200 --badged-only --prompt-file prompts/v1.3-20260410.txt
  python tools/batch-scale.py --count 500 --output-dir output/scale-500
  python tools/batch-scale.py --count 2000 --output-dir output/scale-2000
  python tools/batch-scale.py --count 100 --player PickleBill --badged-only
  python tools/batch-scale.py --count 50 --min-badges 3 --badged-only

FLAGS:
  --count N           How many clips to process (default: 200)
  --badged-only       Only clips from groups with badge awards
  --prompt-file       Which prompt version to use
  --output-dir        Where to save analysis outputs
  --skip-existing     Don't re-analyze clips already in the output dir
  --player NAME       Filter to clips from a specific player
  --min-badges N      Only groups with N+ badge awards (for high-signal clips)
  --skip-fetch        Skip fetching, use existing manifest
  --skip-analyze      Skip analysis, just run warehouse
  --skip-warehouse    Skip warehouse update

COST ESTIMATE:
  $0.0054/clip × count = total cost
  200 clips = ~$1.08 | 500 = ~$2.70 | 2000 = ~$10.80

OUTPUT:
  {output-dir}/clip-manifest.json    — clip URLs + ground truth
  {output-dir}/ground-truth.json     — full badge award data
  {output-dir}/analysis_*.json       — Gemini analysis per clip
  {output-dir}/batch-report.md       — summary with metrics
"""

import os
import sys
import json
import argparse
import subprocess
from datetime import datetime
from pathlib import Path


def estimate_cost(count):
    return round(count * 0.0054, 2)


def estimate_time_minutes(count):
    return round(count * 2.5 / 60, 1)  # ~2.5 sec per clip


def main():
    parser = argparse.ArgumentParser(description="Pickle DaaS — Batch Scale Pipeline")
    parser.add_argument("--count", type=int, default=200, help="Number of clips to process")
    parser.add_argument("--badged-only", action="store_true", help="Only clips from badged groups")
    parser.add_argument("--prompt-file", default=None, help="Prompt file for analysis")
    parser.add_argument("--output-dir", default=None, help="Output directory")
    parser.add_argument("--skip-existing", action="store_true", help="Don't re-analyze existing clips")
    parser.add_argument("--player", default=None, help="Filter to specific player")
    parser.add_argument("--min-badges", type=int, default=1, help="Min badges per group")
    parser.add_argument("--skip-fetch", action="store_true", help="Skip fetch step")
    parser.add_argument("--skip-analyze", action="store_true", help="Skip analysis step")
    parser.add_argument("--skip-warehouse", action="store_true", help="Skip warehouse update")
    args = parser.parse_args()

    # Set defaults
    if args.output_dir is None:
        tag = "badged" if args.badged_only else "mixed"
        args.output_dir = f"output/scale-{args.count}-{tag}"

    # Change to project root
    os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

    cost = estimate_cost(args.count)
    time_est = estimate_time_minutes(args.count)

    print("=" * 60)
    print("BATCH SCALE PIPELINE")
    print("=" * 60)
    print(f"  Clips:        {args.count}")
    print(f"  Badged only:  {args.badged_only}")
    print(f"  Min badges:   {args.min_badges}")
    print(f"  Player:       {args.player or 'all'}")
    print(f"  Prompt:       {args.prompt_file or 'built-in'}")
    print(f"  Output:       {args.output_dir}")
    print(f"  Est. cost:    ${cost}")
    print(f"  Est. time:    ~{time_est} min")
    print("=" * 60)

    manifest_path = os.path.join(args.output_dir, "clip-manifest.json")
    gt_path = os.path.join(args.output_dir, "ground-truth.json")

    # ── Step 1: Fetch clips ──
    if not args.skip_fetch:
        print(f"\n[1/3] FETCHING {args.count} clips...")
        fetch_cmd = [
            sys.executable, "tools/fetch-badged-clips.py",
            "--count", str(args.count),
            "--min-badges", str(args.min_badges),
            "--output-dir", args.output_dir,
        ]
        if args.player:
            fetch_cmd.extend(["--player", args.player])

        result = subprocess.run(fetch_cmd, capture_output=False)
        if result.returncode != 0:
            print("ERROR: Fetch step failed.")
            sys.exit(1)

        if not os.path.exists(manifest_path):
            print(f"ERROR: Expected manifest at {manifest_path} but not found.")
            sys.exit(1)
    else:
        print(f"\n[1/3] SKIPPING fetch (using existing manifest)")
        if not os.path.exists(manifest_path):
            print(f"ERROR: No manifest at {manifest_path}. Run without --skip-fetch first.")
            sys.exit(1)

    # Count actual clips in manifest
    with open(manifest_path) as f:
        manifest = json.load(f)
    actual_count = len(manifest)
    print(f"  Manifest has {actual_count} clips")

    # ── Step 2: Analyze clips ──
    if not args.skip_analyze:
        analysis_dir = args.output_dir
        print(f"\n[2/3] ANALYZING {actual_count} clips (~${estimate_cost(actual_count)}, ~{estimate_time_minutes(actual_count)} min)...")

        analyze_cmd = [
            sys.executable, "pickle-daas-gemini-analyzer.py",
            "--url-file", manifest_path,
            "--output-dir", analysis_dir,
            "--limit", str(actual_count),
        ]
        if args.prompt_file:
            analyze_cmd.extend(["--prompt-file", args.prompt_file])

        result = subprocess.run(analyze_cmd, capture_output=False)
        if result.returncode != 0:
            print("WARNING: Analysis step had errors (some clips may have failed).")

        # Count analysis files
        import glob
        analysis_files = glob.glob(os.path.join(analysis_dir, "analysis_*.json"))
        print(f"  Analysis files generated: {len(analysis_files)}")
    else:
        print(f"\n[2/3] SKIPPING analysis")

    # ── Step 3: Update warehouse ──
    if not args.skip_warehouse:
        print(f"\n[3/3] UPDATING badge warehouse...")

        # Check if analysis dir is in warehouse ANALYSIS_DIRS
        # Add it dynamically by running warehouse with all subcommand
        warehouse_cmd = [sys.executable, "tools/badge-warehouse.py", "all"]
        result = subprocess.run(warehouse_cmd, capture_output=False)
        if result.returncode != 0:
            print("WARNING: Warehouse update had errors.")
    else:
        print(f"\n[3/3] SKIPPING warehouse update")

    # ── Generate batch report ──
    print(f"\n{'='*60}")
    print("BATCH COMPLETE")
    print(f"{'='*60}")

    report_lines = [
        f"# Batch Scale Report",
        f"**Generated:** {datetime.now().isoformat()}",
        f"",
        f"## Parameters",
        f"- Clips requested: {args.count}",
        f"- Clips fetched: {actual_count}",
        f"- Badged only: {args.badged_only}",
        f"- Min badges: {args.min_badges}",
        f"- Player filter: {args.player or 'none'}",
        f"- Prompt: {args.prompt_file or 'built-in'}",
        f"- Output: {args.output_dir}",
        f"- Est. cost: ${cost}",
        f"",
        f"## Output Files",
        f"- Manifest: {manifest_path}",
        f"- Ground truth: {gt_path}",
        f"- Analysis dir: {args.output_dir}",
        f"",
        f"## Next Steps",
        f"- View dashboard: `open output/badge-analytics-dashboard.html`",
        f"- Run warehouse: `python tools/badge-warehouse.py all`",
        f"- Scale up: `python tools/batch-scale.py --count {args.count * 2}`",
    ]

    report_path = os.path.join(args.output_dir, "batch-report.md")
    Path(args.output_dir).mkdir(parents=True, exist_ok=True)
    with open(report_path, "w") as f:
        f.write("\n".join(report_lines))

    print(f"  Report: {report_path}")
    print(f"  Dashboard: output/badge-analytics-dashboard.html")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()

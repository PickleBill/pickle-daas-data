#!/usr/bin/env python3
"""
Pickle DaaS — Fine-Tuning Training Data Export
================================================
Takes all existing Gemini analyses and formats them as training data
for fine-tuning a cheaper model (Claude Haiku, GPT-4 Mini, etc.).

Outputs JSONL format compatible with:
- Anthropic fine-tuning API
- OpenAI fine-tuning API
- Generic JSONL for any provider

USAGE:
  python tools/export-training-data.py                    # Export all
  python tools/export-training-data.py --format anthropic  # Anthropic format
  python tools/export-training-data.py --format openai     # OpenAI format
"""

import json
import glob
import os
import argparse
from pathlib import Path
from datetime import datetime

CORPUS_DIR = "output"
ANALYSIS_PROMPT_SHORT = """Analyze this pickleball highlight video clip. Return structured JSON with: clip_meta (quality/viral/watchability scores), players_detected, shot_analysis (each shot with type/quality/outcome), skill_indicators (10 dimensions), brand_detection, badge_intelligence, commentary (ESPN/Ron Burgundy/social), and daas_signals."""


def load_analyses():
    files = glob.glob(f"{CORPUS_DIR}/**/analysis_*.json", recursive=True)
    analyses = []
    for f in files:
        try:
            if os.path.getsize(f) < 5000:
                continue
            with open(f) as fh:
                data = json.load(fh)
            if "clip_meta" in data and "_source_url" in data:
                analyses.append(data)
        except (json.JSONDecodeError, KeyError):
            continue
    return analyses


def to_anthropic_format(video_url, analysis):
    """Anthropic fine-tuning JSONL format."""
    # Strip internal metadata from the training output
    clean = {k: v for k, v in analysis.items() if not k.startswith("_")}
    return {
        "messages": [
            {"role": "user", "content": f"[Video: {video_url}]\n\n{ANALYSIS_PROMPT_SHORT}"},
            {"role": "assistant", "content": json.dumps(clean, indent=2)}
        ]
    }


def to_openai_format(video_url, analysis):
    """OpenAI fine-tuning JSONL format."""
    clean = {k: v for k, v in analysis.items() if not k.startswith("_")}
    return {
        "messages": [
            {"role": "system", "content": "You are a pickleball video analyst. Analyze clips and return structured JSON."},
            {"role": "user", "content": f"Analyze this pickleball clip: {video_url}"},
            {"role": "assistant", "content": json.dumps(clean, indent=2)}
        ]
    }


def to_generic_format(video_url, analysis):
    """Generic JSONL: input/output pairs."""
    clean = {k: v for k, v in analysis.items() if not k.startswith("_")}
    return {
        "input": f"Analyze pickleball clip: {video_url}",
        "output": json.dumps(clean),
        "metadata": {
            "source": "gemini-2.5-flash",
            "video_url": video_url,
            "quality_score": analysis.get("clip_meta", {}).get("clip_quality_score"),
            "viral_score": analysis.get("clip_meta", {}).get("viral_potential_score"),
        }
    }


def main():
    parser = argparse.ArgumentParser(description="Export training data for fine-tuning")
    parser.add_argument("--format", choices=["anthropic", "openai", "generic"], default="generic")
    parser.add_argument("--output", default=None)
    args = parser.parse_args()

    if args.output is None:
        args.output = f"output/training-data-{args.format}.jsonl"

    print(f"{'='*60}")
    print(f"Fine-Tuning Training Data Export ({args.format})")
    print(f"{'='*60}")

    analyses = load_analyses()
    print(f"Loaded {len(analyses)} analyses")

    formatters = {
        "anthropic": to_anthropic_format,
        "openai": to_openai_format,
        "generic": to_generic_format,
    }
    fmt = formatters[args.format]

    exported = 0
    with open(args.output, "w") as f:
        for a in analyses:
            url = a.get("_source_url", "")
            if not url:
                continue
            record = fmt(url, a)
            f.write(json.dumps(record) + "\n")
            exported += 1

    size_mb = os.path.getsize(args.output) / (1024 * 1024)
    print(f"\nExported {exported} training examples")
    print(f"Output: {args.output} ({size_mb:.1f} MB)")
    print(f"\nThis dataset can be used to fine-tune a model that replicates")
    print(f"Gemini's pickleball analysis at a fraction of the cost.")
    print(f"Target: 80%+ quality match at 1/5th the price per clip.")


if __name__ == "__main__":
    main()

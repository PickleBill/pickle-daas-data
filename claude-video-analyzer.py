#!/usr/bin/env python3
"""
Pickle DaaS — Claude Strategic Layer
======================================
Takes existing Gemini analysis JSON and runs it through Claude
to add a strategic/editorial intelligence layer.

Architecture:
  Gemini 2.5 Flash → raw video parsing (shots, brands, physics)
  Claude Opus/Sonnet → narrative, business value, coaching arc, investor framing

This is the multi-model architecture: each AI does what it's best at.
Gemini sees the frames. Claude reads the story.

USAGE:
  python claude-video-analyzer.py                          # Process 5 clips
  python claude-video-analyzer.py --count 20              # Process 20 clips
  python claude-video-analyzer.py --input path/to/analysis.json  # Single file
  python claude-video-analyzer.py --rebuild-dashboard     # Regenerate comparison HTML only

SETUP:
  Add to .env: ANTHROPIC_API_KEY=sk-ant-...
  pip install anthropic
"""

import json
import glob
import os
import argparse
import time
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
OUTPUT_DIR = "output/multi-model"
COMPARISON_HTML = "output/multi-model-comparison.html"

CLAUDE_STRATEGIC_PROMPT = """You are a strategic analyst for Pickle DaaS, a pickleball data-as-a-service platform.

You've been given a structured JSON analysis of a pickleball highlight clip, produced by Gemini 2.5 Flash from raw video frames.

Your job is NOT to repeat what Gemini said. Your job is to add a **strategic intelligence layer** — the narrative, business, and coaching intelligence that emerges from the data but can't be seen in individual frames.

Produce a JSON response with exactly these fields:

{
  "claude_model": "claude-opus-4-6",
  "strategic_narrative": "2-3 sentences on what STORY this clip tells beyond the shot data",
  "content_strategy": {
    "platform_recommendation": "tiktok|instagram|youtube|coaching_app",
    "hook_text": "The specific caption/hook that would maximize engagement",
    "cut_recommendation": "What part of the clip to show and how to edit it",
    "reframed_viral_score": 1-10
  },
  "skill_reframe": {
    "psychological_dimensions": {
      "dimension_name": score_1_to_10,
      ...3-5 dimensions Gemini can't see from frames alone (e.g. patience, adaptability, nerve, deception, in_rally_learning)
    },
    "archetype_label": "one-phrase player archetype e.g. 'Chess Player', 'The Grinder', 'Opportunist'"
  },
  "brand_intelligence": {
    "strategic_insight": "What the brand data reveals about market dynamics",
    "sellable_report_title": "A report title you could sell to the brand detected",
    "estimated_brand_value_usd": number
  },
  "coaching_narrative": "The coaching insight written as if speaking directly to the player — 3-4 sentences, conversational, specific",
  "investor_proof_point": "1-2 sentences on what this clip demonstrates about the DaaS thesis",
  "novel_metric_detected": {
    "metric_name": "Name of a new metric this clip reveals",
    "metric_value": "The value or description",
    "why_novel": "Why no existing analytics platform measures this"
  }
}

Respond ONLY with valid JSON. No markdown, no explanation.

Here is the Gemini analysis:
"""


def load_analyses(count=5):
    """Load the richest Gemini analyses available."""
    files = glob.glob("output/**/analysis_*.json", recursive=True)
    good = sorted([f for f in files if os.path.getsize(f) > 10000], key=os.path.getsize, reverse=True)

    seen_urls = set()
    clips = []
    for f in good:
        try:
            with open(f) as fh:
                d = json.load(fh)
            url = d.get("_source_url", "")
            if url and url not in seen_urls:
                seen_urls.add(url)
                clips.append({"gemini": d, "file": f, "url": url})
                if len(clips) >= count:
                    break
        except Exception:
            continue
    return clips


def analyze_with_claude(gemini_data: dict) -> dict:
    """Send Gemini output to Claude for strategic layer."""
    try:
        import anthropic
    except ImportError:
        print("  pip install anthropic  ← needed for Claude API calls")
        return {}

    if not ANTHROPIC_API_KEY:
        print("  ANTHROPIC_API_KEY not set in .env")
        return {}

    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

    # Strip large arrays to keep token count manageable
    slim = {k: v for k, v in gemini_data.items() if k not in ["shot_analysis"]}
    slim["shot_summary"] = {
        "total_shots": len(gemini_data.get("shot_analysis", {}).get("shots", [])),
        "shot_types": list(set(s.get("shot_type", "") for s in gemini_data.get("shot_analysis", {}).get("shots", []))),
        "outcomes": list(set(s.get("outcome", "") for s in gemini_data.get("shot_analysis", {}).get("shots", []))),
    }

    prompt = CLAUDE_STRATEGIC_PROMPT + json.dumps(slim, indent=2)

    try:
        response = client.messages.create(
            model="claude-opus-4-6",
            max_tokens=1500,
            messages=[{"role": "user", "content": prompt}]
        )
        text = response.content[0].text.strip()
        # Strip markdown if model adds it
        if text.startswith("```"):
            text = text.split("```")[1]
            if text.startswith("json"):
                text = text[4:]
        return json.loads(text)
    except json.JSONDecodeError as e:
        print(f"  JSON parse error: {e}")
        return {}
    except Exception as e:
        print(f"  Claude API error: {e}")
        return {}


def save_fused_output(clip: dict, claude_output: dict):
    """Save the fused Gemini + Claude analysis."""
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    uuid = clip["url"].split("/")[-1].replace(".mp4", "")
    out = {
        "_fused_at": datetime.utcnow().isoformat() + "Z",
        "_source_url": clip["url"],
        "gemini_analysis": clip["gemini"],
        "claude_strategic_layer": claude_output,
    }
    path = f"{OUTPUT_DIR}/fused_{uuid}.json"
    with open(path, "w") as f:
        json.dump(out, f, indent=2)
    return path


def main():
    parser = argparse.ArgumentParser(description="Claude Strategic Layer for Pickle DaaS")
    parser.add_argument("--count", type=int, default=5, help="Number of clips to process")
    parser.add_argument("--input", default=None, help="Single analysis JSON file to process")
    args = parser.parse_args()

    print(f"{'='*60}")
    print(f"Pickle DaaS — Multi-Model Analysis (Gemini + Claude)")
    print(f"{'='*60}")

    if not ANTHROPIC_API_KEY:
        print("\n⚠️  ANTHROPIC_API_KEY not set.")
        print("   Add to PICKLE-DAAS/.env: ANTHROPIC_API_KEY=sk-ant-...")
        print("   Then rerun this script.\n")
        print("   For now, the comparison dashboard uses pre-computed Claude analysis.")
        print(f"   Open: output/multi-model-comparison.html")
        return

    if args.input:
        with open(args.input) as fh:
            gemini_data = json.load(fh)
        clips = [{"gemini": gemini_data, "file": args.input, "url": gemini_data.get("_source_url", "")}]
    else:
        print(f"\nLoading top {args.count} analyses...")
        clips = load_analyses(args.count)
        print(f"  Loaded {len(clips)} clips")

    results = []
    for i, clip in enumerate(clips):
        uuid = clip["url"].split("/")[-1][:8]
        print(f"\n[{i+1}/{len(clips)}] Claude analyzing {uuid}...")
        claude_out = analyze_with_claude(clip["gemini"])
        if claude_out:
            path = save_fused_output(clip, claude_out)
            results.append({"clip": clip, "claude": claude_out, "path": path})
            print(f"  Saved: {path}")
            narrative = claude_out.get("strategic_narrative", "")[:80]
            print(f"  Narrative: {narrative}...")
        else:
            print(f"  Skipped — no Claude output")
        if i < len(clips) - 1:
            time.sleep(2)  # Rate limit courtesy

    print(f"\n{'='*60}")
    print(f"Processed {len(results)}/{len(clips)} clips")
    print(f"Fused outputs: {OUTPUT_DIR}/")
    print(f"Open comparison dashboard: output/multi-model-comparison.html")


if __name__ == "__main__":
    main()

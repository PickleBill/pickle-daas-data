#!/usr/bin/env python3
"""
Pickle DaaS — Character Commentary Rewriter
Uses Gemini to rewrite existing commentary into TMNT (or other) character voices.
Writes {char_key}_voice fields back into each analysis JSON's commentary section.

Usage:
  python character-commentary-rewriter.py --batch ./output/ --pack tmnt
  python character-commentary-rewriter.py --analysis ./output/test-001/analysis_*.json --character tmnt_leonardo
  python character-commentary-rewriter.py --batch ./output/ --character tmnt_raphael
"""

import os
import sys
import json
import glob
import argparse
import requests
from pathlib import Path
from importlib.machinery import SourceFileLoader

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# ---------------------------------------------------------------------------
# Import VOICE_PRESETS and VOICE_PACKS from elevenlabs-voice-pipeline.py
# ---------------------------------------------------------------------------
_pipeline_path = Path(__file__).parent / "elevenlabs-voice-pipeline.py"
_pipeline = SourceFileLoader("elevenlabs_voice_pipeline", str(_pipeline_path)).load_module()
VOICE_PRESETS = _pipeline.VOICE_PRESETS
VOICE_PACKS = _pipeline.VOICE_PACKS

# ---------------------------------------------------------------------------
# Gemini config
# ---------------------------------------------------------------------------
GEMINI_MODEL = "gemini-2.5-flash"
GEMINI_API_URL = f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent"


def rewrite_with_gemini(source_text: str, character_prompt: str, api_key: str) -> str:
    """Call Gemini REST API to rewrite commentary in character voice."""
    system_instruction = (
        "You are a sports commentary rewriter. Given source commentary about a pickleball play, "
        "rewrite it in a specific character voice. Keep it 2-4 sentences max. "
        "Be vivid, stay in character, and make it feel authentic. "
        "Do NOT add quotes around your response or explain yourself. Just output the commentary."
    )

    prompt = (
        f"{system_instruction}\n\n"
        f"CHARACTER VOICE INSTRUCTIONS:\n{character_prompt}\n\n"
        f"ORIGINAL COMMENTARY:\n{source_text}\n\n"
        f"Rewrite in character voice:"
    )

    payload = {
        "contents": [
            {
                "parts": [{"text": prompt}]
            }
        ],
        "generationConfig": {
            "temperature": 0.9,
            "maxOutputTokens": 300,
        }
    }

    headers = {"Content-Type": "application/json"}
    url = f"{GEMINI_API_URL}?key={api_key}"

    resp = requests.post(url, json=payload, headers=headers, timeout=30)
    if resp.status_code != 200:
        raise RuntimeError(f"Gemini API error: {resp.status_code} — {resp.text[:300]}")

    data = resp.json()
    try:
        return data["candidates"][0]["content"]["parts"][0]["text"].strip()
    except (KeyError, IndexError) as e:
        raise RuntimeError(f"Unexpected Gemini response format: {e}\n{json.dumps(data)[:300]}")


def get_source_text(commentary: dict) -> str:
    """Get the best available source text from commentary dict."""
    # Priority: ESPN > hype > TTS fallback
    for field in ["neutral_announcer_espn", "hype_announcer_charged", "announcement_text_for_tts"]:
        text = commentary.get(field)
        if text:
            return text
    # Last resort: any string value
    for v in commentary.values():
        if isinstance(v, str) and len(v) > 20:
            return v
    return ""


def process_file(path: str, characters: list, api_key: str) -> dict:
    """Process one analysis JSON, rewriting commentary for each character. Returns results dict."""
    with open(path) as f:
        analysis = json.load(f)

    commentary = analysis.get("commentary", {})
    source_text = get_source_text(commentary)

    if not source_text:
        print(f"  SKIP: No source commentary found in {path}")
        return {}

    results = {}
    for char_key in characters:
        preset = VOICE_PRESETS.get(char_key)
        if not preset:
            print(f"  SKIP: Unknown character '{char_key}'")
            continue

        char_prompt = preset.get("character_prompt")
        if not char_prompt:
            print(f"  SKIP: No character_prompt for '{char_key}'")
            continue

        field_name = f"{char_key}_voice"
        print(f"  Rewriting as {char_key} ({preset['description']})...")
        try:
            rewritten = rewrite_with_gemini(source_text, char_prompt, api_key)
            commentary[field_name] = rewritten
            results[char_key] = rewritten
            print(f"    -> {rewritten[:100]}...")
        except Exception as e:
            print(f"  ERROR ({char_key}): {e}")

    # Write back
    analysis["commentary"] = commentary
    with open(path, "w") as f:
        json.dump(analysis, f, indent=2)

    return results


def main():
    parser = argparse.ArgumentParser(description="Pickle DaaS — Character Commentary Rewriter")

    input_group = parser.add_mutually_exclusive_group(required=True)
    input_group.add_argument("--analysis", help="Path/glob to analysis JSON file(s)")
    input_group.add_argument("--batch",    help="Directory containing analysis JSON files (batch mode)")

    char_group = parser.add_mutually_exclusive_group(required=True)
    char_group.add_argument("--pack",      help="Voice pack name (e.g. tmnt, classic)", choices=list(VOICE_PACKS.keys()))
    char_group.add_argument("--character", help="Single character key (e.g. tmnt_leonardo)", choices=list(VOICE_PRESETS.keys()))

    args = parser.parse_args()

    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("ERROR: GEMINI_API_KEY not set. Add it to .env or export it.")
        sys.exit(1)

    # Collect paths
    if args.analysis:
        paths = glob.glob(args.analysis)
        if not paths:
            print(f"ERROR: No files found: {args.analysis}")
            sys.exit(1)
    else:
        batch_dir = args.batch
        paths = glob.glob(os.path.join(batch_dir, "**/analysis_*.json"), recursive=True)
        if not paths:
            print(f"ERROR: No analysis_*.json files found in: {batch_dir}")
            sys.exit(1)
        print(f"Batch mode: found {len(paths)} analysis files in {batch_dir}")

    characters = VOICE_PACKS[args.pack] if args.pack else [args.character]

    total_rewrites = 0
    for path in paths:
        print(f"\n{'='*60}")
        print(f"Processing: {path}")
        results = process_file(path, characters, api_key)
        total_rewrites += len(results)

    print(f"\n{'='*60}")
    print(f"Done. Wrote {total_rewrites} character voice fields across {len(paths)} files.")


if __name__ == "__main__":
    main()

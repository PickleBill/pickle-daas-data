#!/usr/bin/env python3
"""
Pickle DaaS — ElevenLabs Voices Catalog
Lists all available voices and lets you interactively add them to the VOICE_PRESETS catalog.
Selections are saved to voices-custom.json for use with the voice pipeline.

Usage:
  python voices-catalog.py
"""

import os
import sys
import json
import requests
from pathlib import Path

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

CUSTOM_VOICES_FILE = Path(__file__).parent / "voices-custom.json"


def fetch_voices(api_key: str) -> list:
    """Fetch all voices from ElevenLabs API."""
    resp = requests.get(
        "https://api.elevenlabs.io/v1/voices",
        headers={"xi-api-key": api_key},
        timeout=15,
    )
    if resp.status_code != 200:
        print(f"ERROR fetching voices: {resp.status_code} — {resp.text[:200]}")
        sys.exit(1)
    return resp.json().get("voices", [])


def print_voices_table(voices: list):
    """Print voices in a formatted table."""
    print(f"\n{'='*80}")
    print(f"ELEVENLABS VOICES CATALOG ({len(voices)} voices)")
    print(f"{'='*80}")
    print(f"{'#':>4}  {'VOICE ID':30}  {'NAME':25}  {'CATEGORY':15}  LABELS")
    print(f"{'-'*80}")
    for i, v in enumerate(voices, 1):
        voice_id = v.get("voice_id", "")
        name     = v.get("name", "")
        category = v.get("category", "")
        labels   = ", ".join(f"{k}:{val}" for k, val in (v.get("labels") or {}).items())
        print(f"{i:>4}  {voice_id:30}  {name:25}  {category:15}  {labels[:40]}")
    print(f"{'='*80}")


def load_custom_voices() -> dict:
    """Load existing custom voices file, or return empty dict."""
    if CUSTOM_VOICES_FILE.exists():
        with open(CUSTOM_VOICES_FILE) as f:
            return json.load(f)
    return {}


def save_custom_voices(custom: dict):
    """Save custom voices to JSON file."""
    with open(CUSTOM_VOICES_FILE, "w") as f:
        json.dump(custom, f, indent=2)
    print(f"\nSaved to: {CUSTOM_VOICES_FILE}")


def main():
    api_key = os.environ.get("ELEVENLABS_API_KEY")
    if not api_key:
        print("ERROR: ELEVENLABS_API_KEY not set. Add it to .env or export it.")
        sys.exit(1)

    print("Fetching voices from ElevenLabs...")
    voices = fetch_voices(api_key)
    print_voices_table(voices)

    custom = load_custom_voices()
    if custom:
        print(f"\nCurrently saved custom voices: {list(custom.keys())}")

    while True:
        print("\nEnter the # of a voice to add to your catalog, or 'q' to quit:")
        user_input = input("> ").strip()

        if user_input.lower() in ("q", "quit", "exit", ""):
            break

        try:
            idx = int(user_input) - 1
            if idx < 0 or idx >= len(voices):
                print(f"  Invalid number. Enter 1–{len(voices)}.")
                continue
        except ValueError:
            print("  Enter a number or 'q' to quit.")
            continue

        selected = voices[idx]
        print(f"\nSelected: {selected['name']} ({selected['voice_id']})")
        print("Enter a short preset name for this voice (e.g. 'my_coach', 'hype_v2'):")
        preset_name = input("> ").strip()

        if not preset_name:
            print("  Skipped — no preset name entered.")
            continue

        # Gather optional settings
        print(f"Stability (0.0–1.0, default 0.6):")
        stab_input = input("> ").strip()
        stability = float(stab_input) if stab_input else 0.6

        print(f"Similarity boost (0.0–1.0, default 0.8):")
        sim_input = input("> ").strip()
        similarity_boost = float(sim_input) if sim_input else 0.8

        print(f"Description (e.g. 'Deep baritone for highlights'):")
        description = input("> ").strip() or selected["name"]

        custom[preset_name] = {
            "voice_id": selected["voice_id"],
            "name": selected["name"],
            "description": description,
            "stability": stability,
            "similarity_boost": similarity_boost,
            "category": selected.get("category", ""),
            "labels": selected.get("labels", {}),
        }

        save_custom_voices(custom)
        print(f"  Added '{preset_name}' -> {selected['name']}")
        print(f"\n  To use in the voice pipeline:")
        print(f"    Edit elevenlabs-voice-pipeline.py and add '{preset_name}' to VOICE_PRESETS")
        print(f"    Or load voices-custom.json programmatically in your pipeline.")

    print(f"\nFinal catalog ({len(custom)} custom voices): {CUSTOM_VOICES_FILE}")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
Pickle DaaS — ElevenLabs Voice Pipeline
Takes a Gemini analysis JSON → generates MP3 commentary via ElevenLabs → optionally merges with video.

Usage:
  python elevenlabs-voice-pipeline.py --analysis ./output/test-001/analysis_*.json
  python elevenlabs-voice-pipeline.py --analysis ./output/test-001/analysis_*.json --voice espn
  python elevenlabs-voice-pipeline.py --analysis ./output/test-001/analysis_*.json --voice ron_burgundy --merge-video
  python elevenlabs-voice-pipeline.py --batch ./output/ --all-voices --output-manifest voice-manifest.json
  python elevenlabs-voice-pipeline.py --batch ./output/ --voice espn --turbo
"""

import os
import sys
import json
import glob
import argparse
import subprocess
import requests
from pathlib import Path
from datetime import datetime, timezone

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# ---------------------------------------------------------------------------
# Voice presets — Bill can swap voice_ids from /v1/voices list
# ---------------------------------------------------------------------------
VOICE_PRESETS = {
    "espn": {
        "voice_id": "TxGEqnHWrfWFTfGW9XjX",  # Josh — deep, broadcast authoritative
        "description": "ESPN broadcast style",
        "stability": 0.6,
        "similarity_boost": 0.8,
    },
    "hype": {
        "voice_id": "ErXwobaYiN019PkySvjV",   # Antoni — energetic, versatile
        "description": "High-energy hype announcer",
        "stability": 0.4,
        "similarity_boost": 0.85,
    },
    "ron_burgundy": {
        "voice_id": "pNInz6obpgDQGcFmaJgB",   # Adam — confident, slightly pompous
        "description": "Ron Burgundy energy (confident, self-assured)",
        "stability": 0.55,
        "similarity_boost": 0.75,
    },
    "chuck_norris": {
        "voice_id": "VR6AewLTigWG4xSOukaG",   # Arnold — legendary, powerful
        "description": "Legendary third-person energy",
        "stability": 0.65,
        "similarity_boost": 0.8,
    },
}

COMMENTARY_FIELD_MAP = {
    "espn": "neutral_announcer_espn",
    "hype": "hype_announcer_charged",
    "ron_burgundy": "ron_burgundy_voice",
    "chuck_norris": "chuck_norris_voice",
    "tts": "announcement_text_for_tts",
}

MODEL_DEFAULT = "eleven_monolingual_v1"
MODEL_TURBO   = "eleven_turbo_v2_5"


def list_available_voices(api_key: str):
    """Print all available ElevenLabs voices."""
    resp = requests.get(
        "https://api.elevenlabs.io/v1/voices",
        headers={"xi-api-key": api_key},
        timeout=15,
    )
    if resp.status_code != 200:
        print(f"ERROR fetching voices: {resp.status_code}")
        return
    voices = resp.json().get("voices", [])
    print(f"\n{'='*60}")
    print(f"AVAILABLE ELEVENLABS VOICES ({len(voices)} total)")
    print(f"{'='*60}")
    for v in voices:
        print(f"  {v['voice_id']:30s}  {v['name']}")


def generate_voice(text: str, voice_preset: dict, api_key: str, model_id: str = MODEL_DEFAULT) -> bytes:
    """Call ElevenLabs TTS API and return MP3 bytes."""
    url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_preset['voice_id']}"
    headers = {
        "Accept": "audio/mpeg",
        "Content-Type": "application/json",
        "xi-api-key": api_key,
    }
    payload = {
        "text": text,
        "model_id": model_id,
        "voice_settings": {
            "stability": voice_preset["stability"],
            "similarity_boost": voice_preset["similarity_boost"],
        },
    }
    print(f"  Calling ElevenLabs ({voice_preset['description']}, model={model_id})...")
    resp = requests.post(url, json=payload, headers=headers, timeout=30)
    if resp.status_code != 200:
        raise RuntimeError(f"ElevenLabs API error: {resp.status_code} — {resp.text[:200]}")
    return resp.content


def merge_audio_video(video_url: str, mp3_path: str, out_path: str):
    """Use FFmpeg to merge commentary audio with original video."""
    print(f"  Merging audio with video via FFmpeg...")
    cmd = [
        "ffmpeg", "-y",
        "-i", video_url,
        "-i", mp3_path,
        "-c:v", "copy",
        "-map", "0:v",
        "-map", "1:a",
        "-shortest",
        out_path,
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"  FFmpeg error: {result.stderr[:300]}")
        return False
    print(f"  Merged video: {out_path}")
    return True


def estimate_duration(text: str) -> int:
    """Rough estimate: average speaking rate ~130 words/min."""
    word_count = len(text.split())
    return max(1, round(word_count / 130 * 60))


def process_single_file(path: str, voice_name: str, api_key: str, model_id: str, merge_video: bool) -> dict:
    """Process one analysis JSON with one voice. Returns manifest entry dict."""
    with open(path) as f:
        analysis = json.load(f)

    commentary = analysis.get("commentary", {})
    commentary_field = COMMENTARY_FIELD_MAP.get(voice_name, "announcement_text_for_tts")
    text = commentary.get(commentary_field) or commentary.get("announcement_text_for_tts")

    if not text:
        print(f"  SKIP: No {commentary_field} found in analysis")
        return {}

    print(f"  Text ({voice_name}): {text[:120]}...")

    preset = VOICE_PRESETS[voice_name]
    mp3_bytes = generate_voice(text, preset, api_key, model_id)
    mp3_path = Path(path).with_suffix(f".{voice_name}.mp3")
    mp3_path.write_bytes(mp3_bytes)
    print(f"  Saved MP3: {mp3_path}  ({len(mp3_bytes):,} bytes)")

    if merge_video:
        video_url = analysis.get("_source_url") or analysis.get("_highlight_meta", {}).get("file")
        if video_url:
            out_video = str(Path(path).with_suffix(f".{voice_name}_commentary.mp4"))
            merge_audio_video(video_url, str(mp3_path), out_video)
        else:
            print("  SKIP merge: no video URL in analysis JSON")

    return {
        "mp3_path": str(mp3_path),
        "text": text,
        "duration_estimate_seconds": estimate_duration(text),
    }


def main():
    parser = argparse.ArgumentParser(description="Pickle DaaS — ElevenLabs Voice Pipeline")

    # Input modes — mutually exclusive
    input_group = parser.add_mutually_exclusive_group(required=True)
    input_group.add_argument("--analysis", help="Path/glob to analysis JSON file(s)")
    input_group.add_argument("--batch",    help="Directory containing analysis JSON files (batch mode)")

    # Voice selection
    parser.add_argument("--voice",       default="espn", choices=list(VOICE_PRESETS.keys()), help="Voice preset (ignored when --all-voices)")
    parser.add_argument("--all-voices",  action="store_true", help="Generate all 4 voice presets for each clip")

    # Output
    parser.add_argument("--merge-video",       action="store_true", help="Merge generated audio with original video via FFmpeg")
    parser.add_argument("--list-voices",       action="store_true", help="List all available ElevenLabs voices and exit")
    parser.add_argument("--output-manifest",   default=None,        help="Write a voice-manifest.json listing all generated MP3s")

    # Model
    parser.add_argument("--turbo", action="store_true", help=f"Use {MODEL_TURBO} instead of {MODEL_DEFAULT}")

    args = parser.parse_args()

    api_key = os.environ.get("ELEVENLABS_API_KEY")
    if not api_key:
        print("ERROR: ELEVENLABS_API_KEY not set. Add it to .env or export it.")
        sys.exit(1)

    if args.list_voices:
        list_available_voices(api_key)
        return

    model_id = MODEL_TURBO if args.turbo else MODEL_DEFAULT

    # Collect paths
    if args.analysis:
        paths = glob.glob(args.analysis)
        if not paths:
            print(f"ERROR: No files found: {args.analysis}")
            sys.exit(1)
    else:
        # Batch mode — find all analysis JSONs in directory
        batch_dir = args.batch
        paths = glob.glob(os.path.join(batch_dir, "**/analysis_*.json"), recursive=True)
        if not paths:
            print(f"ERROR: No analysis_*.json files found in: {batch_dir}")
            sys.exit(1)
        print(f"Batch mode: found {len(paths)} analysis files in {batch_dir}")

    voices_to_run = list(VOICE_PRESETS.keys()) if args.all_voices else [args.voice]

    manifest_clips = []

    for path in paths:
        print(f"\n{'='*60}")
        print(f"Processing: {path}")

        clip_id = Path(path).stem
        clip_voices = {}

        for voice_name in voices_to_run:
            try:
                entry = process_single_file(path, voice_name, api_key, model_id, args.merge_video)
                if entry:
                    clip_voices[voice_name] = entry
            except Exception as e:
                print(f"  ERROR ({voice_name}): {e}")

        if clip_voices:
            manifest_clips.append({
                "clip_id": clip_id,
                "voices": clip_voices,
            })

    # Write manifest if requested
    if args.output_manifest:
        manifest = {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "clips": manifest_clips,
        }
        with open(args.output_manifest, "w") as f:
            json.dump(manifest, f, indent=2)
        print(f"\nManifest written: {args.output_manifest}  ({len(manifest_clips)} clips)")


if __name__ == "__main__":
    main()

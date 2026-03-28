#!/usr/bin/env python3
"""
Pickle DaaS — Audio Mixer
Mixes ElevenLabs voice MP3s with background audio using FFmpeg.
Gracefully falls back to copying the voice file if background audio doesn't exist.

Usage:
  python audio-mixer.py --voice ./output/broadcast/analysis_xxx.tmnt_leonardo.mp3 --bg tmnt_theme --output ./output/mixed/
  python audio-mixer.py --manifest output/lovable-package/voice-manifest-tmnt.json --output ./output/mixed/
  python audio-mixer.py --batch ./output/ --bg-auto --output ./output/mixed/
"""

import os
import sys
import json
import glob
import shutil
import argparse
import subprocess
from pathlib import Path
from datetime import datetime, timezone

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# ---------------------------------------------------------------------------
# Background audio presets
# ---------------------------------------------------------------------------
ASSETS_DIR = Path(__file__).parent / "assets"

BG_AUDIO_PRESETS = {
    "tmnt_theme": {
        "filename": "tmnt_theme.mp3",
        "description": "TMNT theme music loop — iconic 80s cartoon theme",
        "volume": 0.15,   # background level (0.0–1.0)
        "fade_in": 0.5,
        "fade_out": 1.5,
    },
    "arena_crowd": {
        "filename": "arena_crowd.mp3",
        "description": "Indoor sports arena crowd ambience",
        "volume": 0.12,
        "fade_in": 0.3,
        "fade_out": 1.0,
    },
    "pickleball_court": {
        "filename": "pickleball_court.mp3",
        "description": "Outdoor pickleball court ambience with light crowd",
        "volume": 0.1,
        "fade_in": 0.2,
        "fade_out": 0.8,
    },
    "hype_music": {
        "filename": "hype_music.mp3",
        "description": "High-energy hype music bed for intense highlights",
        "volume": 0.18,
        "fade_in": 0.5,
        "fade_out": 2.0,
    },
}

# Map voice preset keys to recommended background audio
VOICE_BG_MAP = {
    "tmnt_leonardo": "tmnt_theme",
    "tmnt_raphael": "tmnt_theme",
    "tmnt_donatello": "tmnt_theme",
    "tmnt_michelangelo": "tmnt_theme",
    "tmnt_splinter": "tmnt_theme",
    "espn": "arena_crowd",
    "hype": "hype_music",
    "ron_burgundy": "arena_crowd",
    "chuck_norris": "arena_crowd",
}


def get_audio_duration(path: str) -> float:
    """Get audio duration in seconds using ffprobe."""
    cmd = [
        "ffprobe", "-v", "quiet", "-print_format", "json",
        "-show_streams", path
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        return 0.0
    try:
        data = json.loads(result.stdout)
        for stream in data.get("streams", []):
            if stream.get("duration"):
                return float(stream["duration"])
    except Exception:
        pass
    return 0.0


def mix_audio(voice_path: str, bg_preset_name: str, output_path: str) -> bool:
    """Mix voice MP3 with background audio using FFmpeg. Returns True on success."""
    preset = BG_AUDIO_PRESETS.get(bg_preset_name)
    if not preset:
        print(f"  WARNING: Unknown BG preset '{bg_preset_name}', copying voice only.")
        shutil.copy2(voice_path, output_path)
        return True

    bg_path = ASSETS_DIR / preset["filename"]
    if not bg_path.exists():
        print(f"  WARNING: Background audio not found: {bg_path}")
        print(f"  Falling back to voice-only copy.")
        shutil.copy2(voice_path, output_path)
        return True

    vol = preset["volume"]
    fade_in = preset["fade_in"]
    fade_out = preset["fade_out"]
    voice_duration = get_audio_duration(voice_path)

    # Build FFmpeg command:
    # - Input 0: voice (full volume)
    # - Input 1: background (looped, volume reduced, faded)
    # - Mix and trim to voice duration
    if voice_duration > 0:
        fade_out_start = max(0, voice_duration - fade_out)
        bg_filter = (
            f"[1:a]volume={vol},"
            f"afade=t=in:st=0:d={fade_in},"
            f"afade=t=out:st={fade_out_start:.2f}:d={fade_out}[bg];"
            f"[0:a][bg]amix=inputs=2:duration=first:normalize=0[out]"
        )
    else:
        bg_filter = (
            f"[1:a]volume={vol},"
            f"afade=t=in:st=0:d={fade_in}[bg];"
            f"[0:a][bg]amix=inputs=2:duration=first:normalize=0[out]"
        )

    cmd = [
        "ffmpeg", "-y",
        "-i", voice_path,
        "-stream_loop", "-1", "-i", str(bg_path),
        "-filter_complex", bg_filter,
        "-map", "[out]",
        "-c:a", "libmp3lame", "-q:a", "2",
        output_path,
    ]

    print(f"  Mixing: {Path(voice_path).name} + {preset['filename']} -> {Path(output_path).name}")
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"  FFmpeg error: {result.stderr[:400]}")
        print(f"  Falling back to voice-only copy.")
        shutil.copy2(voice_path, output_path)
        return False

    in_size = os.path.getsize(voice_path)
    out_size = os.path.getsize(output_path)
    print(f"  Mixed: {out_size:,} bytes (voice was {in_size:,} bytes)")
    return True


def process_voice_file(voice_path: str, bg_name: str, output_dir: str) -> dict:
    """Process a single voice MP3 and mix with background audio."""
    voice_p = Path(voice_path)
    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    # Insert .mixed before extension
    out_name = voice_p.stem + ".mixed.mp3"
    out_path = str(out_dir / out_name)

    success = mix_audio(voice_path, bg_name, out_path)
    return {
        "voice_path": voice_path,
        "mixed_path": out_path,
        "bg_preset": bg_name,
        "success": success,
    }


def infer_bg_from_filename(filename: str) -> str:
    """Infer background audio preset from filename (voice key embedded in name)."""
    for voice_key, bg_key in VOICE_BG_MAP.items():
        if voice_key in filename:
            return bg_key
    return "arena_crowd"  # default


def main():
    parser = argparse.ArgumentParser(description="Pickle DaaS — Audio Mixer")

    input_group = parser.add_mutually_exclusive_group(required=True)
    input_group.add_argument("--voice",    help="Path to single voice MP3")
    input_group.add_argument("--manifest", help="Path to voice-manifest JSON")
    input_group.add_argument("--batch",    help="Directory to scan for *.mp3 voice files")

    parser.add_argument("--bg",       default=None, choices=list(BG_AUDIO_PRESETS.keys()),
                        help="Background audio preset name")
    parser.add_argument("--bg-auto",  action="store_true",
                        help="Auto-detect background audio from voice filename")
    parser.add_argument("--output",   default="./output/mixed/", help="Output directory for mixed files")
    parser.add_argument("--list-presets", action="store_true", help="List available BG audio presets and exit")

    args = parser.parse_args()

    if args.list_presets:
        print(f"\n{'='*60}")
        print("AVAILABLE BACKGROUND AUDIO PRESETS")
        print(f"{'='*60}")
        for k, v in BG_AUDIO_PRESETS.items():
            exists = "EXISTS" if (ASSETS_DIR / v["filename"]).exists() else "MISSING"
            print(f"  {k:20s}  [{exists}]  {v['description']}")
        print(f"\nAssets directory: {ASSETS_DIR}")
        return

    results = []

    if args.voice:
        bg = args.bg or (infer_bg_from_filename(args.voice) if args.bg_auto else "arena_crowd")
        result = process_voice_file(args.voice, bg, args.output)
        results.append(result)

    elif args.manifest:
        with open(args.manifest) as f:
            manifest = json.load(f)
        clips = manifest.get("clips", [])
        for clip in clips:
            for voice_key, voice_data in clip.get("voices", {}).items():
                mp3_path = voice_data.get("mp3_path")
                if not mp3_path or not os.path.exists(mp3_path):
                    print(f"  SKIP: {mp3_path} not found")
                    continue
                bg = args.bg or VOICE_BG_MAP.get(voice_key, "arena_crowd")
                result = process_voice_file(mp3_path, bg, args.output)
                results.append(result)

    else:  # batch
        mp3_files = glob.glob(os.path.join(args.batch, "**/*.mp3"), recursive=True)
        # Skip already-mixed files
        mp3_files = [f for f in mp3_files if ".mixed." not in f]
        if not mp3_files:
            print(f"ERROR: No .mp3 files found in: {args.batch}")
            sys.exit(1)
        print(f"Batch mode: found {len(mp3_files)} MP3 files")
        for mp3_path in mp3_files:
            bg = args.bg or (infer_bg_from_filename(mp3_path) if args.bg_auto else "arena_crowd")
            result = process_voice_file(mp3_path, bg, args.output)
            results.append(result)

    success_count = sum(1 for r in results if r.get("success"))
    print(f"\n{'='*60}")
    print(f"Done. Mixed {success_count}/{len(results)} files successfully.")
    print(f"Output directory: {args.output}")

    # Write mixing report
    report_path = os.path.join(args.output, "mixing-report.json")
    os.makedirs(args.output, exist_ok=True)
    with open(report_path, "w") as f:
        json.dump({
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "total": len(results),
            "success": success_count,
            "results": results,
        }, f, indent=2)
    print(f"Report: {report_path}")


if __name__ == "__main__":
    main()

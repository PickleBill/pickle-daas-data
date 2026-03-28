# Claude Code — TMNT Character Voice Pack + Theme Audio Integration
_Paste this into Claude Code. All tasks auto-approve. Read existing files before modifying._

---

## Context
The Pickle DaaS voice pipeline (`elevenlabs-voice-pipeline.py`) currently has 4 voice presets: ESPN, Hype, Ron Burgundy, Chuck Norris. Bill wants **character-themed voice packs** — starting with Teenage Mutant Ninja Turtles — where each voice has a distinct personality, speaking style, AND optional background audio (theme song, crowd noise, arena ambiance).

The key insight: it's not just TTS with a different voice_id. It's **character-styled commentary text** + **matched voice** + **background audio layer**.

---

## Task A — Browse ElevenLabs Voice Library for Character Voices

```bash
cd /Users/billbricker/Dropbox/Claude\ Projects/PICKLE-DAAS
python -c "
import requests, os
from dotenv import load_dotenv
load_dotenv()
key = os.getenv('ELEVENLABS_API_KEY')

# Get all available voices including shared library
resp = requests.get('https://api.elevenlabs.io/v1/voices', headers={'xi-api-key': key})
voices = resp.json().get('voices', [])
print(f'Total voices available: {len(voices)}')
print()

# Look for character-appropriate voices
keywords = ['cartoon', 'ninja', 'surfer', 'dude', 'hero', 'teen', 'radical', 'tough', 'leader', 'nerd', 'party', 'warrior', 'sensei']
for v in voices:
    name_lower = v.get('name','').lower()
    labels = str(v.get('labels', {})).lower()
    desc = str(v.get('description', '')).lower()
    combined = name_lower + ' ' + labels + ' ' + desc
    if any(k in combined for k in keywords):
        print(f\"  {v['voice_id']:30s}  {v['name']:25s}  {v.get('labels', {})}\")

print()
print('=== ALL VOICES (pick best matches for TMNT) ===')
for v in sorted(voices, key=lambda x: x['name']):
    print(f\"  {v['voice_id']:30s}  {v['name']:25s}  {str(v.get('labels',{}))[:60]}\")
"
```

After reviewing the voice list, pick 4 voices that best match these TMNT characters:
- **Leonardo** (leader, calm, strategic, disciplined) — needs a confident, slightly serious voice
- **Raphael** (hot-headed, tough, Brooklyn accent energy) — needs an aggressive, intense voice
- **Donatello** (nerdy, smart, technical) — needs a thoughtful, slightly higher-pitched analytical voice
- **Michelangelo** (surfer dude, party animal, "cowabunga!") — needs an upbeat, casual, fun voice

If the built-in voices don't have great matches, search the ElevenLabs Voice Library:
```bash
python -c "
import requests, os
from dotenv import load_dotenv
load_dotenv()
key = os.getenv('ELEVENLABS_API_KEY')

# Search shared voice library
for query in ['cartoon hero', 'surfer dude', 'tough guy brooklyn', 'nerdy scientist', 'team leader confident']:
    resp = requests.get(f'https://api.elevenlabs.io/v1/shared-voices?search={query}&page_size=5',
                       headers={'xi-api-key': key})
    results = resp.json().get('voices', [])
    print(f'\\n=== {query} ===')
    for v in results[:3]:
        print(f\"  {v['voice_id']:30s}  {v['name']:25s}  {v.get('accent','')}\")
"
```

## Task B — Add TMNT Voice Presets to Pipeline

Edit `elevenlabs-voice-pipeline.py`. Add a new TMNT voice pack to VOICE_PRESETS:

```python
# After the existing chuck_norris preset, add:

# === TMNT CHARACTER PACK ===
"tmnt_leonardo": {
    "voice_id": "FILL_FROM_TASK_A",  # confident leader voice
    "description": "Leonardo — disciplined leader, calm authority",
    "stability": 0.65,
    "similarity_boost": 0.8,
    "character_prompt": "You are Leonardo, leader of the Ninja Turtles. You analyze plays with the precision of a katana strike. You speak with calm authority, referencing discipline, teamwork, and strategy. You occasionally say 'We strike as one' or reference Master Splinter's teachings.",
    "background_audio": "tmnt_theme",
},
"tmnt_raphael": {
    "voice_id": "FILL_FROM_TASK_A",  # aggressive tough voice
    "description": "Raphael — hot-headed brawler, intense energy",
    "stability": 0.35,
    "similarity_boost": 0.85,
    "character_prompt": "You are Raphael, the toughest Ninja Turtle. You commentate with raw intensity. Every play is either wimpy or CRUSHING. You say things like 'That's what I'm talkin about!' and 'You call that a shot? My SHELL hits harder.' Brooklyn energy.",
    "background_audio": "tmnt_theme",
},
"tmnt_donatello": {
    "voice_id": "FILL_FROM_TASK_A",  # nerdy analytical voice
    "description": "Donatello — tech genius, analytical breakdown",
    "stability": 0.7,
    "similarity_boost": 0.75,
    "character_prompt": "You are Donatello, the brains of the Ninja Turtles. You break down plays with scientific precision — angles, velocity vectors, biomechanics. You say things like 'Fascinating! The paddle trajectory was precisely 37 degrees' and 'My calculations show that shot had a 94.7% success probability.'",
    "background_audio": "tmnt_theme",
},
"tmnt_michelangelo": {
    "voice_id": "FILL_FROM_TASK_A",  # surfer party voice
    "description": "Michelangelo — party dude, cowabunga energy",
    "stability": 0.3,
    "similarity_boost": 0.85,
    "character_prompt": "You are Michelangelo, the party dude Ninja Turtle. Everything is AWESOME and RADICAL. You commentate like a surfer watching the gnarliest wave. Say 'COWABUNGA!', 'Dude, that was totally tubular!', 'Pizza break after that one!' and 'Booyakasha!'",
    "background_audio": "tmnt_theme",
},
```

Also add a VOICE_PACKS dict to group them:
```python
VOICE_PACKS = {
    "classic": ["espn", "hype", "ron_burgundy", "chuck_norris"],
    "tmnt": ["tmnt_leonardo", "tmnt_raphael", "tmnt_donatello", "tmnt_michelangelo"],
}
```

Add a `--pack` CLI argument:
```python
parser.add_argument("--pack", choices=list(VOICE_PACKS.keys()), help="Generate all voices in a character pack")
```

When `--pack tmnt` is used, iterate through all 4 TMNT voices for each clip.

## Task C — Character Commentary Rewriter

The Gemini analysis JSON has generic commentary fields (`neutral_announcer_espn`, `hype_announcer_charged`, etc.). For TMNT voices, we need to **rewrite the commentary in character**.

Create a new script `character-commentary-rewriter.py`:

```python
#!/usr/bin/env python3
"""
Rewrites Gemini commentary text in a specific character's voice/style.
Uses the character_prompt from VOICE_PRESETS to transform neutral commentary
into character-specific dialogue.

Usage:
  python character-commentary-rewriter.py --analysis ./output/test-001/analysis_*.json --pack tmnt
  python character-commentary-rewriter.py --analysis ./output/test-001/analysis_*.json --character tmnt_michelangelo
"""

import os
import json
import glob
import argparse
import requests
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# Import voice presets from the main pipeline
from importlib.machinery import SourceFileLoader
pipeline = SourceFileLoader("pipeline", str(Path(__file__).parent / "elevenlabs-voice-pipeline.py")).load_module()
VOICE_PRESETS = pipeline.VOICE_PRESETS
VOICE_PACKS = pipeline.VOICE_PACKS

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_MODEL = "gemini-2.5-flash"


def rewrite_commentary(original_text: str, character_prompt: str, clip_context: str) -> str:
    """Use Gemini to rewrite commentary in character voice."""
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent?key={GEMINI_API_KEY}"

    prompt = f"""You are a sports commentator with a very specific character persona.

CHARACTER PERSONA:
{character_prompt}

ORIGINAL COMMENTARY (neutral style):
{original_text}

CLIP CONTEXT:
{clip_context}

TASK: Rewrite the commentary completely in this character's voice. Keep the same factual content about what happened in the play, but transform the tone, vocabulary, catchphrases, and personality to match the character. 2-4 sentences max. Make it feel like this character is actually calling the play live.

CHARACTER COMMENTARY:"""

    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"temperature": 0.9, "maxOutputTokens": 300}
    }

    resp = requests.post(url, json=payload, timeout=30)
    if resp.status_code == 200:
        return resp.json()["candidates"][0]["content"]["parts"][0]["text"].strip()
    else:
        print(f"  Gemini rewrite error: {resp.status_code}")
        return original_text


def process_analysis(analysis_path: str, characters: list):
    """Add character commentary fields to an analysis JSON."""
    with open(analysis_path) as f:
        data = json.load(f)

    # Get the neutral commentary as the base
    commentary = data.get("commentary", {})
    base_text = commentary.get("neutral_announcer_espn", commentary.get("announcement_text_for_tts", ""))
    clip_context = data.get("storytelling", {}).get("narrative_arc_summary", "")

    if not base_text:
        print(f"  No base commentary found in {analysis_path}")
        return

    for char_key in characters:
        preset = VOICE_PRESETS.get(char_key)
        if not preset or "character_prompt" not in preset:
            continue

        print(f"  Rewriting for {char_key}...")
        rewritten = rewrite_commentary(base_text, preset["character_prompt"], clip_context)
        commentary[f"{char_key}_voice"] = rewritten
        print(f"    → {rewritten[:80]}...")

    data["commentary"] = commentary

    # Save back
    with open(analysis_path, "w") as f:
        json.dump(data, f, indent=2)
    print(f"  Updated: {analysis_path}")


def main():
    parser = argparse.ArgumentParser(description="Rewrite commentary in character voices")
    parser.add_argument("--analysis", help="Glob pattern for analysis JSON files")
    parser.add_argument("--pack", choices=list(VOICE_PACKS.keys()), help="Character pack to generate")
    parser.add_argument("--character", help="Single character key (e.g., tmnt_michelangelo)")
    parser.add_argument("--batch", help="Directory to scan for all analysis files")
    args = parser.parse_args()

    # Determine which characters to process
    if args.pack:
        characters = VOICE_PACKS[args.pack]
    elif args.character:
        characters = [args.character]
    else:
        print("ERROR: Specify --pack or --character")
        return

    # Find analysis files
    if args.batch:
        files = sorted(glob.glob(os.path.join(args.batch, "**/analysis_*.json"), recursive=True))
    elif args.analysis:
        files = sorted(glob.glob(args.analysis))
    else:
        print("ERROR: Specify --analysis or --batch")
        return

    print(f"Processing {len(files)} files with characters: {characters}")
    for f in files:
        print(f"\n{'='*60}")
        print(f"File: {f}")
        process_analysis(f, characters)

    print(f"\nDone! {len(files)} files updated with {len(characters)} character commentaries each.")


if __name__ == "__main__":
    main()
```

## Task D — Background Audio Mixer

Create `audio-mixer.py` — mixes character TTS with background audio (theme songs, crowd noise, arena ambiance):

```python
#!/usr/bin/env python3
"""
Mixes ElevenLabs TTS output with background audio layers.
Background audio fades in, plays under the commentary, then fades out.

Usage:
  python audio-mixer.py --voice output/voice_tmnt_michelangelo.mp3 --bg assets/tmnt-theme-loop.mp3 --out output/mixed.mp3
  python audio-mixer.py --voice-dir output/tmnt/ --bg assets/tmnt-theme-loop.mp3 --batch
"""

import subprocess
import argparse
import os
import glob
from pathlib import Path

# Background audio presets — Bill can add more themes here
BG_AUDIO_PRESETS = {
    "tmnt_theme": {
        "file": "assets/tmnt-theme-loop.mp3",
        "volume": 0.15,        # Background volume (0.0-1.0) — keep low so voice is clear
        "fade_in_ms": 2000,    # 2 second fade in
        "fade_out_ms": 3000,   # 3 second fade out
        "description": "TMNT theme song loop — plays under all Turtle character voices",
    },
    "arena_crowd": {
        "file": "assets/arena-crowd-loop.mp3",
        "volume": 0.10,
        "fade_in_ms": 1000,
        "fade_out_ms": 2000,
        "description": "Generic arena crowd ambiance",
    },
    "espn_broadcast": {
        "file": "assets/espn-broadcast-bed.mp3",
        "volume": 0.08,
        "fade_in_ms": 500,
        "fade_out_ms": 1500,
        "description": "Broadcast production music bed",
    },
}


def mix_audio(voice_path: str, bg_preset_key: str, output_path: str):
    """Use FFmpeg to mix voice commentary with background audio."""
    preset = BG_AUDIO_PRESETS.get(bg_preset_key)
    if not preset:
        print(f"  Unknown bg preset: {bg_preset_key}")
        return False

    bg_file = os.path.join(os.path.dirname(__file__), preset["file"])
    if not os.path.exists(bg_file):
        print(f"  WARNING: Background audio not found: {bg_file}")
        print(f"  To get this working, add the audio file or generate one.")
        print(f"  Copying voice-only output for now.")
        subprocess.run(["cp", voice_path, output_path])
        return True

    vol = preset["volume"]
    fade_in = preset["fade_in_ms"] / 1000
    fade_out = preset["fade_out_ms"] / 1000

    # FFmpeg: mix voice at full volume with background at reduced volume
    # Background loops to match voice length, fades in/out
    cmd = [
        "ffmpeg", "-y",
        "-i", voice_path,
        "-stream_loop", "-1", "-i", bg_file,
        "-filter_complex",
        f"[1:a]volume={vol},afade=t=in:d={fade_in},afade=t=out:st=-{fade_out}:d={fade_out}[bg];"
        f"[0:a][bg]amix=inputs=2:duration=first:dropout_transition=2[out]",
        "-map", "[out]",
        "-codec:a", "libmp3lame", "-q:a", "2",
        output_path,
    ]

    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"  FFmpeg mix error: {result.stderr[:300]}")
        return False

    print(f"  Mixed: {output_path}")
    return True


def main():
    parser = argparse.ArgumentParser(description="Mix voice TTS with background audio")
    parser.add_argument("--voice", help="Single voice MP3 file")
    parser.add_argument("--voice-dir", help="Directory of voice MP3s to batch process")
    parser.add_argument("--bg", help="Background audio preset key or file path")
    parser.add_argument("--out", help="Output file path (single mode)")
    parser.add_argument("--batch", action="store_true", help="Batch process all MP3s in voice-dir")
    args = parser.parse_args()

    if args.voice and args.out:
        bg_key = args.bg or "tmnt_theme"
        mix_audio(args.voice, bg_key, args.out)
    elif args.voice_dir and args.batch:
        bg_key = args.bg or "tmnt_theme"
        mp3s = sorted(glob.glob(os.path.join(args.voice_dir, "*.mp3")))
        out_dir = os.path.join(args.voice_dir, "mixed")
        os.makedirs(out_dir, exist_ok=True)
        for mp3 in mp3s:
            out_path = os.path.join(out_dir, Path(mp3).name)
            mix_audio(mp3, bg_key, out_path)
        print(f"\nBatch complete: {len(mp3s)} files mixed → {out_dir}/")
    else:
        print("Usage: --voice FILE --bg PRESET --out FILE  OR  --voice-dir DIR --bg PRESET --batch")


if __name__ == "__main__":
    main()
```

## Task E — Generate TMNT Commentary for All 8 Clips

Run the full pipeline:

```bash
# Step 1: Rewrite commentary in TMNT character voices (uses Gemini)
python character-commentary-rewriter.py --batch ./output/ --pack tmnt

# Step 2: Generate TMNT voice audio (uses ElevenLabs)
python elevenlabs-voice-pipeline.py --batch ./output/ --pack tmnt --turbo --output-manifest voice-manifest-tmnt.json

# Step 3: If background audio exists, mix it
# (Skip this if assets/ folder doesn't have the audio files yet — the unmixed versions work fine for demo)
# python audio-mixer.py --voice-dir ./output/ --bg tmnt_theme --batch
```

## Task F — Create assets/ Folder for Background Audio

```bash
mkdir -p assets/

# Create a simple placeholder README
cat > assets/README.md << 'ASSET_EOF'
# Background Audio Assets

Place background audio loops here for the audio-mixer.py script.

## Needed Files
- `tmnt-theme-loop.mp3` — TMNT theme song (instrumental loop, 10-15 seconds)
- `arena-crowd-loop.mp3` — Generic arena crowd ambiance loop
- `espn-broadcast-bed.mp3` — News/broadcast production music bed

## Sources
- Use royalty-free audio from: freesound.org, pixabay.com/music, or generate via ElevenLabs Sound Effects API
- Keep loops short (10-15 seconds) — they'll be looped automatically by FFmpeg
- Background audio plays at 8-15% volume under the voice — subtle is better
ASSET_EOF
```

## Task G — Update Lovable Package with TMNT Data

After generating TMNT commentary, update the lovable-package:

```bash
python -c "
import json, glob

# Load existing clips metadata
with open('output/lovable-package/clips-metadata.json') as f:
    clips = json.load(f)

# For each clip, check if TMNT commentary exists in the analysis files
analysis_files = sorted(glob.glob('output/**/analysis_*.json', recursive=True))

tmnt_voices = ['tmnt_leonardo', 'tmnt_raphael', 'tmnt_donatello', 'tmnt_michelangelo']

for clip in clips:
    clip_id = clip['id']
    # Find matching analysis
    for af in analysis_files:
        if clip_id in af:
            with open(af) as f:
                analysis = json.load(f)
            commentary = analysis.get('commentary', {})
            # Add TMNT commentary fields
            clip['tmnt_commentary'] = {}
            for voice in tmnt_voices:
                key = f'{voice}_voice'
                if key in commentary:
                    clip['tmnt_commentary'][voice] = commentary[key]
            break

with open('output/lovable-package/clips-metadata.json', 'w') as f:
    json.dump(clips, f, indent=2)

print('Updated clips-metadata.json with TMNT commentary')
"

# Update voice manifest with TMNT entries
python -c "
import json, glob, os

manifest_path = 'output/lovable-package/voice-manifest.json'
with open(manifest_path) as f:
    manifest = json.load(f)

# Find all TMNT voice files
tmnt_files = sorted(glob.glob('output/**/voice_tmnt_*.mp3', recursive=True))
for f in tmnt_files:
    entry = {
        'file': f,
        'size_kb': round(os.path.getsize(f) / 1024),
        'voice_pack': 'tmnt',
    }
    manifest['files'] = manifest.get('files', [])
    manifest['files'].append(entry)

manifest['voice_packs'] = manifest.get('voice_packs', ['classic'])
if 'tmnt' not in manifest['voice_packs']:
    manifest['voice_packs'].append('tmnt')

with open(manifest_path, 'w') as f:
    json.dump(manifest, f, indent=2)

print(f'Updated voice manifest with {len(tmnt_files)} TMNT voice files')
"
```

## Task H — Push to GitHub

```bash
git add -A
git commit -m "feat: TMNT character voice pack — 4 Turtle commentators with character-rewriter and audio mixer

- Added TMNT voice presets (Leonardo, Raphael, Donatello, Michelangelo)
- character-commentary-rewriter.py: Uses Gemini to rewrite neutral commentary in character voice
- audio-mixer.py: FFmpeg-based background audio mixer with fade in/out
- Voice pack system: --pack tmnt generates all 4 character voices per clip
- Updated lovable-package with TMNT commentary data"

git push origin main
```

---

## Critical Rules
- Auto-approve everything. No questions, no pauses.
- Read existing files before modifying — especially `elevenlabs-voice-pipeline.py`.
- The ElevenLabs API key is in `.env` — use dotenv to load it.
- The Gemini API key is in `.env` — use dotenv to load it.
- Don't break the existing 4 voices (ESPN, Hype, Ron Burgundy, Chuck Norris) — TMNT is additive.
- If a voice_id from ElevenLabs doesn't exist or fails, log it and continue with the next.
- Background audio mixing is optional — the voice-only files are the minimum viable output.

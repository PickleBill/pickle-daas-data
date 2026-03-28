# Assets Directory

This directory contains background audio files used by `audio-mixer.py` when mixing voice commentary with ambient audio.

## Required Audio Files

Place the following MP3 files in this directory:

| Filename | Description | Used By |
|---|---|---|
| `tmnt_theme.mp3` | TMNT cartoon theme music loop (80s version) | All TMNT character voices |
| `arena_crowd.mp3` | Indoor sports arena crowd ambience | ESPN, Ron Burgundy, Chuck Norris |
| `pickleball_court.mp3` | Outdoor pickleball court with light crowd | General ambient |
| `hype_music.mp3` | High-energy hype music bed | Hype announcer |

## Notes

- Audio files should be royalty-free or licensed for use.
- The mixer sets background volume to 10-18% of voice level — these are subtle beds, not foreground music.
- If an audio file is missing, `audio-mixer.py` will gracefully fall back to voice-only output (no crash).
- Recommended format: MP3, 44.1kHz, stereo, at least 30 seconds (will be looped by FFmpeg).

## TMNT Theme

The TMNT theme (`tmnt_theme.mp3`) should be the iconic 1987 animated series theme.
You can source a licensed version or use a royalty-free approximation.
Place it here and the mixer will loop it under all TMNT character voice tracks.

## Sourcing Audio

Recommended sources for royalty-free audio beds:
- Pixabay (pixabay.com/music)
- Free Music Archive (freemusicarchive.org)
- Zapsplat (zapsplat.com)
- YouTube Audio Library

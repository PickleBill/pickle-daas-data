#!/usr/bin/env python3
"""
Pickle DaaS — Frame Extractor
================================
Downloads pickleball clip videos from CDN and extracts keyframes using FFmpeg.
Outputs JPEG frames for downstream brand detection and moment analysis.

Two extraction modes:
  --mode keyframes   Scene-change detection (default) — captures brand-visible moments
  --mode uniform     Every N seconds (default 0.5s) — comprehensive coverage

USAGE:
  # Extract frames from a single CDN URL
  python tools/frame-extractor.py \
    --url "https://cdn.courtana.com/files/production/u/.../clip.mp4"

  # Extract frames from top clips in a batch directory
  python tools/frame-extractor.py --batch output/batch-30-daas --top 3

  # Extract frames from all analyzed clips
  python tools/frame-extractor.py --batch output/batch-30-daas

OUTPUT:
  output/frames/{clip_id}/frame_0001.jpg  (scene-change frames)
  output/frames/{clip_id}/frame_0001_t2.5.jpg  (uniform: t = timestamp in seconds)
  output/frames/{clip_id}/manifest.json   (frame list with timestamps)

FFMPEG PATH: Tries system PATH, then Homebrew locations.
"""

import os
import sys
import json
import glob
import argparse
import subprocess
import tempfile
import re
import shutil
import urllib.request
from datetime import datetime
from pathlib import Path

# FFmpeg binary locations to try
FFMPEG_CANDIDATES = [
    'ffmpeg',
    '/opt/homebrew/opt/ffmpeg@2.8/bin/ffmpeg',
    '/opt/homebrew/bin/ffmpeg',
    '/usr/local/bin/ffmpeg',
    '/usr/bin/ffmpeg',
]

def find_ffmpeg():
    for candidate in FFMPEG_CANDIDATES:
        try:
            result = subprocess.run([candidate, '-version'], capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                return candidate
        except (FileNotFoundError, subprocess.TimeoutExpired):
            continue
    return None


def get_clip_id(url):
    """Extract UUID from CDN URL."""
    match = re.search(r'/([a-f0-9-]{36})\.mp4', url)
    if match:
        return match.group(1)[:8]  # Short ID (first 8 chars)
    return 'unknown'


def download_video(url, dest_path, timeout=30):
    """Download a video from CDN to a temp file."""
    req = urllib.request.Request(url, headers={'User-Agent': 'PickleDaaS/1.0'})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as response:
            with open(dest_path, 'wb') as f:
                while True:
                    chunk = response.read(65536)
                    if not chunk:
                        break
                    f.write(chunk)
        return True
    except Exception as e:
        print(f"    Download failed: {e}")
        return False


def extract_keyframes(ffmpeg_bin, video_path, output_dir, mode='keyframes', interval=0.5, max_frames=30):
    """
    Extract frames from a video file.

    Modes:
      keyframes: Scene-change detection (best for brand visibility moments)
      uniform:   Every `interval` seconds
      both:      Both approaches (most comprehensive, more frames)
    """
    os.makedirs(output_dir, exist_ok=True)
    frames = []

    if mode in ('keyframes', 'both'):
        # Scene-change detection: captures moments when something significant happens
        # threshold 0.3 = captures most scene changes without too many duplicates
        scene_pattern = os.path.join(output_dir, 'scene_%04d.jpg')
        cmd = [
            ffmpeg_bin,
            '-i', video_path,
            '-vf', "select='gt(scene,0.3)',scale=1280:-1",
            '-vsync', 'vfr',
            '-q:v', '2',  # High quality JPEG
            '-frames:v', str(max_frames),
            scene_pattern,
            '-y', '-loglevel', 'error'
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)
        scene_frames = sorted(glob.glob(os.path.join(output_dir, 'scene_*.jpg')))
        frames.extend([{'path': f, 'type': 'scene_change'} for f in scene_frames])

    if mode in ('uniform', 'both'):
        # Uniform sampling: every N seconds
        uniform_pattern = os.path.join(output_dir, 'uniform_%04d.jpg')
        cmd = [
            ffmpeg_bin,
            '-i', video_path,
            '-vf', f"fps=1/{interval},scale=1280:-1",
            '-q:v', '2',
            '-frames:v', str(max_frames),
            uniform_pattern,
            '-y', '-loglevel', 'error'
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)
        uniform_frames = sorted(glob.glob(os.path.join(output_dir, 'uniform_*.jpg')))
        frames.extend([{'path': f, 'type': 'uniform'} for f in uniform_frames])

    # Get video duration for timestamp calculation
    duration = get_video_duration(ffmpeg_bin, video_path)

    # Build manifest
    manifest = {
        'video_path':   video_path,
        'mode':         mode,
        'total_frames': len(frames),
        'duration_sec': duration,
        'extracted_at': datetime.now().isoformat(),
        'frames': [],
    }

    for i, frame in enumerate(frames):
        # Estimate timestamp from frame position in uniform mode
        frame_filename = os.path.basename(frame['path'])
        frame_num = int(re.search(r'(\d+)', frame_filename).group(1)) if re.search(r'(\d+)', frame_filename) else i

        if frame['type'] == 'uniform' and duration:
            timestamp_est = round((frame_num - 1) * interval, 2)
        else:
            # Scene change: approximate position in video
            timestamp_est = round((i / max(len(frames), 1)) * (duration or 0), 2) if duration else None

        manifest['frames'].append({
            'filename':       frame_filename,
            'path':           frame['path'],
            'type':           frame['type'],
            'frame_num':      frame_num,
            'timestamp_est':  timestamp_est,
        })

    manifest_path = os.path.join(output_dir, 'manifest.json')
    with open(manifest_path, 'w') as f:
        json.dump(manifest, f, indent=2)

    return manifest


def get_video_duration(ffmpeg_bin, video_path):
    """Get video duration in seconds using ffprobe."""
    ffprobe = ffmpeg_bin.replace('ffmpeg', 'ffprobe')
    try:
        result = subprocess.run(
            [ffprobe, '-v', 'quiet', '-print_format', 'json', '-show_format', video_path],
            capture_output=True, text=True, timeout=10
        )
        if result.returncode == 0:
            data = json.loads(result.stdout)
            return float(data.get('format', {}).get('duration', 0))
    except Exception:
        pass
    return None


def process_url(ffmpeg_bin, url, output_base, mode='keyframes', max_frames=30):
    """Download a video and extract frames."""
    clip_id = get_clip_id(url)
    output_dir = os.path.join(output_base, clip_id)

    # Check if already extracted
    manifest_path = os.path.join(output_dir, 'manifest.json')
    if os.path.exists(manifest_path):
        print(f"  ↩️  Already extracted: {clip_id} (use --force to re-extract)")
        with open(manifest_path) as f:
            return json.load(f)

    print(f"  📹 Downloading: {clip_id}...", end='', flush=True)

    with tempfile.NamedTemporaryFile(suffix='.mp4', delete=False) as tmp:
        tmp_path = tmp.name

    try:
        ok = download_video(url, tmp_path)
        if not ok:
            return None
        print(f" ✅ ({os.path.getsize(tmp_path)//1024}KB)")

        print(f"  🖼️  Extracting frames (mode: {mode})...", end='', flush=True)
        manifest = extract_keyframes(ffmpeg_bin, tmp_path, output_dir, mode=mode, max_frames=max_frames)
        print(f" {manifest['total_frames']} frames → {output_dir}")
        return manifest

    finally:
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)


def load_top_clips(batch_dir, top_n):
    """Load top N clip URLs by quality score from a batch directory."""
    pattern = os.path.join(batch_dir, 'analysis_*.json')
    clips = []
    for filepath in glob.glob(pattern):
        try:
            with open(filepath) as f:
                data = json.load(f)
            url = data.get('_source_url', '')
            quality = data.get('clip_meta', {}).get('clip_quality_score', 0) or 0
            if url:
                clips.append((quality, url, os.path.basename(filepath)))
        except Exception:
            continue
    clips.sort(reverse=True)
    return [(url, fname) for _, url, fname in clips[:top_n]]


def main():
    parser = argparse.ArgumentParser(description='Extract keyframes from pickleball clips for brand detection')
    parser.add_argument('--url',        help='Single CDN video URL to process')
    parser.add_argument('--batch',      help='Batch directory with analysis JSONs')
    parser.add_argument('--top',        type=int, default=3, help='Top N clips by quality (with --batch)')
    parser.add_argument('--all',        action='store_true', help='Process all clips in batch (not just top N)')
    parser.add_argument('--mode',       choices=['keyframes', 'uniform', 'both'], default='keyframes')
    parser.add_argument('--max-frames', type=int, default=30, help='Max frames per clip')
    parser.add_argument('--output',     default='output/frames', help='Output base directory')
    parser.add_argument('--force',      action='store_true', help='Re-extract even if already done')
    args = parser.parse_args()

    ffmpeg_bin = find_ffmpeg()
    if not ffmpeg_bin:
        print("❌ FFmpeg not found. Install with: brew install ffmpeg")
        sys.exit(1)
    print(f"✅ FFmpeg: {ffmpeg_bin}")

    os.makedirs(args.output, exist_ok=True)

    clips_to_process = []
    if args.url:
        clips_to_process.append((args.url, 'cli'))
    elif args.batch:
        if args.all:
            clips_to_process = load_top_clips(args.batch, 9999)
        else:
            clips_to_process = load_top_clips(args.batch, args.top)
        print(f"📂 Loaded {len(clips_to_process)} clips from {args.batch}")
    else:
        parser.print_help()
        sys.exit(1)

    print(f"\n🎬 Extracting frames: {len(clips_to_process)} clips, mode={args.mode}\n")

    results = []
    for url, fname in clips_to_process:
        manifest = process_url(ffmpeg_bin, url, args.output, mode=args.mode, max_frames=args.max_frames)
        if manifest:
            results.append(manifest)

    # Summary
    total_frames = sum(m['total_frames'] for m in results)
    print(f"\n✅ Done: {len(results)} clips, {total_frames} total frames")
    print(f"   Frames directory: {args.output}")
    print(f"\n   Next step: python tools/frame-analyzer.py --frames-dir {args.output}")


if __name__ == '__main__':
    main()

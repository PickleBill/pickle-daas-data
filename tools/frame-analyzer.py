#!/usr/bin/env python3
"""
Pickle DaaS — Frame-Level Brand Analyzer
==========================================
Sends extracted video frames to Gemini for precise brand detection.
Produces a "frame intelligence" JSON alongside each clip's analysis:
  - Per-frame brand detections with timestamps + confidence
  - Bounding box estimates (relative position in frame)
  - Visibility quality and duration estimates
  - Merged summary: which brands appeared, for how long, at what moments

This is the "evidence layer" — the clip-level analysis tells the story,
the frame-level analysis provides the receipts.

USAGE:
  # Analyze frames from a single clip
  python tools/frame-analyzer.py --clip-id 139453f3

  # Analyze all extracted clips
  python tools/frame-analyzer.py --frames-dir output/frames

  # Run frame extraction + analysis in one shot
  python tools/frame-analyzer.py --batch output/batch-30-daas --top 3

OUTPUT:
  output/frames/{clip_id}/frame-intelligence.json  — Per-frame brand detections
  output/frames/{clip_id}/brand-summary.json       — Aggregated brand report for this clip
  output/brand-intelligence-corpus.json            — All clips merged (run after all clips)
"""

import os
import sys
import json
import glob
import base64
import argparse
from datetime import datetime
from pathlib import Path
from collections import defaultdict, Counter

try:
    from dotenv import load_dotenv
    load_dotenv(dotenv_path='.env')
except Exception:
    pass

try:
    import google.generativeai as genai
    GEMINI_KEY = os.environ.get('GEMINI_API_KEY')
    if GEMINI_KEY:
        genai.configure(api_key=GEMINI_KEY)
        GEMINI_AVAILABLE = True
    else:
        GEMINI_AVAILABLE = False
except Exception:
    GEMINI_AVAILABLE = False


# Frame-level brand detection prompt (v1.2 — expanded to ALL brands)
FRAME_BRAND_PROMPT = """You are a brand intelligence analyst reviewing a still frame from a pickleball video.

Identify EVERY visible brand, logo, product, or identifiable item in this frame — not just sports equipment. Scan the ENTIRE frame: players, equipment, clothing, accessories, court surroundings, signage, background, sidelines.

Return ONLY valid JSON, no markdown, no explanation:

{
  "brands_detected": [
    {
      "brand_name": "<exact brand name as it appears>",
      "category": "paddle|net|shoes|apparel_top|apparel_bottom|hat|sunglasses|bag|drink_bottle|water_bottle|cooler|wearable_tech|court_surface|banner|venue_signage|local_business|fitness_chain|vehicle|phone_case|towel|chair|ball|other",
      "confidence": "high|medium|low",
      "position_in_frame": "top_left|top_center|top_right|center_left|center|center_right|bottom_left|bottom_center|bottom_right",
      "visibility": "clear_logo|partial_logo|color_pattern_only|text_visible",
      "estimated_size_pct": <0-100, what % of frame does this brand occupy?>,
      "location_detail": "<where exactly: on paddle face, on shirt chest, on banner above court, on net, on water bottle at sideline, on hat, on shoe tongue, etc.>",
      "notes": "<any relevant detail about why you identified this brand>"
    }
  ],
  "dominant_colors": ["<top 3 colors visible in frame>"],
  "scene_type": "rally|kitchen_battle|serve|between_points|overhead|player_close_up|wide_shot|unknown",
  "players_visible": <number>,
  "paddles_visible": <number>,
  "brand_detection_confidence": "high|medium|low",
  "why_low_confidence": "<if low, explain: blurry/too far/partial view/etc.>"
}

WHAT TO LOOK FOR (scan everything):
- Paddle brands: JOOLA, Selkirk, Engage, HEAD, Paddletek, Franklin, Onix, Gearbox, Six Zero, Prince, Wilson
- Shoe brands: Nike, ASICS, New Balance, K-Swiss, Skechers, adidas, On, HOKA, Fila, Puma
- Clothing brands: Nike, adidas, Lululemon, Fabletics, Vuori, Under Armour, Fila, HEAD, JOOLA
- Eyewear: Oakley, Goodr, Rudy Project, 100%, Costa, Ray-Ban
- Drinks/bottles: Gatorade, BODYARMOR, Yeti, Hydro Flask, Stanley, CamelBak, Prime, Liquid IV
- Court/net equipment: JOOLA, Onix, Franklin, HEAD, Rally Meister
- Venue signage: Restaurant names, local businesses, sponsor banners, fitness chains (Life Time, etc.)
- Tech/wearables: Apple Watch, Fitbit, Garmin, WHOOP
- Bags, coolers, chairs, towels — anything with a visible brand name or logo

IMPORTANT:
- Report EVERY brand you can see — not just sports equipment
- When in doubt, include it with "low" confidence rather than omitting
- JOOLA nets are very common in competitive pickleball courts
- Paddle brands are the highest-value detection — look carefully at paddle face/throat
- Report color_pattern_only when you see branded colors but no readable logo
- If no brands are visible, return empty brands_detected array"""


def encode_image(image_path):
    """Base64 encode an image for Gemini."""
    with open(image_path, 'rb') as f:
        return base64.b64encode(f.read()).decode('utf-8')


def analyze_frame(image_path, clip_id, frame_meta):
    """Send a single frame to Gemini for brand detection."""
    if not GEMINI_AVAILABLE:
        return None

    try:
        model = genai.GenerativeModel('gemini-2.5-flash')
        image_data = encode_image(image_path)

        response = model.generate_content([
            {'mime_type': 'image/jpeg', 'data': image_data},
            FRAME_BRAND_PROMPT,
        ])

        text = response.text.strip()
        # Strip markdown if present
        if text.startswith('```'):
            text = '\n'.join(text.split('\n')[1:-1])

        result = json.loads(text)
        result['_frame_path']     = image_path
        result['_timestamp_est']  = frame_meta.get('timestamp_est')
        result['_frame_num']      = frame_meta.get('frame_num')
        result['_frame_type']     = frame_meta.get('type', 'unknown')
        result['_analyzed_at']    = datetime.now().isoformat()
        return result

    except json.JSONDecodeError as e:
        return {'_error': f'JSON parse error: {e}', '_raw': text[:200], '_frame_path': image_path}
    except Exception as e:
        return {'_error': str(e), '_frame_path': image_path}


def aggregate_brand_summary(frame_results, clip_id, source_url=None):
    """Aggregate per-frame brand detections into a clip-level brand summary."""
    brand_appearances = defaultdict(lambda: {
        'frames': [],
        'confidence_levels': Counter(),
        'visibility_types': Counter(),
        'categories': Counter(),
        'positions': Counter(),
    })

    total_frames = len(frame_results)
    successful_frames = [r for r in frame_results if 'brands_detected' in r]

    for frame_result in successful_frames:
        timestamp = frame_result.get('_timestamp_est')
        for brand in frame_result.get('brands_detected', []):
            name = brand.get('brand_name', 'Unknown')
            if not name or name == 'Unknown':
                continue

            brand_appearances[name]['frames'].append(timestamp)
            brand_appearances[name]['confidence_levels'][brand.get('confidence', 'low')] += 1
            brand_appearances[name]['visibility_types'][brand.get('visibility', 'unknown')] += 1
            brand_appearances[name]['categories'][brand.get('category', 'other')] += 1
            brand_appearances[name]['positions'][brand.get('position_in_frame', 'unknown')] += 1

    # Build summary
    brands_summary = []
    for brand_name, data in sorted(brand_appearances.items(), key=lambda x: -len(x[1]['frames'])):
        timestamps = [t for t in data['frames'] if t is not None]
        brands_summary.append({
            'brand_name':        brand_name,
            'frame_appearances': len(data['frames']),
            'appearance_rate':   round(len(data['frames']) / max(total_frames, 1), 2),
            'primary_confidence': data['confidence_levels'].most_common(1)[0][0] if data['confidence_levels'] else 'low',
            'primary_visibility': data['visibility_types'].most_common(1)[0][0] if data['visibility_types'] else 'unknown',
            'primary_category':   data['categories'].most_common(1)[0][0] if data['categories'] else 'other',
            'first_seen_sec':    min(timestamps) if timestamps else None,
            'last_seen_sec':     max(timestamps) if timestamps else None,
            'estimated_visible_duration_sec': round(max(timestamps) - min(timestamps), 1) if len(timestamps) > 1 else 0,
        })

    summary = {
        'clip_id':            clip_id,
        'source_url':         source_url,
        'generated_at':       datetime.now().isoformat(),
        'total_frames':       total_frames,
        'frames_analyzed':    len(successful_frames),
        'brands_detected':    brands_summary,
        'brand_count':        len(brands_summary),
        'high_confidence_brands': [b for b in brands_summary if b['primary_confidence'] == 'high'],
        'sponsorship_whitespace': detect_whitespace(brands_summary),
    }

    return summary


def detect_whitespace(brands_summary):
    """Identify major pickleball brands NOT detected — potential sponsorship opportunity."""
    major_brands = {'Selkirk', 'Engage', 'Franklin', 'HEAD', 'Paddletek', 'Six Zero', 'Gearbox', 'Onix', 'Prince', 'Wilson'}
    detected = {b['brand_name'] for b in brands_summary}
    whitespace = list(major_brands - detected)
    return sorted(whitespace)


def analyze_clip_frames(frames_dir, clip_id, skip_existing=True):
    """Analyze all frames for a single clip."""
    clip_dir = os.path.join(frames_dir, clip_id)
    manifest_path = os.path.join(clip_dir, 'manifest.json')

    if not os.path.exists(manifest_path):
        print(f"  ❌ No manifest found: {clip_dir}")
        return None

    intelligence_path = os.path.join(clip_dir, 'frame-intelligence.json')
    if skip_existing and os.path.exists(intelligence_path):
        print(f"  ↩️  Already analyzed: {clip_id}")
        with open(intelligence_path) as f:
            return json.load(f)

    with open(manifest_path) as f:
        manifest = json.load(f)

    frames = manifest.get('frames', [])
    if not frames:
        print(f"  ⚠️  No frames in manifest: {clip_id}")
        return None

    print(f"  🔍 Analyzing {len(frames)} frames for {clip_id}...")

    frame_results = []
    for i, frame_meta in enumerate(frames):
        frame_path = frame_meta.get('path') or os.path.join(clip_dir, frame_meta['filename'])
        if not os.path.exists(frame_path):
            continue

        result = analyze_frame(frame_path, clip_id, frame_meta)
        if result:
            frame_results.append(result)
            brands_found = len(result.get('brands_detected', []))
            status = f"{brands_found} brand(s)" if brands_found else "no brands"
            print(f"    Frame {i+1}/{len(frames)}: {status}")
        else:
            print(f"    Frame {i+1}/{len(frames)}: skipped (Gemini unavailable)")
            # Still add a placeholder so we know we tried
            frame_results.append({
                '_frame_path': frame_path,
                '_timestamp_est': frame_meta.get('timestamp_est'),
                '_frame_num': frame_meta.get('frame_num'),
                '_skipped': True,
                'brands_detected': [],
            })

    # Save frame intelligence
    with open(intelligence_path, 'w') as f:
        json.dump(frame_results, f, indent=2)
    print(f"    ✅ Frame intelligence saved: {intelligence_path}")

    # Build and save brand summary
    source_url = manifest.get('_source_url')
    summary = aggregate_brand_summary(frame_results, clip_id, source_url)
    summary_path = os.path.join(clip_dir, 'brand-summary.json')
    with open(summary_path, 'w') as f:
        json.dump(summary, f, indent=2)
    print(f"    ✅ Brand summary saved: {summary_path}")
    print(f"    Brands found: {[b['brand_name'] for b in summary['brands_detected']]}")

    return frame_results


def build_corpus_report(frames_dir):
    """Aggregate all clip brand summaries into a corpus-wide report."""
    summary_files = glob.glob(os.path.join(frames_dir, '*/brand-summary.json'))

    if not summary_files:
        return None

    corpus_brands = defaultdict(lambda: {
        'clip_count': 0,
        'total_frames': 0,
        'clips': [],
    })

    total_clips = 0
    for summary_path in summary_files:
        with open(summary_path) as f:
            summary = json.load(f)
        total_clips += 1

        for brand in summary.get('brands_detected', []):
            name = brand['brand_name']
            corpus_brands[name]['clip_count'] += 1
            corpus_brands[name]['total_frames'] += brand['frame_appearances']
            corpus_brands[name]['clips'].append({
                'clip_id':       summary['clip_id'],
                'appearances':   brand['frame_appearances'],
                'confidence':    brand['primary_confidence'],
                'visible_sec':   brand['estimated_visible_duration_sec'],
            })

    corpus_report = {
        'generated_at':   datetime.now().isoformat(),
        'total_clips':    total_clips,
        'brands': [
            {
                'brand_name':       brand,
                'clip_count':       data['clip_count'],
                'clip_frequency':   round(data['clip_count'] / total_clips, 2),
                'total_frame_appearances': data['total_frames'],
                'clips':            data['clips'],
            }
            for brand, data in sorted(corpus_brands.items(), key=lambda x: -x[1]['clip_count'])
        ],
    }

    report_path = os.path.join(frames_dir, '../brand-intelligence-corpus.json')
    report_path = os.path.normpath(report_path)
    with open(report_path, 'w') as f:
        json.dump(corpus_report, f, indent=2)

    print(f"\n✅ Corpus brand report: {report_path}")
    print(f"   Clips with brand data: {total_clips}")
    for brand_data in corpus_report['brands'][:8]:
        pct = brand_data['clip_frequency'] * 100
        print(f"   {brand_data['brand_name']:20} {pct:.0f}% of clips ({brand_data['clip_count']} clips)")

    return corpus_report


def demo_mode(frames_dir, clip_id):
    """Demo mode when Gemini is unavailable — creates mock frame intelligence from existing analysis."""
    print(f"  ℹ️  Demo mode (Gemini not available) — creating mock frame intelligence for {clip_id}")

    clip_dir = os.path.join(frames_dir, clip_id)
    manifest_path = os.path.join(clip_dir, 'manifest.json')

    if not os.path.exists(manifest_path):
        return None

    with open(manifest_path) as f:
        manifest = json.load(f)

    frames = manifest.get('frames', [])

    # Create mock detections based on common pickleball brands
    mock_detections = [
        {'brand_name': 'JOOLA', 'category': 'net', 'confidence': 'high',
         'position_in_frame': 'center', 'visibility': 'clear_logo', 'estimated_size_pct': 8},
    ]

    frame_results = []
    for i, frame_meta in enumerate(frames):
        # JOOLA net visible in most frames, paddle brands occasionally
        brands = list(mock_detections)
        if i % 3 == 0:  # Every 3rd frame might have a paddle visible
            brands.append({
                'brand_name': 'Unknown Paddle', 'category': 'paddle', 'confidence': 'low',
                'position_in_frame': 'center', 'visibility': 'partial_logo', 'estimated_size_pct': 3
            })

        frame_results.append({
            'brands_detected': brands,
            'scene_type': 'rally' if i > 0 else 'wide_shot',
            'players_visible': 2,
            'paddles_visible': 2,
            '_frame_path': frame_meta.get('path', ''),
            '_timestamp_est': frame_meta.get('timestamp_est'),
            '_frame_num': frame_meta.get('frame_num'),
            '_is_demo': True,
        })

    intelligence_path = os.path.join(clip_dir, 'frame-intelligence.json')
    with open(intelligence_path, 'w') as f:
        json.dump(frame_results, f, indent=2)

    summary = aggregate_brand_summary(frame_results, clip_id)
    summary['_is_demo'] = True
    summary_path = os.path.join(clip_dir, 'brand-summary.json')
    with open(summary_path, 'w') as f:
        json.dump(summary, f, indent=2)

    print(f"    ✅ Demo frame intelligence: {len(frame_results)} frames, {len(summary['brands_detected'])} brands")
    return frame_results


def main():
    parser = argparse.ArgumentParser(description='Analyze video frames for brand detection')
    parser.add_argument('--clip-id',    help='Analyze a specific clip ID (folder name in frames-dir)')
    parser.add_argument('--frames-dir', default='output/frames', help='Base frames directory')
    parser.add_argument('--batch',      help='Run frame extraction + analysis on a batch dir')
    parser.add_argument('--top',        type=int, default=3, help='Top N clips (with --batch)')
    parser.add_argument('--no-skip',    action='store_true', help='Re-analyze even if already done')
    parser.add_argument('--demo',       action='store_true', help='Demo mode (no Gemini, creates mock data)')
    parser.add_argument('--corpus',     action='store_true', help='Build corpus report from all analyzed clips')
    args = parser.parse_args()

    os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

    if not GEMINI_AVAILABLE and not args.demo:
        print("⚠️  GEMINI_API_KEY not set. Run with --demo for mock data, or set key in .env")

    if args.corpus:
        build_corpus_report(args.frames_dir)
        return

    if args.batch:
        # Import frame extractor inline
        sys.path.insert(0, 'tools')
        import importlib.util
        spec = importlib.util.spec_from_file_location("frame_extractor", "tools/frame-extractor.py")
        fe = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(fe)

        ffmpeg_bin = fe.find_ffmpeg()
        if not ffmpeg_bin:
            print("❌ FFmpeg not found. Frame extraction requires FFmpeg.")
            sys.exit(1)

        clips = fe.load_top_clips(args.batch, args.top)
        print(f"\n🎬 Processing {len(clips)} clips from {args.batch}\n")

        for url, fname in clips:
            clip_id = fe.get_clip_id(url)
            print(f"\n📹 Clip: {clip_id}")
            manifest = fe.process_url(ffmpeg_bin, url, args.frames_dir)
            if manifest and manifest['total_frames'] > 0:
                if args.demo:
                    demo_mode(args.frames_dir, clip_id)
                else:
                    analyze_clip_frames(args.frames_dir, clip_id, skip_existing=not args.no_skip)

        build_corpus_report(args.frames_dir)
        return

    # Single clip or all clips in frames dir
    if args.clip_id:
        clip_ids = [args.clip_id]
    else:
        # Find all clip dirs with manifests
        clip_dirs = glob.glob(os.path.join(args.frames_dir, '*/manifest.json'))
        clip_ids = [os.path.basename(os.path.dirname(d)) for d in clip_dirs]
        if not clip_ids:
            print(f"No extracted frames found in {args.frames_dir}")
            print("Run frame-extractor.py first, then re-run this tool")
            sys.exit(0)

    print(f"\n🔍 Analyzing {len(clip_ids)} clip(s)\n")

    for clip_id in clip_ids:
        print(f"\n📊 {clip_id}")
        if args.demo or not GEMINI_AVAILABLE:
            demo_mode(args.frames_dir, clip_id)
        else:
            analyze_clip_frames(args.frames_dir, clip_id, skip_existing=not args.no_skip)

    if len(clip_ids) > 1:
        build_corpus_report(args.frames_dir)


if __name__ == '__main__':
    main()

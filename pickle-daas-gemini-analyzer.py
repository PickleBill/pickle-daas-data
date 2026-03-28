#!/usr/bin/env python3
"""
=============================================================================
PICKLE DaaS — Gemini Video Analyzer
=============================================================================
Analyzes Courtana highlight videos using Google Gemini Flash 2.5.
Extracts rich structured JSON: shot analysis, brand detection, player DNA,
badge prediction, commentary generation, and more.

USAGE:
  Single clip:
    python pickle-daas-gemini-analyzer.py --url "https://cdn.courtana.com/files/.../clip.mp4"

  Batch from Courtana API (requires auth token):
    python pickle-daas-gemini-analyzer.py --courtana-token "your_jwt" --player "PickleBill" --limit 20

  Batch from local JSON file of URLs:
    python pickle-daas-gemini-analyzer.py --url-file highlights.json

  Batch from directory (auto-finds *clips*.json):
    python pickle-daas-gemini-analyzer.py --batch-dir ./data/

  With Supabase output:
    python pickle-daas-gemini-analyzer.py --url "..." --supabase

  Compare two Gemini models on same clip:
    python pickle-daas-gemini-analyzer.py --url "..." --compare-models

  Auto-run voice pipeline after analysis:
    python pickle-daas-gemini-analyzer.py --url "..." --voice-pipeline espn

ENVIRONMENT VARIABLES:
  GEMINI_API_KEY          Required. Your Google AI Studio API key.
  COURTANA_TOKEN          Optional. JWT from courtana.com localStorage.
  SUPABASE_URL            Optional. Your Supabase project URL.
  SUPABASE_SERVICE_KEY    Optional. Supabase service role key (not anon key).

=============================================================================
"""

import os
import sys
import json
import time
import tempfile
import argparse
import subprocess
import requests
from pathlib import Path
from datetime import datetime
from typing import Optional

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # python-dotenv optional — export vars manually if not installed

import google.generativeai as genai

# ---------------------------------------------------------------------------
# CONFIG
# ---------------------------------------------------------------------------

GEMINI_MODEL         = "gemini-2.5-flash"  # Switch to "gemini-2.5-pro" for deeper analysis
GEMINI_MODEL_COMPARE = "gemini-2.5-pro"    # Used for --compare-models

COURTANA_API_BASE = "https://api.courtana.com/private-api/v1"

# ---------------------------------------------------------------------------
# THE ANALYSIS PROMPT — Go crazy. Each field is an experiment.
# ---------------------------------------------------------------------------

ANALYSIS_PROMPT = """You are an expert pickleball analyst, sports scientist, brand intelligence researcher, and entertainment writer. Analyze this pickleball highlight video clip completely.

Return ONLY a single valid JSON object — no markdown, no explanation, no code fences. Every field below must appear. Use null for fields you cannot determine confidently.

{
  "analyzed_at": "<ISO timestamp>",
  "model_used": "gemini-2.5-flash",

  "clip_meta": {
    "duration_seconds": <number>,
    "clip_quality_score": <1-10, combines production quality + play quality>,
    "viral_potential_score": <1-10, how shareable is this on social media?>,
    "watchability_score": <1-10, would someone rewatch this?>,
    "cinematic_score": <1-10, camera angle, lighting, framing quality>
  },

  "players_detected": [
    {
      "approximate_position": "left|right|center|unknown",
      "side": "near|far|both_sides",
      "dominance_in_clip": "primary|secondary|background",
      "estimated_skill_level": "beginner|intermediate|advanced|pro|elite",
      "energy_level": "calm|moderate|high|intense|electric",
      "handedness": "left|right|unknown",
      "height_estimate": "short|medium|tall|unknown",
      "movement_style": "smooth|explosive|defensive|methodical|reactive|unknown",
      "apparel_summary": "<brief description of what they're wearing>"
    }
  ],

  "shot_analysis": {
    "shots": [
      {
        "shot_type": "dink|drive|lob|drop|volley|erne|atp|reset|overhead|smash|serve|return|speed_up|block|roll|flick|tweener|scorpion|other",
        "player_position": "kitchen|transition|mid_court|baseline|in_air",
        "quality_score": <1-10>,
        "difficulty_score": <1-10>,
        "outcome": "winner|error|forced_error|rally_continues|unknown",
        "wow_factor": <1-10>,
        "timestamp_approximate_seconds": <number or null>
      }
    ],
    "dominant_shot_type": "<string>",
    "total_shots_estimated": <number>,
    "rally_length_estimated": <number of total shots in the rally>,
    "longest_exchange_type": "kitchen_battle|driving|mixed|unknown"
  },

  "skill_indicators": {
    "court_coverage_rating": <1-10>,
    "kitchen_mastery_rating": <1-10>,
    "power_game_rating": <1-10>,
    "touch_and_feel_rating": <1-10>,
    "athleticism_rating": <1-10>,
    "creativity_rating": <1-10>,
    "court_iq_rating": <1-10>,
    "consistency_rating": <1-10>,
    "composure_under_pressure": <1-10>,
    "paddle_control_rating": <1-10, based on shot quality and touch>,
    "grip_pressure_estimate": "loose|medium|firm — inferred from shot outcomes",
    "aggression_style": "aggressive|balanced|defensive|counter_puncher",
    "play_style_tags": ["<e.g. kitchen specialist, banger, lefty, baseliner, net rusher, scrambler>"],
    "signature_move_detected": "<describe any signature or recurring move, or null>",
    "tactical_tendencies": ["<observable patterns in shot selection or positioning>"],
    "physical_descriptors": ["<handedness, movement economy, athleticism markers>"],
    "improvement_opportunities": ["<what would make this player better based on this clip>"]
  },

  "brand_detection": {
    "brands": [
      {
        "brand_name": "<brand name>",
        "category": "paddle|shoes|apparel_top|apparel_bottom|hat|headwear|sunglasses|bag|wristband|court_surface|net|ball|sponsor_banner|other",
        "confidence": "high|medium|low",
        "player_side": "left|right|both|court_equipment|unknown",
        "visibility_quality": "clear|partial|blurry|brief_flash",
        "estimated_visible_seconds": <number or null>,
        "color_scheme_noted": "<dominant colors, useful for brand matching>"
      }
    ],
    "total_brands_detected": <number>,
    "unidentified_equipment_notes": "<notes on gear that's visible but brand unidentifiable>",
    "sponsorship_whitespace": ["<brands that would be natural sponsors but aren't visibly present>"]
  },

  "paddle_intel": {
    "paddle_brand": "<brand name if detectable, e.g. Selkirk, JOOLA, Engage, HEAD, Paddletek, Franklin, Onix, Gearbox, Six Zero>",
    "paddle_model_estimate": "<specific model if visible, or null>",
    "paddle_color_scheme": "<dominant colors>",
    "paddle_shape_estimate": "elongated|standard|wide_body|unknown",
    "paddle_grip_style_observed": "two_handed|one_handed|continental|eastern|western|unknown",
    "grip_color": "<if visible>",
    "overgrip_present": "<boolean or null>",
    "lead_tape_visible": "<boolean — players who customize paddles are serious>",
    "confidence": "high|medium|low",
    "notes": "<any other observable paddle details>"
  },

  "storytelling": {
    "story_arc": "comeback|dominant_performance|clutch_moment|creative_play|athletic_highlight|teaching_moment|pure_fun|grind_rally|error_highlight|unknown",
    "emotional_tone": "intense|celebratory|focused|casual|competitive|playful|grinding|triumphant",
    "defining_moment_timestamp_seconds": <number or null>,
    "crowd_energy_detected": <boolean>,
    "player_celebration_detected": <boolean>,
    "trash_talk_detected": <boolean>,
    "turning_point_visible": <boolean>,
    "narrative_arc_summary": "<1 sentence: the story of this clip>"
  },

  "badge_intelligence": {
    "predicted_badges": [
      {
        "badge_name": "<match to Courtana taxonomy: Epic Rally, Erne Machine, Around the Post, Lob Genius, Tweener, Kitchen King, Wall of Hands, Momentum Shift, Clutch Performer, Airborne, Scorpion Tail, etc.>",
        "confidence": "high|medium|low",
        "reasoning": "<why this badge applies>"
      }
    ],
    "badge_trigger_moments": ["<describe specific moments that triggered or could trigger badges>"],
    "highlight_reel_worthy": <boolean>,
    "top_10_play_candidate": <boolean>
  },

  "commentary": {
    "neutral_announcer_espn": "<2-3 sentence ESPN broadcast style>",
    "hype_announcer_charged": "<2-3 sentence high-energy TNT/NBA-style call>",
    "coaching_breakdown": "<what a coach would say analyzing this tactically>",
    "social_media_caption": "<perfect Instagram/TikTok caption, under 100 chars>",
    "social_media_hashtags": ["#pickleball", "<5 relevant hashtags>"],
    "ron_burgundy_voice": "<Stay classy, San Diego — full Ron Burgundy energy, 2-3 sentences>",
    "chuck_norris_voice": "<third person, legendary, 1-2 sentences>",
    "color_commentator_banter": "<what the color commentator would riff on>",
    "crowd_chant_if_epic": "<what the crowd would chant, or null if not epic enough>",
    "trash_talk_friendly": "<playful banter-style commentary from one player to the other>",
    "announcement_text_for_tts": "<clean text optimized for text-to-speech voice generation, no special chars>"
  },

  "daas_signals": {
    "highlight_category": "top_play|teaching_moment|funny|athletic|strategic|social_play|gear_showcase|comeback",
    "clip_summary_one_sentence": "<what happened: factual, specific, under 20 words>",
    "search_tags": ["<10-15 specific, searchable tags>"],
    "content_use_cases": ["social_media", "coaching_tool", "player_recruitment", "venue_marketing", "sponsor_pitch", "investor_demo", "fan_engagement"],
    "estimated_player_rating_dupr": "<estimated DUPR rating range of primary player, e.g. '4.0-4.5', or null>",
    "match_context_inferred": "casual|competitive|tournament|drill|warmup|unknown",
    "data_richness_score": <1-10, how much useful data could be extracted from this clip?>
  }
}"""

# ---------------------------------------------------------------------------
# GEMINI FUNCTIONS
# ---------------------------------------------------------------------------

def init_gemini(model_name: str = None):
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("ERROR: GEMINI_API_KEY environment variable not set.")
        print("Get one at: https://aistudio.google.com/app/apikey")
        sys.exit(1)
    genai.configure(api_key=api_key)
    return genai.GenerativeModel(model_name or GEMINI_MODEL)


def download_video(url: str, dest_path: str) -> bool:
    """Download a video from a URL to a local path."""
    print(f"  Downloading: {url[:80]}...")
    try:
        headers = {"User-Agent": "PickleDaaS/1.0"}
        resp = requests.get(url, headers=headers, stream=True, timeout=60)
        resp.raise_for_status()
        with open(dest_path, "wb") as f:
            for chunk in resp.iter_content(chunk_size=8192):
                f.write(chunk)
        size_mb = Path(dest_path).stat().st_size / (1024 * 1024)
        print(f"  Downloaded: {size_mb:.1f} MB")
        return True
    except Exception as e:
        print(f"  ERROR downloading video: {e}")
        return False


def upload_to_gemini(local_path: str) -> Optional[object]:
    """Upload a video file to Gemini File API."""
    print(f"  Uploading to Gemini File API...")
    try:
        video_file = genai.upload_file(path=local_path, mime_type="video/mp4")
        # Wait for processing
        while video_file.state.name == "PROCESSING":
            print("  Gemini processing video...", end="\r")
            time.sleep(3)
            video_file = genai.get_file(video_file.name)
        if video_file.state.name == "FAILED":
            print("  ERROR: Gemini file processing failed.")
            return None
        print(f"  Upload complete: {video_file.name}")
        return video_file
    except Exception as e:
        print(f"  ERROR uploading to Gemini: {e}")
        return None


def analyze_video(model, video_file, extra_context: dict = None) -> Optional[dict]:
    """Run analysis prompt against an uploaded Gemini video file."""
    model_name = getattr(model, 'model_name', GEMINI_MODEL)
    print(f"  Running Gemini analysis ({model_name})...")
    prompt = ANALYSIS_PROMPT

    if extra_context:
        context_str = "\n\nADDITIONAL CONTEXT FROM COURTANA API:\n" + json.dumps(extra_context, indent=2)
        prompt += context_str + "\n\nUse the above context to fill in player IDs, badge history, etc. where applicable."

    try:
        response = model.generate_content(
            [video_file, prompt],
            generation_config=genai.GenerationConfig(
                temperature=0.3,         # Lower = more consistent JSON
                max_output_tokens=8192,
            )
        )
        raw_text = response.text.strip()

        # Strip markdown code fences if model adds them anyway
        if raw_text.startswith("```"):
            lines = raw_text.split("\n")
            raw_text = "\n".join(lines[1:-1]).strip()

        # Extract JSON object robustly — find outermost { ... }
        import re
        brace_match = re.search(r'\{.*\}', raw_text, re.DOTALL)
        if brace_match:
            raw_text = brace_match.group(0)

        # Remove JavaScript-style comments (// ...) that Gemini sometimes adds
        raw_text = re.sub(r'//[^\n]*', '', raw_text)

        # Remove trailing commas before } or ] (common Gemini JSON quirk)
        raw_text = re.sub(r',\s*([}\]])', r'\1', raw_text)

        result = json.loads(raw_text)
        return result

    except json.JSONDecodeError as e:
        print(f"  ERROR parsing JSON response: {e}")
        print(f"  Raw response (first 500 chars): {response.text[:500]}")
        return None
    except Exception as e:
        print(f"  ERROR calling Gemini: {e}")
        return None


def cleanup_gemini_file(video_file):
    """Delete uploaded file from Gemini to save quota."""
    try:
        genai.delete_file(video_file.name)
        print(f"  Cleaned up Gemini file: {video_file.name}")
    except Exception:
        pass  # Non-critical


# ---------------------------------------------------------------------------
# COURTANA API FUNCTIONS
# ---------------------------------------------------------------------------

def fetch_highlights_from_courtana(token: str, player_username: str = None, limit: int = 20) -> list:
    """Fetch highlight objects from the Courtana API."""
    headers = {"Authorization": f"Bearer {token}"}
    url = f"{COURTANA_API_BASE}/app/highlight-groups/?page_size={limit}"

    print(f"  Fetching {limit} highlights from Courtana API...")
    try:
        resp = requests.get(url, headers=headers, timeout=30)
        resp.raise_for_status()
        data = resp.json()
        highlights = data.get("results", [])

        # Filter by player username if specified
        if player_username:
            filtered = []
            for hg in highlights:
                for h in hg.get("highlights", [hg]):
                    participants = h.get("participants", [])
                    if any(p.get("username", "").lower() == player_username.lower() for p in participants):
                        filtered.append(h)
                        break
            highlights = filtered
            print(f"  Found {len(filtered)} highlights for player '{player_username}'")
        else:
            print(f"  Found {len(highlights)} highlights total")

        return highlights
    except Exception as e:
        print(f"  ERROR fetching from Courtana: {e}")
        return []


# ---------------------------------------------------------------------------
# SUPABASE OUTPUT
# ---------------------------------------------------------------------------

def push_to_supabase(analysis: dict, highlight_meta: dict = None):
    """Push analysis result to Supabase pickle_daas_analyses table."""
    supabase_url = os.environ.get("SUPABASE_URL")
    supabase_key = os.environ.get("SUPABASE_SERVICE_KEY")

    if not supabase_url or not supabase_key:
        print("  SUPABASE_URL or SUPABASE_SERVICE_KEY not set — skipping Supabase push.")
        return

    record = {
        "analyzed_at": analysis.get("analyzed_at", datetime.utcnow().isoformat()),
        "highlight_id": highlight_meta.get("id") if highlight_meta else None,
        "highlight_name": highlight_meta.get("name") if highlight_meta else None,
        "video_url": highlight_meta.get("file") if highlight_meta else None,
        "clip_quality_score": analysis.get("clip_meta", {}).get("clip_quality_score"),
        "viral_potential_score": analysis.get("clip_meta", {}).get("viral_potential_score"),
        "brands_detected": json.dumps(analysis.get("brand_detection", {}).get("brands", [])),
        "predicted_badges": json.dumps(analysis.get("badge_intelligence", {}).get("predicted_badges", [])),
        "play_style_tags": json.dumps(analysis.get("skill_indicators", {}).get("play_style_tags", [])),
        "commentary_social": analysis.get("commentary", {}).get("social_media_caption"),
        "commentary_ron_burgundy": analysis.get("commentary", {}).get("ron_burgundy_voice"),
        "clip_summary": analysis.get("daas_signals", {}).get("clip_summary_one_sentence"),
        "search_tags": json.dumps(analysis.get("daas_signals", {}).get("search_tags", [])),
        "full_analysis": json.dumps(analysis),
    }

    headers = {
        "apikey": supabase_key,
        "Authorization": f"Bearer {supabase_key}",
        "Content-Type": "application/json",
        "Prefer": "return=minimal"
    }

    try:
        resp = requests.post(
            f"{supabase_url}/rest/v1/pickle_daas_analyses",
            headers=headers,
            json=record,
            timeout=15
        )
        if resp.status_code in (200, 201):
            print(f"  Pushed to Supabase ✓")
        else:
            print(f"  Supabase push failed: {resp.status_code} {resp.text[:200]}")
    except Exception as e:
        print(f"  Supabase ERROR: {e}")


# ---------------------------------------------------------------------------
# BATCH POST-PROCESSING
# ---------------------------------------------------------------------------

def post_process_batch(results: list) -> list:
    """After running a batch, add relative rankings and cross-clip context."""
    if not results:
        return results

    scored = [(i, r) for i, r in enumerate(results) if r.get("clip_meta", {}).get("clip_quality_score")]
    scored.sort(key=lambda x: x[1]["clip_meta"]["clip_quality_score"], reverse=True)

    for rank, (original_idx, _) in enumerate(scored, 1):
        results[original_idx]["daas_signals"]["clip_rank_in_batch"] = rank
        score = results[original_idx]["clip_meta"]["clip_quality_score"]
        avg = sum(r["clip_meta"].get("clip_quality_score", 0) for r in results if r.get("clip_meta")) / len(results)
        results[original_idx]["daas_signals"]["relative_quality_vs_batch"] = "above_average" if score > avg else "below_average"

    return results


# ---------------------------------------------------------------------------
# COMPARE MODELS
# ---------------------------------------------------------------------------

def compare_models(video_url: str, output_dir: str):
    """Run same clip through both flash and pro models and print a diff report."""
    print(f"\n{'='*60}")
    print(f"COMPARE MODELS: {GEMINI_MODEL} vs {GEMINI_MODEL_COMPARE}")
    print(f"{'='*60}")

    model_flash = init_gemini(GEMINI_MODEL)
    model_pro   = init_gemini(GEMINI_MODEL_COMPARE)

    with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as tmp:
        tmp_path = tmp.name

    try:
        if not download_video(video_url, tmp_path):
            return

        # Upload once, analyze twice
        video_file = upload_to_gemini(tmp_path)
        if not video_file:
            return

        extra_context = {"video_url": video_url, "platform": "Courtana", "sport": "pickleball"}

        print(f"\n--- Running {GEMINI_MODEL} ---")
        result_flash = analyze_video(model_flash, video_file, extra_context)

        print(f"\n--- Running {GEMINI_MODEL_COMPARE} ---")
        result_pro   = analyze_video(model_pro,   video_file, extra_context)

        cleanup_gemini_file(video_file)

        if not result_flash or not result_pro:
            print("ERROR: One or both models failed to return results.")
            return

        # Save both outputs
        safe_name = video_url.split("/")[-1].replace(".mp4", "")
        ts = int(time.time())
        path_flash = Path(output_dir) / f"analysis_{safe_name}_{GEMINI_MODEL}_{ts}.json"
        path_pro   = Path(output_dir) / f"analysis_{safe_name}_{GEMINI_MODEL_COMPARE}_{ts}.json"
        result_flash["_model_used"] = GEMINI_MODEL
        result_pro["_model_used"]   = GEMINI_MODEL_COMPARE
        with open(path_flash, "w") as f: json.dump(result_flash, f, indent=2)
        with open(path_pro,   "w") as f: json.dump(result_pro,   f, indent=2)
        print(f"\nSaved: {path_flash}")
        print(f"Saved: {path_pro}")

        # Print diff report on key scalar fields
        compare_fields = [
            ("clip_meta", "clip_quality_score"),
            ("clip_meta", "viral_potential_score"),
            ("clip_meta", "watchability_score"),
            ("storytelling", "story_arc"),
            ("storytelling", "emotional_tone"),
            ("daas_signals", "highlight_category"),
            ("daas_signals", "clip_summary_one_sentence"),
        ]

        print(f"\n{'='*60}")
        print(f"DIFF REPORT: {GEMINI_MODEL} vs {GEMINI_MODEL_COMPARE}")
        print(f"{'='*60}")
        print(f"{'FIELD':40}  {'FLASH':25}  {'PRO':25}  MATCH?")
        print(f"{'-'*100}")
        for section, field in compare_fields:
            val_flash = str(result_flash.get(section, {}).get(field, "—"))
            val_pro   = str(result_pro.get(section, {}).get(field, "—"))
            match     = "==" if val_flash == val_pro else "!="
            print(f"  {section}.{field:33}  {val_flash:25}  {val_pro:25}  {match}")

    finally:
        Path(tmp_path).unlink(missing_ok=True)


# ---------------------------------------------------------------------------
# CORE PIPELINE: ANALYZE ONE VIDEO URL
# ---------------------------------------------------------------------------

def analyze_url(model, video_url: str, highlight_meta: dict = None, use_supabase: bool = False,
                output_dir: str = ".", voice_pipeline: str = None) -> Optional[dict]:
    """Full pipeline: download → upload → analyze → save."""
    print(f"\n{'='*60}")
    print(f"Analyzing: {video_url[-60:]}")
    print(f"{'='*60}")

    with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as tmp:
        tmp_path = tmp.name

    try:
        # 1. Download
        if not download_video(video_url, tmp_path):
            return None

        # 2. Upload to Gemini
        video_file = upload_to_gemini(tmp_path)
        if not video_file:
            return None

        # 3. Analyze
        extra_context = {
            "video_url": video_url,
            "highlight_metadata": highlight_meta or {},
            "platform": "Courtana (courtana.com)",
            "sport": "pickleball"
        }
        result = analyze_video(model, video_file, extra_context)

        # 4. Cleanup Gemini file
        cleanup_gemini_file(video_file)

        if result:
            # Add source metadata
            result["_source_url"] = video_url
            result["_highlight_meta"] = highlight_meta or {}

            # 5. Save JSON locally
            safe_name = video_url.split("/")[-1].replace(".mp4", "")
            out_path = Path(output_dir) / f"analysis_{safe_name}_{int(time.time())}.json"
            with open(out_path, "w") as f:
                json.dump(result, f, indent=2)
            print(f"  Saved: {out_path}")

            # 6. Print highlights
            print(f"\n  QUICK RESULTS:")
            print(f"    Quality Score:   {result.get('clip_meta', {}).get('clip_quality_score')}/10")
            print(f"    Viral Potential: {result.get('clip_meta', {}).get('viral_potential_score')}/10")
            print(f"    Story Arc:       {result.get('storytelling', {}).get('story_arc')}")
            print(f"    Brands:          {[b['brand_name'] for b in result.get('brand_detection', {}).get('brands', [])]}")
            print(f"    Caption:         {result.get('commentary', {}).get('social_media_caption')}")
            print(f"    Ron Burgundy:    {result.get('commentary', {}).get('ron_burgundy_voice', '')[:100]}")

            # 7. Push to Supabase
            if use_supabase:
                push_to_supabase(result, highlight_meta)

            # 8. Voice pipeline (optional)
            if voice_pipeline:
                print(f"\n  Running voice pipeline ({voice_pipeline})...")
                subprocess.run([
                    'python', 'elevenlabs-voice-pipeline.py',
                    '--analysis', str(out_path),
                    '--voice', voice_pipeline
                ])

        return result

    finally:
        Path(tmp_path).unlink(missing_ok=True)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    global GEMINI_MODEL
    parser = argparse.ArgumentParser(description="Pickle DaaS — Gemini Video Analyzer")

    # Input modes
    input_group = parser.add_mutually_exclusive_group(required=True)
    input_group.add_argument("--url",            help="Single video URL to analyze")
    input_group.add_argument("--url-file",       help="JSON file with array of video URLs (or highlight objects)")
    input_group.add_argument("--courtana-token", help="Courtana JWT — fetches from live API")
    input_group.add_argument("--compare-models", metavar="URL", help="Run clip through both flash and pro models and print diff")
    input_group.add_argument("--batch-dir",      help="Directory to auto-find *clips*.json and process all clips")

    # Batch options
    parser.add_argument("--player", help="Filter by Courtana player username (e.g. PickleBill)")
    parser.add_argument("--limit", type=int, default=20, help="Max highlights to process (default: 20)")

    # Output options
    parser.add_argument("--output-dir", default="./pickle-daas-output", help="Where to save JSON files")
    parser.add_argument("--supabase", action="store_true", help="Push results to Supabase")

    # Model option
    parser.add_argument("--model", default=None, help=f"Gemini model to use (default: {GEMINI_MODEL})")

    # Post-analysis pipeline
    parser.add_argument("--voice-pipeline", default=None, metavar="VOICE",
                        help="After analysis, auto-run elevenlabs-voice-pipeline.py with this voice preset (e.g. espn, ron_burgundy)")

    args = parser.parse_args()

    # Setup
    if args.model:
        GEMINI_MODEL = args.model
    Path(args.output_dir).mkdir(parents=True, exist_ok=True)

    # ---- Compare models mode ----
    if args.compare_models:
        compare_models(args.compare_models, args.output_dir)
        return

    model = init_gemini()
    results = []

    # ---- Single URL ----
    if args.url:
        result = analyze_url(model, args.url, use_supabase=args.supabase, output_dir=args.output_dir,
                             voice_pipeline=args.voice_pipeline)
        if result:
            results.append(result)

    # ---- URL file ----
    elif args.url_file:
        with open(args.url_file) as f:
            items = json.load(f)

        # Accept either plain URL strings or highlight objects with 'file' key
        for item in items[:args.limit]:
            if isinstance(item, str):
                url = item
                meta = {}
            else:
                url = item.get("file") or item.get("url")
                meta = item

            if url:
                result = analyze_url(model, url, highlight_meta=meta, use_supabase=args.supabase,
                                     output_dir=args.output_dir, voice_pipeline=args.voice_pipeline)
                if result:
                    results.append(result)
                time.sleep(2)  # Be gentle with Gemini rate limits

    # ---- Batch dir — auto-find *clips*.json ----
    elif args.batch_dir:
        import glob as _glob
        clip_files = _glob.glob(os.path.join(args.batch_dir, "*clips*.json"), recursive=False)
        if not clip_files:
            clip_files = _glob.glob(os.path.join(args.batch_dir, "**", "*clips*.json"), recursive=True)
        if not clip_files:
            print(f"ERROR: No *clips*.json found in {args.batch_dir}")
            sys.exit(1)

        print(f"Found clip files: {clip_files}")
        for clip_file in clip_files:
            print(f"\nProcessing clip file: {clip_file}")
            with open(clip_file) as f:
                items = json.load(f)

            if not isinstance(items, list):
                items = items.get("clips") or items.get("highlights") or []

            for item in items[:args.limit]:
                if isinstance(item, str):
                    url  = item
                    meta = {}
                else:
                    url  = item.get("file") or item.get("url") or item.get("video_url")
                    meta = item

                if url:
                    result = analyze_url(model, url, highlight_meta=meta, use_supabase=args.supabase,
                                         output_dir=args.output_dir, voice_pipeline=args.voice_pipeline)
                    if result:
                        results.append(result)
                    time.sleep(2)

    # ---- Courtana live API ----
    elif args.courtana_token:
        highlights = fetch_highlights_from_courtana(
            token=args.courtana_token,
            player_username=args.player,
            limit=args.limit
        )

        for h in highlights:
            video_url = h.get("file")
            if not video_url:
                continue
            result = analyze_url(model, video_url, highlight_meta=h, use_supabase=args.supabase,
                                 output_dir=args.output_dir, voice_pipeline=args.voice_pipeline)
            if result:
                results.append(result)
            time.sleep(2)

    # ---- Post-process batch ----
    if len(results) > 1:
        results = post_process_batch(results)
        batch_path = Path(args.output_dir) / f"batch_summary_{int(time.time())}.json"
        with open(batch_path, "w") as f:
            json.dump(results, f, indent=2)
        print(f"\n{'='*60}")
        print(f"BATCH COMPLETE: {len(results)} clips analyzed")
        print(f"Batch summary saved: {batch_path}")

        # Push batch results to Supabase via push-to-supabase.py if requested
        if args.supabase:
            print(f"\nPushing batch to Supabase via push-to-supabase.py...")
            subprocess.run([
                'python', 'push-to-supabase.py',
                f'{args.output_dir}/**/analysis_*.json'
            ])

        # Print top clips
        sorted_results = sorted(results, key=lambda r: r.get("clip_meta", {}).get("clip_quality_score", 0), reverse=True)
        print(f"\nTOP 5 CLIPS BY QUALITY:")
        for i, r in enumerate(sorted_results[:5], 1):
            name    = r.get("_highlight_meta", {}).get("name", "Unknown")
            score   = r.get("clip_meta", {}).get("clip_quality_score", "?")
            caption = r.get("commentary", {}).get("social_media_caption", "")
            print(f"  {i}. [{score}/10] {name} — {caption[:60]}")


if __name__ == "__main__":
    main()

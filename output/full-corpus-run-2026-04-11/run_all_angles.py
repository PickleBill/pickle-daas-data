#!/usr/bin/env python3
"""
Full Corpus All-Angles Analysis
PickleBill / Courtana — 2026-04-11
One Gemini pass per clip capturing: tactical + player + brand + narrative
"""

import os, sys, json, time, glob, logging, datetime, traceback
from pathlib import Path
from dotenv import load_dotenv

# Load env from PICKLE-DAAS root
env_path = Path(__file__).parent.parent.parent / '.env'
load_dotenv(env_path)

import google.generativeai as genai
import requests

# ─── CONFIG ──────────────────────────────────────────────────────────────────
GEMINI_API_KEY    = os.getenv('GEMINI_API_KEY')
COURTANA_TOKEN    = os.getenv('COURTANA_TOKEN')
BASE_URL          = 'https://courtana.com'
ANON_ENDPOINT     = f'{BASE_URL}/app/anon-highlight-groups/'
PAGE_SIZE         = 100
MODEL             = 'gemini-2.5-flash-preview-04-17'
HARD_STOP_USD     = 22.00   # stop fetching new clips above this
ABSOLUTE_MAX_USD  = 25.00   # emergency kill
COST_PER_CLIP_EST = 0.0054  # estimated cost per clip
LOG_EVERY         = 10      # log running cost every N clips

RUN_DIR   = Path(__file__).parent
ANALYSES  = RUN_DIR / 'analyses'
ANALYSES.mkdir(exist_ok=True)
MANIFEST  = RUN_DIR / 'clip-manifest.json'
COST_LOG  = RUN_DIR / 'cost-log.jsonl'
PROGRESS  = RUN_DIR / 'progress.json'

# ─── LOGGING ────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s %(message)s',
    handlers=[
        logging.FileHandler(RUN_DIR / 'run.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
log = logging.getLogger(__name__)

# ─── GEMINI SETUP ────────────────────────────────────────────────────────────
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel(MODEL)

# ─── PROMPT TEMPLATE ─────────────────────────────────────────────────────────
ALL_ANGLES_PROMPT = """You are an expert pickleball analyst with deep knowledge of professional play, coaching, equipment, and sports media.

Analyze this pickleball highlight video clip and return a SINGLE JSON object with ALL of the following fields. Be specific and evidence-based. If something cannot be determined from the video, use null.

Return ONLY valid JSON, no markdown, no explanation.

{{
  "clip_uuid": "{clip_uuid}",
  "clip_url": "{clip_url}",
  "analysis_timestamp": "{timestamp}",

  "shot_analysis": {{
    "shots": [
      {{
        "shot_type": "dink|drive|lob|drop|erne|atp|volley|overhead|serve|reset|speedup",
        "player_position": "kitchen|transition|baseline",
        "quality_score": 1-10,
        "difficulty_score": 1-10,
        "outcome": "winner|error|rally_continues|forced_error",
        "wow_factor": 1-10,
        "timestamp_approximate_seconds": float
      }}
    ],
    "total_shots_counted": int,
    "rally_length": int,
    "rally_duration_seconds": float,
    "rally_type": "dink_battle|drive_exchange|mixed|quick_point",
    "kitchen_control_percentage": 0-100,
    "dominant_shot_type": "string",
    "winning_shot_type": "string|null",
    "error_type": "unforced|forced|null",
    "sequence_pattern": "describe the key shot sequence in plain English"
  }},

  "skill_indicators": {{
    "court_coverage": 1-10,
    "kitchen_mastery": 1-10,
    "power_game": 1-10,
    "touch_and_feel": 1-10,
    "athleticism": 1-10,
    "creativity": 1-10,
    "court_iq": 1-10,
    "consistency": 1-10,
    "composure": 1-10,
    "paddle_control": 1-10,
    "aggression_style": "aggressive|balanced|defensive|counter-puncher",
    "play_style_tags": ["list", "of", "style", "descriptors"],
    "tactical_tendencies": "plain English description of observable patterns",
    "DUPR_estimate": "2.0-3.0|3.0-3.5|3.5-4.0|4.0-4.5|4.5-5.0|5.0+",
    "skill_level_label": "beginner|intermediate|advanced|professional",
    "signature_moves_observed": ["list of notable moves"]
  }},

  "brand_detection": {{
    "paddle_brands": ["list of brands seen on paddles"],
    "apparel_brands": ["list of clothing/shoe brands visible"],
    "equipment_visible": ["bags", "water bottles", "accessories with logos"],
    "sponsorship_logos": ["logos seen on court, banner, shirt"],
    "court_branding": "describe any court-side signage or branding",
    "confidence_notes": "how confident are you in brand IDs (1-10)"
  }},

  "narrative": {{
    "highlight_category": "trick_shot|clutch_moment|athletic_rally|comedy|teaching_moment|competitive_intensity|beginner_win|pro_showcase",
    "viral_score": 1-10,
    "story_arc": "plain English description of the narrative arc of this clip",
    "comedy_potential": 1-10,
    "sponsor_pitch_moment": true|false,
    "sponsor_pitch_reason": "string|null",
    "social_caption_draft": "ready-to-post caption for Instagram/TikTok",
    "best_for_investor_demo": true|false,
    "why_memorable": "one sentence on what makes this clip stick in memory"
  }},

  "venue_signals": {{
    "indoor_outdoor": "indoor|outdoor|unclear",
    "court_surface": "concrete|asphalt|sport_court|other|unclear",
    "court_quality": "recreational|club|tournament|unclear",
    "lighting_quality": "poor|adequate|good|excellent",
    "crowd_present": true|false,
    "estimated_venue_type": "community_center|private_club|resort|dedicated_pickleball|backyard|unclear"
  }},

  "data_quality": {{
    "video_clarity": 1-10,
    "angle_quality": 1-10,
    "analysis_confidence": 1-10,
    "limiting_factors": ["list any factors that limited analysis quality"]
  }}
}}"""

# ─── HELPERS ─────────────────────────────────────────────────────────────────

def get_already_analyzed():
    """Collect all clip UUIDs already analyzed in previous runs."""
    analyzed = set()
    base = Path(__file__).parent.parent
    patterns = [
        'batches/2026-04-11-tactical/analysis_*.json',
        'batches/batch-30-daas/analysis_*.json',
        'batches/broadcast/analysis_*.json',
        'batches/picklebill-batch-001/analysis_*.json',
        'batches/test-001/analysis_*.json',
        'picklebill-batch-20260410/analysis_*.json',
        'batch-30-daas/analysis_*.json',
        'full-corpus-run-2026-04-11/analyses/analysis_*.json',
    ]
    for pat in patterns:
        for f in glob.glob(str(base / pat)):
            fname = Path(f).stem  # analysis_{uuid}_{ts}
            # strip "analysis_" prefix then take UUID (first 36 chars or dash-joined)
            rest = fname[len('analysis_'):]
            # UUID is 36 chars: 8-4-4-4-12
            uuid = rest[:36]
            analyzed.add(uuid)
    return analyzed


def fetch_all_clips():
    """Paginate Courtana anon endpoint, collect all highlight clips with video URLs."""
    all_clips = []
    page = 1
    headers = {'Accept': 'application/json'}

    log.info("Fetching clip manifest from Courtana API...")

    while True:
        url = f'{ANON_ENDPOINT}?page_size={PAGE_SIZE}&page={page}'
        try:
            resp = requests.get(url, headers=headers, timeout=30)
            resp.raise_for_status()
            data = resp.json()
        except Exception as e:
            log.error(f"Page {page} fetch failed: {e}")
            break

        results = data.get('results', [])
        if not results:
            log.info(f"No results on page {page}, stopping pagination.")
            break

        for group in results:
            group_id = group.get('random_id') or str(group.get('id'))
            for hl in group.get('highlights', []):
                file_url = hl.get('file', '')
                if not file_url or not file_url.endswith('.mp4'):
                    continue
                clip_uuid = hl.get('random_id') or hl.get('id')
                if not clip_uuid:
                    continue
                all_clips.append({
                    'uuid': str(clip_uuid),
                    'url': file_url,
                    'group_id': group_id,
                    'thumbnail': hl.get('thumbnail_file', ''),
                    'name': hl.get('name', ''),
                    'type': hl.get('type', ''),
                    'ai_analyzed': hl.get('ai_analyzed', False),
                    'created_at': hl.get('created_at', ''),
                    'participants': [p.get('username') for p in group.get('participants', [])]
                })

        total_pages = data.get('total_pages', 1)
        log.info(f"Page {page}/{total_pages} — clips so far: {len(all_clips)}")

        if page >= total_pages:
            break

        page += 1
        time.sleep(0.1)  # polite rate limiting

    log.info(f"Total clips fetched: {len(all_clips)}")
    return all_clips


def analyze_clip(clip):
    """Call Gemini with all-angles prompt for one clip. Returns dict or None."""
    clip_uuid = clip['uuid']
    clip_url = clip['url']
    timestamp = datetime.datetime.utcnow().isoformat() + 'Z'

    prompt = ALL_ANGLES_PROMPT.format(
        clip_uuid=clip_uuid,
        clip_url=clip_url,
        timestamp=timestamp
    )

    # Build message with video URL for Gemini to analyze
    # Gemini 2.5 Flash can analyze video from URL via file API, but for CDN direct URLs
    # we pass as a Part with file_data
    import google.generativeai as genai2

    contents = [
        {
            "parts": [
                {
                    "file_data": {
                        "mime_type": "video/mp4",
                        "file_uri": clip_url
                    }
                },
                {
                    "text": prompt
                }
            ]
        }
    ]

    max_retries = 3
    for attempt in range(max_retries):
        try:
            response = model.generate_content(
                contents,
                generation_config={
                    "temperature": 0.1,
                    "max_output_tokens": 4096,
                    "response_mime_type": "application/json"
                }
            )
            text = response.text.strip()
            # Clean up any markdown fences if present
            if text.startswith('```'):
                text = text.split('\n', 1)[1].rsplit('```', 1)[0]
            result = json.loads(text)
            result['_clip_meta'] = clip
            return result
        except json.JSONDecodeError as e:
            log.warning(f"JSON parse error on {clip_uuid} attempt {attempt+1}: {e}")
            if attempt == max_retries - 1:
                return {'error': 'json_parse_failed', '_clip_meta': clip, 'raw': text[:500]}
        except Exception as e:
            err_str = str(e)
            if 'RATE_LIMIT' in err_str or '429' in err_str or 'quota' in err_str.lower():
                wait = 2 ** (attempt + 2)  # 4, 8, 16 seconds
                log.warning(f"Rate limit on {clip_uuid}, waiting {wait}s...")
                time.sleep(wait)
            elif 'SAFETY' in err_str or 'blocked' in err_str.lower():
                log.warning(f"Safety block on {clip_uuid}: {err_str[:100]}")
                return {'error': 'safety_blocked', '_clip_meta': clip}
            else:
                log.error(f"Gemini error on {clip_uuid} attempt {attempt+1}: {err_str[:200]}")
                if attempt == max_retries - 1:
                    return {'error': err_str[:200], '_clip_meta': clip}
                time.sleep(2 ** attempt)

    return None


def save_analysis(result, clip_uuid):
    out_path = ANALYSES / f'analysis_{clip_uuid}.json'
    with open(out_path, 'w') as f:
        json.dump(result, f, indent=2)
    return out_path


def log_cost(clip_uuid, cumulative_cost, clips_done, clips_total):
    entry = {
        'ts': datetime.datetime.utcnow().isoformat(),
        'clip_uuid': clip_uuid,
        'cumulative_cost_usd': round(cumulative_cost, 4),
        'clips_done': clips_done,
        'clips_total': clips_total
    }
    with open(COST_LOG, 'a') as f:
        f.write(json.dumps(entry) + '\n')


def save_progress(done_uuids, total_cost, clips_total):
    with open(PROGRESS, 'w') as f:
        json.dump({
            'last_updated': datetime.datetime.utcnow().isoformat(),
            'clips_analyzed': len(done_uuids),
            'clips_total': clips_total,
            'total_cost_usd': round(total_cost, 4),
            'done_uuids': list(done_uuids)
        }, f, indent=2)


# ─── MAIN ────────────────────────────────────────────────────────────────────

def main():
    log.info("=" * 60)
    log.info("FULL CORPUS ALL-ANGLES RUN — 2026-04-11")
    log.info("=" * 60)

    if not GEMINI_API_KEY:
        log.error("GEMINI_API_KEY not set. Aborting.")
        sys.exit(1)

    # Step 1: Get already-analyzed clips
    already_done = get_already_analyzed()
    log.info(f"Previously analyzed: {len(already_done)} clips (will skip)")

    # Step 2: Load or fetch manifest
    if MANIFEST.exists():
        log.info("Loading existing clip manifest...")
        with open(MANIFEST) as f:
            all_clips = json.load(f)
        log.info(f"Manifest loaded: {len(all_clips)} clips")
    else:
        log.info("Fetching clip manifest from Courtana API (this may take a few minutes)...")
        all_clips = fetch_all_clips()
        with open(MANIFEST, 'w') as f:
            json.dump(all_clips, f, indent=2)
        log.info(f"Manifest saved: {len(all_clips)} clips")

    # Step 3: Filter to unanalyzed clips
    to_analyze = [c for c in all_clips if c['uuid'] not in already_done]
    log.info(f"Clips to analyze: {len(to_analyze)} (of {len(all_clips)} total)")

    # Step 4: Estimate total cost
    est_cost = len(to_analyze) * COST_PER_CLIP_EST
    log.info(f"Estimated cost: ${est_cost:.2f} (budget: ${HARD_STOP_USD})")

    if est_cost > ABSOLUTE_MAX_USD:
        clips_at_budget = int(HARD_STOP_USD / COST_PER_CLIP_EST)
        log.info(f"Will cap at ~{clips_at_budget} clips to stay within ${HARD_STOP_USD} budget")

    # Step 5: Run analysis
    total_cost = 0.0
    done_in_run = []
    errors = []

    for i, clip in enumerate(to_analyze):
        clip_uuid = clip['uuid']

        # Cost check
        if total_cost >= HARD_STOP_USD:
            log.info(f"HARD STOP: Reached ${total_cost:.4f} — stopping at {len(done_in_run)} clips")
            break

        # Emergency kill
        if total_cost >= ABSOLUTE_MAX_USD:
            log.error(f"EMERGENCY STOP: Cost ${total_cost:.4f} exceeds ${ABSOLUTE_MAX_USD}")
            break

        log.info(f"[{i+1}/{len(to_analyze)}] Analyzing {clip_uuid} — running cost: ${total_cost:.4f}")

        result = analyze_clip(clip)

        if result:
            out_path = save_analysis(result, clip_uuid)
            done_in_run.append(clip_uuid)
            total_cost += COST_PER_CLIP_EST

            if 'error' in result:
                errors.append({'uuid': clip_uuid, 'error': result['error']})
                log.warning(f"  Error result saved: {result['error']}")
            else:
                log.info(f"  Saved to {out_path.name}")
        else:
            errors.append({'uuid': clip_uuid, 'error': 'no_result_returned'})
            log.error(f"  No result for {clip_uuid}")

        # Log cost every N clips
        if (i + 1) % LOG_EVERY == 0:
            log_cost(clip_uuid, total_cost, len(done_in_run), len(to_analyze))
            save_progress(set(list(already_done) + done_in_run), total_cost, len(all_clips))
            log.info(f"  === CHECKPOINT: {len(done_in_run)} done, ${total_cost:.4f} spent ===")

        # Small delay between clips to avoid rate limits
        time.sleep(0.5)

    # Final save
    all_done = set(list(already_done) + done_in_run)
    save_progress(all_done, total_cost, len(all_clips))
    log_cost('FINAL', total_cost, len(done_in_run), len(to_analyze))

    log.info("=" * 60)
    log.info(f"RUN COMPLETE")
    log.info(f"Clips analyzed this run: {len(done_in_run)}")
    log.info(f"Total clips ever analyzed: {len(all_done)}")
    log.info(f"Total cost this run: ${total_cost:.4f}")
    log.info(f"Errors: {len(errors)}")
    log.info("=" * 60)

    if errors:
        with open(RUN_DIR / 'errors.json', 'w') as f:
            json.dump(errors, f, indent=2)
        log.info(f"Error log: {RUN_DIR / 'errors.json'}")

    return {
        'clips_this_run': len(done_in_run),
        'total_ever': len(all_done),
        'cost_usd': total_cost,
        'errors': len(errors)
    }


if __name__ == '__main__':
    result = main()
    print(json.dumps(result, indent=2))

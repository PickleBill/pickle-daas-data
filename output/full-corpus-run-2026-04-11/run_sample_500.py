#!/usr/bin/env python3
"""
Sample-500 Analysis — PickleBill / Courtana 2026-04-11
Stratified sample of 500 clips from 20,034-clip corpus.
Budget: $5 hard stop (~925 clips max @ $0.0054, so 500 is safe)
All-angles: tactical + player + brand + narrative in ONE Gemini call.
Saves progress every 10 clips so restarts resume cleanly.
"""

import os, sys, json, time, glob, logging, datetime, io
from pathlib import Path
from dotenv import load_dotenv

PICKLE_DAAS_ROOT = Path(__file__).parent.parent.parent
load_dotenv(PICKLE_DAAS_ROOT / '.env')

import google.genai as genai
from google.genai import types
import requests

# ─── CONFIG ──────────────────────────────────────────────────────────────────
GEMINI_API_KEY    = os.getenv('GEMINI_API_KEY')
MODEL             = 'gemini-2.5-flash'
HARD_STOP_USD     = 5.00       # Per Bill's instruction: hard stop at $5
COST_PER_CLIP_EST = 0.0054
LOG_EVERY         = 10
MAX_RETRIES       = 3
DOWNLOAD_TIMEOUT  = 45
MAX_CLIP_MB       = 50

RUN_DIR  = Path(__file__).parent
ANALYSES = RUN_DIR / 'analyses'
ANALYSES.mkdir(exist_ok=True)
SAMPLE   = RUN_DIR / 'sample-500.json'
COST_LOG = RUN_DIR / 'cost-log.jsonl'
PROGRESS = RUN_DIR / 'progress.json'

# ─── LOGGING ─────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s %(message)s',
    handlers=[
        logging.FileHandler(RUN_DIR / 'run.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
log = logging.getLogger(__name__)

client = genai.Client(api_key=GEMINI_API_KEY)

# ─── SCHEMA (flat, all-angles) ────────────────────────────────────────────────
ANALYSIS_SCHEMA = {
    'type': 'object',
    'properties': {
        # Tactical
        'dominant_shot_type': {'type': 'string', 'description': 'dink|drive|lob|drop|erne|atp|volley|overhead|serve|reset|speedup'},
        'rally_length': {'type': 'integer', 'description': 'Number of shots in the rally'},
        'kitchen_control_pct': {'type': 'integer', 'description': '0-100'},
        'rally_type': {'type': 'string', 'description': 'dink_battle|drive_exchange|mixed|quick_point'},
        'winning_shot_type': {'type': 'string', 'description': 'Shot that ended the rally, or null'},
        'error_type': {'type': 'string', 'description': 'unforced|forced|null'},
        'sequence_pattern': {'type': 'string', 'description': 'Key shot sequence in plain English'},
        'shot_breakdown': {'type': 'string', 'description': 'CSV of shot types e.g. dink,dink,drive,overhead'},
        # Player skill
        'skill_level': {'type': 'string', 'description': 'beginner|intermediate|advanced|professional'},
        'DUPR_estimate': {'type': 'string', 'description': '2.0-3.0|3.0-3.5|3.5-4.0|4.0-4.5|4.5-5.0|5.0+'},
        'court_coverage': {'type': 'integer', 'description': '1-10'},
        'kitchen_mastery': {'type': 'integer', 'description': '1-10'},
        'athleticism': {'type': 'integer', 'description': '1-10'},
        'court_iq': {'type': 'integer', 'description': '1-10'},
        'aggression_style': {'type': 'string', 'description': 'aggressive|balanced|defensive|counter-puncher'},
        'play_style_tags': {'type': 'array', 'items': {'type': 'string'}, 'description': 'e.g. dink-heavy, power-hitter, kitchen-dominant'},
        'signature_moves': {'type': 'string', 'description': 'Notable moves like erne, ATP, fake drop'},
        # Brand
        'paddle_brands': {'type': 'array', 'items': {'type': 'string'}, 'description': 'Selkirk, Joola, Engage, Franklin, Head, Paddletek, Gamma, etc.'},
        'apparel_brands': {'type': 'array', 'items': {'type': 'string'}, 'description': 'Nike, Adidas, K-Swiss, Lululemon, etc.'},
        'sponsorship_logos': {'type': 'array', 'items': {'type': 'string'}, 'description': 'Logos on court, banners, walls'},
        # Narrative
        'viral_score': {'type': 'integer', 'description': '1-10'},
        'highlight_category': {'type': 'string', 'description': 'trick_shot|clutch_moment|athletic_rally|comedy|teaching_moment|competitive_intensity|beginner_win|pro_showcase'},
        'best_for_investor_demo': {'type': 'boolean'},
        'comedy_potential': {'type': 'integer', 'description': '1-10'},
        'why_memorable': {'type': 'string', 'description': 'One sentence on what makes this clip stick'},
        'social_caption': {'type': 'string', 'description': 'Instagram/TikTok ready caption with emojis'},
        # Venue
        'indoor_outdoor': {'type': 'string', 'description': 'indoor|outdoor|unclear'},
        'venue_type': {'type': 'string', 'description': 'community_center|private_club|resort|dedicated_pickleball|backyard|unclear'},
        'court_quality': {'type': 'string', 'description': 'recreational|club|tournament|unclear'},
        'crowd_present': {'type': 'boolean'},
        # Quality
        'video_clarity': {'type': 'integer', 'description': '1-10'},
        'analysis_confidence': {'type': 'integer', 'description': '1-10'},
    },
    'required': [
        'dominant_shot_type', 'rally_length', 'viral_score', 'skill_level',
        'DUPR_estimate', 'analysis_confidence', 'highlight_category', 'indoor_outdoor'
    ]
}

ANALYSIS_PROMPT = """Analyze this pickleball highlight video clip. Fill in all fields based on what you observe.

Shot types: dink, drive, lob, drop, erne, atp, volley, overhead, serve, reset, speedup
Skill: beginner (DUPR 2-3), intermediate (3-3.5), advanced (3.5-4.5), professional (4.5+)
Style tags: dink-heavy, power-hitter, kitchen-dominant, lobber, all-court, baseline-oriented, counter-puncher
Category: trick_shot, clutch_moment, athletic_rally, comedy, teaching_moment, competitive_intensity, beginner_win, pro_showcase
Brands: Look carefully at paddle shapes and logos. Common: Selkirk, Joola, Engage, Franklin, Head, Paddletek, Gamma."""


def get_done_uuids():
    """Return set of UUIDs already analyzed in this run's analyses/ dir."""
    done = set()
    for f in glob.glob(str(ANALYSES / 'analysis_*.json')):
        stem = Path(f).stem  # analysis_<uuid>
        uuid = stem[len('analysis_'):]
        done.add(uuid)
    return done


def load_progress():
    """Load previous progress for cost accumulation across restarts."""
    if PROGRESS.exists():
        try:
            with open(PROGRESS) as f:
                p = json.load(f)
                return p.get('cost_usd_this_run', 0.0), p.get('clips_this_run', 0)
        except Exception:
            pass
    return 0.0, 0


def download_clip(url):
    try:
        resp = requests.get(url, timeout=DOWNLOAD_TIMEOUT, stream=True)
        resp.raise_for_status()
        cl = resp.headers.get('Content-Length')
        if cl and int(cl) > MAX_CLIP_MB * 1024 * 1024:
            log.warning(f"  Too large ({int(cl)//1024//1024}MB), skipping")
            return None
        content = resp.content
        if len(content) > MAX_CLIP_MB * 1024 * 1024:
            log.warning(f"  Downloaded {len(content)//1024//1024}MB, too large")
            return None
        return content
    except Exception as e:
        log.error(f"  Download error: {e}")
        return None


def analyze_clip(clip):
    uid  = clip['uuid']
    url  = clip['url']

    video_bytes = download_clip(url)
    if not video_bytes:
        return {'error': 'download_failed', '_clip_meta': clip}

    log.info(f"  {len(video_bytes)/1024/1024:.1f}MB downloaded")

    # Upload to Gemini Files API
    uploaded = None
    for attempt in range(MAX_RETRIES):
        try:
            uploaded = client.files.upload(
                file=io.BytesIO(video_bytes),
                config=types.UploadFileConfig(mime_type='video/mp4', display_name=f'{uid}.mp4')
            )
            break
        except Exception as e:
            if '429' in str(e) or 'quota' in str(e).lower():
                wait = 10 * (attempt + 1)
                log.warning(f"  Upload rate limit, wait {wait}s")
                time.sleep(wait)
            else:
                log.error(f"  Upload attempt {attempt+1}: {str(e)[:100]}")
                if attempt == MAX_RETRIES - 1:
                    return {'error': f'upload_failed: {str(e)[:80]}', '_clip_meta': clip}
                time.sleep(3)

    if not uploaded:
        return {'error': 'upload_failed', '_clip_meta': clip}

    # Wait for processing
    for _ in range(15):
        if uploaded.state.name != 'PROCESSING':
            break
        time.sleep(2)
        try:
            uploaded = client.files.get(name=uploaded.name)
        except Exception:
            break

    if uploaded.state.name != 'ACTIVE':
        try:
            client.files.delete(name=uploaded.name)
        except Exception:
            pass
        return {'error': f'file_not_active:{uploaded.state}', '_clip_meta': clip}

    # Analyze
    result = None
    for attempt in range(MAX_RETRIES):
        try:
            response = client.models.generate_content(
                model=MODEL,
                contents=[types.Content(parts=[
                    types.Part(file_data=types.FileData(mime_type='video/mp4', file_uri=uploaded.uri)),
                    types.Part(text=ANALYSIS_PROMPT)
                ])],
                config=types.GenerateContentConfig(
                    temperature=0.1,
                    max_output_tokens=4096,
                    response_mime_type='application/json',
                    response_schema=ANALYSIS_SCHEMA
                )
            )
            result = json.loads(response.text)
            result['_uuid'] = uid
            result['_url'] = url
            result['_clip_meta'] = clip
            result['_model'] = MODEL
            result['_ts'] = datetime.datetime.utcnow().isoformat() + 'Z'
            if response.usage_metadata:
                result['_tokens_in']  = response.usage_metadata.prompt_token_count
                result['_tokens_out'] = response.usage_metadata.candidates_token_count
            break

        except json.JSONDecodeError as e:
            log.warning(f"  JSON error attempt {attempt+1}: {e}")
            if attempt == MAX_RETRIES - 1:
                result = {'error': 'json_parse_failed', '_clip_meta': clip}

        except Exception as e:
            err = str(e)
            if '429' in err or 'quota' in err.lower() or 'exhausted' in err.lower():
                wait = 15 * (attempt + 1)
                log.warning(f"  Rate limit attempt {attempt+1}, wait {wait}s")
                time.sleep(wait)
            elif 'SAFETY' in err:
                result = {'error': 'safety_blocked', '_clip_meta': clip}
                break
            else:
                log.error(f"  Analysis error attempt {attempt+1}: {err[:120]}")
                if attempt == MAX_RETRIES - 1:
                    result = {'error': err[:150], '_clip_meta': clip}
                time.sleep(3)

    # Always delete uploaded file
    try:
        client.files.delete(name=uploaded.name)
    except Exception:
        pass

    return result or {'error': 'no_result', '_clip_meta': clip}


def save_analysis(result, uid):
    out = ANALYSES / f'analysis_{uid}.json'
    with open(out, 'w') as f:
        json.dump(result, f, indent=2)
    return out


def checkpoint(label, cost, done_count, total):
    entry = {
        'ts': datetime.datetime.utcnow().isoformat(),
        'label': str(label),
        'cost_usd': round(cost, 4),
        'done': done_count,
        'total': total
    }
    with open(COST_LOG, 'a') as f:
        f.write(json.dumps(entry) + '\n')
    with open(PROGRESS, 'w') as f:
        json.dump({
            'last_updated': datetime.datetime.utcnow().isoformat(),
            'clips_this_run': done_count,
            'total_in_sample': total,
            'cost_usd_this_run': round(cost, 4)
        }, f, indent=2)


def main():
    log.info("=" * 60)
    log.info("SAMPLE-500 ALL-ANGLES ANALYSIS — 2026-04-11")
    log.info(f"Model: {MODEL}  Hard stop: ${HARD_STOP_USD}")
    log.info("=" * 60)

    if not GEMINI_API_KEY:
        log.error("GEMINI_API_KEY missing from .env")
        sys.exit(1)

    # Load sample
    if not SAMPLE.exists():
        log.error(f"Sample file not found: {SAMPLE}")
        sys.exit(1)

    with open(SAMPLE) as f:
        sample = json.load(f)
    log.info(f"Sample loaded: {len(sample)} clips")

    # Resume support: skip already done
    already_done = get_done_uuids()
    prior_cost, prior_count = load_progress()
    log.info(f"Already done this run: {len(already_done)}  Prior cost: ${prior_cost:.4f}")

    to_analyze = [c for c in sample if c['uuid'] not in already_done]
    log.info(f"Remaining to analyze: {len(to_analyze)}")
    log.info(f"Est. cost for remainder: ${len(to_analyze) * COST_PER_CLIP_EST:.2f}")
    log.info(f"Est. time: {len(to_analyze) * 17 / 60:.0f} minutes at ~17s/clip")

    cost   = prior_cost
    done   = list(already_done)
    errors = []

    for i, clip in enumerate(to_analyze):
        uid = clip['uuid']

        if cost >= HARD_STOP_USD:
            log.info(f"HARD STOP at ${cost:.2f} — budget reached")
            break

        t0 = time.time()
        log.info(f"\n[{i+1}/{len(to_analyze)}] {uid}  ${cost:.4f} spent")

        result = analyze_clip(clip)

        if result:
            save_analysis(result, uid)
            done.append(uid)
            cost += COST_PER_CLIP_EST

            has_error = 'error' in result and 'viral_score' not in result
            if has_error:
                errors.append({'uuid': uid, 'error': result.get('error')})
                log.warning(f"  Error: {result.get('error')}")
            else:
                vs    = result.get('viral_score', '?')
                dupr  = result.get('DUPR_estimate', '?')
                cat   = result.get('highlight_category', '?')
                style = result.get('skill_level', '?')
                elapsed = time.time() - t0
                log.info(f"  viral={vs} dupr={dupr} cat={cat} skill={style} | {elapsed:.1f}s")
        else:
            errors.append({'uuid': uid, 'error': 'no_result'})

        if (i + 1) % LOG_EVERY == 0:
            log.info(f"  --- Checkpoint: {len(done)} done, ${cost:.4f} spent ---")
            checkpoint(uid, cost, len(done), len(sample))

    checkpoint('FINAL', cost, len(done), len(sample))

    if errors:
        with open(RUN_DIR / 'errors.json', 'w') as f:
            json.dump(errors, f, indent=2)

    summary = {
        'clips_analyzed_this_run': len(done) - len(already_done),
        'total_done_including_prior': len(done),
        'sample_size': len(sample),
        'corpus_total': 20034,
        'coverage_pct_of_corpus': round(len(done) / 20034 * 100, 2),
        'cost_usd': round(cost, 4),
        'errors': len(errors),
        'run_completed': datetime.datetime.utcnow().isoformat() + 'Z'
    }

    log.info("=" * 60)
    log.info("COMPLETE")
    for k, v in summary.items():
        log.info(f"  {k}: {v}")
    log.info("=" * 60)

    print("\n" + json.dumps(summary, indent=2))
    return summary


if __name__ == '__main__':
    main()

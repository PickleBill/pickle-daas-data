#!/usr/bin/env python3
"""
Full Corpus All-Angles Analysis
PickleBill / Courtana — 2026-04-11
One Gemini pass per clip: tactical + player + brand + narrative

Strategy: download CDN clip → upload via Files API → analyze with schema → delete
Validated: ~17s/clip, ~$0.0054/clip, ~6,400 input tokens, ~250 output tokens
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
BASE_URL          = 'https://courtana.com'
ANON_ENDPOINT     = f'{BASE_URL}/app/anon-highlight-groups/'
PAGE_SIZE         = 100
MODEL             = 'gemini-2.5-flash'
HARD_STOP_USD     = 22.00
ABSOLUTE_MAX_USD  = 25.00
COST_PER_CLIP_EST = 0.0054
LOG_EVERY         = 10
MAX_RETRIES       = 3
DOWNLOAD_TIMEOUT  = 45
MAX_CLIP_MB       = 50

RUN_DIR  = Path(__file__).parent
ANALYSES = RUN_DIR / 'analyses'
ANALYSES.mkdir(exist_ok=True)
MANIFEST = RUN_DIR / 'clip-manifest.json'
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

# ─── SCHEMA ──────────────────────────────────────────────────────────────────
ANALYSIS_SCHEMA = {
    'type': 'object',
    'properties': {
        # Tactical
        'dominant_shot_type': {'type': 'string', 'description': 'Most common shot: dink|drive|lob|drop|erne|atp|volley|overhead|serve|reset|speedup'},
        'rally_length': {'type': 'integer', 'description': 'Number of shots in the rally'},
        'kitchen_control_pct': {'type': 'integer', 'description': '0-100, percentage of play at kitchen line'},
        'rally_type': {'type': 'string', 'description': 'dink_battle|drive_exchange|mixed|quick_point'},
        'winning_shot_type': {'type': 'string', 'description': 'Shot that ended the rally, or null'},
        'error_type': {'type': 'string', 'description': 'unforced|forced|null'},
        'sequence_pattern': {'type': 'string', 'description': 'Key shot sequence in plain English'},
        'shot_breakdown': {'type': 'string', 'description': 'CSV of shot types seen e.g. dink,dink,drive,overhead'},
        # Player skill
        'skill_level': {'type': 'string', 'description': 'beginner|intermediate|advanced|professional'},
        'DUPR_estimate': {'type': 'string', 'description': '2.0-3.0|3.0-3.5|3.5-4.0|4.0-4.5|4.5-5.0|5.0+'},
        'court_coverage': {'type': 'integer', 'description': '1-10'},
        'kitchen_mastery': {'type': 'integer', 'description': '1-10'},
        'athleticism': {'type': 'integer', 'description': '1-10'},
        'court_iq': {'type': 'integer', 'description': '1-10'},
        'aggression_style': {'type': 'string', 'description': 'aggressive|balanced|defensive|counter-puncher'},
        'play_style_tags': {'type': 'array', 'items': {'type': 'string'}, 'description': 'e.g. dink-heavy, power-hitter, kitchen-dominant, lobber, all-court'},
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
        'analysis_confidence': {'type': 'integer', 'description': '1-10 overall confidence'},
    },
    'required': [
        'dominant_shot_type', 'rally_length', 'viral_score', 'skill_level',
        'DUPR_estimate', 'analysis_confidence', 'highlight_category', 'indoor_outdoor'
    ]
}

ANALYSIS_PROMPT = """Analyze this pickleball highlight video clip. Fill in all fields based on what you actually observe.

Shot types: dink, drive, lob, drop, erne, atp, volley, overhead, serve, reset, speedup
Skill: beginner (DUPR 2-3), intermediate (3-3.5), advanced (3.5-4.5), professional (4.5+)
Style tags: dink-heavy, power-hitter, kitchen-dominant, lobber, all-court, baseline-oriented, counter-puncher
Venue: community_center, private_club, resort, dedicated_pickleball, backyard, unclear
Category: trick_shot, clutch_moment, athletic_rally, comedy, teaching_moment, competitive_intensity, beginner_win, pro_showcase
Brands: Look carefully at paddle shapes, logos, clothing. Common paddles: Selkirk, Joola, Engage, Franklin, Head, Paddletek, Gamma."""


def get_already_analyzed():
    analyzed = set()
    base = PICKLE_DAAS_ROOT / 'output'
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
            rest = Path(f).stem[len('analysis_'):]
            clip_id = rest.split('_')[0] if '_' in rest else rest
            analyzed.add(clip_id)
    return analyzed


def fetch_all_clips():
    all_clips = []
    seen = set()
    headers = {'Accept': 'application/json'}

    log.info("Paginating Courtana API...")
    resp = requests.get(f'{ANON_ENDPOINT}?page_size={PAGE_SIZE}&page=1', headers=headers, timeout=30)
    data = resp.json()
    total_pages = data.get('total_pages', 1)
    log.info(f"Total pages: {total_pages}")

    def parse_page(page_data):
        clips = []
        for group in page_data.get('results', []):
            gid = group.get('random_id') or str(group.get('id', ''))
            plist = [p.get('username', '') for p in group.get('participants', [])]
            for hl in group.get('highlights', []):
                url = hl.get('file', '')
                if not url or not url.endswith('.mp4'):
                    continue
                uid = str(hl.get('random_id') or hl.get('id', ''))
                if not uid or uid in seen:
                    continue
                seen.add(uid)
                clips.append({
                    'uuid': uid,
                    'url': url,
                    'group_id': gid,
                    'thumbnail': hl.get('thumbnail_file', ''),
                    'name': hl.get('name', ''),
                    'type': hl.get('type', ''),
                    'created_at': hl.get('created_at', ''),
                    'participants': plist
                })
        return clips

    all_clips.extend(parse_page(data))

    for page in range(2, total_pages + 1):
        try:
            resp = requests.get(f'{ANON_ENDPOINT}?page_size={PAGE_SIZE}&page={page}', headers=headers, timeout=30)
            resp.raise_for_status()
            all_clips.extend(parse_page(resp.json()))
        except Exception as e:
            log.error(f"Page {page} error: {e}")
            time.sleep(2)

        if page % 100 == 0:
            log.info(f"  Page {page}/{total_pages} — {len(all_clips)} clips")
        time.sleep(0.05)

    log.info(f"Total clips: {len(all_clips)}")
    return all_clips


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
    uid = clip['uuid']
    url = clip['url']

    # Download
    video_bytes = download_clip(url)
    if not video_bytes:
        return {'error': 'download_failed', '_clip_meta': clip}

    mb = len(video_bytes) / 1024 / 1024
    log.info(f"  {mb:.1f}MB downloaded")

    # Upload to Files API
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
                result['_tokens_in'] = response.usage_metadata.prompt_token_count
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

    # Always delete file
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


def checkpoint(label, cost, done, total):
    with open(COST_LOG, 'a') as f:
        f.write(json.dumps({
            'ts': datetime.datetime.utcnow().isoformat(),
            'label': str(label),
            'cost_usd': round(cost, 4),
            'done': done,
            'total': total
        }) + '\n')
    with open(PROGRESS, 'w') as f:
        json.dump({
            'last_updated': datetime.datetime.utcnow().isoformat(),
            'clips_this_run': done,
            'total_in_corpus': total,
            'cost_usd_this_run': round(cost, 4)
        }, f, indent=2)


def main():
    log.info("=" * 60)
    log.info("FULL CORPUS ALL-ANGLES — 2026-04-11")
    log.info(f"Model: {MODEL}  Budget: ${HARD_STOP_USD}")
    log.info("=" * 60)

    if not GEMINI_API_KEY:
        log.error("GEMINI_API_KEY missing")
        sys.exit(1)

    already_done = get_already_analyzed()
    log.info(f"Previously analyzed: {len(already_done)}")

    if MANIFEST.exists():
        with open(MANIFEST) as f:
            all_clips = json.load(f)
        log.info(f"Manifest loaded: {len(all_clips)} clips")
    else:
        all_clips = fetch_all_clips()
        with open(MANIFEST, 'w') as f:
            json.dump(all_clips, f, indent=2)
        log.info(f"Manifest saved: {len(all_clips)} clips")

    to_analyze = [c for c in all_clips if c['uuid'] not in already_done]
    budget_cap = int(HARD_STOP_USD / COST_PER_CLIP_EST)
    if len(to_analyze) > budget_cap:
        to_analyze = to_analyze[:budget_cap]
        log.info(f"Capped to {budget_cap} clips for ${HARD_STOP_USD} budget")

    log.info(f"Clips to analyze: {len(to_analyze)}")
    log.info(f"Estimated cost: ${len(to_analyze) * COST_PER_CLIP_EST:.2f}")
    log.info(f"Estimated time: {len(to_analyze) * 17 / 3600:.1f}h at ~17s/clip")

    cost = 0.0
    done = []
    errors = []

    for i, clip in enumerate(to_analyze):
        uid = clip['uuid']

        if cost >= HARD_STOP_USD:
            log.info(f"HARD STOP at ${cost:.2f}")
            break
        if cost >= ABSOLUTE_MAX_USD:
            log.error(f"EMERGENCY STOP ${cost:.2f}")
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
                log.warning(f"  Error saved: {result.get('error')}")
            else:
                vs = result.get('viral_score', '?')
                dupr = result.get('DUPR_estimate', '?')
                cat = result.get('highlight_category', '?')
                elapsed = time.time() - t0
                log.info(f"  viral={vs} dupr={dupr} cat={cat} | {elapsed:.1f}s")
        else:
            errors.append({'uuid': uid, 'error': 'no_result'})

        if (i + 1) % LOG_EVERY == 0:
            checkpoint(uid, cost, len(done), len(to_analyze))

    checkpoint('FINAL', cost, len(done), len(to_analyze))

    if errors:
        with open(RUN_DIR / 'errors.json', 'w') as f:
            json.dump(errors, f, indent=2)

    summary = {
        'clips_this_run': len(done),
        'corpus_total': len(all_clips),
        'prev_analyzed': len(already_done),
        'total_ever': len(already_done) + len(done),
        'coverage_pct': round((len(already_done) + len(done)) / max(len(all_clips), 1) * 100, 2),
        'cost_usd': round(cost, 4),
        'errors': len(errors)
    }

    log.info("=" * 60)
    log.info("COMPLETE")
    for k, v in summary.items():
        log.info(f"  {k}: {v}")
    log.info("=" * 60)

    print(json.dumps(summary, indent=2))
    return summary


if __name__ == '__main__':
    main()

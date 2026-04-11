#!/usr/bin/env python3
"""
corpus-auto-ingest.py — chief@courtana.com AI Employee
=======================================================
Nightly auto-ingest of new Courtana highlight clips.

What it does:
  1. Fetches all highlight groups from the anon Courtana API
  2. Compares against existing corpus (enriched-corpus.json)
  3. Finds clips NOT yet in the corpus (new only)
  4. Runs Gemini 2.5 Flash analysis on each new clip (batch of 20 max)
  5. Saves results to output/batches/auto-[date]/
  6. Updates output/auto-ingest-log.json
  7. Hard stops if spend exceeds $5 in one run

PAGINATION RULE: NEVER use the `next` field from API responses.
It has a port 443 bug. Always manually increment ?page=N&page_size=100.

Usage:
  python agents/corpus-auto-ingest.py
  python agents/corpus-auto-ingest.py --dry-run     (preview only, no API calls)
  python agents/corpus-auto-ingest.py --max-clips 5 (limit clips to analyze)

Schedule: Nightly via cron (called by agent-loop.py)
"""

import os
import sys
import json
import time
import math
import urllib.request
import urllib.error
from pathlib import Path
from datetime import datetime

try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).parent.parent / ".env")
except ImportError:
    pass

# ---------------------------------------------------------------------------
# CONFIG
# ---------------------------------------------------------------------------

ROOT             = Path(__file__).parent.parent
CORPUS_PATH      = ROOT / "enriched-corpus.json"
BATCHES_DIR      = ROOT / "output" / "batches"
INGEST_LOG_PATH  = ROOT / "output" / "auto-ingest-log.json"

COURTANA_BASE    = "https://courtana.com"
COURTANA_ANON    = f"{COURTANA_BASE}/app/anon-highlight-groups/"
PAGE_SIZE        = 100
BATCH_SIZE       = 20          # Max clips to analyze in one Gemini batch
COST_PER_CLIP    = 0.0054      # Proven baseline (Gemini 2.5 Flash)
MAX_SPEND        = 5.00        # Hard stop if this is exceeded in one run

# Gemini
GEMINI_API_KEY   = os.getenv("GEMINI_API_KEY", "")
GEMINI_MODEL     = "gemini-2.5-flash"
GEMINI_URL       = (
    f"https://generativelanguage.googleapis.com/v1beta/models/"
    f"{GEMINI_MODEL}:generateContent?key={GEMINI_API_KEY}"
)

# ---------------------------------------------------------------------------
# ANALYSIS PROMPT — tactical + player + brand + narrative in ONE call
# ---------------------------------------------------------------------------

ANALYSIS_PROMPT = """You are a senior sports intelligence analyst. Analyze this pickleball highlight video clip.

Return ONLY a valid JSON object with these exact fields — no markdown, no commentary:

{
  "quality": <integer 1-10, overall clip quality for highlights>,
  "viral": <integer 1-10, viral/shareability potential>,
  "watchability": <integer 1-10, entertainment value>,
  "arc": <"rally" | "point_winner" | "error" | "serve" | "drop_shot" | "lob" | "speed_up" | "reset" | "other">,
  "summary": <1-sentence plain English description of what happens>,
  "dominant_shot": <most prominent shot type shown>,
  "total_shots": <estimated total shots in the rally>,
  "brands": [<list of visible brand names — be specific: "JOOLA Scorpeus", "Selkirk VANGUARD" etc>],
  "badges": [<list of tags: "cross_court_winner", "kitchen_battle", "speed_up_attack", "reset_mastery", "lob_winner", "erne", "ATP", "between_legs", "overhead_smash", "dink_duel", "tournament_play">],
  "social_caption": <punchy 1-sentence social media caption for this clip>,
  "coaching": <1-2 sentences coaching insight — what can players learn from this?>,
  "tactical": {
    "pattern": <tactical pattern observed>,
    "advantage": <"offense" | "defense" | "neutral">,
    "court_position": <where action happens: "kitchen", "transition", "baseline", "mixed">
  },
  "player": {
    "estimated_skill": <"beginner" | "intermediate" | "advanced" | "pro">,
    "play_style": <"aggressive" | "defensive" | "all-court" | "dink-heavy">,
    "fitness_signal": <"fresh" | "fatigued" | "unknown">
  },
  "narrative": {
    "momentum": <"building" | "peak" | "shift" | "stable">,
    "drama_level": <integer 1-10>
  },
  "model": "gemini-2.5-flash",
  "analyzed_at": "<ISO timestamp>"
}"""

# ---------------------------------------------------------------------------
# HELPERS
# ---------------------------------------------------------------------------

def log(msg: str):
    ts = datetime.now().strftime("%H:%M:%S")
    print(f"[{ts}] {msg}")


def fetch_page(page: int) -> dict:
    """Fetch one page from the anon endpoint. NEVER uses next field."""
    url = f"{COURTANA_ANON}?page_size={PAGE_SIZE}&page={page}"
    req = urllib.request.Request(url, headers={"Accept": "application/json"})
    max_retries = 4
    for attempt in range(max_retries):
        try:
            with urllib.request.urlopen(req, timeout=20) as r:
                return json.loads(r.read())
        except urllib.error.HTTPError as e:
            if e.code == 429:
                wait = 2 ** attempt
                log(f"  Rate limit on page {page}, waiting {wait}s...")
                time.sleep(wait)
            else:
                raise
        except Exception:
            if attempt == max_retries - 1:
                raise
            time.sleep(2 ** attempt)
    raise RuntimeError(f"Failed to fetch page {page} after {max_retries} attempts")


def fetch_all_highlight_groups() -> list[dict]:
    """Fetch every highlight group from the API. Pages manually — never uses `next`."""
    log("Fetching page 1 to get total count...")
    first = fetch_page(1)
    total_count = first.get("count", 0)
    results = first.get("results", [])

    total_pages = math.ceil(total_count / PAGE_SIZE)
    log(f"Total highlight groups: {total_count} across {total_pages} pages")

    for page in range(2, total_pages + 1):
        log(f"  Fetching page {page}/{total_pages}...")
        data = fetch_page(page)
        results.extend(data.get("results", []))
        time.sleep(0.3)  # Be polite

    log(f"Fetched {len(results)} total highlight groups")
    return results


def load_existing_corpus() -> set[str]:
    """Load existing corpus and return set of UUIDs already analyzed."""
    if not CORPUS_PATH.exists():
        log(f"No corpus found at {CORPUS_PATH} — treating all clips as new")
        return set()
    with open(CORPUS_PATH) as f:
        data = json.load(f)
    uuids = {item.get("uuid") for item in data if item.get("uuid")}
    log(f"Existing corpus: {len(uuids)} clips")
    return uuids


def extract_video_url(group: dict) -> str | None:
    """Pull the best video URL from a highlight group."""
    # Direct video_url field
    if group.get("video_url"):
        return group["video_url"]
    # Check clips array
    clips = group.get("clips", [])
    if clips:
        for clip in clips:
            url = clip.get("video_url") or clip.get("url")
            if url:
                return url
    # Try direct URL field
    if group.get("url"):
        return group["url"]
    return None


def analyze_clip_gemini(uuid: str, video_url: str) -> dict:
    """Run Gemini analysis on a single clip. Returns analysis dict."""
    if not GEMINI_API_KEY:
        raise ValueError("GEMINI_API_KEY not set in .env")

    payload = {
        "contents": [
            {
                "parts": [
                    {
                        "file_data": {
                            "mime_type": "video/mp4",
                            "file_uri": video_url
                        }
                    },
                    {"text": ANALYSIS_PROMPT}
                ]
            }
        ],
        "generationConfig": {
            "temperature": 0.2,
            "maxOutputTokens": 1024,
        }
    }

    data = json.dumps(payload).encode()
    req = urllib.request.Request(
        GEMINI_URL,
        data=data,
        headers={"Content-Type": "application/json"}
    )

    max_retries = 4
    for attempt in range(max_retries):
        try:
            with urllib.request.urlopen(req, timeout=60) as r:
                resp = json.loads(r.read())
                text = resp["candidates"][0]["content"]["parts"][0]["text"].strip()
                # Strip markdown code fences if Gemini wraps it
                if text.startswith("```"):
                    text = text.split("```")[1]
                    if text.startswith("json"):
                        text = text[4:].strip()
                result = json.loads(text)
                result["uuid"] = uuid
                result["video_url"] = video_url
                result["analyzed_at"] = datetime.now().isoformat()
                result["model"] = GEMINI_MODEL
                return result
        except urllib.error.HTTPError as e:
            if e.code == 429:
                wait = 2 ** (attempt + 2)
                log(f"    Rate limit, waiting {wait}s...")
                time.sleep(wait)
            elif e.code == 400:
                # Bad request — likely video URL not accessible
                raise ValueError(f"Gemini 400 on {uuid}: possibly inaccessible URL")
            else:
                raise
        except json.JSONDecodeError as e:
            raise ValueError(f"Gemini returned non-JSON for {uuid}: {e}")
    raise RuntimeError(f"Gemini failed after {max_retries} attempts for {uuid}")


def save_batch_results(results: list[dict], batch_dir: Path, run_meta: dict):
    """Save batch results to dated directory."""
    batch_dir.mkdir(parents=True, exist_ok=True)

    # Save individual clip results
    for item in results:
        uuid = item.get("uuid", "unknown")
        path = batch_dir / f"{uuid}.json"
        with open(path, "w") as f:
            json.dump(item, f, indent=2)

    # Save batch summary
    summary_path = batch_dir / "batch-summary.json"
    summary = {
        "run_at": run_meta["run_at"],
        "clips_analyzed": len(results),
        "cost_estimate": run_meta["cost_so_far"],
        "clips": [r.get("uuid") for r in results]
    }
    with open(summary_path, "w") as f:
        json.dump(summary, f, indent=2)

    log(f"Saved {len(results)} clips to {batch_dir}")


def update_ingest_log(entry: dict):
    """Append to the running auto-ingest-log.json."""
    INGEST_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)

    history = []
    if INGEST_LOG_PATH.exists():
        with open(INGEST_LOG_PATH) as f:
            history = json.load(f)

    history.append(entry)

    # Keep last 90 entries
    if len(history) > 90:
        history = history[-90:]

    with open(INGEST_LOG_PATH, "w") as f:
        json.dump(history, f, indent=2)


# ---------------------------------------------------------------------------
# MAIN
# ---------------------------------------------------------------------------

def main():
    import argparse
    parser = argparse.ArgumentParser(description="Nightly corpus auto-ingest")
    parser.add_argument("--dry-run", action="store_true",
                        help="Preview new clips without calling Gemini")
    parser.add_argument("--max-clips", type=int, default=BATCH_SIZE,
                        help=f"Max clips to analyze (default {BATCH_SIZE})")
    args = parser.parse_args()

    run_at = datetime.now().isoformat()
    date_str = datetime.now().strftime("%Y-%m-%d")
    run_meta = {
        "run_at": run_at,
        "clips_found": 0,
        "clips_analyzed": 0,
        "cost_so_far": 0.0,
        "errors": [],
        "status": "running"
    }

    print("=" * 60)
    print("  corpus-auto-ingest.py — chief@courtana.com")
    print(f"  {date_str} | dry_run={args.dry_run} | max_clips={args.max_clips}")
    print("=" * 60)

    # 1. Load existing corpus UUIDs
    existing_uuids = load_existing_corpus()

    # 2. Fetch all groups from API
    try:
        all_groups = fetch_all_highlight_groups()
    except Exception as e:
        log(f"ERROR fetching from Courtana API: {e}")
        run_meta["status"] = "failed"
        run_meta["errors"].append(f"API fetch failed: {e}")
        update_ingest_log(run_meta)
        sys.exit(1)

    # 3. Find new clips not in corpus
    new_groups = []
    for g in all_groups:
        uuid = g.get("uuid") or g.get("id")
        if uuid and uuid not in existing_uuids:
            video_url = extract_video_url(g)
            if video_url:
                new_groups.append({"uuid": uuid, "video_url": video_url, "raw": g})

    run_meta["clips_found"] = len(new_groups)
    log(f"\nNew clips not in corpus: {len(new_groups)}")

    if not new_groups:
        log("Nothing new to ingest. Corpus is up to date.")
        run_meta["status"] = "complete_no_new"
        update_ingest_log(run_meta)
        print("\nDone. Corpus already up to date.")
        return

    if args.dry_run:
        log("[DRY RUN] Would analyze these clips:")
        for g in new_groups[:args.max_clips]:
            log(f"  {g['uuid']} — {g['video_url'][:60]}...")
        log(f"  ... and {max(0, len(new_groups) - args.max_clips)} more")
        log(f"\n[DRY RUN] Estimated cost: ${len(new_groups[:args.max_clips]) * COST_PER_CLIP:.4f}")
        run_meta["status"] = "dry_run"
        update_ingest_log(run_meta)
        return

    if not GEMINI_API_KEY:
        log("ERROR: GEMINI_API_KEY not set in .env — cannot analyze clips")
        run_meta["status"] = "failed"
        run_meta["errors"].append("GEMINI_API_KEY missing")
        update_ingest_log(run_meta)
        sys.exit(1)

    # 4. Limit to max_clips
    to_analyze = new_groups[:args.max_clips]
    estimated_cost = len(to_analyze) * COST_PER_CLIP
    log(f"Analyzing {len(to_analyze)} clips (estimated cost: ${estimated_cost:.4f})")

    if estimated_cost > MAX_SPEND:
        log(f"WARNING: Estimated cost ${estimated_cost:.2f} exceeds ${MAX_SPEND} limit")
        safe_count = int(MAX_SPEND / COST_PER_CLIP)
        to_analyze = to_analyze[:safe_count]
        log(f"Reduced to {len(to_analyze)} clips to stay under budget")

    # 5. Create batch output directory
    batch_dir = BATCHES_DIR / f"auto-{date_str}"
    # If dir already exists from a prior run today, add a suffix
    if batch_dir.exists():
        suffix = datetime.now().strftime("%H%M")
        batch_dir = BATCHES_DIR / f"auto-{date_str}-{suffix}"

    results = []
    errors = []

    # 6. Analyze each clip
    for i, group in enumerate(to_analyze, 1):
        uuid = group["uuid"]
        video_url = group["video_url"]

        # Budget check before each clip
        if run_meta["cost_so_far"] >= MAX_SPEND:
            log(f"STOP: Reached ${MAX_SPEND} spend limit after {i-1} clips")
            run_meta["errors"].append(f"Stopped at ${MAX_SPEND} spend limit")
            break

        log(f"\n[{i}/{len(to_analyze)}] Analyzing {uuid[:16]}...")
        log(f"  URL: {video_url[:70]}...")

        try:
            result = analyze_clip_gemini(uuid, video_url)
            results.append(result)
            clip_cost = COST_PER_CLIP
            run_meta["cost_so_far"] += clip_cost
            run_meta["clips_analyzed"] += 1
            log(f"  quality={result.get('quality','?')} viral={result.get('viral','?')} "
                f"arc={result.get('arc','?')} cost=${clip_cost:.4f} "
                f"(total=${run_meta['cost_so_far']:.4f})")
        except Exception as e:
            log(f"  ERROR: {e}")
            errors.append({"uuid": uuid, "error": str(e)})
            run_meta["errors"].append(f"{uuid}: {e}")

        # Small delay between clips to avoid rate limits
        if i < len(to_analyze):
            time.sleep(1)

    # 7. Save results
    if results:
        save_batch_results(results, batch_dir, run_meta)
    else:
        log("No results to save (all clips failed or budget exhausted)")

    # 8. Update ingest log
    run_meta["status"] = "complete"
    run_meta["batch_dir"] = str(batch_dir)
    run_meta["error_count"] = len(errors)
    update_ingest_log(run_meta)

    # 9. Print summary
    print("\n" + "=" * 60)
    print(f"  RUN SUMMARY")
    print("=" * 60)
    print(f"  New clips found:     {run_meta['clips_found']}")
    print(f"  Clips analyzed:      {run_meta['clips_analyzed']}")
    print(f"  Errors:              {len(errors)}")
    print(f"  Total cost:          ${run_meta['cost_so_far']:.4f}")
    print(f"  Output:              {batch_dir}")
    print(f"  Log:                 {INGEST_LOG_PATH}")
    print("=" * 60)

    if errors:
        print(f"\n  Failed clips:")
        for e in errors:
            print(f"    {e['uuid'][:16]}: {e['error']}")


if __name__ == "__main__":
    main()

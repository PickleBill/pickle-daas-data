#!/usr/bin/env python3
"""
Task 2: Verification Re-Analysis
Pick 20 random clips with existing Gemini analysis.
Re-analyze them with the SAME prompt. Compare results.
"""

import json, os, sys, glob, random, time, tempfile
from datetime import datetime
from pathlib import Path
from collections import defaultdict

BASE = "/Users/billbricker/PickleBill Dropbox/PickleBill Team Folder/Claude Projects/PICKLE-DAAS"
BATCHES = f"{BASE}/output/batches"
OUT = f"{BASE}/output/discovery/v2"
os.makedirs(OUT, exist_ok=True)

# Add parent to path for imports
sys.path.insert(0, BASE)

try:
    from dotenv import load_dotenv
    load_dotenv(f"{BASE}/.env")
except ImportError:
    pass

from google import genai
from google.genai import types

print("=" * 70)
print("TASK 2: VERIFICATION RE-ANALYSIS")
print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("=" * 70)

# Load the SAME analysis prompt from the analyzer
sys.path.insert(0, BASE)
# Read ANALYSIS_PROMPT directly from the file to avoid import side effects
import re as re_mod
analyzer_path = os.path.join(BASE, "pickle-daas-gemini-analyzer.py")
with open(analyzer_path) as f:
    src = f.read()

# Extract ANALYSIS_PROMPT
match = re_mod.search(r'ANALYSIS_PROMPT\s*=\s*"""(.*?)"""', src, re_mod.DOTALL)
if match:
    ANALYSIS_PROMPT = match.group(1)
    print(f"Loaded ANALYSIS_PROMPT ({len(ANALYSIS_PROMPT)} chars)")
else:
    print("ERROR: Could not extract ANALYSIS_PROMPT from analyzer")
    sys.exit(1)

# Gather all unique clips with source URLs
all_files = glob.glob(f"{BATCHES}/**/analysis_*.json", recursive=True)
clip_map = {}
for f in all_files:
    bn = os.path.basename(f)
    parts = bn.replace("analysis_", "").split("_")
    clip_id = parts[0]
    mtime = os.path.getmtime(f)
    if clip_id not in clip_map or mtime > clip_map[clip_id]["mtime"]:
        clip_map[clip_id] = {"path": f, "mtime": mtime, "clip_id": clip_id}

# Load clips that have source URLs
candidates = []
for item in clip_map.values():
    try:
        with open(item["path"]) as fh:
            d = json.load(fh)
        url = d.get("_source_url", "")
        if url and "cdn.courtana.com" in url:
            candidates.append({
                "clip_id": item["clip_id"],
                "path": item["path"],
                "source_url": url,
                "original": d
            })
    except Exception:
        continue

print(f"Candidates with CDN URLs: {len(candidates)}")

# Pick 20 random clips (seed=42 for reproducibility)
random.seed(42)
sample = random.sample(candidates, min(20, len(candidates)))
print(f"Selected {len(sample)} clips for re-analysis")

# Initialize Gemini client
api_key = os.environ.get("GEMINI_API_KEY")
if not api_key:
    print("ERROR: GEMINI_API_KEY not set")
    sys.exit(1)

client = genai.Client(api_key=api_key)
MODEL = "gemini-2.5-flash-lite"  # Same model as current pipeline

import requests as req

def download_video(url, dest):
    try:
        r = req.get(url, timeout=60)
        if r.status_code == 200:
            with open(dest, "wb") as f:
                f.write(r.content)
            return True
    except Exception as e:
        print(f"  Download error: {e}")
    return False

def compare_brands(orig, reanalysis):
    """Compare brand detection between original and re-analysis."""
    def get_brands(d):
        bd = d.get("brand_detection", {})
        if isinstance(bd, dict):
            return set(b.get("brand_name", "").lower().strip()
                      for b in (bd.get("brands", []) or [])
                      if isinstance(b, dict) and b.get("brand_name"))
        return set()

    orig_brands = get_brands(orig)
    re_brands = get_brands(reanalysis)

    if not orig_brands and not re_brands:
        return {"match": True, "agreement": 1.0, "orig": [], "re": [], "note": "both empty"}

    union = orig_brands | re_brands
    intersection = orig_brands & re_brands
    agreement = len(intersection) / len(union) if union else 1.0

    return {
        "match": orig_brands == re_brands,
        "agreement": round(agreement, 3),
        "orig": sorted(orig_brands),
        "re": sorted(re_brands),
        "added": sorted(re_brands - orig_brands),
        "removed": sorted(orig_brands - re_brands)
    }

def compare_shots(orig, reanalysis):
    """Compare shot counts between original and re-analysis."""
    def get_shot_count(d):
        sa = d.get("shot_analysis", {})
        if isinstance(sa, dict):
            return len(sa.get("shots", []) or [])
        elif isinstance(sa, list):
            return len(sa)
        return 0

    orig_n = get_shot_count(orig)
    re_n = get_shot_count(reanalysis)

    if orig_n == 0 and re_n == 0:
        return {"match": True, "within_20pct": True, "orig": 0, "re": 0}

    max_n = max(orig_n, re_n)
    diff_pct = abs(orig_n - re_n) / max_n if max_n > 0 else 0

    return {
        "match": orig_n == re_n,
        "within_20pct": diff_pct <= 0.20,
        "orig": orig_n,
        "re": re_n,
        "diff_pct": round(diff_pct * 100, 1)
    }

def compare_skill(orig, reanalysis):
    """Compare skill level estimates."""
    def get_skill(d):
        players = d.get("players_detected", [])
        if isinstance(players, list) and players:
            for p in players:
                if isinstance(p, dict):
                    sl = p.get("estimated_skill_level", "")
                    if sl:
                        return sl.lower().strip()
        return "unknown"

    orig_skill = get_skill(orig)
    re_skill = get_skill(reanalysis)
    return {
        "match": orig_skill == re_skill,
        "orig": orig_skill,
        "re": re_skill
    }

def compare_dupr(orig, reanalysis):
    """Compare DUPR estimates."""
    def get_dupr(d):
        si = d.get("skill_indicators", {})
        if isinstance(si, dict):
            dupr = si.get("estimated_dupr_range", si.get("dupr_estimate", ""))
            return str(dupr).strip() if dupr else "none"
        return "none"

    orig_dupr = get_dupr(orig)
    re_dupr = get_dupr(reanalysis)

    # Try numeric comparison
    def parse_dupr_mid(s):
        try:
            parts = s.replace("-", " ").split()
            nums = [float(x) for x in parts if x.replace(".", "").isdigit()]
            return sum(nums) / len(nums) if nums else None
        except Exception:
            return None

    orig_mid = parse_dupr_mid(orig_dupr)
    re_mid = parse_dupr_mid(re_dupr)

    within_half = False
    if orig_mid is not None and re_mid is not None:
        within_half = abs(orig_mid - re_mid) <= 0.5

    return {
        "match": orig_dupr == re_dupr,
        "within_0_5": within_half,
        "orig": orig_dupr,
        "re": re_dupr
    }

# Run re-analysis
results = []
total_cost = 0.0

for i, clip in enumerate(sample):
    print(f"\n[{i+1}/{len(sample)}] Clip: {clip['clip_id'][:12]}...")
    print(f"  URL: ...{clip['source_url'][-50:]}")

    with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as tmp:
        tmp_path = tmp.name

    try:
        if not download_video(clip["source_url"], tmp_path):
            print("  SKIP: download failed")
            results.append({"clip_id": clip["clip_id"], "status": "download_failed"})
            continue

        size_mb = os.path.getsize(tmp_path) / (1024 * 1024)
        if size_mb > 20:
            print(f"  SKIP: {size_mb:.1f} MB too large")
            results.append({"clip_id": clip["clip_id"], "status": "too_large"})
            continue

        video_bytes = Path(tmp_path).read_bytes()
        video_part = types.Part.from_bytes(data=video_bytes, mime_type="video/mp4")

        t_start = time.time()
        try:
            response = client.models.generate_content(
                model=MODEL,
                contents=[video_part, ANALYSIS_PROMPT],
                config=types.GenerateContentConfig(
                    temperature=0.3,
                    max_output_tokens=12288,
                ),
            )
            elapsed = time.time() - t_start

            # Parse JSON from response
            text = response.text
            # Try to extract JSON
            import re as re_mod2
            json_match = re_mod2.search(r'\{[\s\S]*\}', text)
            if json_match:
                reanalysis = json.loads(json_match.group())
            else:
                print(f"  WARN: No JSON in response")
                results.append({"clip_id": clip["clip_id"], "status": "no_json"})
                continue

            # Compare
            brand_cmp = compare_brands(clip["original"], reanalysis)
            shot_cmp = compare_shots(clip["original"], reanalysis)
            skill_cmp = compare_skill(clip["original"], reanalysis)
            dupr_cmp = compare_dupr(clip["original"], reanalysis)

            result = {
                "clip_id": clip["clip_id"],
                "status": "success",
                "elapsed_seconds": round(elapsed, 1),
                "brand_comparison": brand_cmp,
                "shot_comparison": shot_cmp,
                "skill_comparison": skill_cmp,
                "dupr_comparison": dupr_cmp
            }
            results.append(result)

            print(f"  OK ({elapsed:.1f}s) | Brands: {brand_cmp['agreement']:.0%} | "
                  f"Shots: {'✓' if shot_cmp['within_20pct'] else '✗'} | "
                  f"Skill: {'✓' if skill_cmp['match'] else '✗'} | "
                  f"DUPR: {'✓' if dupr_cmp.get('within_0_5') else '✗'}")

        except Exception as e:
            print(f"  Gemini error: {e}")
            results.append({"clip_id": clip["clip_id"], "status": f"error: {str(e)[:100]}"})

        # Rate limit
        time.sleep(2)

    finally:
        try:
            os.unlink(tmp_path)
        except Exception:
            pass

# Compute aggregate stats
successful = [r for r in results if r.get("status") == "success"]
n = len(successful)

if n > 0:
    brand_agreement = sum(r["brand_comparison"]["agreement"] for r in successful) / n
    shot_agreement = sum(1 for r in successful if r["shot_comparison"]["within_20pct"]) / n
    skill_agreement = sum(1 for r in successful if r["skill_comparison"]["match"]) / n
    dupr_agreement = sum(1 for r in successful if r["dupr_comparison"].get("within_0_5")) / n
else:
    brand_agreement = shot_agreement = skill_agreement = dupr_agreement = 0

# Determine conclusions
conclusions = []
if brand_agreement >= 0.80:
    conclusions.append(f"Brand detection is reliable ({brand_agreement:.0%} agreement)")
else:
    conclusions.append(f"Brand detection inconsistent ({brand_agreement:.0%}) — needs prompt tuning")

if shot_agreement >= 0.80:
    conclusions.append(f"Shot counting is stable ({shot_agreement:.0%} within ±20%)")
else:
    conclusions.append(f"Shot counting varies ({shot_agreement:.0%}) — expect ±20% variance per clip")

if skill_agreement >= 0.70:
    conclusions.append(f"Skill estimates are consistent ({skill_agreement:.0%} exact match)")
else:
    conclusions.append(f"Skill estimates drift between runs ({skill_agreement:.0%}) — treat as approximate")

if dupr_agreement >= 0.60:
    conclusions.append(f"DUPR predictions stable within ±0.5 ({dupr_agreement:.0%})")
else:
    conclusions.append(f"DUPR predictions need calibration ({dupr_agreement:.0%} within ±0.5)")

report = {
    "generated_at": datetime.now().isoformat(),
    "clips_tested": len(sample),
    "clips_successful": n,
    "clips_failed": len(sample) - n,
    "model_used": MODEL,
    "brand_agreement_rate": round(brand_agreement, 3),
    "shot_count_agreement": round(shot_agreement, 3),
    "skill_level_agreement": round(skill_agreement, 3),
    "dupr_agreement": round(dupr_agreement, 3),
    "conclusions": conclusions,
    "per_clip_results": results
}

with open(f"{OUT}/verification-report.json", "w") as fh:
    json.dump(report, fh, indent=2)

print(f"\n{'='*60}")
print("VERIFICATION SUMMARY")
print(f"{'='*60}")
print(f"Clips tested: {len(sample)} | Successful: {n}")
print(f"Brand agreement:  {brand_agreement:.0%}")
print(f"Shot agreement:   {shot_agreement:.0%}")
print(f"Skill agreement:  {skill_agreement:.0%}")
print(f"DUPR agreement:   {dupr_agreement:.0%}")
print(f"\nConclusions:")
for c in conclusions:
    print(f"  • {c}")
print(f"\nSaved to: {OUT}/verification-report.json")
print(f"Done: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

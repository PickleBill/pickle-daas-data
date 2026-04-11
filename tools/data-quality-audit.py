#!/usr/bin/env python3
"""
Task 1: Data Quality Audit
Audits all analysis JSONs for venue distribution, temporal distribution,
duplicate clips, and sample bias.
"""

import json, os, glob, re
from datetime import datetime
from collections import Counter, defaultdict

BASE = "/Users/billbricker/PickleBill Dropbox/PickleBill Team Folder/Claude Projects/PICKLE-DAAS"
BATCHES = f"{BASE}/output/batches"
OUT = f"{BASE}/output/discovery/v2"
os.makedirs(OUT, exist_ok=True)

print("=" * 70)
print("TASK 1: DATA QUALITY AUDIT")
print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("=" * 70)

# Load all analysis files
all_files = glob.glob(f"{BATCHES}/**/analysis_*.json", recursive=True)
print(f"\nFound {len(all_files)} analysis files")

# Deduplicate by clip UUID (keep latest)
clip_map = {}
for f in all_files:
    bn = os.path.basename(f)
    parts = bn.replace("analysis_", "").split("_")
    clip_id = parts[0]
    mtime = os.path.getmtime(f)
    if clip_id not in clip_map or mtime > clip_map[clip_id]["mtime"]:
        clip_map[clip_id] = {"path": f, "mtime": mtime, "clip_id": clip_id}

print(f"Unique clips (deduped): {len(clip_map)}")

# Track duplicates
dup_tracker = defaultdict(list)
for f in all_files:
    bn = os.path.basename(f)
    parts = bn.replace("analysis_", "").split("_")
    clip_id = parts[0]
    batch = os.path.basename(os.path.dirname(f))
    dup_tracker[clip_id].append({"batch": batch, "path": f})

duplicate_clips = {k: v for k, v in dup_tracker.items() if len(v) > 1}
print(f"Clips appearing in multiple batches: {len(duplicate_clips)}")

# Load and analyze each unique clip
clips = []
venue_counter = Counter()
temporal_counter = Counter()
source_url_domains = Counter()
brand_per_clip = []
skill_levels = Counter()
dupr_estimates = Counter()

for item in clip_map.values():
    try:
        with open(item["path"]) as fh:
            d = json.load(fh)
    except Exception:
        continue

    d["_clip_id"] = item["clip_id"]
    d["_batch"] = os.path.basename(os.path.dirname(item["path"]))
    clips.append(d)

    # Extract venue from source URL or highlight meta
    source_url = d.get("_source_url", "")
    meta = d.get("_highlight_meta", {}) or {}

    # Try to identify venue from various sources
    venue = "unknown"

    # Check highlight meta for venue info
    if isinstance(meta, dict):
        for key in ["venue", "venue_name", "facility", "location"]:
            if meta.get(key):
                venue = str(meta[key])
                break

    # Check brand detection for venue clues
    brands = d.get("brand_detection", {})
    if isinstance(brands, dict):
        brand_list = brands.get("brands", []) or []
        for b in brand_list:
            if isinstance(b, dict):
                name = b.get("brand_name", "")
                cat = b.get("category", "")
                if "LIFE TIME" in str(name).upper() or "LIFETIME" in str(name).upper():
                    venue = "Lifetime (detected via brand)"
                elif "Underground" in str(name):
                    venue = "The Underground (detected via brand)"

    venue_counter[venue] += 1

    # Temporal distribution
    analyzed_at = d.get("analyzed_at", "")
    if analyzed_at:
        try:
            dt = datetime.fromisoformat(analyzed_at.replace("Z", "+00:00"))
            temporal_counter[dt.strftime("%Y-%m")] += 1
        except Exception:
            temporal_counter["parse_error"] += 1

    # Source URL analysis
    if source_url:
        if "cdn.courtana.com" in source_url:
            source_url_domains["cdn.courtana.com"] += 1
        else:
            source_url_domains["other"] += 1

    # Skill level tracking
    players = d.get("players_detected", [])
    if isinstance(players, list):
        for p in players:
            if isinstance(p, dict):
                sl = p.get("estimated_skill_level", "")
                if sl:
                    skill_levels[sl] += 1

    # DUPR estimate tracking
    si = d.get("skill_indicators", {})
    if isinstance(si, dict):
        dupr = si.get("estimated_dupr_range", si.get("dupr_estimate", ""))
        if dupr:
            dupr_estimates[str(dupr)] += 1

    # Brand count per clip
    if isinstance(brands, dict):
        brand_list = brands.get("brands", []) or []
        brand_per_clip.append(len(brand_list))
    else:
        brand_per_clip.append(0)

# Compute bias flags
bias_flags = []
total = len(clips)

# Check venue concentration
if venue_counter:
    top_venue, top_count = venue_counter.most_common(1)[0]
    top_pct = round(top_count / total * 100, 1)
    if top_pct > 50:
        bias_flags.append(f"{top_pct}% of clips from '{top_venue}' — heavy single-venue bias")
    unknown_pct = round(venue_counter.get("unknown", 0) / total * 100, 1)
    if unknown_pct > 30:
        bias_flags.append(f"{unknown_pct}% of clips have no identifiable venue")

# Check temporal concentration
if temporal_counter:
    months = [k for k in temporal_counter if k != "parse_error"]
    if len(months) <= 2:
        bias_flags.append(f"Clips span only {len(months)} month(s) — limited temporal diversity")

# Sample selection
bias_flags.append("Sample is non-random: clips selected from Courtana highlight system, not sequential recording")
bias_flags.append("All clips sourced via CDN highlight groups — may over-represent 'interesting' moments vs typical play")

# Check skill level concentration
if skill_levels:
    top_skill, top_skill_count = skill_levels.most_common(1)[0]
    skill_total = sum(skill_levels.values())
    skill_pct = round(top_skill_count / skill_total * 100, 1)
    if skill_pct > 60:
        bias_flags.append(f"{skill_pct}% of players detected as '{top_skill}' — skill diversity limited")

# Duplicate analysis
dup_details = []
for clip_id, appearances in sorted(duplicate_clips.items(), key=lambda x: -len(x[1])):
    dup_details.append({
        "clip_id": clip_id,
        "appearances": len(appearances),
        "batches": [a["batch"] for a in appearances]
    })

# Batch distribution
batch_counts = Counter()
for c in clips:
    batch_counts[c["_batch"]] += 1

# Confidence cap recommendations
confidence_caps = {
    "single_venue_dominance": "Max confidence 80 (>50% of clips from one venue)",
    "non_random_sample": "Max confidence 75 (highlight clips, not random selection)",
    "small_n_threshold": "Max confidence 60 for any finding with N < 20",
    "temporal_limitation": "Max confidence 70 (limited month diversity)"
}

# V1 discovery impact assessment
v1_impact = [
    {
        "discovery": "JOOLA paddle dominance (77/127)",
        "impact": "HIGH — likely venue-specific artifact. Lifetime is a JOOLA partner.",
        "recommendation": "Flag as venue-biased. Needs multi-venue data to confirm."
    },
    {
        "discovery": "Courtana clips avg 7.43/10 quality",
        "impact": "MEDIUM — 'Courtana' means brand was detected on screen, not a product type. Self-selection likely.",
        "recommendation": "Clarify definition. Note that Courtana branding = venue's own system."
    },
    {
        "discovery": "Price signals ($5K-$15K/month)",
        "impact": "HIGH — no market comparables cited. Numbers are aspirational.",
        "recommendation": "Ground all pricing in real comparables (Sportradar, StatsBomb, ShotTracker, Hudl)."
    },
    {
        "discovery": "DUPR prediction 3.5-4.0 modal",
        "impact": "MEDIUM — methodology not explained. Likely reflects Lifetime membership demo.",
        "recommendation": "Explain: AI estimates from video cues (shot speed, positioning, decision quality). Note venue bias."
    },
    {
        "discovery": "Gatorade as 'unowned category'",
        "impact": "LOW-MEDIUM — methodology sound but framing misleading. AI checked for common sports brands and found none.",
        "recommendation": "Reframe: 'Zero hydration brand detected in 127 clips' with clear methodology note."
    },
    {
        "discovery": "84.3% of clips have identifiable brands",
        "impact": "LOW — this is a data observation, relatively robust.",
        "recommendation": "Keep but note sample is highlight clips (may have more branding than average)."
    }
]

# Build output
audit_result = {
    "generated_at": datetime.now().isoformat(),
    "total_analysis_files": len(all_files),
    "total_unique_clips": len(clips),
    "duplicate_clips_count": len(duplicate_clips),
    "venue_distribution": dict(venue_counter.most_common()),
    "temporal_distribution": dict(sorted(temporal_counter.items())),
    "source_url_domains": dict(source_url_domains),
    "batch_distribution": dict(batch_counts.most_common()),
    "skill_level_distribution": dict(skill_levels.most_common()),
    "dupr_estimate_distribution": dict(dupr_estimates.most_common()),
    "brand_stats": {
        "avg_brands_per_clip": round(sum(brand_per_clip) / len(brand_per_clip), 2) if brand_per_clip else 0,
        "clips_with_zero_brands": sum(1 for b in brand_per_clip if b == 0),
        "clips_with_3plus_brands": sum(1 for b in brand_per_clip if b >= 3)
    },
    "selection_bias_flags": bias_flags,
    "confidence_caps": confidence_caps,
    "duplicate_clip_details": dup_details[:20],
    "v1_discovery_impact_assessment": v1_impact,
    "recommendation": "Next batch should target: (1) Peak venue clips for multi-venue diversity, (2) random sampling within venue, (3) date diversity across 3+ months, (4) at least 50 clips per venue for statistical significance"
}

# Save
with open(f"{OUT}/data-quality-audit.json", "w") as fh:
    json.dump(audit_result, fh, indent=2)

print(f"\n--- RESULTS ---")
print(f"Unique clips: {len(clips)}")
print(f"Duplicates found: {len(duplicate_clips)}")
print(f"\nVenue distribution:")
for v, c in venue_counter.most_common():
    print(f"  {v}: {c} ({round(c/total*100,1)}%)")
print(f"\nTemporal distribution:")
for m, c in sorted(temporal_counter.items()):
    print(f"  {m}: {c}")
print(f"\nBatch distribution:")
for b, c in batch_counts.most_common():
    print(f"  {b}: {c}")
print(f"\nBias flags:")
for flag in bias_flags:
    print(f"  ⚠ {flag}")
print(f"\nSkill levels: {dict(skill_levels.most_common())}")
print(f"\nSaved to: {OUT}/data-quality-audit.json")
print(f"Done: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

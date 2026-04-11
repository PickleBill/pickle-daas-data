#!/usr/bin/env python3
"""
Pickle DaaS — Auto Push to gh-pages
=====================================
Rebuilds corpus-export.json from all analysis files, then pushes
updated data to the gh-pages branch for Lovable frontend consumption.

Run after any ingest batch to keep the live data current.

USAGE:
  python tools/push-to-ghpages.py              # Rebuild + push
  python tools/push-to-ghpages.py --dry-run    # Rebuild only, don't push
"""

import json
import glob
import os
import subprocess
import argparse
from collections import Counter
from datetime import datetime, timezone

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUTPUT = os.path.join(ROOT, "output")


def rebuild_corpus():
    """Rebuild corpus-export.json from all analysis files."""
    files = glob.glob(os.path.join(OUTPUT, "**", "analysis_*.json"), recursive=True)
    good = [f for f in files if os.path.getsize(f) > 5000]

    seen_urls = set()
    corpus = []
    brand_counter = Counter()
    shot_counter = Counter()
    arc_counter = Counter()
    quality_scores = []
    viral_scores = []

    for f in good:
        try:
            with open(f) as fh:
                d = json.load(fh)
            url = d.get("_source_url", "")
            if not url or url in seen_urls:
                continue
            seen_urls.add(url)

            meta = d.get("clip_meta", {})
            skills = d.get("skill_indicators", {})
            commentary = d.get("commentary", {})
            brands_raw = d.get("brand_detection", {})
            brands = brands_raw.get("brands", brands_raw.get("brands_detected", []))
            badges = d.get("badge_intelligence", {}).get("predicted_badges", [])
            story = d.get("storytelling", {})
            daas = d.get("daas_signals", {})
            shots = d.get("shot_analysis", {})

            uuid = url.split("/")[-1].replace(".mp4", "")
            thumb = url.replace(".mp4", ".jpeg")

            brand_names = list(set(b.get("brand_name", "") for b in brands if b.get("brand_name")))
            badge_names = [b.get("badge_name", "") for b in badges[:5] if b.get("badge_name")]

            q = meta.get("clip_quality_score") or 0
            v = meta.get("viral_potential_score") or 0
            if q: quality_scores.append(q)
            if v: viral_scores.append(v)

            for b in brand_names: brand_counter[b] += 1
            dom = shots.get("dominant_shot_type", "")
            if dom: shot_counter[dom] += 1
            arc = story.get("story_arc", "")
            if arc: arc_counter[arc] += 1

            corpus.append({
                "uuid": uuid,
                "video_url": url,
                "thumbnail": thumb,
                "quality": q,
                "viral": v,
                "watchability": meta.get("watchability_score") or 0,
                "arc": story.get("story_arc", ""),
                "summary": daas.get("clip_summary_one_sentence", ""),
                "dominant_shot": shots.get("dominant_shot_type", ""),
                "total_shots": shots.get("total_shots_estimated") or 0,
                "brands": brand_names,
                "badges": badge_names,
                "ron_burgundy": commentary.get("ron_burgundy_voice", "") or commentary.get("ron_burgundy_style", {}).get("commentary", ""),
                "social_caption": commentary.get("social_media_caption", ""),
                "espn": commentary.get("neutral_announcer_espn", "") or commentary.get("espn_style", {}).get("commentary", ""),
                "coaching": commentary.get("coaching_breakdown", ""),
                "hype": commentary.get("hype_announcer_charged", "") or commentary.get("charged_style", {}).get("commentary", ""),
                "skills": {
                    "court_coverage": skills.get("court_coverage_rating") or 0,
                    "kitchen": skills.get("kitchen_mastery_rating") or 0,
                    "power": skills.get("power_game_rating") or 0,
                    "touch": skills.get("touch_and_feel_rating") or 0,
                    "athleticism": skills.get("athleticism_rating") or 0,
                    "creativity": skills.get("creativity_rating") or 0,
                    "court_iq": skills.get("court_iq_rating") or 0,
                    "consistency": skills.get("consistency_rating") or 0,
                    "composure": skills.get("composure_under_pressure") or 0,
                },
                "model": d.get("model_used", "gemini-2.5-flash"),
                "signature_move": skills.get("signature_move_detected", ""),
                "play_style": skills.get("aggression_style", ""),
            })
        except Exception:
            continue

    corpus.sort(key=lambda c: c.get("quality", 0), reverse=True)

    # Save corpus
    corpus_path = os.path.join(OUTPUT, "corpus-export.json")
    with open(corpus_path, "w") as f:
        json.dump(corpus, f, indent=2)

    # Save enriched corpus (same data)
    with open(os.path.join(OUTPUT, "enriched-corpus.json"), "w") as f:
        json.dump(corpus, f, indent=2)

    # Save dashboard stats
    stats = {
        "total_clips": len(corpus),
        "unique_brands": len(brand_counter),
        "top_brands": [{"brand": b, "count": c} for b, c in brand_counter.most_common(15)],
        "avg_quality": round(sum(quality_scores) / len(quality_scores), 2) if quality_scores else 0,
        "avg_viral": round(sum(viral_scores) / len(viral_scores), 2) if viral_scores else 0,
        "shot_distribution": dict(shot_counter.most_common(10)),
        "arc_distribution": dict(arc_counter.most_common(10)),
        "cost_per_clip": 0.0054,
        "total_estimated_cost": round(len(corpus) * 0.0054, 2),
        "skills_populated": sum(1 for c in corpus if (c["skills"].get("kitchen") or 0) > 0),
        "models_used": dict(Counter(c["model"] for c in corpus)),
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }
    with open(os.path.join(OUTPUT, "dashboard-stats.json"), "w") as f:
        json.dump(stats, f, indent=2)

    print(f"  Corpus: {len(corpus)} clips ({stats['skills_populated']} with skills)")
    print(f"  Brands: {len(brand_counter)} | Top: {brand_counter.most_common(3)}")
    print(f"  Quality: {stats['avg_quality']} | Viral: {stats['avg_viral']}")
    return corpus, stats


def push_to_ghpages(dry_run=False):
    """Copy data files to gh-pages branch and push."""
    import tempfile
    import shutil

    tmpdir = tempfile.mkdtemp()

    # Files to push
    data_files = [
        "corpus-export.json",
        "enriched-corpus.json",
        "dashboard-stats.json",
        "player-profiles.json",
        "creative-badges.json",
        "voice-manifest.json",
    ]

    for f in data_files:
        src = os.path.join(OUTPUT, f)
        if os.path.exists(src):
            shutil.copy2(src, os.path.join(tmpdir, f))

    # Copy dashboards
    dash_dir = os.path.join(OUTPUT, "dashboards")
    if os.path.exists(dash_dir):
        tmpd = os.path.join(tmpdir, "dashboards")
        os.makedirs(tmpd, exist_ok=True)
        for f in glob.glob(os.path.join(dash_dir, "*.html")):
            shutil.copy2(f, tmpd)

    if dry_run:
        print(f"  DRY RUN — would push {len(os.listdir(tmpdir))} files to gh-pages")
        return

    # Git operations
    os.chdir(ROOT)

    # Save current branch
    result = subprocess.run(["git", "branch", "--show-current"], capture_output=True, text=True)
    current_branch = result.stdout.strip()

    try:
        subprocess.run(["git", "stash"], capture_output=True)
        subprocess.run(["git", "checkout", "gh-pages"], capture_output=True, check=True)

        # Copy files
        for f in data_files:
            src = os.path.join(tmpdir, f)
            if os.path.exists(src):
                shutil.copy2(src, os.path.join(ROOT, f))

        # Copy dashboards
        dash_dst = os.path.join(ROOT, "dashboards")
        os.makedirs(dash_dst, exist_ok=True)
        tmpd = os.path.join(tmpdir, "dashboards")
        if os.path.exists(tmpd):
            for f in glob.glob(os.path.join(tmpd, "*.html")):
                shutil.copy2(f, dash_dst)

        # Commit and push
        subprocess.run(["git", "add", "-A"], capture_output=True)
        result = subprocess.run(["git", "status", "--porcelain"], capture_output=True, text=True)
        if result.stdout.strip():
            ts = datetime.now().strftime("%Y-%m-%d %H:%M")
            subprocess.run([
                "git", "commit", "-m",
                f"Auto-update: corpus + dashboards ({ts})\n\nCo-Authored-By: Claude Opus 4.6 (1M context) <noreply@anthropic.com>"
            ], capture_output=True)
            subprocess.run(["git", "push", "origin", "gh-pages"], capture_output=True, check=True)
            print("  ✅ Pushed to gh-pages")
        else:
            print("  No changes to push")
    finally:
        subprocess.run(["git", "checkout", current_branch], capture_output=True)
        subprocess.run(["git", "stash", "pop"], capture_output=True)

    shutil.rmtree(tmpdir, ignore_errors=True)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    print("=" * 50)
    print("Pickle DaaS — Rebuild & Push to gh-pages")
    print("=" * 50)

    print("\n1. Rebuilding corpus...")
    corpus, stats = rebuild_corpus()

    print("\n2. Pushing to gh-pages...")
    push_to_ghpages(dry_run=args.dry_run)

    print(f"\n✅ Done. {stats['total_clips']} clips live at picklebill.github.io/pickle-daas-data/")


if __name__ == "__main__":
    main()

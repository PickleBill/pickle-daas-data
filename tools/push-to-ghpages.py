#!/usr/bin/env python3
"""
push-to-ghpages.py — Rebuild corpus + push to gh-pages
=======================================================
Reads all analysis JSON files from output/auto-ingest-* directories,
normalizes them to corpus format, merges with existing corpus-export.json,
updates dashboard-stats.json, commits and pushes to gh-pages branch.

Usage:
  python3 tools/push-to-ghpages.py
"""

import json
import glob
import subprocess
import sys
from collections import Counter
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).parent.parent
OUTPUT = ROOT / "output"
CORPUS_FILE = ROOT / "corpus-export.json"
STATS_FILE = ROOT / "dashboard-stats.json"


def extract_uuid(url):
    return url.split("/")[-1].replace(".mp4", "").replace(".jpeg", "")


def normalize_analysis(raw):
    """Convert a new-format analysis file to corpus export format."""
    src = raw.get("_source_url", "")
    uuid = extract_uuid(src) if src else raw.get("_highlight_meta", {}).get("uuid", "")
    if not uuid:
        return None

    clip_meta = raw.get("clip_meta", {})
    shot_analysis = raw.get("shot_analysis", {})
    skill = raw.get("skill_indicators", {})
    brands_raw = raw.get("brand_detection", {}).get("brands", [])
    badges = raw.get("_highlight_meta", {}).get("badge_awards", [])
    commentary = raw.get("commentary", {})
    daas = raw.get("daas_signals", {})
    storytelling = raw.get("storytelling", {})

    # Normalize brands list (may be list of strings or list of dicts)
    brands = []
    for b in brands_raw:
        if isinstance(b, str):
            brands.append(b)
        elif isinstance(b, dict):
            name = b.get("brand_name") or b.get("brand") or b.get("name", "")
            if name:
                brands.append(name)

    skills_map = {
        "court_coverage": skill.get("court_coverage_rating", 0),
        "kitchen": skill.get("kitchen_mastery_rating", 0),
        "power": skill.get("power_game_rating", 0),
        "touch": skill.get("touch_and_feel_rating", 0),
        "athleticism": skill.get("athleticism_rating", 0),
        "creativity": skill.get("creativity_rating", 0),
        "court_iq": skill.get("court_iq_rating", 0),
        "consistency": skill.get("consistency_rating", 0),
        "composure": skill.get("composure_under_pressure", 0),
    }

    play_style_tags = skill.get("play_style_tags", [])
    play_style = play_style_tags[0] if isinstance(play_style_tags, list) and play_style_tags else "balanced"

    return {
        "uuid": uuid,
        "video_url": src,
        "thumbnail": src.replace(".mp4", ".jpeg") if src else "",
        "quality": clip_meta.get("clip_quality_score", 0),
        "viral": clip_meta.get("viral_potential_score", 0),
        "watchability": clip_meta.get("watchability_score", 0),
        "arc": daas.get("highlight_category") or storytelling.get("story_arc") or "unknown",
        "summary": daas.get("clip_summary_one_sentence") or storytelling.get("narrative_arc_summary") or "",
        "dominant_shot": shot_analysis.get("dominant_shot_type") or shot_analysis.get("longest_exchange_type") or "unknown",
        "total_shots": shot_analysis.get("total_shots_estimated") or len(shot_analysis.get("shots", [])),
        "brands": brands,
        "badges": badges,
        "ron_burgundy": commentary.get("ron_burgundy_voice", ""),
        "social_caption": commentary.get("social_media_caption", ""),
        "espn": commentary.get("neutral_announcer_espn", ""),
        "coaching": commentary.get("coaching_breakdown", ""),
        "hype": commentary.get("hype_announcer_charged", ""),
        "skills": skills_map,
        "model": raw.get("_model_used") or raw.get("model_used", "gemini"),
        "signature_move": str(skill.get("signature_move_detected") or "null"),
        "play_style": play_style,
    }


def load_existing_corpus():
    """Load corpus-export.json from the gh-pages branch."""
    result = subprocess.run(
        ["git", "show", "gh-pages:output/corpus-export.json"],
        capture_output=True, text=True, cwd=ROOT
    )
    if result.returncode != 0:
        print("  Warning: could not load existing corpus from gh-pages, starting fresh")
        return {}
    try:
        data = json.loads(result.stdout)
        clips = data if isinstance(data, list) else data.get("clips", [])
        return {c["uuid"]: c for c in clips if "uuid" in c}
    except Exception as e:
        print(f"  Warning: error parsing corpus: {e}")
        return {}


def rebuild_corpus():
    """Scan all analysis files, normalize, merge with existing, dedup."""
    print("[1/4] Loading existing corpus from gh-pages...")
    existing = load_existing_corpus()
    print(f"  Existing: {len(existing)} clips")

    print("[2/4] Scanning new analysis files...")
    new_count = 0
    dup_count = 0
    error_count = 0
    new_clips = {}

    for json_path in sorted(glob.glob(str(OUTPUT / "auto-ingest-*" / "analysis_*.json"))):
        try:
            raw = json.loads(Path(json_path).read_text())
            clip = normalize_analysis(raw)
            if not clip:
                error_count += 1
                continue
            uuid = clip["uuid"]
            if uuid in new_clips:
                dup_count += 1  # duplicate within new runs
                continue
            new_clips[uuid] = clip
        except Exception as e:
            error_count += 1
            continue

    truly_new = {uuid: clip for uuid, clip in new_clips.items() if uuid not in existing}
    print(f"  Found: {len(new_clips)} analyzed clips in auto-ingest dirs")
    print(f"  Truly new (not in existing corpus): {len(truly_new)}")
    print(f"  Duplicates skipped: {dup_count}, errors: {error_count}")

    # Merge: existing takes precedence for shared UUIDs (preserve prior analysis quality)
    merged = {**new_clips, **existing}  # existing overwrites new for same UUIDs
    # But also add truly new ones
    for uuid, clip in truly_new.items():
        merged[uuid] = clip

    all_clips = list(merged.values())
    print(f"  Total corpus: {len(all_clips)} unique clips")
    return all_clips, len(truly_new)


def build_dashboard_stats(clips):
    """Generate dashboard-stats.json from corpus."""
    brand_counter = Counter()
    arc_counter = Counter()
    total_quality = 0
    total_viral = 0
    for c in clips:
        for b in (c.get("brands") or []):
            if b:
                brand_counter[b] += 1
        arc = c.get("arc") or "unknown"
        arc_counter[arc] += 1
        total_quality += c.get("quality") or 0
        total_viral += c.get("viral") or 0

    n = len(clips)
    return {
        "total_clips": n,
        "unique_brands": len(brand_counter),
        "top_brands": [{"brand": b, "count": cnt} for b, cnt in brand_counter.most_common(20)],
        "top_arcs": [{"arc": a, "count": cnt} for a, cnt in arc_counter.most_common(10)],
        "avg_quality": round(total_quality / n, 2) if n else 0,
        "avg_viral": round(total_viral / n, 2) if n else 0,
        "last_updated": datetime.now().isoformat(),
    }


def update_gh_pages(clips, new_count):
    """Update corpus-export.json and dashboard-stats.json on gh-pages branch using a worktree."""
    print("[3/4] Building dashboard stats...")
    stats = build_dashboard_stats(clips)

    corpus_json = json.dumps(clips, indent=2)
    stats_json = json.dumps(stats, indent=2)
    print(f"  corpus-export.json: {len(clips)} clips")
    print(f"  dashboard-stats.json: {stats['total_clips']} total, {stats['unique_brands']} brands")

    print("[4/4] Committing to gh-pages branch via worktree...")
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M")
    worktree_path = ROOT / ".gh-pages-worktree"

    # Clean up any leftover worktree
    subprocess.run(["git", "worktree", "remove", "--force", str(worktree_path)],
                   capture_output=True, cwd=ROOT)

    def run(cmd, check=True):
        result = subprocess.run(cmd, capture_output=True, text=True, cwd=ROOT)
        if check and result.returncode != 0:
            print(f"  ERROR: {' '.join(str(c) for c in cmd)}")
            print(f"  stdout: {result.stdout.strip()}")
            print(f"  stderr: {result.stderr.strip()}")
            raise RuntimeError(f"Command failed: {' '.join(str(c) for c in cmd)}")
        return result

    try:
        # Create worktree for gh-pages
        run(["git", "worktree", "add", str(worktree_path), "gh-pages"])
        print("  OK: git worktree add gh-pages")

        # Write updated files into worktree
        wt_output = worktree_path / "output"
        wt_output.mkdir(exist_ok=True)
        (wt_output / "corpus-export.json").write_text(corpus_json)
        (wt_output / "dashboard-stats.json").write_text(stats_json)

        # Commit and push from the worktree
        commit_msg = (
            f"Auto-update: corpus + dashboards ({now_str})\n\n"
            f"{new_count} new clips analyzed, corpus grows to {len(clips)}.\n\n"
            f"Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>"
        )
        subprocess.run(["git", "add", "output/corpus-export.json", "output/dashboard-stats.json"],
                       check=True, cwd=worktree_path)
        subprocess.run(["git", "commit", "-m", commit_msg],
                       check=True, cwd=worktree_path)
        subprocess.run(["git", "push", "origin", "gh-pages"],
                       check=True, cwd=worktree_path)
        print("  OK: pushed gh-pages")

        return True

    except Exception as e:
        print(f"  ERROR: {e}")
        return False
    finally:
        subprocess.run(["git", "worktree", "remove", "--force", str(worktree_path)],
                       capture_output=True, cwd=ROOT)


def main():
    print("=" * 60)
    print(f"Pickle DaaS — Push to gh-pages ({datetime.now().strftime('%Y-%m-%d %H:%M')})")
    print("=" * 60)
    print()

    clips, new_count = rebuild_corpus()
    if not clips:
        print("ERROR: No clips found. Aborting.")
        sys.exit(1)

    ok = update_gh_pages(clips, new_count)
    if ok:
        print()
        print(f"Done. Corpus: {len(clips)} clips (+{new_count} new). Live at: https://picklebill.github.io/pickle-daas-data/")
    else:
        print()
        print("ERROR: gh-pages push failed. See errors above.")
        sys.exit(1)


if __name__ == "__main__":
    main()

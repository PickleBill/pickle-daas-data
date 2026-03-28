#!/usr/bin/env python3
"""
Pickle DaaS — Brand Intelligence Report Generator
Reads batch_summary JSON → builds frequency table → outputs JSON + Markdown report.

Usage:
  python brand-intelligence-report.py ./output/picklebill-batch-001/batch_summary_*.json
"""

import json
import sys
import glob
from pathlib import Path
from datetime import datetime, timezone
from collections import defaultdict, Counter

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

CATEGORY_ICONS = {
    "paddle": "🏓", "shoes": "👟", "apparel_top": "👕", "apparel_bottom": "👖",
    "hat": "🧢", "headwear": "🧢", "sunglasses": "🕶️", "bag": "🎒",
    "court_surface": "🏟️", "net": "🥅", "ball": "🟡", "sponsor_banner": "📢",
    "other": "📦",
}


def load_batch(path_pattern):
    paths = glob.glob(path_pattern)
    if not paths:
        print(f"ERROR: No files found matching: {path_pattern}")
        sys.exit(1)
    results = []
    for p in paths:
        with open(p) as f:
            data = json.load(f)
        if isinstance(data, list):
            results.extend(data)
        else:
            results.append(data)
    return results


def build_brand_registry(results):
    brands = defaultdict(lambda: {
        "total_appearances": 0,
        "clips_seen_in": 0,
        "clip_ids": set(),
        "player_sides": Counter(),
        "confidences": Counter(),
        "categories": Counter(),
        "visibility": Counter(),
        "visible_seconds_total": 0,
    })
    whitespace_counter = Counter()

    for r in results:
        if not isinstance(r, dict):
            continue
        bd = r.get("brand_detection", {})
        clip_id = r.get("_highlight_meta", {}).get("id") or r.get("_source_url", "")

        for b in bd.get("brands", []):
            name = b.get("brand_name", "").strip()
            if not name:
                continue
            entry = brands[name]
            entry["total_appearances"] += 1
            entry["clip_ids"].add(clip_id)
            cat = b.get("category", "other")
            entry["categories"][cat] += 1
            entry["confidences"][b.get("confidence", "medium")] += 1
            entry["player_sides"][b.get("player_side", "unknown")] += 1
            entry["visibility"][b.get("visibility_quality", "unknown")] += 1
            secs = b.get("estimated_visible_seconds")
            if secs:
                entry["visible_seconds_total"] += float(secs)

        for ws in bd.get("sponsorship_whitespace", []):
            if ws:
                whitespace_counter[ws] += 1

    # Finalize
    registry = []
    for name, data in brands.items():
        data["clips_seen_in"] = len(data["clip_ids"])
        data.pop("clip_ids")
        dom_confidence = data["confidences"].most_common(1)[0][0] if data["confidences"] else "medium"
        dom_category   = data["categories"].most_common(1)[0][0] if data["categories"] else "other"
        registry.append({
            "brand_name": name,
            "dominant_category": dom_category,
            "total_appearances": data["total_appearances"],
            "clips_seen_in": data["clips_seen_in"],
            "avg_confidence": dom_confidence,
            "total_visible_seconds": round(data["visible_seconds_total"], 1),
            "categories": dict(data["categories"]),
            "player_sides": dict(data["player_sides"]),
        })

    registry.sort(key=lambda x: x["total_appearances"], reverse=True)
    whitespace = [{"brand": w, "mentions": c} for w, c in whitespace_counter.most_common(10)]
    return registry, whitespace


def write_markdown(registry, whitespace, total_clips, player, out_path):
    date_str = datetime.now(timezone.utc).strftime("%B %d, %Y")
    lines = [
        "# Courtana Brand Intelligence Report",
        f"**Generated:** {date_str}  |  **Clips analyzed:** {total_clips}  |  **Player:** {player}",
        "",
        "---",
        "",
        "## Top Brands Detected",
        "",
        "| # | Brand | Category | Appearances | Clips | Avg Confidence | Visible Seconds |",
        "|---|-------|----------|------------|-------|----------------|----------------|",
    ]
    for i, b in enumerate(registry[:15], 1):
        icon = CATEGORY_ICONS.get(b["dominant_category"], "📦")
        lines.append(
            f"| {i} | **{b['brand_name']}** | {icon} {b['dominant_category']} | "
            f"{b['total_appearances']} | {b['clips_seen_in']} | {b['avg_confidence']} | "
            f"{b['total_visible_seconds']}s |"
        )

    lines += [
        "",
        "---",
        "",
        "## Sponsorship Whitespace",
        "_Brands mentioned in 'sponsorship_whitespace' fields — present in the sport but NOT detected in clips._",
        "",
    ]
    if whitespace:
        lines += ["| Brand | Mentions |", "|-------|---------|"]
        for w in whitespace:
            lines.append(f"| {w['brand']} | {w['mentions']} |")
    else:
        lines.append("_None detected in this batch._")

    lines += [
        "",
        "---",
        "",
        "## Brand-Player Associations",
        "",
    ]
    for b in registry[:8]:
        sides = ", ".join(f"{k} ({v})" for k, v in b["player_sides"].items() if k != "unknown")
        lines.append(f"- **{b['brand_name']}** — {b['total_appearances']} appearances | sides: {sides or 'n/a'}")

    lines += [
        "",
        "---",
        "",
        "## Pitch Takeaways",
        "",
        f"- **{registry[0]['brand_name']}** is the dominant brand in this corpus ({registry[0]['total_appearances']} appearances across {registry[0]['clips_seen_in']} clips).",
        f"- **{len(registry)} distinct brands** detected across {total_clips} clips.",
        f"- **{len(whitespace)} whitespace opportunities** identified — brands relevant to pickleball not yet in these clips.",
        "",
        "_Report generated by Pickle DaaS — Courtana AI platform_",
    ]

    out_path.write_text("\n".join(lines))


def main():
    if len(sys.argv) < 2:
        print("Usage: python brand-intelligence-report.py <batch_summary.json>")
        sys.exit(1)

    path_pattern = sys.argv[1]
    player = "PickleBill"
    if "--player" in sys.argv:
        idx = sys.argv.index("--player")
        player = sys.argv[idx + 1]

    results = load_batch(path_pattern)
    registry, whitespace = build_brand_registry(results)

    out_dir = Path("./output")
    out_dir.mkdir(exist_ok=True)

    json_path = out_dir / "brand-registry.json"
    with open(json_path, "w") as f:
        json.dump({"generated_at": datetime.now(timezone.utc).isoformat(), "player": player,
                   "total_clips": len(results), "brands": registry, "whitespace": whitespace}, f, indent=2)

    md_path = out_dir / "brand-report.md"
    write_markdown(registry, whitespace, len(results), player, md_path)

    print(f"\n{'='*60}")
    print(f"BRAND INTELLIGENCE — {player} ({len(results)} clips)")
    print(f"{'='*60}")
    for b in registry[:5]:
        print(f"  {b['brand_name']:20s} {b['total_appearances']} appearances / {b['clips_seen_in']} clips")
    print(f"\nJSON:     {json_path}")
    print(f"Markdown: {md_path}")


if __name__ == "__main__":
    main()

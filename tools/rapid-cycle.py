#!/usr/bin/env python3
"""
Rapid Insight Cycle — Courtana / Pickle DaaS
Local pattern analysis on existing corpus. Zero API calls for quick_scan.
Usage: python tools/rapid-cycle.py --depth quick_scan --angle brand --data-slice all --output-format brief
"""

import os
import json
import argparse
import sys
from datetime import datetime
from pathlib import Path
from collections import Counter, defaultdict

try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).parent.parent / ".env")
except ImportError:
    pass

# ── Config ────────────────────────────────────────────────────────────────────
ROOT = Path(__file__).parent.parent
OUTPUT = ROOT / "output"

VALID_DEPTHS = ["quick_scan", "deep_dive"]
VALID_ANGLES = ["brand", "skill", "viral", "tactical", "coach"]
VALID_SLICES = ["all", "viral", "high_quality", "badged", "recent"]
VALID_FORMATS = ["brief", "json", "dashboard", "lovable-ready", "full"]

TIMESTAMP = datetime.now().strftime("%Y%m%d-%H%M")
DATE_LABEL = datetime.now().strftime("%Y-%m-%d %H:%M")

# Confidence caps based on V2 verification findings (LESSONS.md)
CONFIDENCE_CAPS = {
    "brand": 0.20,      # 20% agreement in V2
    "shot_count": 0.40, # 40% agreement
    "skill": 0.45,      # 45% agreement
    "dupr": 0.00,       # 0% agreement — don't trust
    "viral": 0.65,      # higher confidence
    "quality": 0.70,
}


# ── Data Loading ──────────────────────────────────────────────────────────────

def load_corpus() -> list[dict]:
    """Load enriched corpus, fall back to raw corpus."""
    for fname in ["enriched-corpus.json", "corpus-export.json"]:
        path = OUTPUT / fname
        if path.exists():
            try:
                data = json.loads(path.read_text())
                if isinstance(data, list):
                    print(f"[rapid] Loaded {len(data)} clips from {fname}")
                    return data
                elif isinstance(data, dict) and "clips" in data:
                    print(f"[rapid] Loaded {len(data['clips'])} clips from {fname}")
                    return data["clips"]
            except Exception as e:
                print(f"[rapid] Warning: could not load {fname}: {e}")
    print("[rapid] ERROR: No corpus found. Run the pipeline first.")
    sys.exit(1)


def apply_slice(clips: list, data_slice: str) -> list:
    if data_slice == "all":
        return clips
    elif data_slice == "viral":
        return [c for c in clips if c.get("viral", False)]
    elif data_slice == "high_quality":
        return [c for c in clips if c.get("quality", 0) >= 7]
    elif data_slice == "badged":
        return [c for c in clips if c.get("badges")]
    elif data_slice == "recent":
        return clips[-30:]  # last 30 in corpus order
    return clips


# ── Angle Analysis ────────────────────────────────────────────────────────────

def analyze_brand(clips: list) -> dict:
    """Brand detection patterns."""
    brand_counts = Counter()
    brand_co_occurrence = defaultdict(Counter)

    for clip in clips:
        brands = clip.get("brands", [])
        for b in brands:
            brand_counts[b.lower()] += 1
        for i, b1 in enumerate(brands):
            for b2 in brands[i+1:]:
                brand_co_occurrence[b1.lower()][b2.lower()] += 1

    total = len(clips)
    top_brands = brand_counts.most_common(10)

    findings = []
    for brand, count in top_brands[:5]:
        pct = round(count / total * 100, 1)
        findings.append(f"{brand.title()} appears in {pct}% of clips ({count}/{total})")

    pairs = []
    for b1, others in brand_co_occurrence.items():
        for b2, count in others.most_common(1):
            if count >= 2:
                pairs.append(f"{b1.title()} + {b2.title()} co-appear {count}x")

    return {
        "angle": "brand",
        "total_clips": total,
        "top_brands": top_brands[:10],
        "co_occurrence_pairs": pairs[:5],
        "key_findings": findings,
        "confidence_cap": CONFIDENCE_CAPS["brand"],
        "investor_note": f"Brand detection at ~{int(CONFIDENCE_CAPS['brand']*100)}% verified accuracy (V2 test). Use aggregate trends, not individual clip data.",
        "counter_argument": "Brand logos in pickleball are often small/occluded; detection may over-count branded paddle faces.",
    }


def analyze_skill(clips: list) -> dict:
    """Skill detection patterns."""
    skill_counts = Counter()
    skill_by_quality = defaultdict(list)

    for clip in clips:
        skills = clip.get("skills", [])
        quality = clip.get("quality", 5)
        for s in skills:
            skill_counts[s.lower()] += 1
            skill_by_quality[s.lower()].append(quality)

    total = len(clips)
    top_skills = skill_counts.most_common(10)

    skill_quality = {}
    for skill, qualities in skill_by_quality.items():
        skill_quality[skill] = round(sum(qualities) / len(qualities), 1)

    findings = []
    for skill, count in top_skills[:5]:
        pct = round(count / total * 100, 1)
        avg_q = skill_quality.get(skill, "?")
        findings.append(f"'{skill}' detected in {pct}% of clips, avg quality {avg_q}/10")

    return {
        "angle": "skill",
        "total_clips": total,
        "top_skills": top_skills[:10],
        "skill_quality_avg": {k: v for k, v in sorted(skill_quality.items(), key=lambda x: -x[1])[:8]},
        "key_findings": findings,
        "confidence_cap": CONFIDENCE_CAPS["skill"],
        "investor_note": f"Skill detection at ~{int(CONFIDENCE_CAPS['skill']*100)}% verified accuracy (V2 test). Coaching clip selection uses this.",
        "counter_argument": "Short clip windows may miss skill context; multi-shot sequences needed for reliable detection.",
    }


def analyze_viral(clips: list) -> dict:
    """Viral pattern analysis."""
    viral = [c for c in clips if c.get("viral", False)]
    non_viral = [c for c in clips if not c.get("viral", False)]

    total = len(clips)
    viral_count = len(viral)
    viral_pct = round(viral_count / total * 100, 1) if total else 0

    # What do viral clips have that others don't?
    viral_badges = Counter()
    viral_skills = Counter()
    viral_shots = []
    for c in viral:
        viral_badges.update(c.get("badges", []))
        viral_skills.update(c.get("skills", []))
        viral_shots.append(c.get("total_shots", 0))

    avg_shots_viral = round(sum(viral_shots) / len(viral_shots), 1) if viral_shots else 0
    non_viral_shots = [c.get("total_shots", 0) for c in non_viral]
    avg_shots_non = round(sum(non_viral_shots) / len(non_viral_shots), 1) if non_viral_shots else 0

    findings = [
        f"{viral_pct}% of clips flagged as viral ({viral_count}/{total})",
        f"Viral clips avg {avg_shots_viral} shots vs {avg_shots_non} for non-viral",
    ]
    if viral_badges:
        top_badge = viral_badges.most_common(1)[0]
        findings.append(f"Most common viral badge: '{top_badge[0]}' ({top_badge[1]}x)")
    if viral_skills:
        top_skill = viral_skills.most_common(1)[0]
        findings.append(f"Most viral skill signal: '{top_skill[0]}' ({top_skill[1]}x)")

    return {
        "angle": "viral",
        "total_clips": total,
        "viral_count": viral_count,
        "viral_pct": viral_pct,
        "viral_badge_patterns": viral_badges.most_common(5),
        "viral_skill_patterns": viral_skills.most_common(5),
        "avg_shots_viral": avg_shots_viral,
        "avg_shots_non_viral": avg_shots_non,
        "key_findings": findings,
        "confidence_cap": CONFIDENCE_CAPS["viral"],
        "investor_note": "Viral flag is model-predicted, not human-verified. Good for relative comparison, not absolute counts.",
    }


def analyze_tactical(clips: list) -> dict:
    """High-level pipeline health + data flywheel metrics."""
    total = len(clips)
    quality_dist = Counter()
    for c in clips:
        q = c.get("quality", 0)
        bucket = f"{(q // 2) * 2}-{(q // 2) * 2 + 1}"
        quality_dist[bucket] += 1

    has_brands = sum(1 for c in clips if c.get("brands"))
    has_skills = sum(1 for c in clips if c.get("skills"))
    has_badges = sum(1 for c in clips if c.get("badges"))
    viral_count = sum(1 for c in clips if c.get("viral"))
    high_quality = sum(1 for c in clips if c.get("quality", 0) >= 7)

    cost_per_clip = 0.0054
    total_cost = round(total * cost_per_clip, 4)

    findings = [
        f"Pipeline: {total} clips analyzed at ${cost_per_clip}/clip = ${total_cost} total",
        f"Data richness: {round(has_brands/total*100)}% have brand data, {round(has_skills/total*100)}% skill data, {round(has_badges/total*100)}% badges",
        f"Quality: {round(high_quality/total*100)}% are high-quality (≥7/10)",
        f"Viral pool: {viral_count} clips ({round(viral_count/total*100)}%) flagged viral",
        f"Scale projection: 400K clips = ${round(400000*cost_per_clip):,} (batch mode: ${round(400000*0.0027):,})",
    ]

    return {
        "angle": "tactical",
        "total_clips": total,
        "quality_distribution": dict(quality_dist),
        "coverage": {
            "brands": round(has_brands / total * 100, 1),
            "skills": round(has_skills / total * 100, 1),
            "badges": round(has_badges / total * 100, 1),
            "viral": round(viral_count / total * 100, 1),
            "high_quality": round(high_quality / total * 100, 1),
        },
        "cost_baseline": {
            "per_clip": cost_per_clip,
            "corpus_total": total_cost,
            "scale_400k": round(400000 * cost_per_clip, 2),
            "scale_400k_batch": round(400000 * 0.0027, 2),
        },
        "key_findings": findings,
        "investor_note": "Economics verified Apr 9. Lead with $0.005/clip and the verification story.",
    }


def analyze_coach(clips: list) -> dict:
    """Coaching clip identification and quality signals."""
    coaching_candidates = []
    for c in clips:
        skills = c.get("skills", [])
        quality = c.get("quality", 0)
        watchability = c.get("watchability", 0)
        if skills and quality >= 6:
            coaching_candidates.append({
                "uuid": c.get("uuid", ""),
                "skills": skills,
                "quality": quality,
                "watchability": watchability,
                "video_url": c.get("video_url", ""),
            })

    coaching_candidates.sort(key=lambda x: -(x["quality"] + x["watchability"]))

    skill_freq = Counter()
    for c in coaching_candidates:
        skill_freq.update(c.get("skills", []))

    findings = [
        f"{len(coaching_candidates)} clips qualify as coaching material (quality ≥6 + skill data)",
        f"Top coaching skill: '{skill_freq.most_common(1)[0][0] if skill_freq else 'n/a'}'",
        f"Best {min(3, len(coaching_candidates))} clips by quality: {[c['uuid'][:8] for c in coaching_candidates[:3]]}",
    ]

    return {
        "angle": "coach",
        "total_clips": len(clips),
        "coaching_candidates": len(coaching_candidates),
        "top_coaching_clips": coaching_candidates[:5],
        "skill_frequency": skill_freq.most_common(8),
        "key_findings": findings,
        "investor_note": "Coaching clips are the premium DaaS product tier. These are the clips venues pay most for.",
    }


ANGLE_HANDLERS = {
    "brand": analyze_brand,
    "skill": analyze_skill,
    "viral": analyze_viral,
    "tactical": analyze_tactical,
    "coach": analyze_coach,
}


# ── Output Formatters ─────────────────────────────────────────────────────────

def format_brief(result: dict, args) -> str:
    lines = [
        f"# Rapid Cycle Brief — {result['angle'].title()} / {args.depth}",
        f"_Generated {DATE_LABEL} | Slice: {args.data_slice} | Clips: {result.get('total_clips', '?')}_",
        "",
        "## Key Findings",
        "",
    ]
    for f in result.get("key_findings", []):
        lines.append(f"- {f}")

    lines += ["", "## Confidence Note", ""]
    cap = result.get("confidence_cap")
    if cap is not None:
        lines.append(f"⚠️ Verified accuracy cap: **{int(cap*100)}%** — use for trends, not absolutes")
    note = result.get("investor_note")
    if note:
        lines.append(f"\n> **Investor framing:** {note}")
    counter = result.get("counter_argument")
    if counter:
        lines.append(f"\n> **Bias check:** {counter}")

    return "\n".join(lines)


def format_dashboard(result: dict, args) -> str:
    angle = result.get("angle", "analysis")
    findings_html = "\n".join(
        f'<li>{f}</li>' for f in result.get("key_findings", [])
    )
    cap = result.get("confidence_cap", 0)
    note = result.get("investor_note", "")

    extra_html = ""
    if "top_brands" in result:
        rows = "\n".join(
            f'<tr><td>{b.title()}</td><td>{c}</td></tr>'
            for b, c in result["top_brands"][:8]
        )
        extra_html = f'<table><thead><tr><th>Brand</th><th>Clips</th></tr></thead><tbody>{rows}</tbody></table>'
    elif "coverage" in result:
        cov = result["coverage"]
        extra_html = "<ul>" + "".join(
            f'<li><strong>{k.title()}:</strong> {v}%</li>'
            for k, v in cov.items()
        ) + "</ul>"

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Rapid Cycle — {angle.title()}</title>
  <style>
    :root {{--bg:#0f1219;--surface:#161c27;--border:#1e2a3a;--accent:#00E676;--text:#e0e6f0;--muted:#6b7fa0;}}
    *{{box-sizing:border-box;margin:0;padding:0;}}
    body{{background:var(--bg);color:var(--text);font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;max-width:800px;margin:0 auto;padding:20px;}}
    h1{{color:var(--accent);font-size:1.4rem;margin-bottom:4px;}}
    .meta{{color:var(--muted);font-size:0.8rem;margin-bottom:20px;}}
    .card{{background:var(--surface);border:1px solid var(--border);border-radius:10px;padding:16px;margin-bottom:14px;}}
    .card h2{{font-size:1rem;margin-bottom:10px;color:var(--accent);}}
    ul{{list-style:none;}}
    li{{padding:5px 0;border-bottom:1px solid var(--border);font-size:0.88rem;}}
    li:last-child{{border-bottom:none;}}
    table{{width:100%;border-collapse:collapse;font-size:0.85rem;}}
    th,td{{padding:8px;text-align:left;border-bottom:1px solid var(--border);}}
    th{{color:var(--muted);font-weight:600;}}
    .cap-warning{{background:#1a1a2e;border-left:3px solid #ff6b35;padding:10px 14px;border-radius:4px;font-size:0.82rem;margin-top:8px;}}
    .investor-note{{background:#0d1f1a;border-left:3px solid var(--accent);padding:10px 14px;border-radius:4px;font-size:0.82rem;margin-top:8px;}}
  </style>
</head>
<body>
  <h1>🏓 Rapid Cycle — {angle.title()}</h1>
  <p class="meta">Generated {DATE_LABEL} · {result.get('total_clips','?')} clips · {args.data_slice} slice</p>

  <div class="card">
    <h2>Key Findings</h2>
    <ul>{findings_html}</ul>
  </div>

  {"<div class='card'><h2>Data</h2>" + extra_html + "</div>" if extra_html else ""}

  <div class="card">
    <h2>Confidence</h2>
    <div class="cap-warning">⚠️ Verified accuracy cap: <strong>{int(cap*100)}%</strong> — use for trends, not absolute claims</div>
    {f'<div class="investor-note">💡 {note}</div>' if note else ''}
  </div>
</body>
</html>"""


def format_lovable_ready(result: dict, args) -> str:
    """Generate a Lovable prompt snippet for this analysis."""
    findings = result.get("key_findings", [])
    angle = result.get("angle", "analysis")
    clip_count = result.get("total_clips", 0)

    return f"""# Lovable Prompt — {angle.title()} Intelligence Dashboard

Build a dark-theme intelligence card component for the Courtana DaaS platform.

Data source: {clip_count} analyzed clips via Pickle DaaS pipeline.

Key stats to display:
{chr(10).join(f"- {f}" for f in findings[:4])}

Design requirements:
- Background: #0f1219 (deep navy)
- Accent: #00E676 (green)
- Card style: rounded corners, subtle border (#1e2a3a)
- Mobile-first, expandable sections
- Include a confidence badge showing verified accuracy: {int(result.get("confidence_cap", 0)*100)}%

Investor framing:
{result.get("investor_note", "")}

Do NOT include booking features. Courtana is booking-agnostic.
"""


# ── Deep Dive ─────────────────────────────────────────────────────────────────

def run_deep_dive(clips: list, angle: str, args) -> dict:
    """Call Gemini API for deeper analysis on a targeted subset."""
    gemini_key = os.getenv("GEMINI_API_KEY")
    if not gemini_key:
        print("[rapid] No GEMINI_API_KEY — cannot run deep_dive. Falling back to quick_scan.")
        return ANGLE_HANDLERS[angle](clips)

    try:
        import urllib.request
        import urllib.error

        # Sample 10 clips to keep costs low
        sample = clips[:10]
        prompt = f"""You are analyzing pickleball video clip metadata for Courtana's DaaS platform.
Angle: {angle}
Clips (JSON): {json.dumps(sample, indent=2)[:4000]}

Provide:
1. 5 key findings as bullet points
2. One surprising pattern
3. One investment-grade insight about data moat value
4. One honest limitation or bias warning

Be concise and direct."""

        payload = json.dumps({
            "contents": [{"parts": [{"text": prompt}]}]
        }).encode()

        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={gemini_key}"
        req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"})

        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read())
            text = data["candidates"][0]["content"]["parts"][0]["text"]

        base = ANGLE_HANDLERS[angle](clips)
        base["deep_dive_response"] = text
        base["model_used"] = "gemini-2.0-flash"
        base["key_findings"].insert(0, "🤖 Deep dive (Gemini) insights below:")
        for line in text.split("\n")[:6]:
            if line.strip().startswith(("-", "*", "1", "2", "3", "4", "5")):
                base["key_findings"].append(line.strip("*- "))
        return base

    except Exception as e:
        print(f"[rapid] Gemini call failed: {e}. Falling back to quick_scan.")
        return ANGLE_HANDLERS[angle](clips)


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Rapid Insight Cycle")
    parser.add_argument("--depth", choices=VALID_DEPTHS, default="quick_scan")
    parser.add_argument("--angle", choices=VALID_ANGLES, default="tactical")
    parser.add_argument("--data-slice", choices=VALID_SLICES, default="all", dest="data_slice")
    parser.add_argument("--output-format", choices=VALID_FORMATS, default="brief", dest="output_format")
    args = parser.parse_args()

    print(f"[rapid] Starting {args.depth} | angle={args.angle} | slice={args.data_slice} | format={args.output_format}")

    clips = load_corpus()
    clips = apply_slice(clips, args.data_slice)
    print(f"[rapid] Working set: {len(clips)} clips after slice '{args.data_slice}'")

    if args.depth == "quick_scan":
        result = ANGLE_HANDLERS[args.angle](clips)
    else:
        result = run_deep_dive(clips, args.angle, args)

    # Save JSON result always
    out_dir = OUTPUT / "discovery"
    out_dir.mkdir(exist_ok=True)
    json_out = out_dir / f"rapid-{args.angle}-{args.depth}-{TIMESTAMP}.json"
    json_out.write_text(json.dumps(result, indent=2))
    print(f"[rapid] ✓ JSON → {json_out}")

    # Format and save primary output
    if args.output_format == "brief":
        content = format_brief(result, args)
        ext = ".md"
    elif args.output_format == "dashboard":
        content = format_dashboard(result, args)
        ext = ".html"
    elif args.output_format == "lovable-ready":
        content = format_lovable_ready(result, args)
        ext = ".md"
    elif args.output_format == "json":
        content = json.dumps(result, indent=2)
        ext = ".json"
    else:  # full
        content = format_brief(result, args) + "\n\n---\n\n```json\n" + json.dumps(result, indent=2) + "\n```"
        ext = ".md"

    out_path = out_dir / f"rapid-{args.angle}-{args.depth}-{TIMESTAMP}-output{ext}"
    out_path.write_text(content)
    print(f"[rapid] ✓ Output → {out_path}")

    if ext == ".html":
        os.system(f'open "{out_path}"')
        print(f"[rapid] Opened in browser.")
    elif ext == ".md":
        print("\n" + "─" * 60)
        print(content[:1500])
        if len(content) > 1500:
            print("... (truncated — full output in file)")

    print(f"\n[rapid] Done. Slice: {len(clips)} clips | Depth: {args.depth} | $0 API cost (quick_scan)")


if __name__ == "__main__":
    main()

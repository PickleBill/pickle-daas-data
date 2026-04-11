#!/usr/bin/env python3
"""
Overnight Prompt Generator — Courtana / Pickle DaaS
Reads current state and generates the highest-leverage next Claude Code session prompt.
Usage: python tools/generate-overnight-prompt.py
"""

import json
import os
from datetime import datetime
from pathlib import Path

try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).parent.parent / ".env")
except ImportError:
    pass

# ── Paths ─────────────────────────────────────────────────────────────────────
ROOT = Path(__file__).parent.parent
OUTPUT = ROOT / "output"
SESSION_LOGS = OUTPUT / "session-logs"
DISCOVERY = OUTPUT / "discovery"
BILL_OS = ROOT.parent / "BILL-OS"

DATE_LABEL = datetime.now().strftime("%Y-%m-%d")
TIMESTAMP = datetime.now().strftime("%Y%m%d-%H%M")


# ── State Readers ─────────────────────────────────────────────────────────────

def get_completed_angles() -> set:
    """Check which rapid-cycle angles have already been run."""
    completed = set()
    if not DISCOVERY.exists():
        return completed
    for f in DISCOVERY.glob("rapid-*-quick_scan-*.json"):
        parts = f.name.split("-")
        if len(parts) >= 2:
            completed.add(parts[1])  # the angle
    return completed


def get_corpus_stats() -> dict:
    corpus_path = OUTPUT / "enriched-corpus.json"
    if not corpus_path.exists():
        return {}
    try:
        clips = json.loads(corpus_path.read_text())
        total = len(clips)
        viral = sum(1 for c in clips if c.get("viral", False))
        high_q = sum(1 for c in clips if c.get("quality", 0) >= 7)
        return {"total": total, "viral": viral, "high_quality": high_q}
    except Exception:
        return {}


def get_latest_discovery_findings() -> str:
    """Pull the most recent discovery brief."""
    if not DISCOVERY.exists():
        return ""
    briefs = sorted(DISCOVERY.glob("rapid-*-output.md"), reverse=True)
    if not briefs:
        return ""
    try:
        text = briefs[0].read_text()
        return text[:800]
    except Exception:
        return ""


def get_recent_session_log() -> str:
    """Pull latest session log summary."""
    logs = sorted(SESSION_LOGS.glob("session-*.md"), reverse=True)
    if not logs:
        return "No prior session logs."
    try:
        return logs[0].read_text()[:1000]
    except Exception:
        return ""


def has_investor_materials() -> bool:
    return any(OUTPUT.glob("*investor*"))


def has_dupr_plan() -> bool:
    return (OUTPUT / "dupr-integration-plan.md").exists()


# ── Direction Picker ──────────────────────────────────────────────────────────

def pick_next_direction(completed_angles: set, corpus: dict, has_investor: bool) -> dict:
    """
    Pick the highest-leverage next direction based on what's least explored.
    Priority order based on deal stage and investor readiness.
    """
    all_angles = ["tactical", "brand", "viral", "skill", "coach"]
    unexplored = [a for a in all_angles if a not in completed_angles]

    # Court Kings is the biggest deal ($250-500K) — brand + coaching matter most
    if "coach" not in completed_angles:
        return {
            "angle": "coach",
            "depth": "quick_scan",
            "data_slice": "high_quality",
            "output_format": "dashboard",
            "rationale": "Court Kings demo prep — coaching clips are the premium DaaS tier. Kings Court Coach demo needs this data.",
        }
    if "brand" not in completed_angles:
        return {
            "angle": "brand",
            "depth": "quick_scan",
            "data_slice": "all",
            "output_format": "dashboard",
            "rationale": "Brand intelligence = DaaS data moat story for investors. Joola/Selkirk co-occurrence patterns.",
        }
    if "viral" not in completed_angles:
        return {
            "angle": "viral",
            "depth": "quick_scan",
            "data_slice": "all",
            "output_format": "lovable-ready",
            "rationale": "Viral clip patterns = social proof engine for venues. Lovable-ready output for Peak/Concord demos.",
        }
    if "skill" not in completed_angles:
        return {
            "angle": "skill",
            "depth": "quick_scan",
            "data_slice": "high_quality",
            "output_format": "brief",
            "rationale": "Skill detection is the coaching product. High-quality clips only to maximize signal.",
        }

    # If all quick_scans done, escalate one to deep_dive
    if corpus.get("total", 0) > 0 and not has_investor:
        return {
            "angle": "tactical",
            "depth": "quick_scan",
            "data_slice": "all",
            "output_format": "dashboard",
            "rationale": "Build investor-grade tactical dashboard with $0.005/clip cost story.",
        }

    # Default: re-run tactical with fresh data
    return {
        "angle": "tactical",
        "depth": "quick_scan",
        "data_slice": "all",
        "output_format": "full",
        "rationale": "Refresh tactical overview — check for new corpus data or pipeline additions.",
    }


# ── Prompt Builder ────────────────────────────────────────────────────────────

def build_prompt(direction: dict, corpus: dict, latest_findings: str, session_log: str) -> str:
    angle = direction["angle"]
    depth = direction["depth"]
    data_slice = direction["data_slice"]
    output_format = direction["output_format"]
    rationale = direction["rationale"]

    findings_section = ""
    if latest_findings:
        findings_section = f"""
## What the Last Session Found

```
{latest_findings[:600]}
```
"""

    session_section = ""
    if session_log and "No prior" not in session_log:
        session_section = f"""
## Last Session Summary

```
{session_log[:400]}
```
"""

    return f"""# Overnight Claude Code Session — {DATE_LABEL}
# Direction: {angle.title()} Intelligence
# Rationale: {rationale}

---

## IDENTITY

You are Bill Bricker's AI Chief of Staff. Bill is the founder/CEO of Courtana — AI-powered
smart court tech for pickleball venues. Raising $1.3M seed. Three venue deals in close.

Critical rules:
- NEVER use api.courtana.com — base URL is https://courtana.com
- ALWAYS set Accept: application/json on API calls
- NEVER use the `next` pagination field — build URLs manually (?page=N&page_size=100)
- CDN assets (cdn.courtana.com) are public — link directly
- Show outputs: run `open [file.html]` after every HTML build
- Automate don't instruct
- Keep scripts under 300 lines

---

## CORPUS STATUS

- Clips analyzed: {corpus.get('total', 0)}
- Viral clips: {corpus.get('viral', 0)}
- High quality (≥7): {corpus.get('high_quality', 0)}
- Main file: output/enriched-corpus.json
- Cost baseline: $0.005/clip (Gemini 2.5 Flash, verified Apr 9)

{findings_section}
{session_section}

---

## TONIGHT'S TASK

Run:
```bash
cd PICKLE-DAAS
python tools/rapid-cycle.py --depth {depth} --angle {angle} --data-slice {data_slice} --output-format {output_format}
```

Then run the morning brief:
```bash
python tools/morning-brief-generator.py
```

Then run the session closer:
```bash
python tools/session-closer.py
```

---

## WHAT TO BUILD (if rapid-cycle output inspires it)

Based on the {angle} angle results, consider building ONE of:
1. A Lovable-ready dashboard prompt for the {angle} intelligence view
2. An investor proof point adding the {angle} data to output/pickle-daas-investor-proof-points.md
3. A venue demo snippet showing what {angle} data looks like for a Court Kings pitch

Build whichever adds the most deal value. Don't build all three.

---

## WHAT NOT TO DO THIS SESSION

- Don't re-fetch the corpus from the Courtana API (we have 96 clips, it's enough)
- Don't build booking or payment features (Courtana is booking-agnostic)
- Don't run deep_dive unless quick_scan shows something worth investigating
- Don't create more than 3 new files without checking if they're needed
- Don't amend existing commits

---

## WHEN DONE

1. Run `python tools/session-closer.py`
2. Open all HTML outputs immediately after building
3. Update output/next-overnight-prompt.md with the NEXT direction
4. Print: "Session complete. Morning brief ready at output/briefs/morning-brief-{DATE_LABEL}.html"

_Generated by tools/generate-overnight-prompt.py — {datetime.now().strftime('%Y-%m-%d %H:%M')}_
"""


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    print(f"[overnight] Generating next session prompt for {DATE_LABEL}...")

    completed_angles = get_completed_angles()
    print(f"[overnight] Completed angles: {completed_angles or 'none yet'}")

    corpus = get_corpus_stats()
    print(f"[overnight] Corpus: {corpus.get('total', 0)} clips")

    latest_findings = get_latest_discovery_findings()
    session_log = get_recent_session_log()
    has_investor = has_investor_materials()

    direction = pick_next_direction(completed_angles, corpus, has_investor)
    print(f"[overnight] Chosen direction: {direction['angle']} ({direction['rationale'][:60]}...)")

    prompt = build_prompt(direction, corpus, latest_findings, session_log)

    out_path = OUTPUT / "next-overnight-prompt.md"
    out_path.write_text(prompt)

    print(f"\n[overnight] ✓ Prompt saved → {out_path}")
    print(f"\n{'─'*60}")
    print(f"Your next prompt is ready.")
    print(f"Open a new Claude Code chat and paste the contents of:")
    print(f"  output/next-overnight-prompt.md")
    print(f"{'─'*60}")
    print(f"\nDirection: {direction['angle'].upper()}")
    print(f"Rationale: {direction['rationale']}")


if __name__ == "__main__":
    main()

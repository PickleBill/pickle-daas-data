#!/usr/bin/env python3
"""
Session Closer — Courtana / Pickle DaaS
Captures what happened in a Claude Code session. Run at end of every session.
Usage: python tools/session-closer.py
"""

import os
import json
import subprocess
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
SESSION_LOGS.mkdir(parents=True, exist_ok=True)

MANIFEST_PATH = OUTPUT / ".file-manifest.json"
TIMESTAMP = datetime.now().strftime("%Y%m%d-%H%M")
DATE_LABEL = datetime.now().strftime("%Y-%m-%d %H:%M")


# ── Manifest helpers ──────────────────────────────────────────────────────────

def load_manifest() -> dict:
    if MANIFEST_PATH.exists():
        try:
            return json.loads(MANIFEST_PATH.read_text())
        except Exception:
            return {}
    return {}


def save_manifest(manifest: dict):
    MANIFEST_PATH.write_text(json.dumps(manifest, indent=2))


def scan_output_files() -> dict:
    """Return {relative_path: mtime} for all files in output/."""
    result = {}
    for p in OUTPUT.rglob("*"):
        if p.is_file() and not p.name.startswith("."):
            try:
                rel = str(p.relative_to(OUTPUT))
                result[rel] = p.stat().st_mtime
            except OSError:
                pass
    return result


def diff_manifest(old: dict, new: dict) -> tuple[list, list]:
    """Returns (new_files, modified_files)."""
    new_files = [k for k in new if k not in old]
    modified = [
        k for k in new
        if k in old and new[k] != old[k]
        and not k.startswith("session-logs/")
        and not k.startswith("briefs/")
    ]
    return sorted(new_files), sorted(modified)


# ── Git helpers ───────────────────────────────────────────────────────────────

def get_git_log(n: int = 5) -> str:
    try:
        result = subprocess.run(
            ["git", "log", f"--oneline", f"-{n}"],
            cwd=ROOT,
            capture_output=True, text=True, timeout=10
        )
        return result.stdout.strip() or "(no commits)"
    except Exception:
        return "(git not available)"


def get_git_status() -> str:
    try:
        result = subprocess.run(
            ["git", "status", "--short"],
            cwd=ROOT,
            capture_output=True, text=True, timeout=10
        )
        return result.stdout.strip() or "(clean)"
    except Exception:
        return "(git not available)"


# ── Pushed to gh-pages ───────────────────────────────────────────────────────

def detect_gh_pages_files(new_files: list) -> list:
    """Heuristic: HTML files in output/ are candidates for gh-pages."""
    return [f for f in new_files if f.endswith(".html")]


# ── Next session prompt ──────────────────────────────────────────────────────

def generate_next_prompt(new_files: list, modified_files: list) -> str:
    has_corpus = any("corpus" in f for f in new_files + modified_files)
    has_dashboards = any(".html" in f for f in new_files)
    has_analysis = any("analysis" in f or "discovery" in f for f in new_files)

    if has_analysis:
        direction = "brand-intelligence deep-dive"
        angle = "brand"
    elif has_dashboards:
        direction = "DUPR integration or player profile expansion"
        angle = "skill"
    else:
        direction = "quick_scan on latest corpus data"
        angle = "tactical"

    return f"""You are Bill's AI Chief of Staff running an overnight cycle.

Context:
- Last session produced {len(new_files)} new files and modified {len(modified_files)} files
- Corpus: output/enriched-corpus.json (96 clips analyzed)
- Available tools: tools/rapid-cycle.py, tools/morning-brief-generator.py

Tonight's direction: {direction}

Run:
  python tools/rapid-cycle.py --depth quick_scan --angle {angle} --data-slice all --output-format brief

Then run:
  python tools/morning-brief-generator.py

Report blockers. Open all HTML outputs immediately after building them.
"""


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    print(f"[closer] Session closer running — {DATE_LABEL}")

    old_manifest = load_manifest()
    new_manifest = scan_output_files()
    new_files, modified_files = diff_manifest(old_manifest, new_manifest)

    git_log = get_git_log()
    git_status = get_git_status()
    gh_pages = detect_gh_pages_files(new_files)
    next_prompt = generate_next_prompt(new_files, modified_files)

    # Identify blockers from new MD files
    blockers = []
    for f in new_files:
        if f.endswith(".md"):
            try:
                content = (OUTPUT / f).read_text()
                for line in content.split("\n"):
                    if any(w in line.lower() for w in ["blocked", "needs bill", "todo", "decision needed"]):
                        blockers.append(f"  [{f}] {line.strip()[:80]}")
            except Exception:
                pass

    # Build log
    log_path = SESSION_LOGS / f"session-{TIMESTAMP}.md"
    next_prompt_path = OUTPUT / "next-overnight-prompt.md"

    lines = [
        f"# Session Log — {DATE_LABEL}",
        "",
        "## What Was Built",
        "",
    ]
    if new_files:
        for f in new_files[:20]:
            lines.append(f"- `{f}` (new)")
    else:
        lines.append("- No new files this session")

    if modified_files:
        lines.append("")
        for f in modified_files[:10]:
            lines.append(f"- `{f}` (modified)")

    lines += [
        "",
        "## Git Status",
        "",
        f"```\n{git_log}\n```",
        "",
        "## Pushed to gh-pages",
        "",
    ]
    if gh_pages:
        for f in gh_pages:
            lines.append(f"- `{f}`")
    else:
        lines.append("- Nothing pushed this session")

    lines += [
        "",
        "## Blockers / Needs Bill",
        "",
    ]
    if blockers:
        lines.extend(blockers[:5])
    else:
        lines.append("- None detected")

    lines += [
        "",
        "## Suggested Next Session Prompt",
        "",
        "```",
        next_prompt,
        "```",
        "",
        f"_Closed {DATE_LABEL}_",
    ]

    log_content = "\n".join(lines)
    log_path.write_text(log_content)
    next_prompt_path.write_text(next_prompt)

    # Update manifest
    save_manifest(new_manifest)

    print(f"[closer] ✓ Session log  → {log_path}")
    print(f"[closer] ✓ Next prompt  → {next_prompt_path}")
    print(f"[closer] New files: {len(new_files)}, Modified: {len(modified_files)}")
    print(f"\n[closer] Your next prompt is ready.")
    print(f"         Open a new Claude Code chat and paste: output/next-overnight-prompt.md")


if __name__ == "__main__":
    main()

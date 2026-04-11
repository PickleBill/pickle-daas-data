#!/usr/bin/env python3
"""Session Closer. Run at end of every session: python tools/session-closer.py"""
import json, subprocess
from datetime import datetime
from pathlib import Path
try:
    from dotenv import load_dotenv; load_dotenv(Path(__file__).parent.parent / ".env")
except ImportError: pass

ROOT = Path(__file__).parent.parent
OUTPUT = ROOT / "output"
SESSION_LOGS = OUTPUT / "session-logs"
SESSION_LOGS.mkdir(parents=True, exist_ok=True)
MANIFEST = OUTPUT / ".file-manifest.json"
TIMESTAMP = datetime.now().strftime("%Y%m%d-%H%M")
NOW = datetime.now().strftime("%Y-%m-%d %H:%M")

def load_manifest():
    if MANIFEST.exists():
        try: return json.loads(MANIFEST.read_text())
        except: pass
    return {}

def scan():
    r = {}
    for p in OUTPUT.rglob("*"):
        if p.is_file() and not p.name.startswith("."):
            try: r[str(p.relative_to(OUTPUT))] = p.stat().st_mtime
            except: pass
    return r

def git_log():
    try:
        r = subprocess.run(["git","log","--oneline","-5"], cwd=ROOT, capture_output=True, text=True, timeout=10)
        return r.stdout.strip() or "(no commits)"
    except: return "(git not available)"

def main():
    old = load_manifest(); new = scan()
    new_files = sorted(k for k in new if k not in old)
    modified = sorted(k for k in new if k in old and new[k] != old[k]
                      and not k.startswith("session-logs/") and not k.startswith("briefs/"))
    angle = "coach" if any("coach" in f for f in new_files) else "brand" if any("brand" in f for f in new_files) else "tactical"
    next_p = f"Run: python tools/rapid-cycle.py --depth quick_scan --angle {angle} --data-slice all --output-format dashboard\nThen: python tools/morning-brief-generator.py\nThen: python tools/session-closer.py"
    log = SESSION_LOGS / f"session-{TIMESTAMP}.md"
    lines = [f"# Session Log — {NOW}", "", "## New Files", ""] + [f"- `{f}`" for f in new_files[:20]] + (["- None"] if not new_files else [])
    if modified: lines += ["", "## Modified", ""] + [f"- `{f}`" for f in modified[:10]]
    lines += ["", "## Git", "", f"```\n{git_log()}\n```", "", "## Next Prompt", "", f"```\n{next_p}\n```", "", f"_Closed {NOW}_"]
    log.write_text("\n".join(lines))
    (OUTPUT / "next-overnight-prompt.md").write_text(next_p)
    MANIFEST.write_text(json.dumps(new, indent=2))
    print(f"[closer] ✓ {log}")
    print(f"[closer] New: {len(new_files)} | Modified: {len(modified)}")
    print(f"\nNext prompt ready: output/next-overnight-prompt.md")

if __name__ == "__main__": main()

#!/usr/bin/env python3
"""
Morning Brief Generator — Courtana / Pickle DaaS
Reads output/ and session logs, produces a short daily brief in MD + HTML.
Run: python tools/morning-brief-generator.py
"""

import os
import json
import sys
from datetime import datetime, timedelta
from pathlib import Path

try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).parent.parent / ".env")
except ImportError:
    pass

# ── Paths ───────────────────────────────────────────────────────────────────
ROOT = Path(__file__).parent.parent
OUTPUT = ROOT / "output"
BRIEFS = OUTPUT / "briefs"
SESSION_LOGS = OUTPUT / "session-logs"
BILL_OS = ROOT.parent / "BILL-OS"
BRIEFS.mkdir(parents=True, exist_ok=True)

TODAY = datetime.now().strftime("%Y-%m-%d")
DATE_LABEL = datetime.now().strftime("%A, %B %-d, %Y")
YESTERDAY = (datetime.now() - timedelta(days=1))


# ── Helpers ──────────────────────────────────────────────────────────────────

def new_files_since_yesterday(directory: Path) -> list[Path]:
    """Return files modified in the last 24h."""
    cutoff = YESTERDAY.timestamp()
    results = []
    for p in directory.rglob("*"):
        if p.is_file() and not p.name.startswith("."):
            try:
                if p.stat().st_mtime > cutoff:
                    results.append(p)
            except OSError:
                pass
    return sorted(results, key=lambda x: x.stat().st_mtime, reverse=True)


def read_latest_session_log() -> dict:
    """Return contents of the most recent session log."""
    logs = sorted(SESSION_LOGS.glob("session-*.md"), reverse=True)
    if not logs:
        return {}
    text = logs[0].read_text()
    return {"path": str(logs[0]), "content": text[:2000]}


def scan_corpus() -> dict:
    """Quick stats from enriched corpus."""
    corpus_path = OUTPUT / "enriched-corpus.json"
    if not corpus_path.exists():
        return {}
    try:
        clips = json.loads(corpus_path.read_text())
        total = len(clips)
        viral = sum(1 for c in clips if c.get("viral", False))
        badges = sum(len(c.get("badges", [])) for c in clips)
        brands = set()
        for c in clips:
            brands.update(c.get("brands", []))
        return {
            "total_clips": total,
            "viral_clips": viral,
            "total_badges": badges,
            "brands_detected": sorted(brands)[:8],
        }
    except Exception:
        return {}


def read_bill_os_hit_list() -> str:
    """Pull the top 3 items from BILL-OS hit list."""
    os_path = BILL_OS / "BILL-OS.md"
    if not os_path.exists():
        return ""
    text = os_path.read_text()
    # Find the hit list table
    start = text.find("PRIORITIZED HIT LIST")
    if start == -1:
        return ""
    chunk = text[start:start + 1500]
    lines = chunk.split("\n")
    items = []
    for line in lines:
        if line.startswith("|") and "|" in line[1:]:
            cols = [c.strip() for c in line.split("|") if c.strip()]
            if cols and cols[0].isdigit() and int(cols[0]) <= 3:
                action = cols[1] if len(cols) > 1 else ""
                # Clean markdown bold
                action = action.replace("**", "")
                items.append(f"{cols[0]}. {action}")
    return "\n".join(items[:3])


def check_blocked_items() -> list[str]:
    """Scan session logs and BILL-OS for blocked/needs-attention items."""
    blocked = []

    # Check most recent session log
    latest = read_latest_session_log()
    if latest.get("content"):
        content = latest["content"]
        for line in content.split("\n"):
            if any(word in line.lower() for word in ["blocked", "needs bill", "waiting on bill", "decision needed"]):
                blocked.append(line.strip("# -").strip())

    # Check SPEND-LOG for budget flags
    spend_log = OUTPUT / "SPEND-LOG.md"
    if spend_log.exists():
        text = spend_log.read_text()[-500:]
        for line in text.split("\n"):
            if "⚠" in line or "warning" in line.lower():
                blocked.append(line.strip())

    return blocked[:3]


def build_new_outputs_list() -> list[str]:
    """List notable new files built overnight."""
    new_files = new_files_since_yesterday(OUTPUT)
    notable_extensions = {".html", ".json", ".md", ".csv"}
    skip_dirs = {"briefs", "session-logs", ".git"}

    results = []
    for f in new_files[:15]:
        # Skip hidden, skip brief/log dirs
        parts = set(f.parts)
        if any(s in str(f) for s in skip_dirs):
            continue
        if f.suffix in notable_extensions:
            rel = f.relative_to(OUTPUT)
            results.append(str(rel))

    return results[:8]


# ── Generators ────────────────────────────────────────────────────────────────

def generate_brief_md(corpus: dict, hit_list: str, new_outputs: list, blocked: list) -> str:
    """Build the markdown brief."""
    lines = [
        f"# Morning Brief — {DATE_LABEL}",
        "",
        "---",
        "",
        "## 3 Things to Do Today",
        "",
    ]

    if hit_list:
        for item in hit_list.split("\n"):
            lines.append(f"- {item}")
    else:
        lines.append("- Check BILL-OS.md for today's hit list")

    lines += [
        "",
        "---",
        "",
        "## Threads Don't Let Die",
        "",
        "- **Court Kings:** Rich back from vacation ~Apr 24 — prep Kings Court Coach demo",
        "- **Peak Pickleball:** Hardware ship + install plan needed (grand opening May 9)",
        "- **Concord:** Chris W. back week of Apr 14 — address CourtReserve objection",
        "- **Pickle DaaS:** Discovery Engine V2 verified — investor deck needs cost story ($0.005/clip)",
        "",
        "---",
        "",
        "## What Your AI Built Overnight",
        "",
    ]

    if new_outputs:
        for f in new_outputs:
            lines.append(f"- `output/{f}`")
    else:
        lines.append("- No new files since yesterday")

    if corpus:
        lines += [
            "",
            f"**Corpus stats:** {corpus.get('total_clips', 0)} clips analyzed | "
            f"{corpus.get('viral_clips', 0)} viral | "
            f"{corpus.get('total_badges', 0)} badges | "
            f"Brands: {', '.join(corpus.get('brands_detected', [])[:5])}",
        ]

    lines += [
        "",
        "---",
        "",
        "## One Decision Needed",
        "",
    ]

    if blocked:
        lines.append(f"→ **{blocked[0]}**")
        for b in blocked[1:]:
            lines.append(f"→ {b}")
    else:
        lines.append("→ **Next overnight run direction:** Brand intelligence deep-dive vs. DUPR integration plan?")

    lines += [
        "",
        "---",
        "",
        f"_Generated {datetime.now().strftime('%Y-%m-%d %H:%M')} · Pickle DaaS AI Chief of Staff_",
    ]

    return "\n".join(lines)


def generate_brief_html(md_content: str, corpus: dict, new_outputs: list) -> str:
    """Build a dark-theme mobile-first HTML brief."""
    hit_list_items = ""
    threads_items = ""
    outputs_items = ""
    decision_item = ""

    # Parse sections from MD
    sections = md_content.split("---")
    for section in sections:
        if "3 Things to Do Today" in section:
            for line in section.split("\n"):
                if line.startswith("- "):
                    hit_list_items += f"<li>{line[2:]}</li>\n"
        elif "Threads Don't Let Die" in section:
            for line in section.split("\n"):
                if line.startswith("- "):
                    threads_items += f"<li>{line[2:]}</li>\n"
        elif "What Your AI Built" in section:
            for line in section.split("\n"):
                if line.startswith("- `"):
                    fname = line.strip("- `").strip("`")
                    outputs_items += f'<li><code>{fname}</code></li>\n'
                elif line.startswith("- ") and line != "- No new files since yesterday":
                    outputs_items += f'<li>{line[2:]}</li>\n'
        elif "One Decision Needed" in section:
            for line in section.split("\n"):
                if line.startswith("→"):
                    decision_item += f'<p class="decision">{line[1:].strip()}</p>\n'

    corpus_badge = ""
    if corpus:
        corpus_badge = f"""
        <div class="corpus-badge">
          <span>📊 {corpus.get('total_clips',0)} clips</span>
          <span>🔥 {corpus.get('viral_clips',0)} viral</span>
          <span>🏆 {corpus.get('total_badges',0)} badges</span>
        </div>"""

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Morning Brief — {DATE_LABEL}</title>
  <style>
    :root {{
      --bg: #0f1219;
      --surface: #161c27;
      --border: #1e2a3a;
      --accent: #00E676;
      --accent2: #00B0FF;
      --text: #e0e6f0;
      --muted: #6b7fa0;
    }}
    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{
      background: var(--bg);
      color: var(--text);
      font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
      max-width: 640px;
      margin: 0 auto;
      padding: 16px;
      line-height: 1.6;
    }}
    header {{
      border-bottom: 1px solid var(--accent);
      padding-bottom: 12px;
      margin-bottom: 20px;
    }}
    header h1 {{ font-size: 1.1rem; color: var(--accent); font-weight: 700; }}
    header p {{ font-size: 0.8rem; color: var(--muted); margin-top: 2px; }}
    .section {{
      background: var(--surface);
      border: 1px solid var(--border);
      border-radius: 10px;
      margin-bottom: 14px;
      overflow: hidden;
    }}
    .section-header {{
      padding: 12px 16px;
      cursor: pointer;
      display: flex;
      justify-content: space-between;
      align-items: center;
      font-weight: 600;
      font-size: 0.9rem;
    }}
    .section-header:hover {{ background: var(--border); }}
    .section-header .icon {{ color: var(--accent); margin-right: 8px; }}
    .section-header .arrow {{ color: var(--muted); transition: transform 0.2s; }}
    .section-body {{ padding: 12px 16px; border-top: 1px solid var(--border); }}
    .section-body.collapsed {{ display: none; }}
    ul {{ list-style: none; padding: 0; }}
    ul li {{
      padding: 6px 0;
      border-bottom: 1px solid var(--border);
      font-size: 0.88rem;
    }}
    ul li:last-child {{ border-bottom: none; }}
    code {{
      background: #1a2535;
      padding: 2px 6px;
      border-radius: 4px;
      font-size: 0.8rem;
      color: var(--accent2);
    }}
    .decision {{
      font-size: 1rem;
      font-weight: 600;
      color: var(--accent);
      padding: 8px 0;
    }}
    .corpus-badge {{
      display: flex;
      gap: 12px;
      flex-wrap: wrap;
      font-size: 0.8rem;
      color: var(--muted);
      margin-top: 10px;
      padding-top: 10px;
      border-top: 1px solid var(--border);
    }}
    .corpus-badge span {{ color: var(--text); }}
    footer {{
      text-align: center;
      font-size: 0.75rem;
      color: var(--muted);
      margin-top: 20px;
      padding-top: 12px;
      border-top: 1px solid var(--border);
    }}
  </style>
</head>
<body>
  <header>
    <h1>🏓 Morning Brief</h1>
    <p>{DATE_LABEL}</p>
  </header>

  <div class="section">
    <div class="section-header" onclick="toggle(this)">
      <span><span class="icon">🎯</span>3 Things to Do Today</span>
      <span class="arrow">▼</span>
    </div>
    <div class="section-body">
      <ul>{hit_list_items or '<li>Check BILL-OS.md hit list</li>'}</ul>
    </div>
  </div>

  <div class="section">
    <div class="section-header" onclick="toggle(this)">
      <span><span class="icon">🔥</span>Threads Don't Let Die</span>
      <span class="arrow">▼</span>
    </div>
    <div class="section-body">
      <ul>{threads_items or '<li>All threads current</li>'}</ul>
    </div>
  </div>

  <div class="section">
    <div class="section-header" onclick="toggle(this)">
      <span><span class="icon">🤖</span>What Your AI Built Overnight</span>
      <span class="arrow">▼</span>
    </div>
    <div class="section-body">
      <ul>{outputs_items or '<li>No new files since yesterday</li>'}</ul>
      {corpus_badge}
    </div>
  </div>

  <div class="section">
    <div class="section-header" onclick="toggle(this)">
      <span><span class="icon">⚡</span>One Decision Needed</span>
      <span class="arrow">▼</span>
    </div>
    <div class="section-body">
      {decision_item or '<p class="decision">→ Check session logs for blockers</p>'}
    </div>
  </div>

  <footer>Pickle DaaS AI Chief of Staff · {datetime.now().strftime("%H:%M")}</footer>

  <script>
    function toggle(header) {{
      const body = header.nextElementSibling;
      const arrow = header.querySelector('.arrow');
      body.classList.toggle('collapsed');
      arrow.textContent = body.classList.contains('collapsed') ? '▶' : '▼';
    }}
  </script>
</body>
</html>"""


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    print(f"[brief] Generating morning brief for {TODAY}...")

    md_out = BRIEFS / f"morning-brief-{TODAY}.md"
    html_out = BRIEFS / f"morning-brief-{TODAY}.html"

    if md_out.exists():
        print(f"[brief] Brief already exists: {md_out}")
        print(f"[brief] Opening existing brief...")
        os.system(f'open "{html_out}"')
        return

    print("[brief] Scanning corpus...")
    corpus = scan_corpus()

    print("[brief] Reading hit list...")
    hit_list = read_bill_os_hit_list()

    print("[brief] Scanning new outputs...")
    new_outputs = build_new_outputs_list()

    print("[brief] Checking blocked items...")
    blocked = check_blocked_items()

    md_content = generate_brief_md(corpus, hit_list, new_outputs, blocked)
    html_content = generate_brief_html(md_content, corpus, new_outputs)

    md_out.write_text(md_content)
    html_out.write_text(html_content)

    print(f"[brief] ✓ MD   → {md_out}")
    print(f"[brief] ✓ HTML → {html_out}")
    print(f"[brief] Opening brief in browser...")
    os.system(f'open "{html_out}"')


if __name__ == "__main__":
    main()

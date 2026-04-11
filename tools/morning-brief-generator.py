#!/usr/bin/env python3
"""Morning Brief Generator. Run: python tools/morning-brief-generator.py"""
import os, json
from datetime import datetime, timedelta
from pathlib import Path
try:
    from dotenv import load_dotenv; load_dotenv(Path(__file__).parent.parent / ".env")
except ImportError: pass

ROOT = Path(__file__).parent.parent
OUTPUT = ROOT / "output"
BRIEFS = OUTPUT / "briefs"
BILL_OS = ROOT.parent / "BILL-OS"
BRIEFS.mkdir(parents=True, exist_ok=True)
TODAY = datetime.now().strftime("%Y-%m-%d")
DATE_LABEL = datetime.now().strftime("%A, %B %-d, %Y")
YESTERDAY = datetime.now() - timedelta(days=1)

def scan_corpus():
    p = OUTPUT / "enriched-corpus.json"
    if not p.exists(): return {}
    try:
        clips = json.loads(p.read_text())
        brands = set()
        for c in clips: brands.update(c.get("brands", []))
        viral_high = sum(1 for c in clips if isinstance(c.get("viral"), (int,float)) and c.get("viral",0) >= 7)
        return {"total": len(clips), "viral_high": viral_high, "brands": sorted(brands)[:6]}
    except: return {}

def read_hit_list():
    p = BILL_OS / "BILL-OS.md"
    if not p.exists(): return []
    text = p.read_text(); start = text.find("PRIORITIZED HIT LIST")
    if start == -1: return []
    items = []
    for line in text[start:start+1500].split("\n"):
        if line.startswith("|"):
            cols = [c.strip() for c in line.split("|") if c.strip()]
            if cols and cols[0].isdigit() and int(cols[0]) <= 3:
                items.append(f"{cols[0]}. {cols[1].replace('**','') if len(cols)>1 else ''}")
    return items[:3]

def new_outputs():
    cutoff = YESTERDAY.timestamp()
    skip = {"briefs","session-logs"}
    results = []
    for p in OUTPUT.rglob("*"):
        if p.is_file() and not p.name.startswith(".") and p.suffix in {".html",".json",".md"}:
            try:
                if p.stat().st_mtime > cutoff and not any(s in str(p) for s in skip):
                    results.append(str(p.relative_to(OUTPUT)))
            except: pass
    return results[:8]

def main():
    md_out = BRIEFS / f"morning-brief-{TODAY}.md"
    html_out = BRIEFS / f"morning-brief-{TODAY}.html"
    if md_out.exists():
        print(f"[brief] Already exists — opening."); os.system(f'open "{html_out}"'); return
    corpus = scan_corpus(); hit = read_hit_list(); outputs = new_outputs()
    threads = [
        "<strong>Court Kings:</strong> Rich back ~Apr 24 — prep Kings Court Coach demo",
        "<strong>Peak Pickleball:</strong> Hardware + install plan (opens May 9)",
        "<strong>Concord:</strong> Chris W. back Apr 14 — CourtReserve objection",
        "<strong>Pickle DaaS:</strong> $0.005/clip verified — weave into investor deck",
    ]
    hit_li = "".join(f"<li>{i}</li>" for i in (hit or ["Check BILL-OS.md hit list"]))
    thread_li = "".join(f"<li>{t}</li>" for t in threads)
    out_li = "".join(f"<li><code>{f}</code></li>" for f in outputs) or "<li>No new files since yesterday</li>"
    corpus_txt = f'<div class="corpus"><span>📊 {corpus.get("total",0)} clips</span><span>🔥 {corpus.get("viral_high",0)} high-viral</span><span>🏷 Brands: {", ".join(corpus.get("brands",[])[:4])}</span></div>' if corpus else ""
    html = f"""<!DOCTYPE html><html><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>Morning Brief</title><style>
:root{{--bg:#0f1219;--sur:#161c27;--bdr:#1e2a3a;--acc:#00E676;--txt:#e0e6f0;--mut:#6b7fa0;}}
*{{box-sizing:border-box;margin:0;padding:0;}}
body{{background:var(--bg);color:var(--txt);font-family:-apple-system,sans-serif;max-width:600px;margin:0 auto;padding:16px;line-height:1.6;}}
header{{border-bottom:2px solid var(--acc);padding-bottom:10px;margin-bottom:16px;}}
h1{{font-size:1.1rem;color:var(--acc);}} p.sub{{font-size:.78rem;color:var(--mut);}}
.card{{background:var(--sur);border:1px solid var(--bdr);border-radius:10px;margin-bottom:12px;overflow:hidden;}}
.ch{{padding:12px 16px;cursor:pointer;display:flex;justify-content:space-between;font-weight:600;font-size:.88rem;}}
.ch:hover{{background:var(--bdr);}} .cb{{padding:12px 16px;border-top:1px solid var(--bdr);}}
ul{{list-style:none;}} li{{padding:5px 0;border-bottom:1px solid var(--bdr);font-size:.84rem;}} li:last-child{{border-bottom:none;}}
code{{background:#1a2535;padding:2px 5px;border-radius:4px;font-size:.78rem;color:#00B0FF;}}
.corpus{{display:flex;gap:10px;flex-wrap:wrap;font-size:.78rem;color:var(--mut);margin-top:8px;padding-top:8px;border-top:1px solid var(--bdr);}}
</style></head><body>
<header><h1>🏓 Morning Brief</h1><p class="sub">{DATE_LABEL}</p></header>
<div class="card"><div class="ch" onclick="t(this)"><span>🎯 3 Things to Do Today</span><span>▼</span></div><div class="cb"><ul>{hit_li}</ul></div></div>
<div class="card"><div class="ch" onclick="t(this)"><span>🔥 Threads Don't Let Die</span><span>▼</span></div><div class="cb"><ul>{thread_li}</ul></div></div>
<div class="card"><div class="ch" onclick="t(this)"><span>🤖 What Your AI Built</span><span>▼</span></div><div class="cb"><ul>{out_li}</ul>{corpus_txt}</div></div>
<div class="card"><div class="ch" onclick="t(this)"><span>⚡ One Decision Needed</span><span>▼</span></div><div class="cb"><p style="color:#00E676;font-weight:600;padding:6px 0">→ Tonight: Brand intelligence or coaching clips for Court Kings?</p></div></div>
<script>function t(h){{const b=h.nextElementSibling,a=h.querySelector('span:last-child');b.style.display=b.style.display==='none'?'':'none';a.textContent=b.style.display==='none'?'▶':'▼';}}</script>
</body></html>"""
    md_out.write_text(f"# Morning Brief — {DATE_LABEL}\n\n## Hit List\n" + "\n".join(f"- {i}" for i in (hit or ["See BILL-OS.md"])))
    html_out.write_text(html)
    print(f"[brief] ✓ {html_out}")
    os.system(f'open "{html_out}"')

if __name__ == "__main__": main()

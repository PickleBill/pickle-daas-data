#!/usr/bin/env python3
"""Overnight Prompt Generator. Usage: python tools/generate-overnight-prompt.py"""
import json
from datetime import datetime
from pathlib import Path
try:
    from dotenv import load_dotenv; load_dotenv(Path(__file__).parent.parent / ".env")
except ImportError: pass

ROOT = Path(__file__).parent.parent
OUTPUT = ROOT / "output"
DISCOVERY = OUTPUT / "discovery"
DATE = datetime.now().strftime("%Y-%m-%d")

def done_angles():
    if not DISCOVERY.exists(): return set()
    return {f.name.split("-")[1] for f in DISCOVERY.glob("rapid-*-quick_scan-*.json")}

def corpus_stats():
    p = OUTPUT / "enriched-corpus.json"
    if not p.exists(): return {}
    try:
        clips = json.loads(p.read_text())
        return {"total":len(clips),"viral_high":sum(1 for c in clips if isinstance(c.get("viral"),(int,float)) and c.get("viral",0)>=7),
                "high_q":sum(1 for c in clips if c.get("quality",0)>=7)}
    except: return {}

def pick(done, corpus):
    if "coach" not in done: return {"angle":"coach","slice":"high_quality","format":"dashboard","why":"Court Kings demo prep — coaching clips are the premium DaaS tier ($250-500K deal)"}
    if "brand" not in done: return {"angle":"brand","slice":"all","format":"dashboard","why":"Brand intelligence = data moat story for investors. JOOLA in 71% of clips."}
    if "viral" not in done: return {"angle":"viral","slice":"all","format":"brief","why":"Viral patterns → social proof for venue demos"}
    if "skill" not in done: return {"angle":"skill","slice":"high_quality","format":"brief","why":"Shot-type classification drives coaching product"}
    return {"angle":"tactical","slice":"all","format":"dashboard","why":"Refresh tactical overview + investor dashboard"}

def main():
    done = done_angles(); corpus = corpus_stats()
    d = pick(done, corpus)
    print(f"[overnight] Completed: {done or 'none'}")
    print(f"[overnight] Direction: {d['angle']} — {d['why'][:55]}...")
    prompt = f"""# Overnight Session — {DATE}\n# Direction: {d['angle'].title()}\n# Why: {d['why']}\n\n---\n\n## IDENTITY\nBill Bricker's AI Chief of Staff. Courtana = AI smart court tech. Raising $1.3M seed.\nCritical: NEVER api.courtana.com. Always Accept: application/json. Never use `next` pagination.\nShow outputs: open HTML immediately. Automate don't instruct.\n\n## CORPUS: {corpus.get('total',0)} clips | {corpus.get('viral_high',0)} high-viral | {corpus.get('high_q',0)} high-quality\nCost: $0.005/clip (verified Apr 9)\n\n## TASKS\n1. python tools/rapid-cycle.py --depth quick_scan --angle {d['angle']} --data-slice {d['slice']} --output-format {d['format']}\n2. python tools/morning-brief-generator.py\n3. python tools/session-closer.py\n\n## IF FINDINGS ARE STRONG: build ONE of:\n- Lovable dashboard prompt for {d['angle']} view\n- Investor proof point → output/pickle-daas-investor-proof-points.md\n- Venue demo snippet for Court Kings pitch\n\n## DO NOT: Re-fetch corpus. Build booking features. Create >3 files without checking.\n\n_Generated {datetime.now().strftime('%Y-%m-%d %H:%M')}_"""
    out = OUTPUT / "next-overnight-prompt.md"
    out.write_text(prompt)
    print(f"\n[overnight] ✓ {out}")
    print(f"\nPaste output/next-overnight-prompt.md into a new Claude Code chat.")
    print(f"Direction: {d['angle'].upper()} — {d['why']}")

if __name__ == "__main__": main()

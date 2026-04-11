#!/usr/bin/env python3
"""
Chief of Staff Setup — run this once to install all 4 tools.
Usage: python tools/setup-chief-of-staff.py
If Dropbox wipes the tools, just run this again.
"""
import os
from pathlib import Path

ROOT = Path(__file__).parent.parent
TOOLS = ROOT / "tools"
OUTPUT = ROOT / "output"

for d in [OUTPUT / "briefs", OUTPUT / "session-logs", OUTPUT / "discovery"]:
    d.mkdir(parents=True, exist_ok=True)

SCRIPTS = {}

# ── morning-brief-generator.py ────────────────────────────────────────────────
SCRIPTS["morning-brief-generator.py"] = r'''#!/usr/bin/env python3
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
'''

# ── session-closer.py ─────────────────────────────────────────────────────────
SCRIPTS["session-closer.py"] = r'''#!/usr/bin/env python3
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
'''

# ── rapid-cycle.py ────────────────────────────────────────────────────────────
SCRIPTS["rapid-cycle.py"] = r'''#!/usr/bin/env python3
"""Rapid Insight Cycle. Usage: python tools/rapid-cycle.py --depth quick_scan --angle tactical --data-slice all --output-format brief"""
import os, json, argparse, sys
from datetime import datetime
from pathlib import Path
from collections import Counter, defaultdict
try:
    from dotenv import load_dotenv; load_dotenv(Path(__file__).parent.parent / ".env")
except ImportError: pass

ROOT = Path(__file__).parent.parent
OUTPUT = ROOT / "output"
TS = datetime.now().strftime("%Y%m%d-%H%M")
NOW = datetime.now().strftime("%Y-%m-%d %H:%M")
CAPS = {"brand":0.20,"skill":0.45,"viral":0.65,"quality":0.70}

def load_corpus():
    for fn in ["enriched-corpus.json","corpus-export.json"]:
        p = OUTPUT / fn
        if p.exists():
            try:
                d = json.loads(p.read_text())
                clips = d if isinstance(d,list) else d.get("clips",[])
                print(f"[rapid] Loaded {len(clips)} clips from {fn}"); return clips
            except Exception as e: print(f"[rapid] Warning {fn}: {e}")
    print("[rapid] ERROR: No corpus."); sys.exit(1)

def apply_slice(clips, s):
    if s=="viral": return [c for c in clips if isinstance(c.get("viral"),(int,float)) and c.get("viral",0)>=7]
    if s=="high_quality": return [c for c in clips if c.get("quality",0)>=7]
    if s=="badged": return [c for c in clips if c.get("badges")]
    if s=="recent": return clips[-30:]
    return clips

def analyze_brand(clips):
    bc=Counter(); co=defaultdict(Counter)
    for c in clips:
        bs=c.get("brands",[]); [bc.update([b.lower()]) for b in bs]
        for i,b1 in enumerate(bs):
            for b2 in bs[i+1:]: co[b1.lower()][b2.lower()]+=1
    total=len(clips); top=bc.most_common(10)
    findings=[f"{b.title()} in {round(n/total*100,1)}% of clips ({n}/{total})" for b,n in top[:5]]
    pairs=[f"{b1.title()} + {list(o.keys())[0].title()} co-appear {list(o.values())[0]}x" for b1,o in list(co.items())[:3] if o]
    return {"angle":"brand","total_clips":total,"top_brands":top[:10],"co_occurrence_pairs":pairs,
            "key_findings":findings,"confidence_cap":CAPS["brand"],
            "investor_note":f"Brand detection ~{int(CAPS['brand']*100)}% verified (V2). Use aggregate trends.",
            "counter_argument":"Paddle logos often small/occluded — may over-count."}

def analyze_skill(clips):
    sc=Counter(); aq=Counter(); ac=Counter()
    for c in clips:
        shot=(c.get("dominant_shot") or "unknown").lower()
        arc=(c.get("arc") or "unknown").lower()
        sc[shot]+=1; aq[shot]+=c.get("quality",5); ac[arc]+=1
    total=len(clips); top=sc.most_common(8)
    findings=[f"'{s}' dominant shot in {round(n/total*100,1)}% of clips, avg quality {round(aq[s]/n,1)}/10" for s,n in top[:3]]
    findings+=[f"Rally arc '{a}' in {n} clips" for a,n in ac.most_common(3)[:2]]
    findings.append("Note: skills score dict is all-zero in corpus — shot/arc used as proxy")
    return {"angle":"skill","total_clips":total,"top_shot_types":top,"top_arc_types":ac.most_common(6),
            "key_findings":findings,"confidence_cap":CAPS["skill"],
            "investor_note":"Shot-type classification drives coaching clip selection. Skills dict needs re-run."}

def analyze_viral(clips):
    THR=7; viral=[c for c in clips if isinstance(c.get("viral"),(int,float)) and c.get("viral",0)>=THR]
    non=[c for c in clips if c not in viral]; total=len(clips); vc=len(viral)
    sd=Counter(int(c.get("viral",0)) for c in clips if isinstance(c.get("viral"),(int,float)))
    vs=Counter((c.get("dominant_shot") or "?").lower() for c in viral)
    va=Counter((c.get("arc") or "?").lower() for c in viral)
    sa=round(sum(c.get("total_shots",0) for c in viral)/vc,1) if vc else 0
    na=round(sum(c.get("total_shots",0) for c in non)/len(non),1) if non else 0
    findings=[f"High-viral (≥{THR}): {vc}/{total} ({round(vc/total*100,1)}%)",
              f"Score distribution: {dict(sorted(sd.items()))}",
              f"Viral clips avg {sa} shots vs {na} for others"]
    if vs: findings.append(f"Top shot in viral: '{vs.most_common(1)[0][0]}'")
    if va: findings.append(f"Top arc in viral: '{va.most_common(1)[0][0]}'")
    return {"angle":"viral","total_clips":total,"viral_count":vc,"viral_pct":round(vc/total*100,1) if total else 0,
            "score_distribution":dict(sd),"viral_shot_patterns":vs.most_common(5),"viral_arc_patterns":va.most_common(5),
            "key_findings":findings,"confidence_cap":CAPS["viral"],
            "investor_note":f"viral is numeric 2-8 (not boolean). Only {vc} clips score ≥{THR}."}

def analyze_tactical(clips):
    total=len(clips); cost=0.0054
    hb=sum(1 for c in clips if c.get("brands"))
    hs=sum(1 for c in clips if c.get("dominant_shot") and c.get("dominant_shot")!="unknown")
    hbg=sum(1 for c in clips if c.get("badges"))
    vh=sum(1 for c in clips if isinstance(c.get("viral"),(int,float)) and c.get("viral",0)>=7)
    hq=sum(1 for c in clips if c.get("quality",0)>=7)
    findings=[f"Pipeline: {total} clips @ ${cost}/clip = ${round(total*cost,4)} total",
              f"Brand data: {round(hb/total*100)}% of clips",
              f"Shot classification: {round(hs/total*100)}% have dominant_shot",
              f"Quality: {round(hq/total*100)}% high-quality (≥7/10)",
              f"High-viral (≥7): {vh} clips ({round(vh/total*100)}%)",
              f"Scale: 400K clips = ${round(400000*cost):,} (batch: ${round(400000*0.0027):,})"]
    return {"angle":"tactical","total_clips":total,
            "coverage":{"brands":round(hb/total*100,1),"shot_data":round(hs/total*100,1),
                        "badges":round(hbg/total*100,1),"viral_high":round(vh/total*100,1),"high_quality":round(hq/total*100,1)},
            "cost_baseline":{"per_clip":cost,"corpus_total":round(total*cost,4),
                             "scale_400k":round(400000*cost,2),"scale_400k_batch":round(400000*0.0027,2)},
            "key_findings":findings,"confidence_cap":0.70,
            "investor_note":"Economics verified Apr 9. Lead with $0.005/clip + verification story."}

def analyze_coach(clips):
    cands=sorted([c for c in clips if c.get("quality",0)>=6],key=lambda x:-(x.get("quality",0)+x.get("watchability",0)))
    sf=Counter((c.get("dominant_shot") or "unknown").lower() for c in cands)
    af=Counter((c.get("arc") or "unknown").lower() for c in cands)
    findings=[f"{len(cands)}/{len(clips)} clips qualify (quality ≥6)",
              f"Top coaching shot: '{sf.most_common(1)[0][0] if sf else 'n/a'}'",
              f"Best clips: {[c['uuid'][:8] for c in cands[:3]]}",
              f"Shot distribution: {dict(sf.most_common(4))}"]
    return {"angle":"coach","total_clips":len(clips),"coaching_candidates":len(cands),
            "top_coaching_clips":[{"uuid":c["uuid"],"dominant_shot":c.get("dominant_shot"),"arc":c.get("arc"),
                                    "quality":c.get("quality"),"watchability":c.get("watchability"),"video_url":c.get("video_url","")} for c in cands[:5]],
            "shot_frequency":sf.most_common(8),"arc_frequency":af.most_common(6),
            "key_findings":findings,"confidence_cap":CAPS["skill"],
            "investor_note":"Coaching clips = premium DaaS tier. Venues pay most for these."}

HANDLERS={"brand":analyze_brand,"skill":analyze_skill,"viral":analyze_viral,"tactical":analyze_tactical,"coach":analyze_coach}

def format_brief(r,args):
    lines=[f"# Rapid Cycle — {r['angle'].title()} / {args.depth}",f"_{NOW} | slice:{args.data_slice} | clips:{r.get('total_clips','?')}_","","## Key Findings",""]
    lines+=[f"- {f}" for f in r.get("key_findings",[])]
    cap=r.get("confidence_cap"); lines+=["","## Confidence","",f"⚠️ Verified accuracy: **{int(cap*100)}%** — use for trends"] if cap is not None else []
    note=r.get("investor_note"); lines+=[f"\n> **Investor:** {note}"] if note else []
    return "\n".join(lines)

def format_dashboard(r,args):
    angle=r.get("angle","analysis"); findings_html="".join(f"<li>{f}</li>" for f in r.get("key_findings",[]))
    cap=r.get("confidence_cap",0); note=r.get("investor_note","")
    extra=""
    if "top_brands" in r:
        rows="".join(f"<tr><td>{b.title()}</td><td>{c}</td></tr>" for b,c in r["top_brands"][:8])
        extra=f"<table><thead><tr><th>Brand</th><th>Clips</th></tr></thead><tbody>{rows}</tbody></table>"
    elif "coverage" in r:
        bars="".join(f'<div style="display:flex;align-items:center;gap:8px;padding:4px 0;font-size:.82rem"><span style="min-width:80px">{k.title()}</span><div style="flex:1;background:#1a2535;border-radius:4px;height:8px"><div style="background:#00E676;width:{v}%;height:100%;border-radius:4px"></div></div><span>{v}%</span></div>' for k,v in r["coverage"].items())
        extra=f"<div>{bars}</div>"
    elif "top_shot_types" in r:
        rows="".join(f"<tr><td>{s.title()}</td><td>{c}</td></tr>" for s,c in r.get("top_shot_types",[])[:8])
        extra=f"<table><thead><tr><th>Shot Type</th><th>Clips</th></tr></thead><tbody>{rows}</tbody></table>"
    elif "top_coaching_clips" in r:
        rows="".join(f"<tr><td><code>{c['uuid'][:12]}</code></td><td>{c.get('quality')}/10</td><td>{c.get('dominant_shot','')}</td><td>{c.get('arc','')}</td></tr>" for c in r.get("top_coaching_clips",[])[:5])
        extra=f"<table><thead><tr><th>Clip</th><th>Quality</th><th>Shot</th><th>Arc</th></tr></thead><tbody>{rows}</tbody></table>"
    return f"""<!DOCTYPE html><html><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0"><title>{angle.title()} Intelligence</title>
<style>:root{{--bg:#0f1219;--sur:#161c27;--bdr:#1e2a3a;--acc:#00E676;--txt:#e0e6f0;--mut:#6b7fa0;}}
*{{box-sizing:border-box;margin:0;padding:0;}}body{{background:var(--bg);color:var(--txt);font-family:-apple-system,sans-serif;max-width:800px;margin:0 auto;padding:20px;}}
h1{{color:var(--acc);font-size:1.4rem;margin-bottom:4px;}}.meta{{color:var(--mut);font-size:.8rem;margin-bottom:20px;}}
.card{{background:var(--sur);border:1px solid var(--bdr);border-radius:10px;padding:16px;margin-bottom:14px;}}
.card h2{{font-size:.95rem;margin-bottom:10px;color:var(--acc);}}ul{{list-style:none;}}
li{{padding:5px 0;border-bottom:1px solid var(--bdr);font-size:.86rem;}}li:last-child{{border-bottom:none;}}
table{{width:100%;border-collapse:collapse;font-size:.84rem;}}th,td{{padding:8px;text-align:left;border-bottom:1px solid var(--bdr);}}th{{color:var(--mut);}}
code{{background:#1a2535;padding:2px 5px;border-radius:4px;color:#00B0FF;font-size:.8rem;}}
.warn{{background:#1a1a2e;border-left:3px solid #ff6b35;padding:10px 14px;border-radius:4px;font-size:.82rem;margin-top:8px;}}
.inv{{background:#0d1f1a;border-left:3px solid var(--acc);padding:10px 14px;border-radius:4px;font-size:.82rem;margin-top:8px;}}</style></head><body>
<h1>🏓 {angle.title()} Intelligence</h1>
<p class="meta">Rapid Cycle · {NOW} · {r.get('total_clips','?')} clips · {args.data_slice} slice</p>
<div class="card"><h2>Key Findings</h2><ul>{findings_html}</ul></div>
{"<div class='card'><h2>Data</h2>" + extra + "</div>" if extra else ""}
<div class="card"><h2>Confidence</h2>
<div class="warn">⚠️ Verified accuracy: <strong>{int(cap*100)}%</strong> — use for trends, not absolute claims</div>
{"<div class='inv'>💡 " + note + "</div>" if note else ""}
</div></body></html>"""

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--depth",choices=["quick_scan","deep_dive"],default="quick_scan")
    p.add_argument("--angle",choices=["brand","skill","viral","tactical","coach"],default="tactical")
    p.add_argument("--data-slice",choices=["all","viral","high_quality","badged","recent"],default="all",dest="data_slice")
    p.add_argument("--output-format",choices=["brief","json","dashboard","lovable-ready","full"],default="brief",dest="output_format")
    args=p.parse_args()
    print(f"[rapid] {args.depth} | angle={args.angle} | slice={args.data_slice} | format={args.output_format}")
    clips=apply_slice(load_corpus(),args.data_slice); print(f"[rapid] Working set: {len(clips)} clips")
    result=HANDLERS[args.angle](clips)
    od=OUTPUT/"discovery"; od.mkdir(exist_ok=True)
    (od/f"rapid-{args.angle}-{args.depth}-{TS}.json").write_text(json.dumps(result,indent=2))
    if args.output_format=="brief": content,ext=format_brief(result,args),".md"
    elif args.output_format=="dashboard": content,ext=format_dashboard(result,args),".html"
    elif args.output_format=="json": content,ext=json.dumps(result,indent=2),".json"
    else: content,ext=format_brief(result,args),".md"
    out=od/f"rapid-{args.angle}-{args.depth}-{TS}-output{ext}"
    out.write_text(content); print(f"[rapid] ✓ {out}")
    if ext==".html": os.system(f'open "{out}"')
    else: print("\n"+content[:1200])
    print(f"\n[rapid] Done. $0 API cost.")

if __name__ == "__main__": main()
'''

# ── generate-overnight-prompt.py ─────────────────────────────────────────────
SCRIPTS["generate-overnight-prompt.py"] = r'''#!/usr/bin/env python3
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
'''

# ── README.md ─────────────────────────────────────────────────────────────────
SCRIPTS["README.md"] = """# Pickle DaaS — Tools Index

## Quick Commands
```bash
python tools/morning-brief-generator.py          # Morning brief (opens in browser)
python tools/rapid-cycle.py --depth quick_scan --angle tactical --data-slice all --output-format dashboard
python tools/rapid-cycle.py --depth quick_scan --angle brand --data-slice all --output-format dashboard
python tools/rapid-cycle.py --depth quick_scan --angle coach --data-slice high_quality --output-format dashboard
python tools/generate-overnight-prompt.py        # Generate tonight's prompt
python tools/session-closer.py                   # Close out a session
```

## Tools
| Script | What | API Keys |
|--------|------|----------|
| morning-brief-generator.py | Daily brief: hit list + corpus + threads (opens HTML) | None |
| session-closer.py | Captures session: new files, git log, next prompt | None |
| rapid-cycle.py | Pattern analysis: brand/skill/viral/tactical/coach | None (quick_scan) / Gemini (deep_dive) |
| generate-overnight-prompt.py | Picks next direction, writes paste-ready prompt | None |

## The Loop
```
morning-brief-generator.py → read brief → generate-overnight-prompt.py →
paste into Claude Code → rapid-cycle.py → session-closer.py → repeat
```

## Angles
- **brand**: JOOLA in 71% of clips. Brand co-occurrence. Investor moat story.
- **coach**: 45 clips quality≥6. Shot type + arc signals. Court Kings demo.
- **viral**: Score 2-8 (NOT boolean). 7 clips score ≥7. Shot patterns.
- **skill**: Shot-type proxy (skills dict is all-zero in corpus).
- **tactical**: Full pipeline health. $0.005/clip. Scale economics.
"""

# ── Install ───────────────────────────────────────────────────────────────────
print("Installing Chief of Staff tools...")
for filename, content in SCRIPTS.items():
    path = TOOLS / filename
    path.write_text(content.lstrip())
    print(f"  ✓ tools/{filename}")

print("\nSetup complete! Run your morning brief:")
print("  python tools/morning-brief-generator.py")
print("\nRun a quick analysis:")
print("  python tools/rapid-cycle.py --depth quick_scan --angle tactical --data-slice all --output-format dashboard")

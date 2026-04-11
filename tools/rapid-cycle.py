#!/usr/bin/env python3
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

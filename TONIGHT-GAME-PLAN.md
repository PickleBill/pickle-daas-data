# Tonight's Game Plan — April 11, 2026
_3 parallel Claude Code sessions. Total budget: ~$30. Walk away and come back to results._

---

## The Automation Loop (This Is What We're Building)

```
Morning Brief → Bill picks direction → Overnight prompt auto-generates
     ↑                                          ↓
  Results captured                    Claude Code runs overnight
     ↑                                          ↓
  Session closer logs everything    Outputs land in gh-pages + Lovable
```

Once Session C (below) completes, this loop runs itself.

---

## SESSION A: Pickle Data Sprint (ALREADY RUNNING)
**Status:** Active in Claude Code right now
**What it's doing:** Expanding corpus from 96→250+ clips, building dashboards, multi-model validation
**Budget:** ~$10
**Prompt:** Already pasted (the Phase 2 expansion prompt from earlier)

**Nothing to do here — let it cook.**

---

## SESSION B: Rapid Insight Cycle
**Status:** Ready to launch
**File:** `overnight-rapid-cycle-template.md`
**What it does:** Runs a configurable discovery pass — pick an angle, depth, and hypothesis

### To launch (copy-paste):
```bash
cd ~/path-to/PICKLE-DAAS
claude -p "$(cat overnight-rapid-cycle-template.md)" --max-turns 80 --max-budget-usd 10
```

### Configure before launching:
Open `overnight-rapid-cycle-template.md` and set:
- DEPTH: `deep_dive` (recommended — $5-10, meaningful results)
- ANGLE: `tactical` (shot patterns — least explored angle so far)
- HYPOTHESIS: `"Advanced players have distinct shot sequence signatures that could power a coaching product"`
- OUTPUT_FORMAT: `full`

Or try a different angle — brand, narrative, coaching. The template explains all options.

---

## SESSION C: AI Chief of Staff Bootstrap
**Status:** Ready to launch
**File:** `overnight-ai-chief-of-staff.md`
**What it does:** Builds the operational tools — morning brief generator, session closer, overnight prompt generator, rapid-cycle CLI, tool index

### To launch (copy-paste):
```bash
cd ~/path-to/PICKLE-DAAS
claude -p "$(cat overnight-ai-chief-of-staff.md)" --max-turns 60
```

This is the most important session. When it's done, you'll have:
- `tools/morning-brief-generator.py` — run every morning
- `tools/session-closer.py` — run at end of every Claude Code session
- `tools/rapid-cycle.py` — the Rapid Insight Cycle as a real CLI tool
- `tools/generate-overnight-prompt.py` — auto-creates the next overnight prompt
- A working quick_scan test proving the pipeline works

---

## WHAT WILL BE TRUE TOMORROW MORNING

If all 3 sessions complete:

1. **Data Sprint** produced 250+ analyzed clips, new dashboards, gh-pages updated, DinkData Lovable app has fresh data
2. **Rapid Cycle** produced a deep-dive on tactical patterns with a full dashboard + Lovable-ready export
3. **Chief of Staff** built the tools that make this repeatable — morning brief, session closer, overnight prompt generator

Then tomorrow you:
1. Run `python tools/morning-brief-generator.py` → see what happened overnight
2. Review the dashboards (they'll open automatically)
3. Say what angle you want to explore next
4. Run `python tools/generate-overnight-prompt.py` → get tonight's prompt
5. Paste into Claude Code → repeat

---

## KNOWN BLOCKERS

| Blocker | Impact | Fix |
|---------|--------|-----|
| Anthropic API billing | Multi-model validation (Session A) will skip gracefully | Add payment at console.anthropic.com |
| Supabase service key missing | Can't push to Supabase (non-blocking — gh-pages works) | Get from Supabase dashboard |
| Single venue data | All confidence capped at 75-80% | Get Peak venue clips after install |

---

## FILES CREATED THIS SESSION

| File | What It Is |
|------|-----------|
| `overnight-rapid-cycle-template.md` | Configurable Claude Code prompt for any discovery angle |
| `overnight-ai-chief-of-staff.md` | Claude Code prompt to build the operational tools |
| `TONIGHT-GAME-PLAN.md` | This file — the master plan |

These are in addition to what V2 produced overnight:
- `output/discovery/v2/` — 11 verified discoveries, morning brief, Lovable handoff
- `output/investor/investor-demo-v2.html` — Updated investor dashboard
- `output/lovable/discovery-v2-export.json` — Ready for Lovable import

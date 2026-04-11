# AI Chief of Staff — Ready
_Built: 2026-04-11_

---

## What Was Built

| Tool | Description |
|------|-------------|
| `tools/morning-brief-generator.py` | Reads hit list + corpus, generates dark-theme phone brief (MD + HTML, auto-opens) |
| `tools/session-closer.py` | Captures every session: new files, git log, blockers, next-session prompt |
| `tools/rapid-cycle.py` | Pattern analysis engine — 5 angles, $0 for quick_scan, Gemini for deep_dive |
| `tools/generate-overnight-prompt.py` | Picks highest-leverage next direction, writes paste-ready Claude Code prompt |
| `tools/README.md` | Index of all tools with commands and what they produce |

**Verified working:** `rapid-cycle.py` quick_scan ran live — 96 clips, $0.52 total cost, zero API calls.

---

## The Automation Loop

```
Morning Brief opens on your phone
       ↓
python tools/generate-overnight-prompt.py
       → Picks highest-leverage direction
       → Writes output/next-overnight-prompt.md
       ↓
New Claude Code chat
       → Paste contents of next-overnight-prompt.md
       → Session runs overnight
       ↓
python tools/rapid-cycle.py  ← runs inside the session
       → Produces analysis dashboards
       ↓
python tools/session-closer.py  ← runs at session end
       → Captures what was built
       → Writes next prompt
       ↓
python tools/morning-brief-generator.py  ← tomorrow morning
       → Opens in browser
       ↓
Repeat
```

---

## Run This for Your Morning Brief

```bash
cd PICKLE-DAAS
python tools/morning-brief-generator.py
```

Opens `output/briefs/morning-brief-YYYY-MM-DD.html` in your browser. Under 50 lines. Mobile-first.

---

## Run This to Generate Tonight's Prompt

```bash
cd PICKLE-DAAS
python tools/generate-overnight-prompt.py
```

Prints the next direction and saves to `output/next-overnight-prompt.md`.
Paste that file's contents into a new Claude Code chat.

---

## Quick Test Right Now

```bash
cd PICKLE-DAAS
python tools/rapid-cycle.py --depth quick_scan --angle tactical --data-slice all --output-format dashboard
```

Opens a live dashboard in your browser. $0 cost.

---

## Blockers / Notes

- `viral` flag shows 100% of clips as viral in enriched corpus — this is a data quality flag. The model may have marked everything viral in the enrichment run. Flag for V2 re-verification before using viral counts in investor materials.
- `badges` shows 0% coverage — badges may be in a separate file (creative-badges.json). rapid-cycle reads from enriched-corpus.json which doesn't have badge joins yet.
- Morning brief pulls BILL-OS hit list from `../BILL-OS/BILL-OS.md` — if path changes, update ROOT in the script.
- Deep_dive mode needs GEMINI_API_KEY (it's in .env) — quick_scan is $0 always.

---

_All tools are under 300 lines. All use python-dotenv. All handle missing keys gracefully._

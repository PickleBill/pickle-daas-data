# Pickle DaaS — Tools Index

All scripts live in `tools/`. Run from the `PICKLE-DAAS/` directory.

---

## morning-brief-generator.py
**What:** Scans output/ for new files, reads BILL-OS hit list, generates a phone-friendly daily brief.
**Run:** `python tools/morning-brief-generator.py`
**Produces:** `output/briefs/morning-brief-YYYY-MM-DD.md` + `.html` (opens automatically)
**API keys:** None required

---

## session-closer.py
**What:** Captures what was built this session — new files, git log, blockers, next session prompt.
**Run:** `python tools/session-closer.py`
**Produces:** `output/session-logs/session-TIMESTAMP.md` + `output/next-overnight-prompt.md`
**API keys:** None required

---

## rapid-cycle.py
**What:** Pattern analysis on the clip corpus. Zero API cost for quick_scan mode.
**Run:** `python tools/rapid-cycle.py --depth quick_scan --angle tactical --data-slice all --output-format brief`
**Options:**
- `--depth`: `quick_scan` ($0, local JSON) | `deep_dive` (calls Gemini API)
- `--angle`: `brand` | `skill` | `viral` | `tactical` | `coach`
- `--data-slice`: `all` | `viral` | `high_quality` | `badged` | `recent`
- `--output-format`: `brief` | `json` | `dashboard` | `lovable-ready` | `full`
**Produces:** `output/discovery/rapid-[angle]-[depth]-TIMESTAMP.json` + formatted output file
**API keys:** Only GEMINI_API_KEY needed for `--depth deep_dive`

---

## generate-overnight-prompt.py
**What:** Reads current state, picks the highest-leverage next direction, generates a paste-ready Claude Code session prompt.
**Run:** `python tools/generate-overnight-prompt.py`
**Produces:** `output/next-overnight-prompt.md` (paste into new Claude Code chat)
**API keys:** None required

---

## The Automation Loop

```
Morning Brief → Bill picks direction
      ↓
generate-overnight-prompt.py → output/next-overnight-prompt.md
      ↓
Paste into new Claude Code chat → overnight session runs
      ↓
rapid-cycle.py → analysis + dashboards
      ↓
session-closer.py → captures what was built
      ↓
morning-brief-generator.py → tomorrow's brief (auto-opened)
      ↓
Repeat
```

---

## Quick Commands

```bash
# Your morning brief (run every morning)
python tools/morning-brief-generator.py

# Run a quick analysis right now ($0)
python tools/rapid-cycle.py --depth quick_scan --angle tactical --data-slice all --output-format dashboard

# Generate tonight's overnight prompt
python tools/generate-overnight-prompt.py

# Close out a session
python tools/session-closer.py
```

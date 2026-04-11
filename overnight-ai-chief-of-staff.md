# AI Chief of Staff — Claude Code Bootstrap
# This is a PARALLEL session to the data pipeline work.
# Paste into a fresh Claude Code session.
#
# Run command:
#   claude -p "$(cat overnight-ai-chief-of-staff.md)" --max-turns 60

---

## IDENTITY

You are Bill Bricker's AI Chief of Staff. Bill is the founder/CEO of Courtana — AI-powered
smart court tech for pickleball venues. He's raising $1.3M seed, closing 3 venue deals,
and building a data pipeline product (Pickle DaaS).

Bill is non-technical. He uses voice (Wispr Flow), Lovable for frontends, and Claude Code
for overnight builds. Time is his bottleneck, not money. He wants automation, not instructions.

---

## YOUR JOB THIS SESSION

Build the operational infrastructure that makes the AI Chief of Staff role repeatable.
This means creating files, scripts, and templates — not giving advice.

---

## Task 1: Read Context (~5 min)

Read these files in order:
1. `../BILL-OS/BILL-OS.md` — Master OS: hit list, deals, people
2. `../BILL-OS/LESSONS.md` — How Bill wants to work (CRITICAL — follow these rules)
3. `../BILL-OS/COURTANA-VALUE-PROP.md` — What Courtana is/isn't
4. `../.auto-memory/MEMORY.md` — What's been learned across sessions

Key lessons to internalize:
- Show outputs, don't describe them
- Automate, don't instruct
- Don't explain files Bill doesn't need to see
- Flag abandoned projects — Bill loses threads
- Less setup, more execution

---

## Task 2: Build the Morning Brief Generator (~15 min)

Create: tools/morning-brief-generator.py

This script reads available data and produces a morning brief. It should:

1. **Check BILL-OS.md** for the hit list and flag anything overdue
2. **Check output/** for any new files since yesterday (new analyses, dashboards, etc.)
3. **Check .auto-memory/** for recent memories
4. **Produce** output/briefs/morning-brief-[date].md with sections:
   - "3 Things to Do Today" (ranked by stakes, not effort)
   - "Threads Don't Let Die" (active projects that need attention)
   - "What Your AI Built Overnight" (new files, analyses, dashboards)
   - "Deal Status" (Peak, Court Kings, Concord — any changes?)
   - "One Decision Needed" (the most important decision Bill needs to make today)

The brief should be SHORT. Under 50 lines. Bill reads this on his phone.

Also produce output/briefs/morning-brief-[date].html — dark theme, mobile-first, same content
but with expandable sections and links to dashboards/files.

---

## Task 3: Build the Session Closer (~10 min)

Create: tools/session-closer.py

This script runs at the end of every Claude Code session to capture what happened.
It should:

1. Read git log for commits since session start
2. Scan output/ for new files
3. Produce output/session-logs/session-[timestamp].md with:
   - What was built
   - What's new in output/
   - What's pushed to gh-pages
   - What's blocked or needs Bill
   - Suggested next session prompt (literally copy-paste ready)
4. Append a 1-line entry to ../BILL-OS/SESSION-LOG.md

---

## Task 4: Build Rapid Cycle Launcher (~15 min)

Create: tools/rapid-cycle.py

This is the executable version of the Rapid Insight Cycle skill.
It should accept CLI args:

```bash
python tools/rapid-cycle.py \
  --depth quick_scan \
  --angle brand \
  --data-slice all \
  --hypothesis "JOOLA dominance is venue-specific" \
  --output-format dashboard
```

Implementation:
1. Parse args
2. Load corpus data from output/corpus-export.json (or enriched-corpus.json)
3. Filter by data_slice
4. For quick_scan: run pattern detection on existing JSONs (no API calls)
5. For deep_dive: call Gemini API on targeted clips
6. For full_corpus: analyze all clips
7. Run discovery logic (simplified version — doesn't need 5 separate agents,
   just focused analysis based on angle)
8. Apply validation rules (confidence caps, counter-arguments, bias flags)
9. Generate output in requested format

For quick_scan, this should work WITHOUT any API keys — pure local JSON analysis.

---

## Task 5: Build the Overnight Prompt Generator (~10 min)

Create: tools/generate-overnight-prompt.py

This reads the current state and generates a Claude Code prompt for the next overnight run.
It should:

1. Check what's been done (read session logs, output/)
2. Check what's pending (BILL-OS hit list, blocked items)
3. Pick the highest-leverage next action
4. Generate a complete, copy-paste-ready prompt in the style of overnight-rapid-cycle-template.md
5. Save to output/next-overnight-prompt.md
6. Print the run command to stdout

This is the AUTOMATION LOOP:
  Morning brief → Bill picks direction → Overnight prompt auto-generates → Bill pastes into Claude Code → Runs overnight → Morning brief captures results → Repeat

---

## Task 6: Create INDEX of All Tools (~5 min)

Create: tools/README.md

List every script in tools/ with:
- What it does (1 line)
- How to run it (the command)
- What it produces (output files)
- Whether it needs API keys

Group by category:
- Data Pipeline (fetch, analyze, ingest)
- Discovery (engines, cycles, verification)
- Operations (morning brief, session closer, overnight generator)
- Utilities (cost measurement, model monitoring)

---

## Task 7: Test Quick Scan (~5 min)

Actually RUN a quick scan to prove the pipeline works:

```bash
python tools/rapid-cycle.py --depth quick_scan --angle tactical --data-slice all --output-format brief
```

If it works, save the output. If it fails, fix it and try again.
This is the proof that the automation loop is alive.

---

## RULES

- Every script must use python-dotenv for .env loading
- Every script must handle missing API keys gracefully (skip, don't crash)
- Every script must log what it does to stdout
- Every output goes to output/ in a timestamped subdirectory
- Never overwrite existing files
- Follow the Courtana API rules (courtana.com base, Accept header, manual pagination)
- Keep scripts under 300 lines each — simple beats comprehensive
- Use existing output/corpus-export.json as the data source — don't re-fetch unless expanding

---

## WHEN DONE

Create output/CHIEF-OF-STAFF-READY.md with:
1. What was built (list of tools)
2. The automation loop diagram (text)
3. "Paste this to run your first morning brief" (one command)
4. "Paste this to generate tonight's overnight prompt" (one command)
5. Any blockers or things that need Bill

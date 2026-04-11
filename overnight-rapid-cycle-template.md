# Rapid Insight Cycle — Claude Code Overnight Template
# Copy this entire file, swap the CONFIGURE section, paste into Claude Code.
# Budget: $5-15 depending on depth. Max turns: 80.
#
# Run command:
#   claude -p "$(cat overnight-rapid-cycle-template.md)" --max-turns 80 --max-budget-usd 10

---

## ===== CONFIGURE THIS SECTION =====

DEPTH: deep_dive
# Options: quick_scan ($0, 5min) | deep_dive ($5-25, 30min) | full_corpus ($25-100, 2-4hrs)

ANGLE: brand
# Options: player | brand | tactical | narrative | coaching | equipment | venue | match | shot_type | all

DATA_SLICE: all
# Options: all | venue:lifetime | skill_level:advanced | batch:picklebill-batch-20260410 | etc.
# Combine with &: venue:lifetime&skill_level:advanced

HYPOTHESIS: null
# Optional. Example: "JOOLA dominance is venue-specific, not universal"

OUTPUT_FORMAT: full
# Options: brief | json | dashboard | lovable-ready | full

## ===== END CONFIGURE =====

---

## ENVIRONMENT

Working directory: PICKLE-DAAS/
Load environment: `source .env` or use python-dotenv
Keys available: GEMINI_API_KEY, COURTANA_TOKEN, ELEVENLABS_API_KEY, SUPABASE_URL, SUPABASE_ANON_KEY, GITHUB_TOKEN, ANTHROPIC_API_KEY

## CRITICAL API RULES
- Base URL: https://courtana.com (NEVER api.courtana.com)
- Always: Accept: application/json header
- Pagination: construct ?page=N&page_size=100 manually (NEVER use `next` field)
- Anon endpoint: https://courtana.com/app/anon-highlight-groups/?page_size=100&page=N

---

## EXECUTION PLAN

### Task 0: Setup & Validate (~2 min)
1. cd to PICKLE-DAAS/
2. Verify .env loads: `python -c "from dotenv import load_dotenv; load_dotenv(); import os; print('GEMINI:', bool(os.getenv('GEMINI_API_KEY')))"`
3. Verify API: `curl -s -o /dev/null -w "%{http_code}" -H "Accept: application/json" "https://courtana.com/app/anon-highlight-groups/?page_size=1"` → expect 200
4. Read the CONFIGURE section above. Set variables for this run.

### Task 1: Load Existing Data
1. Read output/corpus-export.json (or enriched-corpus.json if it exists)
2. Count unique clips, players, brands, shots
3. If DATA_SLICE != "all", filter to matching clips
4. Log: "Working set: N clips matching [DATA_SLICE]"

### Task 2: Expand Corpus (if DEPTH = deep_dive or full_corpus)
1. Fetch clip URLs from anon endpoint (paginate manually)
2. Deduplicate against existing corpus UUIDs
3. Run pickle-daas-gemini-analyzer.py on new clips (or equivalent Gemini analysis)
4. Log cost per clip, maintain $0.0054/clip baseline
5. Save new analyses to output/batches/[timestamp]/

### Task 3: Run Discovery Agents
Based on ANGLE, run the appropriate agents:

**Player Agent:** Build per-player profiles — trajectories, signature moves, weaknesses, badges
**Brand Agent:** Brand frequency, equipment correlations, sponsorship whitespace
**Tactical Agent:** Shot sequences, error patterns, kitchen control, rally length
**Narrative Agent:** Viral moments, story arcs, comedy gold, sponsorship opportunity
**All:** Run all 4 in sequence, then Curator synthesizes

Each agent MUST produce findings with:
- data_points: count of supporting clips/shots
- confidence_score: 0-100 (capped: single venue max 80%, non-random max 75%, N<20 max 60%)
- source_clips: list with CDN URLs
- why_it_matters: one-sentence value prop
- sampling_bias_flag: always present if applicable
- strongest_counter_argument: one sentence

If HYPOTHESIS is set:
- Score each finding on how well it supports/refutes the hypothesis
- Include hypothesis_scorecard in output

### Task 4: Rank & Synthesize (Curator)
1. Load all *-discoveries.json files
2. Score each finding:
   composite = (surprise × 0.3) + (confidence × 0.2) + (revenue_potential × 0.3) + (demonstrability × 0.2)
3. Rank top 20
4. Flag cross-agent correlations (e.g., brand X appears in high-skill clips)
5. Output: ranked-discoveries.json

### Task 5: Generate Outputs (based on OUTPUT_FORMAT)

**brief:** → output/discoveries-[timestamp]/BRIEF.md
  - Top 5 findings with 2-line summaries
  - Verification notes
  - "What to do next" recommendation

**json:** → output/discoveries-[timestamp]/discoveries.json
  - All findings with full validation fields

**dashboard:** → output/discoveries-[timestamp]/top-discoveries.html
  - Dark theme: #0f1219 bg, #00E676 accent, #1e2a3a surface
  - Chart.js from CDN (https://cdnjs.cloudflare.com/ajax/libs/Chart.js/4.4.0/chart.umd.js)
  - Sections: hero stats, discovery cards (ranked, color-coded), charts, pitch section
  - Courtana logo: https://cdn.courtana.com/static/img/Courtana_Logo.png
  - Self-contained, mobile-responsive, shareable as standalone file

**lovable-ready:** → output/lovable/discovery-export.json + output/lovable/LOVABLE-DATA-README.md
  - JSON formatted for Lovable corpus import
  - TypeScript interfaces for all data shapes
  - gh-pages push instructions

**full:** → All of the above

### Task 6: Push to gh-pages (if OUTPUT_FORMAT includes lovable-ready or full)
1. git checkout gh-pages
2. Copy updated JSON files
3. git add -A && git commit -m "Rapid cycle: [ANGLE] [DEPTH] [timestamp]"
4. git push origin gh-pages
5. git checkout main

### Task 7: Morning Brief
Create output/discoveries-[timestamp]/MORNING-BRIEF.md:
1. What was the question/angle?
2. What did we find? (top 3 bullet points)
3. What surprised us?
4. What should Bill do with this? (one specific action)
5. Cost of this run
6. Suggested next cycle (angle + depth + hypothesis)

---

## VALIDATION RULES (NON-NEGOTIABLE)

1. **Never claim "verified"** unless re-analyzed with a different model or human-checked
2. **Cap confidence:** single venue = max 80%, non-random sample = max 75%, N<20 = max 60%
3. **Every finding needs a counter-argument** — if you can't think of one, the finding is too vague
4. **Price signals must cite comparables:** Sportradar ($500K-$2M/yr), StatsBomb ($50K-$200K/yr), ShotTracker ($15K/court/yr), Hudl ($200-$2K/mo)
5. **Flag venue bias on everything** — current corpus is likely 90%+ single venue (Lifetime Flower Mound)
6. **Never overwrite output/ files** — always write to new timestamped subdirectories
7. **Log all API costs** in cost-log.csv

---

## COST REFERENCE

| Operation | Cost |
|-----------|------|
| Gemini 2.5 Flash per clip | $0.0054 |
| 10 clips (deep dive) | $0.05 |
| 50 clips | $0.27 |
| 100 clips | $0.54 |
| 191 clips (current corpus) | $1.03 |
| 400 clips | $2.16 |
| Claude Sonnet per clip (est.) | $0.02-0.05 |
| ElevenLabs voice per clip | $0.01-0.03 |

Budget for this run: see --max-budget-usd in run command.

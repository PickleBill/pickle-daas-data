# Overnight Claude Code — Discovery Engine V2 + Lovable Pipeline + Design System
# Run as NEW session: claude -p "$(cat overnight-discovery-v2-lovable-pipeline.md)" --max-turns 100 --max-budget-usd 15
# Expected: 2-3 hours. ~$5-10 Gemini spend. Rest is local compute.
# Prerequisite: .env with GEMINI_API_KEY set (already there)

---

## MISSION

You are the Pickle DaaS Chief Data Scientist + Frontend Architect. Your job tonight:
1. Verify Discovery Engine V1 findings (some are suspect — see below)
2. Produce an honest V2 with proper evidence
3. Push updated data to gh-pages so the DinkData Lovable app auto-refreshes
4. Expand the dashboards significantly
5. Create a back-and-forth prompt system where you challenge your own findings

**CRITICAL CONTEXT:**
- The existing Claude Code data scientist session needs an ANTHROPIC_API_KEY to run claude-video-analyzer.py
- You do NOT need the Anthropic key for the Discovery Engine — it runs on Gemini + local Python
- If you want to use Claude API for cross-model validation, you need the key. Otherwise skip that step.
- The Anthropic API key is obtained from: console.anthropic.com → API Keys → Create Key
- If the key is not in .env, ADD THIS LINE to .env: `ANTHROPIC_API_KEY=` (leave blank, note it's needed)
- DO NOT block on the Anthropic key. Everything else works without it.

**SUPABASE IS NOW CONNECTED:**
- URL: https://yatkumnvwnnriadenafy.supabase.co
- Anon key is in .env (SUPABASE_ANON_KEY)
- Service key is EMPTY — check Supabase dashboard → Settings → API → service_role
- If you can access it, fill in SUPABASE_SERVICE_KEY in .env

---

## TASK 0: FOLDER REORGANIZATION (~5 min)

The output/ folder has 76+ items. Restructure:

```python
# Create tools/reorganize-output.py that:
# 1. Creates subdirectories: batches/, discovery/, investor/, dashboards/, player/, brand/, lovable/, voice/, tools/
# 2. Moves files by pattern (see overnight-discovery-engine-v2.md for full rules)
# 3. Renames discovery-engine/ to discovery/v1/
# 4. Creates output/INDEX.md listing every subdirectory and its purpose
# 5. Logs every move to output/REORGANIZE-LOG.md
# IMPORTANT: Never delete. Only move. Log everything.
```

---

## TASK 1: DATA QUALITY AUDIT (~10 min)

```python
# Create tools/data-quality-audit.py that:
# 1. Counts clips per source venue (from _highlight_meta or _source_url)
# 2. Counts clips per date
# 3. Identifies true duplicates (same clip UUID in multiple batches)
# 4. Flags non-random sampling issues
# Output: output/discovery/v2/data-quality-audit.json
```

---

## TASK 2: VERIFICATION RE-ANALYSIS — 20 Random Clips (~30 min, ~$0.11)

```python
# Create tools/verification-reanalysis.py that:
# 1. Picks 20 clips at random (seed=42 for reproducibility) from existing analyses
# 2. Re-sends each source video URL to Gemini 2.5 Flash with SAME prompt
# 3. Compares: brand detection agreement, shot count agreement, skill level agreement
# 4. Outputs: output/discovery/v2/verification-report.json with per-clip diffs
# This proves (or disproves) that Gemini gives consistent results
```

---

## TASK 3: DISCOVERY ENGINE V2 — HONEST VERSION (~20 min)

Run the same 5 agents (player, brand, tactical, narrative, curator) with STRICT rules:

**Honesty rules:**
- Every insight must cite specific clip UUIDs
- If sample is non-random (it is), say so explicitly
- Price signals must reference comparable companies:
  - Sportradar: $500K-$2M/year league data feeds
  - StatsBomb: $50K-$200K/year per team
  - ShotTracker: ~$15K/court/year
  - Hudl coaching: $200-$2000/month
  - Scale DaaS as fraction: "At 1/100th of Sportradar for a niche sport..."
- Note venue bias: "87% of clips from Lifetime — JOOLA is Lifetime sponsor"
- Include "strongest counter-argument" for each discovery
- Confidence caps: single venue = max 80, non-random = max 75, N<20 = max 60
- Explain "Courtana clips" = clips where Courtana branding was visible on court
- Explain "Gatorade whitespace" = absence detection, not brand recommendation

**Output:** output/discovery/v2/ (same structure as v1 but with verification metadata)

**ALSO: Self-debate mode.** After generating discoveries, run a second pass where you argue AGAINST each finding. Write this as output/discovery/v2/COUNTER-ARGUMENTS.md. For each discovery:
1. State the finding
2. Give the strongest reason it might be wrong
3. State what additional data would resolve the debate
4. Verdict: STRONG / MODERATE / WEAK

---

## TASK 4: EXPANDED DASHBOARDS V2 (~20 min)

Create TWO significantly expanded HTML dashboards:

### 4a: Discovery Dashboard V2
File: output/discovery/v2/top-discoveries-v2.html
- Dark theme (#0f1219 bg, #00E676 accent, #1e2a3a surface)
- 12+ sections (vs V1's ~6)
- NEW: Data quality section showing venue distribution + sampling bias
- NEW: Verification badge per discovery (✓ Verified / ⚠ Needs Data / ✗ Bias Flag)
- NEW: Comparable company pricing section
- NEW: Per-discovery expandable detail with clip UUIDs, counter-argument, confidence rationale
- NEW: "What We Don't Know Yet" honest gaps section
- NEW: Three-scenario revenue projection (conservative/base/aggressive)
- Chart.js: venue distribution pie, confidence histogram, scaling area chart

### 4b: Investor Demo V2
File: output/investor/investor-demo-v2.html
- Same dark theme
- Verification proof section ("We re-analyzed 20 clips — here's what matched")
- Comparable companies with real pricing
- Honest "what we know vs projecting" framing
- Revenue model with three scenarios

---

## TASK 5: PUSH TO GH-PAGES + LOVABLE DATA PIPELINE (~15 min)

This is the critical connection to Lovable. The DinkData project fetches from:
- picklebill.github.io/pickle-daas-data/corpus-export.json
- picklebill.github.io/pickle-daas-data/enriched-corpus.json
- picklebill.github.io/pickle-daas-data/dashboard-stats.json

**Do this:**

```python
# 1. Update corpus-export.json with latest data (127+ clips, all V2 fields)
# 2. Update enriched-corpus.json with enriched analysis data
# 3. Update dashboard-stats.json with V2 census numbers
# 4. CREATE NEW: discovery-export.json — all V2 discoveries with verification metadata
#    Structure:
#    {
#      "meta": { "version": "v2", "generated_at": ..., "total_clips": 127, "verification_run": true },
#      "discoveries": [ ... all ranked discoveries with confidence, counter_args, clip_uuids ... ],
#      "census": { ... full census ... },
#      "scaling": [ ... three-scenario projections ... ],
#      "data_quality": { ... audit results ... },
#      "verification": { ... re-analysis agreement rates ... }
#    }
# 5. UPDATE: creative-badges.json (if missing from gh-pages, generate it)
# 6. UPDATE: player-profiles.json (fill in avgSkills — currently empty {})
# 7. UPDATE: voice-manifest.json (fill in mp3Url if voice files exist)
#
# Then push to gh-pages:
# git checkout gh-pages
# cp output/lovable/* . (or the specific files)
# git add -A && git commit -m "V2 discovery data + expanded exports"
# git push origin gh-pages
# git checkout main
```

**IMPORTANT:** The DinkData Lovable project will auto-refresh when gh-pages updates. This is the pipeline:
Claude Code → JSON files → git push gh-pages → Lovable fetches on page load → UI updates.

---

## TASK 6: LOVABLE PROMPT EXPANSION (~10 min)

The existing DinkData project has this ecosystem context (from Bill's paste):

```
CLAUDE CODE PIPELINE
  └─ Gemini analysis → JSON files → gh-pages
       ├─ picklebill.github.io/pickle-daas-data/ (DinkData fetches here)
       └─ raw.githubusercontent.com/.../output/lovable-package/ (PickleStats Hub fetches here)

LOVABLE PROJECTS:
  ├─ DinkData (Pickle DaaS Explorer) — data intelligence product
  ├─ PickleStats Hub — player gamification, voices, broadcast
  ├─ Kings Court Coach — coaching marketplace
  └─ v1 Venue Launchpad - Peak — venue operations
```

Create TWO Lovable prompt files:

### 6a: DinkData Discovery Update Prompt
File: lovable-prompts/12-dinkdata-discovery-integration.md

This prompt tells DinkData to:
1. Fetch the NEW discovery-export.json from gh-pages
2. Add a Discovery Intelligence section to the home page
3. Show top 5 V2 discoveries with verification badges
4. Add confidence bars, counter-argument expandables
5. Add data quality section with venue distribution
6. Use the Courtana Kit A design (already in workspace knowledge)
7. Match the existing DinkData aesthetic (dark, stats-heavy, data-forward)

### 6b: Ecosystem-Wide Workspace Knowledge V2
File: lovable-prompts/WORKSPACE-KNOWLEDGE-V2.md

This is the upgraded version of lovable-workspace-knowledge.md with:
1. ALL the Kit A/Kit B design specs (already there)
2. NEW: Discovery Engine data shapes and TypeScript interfaces
3. NEW: The 4 new JSON endpoints (dashboard-stats, player-profiles, voice-manifest, creative-badges)
4. NEW: Cross-project data sharing patterns (DinkData ↔ PickleStats Hub)
5. NEW: The "impeccable design" principles:
   - Every number animates (count-up on scroll)
   - Every card has hover state + expand/collapse
   - Every empty state is designed (not blank)
   - Typography hierarchy: 3xl bold for heroes, xl semibold for section headers, mono tabular-nums for all data
   - Glow effects: shadow-[0_0_30px_rgba(0,230,118,0.15)] on accent elements
   - Skeleton loaders on ALL async fetches
   - "Designed by a senior product designer at Vercel/Linear/Stripe" as the quality bar
6. NEW: Supabase connection details (URL + anon key for wiring)
7. NEW: The ecosystem map showing how all 4 Lovable projects connect

---

## TASK 7: MULTI-MODEL EXPLORATION (OPTIONAL — only if ANTHROPIC_API_KEY exists)

If ANTHROPIC_API_KEY is set in .env:

```python
# Create tools/multi-model-validation.py
# Pick 5 clips from the verification set
# Run each through Claude 3.5 Sonnet with the same structured prompt
# Compare Claude vs Gemini outputs
# Which model detects more brands? Better skill estimates? More consistent?
# Output: output/discovery/v2/multi-model-comparison.json
```

If ANTHROPIC_API_KEY is NOT set, skip this task entirely. Log: "Skipped multi-model validation — ANTHROPIC_API_KEY not configured."

Also explore using different Gemini models:
- Gemini 2.5 Flash (current — fast, cheap, $0.0054/clip)
- Gemini 2.5 Pro (slower, more expensive, potentially better brand detection)
- Run 5 clips through Pro, compare to Flash outputs
- Output: output/discovery/v2/gemini-model-comparison.json

---

## TASK 8: MORNING BRIEF + SELF-CHALLENGE REPORT (~5 min)

```markdown
# Create output/discovery/v2/MORNING-BRIEF-V2.md
# 1. What changed V1 → V2 (honesty, verification, comparable pricing)
# 2. Top 5 discoveries that SURVIVED verification
# 3. Top 3 that WEAKENED
# 4. Data quality summary
# 5. Verification re-analysis results (agreement rates)
# 6. Counter-argument verdicts (which findings are STRONG vs WEAK)
# 7. What to show Scot/investors NOW vs AFTER more data
# 8. Lovable status: which prompts to paste, in what order
# 9. "The one thing Bill should do tomorrow" (specific, actionable)

# Create output/discovery/v2/SELF-CHALLENGE-REPORT.md
# For each top 10 discovery, a structured debate:
# - THE CLAIM: [discovery headline]
# - THE EVIDENCE: [specific clip UUIDs, data points]
# - THE COUNTER: [strongest argument against]
# - THE VERDICT: [STRONG/MODERATE/WEAK + why]
# - WHAT WOULD CHANGE MY MIND: [specific data that would flip the verdict]
# This is the "boardroom debate" Bill asked for — AI arguing with itself.
```

---

## PRIORITY ORDER

Task 0 (cleanup) → Task 1 (audit) → Task 2 (verification) → Task 3 (V2 engine) → Task 4 (dashboards) → Task 5 (gh-pages push) → Task 6 (Lovable prompts) → Task 7 (optional multi-model) → Task 8 (brief)

Tasks 0-1 MUST complete before Task 3. Task 2 can run in parallel with Task 1.
Task 5 depends on Tasks 3-4. Task 7 is optional.

---

## ENVIRONMENT NOTES

- .env has: GEMINI_API_KEY, COURTANA_TOKEN, ELEVENLABS_API_KEY, SUPABASE_URL, SUPABASE_ANON_KEY, GITHUB_TOKEN
- .env MISSING: ANTHROPIC_API_KEY (needed for claude-video-analyzer.py and Task 7)
- .env MISSING: SUPABASE_SERVICE_KEY (check Supabase dashboard → Settings → API)
- GITHUB_TOKEN is set — you CAN push to gh-pages
- All analysis scripts are in PICKLE-DAAS/ root and tools/
- Existing data: 264 analysis JSONs across multiple batches, 127 unique clips after dedup

---

## SUCCESS CRITERIA

- [ ] output/ folder reorganized with INDEX.md
- [ ] Data quality audit reveals venue distribution + sampling bias
- [ ] 20 clips re-analyzed, agreement rates measured and reported
- [ ] V2 discoveries have: clip UUIDs, counter-arguments, comparable pricing, confidence caps
- [ ] Self-challenge report with STRONG/MODERATE/WEAK verdicts
- [ ] Two expanded HTML dashboards (12+ sections each)
- [ ] gh-pages updated with V2 data (DinkData auto-refreshes)
- [ ] discovery-export.json published for Lovable consumption
- [ ] Two new Lovable prompt files (DinkData integration + Workspace Knowledge V2)
- [ ] Morning brief with clear "what to do tomorrow" action
- [ ] If ANTHROPIC_API_KEY exists: multi-model comparison
- [ ] If Gemini Pro available: model comparison

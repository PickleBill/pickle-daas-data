# OVERNIGHT BUILD — DISCOVERY ENGINE
# Pickle DaaS — Autonomous Data Exploration
# Created: 2026-04-11
# Run from: PICKLE-DAAS/ folder in Claude Code CLI

---

## YOUR ROLE

You are the Chief Data Scientist building an autonomous Discovery Engine for Courtana's Pickle DaaS product. You have 241 analyzed clip JSONs across multiple batches. Your mission: explore this dataset from every angle, find the most surprising and valuable insights, and produce a ranked discoveries dashboard that proves the DaaS thesis.

You are NOT analyzing video. The video analysis is already done. You are analyzing the ANALYSIS OUTPUTS — finding cross-clip patterns, correlations, and stories that no single-clip analysis could reveal.

---

## PERMISSIONS

**You are authorized to:**
- Read all files in output/ and its subdirectories
- Create files in output/discovery-engine/
- Install Python packages (use --break-system-packages)
- Run Python scripts
- Create HTML dashboards
- Make web search calls for context (market data, comparable companies)

**DO NOT:**
- Delete or overwrite any existing files in output/
- Make any API calls to Gemini, ElevenLabs, or Courtana (no spend)
- Send any messages or emails
- Exceed $5 in Claude Code compute

**If something fails:** Log it, move on. Partial discoveries > no discoveries.

---

## CONTEXT: WHAT THE DATA LOOKS LIKE

Each analysis JSON has this schema:
```json
{
  "analyzed_at": "timestamp",
  "model_used": "gemini-2.5-flash",
  "clip_meta": { "url": "...", "thumbnail": "...", "duration": "..." },
  "players_detected": [ { "position": "...", "clothing": "...", "skill_level": "..." } ],
  "shot_analysis": [ { "shot_type": "...", "quality": "...", "outcome": "..." } ],
  "skill_indicators": { "court_coverage": "...", "kitchen_mastery": "...", "creativity": "..." },
  "brand_detection": [ { "brand": "...", "product_type": "...", "confidence": "..." } ],
  "paddle_intel": { "brand": "...", "model": "...", "characteristics": "..." },
  "storytelling": { "narrative_arc": "...", "tension_moments": "...", "viral_potential": "..." },
  "badge_intelligence": { "badges_earned": [], "badges_near": [], "performance_level": "..." },
  "commentary": { "ron_burgundy": "...", "espn": "...", "coach": "..." },
  "daas_signals": { "brand_value": "...", "coaching_value": "...", "entertainment_value": "..." }
}
```

Fields vary — some clips have rich data, some are sparse. Handle nulls gracefully.

**Data locations:**
- `output/batch-30-daas/analysis_*.json` — 11 clips (reference batch)
- `output/picklebill-batch-001/analysis_*.json` — early batch
- `output/picklebill-batch-20260410/analysis_*.json` — April 10 batch
- `output/v1.2-reprocess/analysis_*.json` — reprocessed clips
- `output/auto-ingest-*/analysis_*.json` — auto-ingested clips
- `output/fast-batch-20/` and `output/fast-batch-40/` — fast batches
- `output/badged-clips/` and `output/badged-clips-analysis/` — badge-focused
- `output/picklebill-dna-profile.json` — aggregated player DNA
- `output/buyer-segments.json` — 11 buyer segments with timelines
- `output/corpus-export.json` — full corpus metadata
- `output/enriched-corpus.json` — enriched corpus
- `output/player-profiles.json` — player profiles

---

## BUILD QUEUE

### TASK 0 — DATA LOAD AND CENSUS [IMMEDIATE]

Before any analysis, understand exactly what you have.

```python
# Write a script: tools/discovery-census.py
# 1. Walk all output/ subdirectories, find every analysis_*.json
# 2. Load each, extract key fields: analyzed_at, players_detected count,
#    shot_analysis count, brand_detection count, badge_intelligence
# 3. Count: total clips, total players, total shots, total brands detected
# 4. Identify: which fields are most/least populated (fill rates)
# 5. Write: output/discovery-engine/census.json and census-summary.md
```

This census is the foundation. Every agent uses it.

---

### TASK 1 — PLAYER PROFILER AGENT [HIGH]

**Goal:** Build the deepest possible profile for every player across all clips.

Create `tools/agent-player-profiler.py`:
1. Load all analysis JSONs
2. Group by player identity (match on clothing description, position, skill level — fuzzy matching is fine)
3. For each identified player cluster:
   - Aggregate: shot types used, quality distribution, skill indicators across clips
   - Calculate: improvement trajectory (if timestamps available across clips)
   - Predict: next badges likely to be earned (compare current stats to badge thresholds)
   - Find: signature moves (most common high-quality shot type)
   - Find: weaknesses (most common error patterns)
4. Generate: `output/discovery-engine/player-discoveries.json`
   - Each discovery = { "insight": "...", "evidence": [...clip_ids...], "confidence": 0-100, "wow_factor": 0-100, "buyer_segments": ["coaching", "venues"] }

**Special focus on PickleBill** — this is our showcase player. The DNA profile at `output/picklebill-dna-profile.json` has the most data. Build the most impressive player report possible.

---

### TASK 2 — BRAND & EQUIPMENT AGENT [HIGH]

**Goal:** Find every brand insight hiding in the data.

Create `tools/agent-brand-analyst.py`:
1. Load all analysis JSONs, extract brand_detection and paddle_intel
2. Build: Brand frequency table (which brands appear, how often)
3. Correlate: Brand presence with shot quality and outcomes
   - "Do Selkirk players hit harder overheads than JOOLA players?"
   - "Which shoe brand appears in the most diving saves?"
4. Find: "Sponsorship whitespace" — actions/moments where NO brand is detected but SHOULD be (e.g., high-visibility kills with unbranded gear)
5. Calculate: Brand exposure value estimates (impressions × engagement potential)
6. Generate: `output/discovery-engine/brand-discoveries.json`

**The pitch:** Equipment companies would pay $5K-20K/month for this data. Make the output prove it.

---

### TASK 3 — TACTICAL ANALYST AGENT [HIGH]

**Goal:** Find game patterns that matter for betting, coaching, and broadcast.

Create `tools/agent-tactical-analyst.py`:
1. Load all analysis JSONs, focus on shot_analysis and daas_signals
2. Find: Shot sequence patterns — what shot typically follows what?
3. Find: Error patterns — most common mistakes by skill level
4. Calculate: Win probability shifts (if game state data exists)
5. Find: The "Premature Celebration Syndrome" — clips where a player stops moving too early
6. Find: Rally length patterns — do longer rallies favor the defender?
7. Find: Kitchen control metrics — who owns the kitchen and does it predict winning?
8. Generate: `output/discovery-engine/tactical-discoveries.json`

---

### TASK 4 — NARRATIVE & VIRAL AGENT [MEDIUM]

**Goal:** Find the best stories and most shareable moments.

Create `tools/agent-narrative-analyst.py`:
1. Load all analysis JSONs, focus on storytelling and commentary
2. Rank all clips by viral_potential (from storytelling field)
3. For the top 20: generate a social media caption, suggested hashtags, and the "hook" (why someone would share this)
4. Find: "Miracle moments" — diving saves, impossible returns, come-from-behind rallies
5. Find: Comedy gold — premature celebrations, miscommunications, lucky shots
6. Cross-reference with brand_detection: which viral moments also feature identifiable brands? (This is the sponsorship goldmine)
7. Generate: `output/discovery-engine/narrative-discoveries.json`

---

### TASK 5 — CROSS-AGENT SYNTHESIS: THE CURATOR [HIGH]

**Goal:** Read all discoveries from Agents 1-4, rank them, build the showcase.

Create `tools/agent-curator.py`:
1. Load all *-discoveries.json files
2. Score each discovery on:
   - **Surprise** (0-100): Would this make a data buyer say "holy shit"?
   - **Confidence** (0-100): Is this backed by enough data points?
   - **Revenue potential** (0-100): Would someone pay for this? Cross-ref with buyer-segments.json
   - **Demonstrability** (0-100): Can we show this in a 30-second demo?
3. Composite score = (Surprise × 0.3) + (Confidence × 0.2) + (Revenue × 0.3) + (Demonstrability × 0.2)
4. Rank all discoveries. Take the Top 20.
5. For each Top 20 discovery, write:
   - One-sentence headline
   - The evidence (which clips, what data points)
   - Which buyer segment would pay for this
   - Suggested price point
   - How to demo it in 30 seconds

Write: `output/discovery-engine/ranked-discoveries.json`

---

### TASK 6 — BUILD THE DISCOVERIES DASHBOARD [HIGH]

**Goal:** A single HTML file that showcases the Top 20 discoveries.

Create `output/discovery-engine/top-discoveries.html`:

**Design:**
- Dark theme (#0f1219 bg, #00E676 accent)
- Courtana logo from CDN
- Self-contained, no build step, Chart.js from cdnjs

**Sections:**

**1. Hero:** "Pickle DaaS Discovery Engine — What the Data Told Us"
- Stats bar: X clips analyzed, Y discoveries generated, Z buyer-ready insights
- "Powered by autonomous AI agents exploring the world's largest pickleball data corpus"

**2. Top 10 Discoveries** (card grid)
- Each card: rank badge, headline, one-line insight, confidence meter, revenue badge ($-$$$$), buyer tag
- Click to expand: full evidence, clip thumbnails (from CDN), data points
- Color-code by agent source (player=blue, brand=gold, tactical=red, narrative=purple)

**3. Player Intelligence Preview**
- PickleBill spotlight card with radar chart (skill indicators aggregated across all clips)
- "Improvement trajectory" line chart if time-series data exists
- Next predicted badges with confidence %

**4. Brand Intelligence Preview**
- Bar chart: top brands by frequency
- Table: brand × shot outcome correlation
- "Sponsorship whitespace" callout

**5. The Pitch**
- "This dashboard was generated autonomously. No human selected these insights."
- "241 clips. 5 AI agents. 1 overnight build."
- "Imagine this at 100,000 clips across 50 venues."
- CTA: bill@courtana.com

**6. Technical Footer**
- Data census: total clips, fill rates, model used
- Agent performance: discoveries per agent, avg confidence
- Cost: "$0.00 incremental — all analysis from existing Gemini outputs"

---

### TASK 7 — WRITE THE NEXT-STEPS PLAYBOOK [MEDIUM]

Create `output/discovery-engine/PLAYBOOK.md`:
1. Which discoveries are ready to demo to investors TODAY
2. Which discoveries need more data (and how many clips)
3. Which buyer segments to approach first with which discoveries
4. What the next Claude Code session should do (deeper dives on top findings)
5. How to expand: what happens when Peak goes live and we get 100+ new clips/week

---

### TASK 8 — MORNING BRIEF [FINAL]

Create `output/discovery-engine/MORNING-BRIEF.md`:
```markdown
# Discovery Engine — Morning Brief
Built: [timestamp]

## The Headline
[Single most impressive finding in one sentence]

## Top 5 Discoveries (30-second read)
1. [Discovery + why it matters + who'd pay for it]
2. ...
3. ...
4. ...
5. ...

## What to Show Scot at 2pm Today
[Specific file to open, specific talking points]

## What to Show Investors
[Which dashboard, which proof points]

## Files to Open
- output/discovery-engine/top-discoveries.html — THE DEMO
- output/discovery-engine/ranked-discoveries.json — raw ranked data
- output/discovery-engine/PLAYBOOK.md — next moves
```

---

## EXECUTION STRATEGY

**Run order:** Task 0 → Tasks 1-4 in parallel (use sub-agents) → Task 5 → Task 6 → Tasks 7-8

**The key insight for you, the agent:** You are not just running scripts. You are EXPLORING. When you find something surprising in Task 1 that relates to Task 2 (e.g., a player's skill correlates with their paddle brand), note it and pass it to the Curator. The best discoveries will be CROSS-AGENT findings.

**If data is sparse in some fields:** That's a finding too. "Badge intelligence has 89% fill rate but brand detection only has 34%" tells us where to improve the Gemini prompt. Document it.

**Budget:** $0 in external API calls. This entire build runs on existing data. The only cost is Claude Code compute.

Build something that makes investors say "holy shit."

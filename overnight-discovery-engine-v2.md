# Overnight Claude Code Prompt — Discovery Engine V2 + Verification + Folder Cleanup
# Run: claude -p "$(cat overnight-discovery-engine-v2.md)" --max-turns 80 --max-budget-usd 10
# Expected: 3-4 hours, mostly local compute, $2-5 Gemini spend on re-analysis
# Prerequisite: .env with GEMINI_API_KEY set

---

## CONTEXT

Discovery Engine V1 ran on April 11, 2026 and produced 21 discoveries from 127 clips.
Bill has flagged that several discoveries need verification — specifically:
- JOOLA dominance may be an artifact of Lifetime venue data (most clips are from Lifetime)
- "Courtana clips avg 7.43/10" — what is a "Courtana clip"? This needs explanation.
- Price signals ($5K, $8K/month) have no sourcing — need comparable market data
- DUPR predictions (3.5-4.0 modal) need to explain methodology
- Gatorade as "unowned category" — where did this come from?
- Sample is non-random (single venue, selected clips, not sequential)

This overnight build has 6 tasks:

---

## TASK 0: FOLDER ARCHITECTURE CLEANUP (~5 min)

The output/ folder has 76+ items and is unwieldy. Restructure:

```bash
# Create organized subdirectory structure
mkdir -p output/batches/       # All batch analysis folders go here
mkdir -p output/discovery/     # Discovery Engine runs (versioned)
mkdir -p output/investor/      # Investor-facing materials
mkdir -p output/dashboards/    # HTML dashboards
mkdir -p output/player/        # Player profiles and DNA files
mkdir -p output/brand/         # Brand reports
mkdir -p output/lovable/       # Lovable-ready data exports
mkdir -p output/voice/         # Voice commentary MP3s
mkdir -p output/tools/         # Cost logs, measurement outputs
```

Then move existing files:
```python
# Create tools/reorganize-output.py
# Rules:
# - batch-* and auto-ingest-* and picklebill-batch-* folders → output/batches/
# - discovery-engine/ → output/discovery/v1/ (rename, don't overwrite)
# - *investor* files → output/investor/
# - *.html dashboards → output/dashboards/
# - player profiles (picklebill-dna-*, picklebill-intel-*) → output/player/
# - brand-intelligence-* → output/brand/
# - lovable-package/ → output/lovable/
# - voice-commentary/ → output/voice/
# - cost-* and *.csv → output/tools/
# - LEAVE corpus-export.json and buyer-segments.json at output/ root (they're referenced by gh-pages)
# - Create output/INDEX.md listing every subdirectory and its purpose
# - Log every move to output/REORGANIZE-LOG.md with timestamps
```

IMPORTANT: Do NOT delete anything. Only move. Log every operation.

---

## TASK 1: DATA QUALITY AUDIT (~10 min)

Before running new analysis, audit what we actually have.

```python
# Create tools/data-quality-audit.py
# For every analysis JSON in output/batches/:
# 1. Extract source venue (from _highlight_meta or _source_url — look for venue identifiers)
# 2. Extract timestamp (analyzed_at)
# 3. Count: how many clips per venue? per date? per batch?
# 4. Check: are the "127 unique clips" truly unique? (some may be same video re-analyzed)
# 5. Check: what is the actual clip selection process? Random? Sequential? Cherry-picked?
# 6. Flag: which insights from V1 depend on a non-representative sample?
#
# Output: output/discovery/v2/data-quality-audit.json with:
# {
#   venue_distribution: { "Lifetime Flower Mound": 87, "unknown": 40 },
#   temporal_distribution: { "2025-05": 12, "2025-06": 45, ... },
#   duplicate_clips: [ list of clip UUIDs that appear in multiple batches ],
#   selection_bias_flags: [ "87% of clips from single venue", ... ],
#   recommendation: "Next batch should target: Peak venue clips, random sampling, date diversity"
# }
```

---

## TASK 2: VERIFICATION RE-ANALYSIS — 20 Random Clips (~30 min, ~$0.10)

Pick 20 clips that we have EXISTING Gemini analysis for. Re-analyze them with the SAME prompt.
Compare: do we get the same brands, shots, skill levels, badges?

```python
# Create tools/verification-reanalysis.py
# 1. Load all analysis JSONs from output/batches/
# 2. Pick 20 at random (truly random — use random.sample with seed=42 for reproducibility)
# 3. For each, re-send the source video URL to Gemini 2.5 Flash with the SAME prompt version
# 4. Compare original vs re-analysis:
#    - Brand detection: same brands? Any new/missing?
#    - Shot count: within ±20%?
#    - Skill level estimate: same category?
#    - DUPR estimate: within ±0.5?
# 5. Output: output/discovery/v2/verification-report.json
# {
#   clips_tested: 20,
#   brand_agreement_rate: 0.85,  // % of brands that match
#   shot_count_agreement: 0.90,  // % within ±20%
#   skill_level_agreement: 0.75, // % exact match
#   dupr_agreement: 0.70,        // % within ±0.5
#   per_clip_results: [ ... detailed comparison per clip ... ],
#   conclusion: "Brand detection is reliable (85%+). Skill estimates are stable. DUPR needs calibration."
# }
```

---

## TASK 3: DISCOVERY ENGINE V2 — HONEST VERSION (~20 min)

Run the same 5 agents but with STRICT honesty rules:

```python
# Create tools/discovery-engine-v2.py
# Same 5 agents (player, brand, tactical, narrative, curator) but with new rules:
#
# RULE 1: Every insight must cite specific clip UUIDs (not just counts)
# RULE 2: If sample is non-random, say so explicitly in the insight
# RULE 3: Price signals must come from comparable market data, not estimation
#         - Use these REAL comparables:
#           - Sportradar: $500K-$2M/year for league-level data feeds
#           - StatsBomb: $50K-$200K/year for team subscriptions
#           - ShotTracker: $15K/court/year for venue analytics
#           - Hudl: $200-$2000/month for coaching analytics
#         - Scale Pickle DaaS pricing as a fraction (smaller sport, earlier stage)
#         - Show the math: "At 1/100th of Sportradar pricing for a niche sport..."
# RULE 4: For brand findings, note venue bias ("87% of clips from Lifetime —
#         JOOLA is a Lifetime sponsor, so dominance may be venue-specific")
# RULE 5: For each discovery, include "strongest counter-argument"
# RULE 6: Confidence scores must reflect sample limitations
#         - Single venue = max confidence 80 regardless of N
#         - Non-random sample = max confidence 75
#         - N < 20 = max confidence 60
# RULE 7: "Courtana clips" → explain: clips where "Courtana" brand was detected
#         (Courtana logo visible on court/screen). NOT a product category.
# RULE 8: Gatorade/BODYARMOR whitespace → explain methodology: these are product
#         categories that AI identified as ABSENT, not detected. The AI was prompted
#         to look for common sports brands and flagged zero matches.
#
# Output: output/discovery/v2/ (all files follow V1 structure but with verification metadata)
```

---

## TASK 4: EXPANDED DASHBOARDS — V2 of Both (~15 min)

Create significantly expanded versions of the investor demo and discovery dashboard:

```python
# Create output/discovery/v2/top-discoveries-v2.html
# Same dark theme (bg #0f1219, accent #00E676, surface #1e2a3a)
# But EXPANDED with:
# 1. Data Quality section at the top showing venue distribution + sample bias flags
# 2. Verification badge on each discovery (✓ Verified, ⚠ Needs More Data, ✗ Sampling Bias)
# 3. Comparable company pricing section (not just our estimates)
# 4. Per-discovery expandable section showing: source clip UUIDs, counter-argument, confidence rationale
# 5. "What We Don't Know Yet" section — honest about gaps
# 6. Chart.js: venue distribution pie chart, confidence distribution histogram
# 7. Scaling projection with pessimistic/optimistic/base scenarios
# 8. Total section count: 12+ (significantly more than V1's ~6)

# Create output/investor/investor-demo-v2.html  
# Same dark theme but with:
# 1. Verification proof section ("We re-analyzed 20 clips — here's what matched")
# 2. Comparable companies with real pricing data
# 3. Honest "what we know vs what we're projecting" framing
# 4. Revenue model with three scenarios (conservative/base/aggressive)
```

---

## TASK 5: LOVABLE DATA EXPORT (~5 min)

Prepare a clean data package that Lovable can consume:

```python
# Create output/lovable/discovery-v2-export.json
# Structure matches corpus-export.json schema for compatibility
# But adds Discovery Engine findings as a separate top-level key
# {
#   "meta": { "generated_at": ..., "version": "v2", "clips_analyzed": 127, ... },
#   "corpus": [ ... existing corpus-export.json data ... ],
#   "discoveries": [ ... V2 discoveries with verification metadata ... ],
#   "census": { ... census data ... },
#   "scaling": [ ... scaling projections ... ],
#   "verification": { ... verification report summary ... },
#   "data_quality": { ... audit results ... }
# }
#
# Also create output/lovable/LOVABLE-DATA-README.md explaining:
# - How to import this into a Lovable project
# - Which fields map to which UI components
# - How to swap from hardcoded to Supabase
```

---

## TASK 6: MORNING BRIEF + HANDOFF (~5 min)

```markdown
# Create output/discovery/v2/MORNING-BRIEF-V2.md
# Include:
# 1. What changed from V1 → V2 (honesty upgrades, verification results)
# 2. Top 5 discoveries that SURVIVED verification (these are the real ones)
# 3. Top 3 discoveries that WEAKENED after verification (be honest)
# 4. Data quality summary (venue bias, sample limitations)
# 5. What to show Scot / investors now vs after we get more data
# 6. Next steps: "Run this on Peak venue clips as soon as they're available"
# 7. Lovable prompt 11 is ready to paste — here's the order

# Create output/discovery/v2/HANDOFF-TO-LOVABLE.md
# Clear instructions for Bill:
# 1. Open Lovable, create new project "pickle-daas-discovery"
# 2. Paste workspace knowledge from BILL-OS/lovable-workspace-knowledge.md
# 3. Paste contents of lovable-prompts/11-discovery-intelligence-dashboard.md
# 4. After build: swap hardcoded data with output/lovable/discovery-v2-export.json
# 5. Connect Supabase when instance is ready
```

---

## PRIORITY ORDER

Task 0 (cleanup) → Task 1 (audit) → Task 2 (verification) → Task 3 (V2 engine) → Task 4 (dashboards) → Task 5 (Lovable export) → Task 6 (brief)

Tasks 0 and 1 MUST complete before Task 3. Task 2 can run in parallel with Task 1.

---

## SUCCESS CRITERIA

- [ ] output/ folder reorganized with INDEX.md
- [ ] Data quality audit reveals actual venue distribution and sampling bias
- [ ] 20 clips re-analyzed, agreement rates measured
- [ ] V2 discoveries have: clip UUIDs, counter-arguments, comparable pricing, confidence caps
- [ ] Two expanded HTML dashboards (discovery + investor)
- [ ] Lovable-ready JSON export
- [ ] Honest morning brief distinguishing strong vs weak findings

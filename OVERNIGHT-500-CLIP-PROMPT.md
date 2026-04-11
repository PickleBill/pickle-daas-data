# Claude Code Overnight Prompt — 500-Clip Corpus Expansion + Pipeline Hardening
_Paste this into Claude Code CLI. Run from the PICKLE-DAAS directory._
_Estimated runtime: 3-5 hours. Estimated cost: ~$3 Gemini API._

---

## CONTEXT

You are running the Pickle DaaS pipeline. Read `CLAUDE.md` in this directory for full technical context.

The pipeline analyzes Courtana pickleball highlight videos using Gemini 2.5 Flash and produces structured JSON intelligence (shot analysis, brand detection, player DNA, badges, commentary).

**Current state:** 92 clips analyzed. 8,214 available in the API. We're expanding to ~590 clips tonight.

**CRITICAL RULES:**
- Never use `api.courtana.com` — always `courtana.com`
- Never follow the `next` pagination field — construct `?page=N&page_size=100` manually
- Always set `Accept: application/json` header
- Never overwrite existing output files — always write to new dated subdirs
- All API keys are in `.env` — never hardcode

---

## TASK SEQUENCE

### Step 1: Run 500-Clip Auto-Ingest (may already be running)

Check if the batch is already running:
```bash
ps aux | grep auto-ingest | grep -v grep
tail -5 output/batch-500-run-20260411.log
```

If NOT running, start it:
```bash
python tools/auto-ingest.py --count 500 --warehouse
```

Wait for completion. This will:
- Fetch 500 new clips from the Courtana anon endpoint
- Skip already-analyzed clips (dedup)
- Skip clips > 20MB (full match recordings)
- Analyze each through Gemini 2.5 Flash Lite
- Save individual analysis JSONs to `output/auto-ingest-YYYYMMDD-HHMM/`
- Generate a batch summary
- Run the badge warehouse to update cross-references

### Step 2: Aggregate and Export

After the batch completes:

```bash
# Aggregate player DNA profiles for all players found
python aggregate-player-dna.py "output/**/batch_summary_*.json"

# Generate brand intelligence report
python brand-intelligence-report.py "output/**/batch_summary_*.json"

# Prepare data for Lovable frontend
python prepare-lovable-data.py
```

### Step 3: Publish to GitHub Pages

The Lovable app (courtana-pulse) fetches data from `picklebill.github.io/pickle-daas-data/`. Update these files:

```bash
cd /path/to/pickle-daas-data  # or clone: git clone https://github.com/PickleBill/pickle-daas-data.git

# Update corpus-export.json with all analyzed clips
# Update enriched-corpus.json with player-enriched clips
# Add creative-badges.json (currently missing from gh-pages)
# Add player-profiles.json (currently missing from gh-pages)
# Add dashboard-stats.json with:
#   { "total_clips_analyzed": N, "total_clips_available": 8214, 
#     "unique_brands": N, "unique_players": N, "avg_quality": N,
#     "cost_per_clip": 0.0054, "pipeline_version": "v1.2",
#     "last_updated": "ISO timestamp" }

git add -A && git commit -m "Corpus expansion: N clips analyzed" && git push
```

### Step 4: Generate Brand-Specific Reports

For the top detected brands, generate individual intelligence reports:

```bash
python brand-intelligence-report.py "output/**/analysis_*.json" --brand JOOLA --output output/brand-reports/
python brand-intelligence-report.py "output/**/analysis_*.json" --brand "LIFE TIME" --output output/brand-reports/
python brand-intelligence-report.py "output/**/analysis_*.json" --brand "Recovery Cave" --output output/brand-reports/
```

### Step 5: Summary Report

Write a summary to `output/overnight-run-summary-20260411.md` with:
- Total clips analyzed (old + new)
- Clips skipped (too large, errors)
- New brands discovered
- New players identified  
- Top 5 clips by quality score
- Cost summary (total Gemini API spend estimate)
- Any errors encountered

---

## IF ERRORS OCCUR

- **Gemini 503/429:** The analyzer has built-in retry with exponential backoff. If persistent, the model cascade falls back to flash-lite.
- **COURTANA_TOKEN expired:** The anon endpoint doesn't need auth. If auth endpoints fail, note it and continue with anon.
- **Disk space:** Each analysis JSON is ~5KB. 500 clips = ~2.5MB. Not a concern.
- **Network timeout:** The analyzer has 30s timeout per download. Large clips (>20MB) are skipped automatically.

---

## SUCCESS CRITERIA

- [ ] 400+ new clips analyzed (some will be >20MB skips)
- [ ] `corpus-export.json` updated on gh-pages with full dataset
- [ ] `creative-badges.json` published to gh-pages
- [ ] Brand intelligence reports for top 3 brands generated
- [ ] Player DNA profiles aggregated for all detected players
- [ ] Summary report written

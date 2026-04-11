# Overnight Mega-Ingest — Phase 2 Corpus Expansion
# Run: claude -p "$(cat overnight-phase2-mega-ingest.md)" --max-turns 200 --max-budget-usd 15
# Expected: 3-5 hours. ~$2-4 Gemini. Corpus target: 250+ unique clips.

---

## MISSION

You are the Pickle DaaS Pipeline Engineer. Your job tonight:
1. Expand the corpus from ~46 to 250+ unique clips
2. After each batch, rebuild corpus-export.json with REAL skill data
3. Push updated data to gh-pages after every batch
4. Track costs and errors

## ENVIRONMENT

- .env has: GEMINI_API_KEY, COURTANA_TOKEN, GITHUB_TOKEN, ANTHROPIC_API_KEY
- NEVER use `api.courtana.com` — use `courtana.com`
- ALWAYS set `Accept: application/json` header
- NEVER use the `next` field from API responses — construct `?page=N&page_size=100` manually
- Gemini rate limit: ~10 RPM for video. Use 15s between clips minimum.
- Cost target: $0.0054/clip × 200 clips = ~$1.08 Gemini spend

## EXECUTION PLAN

### Phase 1: Fetch clip inventory (5 min)
```bash
cd "/Users/billbricker/PickleBill Dropbox/PickleBill Team Folder/Claude Projects/PICKLE-DAAS"
```

1. Fetch pages 1-10 from `https://courtana.com/app/anon-highlight-groups/?page_size=100&page=N`
2. Extract all video URLs and UUIDs
3. Cross-reference against existing `output/**/analysis_*.json` files — identify UNANALYZED clips
4. Save list to `output/mega-ingest-candidates.json`

### Phase 2: Batch analysis (2-3 hours)
Run `tools/auto-ingest.py --count 50` in batches:
- After each batch of 50, run `python3 tools/push-to-ghpages.py` to update live data
- Track: clips analyzed, errors, cost
- If Gemini rate limits: back off 60s and retry
- Target: 5 batches × 50 clips = 250 total

### Phase 3: Rebuild everything (10 min)
1. Run `python3 tools/push-to-ghpages.py` final push
2. Count total unique clips in corpus
3. Save cost summary to `output/SPEND-LOG.md`

### Phase 4: Morning brief (5 min)
Create `output/MORNING-BRIEF-MEGA-INGEST.md` with:
- Total clips before/after
- New brands discovered
- Cost summary
- Any errors or issues
- What changed in gh-pages

## CRITICAL RULES
- NEVER block on errors. Log and skip.
- NEVER use `api.courtana.com`
- After every 50 clips, push to gh-pages
- If Gemini returns 429/503: wait 60s, retry 3x, then skip clip
- Total budget: $15 max (most is Gemini credits)

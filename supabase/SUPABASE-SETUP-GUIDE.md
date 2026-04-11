# Supabase Setup Guide — Pickle DaaS
**Time to complete: ~15 minutes**
**Last updated: 2026-04-10**

---

## Overview

Once this is set up, the Pickle DaaS pipeline can push all Gemini analysis data directly to Supabase, making it available to your Lovable apps via the Supabase JS client.

```
Gemini Analysis → Python push script → Supabase DB → Lovable app (via supabase-js)
```

---

## Step 1: Create Supabase Project (2 min)

1. Go to [supabase.com](https://supabase.com) → New Project
2. Settings:
   - **Name:** `pickle-daas`
   - **Database Password:** Save this somewhere safe
   - **Region:** US East (lowest latency for Courtana API)
3. Wait ~2 minutes for project to initialize
4. Once ready, go to **Project Settings → API**
5. Copy these values into your `.env` file:

```env
SUPABASE_URL=https://YOUR_PROJECT_ID.supabase.co
SUPABASE_ANON_KEY=eyJ...   (labeled "anon / public")
SUPABASE_SERVICE_KEY=eyJ... (labeled "service_role" — keep secret!)
```

---

## Step 2: Run the Schema (3 min)

1. In Supabase Dashboard → **SQL Editor** → **New Query**
2. Paste the contents of `../supabase-schema.sql`
3. Click **Run**
4. Verify: go to **Table Editor** — you should see `pickle_daas_analyses`, `pickle_daas_brands`, `pickle_daas_players` tables

**Quick schema verify command:**
```sql
SELECT table_name FROM information_schema.tables 
WHERE table_schema = 'public' ORDER BY table_name;
```
Expected output: 3+ tables starting with `pickle_daas_`

> ⚠️ The schema uses `CREATE TABLE IF NOT EXISTS` — safe to run multiple times.

---

## Step 3: Add DUPR Enrichment Columns (Optional, 1 min)

Run this in SQL Editor to enable DUPR rating enrichment:
```sql
ALTER TABLE pickle_daas_players ADD COLUMN IF NOT EXISTS dupr_id VARCHAR(50);
ALTER TABLE pickle_daas_players ADD COLUMN IF NOT EXISTS dupr_rating_singles DECIMAL(3,2);
ALTER TABLE pickle_daas_players ADD COLUMN IF NOT EXISTS dupr_rating_doubles DECIMAL(3,2);
ALTER TABLE pickle_daas_players ADD COLUMN IF NOT EXISTS dupr_verified_at TIMESTAMP;
ALTER TABLE pickle_daas_players ADD COLUMN IF NOT EXISTS tournament_wins INTEGER DEFAULT 0;
ALTER TABLE pickle_daas_players ADD COLUMN IF NOT EXISTS tournament_matches INTEGER DEFAULT 0;
```

---

## Step 4: Push Existing Analysis Data (3 min)

From the PICKLE-DAAS directory:

```bash
# Install supabase python client if needed
pip install supabase --break-system-packages

# Set your credentials
export SUPABASE_URL="https://YOUR_PROJECT_ID.supabase.co"
export SUPABASE_SERVICE_KEY="your_service_role_key"

# Push all analyses from tonight's batch
python supabase/push-analysis-to-db.py output/picklebill-batch-20260410/

# Push historical batch
python supabase/push-analysis-to-db.py output/batch-30-daas/

# Push original batch
python supabase/push-analysis-to-db.py output/picklebill-batch-001/
```

**Expected output:**
```
Pushing 20 analyses to Supabase...
✅ analysis_597f6bf5... pushed (clip quality: 8)
✅ analysis_e7340a11... pushed (clip quality: 7)
...
Done: 20/20 pushed, 0 errors
```

---

## Step 5: Verify in Dashboard (2 min)

1. Go to **Table Editor → pickle_daas_analyses**
2. You should see rows with:
   - `clip_quality_score` values (7-8)
   - `commentary_ron_burgundy` text
   - `brands_detected` JSON arrays
3. Run a quick query to confirm data quality:
```sql
SELECT 
  clip_quality_score,
  story_arc,
  clip_summary,
  jsonb_array_length(brands_detected) as brand_count
FROM pickle_daas_analyses 
ORDER BY clip_quality_score DESC 
LIMIT 5;
```

---

## Step 6: Connect to Lovable (2 min)

In your Lovable project:
1. Go to **Settings → Environment Variables**
2. Add:
   - `VITE_SUPABASE_URL` = your Supabase URL
   - `VITE_SUPABASE_ANON_KEY` = your anon key (public-safe)
3. In your Lovable app, install supabase-js:
   - Ask Lovable: "Install @supabase/supabase-js and create a supabase client at lib/supabase.ts"

---

## Current Schema: Tables

| Table | Purpose | Rows Expected |
|-------|---------|---------------|
| `pickle_daas_analyses` | One row per Gemini analysis | 15 today → 4,097 eventually |
| `pickle_daas_brands` | Brand detection records | Multiple per analysis |
| `pickle_daas_players` | Player profiles + DNA | 25 initially |

---

## Useful Queries

```sql
-- Top clips by quality
SELECT clip_summary, clip_quality_score, viral_potential_score, story_arc
FROM pickle_daas_analyses
ORDER BY clip_quality_score DESC, viral_potential_score DESC
LIMIT 10;

-- Brand frequency
SELECT brand_name, COUNT(*) as clip_count
FROM pickle_daas_brands
GROUP BY brand_name
ORDER BY clip_count DESC;

-- Clips by story arc
SELECT story_arc, COUNT(*) as count, AVG(clip_quality_score) as avg_quality
FROM pickle_daas_analyses
GROUP BY story_arc;
```

---

## Notes & Gotchas

- **`api.courtana.com` DOES NOT EXIST** — it's NXDOMAIN. Always use `courtana.com` with relative paths
- The anonymous clip endpoint needs NO auth: `https://courtana.com/app/anon-highlight-groups/?page_size=100`
- Pagination bug: construct page URLs manually (`?page=N&page_size=100`), do NOT follow the `next` field (port 433 bug)
- COURTANA_TOKEN is needed only for private user data (profiles, leaderboard) — not for clip URLs
- Service role key has FULL database access — never expose in frontend code. Use anon key in Lovable.

---

## Estimated Costs (Supabase Free Tier)

| Limit | Free Tier | Needed Today |
|-------|-----------|--------------|
| DB rows | 500M | ~50K max |
| Storage | 1 GB | ~10 MB |
| API calls | 2M/month | ~10K/month |
| Realtime connections | 200 | 5-10 |

**Free tier is sufficient until hundreds of venues are live.** Upgrade to Pro ($25/month) only when needed.

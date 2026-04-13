# Pickle DaaS — Supabase Query Cookbook
_Learn to query your own data. Every question you'd want to ask, with the SQL to answer it._

---

## How to Run These Queries

**Option 1: Supabase Dashboard (easiest)**
1. Go to https://supabase.com/dashboard/project/vlcjaftwnllfjyckjchg/sql
2. Paste any query below into the SQL Editor
3. Click **Run** (or ⌘+Enter)

**Option 2: The `data-lab.html` page (coming next)**
Point-and-click. Preset question buttons. No SQL knowledge needed.

**Option 3: Python** — `python3 tools/run-query.py "SELECT ..."`

---

## Your Data (What's In Supabase)

| Table | Rows | What it holds |
|-------|------|---------------|
| `pickle_daas_analyses` | 403 | Every analyzed clip — quality, viral score, commentary, skills |
| `pickle_daas_brands` | 41 | Every brand detected — JOOLA, Nike, Selkirk, etc. with appearance counts |
| `pickle_daas_players` | 0 | _Not created yet — needs SQL setup (bottom of this doc)_ |

**Key columns in `pickle_daas_analyses`:**
- `video_url` — the clip's CDN URL
- `clip_quality_score`, `viral_potential_score`, `watchability_score` (1-10)
- `story_arc` — e.g., "grind_rally", "clutch_moment", "athletic_highlight"
- `brands_detected` — JSON array of brand objects
- `skill_indicators` — JSON with 9-dimension player skills
- `commentary_espn`, `commentary_social_caption`, `commentary_ron_burgundy` — AI-generated text
- `analyzed_at` — timestamp

---

## The 15 Essential Queries

### 1. 📊 "How many clips have we analyzed?"
```sql
SELECT COUNT(*) AS total_clips
FROM pickle_daas_analyses;
```
**Expected:** `403`

---

### 2. 📅 "How many clips were analyzed in the last 24 hours?"
```sql
SELECT COUNT(*) AS clips_last_24h
FROM pickle_daas_analyses
WHERE analyzed_at > NOW() - INTERVAL '24 hours';
```
**Expected:** Varies — shows pipeline activity.

---

### 3. 🏷️ "Show me the top 10 brands"
```sql
SELECT brand_name, total_appearances, total_clips_seen_in
FROM pickle_daas_brands
ORDER BY total_appearances DESC
LIMIT 10;
```
**Expected:** JOOLA (162), Nike (24), Joola (9), PICKLEBALL (6), Franklin (5), etc.
**Insight:** JOOLA dominates — worth reaching out to them with a partnership pitch.

---

### 4. 💎 "What are the 10 highest-quality clips?"
```sql
SELECT 
  video_url, 
  clip_quality_score, 
  viral_potential_score, 
  story_arc,
  clip_summary
FROM pickle_daas_analyses
WHERE clip_quality_score IS NOT NULL
ORDER BY clip_quality_score DESC, viral_potential_score DESC
LIMIT 10;
```
**Use for:** Picking the best clips for an investor demo.

---

### 5. 🔥 "Which clips are most likely to go viral?"
```sql
SELECT 
  video_url,
  viral_potential_score,
  clip_quality_score,
  story_arc,
  commentary_social_caption
FROM pickle_daas_analyses
WHERE viral_potential_score >= 8
ORDER BY viral_potential_score DESC, clip_quality_score DESC
LIMIT 20;
```
**Use for:** Social media content calendar.

---

### 6. 📖 "What story arcs does our corpus tell?"
```sql
SELECT 
  story_arc, 
  COUNT(*) AS clip_count,
  ROUND(AVG(clip_quality_score)::numeric, 2) AS avg_quality,
  ROUND(AVG(viral_potential_score)::numeric, 2) AS avg_viral
FROM pickle_daas_analyses
WHERE story_arc IS NOT NULL AND story_arc != ''
GROUP BY story_arc
ORDER BY clip_count DESC;
```
**Insight:** Which story types produce the best content? If `clutch_moment` has highest avg viral but lowest count, we need to capture more of those.

---

### 7. 🎯 "JOOLA brand report — clips featuring JOOLA paddles"
```sql
SELECT 
  video_url,
  clip_quality_score,
  viral_potential_score,
  story_arc
FROM pickle_daas_analyses
WHERE brands_detected::text ILIKE '%JOOLA%' OR brands_detected::text ILIKE '%Joola%'
ORDER BY clip_quality_score DESC
LIMIT 20;
```
**Use for:** Generating a brand-specific highlight reel.

---

### 8. 💪 "Find the elite players — high kitchen mastery AND high quality clips"
```sql
SELECT 
  video_url,
  (skill_indicators->>'kitchen_mastery_rating')::int AS kitchen,
  (skill_indicators->>'consistency_rating')::int AS consistency,
  (skill_indicators->>'court_iq_rating')::int AS court_iq,
  clip_quality_score,
  story_arc
FROM pickle_daas_analyses
WHERE (skill_indicators->>'kitchen_mastery_rating')::int >= 8
  AND clip_quality_score >= 7
ORDER BY (skill_indicators->>'kitchen_mastery_rating')::int DESC, clip_quality_score DESC
LIMIT 25;
```
**Insight:** These are the clips that prove our AI can identify "advanced" play.

---

### 9. 📈 "Average skill scores across the entire corpus"
```sql
SELECT 
  ROUND(AVG((skill_indicators->>'kitchen_mastery_rating')::numeric), 2) AS avg_kitchen,
  ROUND(AVG((skill_indicators->>'court_coverage_rating')::numeric), 2) AS avg_court_coverage,
  ROUND(AVG((skill_indicators->>'power_game_rating')::numeric), 2) AS avg_power,
  ROUND(AVG((skill_indicators->>'touch_and_feel_rating')::numeric), 2) AS avg_touch,
  ROUND(AVG((skill_indicators->>'athleticism_rating')::numeric), 2) AS avg_athleticism,
  ROUND(AVG((skill_indicators->>'creativity_rating')::numeric), 2) AS avg_creativity,
  ROUND(AVG((skill_indicators->>'court_iq_rating')::numeric), 2) AS avg_court_iq,
  ROUND(AVG((skill_indicators->>'consistency_rating')::numeric), 2) AS avg_consistency,
  ROUND(AVG((skill_indicators->>'composure_under_pressure')::numeric), 2) AS avg_composure
FROM pickle_daas_analyses
WHERE skill_indicators IS NOT NULL;
```
**Insight:** Tells you what skill profile the average Courtana player has.

---

### 10. 🎨 "Quality distribution — how many clips at each score"
```sql
SELECT 
  clip_quality_score, 
  COUNT(*) AS clip_count
FROM pickle_daas_analyses
WHERE clip_quality_score IS NOT NULL
GROUP BY clip_quality_score
ORDER BY clip_quality_score DESC;
```
**Use for:** Understanding whether most clips are boring (5-6) or great (8-9).

---

### 11. 🗓️ "Daily ingest trend — clips analyzed per day"
```sql
SELECT 
  DATE(analyzed_at) AS day, 
  COUNT(*) AS clips_analyzed
FROM pickle_daas_analyses
WHERE analyzed_at IS NOT NULL
GROUP BY DATE(analyzed_at)
ORDER BY day DESC
LIMIT 14;
```
**Use for:** Seeing if the pipeline is working consistently.

---

### 12. 🤖 "Show me a random high-quality clip for social posting"
```sql
SELECT 
  video_url,
  clip_quality_score,
  viral_potential_score,
  commentary_social_caption,
  commentary_ron_burgundy
FROM pickle_daas_analyses
WHERE clip_quality_score >= 8 AND viral_potential_score >= 6
ORDER BY RANDOM()
LIMIT 1;
```
**Use for:** "Give me a clip to post right now."

---

### 13. 🏆 "Best clip per story arc (the highlight reel)"
```sql
SELECT DISTINCT ON (story_arc)
  story_arc,
  video_url,
  clip_quality_score,
  viral_potential_score,
  clip_summary
FROM pickle_daas_analyses
WHERE story_arc IS NOT NULL AND story_arc != ''
ORDER BY story_arc, clip_quality_score DESC, viral_potential_score DESC;
```
**Use for:** Auto-generating a "Best of" montage covering all arc types.

---

### 14. ⚡ "Quality vs Viral correlation — does higher quality mean more viral?"
```sql
SELECT 
  clip_quality_score,
  ROUND(AVG(viral_potential_score)::numeric, 2) AS avg_viral_at_this_quality,
  COUNT(*) AS sample_size
FROM pickle_daas_analyses
WHERE clip_quality_score IS NOT NULL AND viral_potential_score IS NOT NULL
GROUP BY clip_quality_score
ORDER BY clip_quality_score DESC;
```
**Insight:** If avg_viral doesn't increase with quality, it means our quality score isn't predicting viral — an interesting finding.

---

### 15. 🔍 "Search clips by commentary text"
```sql
SELECT 
  video_url,
  clip_quality_score,
  commentary_espn
FROM pickle_daas_analyses
WHERE commentary_espn ILIKE '%speed up%'  -- or 'dink', 'overhead', 'net cord', etc.
ORDER BY clip_quality_score DESC
LIMIT 10;
```
**Use for:** Finding specific moments ("show me all the net-cord winners").

---

## Setting Up the Players Table

The players table doesn't exist yet. Paste this into the Supabase SQL Editor once, then `tools/sync-to-supabase.py --players` will populate it:

```sql
CREATE TABLE IF NOT EXISTS pickle_daas_players (
    id BIGSERIAL PRIMARY KEY,
    username TEXT UNIQUE NOT NULL,
    display_name TEXT,
    clip_count INTEGER DEFAULT 0,
    avg_quality NUMERIC(3,1),
    avg_viral NUMERIC(3,1),
    top_skill TEXT,
    play_style TEXT,
    brands_used TEXT[],
    first_seen TIMESTAMPTZ,
    last_seen TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_players_username ON pickle_daas_players(username);
CREATE INDEX IF NOT EXISTS idx_players_clip_count ON pickle_daas_players(clip_count DESC);
```

---

## The "I Don't Know SQL" Cheat Sheet

| I want to... | Run this query number |
|--------------|----------------------|
| See how much data we have | #1 |
| Check pipeline health | #2, #11 |
| Pick clips for investor demo | #4 |
| Post on social media | #5, #12 |
| Understand our brand partnerships | #3, #7 |
| Prove we can identify advanced players | #8 |
| Understand our corpus | #6, #9, #10 |
| Build a highlight reel | #13 |
| Test a hypothesis | #14 |
| Find specific moments | #15 |

---

## What to Do Next

1. **Try 3 queries in the Supabase dashboard** — pick any from above
2. **Open `data-lab.html`** (once built) — same queries, one-click buttons
3. **Save your favorites** — Supabase dashboard lets you save queries
4. **Ask new questions** — if you think of a question, ask me to write the SQL for it

Every question has an answer hiding in 403 clips of data. This is your database now.

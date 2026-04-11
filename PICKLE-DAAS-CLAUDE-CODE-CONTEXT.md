# PICKLE DaaS — Claude Code Master Context
_Last updated: 2026-03-28. Read this before doing anything in this project._

---

## The Big Picture

**"What would you do with the world's largest corpus of sports data of all time?"**

That's the closing slide of the Courtana pitch deck. Pickle DaaS is how we prove it.

Courtana already has 4,097 highlight groups, 25+ players, live video at cdn.courtana.com, and a real production API. The system below turns that raw corpus into structured intelligence — automatically, at scale.

**Bill Bricker** (PickleBill) is the proof-of-concept subject:
- Global Rank: #1 on the leaderboard
- XP: 283,950 (Level 17, Gold III)
- Badges: 82 earned
- Most highlights of any player in the system

---

## System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     PICKLE DaaS PIPELINE                        │
│                                                                 │
│  Courtana API          Gemini 2.5 Flash        Supabase         │
│  (live data)    →→→    (perception layer) →→→  (DaaS store)     │
│  - highlight URLs      - video analysis        - analyses table │
│  - player profiles     - brand detection       - player_dna     │
│  - badge history       - shot extraction       - badge_intel    │
│  - match data          - commentary gen        - brand_registry │
│                                                                 │
│                              ↓↓↓                                │
│                    Claude Code (you)                            │
│                    (reasoning + build layer)                    │
│                    - aggregates patterns                        │
│                    - evolves Gemini prompts                     │
│                    - builds API endpoints                       │
│                    - writes Lovable-ready data                  │
│                              ↓↓↓                                │
│                    Lovable (demo UI layer)                      │
│                    - PickleBill Intelligence Dashboard          │
│                    - Court Kings demo suite                     │
│                    - Investor pitch interactives                │
└─────────────────────────────────────────────────────────────────┘
```

---

## Production Stack Reference

### Courtana API
- Base URL: `https://api.courtana.com/private-api/v1/`
- Auth: `Authorization: Bearer <token>` (JWT from courtana.com localStorage)
- Key endpoints:
  - `GET /accounts/profiles/current/` — current user profile
  - `GET /accounts/profiles/action_get_leaderboard/` — global leaderboard
  - `GET /app/highlight-groups/?page_size=N` — paginated highlight list
  - `GET /app/highlights/model_choices/?filters=type` — highlight type enum
  - `GET /app/facilities/` — venue list
  - `GET /app/matches/?status=in_progress&displayed=true` — live matches

### CDN Asset Patterns
- Video: `https://cdn.courtana.com/files/production/u/{user-uuid}/{asset-uuid}.mp4`
- Thumbnail: `https://cdn.courtana.com/files/production/u/{user-uuid}/{asset-uuid}.jpeg`
- Logo: `https://cdn.courtana.com/assets/logos/fulllogo-dark-transparent-grad.svg`
- CDN is **public** — no auth required to fetch. Link directly.

### PickleBill (Bill Bricker) Account Data
- Username: `PickleBill`
- Global Rank: #1
- XP: 283,950 | Level 17 | Gold III
- Badges: 82 total (2 Platinum, 20+ Gold, 260+ Bronze)
- Top Gold Badges: Epic Rally ×38, Highlight Reel ×17, Tag Team Takedown ×16
- Avatar: `https://cdn.courtana.com/files/production/u/a3c7e1d0-4b2f-4a8e-9f1c-6d5e8b3a2c1f/7d873c1f-ec81-487a-8fe7-97bdb94a6397.png`

### Highlight Object Structure (from API)
```json
{
  "id": "UUID",
  "random_id": "string",
  "name": "Epic Rally #427",
  "type": "standard|ai_analysis|ai|panel|full_match",
  "file": "https://cdn.courtana.com/.../clip.mp4",
  "thumbnail_file": "https://cdn.courtana.com/.../thumb.jpeg",
  "ai_analyzed": true,
  "duration": 18,
  "view_count": 42,
  "participants": [{"id": "UUID", "username": "PickleBill", "level": 17, "avatar_url": "..."}],
  "analysis_data": {"shots": [...], "critical_moments": [...], "player_stats": {...}},
  "created_at": "2026-03-26T..."
}
```

---

## Supabase Schema (Build This First)

```sql
-- Main analysis results table
CREATE TABLE pickle_daas_analyses (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  analyzed_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  highlight_id TEXT,
  highlight_name TEXT,
  video_url TEXT,

  -- Top-level scores (for fast queries/sorting)
  clip_quality_score NUMERIC,
  viral_potential_score NUMERIC,
  watchability_score NUMERIC,
  cinematic_score NUMERIC,

  -- Structured extractions (JSONB for flexibility)
  brands_detected JSONB DEFAULT '[]',
  predicted_badges JSONB DEFAULT '[]',
  play_style_tags JSONB DEFAULT '[]',
  shot_analysis JSONB DEFAULT '{}',
  skill_indicators JSONB DEFAULT '{}',
  storytelling JSONB DEFAULT '{}',

  -- Commentary fields (denormalized for easy UI access)
  commentary_espn TEXT,
  commentary_hype TEXT,
  commentary_social_caption TEXT,
  commentary_hashtags JSONB DEFAULT '[]',
  commentary_ron_burgundy TEXT,
  commentary_chuck_norris TEXT,
  commentary_tts_clean TEXT,  -- for ElevenLabs/voice API

  -- Discovery
  clip_summary TEXT,
  search_tags JSONB DEFAULT '[]',
  story_arc TEXT,
  highlight_category TEXT,

  -- Full raw output (source of truth)
  full_analysis JSONB NOT NULL,

  -- Batch context
  batch_id TEXT,
  clip_rank_in_batch INTEGER,

  created_at TIMESTAMPTZ DEFAULT now()
);

-- Brand registry (aggregated across all clips)
CREATE TABLE pickle_daas_brands (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  brand_name TEXT NOT NULL,
  category TEXT,
  total_appearances INTEGER DEFAULT 0,
  player_usernames JSONB DEFAULT '[]',
  clips_seen_in JSONB DEFAULT '[]',
  last_seen_at TIMESTAMPTZ,
  UNIQUE(brand_name, category)
);

-- Player DNA (aggregated per player across all clips)
CREATE TABLE pickle_daas_player_dna (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  player_username TEXT UNIQUE NOT NULL,
  clips_analyzed INTEGER DEFAULT 0,
  avg_quality_score NUMERIC,
  avg_viral_score NUMERIC,
  dominant_shot_type TEXT,
  play_style_tags JSONB DEFAULT '[]',
  skill_aggregate JSONB DEFAULT '{}',
  signature_moves JSONB DEFAULT '[]',
  brands_worn JSONB DEFAULT '[]',
  top_badges JSONB DEFAULT '[]',
  last_updated TIMESTAMPTZ DEFAULT now()
);

-- Indexes for common queries
CREATE INDEX idx_analyses_highlight_id ON pickle_daas_analyses(highlight_id);
CREATE INDEX idx_analyses_quality ON pickle_daas_analyses(clip_quality_score DESC);
CREATE INDEX idx_analyses_viral ON pickle_daas_analyses(viral_potential_score DESC);
CREATE INDEX idx_analyses_story_arc ON pickle_daas_analyses(story_arc);
CREATE INDEX idx_brands_name ON pickle_daas_brands(brand_name);
```

---

## Experiment Backlog — Prioritized

### TIER 1: Build These Now (High Impact, Closes Deals)

---

**EXP-001: PickleBill Player DNA Dashboard**
- What: Lovable app showing PickleBill's real highlights, shot tendencies, badge timeline, quality scores over time
- Data: Pull top 20 highlights from Courtana API → display real thumbnails → link to CDN videos
- Demo value: This IS the Court Kings pitch. Show it to Rich + Bryan.
- Tech: Lovable → `GET /app/highlight-groups/` → live data
- Effort: Medium | Impact: 🔥🔥🔥

**EXP-002: Cross-Highlight Aggregated Insights for PickleBill**
- What: Run 20 PickleBill highlights through Gemini → aggregate: what brands does he wear? What's his signature move? What badge does he earn most? What's his court IQ rating across clips?
- Output: Player DNA JSON profile + readable summary
- Tech: `pickle-daas-gemini-analyzer.py --courtana-token X --player PickleBill --limit 20`
- Effort: Low (script exists) | Impact: 🔥🔥🔥

**EXP-003: Brand Detection Registry**
- What: Run 50+ clips through Gemini brand detection → build table: which brands appear most? Who wears what?
- Output: Brand frequency table, player-brand associations
- Demo value: Sponsorship pitch — "We know exactly who's wearing Selkirk vs JOOLA vs HEAD"
- Effort: Medium | Impact: 🔥🔥🔥

**EXP-004: Court Kings Demo Pack Generator**
- What: Auto-generate a player intelligence report for ANY player at Court Kings using their video
- Output: Branded PDF/page with player DNA, badge predictions, shot analysis
- Demo value: Walk into the Court Kings meeting with their players already analyzed
- Effort: High | Impact: 🔥🔥🔥🔥

---

### TIER 2: Wow Factor / Viral Potential

---

**EXP-005: Ron Burgundy / Voice Announcer Pipeline**
- What: Gemini analyzes clip → generates `commentary_tts_clean` text → ElevenLabs (or Google TTS) speaks it in Ron Burgundy / ESPN / Chuck Norris voice → FFmpeg merges audio with original video → output is a NEW video file with custom commentary
- API to use: ElevenLabs `/v1/text-to-speech/{voice_id}` — they have Ron Burgundy-adjacent voices
- Output: `.mp4` with commentary audio track
- Demo value: Absolutely insane demo moment. Play it at Court Kings meeting.
- Tech stack: `pickle-daas-gemini-analyzer.py` → `commentary_tts_clean` field → ElevenLabs → FFmpeg
- Effort: Medium | Impact: 🔥🔥🔥🔥🔥 (viral)

**EXP-006: Highlight Marketability Ranker**
- What: Run a batch → sort by `viral_potential_score` → surface the top 10 most shareable clips automatically
- Output: Ranked list with captions + hashtags pre-written
- Demo value: "We know which of your 4,097 highlights to post this week"
- Effort: Low (uses existing script) | Impact: 🔥🔥🔥

**EXP-007: Auto-Tagging Pipeline (All 4,097 Highlights)**
- What: Background job — run every highlight through Gemini, store structured tags in Supabase
- Output: Every highlight is now searchable by shot type, brand, story arc, badge type, player style
- Demo value: "Search 'erne machine' and every erne in our corpus shows up"
- Effort: High (time + API cost) | Impact: 🔥🔥🔥🔥 (foundational)

**EXP-008: "What Happened" Natural Language Search**
- What: Gemini generates `clip_summary_one_sentence` for every clip → store in Supabase → expose as semantic search
- Output: Type "clutch comeback at the kitchen" → 12 matching highlights
- Effort: Medium | Impact: 🔥🔥🔥🔥

---

### TIER 3: Product Depth / Coaching Layer

---

**EXP-009: Badge Prediction Engine**
- What: Before a badge fires in the system, Gemini predicts from video what badge is coming → validate against actual badges awarded
- Output: Model accuracy score + "badges we're missing" list
- Demo value: "We can award badges before humans review them"
- Effort: Medium | Impact: 🔥🔥

**EXP-010: Coaching Insight Generator**
- What: Aggregate PickleBill's last 20 highlights → Claude synthesizes: "Here are 3 things to work on to reach Platinum"
- Output: Personalized coaching report
- Demo value: The self-serve AI coach product David and Cedric are building
- Effort: Low (pure prompt engineering) | Impact: 🔥🔥🔥

**EXP-011: Opponent Scouting Report**
- What: Given a player username → pull their last 10 highlights → Gemini extracts tendencies → Claude writes a "how to beat them" scouting report
- Output: Player scouting card
- Demo value: Coaching tool for competitive players
- Effort: Medium | Impact: 🔥🔥🔥

**EXP-012: Player XP Predictor**
- What: Correlate Gemini quality scores with actual XP awarded → build a regression model → predict XP from video analysis alone
- Output: "This rally is worth approximately 850 XP"
- Effort: High | Impact: 🔥🔥

**EXP-013: Shot Chart / Heat Map Builder**
- What: Gemini extracts `player_position` for every shot → aggregate per player → build court heat map
- Output: Visual heat map showing where PickleBill wins/loses from different court zones
- Tech: Python matplotlib or Lovable SVG overlay
- Effort: Medium | Impact: 🔥🔥🔥

---

### TIER 4: Big Swings / Future Bets

---

**EXP-014: Multi-Language Commentary**
- What: Same clip → commentary in English, Spanish, Portuguese — for international venue expansion
- Tech: Gemini generates, ElevenLabs speaks, FFmpeg merges
- Effort: Low (extend EXP-005) | Impact: 🔥🔥

**EXP-015: Auto-Highlight from Badge Trigger**
- What: When badge fires in Courtana → automatically run Gemini analysis on triggering clip → if confirmed → auto-generate social post with caption + hashtags
- Tech: Courtana webhook → Lambda/Supabase Edge Function → Gemini → output
- Effort: High | Impact: 🔥🔥🔥🔥 (automation)

**EXP-016: Cross-Player Style Comparison**
- What: PickleBill vs. Chintan vs. Coach_Block — side-by-side DNA comparison
- Output: Radar chart showing skill dimensions per player
- Demo value: "We have player comps like basketball analytics"
- Effort: Medium | Impact: 🔥🔥🔥

**EXP-017: DUPR Rating Estimator**
- What: Gemini estimates DUPR range from video → compare to actual DUPR if available → train a predictor
- Output: "Based on 10 clips, this player is approximately 4.0-4.5 DUPR"
- Effort: High | Impact: 🔥🔥🔥 (partnerships with DUPR)

**EXP-018: The Gemini Prompt Evolution Loop**
- What: Claude Code evaluates quality of Gemini outputs batch-over-batch → identifies weak fields (e.g., `brands_detected` empty too often) → rewrites the ANALYSIS_PROMPT → re-runs on same clips → diffs outputs → accepts improvement
- This is the AIs-working-together loop. Fully automated prompt versioning.
- Output: Versioned prompts with quality scores per field per version
- Effort: High | Impact: 🔥🔥🔥🔥🔥 (this is the DaaS moat)

---

## Lovable → Courtana Real API Connection Pattern

### The Problem
Lovable apps currently hardcode data. This makes demos fake and iteration slow.

### The Solution: Courtana API Proxy via Supabase Edge Function

```typescript
// Supabase Edge Function: courtana-proxy
// Deploy at: supabase/functions/courtana-proxy/index.ts

import { serve } from "https://deno.land/std@0.168.0/http/server.ts"

const COURTANA_API = "https://api.courtana.com/private-api/v1"
const COURTANA_TOKEN = Deno.env.get("COURTANA_TOKEN") // Set in Supabase secrets

serve(async (req) => {
  const url = new URL(req.url)
  const endpoint = url.searchParams.get("endpoint")

  if (!endpoint) {
    return new Response(JSON.stringify({ error: "endpoint required" }), { status: 400 })
  }

  const response = await fetch(`${COURTANA_API}${endpoint}`, {
    headers: { "Authorization": `Bearer ${COURTANA_TOKEN}` }
  })

  const data = await response.json()

  return new Response(JSON.stringify(data), {
    headers: {
      "Content-Type": "application/json",
      "Access-Control-Allow-Origin": "*"  // Lovable needs this
    }
  })
})
```

### Lovable Prompt to Wire This Up
```
Connect this app to live Courtana data using our Supabase Edge Function proxy.

Supabase URL: [YOUR_SUPABASE_URL]
Edge function: courtana-proxy

To fetch highlight groups:
  GET {SUPABASE_URL}/functions/v1/courtana-proxy?endpoint=/app/highlight-groups/?page_size=20

To fetch the leaderboard:
  GET {SUPABASE_URL}/functions/v1/courtana-proxy?endpoint=/accounts/profiles/action_get_leaderboard/

Replace ALL hardcoded/mock data with live API calls.
Show loading states while fetching.
Handle errors gracefully with a retry button.

This gives us real PickleBill data: rank #1, 283,950 XP, Level 17, 82 badges,
real highlight thumbnails from cdn.courtana.com, real CDN video URLs.
```

---

## Gemini Prompt Evolution Log

| Version | Date | Key Changes | Quality Delta |
|---------|------|-------------|---------------|
| v1.0 | 2026-03-28 | Initial prompt, all fields | Baseline |
| — | — | — | — |

_Claude Code should update this table each time ANALYSIS_PROMPT changes._

---

## Files in This Folder

| File | Purpose |
|------|---------|
| `pickle-daas-gemini-analyzer.py` | Main analysis script — run on any highlight URL or batch |
| `PICKLE-DAAS-CLAUDE-CODE-CONTEXT.md` | THIS FILE — read first |
| `output/` | Local JSON results from analysis runs |
| `prompts/` | Versioned Gemini prompt history |

---

## Quick Start for Claude Code

```bash
# Install dependencies
pip install google-generativeai requests

# Set env vars
export GEMINI_API_KEY="your_key_here"
export COURTANA_TOKEN="jwt_from_courtana_localstorage"

# Test on one highlight
python pickle-daas-gemini-analyzer.py \
  --url "https://cdn.courtana.com/files/production/u/01915c59-9bb7-4683-bd53-e28bddcae12e/ce00696b-9f9b-465a-971c-dbf1334e556c.mp4"

# Run on PickleBill's top 20 highlights from live API
python pickle-daas-gemini-analyzer.py \
  --courtana-token "$COURTANA_TOKEN" \
  --player PickleBill \
  --limit 20 \
  --output-dir ./output/picklebill-run-001

# With Supabase push
python pickle-daas-gemini-analyzer.py \
  --courtana-token "$COURTANA_TOKEN" \
  --player PickleBill \
  --limit 20 \
  --supabase
```

---

## Next Claude Code Tasks (in order)

1. **Run EXP-002**: Execute the analyzer on 5 PickleBill highlights, review output quality
2. **Create Supabase schema**: Run the SQL above in Supabase dashboard, then test a push
3. **Build Lovable proxy**: Deploy the Edge Function, verify CORS, test from browser
4. **Wire EXP-001**: Build the PickleBill dashboard in Lovable against live data
5. **Start EXP-005**: ElevenLabs integration — `commentary_tts_clean` → voice → FFmpeg merge
6. **Begin EXP-018**: Prompt evolution loop — evaluate field coverage on first 5 results

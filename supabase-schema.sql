-- =============================================================================
-- PICKLE DaaS — Supabase Schema
-- Run this in: Supabase Dashboard → SQL Editor
-- All tables use CREATE TABLE IF NOT EXISTS so it's safe to re-run.
-- =============================================================================

-- ---------------------------------------------------------------------------
-- TABLE: pickle_daas_analyses
-- One row per Gemini analysis run on a single highlight clip.
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS pickle_daas_analyses (
  id                        UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  analyzed_at               TIMESTAMPTZ NOT NULL DEFAULT now(),

  -- Source clip info
  highlight_id              TEXT,                       -- Courtana highlight UUID or random_id
  highlight_name            TEXT,                       -- Human-readable clip name (e.g. "Epic Rally #427")
  video_url                 TEXT,                       -- Full CDN URL of the analyzed video

  -- Top-level scores (indexed for fast sorting/filtering)
  clip_quality_score        NUMERIC,                    -- 1-10: combined production + play quality
  viral_potential_score     NUMERIC,                    -- 1-10: social shareability estimate
  watchability_score        NUMERIC,                    -- 1-10: would someone rewatch this?
  cinematic_score           NUMERIC,                    -- 1-10: camera angle, lighting, framing

  -- Structured extractions (JSONB for schema flexibility)
  brands_detected           JSONB DEFAULT '[]',         -- Array of brand detection objects
  predicted_badges          JSONB DEFAULT '[]',         -- Array of badge prediction objects
  play_style_tags           JSONB DEFAULT '[]',         -- Player style tags (e.g. "kitchen specialist")
  shot_analysis             JSONB DEFAULT '{}',         -- Full shot breakdown array + dominance
  skill_indicators          JSONB DEFAULT '{}',         -- Skill ratings (court coverage, kitchen mastery, etc.)
  storytelling              JSONB DEFAULT '{}',         -- Story arc, emotional tone, defining moment
  daas_signals              JSONB DEFAULT '{}',         -- Category, search tags, content use cases, DUPR estimate

  -- Commentary fields (denormalized for direct UI access without JSON parsing)
  commentary_espn           TEXT,                       -- ESPN broadcast style 2-3 sentences
  commentary_hype           TEXT,                       -- High-energy TNT/NBA style
  commentary_social_caption TEXT,                       -- Instagram/TikTok caption (<100 chars)
  commentary_hashtags       JSONB DEFAULT '[]',         -- Array of hashtag strings
  commentary_ron_burgundy   TEXT,                       -- Ron Burgundy voice commentary
  commentary_chuck_norris   TEXT,                       -- Chuck Norris third-person line
  commentary_tts_clean      TEXT,                       -- Clean text optimized for ElevenLabs TTS

  -- Discovery & search
  clip_summary              TEXT,                       -- One sentence: what happened factually
  search_tags               JSONB DEFAULT '[]',         -- 10-15 searchable tags for semantic search
  story_arc                 TEXT,                       -- e.g. "clutch_moment", "comeback", "dominant_performance"
  highlight_category        TEXT,                       -- e.g. "top_play", "teaching_moment", "funny"

  -- Full raw Gemini output (source of truth, never lose data)
  full_analysis             JSONB NOT NULL,             -- Complete Gemini response JSON

  -- Batch tracking
  batch_id                  TEXT,                       -- Group ID for runs (e.g. "picklebill-batch-001")
  clip_rank_in_batch        INTEGER,                    -- 1 = best in batch by quality score

  created_at                TIMESTAMPTZ DEFAULT now()
);

-- Indexes for common query patterns
CREATE INDEX IF NOT EXISTS idx_analyses_highlight_id   ON pickle_daas_analyses(highlight_id);
CREATE INDEX IF NOT EXISTS idx_analyses_quality        ON pickle_daas_analyses(clip_quality_score DESC);
CREATE INDEX IF NOT EXISTS idx_analyses_viral          ON pickle_daas_analyses(viral_potential_score DESC);
CREATE INDEX IF NOT EXISTS idx_analyses_story_arc      ON pickle_daas_analyses(story_arc);
CREATE INDEX IF NOT EXISTS idx_analyses_batch_id       ON pickle_daas_analyses(batch_id);
CREATE INDEX IF NOT EXISTS idx_analyses_highlight_cat  ON pickle_daas_analyses(highlight_category);
CREATE INDEX IF NOT EXISTS idx_analyses_analyzed_at    ON pickle_daas_analyses(analyzed_at DESC);

-- JSONB indexes for brand and tag queries
CREATE INDEX IF NOT EXISTS idx_analyses_brands_gin     ON pickle_daas_analyses USING GIN (brands_detected);
CREATE INDEX IF NOT EXISTS idx_analyses_tags_gin       ON pickle_daas_analyses USING GIN (search_tags);
CREATE INDEX IF NOT EXISTS idx_analyses_badges_gin     ON pickle_daas_analyses USING GIN (predicted_badges);


-- ---------------------------------------------------------------------------
-- TABLE: pickle_daas_brands
-- Aggregated brand registry — updated after each batch run.
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS pickle_daas_brands (
  id                        UUID PRIMARY KEY DEFAULT gen_random_uuid(),

  brand_name                TEXT NOT NULL,              -- e.g. "Selkirk", "JOOLA", "HEAD"
  category                  TEXT,                       -- paddle|shoes|apparel_top|apparel_bottom|hat|other

  -- Frequency data
  total_appearances         INTEGER DEFAULT 0,          -- Total times detected across all clips
  total_clips_seen_in       INTEGER DEFAULT 0,          -- Distinct clips this brand appeared in

  -- Player associations
  player_usernames          JSONB DEFAULT '[]',         -- Array of player usernames who wear/use this brand

  -- Clip references
  clips_seen_in             JSONB DEFAULT '[]',         -- Array of highlight_ids where brand appeared

  -- Detection metadata
  avg_confidence            TEXT,                       -- "high"|"medium"|"low" aggregated
  last_seen_at              TIMESTAMPTZ,                -- Most recent detection timestamp

  UNIQUE(brand_name, category)
);

CREATE INDEX IF NOT EXISTS idx_brands_name             ON pickle_daas_brands(brand_name);
CREATE INDEX IF NOT EXISTS idx_brands_category         ON pickle_daas_brands(category);
CREATE INDEX IF NOT EXISTS idx_brands_appearances      ON pickle_daas_brands(total_appearances DESC);


-- ---------------------------------------------------------------------------
-- TABLE: pickle_daas_player_dna
-- Aggregated player profile — one row per player, updated after each batch.
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS pickle_daas_player_dna (
  id                        UUID PRIMARY KEY DEFAULT gen_random_uuid(),

  player_username           TEXT UNIQUE NOT NULL,       -- Courtana username (e.g. "PickleBill")

  -- Summary stats
  clips_analyzed            INTEGER DEFAULT 0,          -- Total clips processed
  avg_quality_score         NUMERIC,                    -- Mean clip_quality_score across all clips
  avg_viral_score           NUMERIC,                    -- Mean viral_potential_score

  -- Playing style
  dominant_shot_type        TEXT,                       -- Most frequent shot type across clips
  play_style_tags           JSONB DEFAULT '[]',         -- Union of all style tags, sorted by frequency
  signature_moves           JSONB DEFAULT '[]',         -- Notable recurring moves detected

  -- Skill aggregates (averages of each skill_indicator field)
  skill_aggregate           JSONB DEFAULT '{}',         -- {court_coverage: 8.1, kitchen_mastery: 9.2, ...}

  -- Brand associations
  brands_worn               JSONB DEFAULT '[]',         -- [{brand_name, category, count}, ...]

  -- Badge intelligence
  top_badges                JSONB DEFAULT '[]',         -- Most predicted badges + confidence

  -- Best/worst clips
  top_clips                 JSONB DEFAULT '[]',         -- Top 5 by quality score with URL + caption
  coaching_notes            JSONB DEFAULT '[]',         -- Aggregated improvement opportunities

  last_updated              TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_player_dna_username     ON pickle_daas_player_dna(player_username);
CREATE INDEX IF NOT EXISTS idx_player_dna_quality      ON pickle_daas_player_dna(avg_quality_score DESC);

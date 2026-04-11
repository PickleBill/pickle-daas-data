# Pickle DaaS — Phase 2 Lovable Handoff
_Generated: April 11, 2026_

---

## What Changed in gh-pages (picklebill.github.io/pickle-daas-data/)

| File | Before | After | What Changed |
|------|--------|-------|-------------|
| `corpus-export.json` | 96 clips, skills all 0 | **190 clips, skills populated** | 2x more clips, ALL 10 skill dimensions filled (was a bug) |
| `dashboard-stats.json` | 96 clips, stale counts | **190 clips, 27 brands, 6 players** | Real-time census numbers |
| `player-profiles.json` | 6 players, avgSkills: `{}` | **6 players, avgSkills filled** | Kitchen Mastery, Court IQ, etc. now have real values |
| `enriched-corpus.json` | 96 clips, minimal | **190 clips, full analysis data** | Skills, commentary, paddle intel all included |
| `creative-badges.json` | ~40 badges | **52 unique badges with reasoning** | Expanded from larger corpus |
| `voice-manifest.json` | 5 entries | Same | No change |
| `brand-report.json` | **NEW** | **27 brands** | Brand frequency, visibility seconds, co-occurrence, avg quality |

---

## NEW Data Available (Not Yet on gh-pages)

| File | Location | What It Is |
|------|----------|-----------|
| `output/multi-model/fused_*.json` (15 files) | Local | Claude Sonnet strategic analysis layered on top of Gemini data |
| `output/discovery/camera-analysis.json` | Local | Camera quality, indoor/outdoor, crowd presence across 35 clips |
| `output/discovery/match-context.json` | Local | Multi-clip match groupings, skill progression within matches |

---

## Supabase is LIVE

- **URL:** `https://vlcjaftwnllfjyckjchg.supabase.co`
- **Tables:** `pickle_daas_analyses` (30 rows), `pickle_daas_brands`, `pickle_daas_player_dna`
- **Anon Key:** Get from Supabase Dashboard → Settings → API → `anon` / `public`

### Lovable Integration
In Lovable project settings, add these environment variables:
```
VITE_SUPABASE_URL=https://vlcjaftwnllfjyckjchg.supabase.co
VITE_SUPABASE_ANON_KEY=<get from Settings → API>
```

Then ask Lovable:
> "Install @supabase/supabase-js and create a supabase client at lib/supabase.ts using the env vars VITE_SUPABASE_URL and VITE_SUPABASE_ANON_KEY"

---

## TypeScript Interfaces for New Data Shapes

```typescript
// corpus-export.json
interface Clip {
  uuid: string;
  video_url: string;
  thumbnail: string;
  quality: number;        // 1-10
  viral: number;          // 1-10
  watchability: number;   // 1-10
  arc: string;            // "grind_rally", "clutch_moment", etc.
  summary: string;
  dominant_shot: string;
  total_shots: number;
  brands: string[];
  badges: string[];
  ron_burgundy: string;
  social_caption: string;
  skills: {
    court_coverage: number;  // 1-10 (FIXED — was 0)
    kitchen: number;
    power: number;
    touch: number;
    athleticism: number;
    creativity: number;
    court_iq: number;
    consistency: number;
    composure: number;
    paddle_control: number;
  };
  model: string;
}

// player-profiles.json
interface PlayerProfile {
  username: string;
  clips_analyzed: number;
  avgQuality: number;
  avgViral: number;
  avgSkills: Record<string, number>;  // "Kitchen Mastery": 8.2, etc. (FIXED — was empty)
  topBrands: Array<{ brand: string; count: number }>;
  topBadges: Array<{ badge: string; count: number }>;
  playStyleTags: string[];
  signatureMove: string;
}

// brand-report.json (NEW)
interface BrandReport {
  brand_name: string;
  total_appearances: number;
  categories: Record<string, number>;  // "paddle": 45, "net": 12
  avg_quality: number;
  avg_viral: number;
  total_visibility_seconds: number;
  confidence_breakdown: Record<string, number>;
  co_occurring_brands: Array<{ brand: string; count: number }>;
}

// dashboard-stats.json
interface DashboardStats {
  total_clips: number;
  avg_quality: number;
  avg_viral: number;
  unique_brands: number;
  unique_players: number;
  top_brands: Array<{ brand: string; count: number }>;
  top_players: Array<{ player: string; count: number }>;
  story_arcs: Record<string, number>;
  shot_types: Record<string, number>;
  cost_per_clip: number;
  generated_at: string;
}

// Multi-model fused output (future gh-pages addition)
interface FusedAnalysis {
  gemini: object;         // Full Gemini analysis
  claude: {
    strategic_narrative: string;
    content_strategy: {
      platform_recommendation: string;
      hook_text: string;
      reframed_viral_score: number;
    };
    skill_reframe: {
      psychological_dimensions: Record<string, number>;
      archetype_label: string;  // "The Siege Engineer", etc.
    };
    brand_intelligence: {
      strategic_insight: string;
      sellable_report_title: string;
      estimated_brand_value_usd: number;
    };
    coaching_narrative: string;
    investor_proof_point: string;
    novel_metric_detected: {
      metric_name: string;
      metric_value: string;
      why_novel: string;
    };
  };
  _source_url: string;
}
```

---

## DinkData Pages That Need Updating

| Page | What to Update | Data Source |
|------|---------------|------------|
| **Main Dashboard** | Clip count (96 → 190), skill radar should now work | `dashboard-stats.json`, `corpus-export.json` |
| **Data Explorer** | Refresh with 190 clips, filter by skills | `corpus-export.json` (skills now populated) |
| **Player Profiles** | Skill radars actually render now (avgSkills was `{}`) | `player-profiles.json` |
| **Brand Intelligence** | Use new `brand-report.json` for richer brand data | `brand-report.json` (NEW) |
| **Discovery/Insights** | Add multi-model insights if Claude data available | `fused_*.json` files |

---

## Suggested Lovable Prompts

### Prompt: Fix Skill Radars
> "The player skill radar charts should now work — the data at picklebill.github.io/pickle-daas-data/player-profiles.json now has avgSkills populated with real values like {Kitchen Mastery: 8.2, Court Coverage: 7.1, ...}. Update the radar chart component to render these values. Fall back to empty state if avgSkills is empty."

### Prompt: Add Brand Intelligence Page
> "Create a new /brands page that fetches brand-report.json from our gh-pages endpoint. Show: (1) horizontal bar chart of top 15 brands by appearances, (2) per-brand cards with avg quality score, visibility seconds, and category breakdown, (3) a 'Sponsorship Whitespace' section listing brands not yet detected (Gatorade, Nike, Under Armour, Lululemon). Use the dark Boardroom theme."

### Prompt: Add Multi-Model Insights
> "When available, show a 'Claude's Take' card next to each clip that displays the strategic_narrative and archetype_label from the Claude analysis layer. This shows two AIs analyzing the same clip from different angles — Gemini sees the video, Claude reads the story."

### Prompt: Connect to Supabase
> "Replace the static JSON fetch with Supabase queries. Install @supabase/supabase-js. Create lib/supabase.ts with the URL and anon key from env vars. The main query is: supabase.from('pickle_daas_analyses').select('*').order('clip_quality_score', { ascending: false }).limit(50). This gives us real-time data instead of cached JSON."

---

## Pipeline Status

- **Auto-ingest:** Running every hour (50 clips/batch)
- **Corpus:** 190 unique clips (growing hourly)
- **Cost:** $0.0054/clip × 190 = $1.03 total Gemini spend
- **Claude multi-model:** 15 clips analyzed ($0.21)
- **Supabase:** 30 rows live, more pushing as corpus grows
- **gh-pages:** Updated and live

---

## What Comes Next
1. Connect Lovable to Supabase (replaces static JSON)
2. Add the `anon` key to Lovable env vars
3. Wire skill radar charts (data is now correct)
4. Add brand intelligence page
5. Add multi-model Claude insights as optional overlay

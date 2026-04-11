# Pickle DaaS Phase 2 -- Lovable Handoff

_Generated 2026-04-11 | DinkData frontend update guide_
_Data source: `https://picklebill.github.io/pickle-daas-data/`_

---

## 1. What's New on gh-pages

All JSON files are served from the root of `https://picklebill.github.io/pickle-daas-data/`. Fetch with a simple `GET` -- no auth required.

### JSON Files Available

| File | Description | What Changed in Phase 2 |
|------|-------------|------------------------|
| `corpus-export.json` | Full analyzed clip corpus (190+ clips) | NEW. Multi-model fused output. Every clip now has `model` field (gemini-2.5-flash or claude), `skills` object (6 axes), `brands[]`, `badges[]`, `arc`, `dominant_shot`, `ron_burgundy`, `social_caption`. |
| `enriched-corpus.json` | Corpus with player/brand enrichment | NEW. Adds `player`, `brand_count`, `wildcard` fields per clip on top of corpus-export shape. |
| `dashboard-stats.json` | Aggregate KPIs for the dashboard | UPDATED. Now 96 clips analyzed, 24 unique brands, 8 unique players. Added `badge_precision`, `badge_recall`, `badge_f1`, `cost_per_clip`. Arc and brand distributions included. |
| `player-profiles.json` | All player summary profiles | NEW. Array of 8 players with `clipCount`, `avgSkills`, `topBrands`, `badges`, `dominantShot`, `avgQuality`, `avgViral`. |
| `creative-badges.json` | Earned badges per player | NEW. Badge types: Highlight Factory, Brand Magnet, Dink Master, The Grinder, Viral Sensation, Drive Specialist, Camera Magnet, Arc Chameleon, JOOLA Ambassador. Each has `criteria`, `clip_count`, linked clip UUIDs. |
| `clips-metadata.json` | Curated clip details for Lovable cards | Existing. Includes `tmnt_commentary` (5 turtle voices), `sport`, `sport_confidence`. |
| `dashboard-data.json` | Pre-built Lovable dashboard payload | Existing. Player header + KPIs + analytics + skill radar + brand chart data. |
| `player-dna.json` | Single player DNA profile (PickleBill) | Existing. Skill radar (7 axes), coaching insights, play style tags. |
| `brand-registry.json` | Brand intelligence with clip links | Existing. Per-brand: category, appearances, confidence, presence percentage, sponsorship insight. |
| `voice-manifest.json` | Voice commentary MP3 links | Existing. Ron Burgundy voice file references. |
| `voice-manifest-tmnt.json` | TMNT voice commentary links | Existing. Turtle character voice references. |

### New Fields to Know About

- **`model`** on every clip -- either `"gemini-2.5-flash"` or `"claude-sonnet-4-20250514"`. Enables model comparison UI.
- **`skills`** object on every clip -- `{ court_coverage, kitchen, creativity, athleticism, court_iq, power }` (0-10 scale, many still 0 for older clips).
- **`arc`** values: `grind_rally`, `athletic_highlight`, `clutch_moment`, `pure_fun`, `teaching_moment`, `error_highlight`, `dominant_performance`.
- **`dominant_shot`** values: `dink`, `drive`, `volley`, `drop`, `serve`, `dink_to_speed_up`.
- **`badge_precision` / `badge_recall` / `badge_f1`** in dashboard-stats -- ML quality metrics for badge assignment.
- **`cost_per_clip`** in dashboard-stats -- $0.0054 (Gemini baseline).

---

## 2. TypeScript Interfaces

Paste these into your Lovable project's `src/types/daas.ts` (or equivalent).

```typescript
// ---- Corpus Clip (corpus-export.json / enriched-corpus.json) ----

interface CorpusClip {
  uuid: string;
  video_url: string;                    // cdn.courtana.com MP4
  thumbnail: string;                    // cdn.courtana.com JPEG
  quality: number;                      // 1-10
  viral: number;                        // 1-10
  watchability: number;                 // 1-10
  arc: StoryArc;
  summary: string;
  dominant_shot: ShotType;
  total_shots: number;
  brands: string[];
  badges: string[];
  ron_burgundy: string;                 // ESPN-style commentary
  social_caption: string;
  skills: SkillRatings;
  model: "gemini-2.5-flash" | "claude-sonnet-4-20250514";
}

interface EnrichedClip extends CorpusClip {
  player: string;                       // username or "unknown"
  brand_count: number;
  wildcard: Record<string, unknown>;
}

type StoryArc =
  | "grind_rally"
  | "athletic_highlight"
  | "clutch_moment"
  | "pure_fun"
  | "teaching_moment"
  | "error_highlight"
  | "dominant_performance";

type ShotType =
  | "dink"
  | "drive"
  | "volley"
  | "drop"
  | "serve"
  | "dink_to_speed_up";

interface SkillRatings {
  court_coverage: number;               // 0-10
  kitchen: number;
  creativity: number;
  athleticism: number;
  court_iq: number;
  power: number;
}


// ---- Dashboard Stats (dashboard-stats.json) ----

interface DashboardStats {
  total_clips_analyzed: number;
  total_clips_available: number;
  unique_brands: number;
  unique_players: number;
  avg_quality: number;
  badge_precision: number;              // NEW -- ML metric
  badge_recall: number;                 // NEW -- ML metric
  badge_f1: number;                     // NEW -- ML metric
  cost_per_clip: number;                // NEW -- $0.0054
  top_arcs: Record<StoryArc, number>;
  top_brands: Record<string, number>;
  last_updated: string;                 // ISO date
}


// ---- Player Profile (player-profiles.json) ----

interface PlayerProfile {
  name: string;
  clipCount: number;
  avgSkills: Partial<SkillRatings>;     // may be empty {}
  topBrands: string[];
  badges: string[];
  dominantShot: ShotType;
  avgQuality: number;
  avgViral: number;
}


// ---- Creative Badge (creative-badges.json) ----

interface CreativeBadge {
  badge: BadgeType;
  player: string;                       // username or "unknown"
  clip_count: number;
  criteria: string;                     // human-readable rule
  clips?: string[];                     // linked clip UUIDs
  brands?: string[];                    // for Brand Magnet badges
  brand_count?: number;
  arcs?: StoryArc[];                    // for Arc Chameleon badges
}

type BadgeType =
  | "Highlight Factory"
  | "Brand Magnet"
  | "Dink Master"
  | "The Grinder"
  | "Viral Sensation"
  | "Drive Specialist"
  | "Camera Magnet"
  | "Arc Chameleon"
  | "JOOLA Ambassador";


// ---- Player DNA (player-dna.json) ----

interface PlayerDNA {
  username: string;
  rank: number;
  xp: number;
  level: number;
  rank_tier: string;
  badges_count: number;
  clips_analyzed: number;
  dominant_shot: string;
  play_style: string[];
  skill_radar: {
    court_coverage: number;
    kitchen_mastery: number;
    power_game: number;
    touch_feel: number;
    athleticism: number;
    creativity: number;
    court_iq: number;
  };
  coaching_insights: string[];
}


// ---- Clips Metadata (clips-metadata.json) ----

interface ClipMetadata {
  id: string;                           // short UUID
  name: string;
  video_url: string;
  thumbnail_url: string;
  quality_score: number;
  viral_score: number;
  story_arc: StoryArc;
  ron_burgundy_quote: string;
  top_badge: string;
  brands: string[];
  caption: string;
  sport: string;
  sport_confidence: "high" | "medium" | "low";
  tmnt_commentary: {
    tmnt_leonardo: string;
    tmnt_raphael: string;
    tmnt_donatello: string;
    tmnt_michelangelo: string;
    tmnt_splinter: string;
  };
}


// ---- Dashboard Data (dashboard-data.json) ----

interface DashboardData {
  player: {
    username: string;
    rank: number;
    xp: number;
    level: number;
    rank_tier: string;
    badges_count: number;
  };
  kpis: {
    clips_analyzed: number;
    avg_quality_score: number;
    top_brand: string;
    avg_viral_score: number;
  };
  analytics: {
    avg_quality_score: number;
    avg_viral_score: number;
    top_shot_type: string;
    dominant_play_style: string;
    top_brands: { brand: string; count: number }[];
    skill_radar: Record<string, number>;
    story_arc_breakdown: Record<string, number>;
    total_clips_analyzed: number;
    sport_breakdown: Record<string, number>;
  };
  generated_at: string;
}


// ---- Brand Registry (brand-registry.json) ----

interface BrandRegistry {
  total_clips_analyzed: number;
  brands: BrandEntry[];
  sponsorship_insight: string;
  generated_at: string;
}

interface BrandEntry {
  brand_name: string;
  category: string;
  appearances: number;
  clips: string[];
  confidence: "high" | "medium" | "low";
  presence_percentage: number;
}
```

---

## 3. New Data Available (Phase 2 Additions)

### Multi-Model Fused Outputs
Every clip in `corpus-export.json` now carries a `model` field. The pipeline runs both Gemini 2.5 Flash and Claude Sonnet on the same clips. This enables:
- Side-by-side analysis comparison
- Model agreement/disagreement highlighting
- Confidence scoring (when both models agree on arc/shot, confidence is higher)

### Camera-Based Analysis
Each clip is analyzed from the raw video via Gemini's multimodal vision. The AI watches the MP4 and extracts:
- Shot type classification
- Brand detection (logos, apparel, signage)
- Story arc assignment
- Skill ratings on 6 dimensions
- Quality / viral / watchability scores

### Match Context
- `arc` field provides narrative context for every rally
- `total_shots` tracks rally length
- `dominant_shot` reveals what ended or defined the point
- `skills` object gives per-clip skill snapshots that aggregate into player profiles

### Badge Intelligence
`creative-badges.json` contains 9 badge types with full criteria transparency. Each badge links back to the specific clips that earned it, enabling drill-down from badge to video.

### Pipeline Quality Metrics
`dashboard-stats.json` now includes `badge_precision` (38.9%), `badge_recall` (53.9%), and `badge_f1` (45.2%) -- transparency into ML quality that no competitor exposes.

---

## 4. DinkData Pages That Need Updating

| Page | What to Fetch | What to Change |
|------|--------------|----------------|
| **Dashboard / Home** | `dashboard-stats.json` | Add clip count (96 analyzed / 8,125 available), cost per clip, badge F1 score. Show `top_arcs` distribution chart. Update brand counts to 24. |
| **Highlights Grid** | `corpus-export.json` | Replace hardcoded clips with full 190+ corpus. Add filter chips for `arc`, `dominant_shot`, `model`. Show `brands[]` as tags under each card. |
| **Video Player Modal** | Same clip data | Add `model` badge (Gemini vs Claude). Show `skills` radar inline. Display `social_caption` with copy button. |
| **Player Profile** | `player-profiles.json` + `player-dna.json` | Populate for all 8 players instead of just PickleBill. Show `avgSkills` radar, `topBrands`, `badges`, `dominantShot`. |
| **Badges Page** | `creative-badges.json` | NEW PAGE or section. Show earned badges per player with criteria, clip count, and drill-down to linked clips. |
| **Brand Intelligence** | `brand-registry.json` + `dashboard-stats.json` | Update to 24 brands. Show `top_brands` bar chart from stats. Link brand appearances to specific clips. |
| **Leaderboard** | `player-profiles.json` | Rank 8 players by `avgQuality` or `clipCount`. Show dominant shot and top brand per player. |

---

## 5. Suggested Lovable Prompts

### Prompt 11: Visual Intelligence Explorer

```
Build a Visual Intelligence Explorer page for DinkData -- a filterable, browsable
grid of pickleball highlight clips with embedded video playback.

Data source: Fetch from https://picklebill.github.io/pickle-daas-data/corpus-export.json
on page load. Show a loading skeleton while fetching.

Color scheme: dark background #1a2030, cards #252d3a, green accent #00E676, text white.

Layout:

1. FILTER BAR (sticky top, horizontal scroll on mobile)
   - Chips for Story Arc: All, Grind Rally, Athletic Highlight, Clutch Moment,
     Pure Fun, Teaching Moment, Error Highlight
   - Chips for Dominant Shot: All, Dink, Drive, Volley, Drop, Serve
   - Chips for Brand: All, then top 10 brands from the data (count appearances,
     show top 10)
   - Search box: filters by ron_burgundy text and social_caption
   - Sort dropdown: Quality (high to low), Viral (high to low), Newest

2. CLIP GRID (3 cols desktop, 2 tablet, 1 mobile)
   Each card:
   - Thumbnail image (use thumbnail field, cdn.courtana.com JPEG)
   - Play button overlay (centered, semi-transparent)
   - Quality badge (top-right corner, green pill)
   - Arc badge (top-left, color-coded: grind=blue, athletic=orange,
     clutch=red, fun=purple, teaching=teal, error=gray)
   - Brand tags (bottom, small dark chips with white text)
   - Social caption (1 line, truncated with ellipsis)

3. EXPANDED VIEW (click any card)
   - HTML5 video player (autoplay, controls, src from video_url)
   - Below video, two columns:
     Left: Quality/Viral/Watchability scores as circular progress rings
     Right: Skills radar chart (6 axes from skills object) using Recharts RadarChart
   - Ron Burgundy quote (italic, green left border, full text)
   - Social caption with copy-to-clipboard button
   - Brand tags (larger chips)
   - Model badge: show "Gemini 2.5 Flash" or "Claude Sonnet" with icon
   - Close on Escape or click outside

4. STATS RIBBON (bottom of filter bar or above grid)
   - "190 clips" | "24 brands detected" | "7 story arcs" | "$0.005/clip"
   - Values computed from the fetched data, not hardcoded

Use Tailwind CSS. Make fully responsive. All data from the single JSON fetch --
no hardcoded clip data.
```

---

### Prompt 12: Multi-Model Insights

```
Build a Multi-Model Insights page for DinkData that shows Gemini vs Claude
analysis side-by-side for pickleball clips.

Data source: Fetch https://picklebill.github.io/pickle-daas-data/corpus-export.json
Show loading skeleton while fetching.

Color scheme: dark background #1a2030, cards #252d3a, accent green #00E676,
Gemini color #4285F4 (blue), Claude color #D97706 (amber).

Layout:

1. HEADER
   - Title: "Multi-Model Intelligence"
   - Subtitle: "See how two AI models interpret the same pickleball clips"
   - Model legend: blue dot = Gemini 2.5 Flash, amber dot = Claude Sonnet

2. MODEL DISTRIBUTION PANEL
   - Donut chart showing clip count per model
   - Below: average quality score per model, average viral score per model
   - Stat cards: "Gemini analyzed X clips" / "Claude analyzed Y clips"

3. AGREEMENT ANALYSIS
   - For clips where both models exist (future: when we have dual-model data),
     show agreement rate on: arc classification, dominant shot, quality score
     within 1 point
   - For now, group clips by model and show comparative distributions:
     Arc distribution (stacked bar, Gemini blue vs Claude amber)
     Shot type distribution (grouped bar chart)
     Quality score histogram (overlapping, semi-transparent)

4. CLIP COMPARISON CARDS
   - Pick 3 representative clips from each model (highest quality)
   - Show them in a 2-column layout: "Gemini Says" | "Claude Says"
   - Each side: thumbnail, quality/viral scores, arc badge, ron_burgundy quote,
     dominant shot, brands detected
   - Highlight differences in red text where the models disagree

5. COST EFFICIENCY PANEL
   - Gemini: $0.0054/clip
   - Claude: estimated from data (calculate if available)
   - "Cost to analyze entire corpus of 8,125 clips" math for each model
   - Recommendation card: "Gemini for speed, Claude for depth"

Use Recharts for all charts. Tailwind CSS. Responsive.
No hardcoded data -- derive everything from the fetched JSON.
```

---

### Prompt 13: Player DNA Cards

```
Build a Player DNA Cards page for DinkData -- shareable player profile cards
with radar charts, badges, and brand affiliations.

Data sources (fetch both on page load):
- https://picklebill.github.io/pickle-daas-data/player-profiles.json
- https://picklebill.github.io/pickle-daas-data/creative-badges.json

Color scheme: dark background #1a2030, cards #252d3a, green accent #00E676,
gold accent #F59E0B for top players.

Layout:

1. PLAYER SELECTOR (top)
   - Horizontal scroll of player avatar circles (use first letter of name
     as avatar, colored uniquely per player)
   - Selected player has gold ring + scale-up animation
   - Default: PickleBill (first in list)

2. DNA CARD (center, max-width 480px, designed to look like a trading card)
   - Top section: gradient header (dark to green), player name large,
     clip count + avg quality as stats
   - RADAR CHART (Recharts RadarChart, 6 axes):
     If avgSkills is populated, use those values.
     If avgSkills is empty {}, compute from the player's clips in corpus data
     or show "Insufficient Data" overlay.
     Axes: Court Coverage, Kitchen, Creativity, Athleticism, Court IQ, Power
     Fill color: green with 30% opacity, stroke green
   - STATS ROW: Dominant Shot (icon + label), Avg Quality (score),
     Avg Viral (score), Clip Count (number)
   - BRAND AFFILIATIONS: horizontal row of brand name chips from topBrands[]
   - BADGES SECTION: pull this player's badges from creative-badges.json.
     Show badge name + criteria as tooltip. Use icons:
     Highlight Factory = star, Brand Magnet = magnet, Dink Master = hand,
     The Grinder = fire, Viral Sensation = lightning, Camera Magnet = camera
   - SHARE BUTTON: copies a deep link like ?player=PickleBill to clipboard

3. LEADERBOARD TABLE (below card)
   - All 8 players ranked by avgQuality descending
   - Columns: Rank, Name, Clips, Avg Quality, Avg Viral, Dominant Shot, Brands
   - Clicking a row selects that player and scrolls up to their DNA card
   - Highlight current selected player row in green

4. COMPARISON MODE (toggle button top-right)
   - Select 2 players
   - Show both radar charts overlaid on same axes (different colors)
   - Delta table: stat differences with arrows (green up, red down)

Use Tailwind CSS. Recharts for radar. Fully responsive -- card stacks
vertically on mobile. All data from the two JSON fetches.
```

---

## 6. API Endpoints -- Complete Reference

All endpoints are public, no authentication required. CORS-enabled for any origin.

| Endpoint | Shape | Size | Update Frequency |
|----------|-------|------|-----------------|
| `https://picklebill.github.io/pickle-daas-data/corpus-export.json` | `CorpusClip[]` | ~190 clips | Hourly ingest |
| `https://picklebill.github.io/pickle-daas-data/enriched-corpus.json` | `EnrichedClip[]` | ~190 clips | Hourly ingest |
| `https://picklebill.github.io/pickle-daas-data/dashboard-stats.json` | `DashboardStats` | Single object | Hourly ingest |
| `https://picklebill.github.io/pickle-daas-data/player-profiles.json` | `PlayerProfile[]` | 8 players | Hourly ingest |
| `https://picklebill.github.io/pickle-daas-data/creative-badges.json` | `CreativeBadge[]` | ~15 badges | Hourly ingest |
| `https://picklebill.github.io/pickle-daas-data/clips-metadata.json` | `ClipMetadata[]` | 8 curated clips | Manual push |
| `https://picklebill.github.io/pickle-daas-data/dashboard-data.json` | `DashboardData` | Single object | Manual push |
| `https://picklebill.github.io/pickle-daas-data/player-dna.json` | `PlayerDNA` | Single player | Manual push |
| `https://picklebill.github.io/pickle-daas-data/brand-registry.json` | `BrandRegistry` | Single object | Manual push |
| `https://picklebill.github.io/pickle-daas-data/voice-manifest.json` | Voice links | Ron Burgundy | Manual push |
| `https://picklebill.github.io/pickle-daas-data/voice-manifest-tmnt.json` | Voice links | TMNT chars | Manual push |

### CDN Pattern for Video/Thumbnails

```
Video:     https://cdn.courtana.com/files/production/u/{user_uuid}/{clip_uuid}.mp4
Thumbnail: https://cdn.courtana.com/files/production/u/{user_uuid}/{clip_uuid}.jpeg
```

These are public -- link directly, no auth needed.

### Fetch Example

```typescript
const BASE = "https://picklebill.github.io/pickle-daas-data";

async function fetchCorpus(): Promise<CorpusClip[]> {
  const res = await fetch(`${BASE}/corpus-export.json`);
  return res.json();
}

async function fetchStats(): Promise<DashboardStats> {
  const res = await fetch(`${BASE}/dashboard-stats.json`);
  return res.json();
}

async function fetchPlayers(): Promise<PlayerProfile[]> {
  const res = await fetch(`${BASE}/player-profiles.json`);
  return res.json();
}

async function fetchBadges(): Promise<CreativeBadge[]> {
  const res = await fetch(`${BASE}/creative-badges.json`);
  return res.json();
}
```

---

## Prompt Paste Order (Updated for Phase 2)

| Priority | Prompt | What It Builds | Audience |
|----------|--------|---------------|----------|
| 1 | Prompt 13 (Player DNA Cards) | Shareable player profiles with radar + badges | All demos |
| 2 | Prompt 11 (Visual Intelligence Explorer) | Full clip browser with filters + video | Product demos |
| 3 | Prompt 12 (Multi-Model Insights) | Gemini vs Claude comparison | Investors / technical |
| -- | Prompts 08-10 (from Phase 1) | Investor demo, Court Kings, Comparison | Per PASTE-ORDER.md |

---

_End of Phase 2 Handoff_

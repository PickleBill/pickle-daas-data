# Handoff: Pickle DaaS → Lovable Integration
_Generated: 2026-04-11 | Port this to a fresh Claude Code session or Cowork_

---

## Current State

### Data on GitHub Pages (LIVE NOW)
All files at `https://picklebill.github.io/pickle-daas-data/`

| File | Clips/Items | URL |
|------|-------------|-----|
| `corpus-export.json` | 96 clips | [Link](https://picklebill.github.io/pickle-daas-data/corpus-export.json) |
| `enriched-corpus.json` | 96 clips + player field | [Link](https://picklebill.github.io/pickle-daas-data/enriched-corpus.json) |
| `creative-badges.json` | 41 badges | [Link](https://picklebill.github.io/pickle-daas-data/creative-badges.json) |
| `dashboard-stats.json` | Aggregate stats | [Link](https://picklebill.github.io/pickle-daas-data/dashboard-stats.json) |
| `player-profiles.json` | 8 players (camelCase) | [Link](https://picklebill.github.io/pickle-daas-data/player-profiles.json) |
| `voice-manifest.json` | 5 voice characters | [Link](https://picklebill.github.io/pickle-daas-data/voice-manifest.json) |

### Lovable App (v1.1 built, needs data wiring)
- GitHub repo: (Bill has this from Lovable)
- Uses React + TypeScript + Vite + Tailwind + Recharts + Framer Motion
- Currently has hardcoded data — needs to fetch from gh-pages URLs above
- Has 10 routes: Home, Explore, Clip Detail, Brands, Players, Compare, Badges, Buyers, Voices, Player Detail

### Data Schemas (Match These Exactly)

**corpus-export.json clip object:**
```json
{
  "uuid": "string",
  "video_url": "https://cdn.courtana.com/files/.../clip.mp4",
  "thumbnail": "...jpeg",
  "quality": 8, "viral": 6, "watchability": 7,
  "arc": "grind_rally",
  "summary": "string",
  "dominant_shot": "dink",
  "total_shots": 14,
  "brands": ["JOOLA", "Nike"],
  "badges": ["Dink Master"],
  "ron_burgundy": "By the beard of Zeus...",
  "social_caption": "string",
  "skills": { "court_coverage": 8, "kitchen": 9, "creativity": 7, "athleticism": 8, "court_iq": 8, "power": 7 },
  "model": "gemini-2.5-flash-lite"
}
```

**player-profiles.json (camelCase for Lovable):**
```json
{
  "name": "David",
  "clipCount": 20,
  "avgSkills": { "courtCoverage": 6.2, "kitchen": 7.1, "creativity": 5.8, "athleticism": 6.0, "courtIQ": 5.5, "power": 5.3 },
  "topBrands": ["JOOLA", "Nike"],
  "badges": ["Highlight Factory", "Camera Magnet"],
  "dominantShot": "dink",
  "avgQuality": 7.8,
  "avgViral": 6.2
}
```

**voice-manifest.json:**
```json
{ "id": "ron_burgundy", "name": "Ron Burgundy", "voiceId": "pNInz6obpgDQGcFmaJgB", "style": "...", "mp3Url": null, "sampleText": "..." }
```

### Pipeline (Claude Code)
- Analyzer: `pickle-daas-gemini-analyzer.py` — inline bytes, model cascade (flash-lite primary)
- Auto-ingest: `tools/auto-ingest.py` — fetches new clips, skips analyzed, runs pipeline
- Badge warehouse: `tools/badge-warehouse.py` — cross-references predictions vs Courtana ground truth
- Player cards: `tools/generate-player-cards.py` — generates shareable HTML cards
- Current cost: $0.0054/clip via Gemini 2.5 Flash Lite

### Key Metrics
- 96 unique clips analyzed (185 total including re-analyses with different prompts)
- 8 players with enough data for profiles
- 24 unique brands detected
- Badge prediction: P=38.9%, R=53.9%, F1=45.2% (v1.3 prompt with taxonomy)
- Pipeline speed: ~18s/clip (inline bytes, no File API)

---

## What Lovable Needs to Do Next

1. **Wire up data endpoints** — Replace hardcoded data with fetch() from gh-pages URLs
2. **Fix hydration error** — SSR/client mismatch on stylesheet ordering (Lovable knows about this)
3. **Add stagger animations** — Framer Motion entrance reveals on all pages
4. **Connect voice manifest** — Wire up voice-manifest.json for the character selector
5. **Player detail pages** — Use player-profiles.json for the /players route

## What Claude Code Needs to Do Next

1. **Run more clips through Gemini** — 96 is good, 200+ is better, 500+ is statistically significant
2. **Auto-ingest on cron** — `tools/auto-ingest.py --count 30 --warehouse` daily
3. **Generate brand reports** — Per-brand intelligence reports as PDF/HTML for buyers
4. **Supabase** — SERVICE_KEY needs to be added to .env, then `push-to-supabase.py` works

---

## How to Start a Fresh Session

### For Claude Code:
```
cd "~/PickleBill Dropbox/PickleBill Team Folder/Claude Projects/PICKLE-DAAS"
claude
```
Then say: "Load context. The Lovable app is built and fetching from gh-pages. I need to run more clips through Gemini and push updated data."

### For Cowork:
Say: "Load context. The Lovable DaaS Explorer v1.1 is built. Data is on gh-pages. I need to improve the prompts and design for the next Lovable iteration."

### For Lovable (prompt to give it):
"The data files are now live on GitHub Pages. Wire up these new endpoints:
- `https://picklebill.github.io/pickle-daas-data/dashboard-stats.json` → Dashboard counters
- `https://picklebill.github.io/pickle-daas-data/player-profiles.json` → Player pages
- `https://picklebill.github.io/pickle-daas-data/voice-manifest.json` → Voice character selector
- `https://picklebill.github.io/pickle-daas-data/creative-badges.json` → Badge collection page

All schemas match what you specified. The `player-profiles.json` uses camelCase field names as requested. Every clip in `enriched-corpus.json` has a `player` field (defaults to 'unknown'). No schema changes to existing fields — all additions are new fields only."

---

## Product Roadmap Reference
Full roadmap at: `BILL-OS/DAAS-PRODUCT-ROADMAP.md`
- Phase 1 (Week 1): Ship MVP Lovable build with real data
- Phase 2 (Weeks 2-3): Brand reports, buyer personalization, first revenue
- Phase 3 (Month 2): API, auto-ingest, ElevenLabs voices
- Phase 4 (Month 3+): Courtana Universe, viral loops, partnerships

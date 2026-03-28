# Pickle DaaS — Lovable Mega Prompt V3
# The definitive build prompt. Paste this into picklestats-hub to complete the app.
# This supersedes all previous prompts.

---

You are upgrading the existing Pickle DaaS app (picklestats-hub) into a fully data-driven, production-quality sports analytics platform. All data comes from real Gemini AI video analysis of actual pickleball clips.

## THE DATA LAYER — Fetch from GitHub (public, no auth)

All data lives at: `https://raw.githubusercontent.com/PickleBill/pickle-daas-data/main/output/lovable-package/`

```
dashboard-data.json     — KPIs, skill radar, brand counts, analytics
clips-metadata.json     — 8 real clips with video URLs, scores, commentary, brands, badges
player-dna.json         — PickleBill full profile, coaching insights, play style tags
brand-registry.json     — Brand detection with presence %, clip mapping, ROI insight
voice-manifest.json     — 32 ElevenLabs MP3s (8 clips × 4 voices) with file metadata
```

Create a `usePickleDaas()` hook that fetches all 5 JSON files on mount, stores them in React context, and makes them available app-wide. Show a subtle skeleton/pulse loader while fetching. Cache in-memory — never re-fetch within a session.

---

## PAGE 1: DASHBOARD

### KPI Cards (4 in a row, 2×2 on mobile)
Pull from `dashboard-data.json → kpis`:
- **Clips Analyzed**: `8` — large green number
- **Avg Quality**: `7.3 / 10`
- **Top Brand**: `JOOLA`
- **Viral Potential**: `5.5 avg`

On hover: subtle green glow shadow (`box-shadow: 0 0 20px rgba(0,230,118,0.15)`)

### Featured Highlight — TWO COLUMN LAYOUT
Left 60%: HTML5 video player
- Load first clip from `clips-metadata.json` (id: `ce00696b` — "Shot of the Day — Airborne")
- Custom play button overlay (green circle, white triangle) instead of browser default
- Below video: score strip — 4 chips in a row: Quality `8/10` (green), Viral `7/10` (gold), Watchability `8/10` (blue), Cinematic `9/10` (purple)

Right 40%: Commentary panel
- 5 tabs: **ESPN** | **Hype** | **Ron Burgundy** | **Chuck Norris** | **Coach**
- Tab content pulls from clips-metadata.json commentary fields
- Below text: `🔊 Play Voice` button
  - If ElevenLabs connected: call `/functions/v1/elevenlabs-tts` with voice_id and text
  - Fallback: `speechSynthesis.speak()` with voice tuning (hype: rate 1.2, chuck: pitch 0.6, ron: pitch 0.85)
  - While playing: show 4 animated bars (waveform pulse, CSS keyframes, green color)
- Coach tab: show `daas_signals.coaching_breakdown` or fallback coaching text from player-dna.json

Below featured highlight: two columns:
- Left: Recharts `RadarChart` with 7 axes from `dashboard-data.json → analytics.skill_radar` — green fill, dark background
- Right: Horizontal bar chart of `top_brands` — green bars, brand names left-aligned

---

## PAGE 2: HIGHLIGHTS

Fetch `clips-metadata.json` — render all 8 clips in a **3-column grid** (2 tablet, 1 mobile).

### Clip Card Design
Dark card (`background: #1a2535`), green top border (`border-top: 2px solid #00E676`):

**Video section (top):**
- HTML5 video with `preload="metadata"`, `muted`, autoplay on hover (`onMouseEnter`), pause on leave
- Quality score chip: top-right corner, green (`clip_quality_score/10`)
- Viral chip: top-left — red if ≥7, gold if 5-6, gray if <5

**Card body:**
- Story arc tag chip (color-coded):
  - `grind_rally` → blue
  - `teaching_moment` → green
  - `athletic_highlight` → purple
  - `error_highlight` → red/orange
  - `pure_fun` → yellow
- Clip name (bold, white)
- Ron Burgundy quote (italic, small, green left border, `#8899aa` text)
- Brand pills (small, gold bordered for first appearance)
- Badge chips (green)

**Click → Modal:**
Full-screen dark modal containing:
- Full-width video player with score strip beneath
- All 5 commentary tabs (same as dashboard)
- `🔊 Play Voice` button with waveform animation
- Badges section: `badge_intelligence.predicted_badges` as large green chips
- Brand detection: pills with category label
- Hashtags: click-to-copy chips (brief "Copied!" toast on click)
- Caption: styled Instagram-style caption text

---

## PAGE 3: PLAYER DNA

Fetch `player-dna.json`.

### Header Card
- Large circular avatar (green border, white `PB` initials — `60px` font)
- Username: `PickleBill` (large, bold)
- Stats row: `Rank #1 Global` | `XP 283,950` | `Level 17` | `Gold III` | `82 Badges`
- Subtitle: `Clips Analyzed: 8 | Dominant Shot: Drive | Style: Banger, Net Rusher`

### Two-Column Layout
Left: Large `RadarChart` (bigger than dashboard version) — 7 axes:
```
Court Coverage: 6.0
Kitchen Mastery: 5.0
Power Game: 6.0
Touch & Feel: 5.3
Athleticism: 6.3
Creativity: 4.0
Court IQ: 5.7
```

Right: Play Style DNA chips — sized by dominance:
- `banger` — largest (24px font, full-width chip)
- `consistent driver` — large
- `baseliner` — medium
- `net rusher` — medium
- `aggressive baseliner` — smaller

### Coaching AI Insights Card
Green left border (`border-left: 3px solid #00E676`), dark card:
Title: "AI Coaching Insights" with a 🎯 icon
Bullet list from `player-dna.json → coaching_insights`:
- Incorporate more soft game and dinking at the kitchen
- Approach the net more often after third shot drops
- Transition speed from baseline to kitchen needs work
- Keep paddle in ready position between shots
- Stabilize before contact on volleys for more consistency

### Story Arc Distribution
Donut chart (Recharts `PieChart`):
- `grind_rally`: 2 — blue
- `teaching_moment`: 3 — green
- `pure_fun`: 2 — yellow
- `athletic_highlight`: 1 — purple
- `error_highlight`: 1 — red

### Signature Clips Grid
3-column compact grid — same 8 clips as Highlights but compact: just thumbnail video + name + quality chip + arc tag.

---

## PAGE 4: BRANDS

Fetch `brand-registry.json`.

Title: "Brand Detection Registry"
Subtitle: "AI-detected brands across 8 analyzed highlights · Powered by Gemini Vision"

### 3 Brand Cards Side by Side
Each card: dark background, colored icon/logo area at top

**JOOLA** — 8/8 appearances, category: `paddle / net`, confidence: high
- Progress bar: 100% green
- Clip presence: all 8 clips (show 8 small green dots)
- "🎾 Equipment partner — 100% visibility across all clips"

**LIFE TIME PICKLEBALL** — 8/8 appearances, category: `venue / apparel`, confidence: high
- Progress bar: 100% gold
- "🏟️ Venue partner — court branding visible in every clip"

**CRBN** — 2/8 appearances, category: `paddle`, confidence: medium
- Progress bar: 25% green
- "🏓 Paddle brand — detected in 2 clips via logo/colorway"

### Brand Detection Heatmap
Dark table with clip names as rows, brand columns:
- Green dot (●) if brand detected in that clip, empty (·) if not
- Sortable by brand presence

### Sponsorship ROI Callout
Gold border card (`border: 1px solid #FFD600`):
> "JOOLA and LIFE TIME PICKLEBALL have 100% presence across all 8 analyzed clips. Courtana can tell brands exactly how many seconds their equipment appears per clip — turning every highlight into a measurable sponsorship asset."

CTA button: "Download Sponsor Report" (ghost button, gold border) — for now just shows a toast "Coming soon — full PDF report"

---

## PAGE 5: VOICE LAB

Title: "AI Commentary Voice Lab"
Subtitle: "Real ElevenLabs voices · 32 MP3s already generated"

### Clip Selector
Dropdown of all 8 clips by name. Selecting a clip updates all 4 voice cards below.

### 4 Voice Cards (2×2 grid)
Each card:
- Voice name + icon: ESPN 🎙️ | Hype 🔥 | Ron Burgundy 🥃 | Chuck Norris 💪
- Voice ID shown small (muted text)
- Commentary text for selected clip (from clips-metadata.json)
- `🔊 Play` button
  - Primary: Call ElevenLabs TTS via Supabase edge function
  - Fallback: speechSynthesis
  - Waveform animation while playing
- `⬇️ Download MP3` button (future — show toast for now)
- "ElevenLabs Live" green badge

### Pipeline Status Card
```
✅ Gemini 2.5 Flash Analysis    — 8 clips processed · gemini-2.5-flash
✅ ElevenLabs TTS               — 32 MP3s generated · Creator tier · 110k chars
✅ Supabase Database            — 3 tables · pickle_daas_analyses deployed
✅ GitHub Data Pipeline         — Live at github.com/PickleBill/pickle-daas-data
🔜 Auto-Voice on New Clips      — Triggers when new Gemini analysis runs
🔜 Supabase Realtime            — Live clip feed as PickleBill uploads
```

---

## GLOBAL UI POLISH

### Color System (enforce everywhere)
```css
--bg-primary:    #0a0f1a
--bg-card:       #131d2e
--bg-card-hover: #1a2535
--green:         #00E676
--gold:          #FFD600
--text-primary:  #e0eaf8
--text-muted:    #5a7090
--border-subtle: rgba(255,255,255,0.07)
```

### Nav Bar
- Left: `<img src="https://cdn.courtana.com/assets/logos/fulllogo-dark-transparent-grad.svg" height="32" onerror="this.style.display='none'; this.nextSibling.style.display='block'">` + `<span style="display:none;color:#00E676;font-weight:800">Courtana</span>`
- Center: **Pickle DaaS** (green, bold) + "Data as a Service for Pickleball" (muted, small)
- Right: page links — Dashboard | Highlights | Player DNA | Brands | Voice Lab
- Mobile: hamburger menu (collapse all links)
- Subtle bottom border: `1px solid rgba(0,230,118,0.1)`

### Card Design System
- Background: `#131d2e`
- Border: `1px solid rgba(255,255,255,0.07)`
- Border-radius: `14px`
- On hover: border-color shifts to `rgba(0,230,118,0.25)`
- Thin green top accent: `border-top: 2px solid rgba(0,230,118,0.4)`

### Typography
- Font: `-apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif`
- Large numbers (KPI): `font-size: 2.5rem; font-weight: 800; color: #00E676`
- Section titles: `font-size: 11px; font-weight: 700; letter-spacing: 1.2px; text-transform: uppercase; color: #5a7090`
- Body: `font-size: 13px; color: #ccd8e8; line-height: 1.5`

### Animations
- Card hover: `transform: translateY(-2px); transition: 0.2s ease`
- Waveform bars: 4 divs, CSS keyframe `@keyframes wave { 0%,100% { height:4px } 50% { height:16px } }` staggered 75ms each
- Brand bars: slide in from left on mount, `animation: slideIn 0.4s ease forwards`
- KPI number: count up animation on mount using `useEffect` with incrementing state
- Score strip chips: fade in with stagger (0.1s between each)

### Footer
```
Powered by Courtana · Pickle DaaS · Built with Gemini AI + ElevenLabs
github.com/PickleBill/pickle-daas-data  |  courtana.com
```

---

## TECHNICAL NOTES

**Video URLs** — all hosted on CDN, no auth required:
```
https://cdn.courtana.com/files/production/u/01915c59-9bb7-4683-bd53-e28bddcae12e/{clip_id}.mp4
```

**ElevenLabs Voice IDs:**
```
ESPN:        TxGEqnHWrfWFTfGW9XjX  (Josh — deep, broadcast)
Hype:        ErXwobaYiN019PkySvjV  (Antoni — energetic)
Ron Burgundy: pNInz6obpgDQGcFmaJgB  (Adam — confident, pompous)
Chuck Norris: VR6AewLTigWG4xSOukaG  (Arnold — legendary)
```

**Supabase tables (already deployed):**
```
pickle_daas_analyses   — full Gemini analysis JSON per clip
pickle_daas_brands     — brand detection registry
pickle_daas_player_dna — player profiles and skill aggregates
```

**Do NOT re-fetch GitHub JSON on every render** — fetch once on mount, store in context.

**Mobile breakpoints:**
- Desktop: ≥1024px — 3-col grid, sidebar layouts
- Tablet: 768-1023px — 2-col grid
- Mobile: <768px — single column, stacked layouts, hamburger nav

---

## WHAT TO BUILD FIRST (priority order)

1. Wire `usePickleDaas()` hook to fetch all 5 GitHub JSON endpoints
2. Update Dashboard KPIs + Featured Highlight to use real clip data
3. Replace Highlights page clips (currently 3) with all 8 real clips
4. Update Player DNA with real coaching insights + story arc donut chart
5. Update Brands page with 3 brands + heatmap table
6. Polish global CSS (card hover, waveform, KPI count-up, footer)
7. Voice Lab — wire ElevenLabs with real voice IDs + fallback
8. Mobile responsive pass

Build it all. This is the final production version.

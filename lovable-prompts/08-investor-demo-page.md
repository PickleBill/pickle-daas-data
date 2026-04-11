# Lovable Prompt 08 — Investor Demo Page

## What This Builds
A standalone investor demo page showing Pickle DaaS scale, live data pull from Supabase if connected, animated KPIs, radar chart, and a closing pitch CTA. Bill pastes this into a new Lovable project called "pickle-daas-investor".

## Paste This Into Lovable

---

Build a full-page Investor Demo for a product called **Pickle DaaS** — a pickleball data intelligence platform. This is a React app using Tailwind CSS, shadcn/ui components, and Recharts. Route: `/` (root) or `/investor-demo`.

---

### Theme & Colors

- Background: `bg-slate-950` (#020617)
- Card backgrounds: `bg-slate-900` (#0f172a)
- Card borders: `border-slate-800` (#1e293b)
- Primary accent: `#00E676` (bright green)
- Secondary text: `text-slate-400`
- All text on dark backgrounds: white or slate-200
- Font: system-ui / Inter — no custom font imports needed

---

### Data Strategy

At the top of the component file, add this logic:

```typescript
const SUPABASE_URL = import.meta.env.VITE_SUPABASE_URL
const isLive = Boolean(SUPABASE_URL)
```

If `VITE_SUPABASE_URL` is set, fetch from the Supabase `pickle_daas_analyses` table (select `clip_quality_score`, `viral_potential_score`, `brands_detected`, `highlight_name`, `commentary_espn`, `clip_summary` — limit 15, order by `clip_quality_score desc`).

If NOT set, use the hardcoded demo data object below. The UI should work identically either way. Show a small pill badge in the top-right corner of the hero: green "● LIVE DATA" if Supabase is connected, slate "● DEMO DATA" if not.

**Hardcoded demo data (use when Supabase is not connected):**

```typescript
const DEMO_DATA = {
  player: {
    username: "PickleBill",
    rank: 1,
    xp: 311800,
    level: 18,
    tier: "Gold III",
    badges: 82,
    clipsAnalyzed: 15,
    avgQuality: 7.4,
  },
  highlights: [
    { id: "h1", name: "Epic Rally #427", quality: 8.2, viral: 8.5, espnCommentary: "An absolute clinic at the kitchen line — PickleBill extends this rally to 14 shots with surgical dink placement before closing with a cross-court winner.", summary: "Extended kitchen rally ending in a decisive winner.", brands: ["JOOLA", "LIFE TIME PICKLEBALL"], arc: "comeback" },
    { id: "h2", name: "ATP Slam #89", quality: 8.0, viral: 9.1, espnCommentary: "That is a professional-grade around-the-post shot. Full extension, perfect angle — this clip is going viral.", summary: "Around-the-post ATP winner off a wide ball.", brands: ["Selkirk"], arc: "highlight_reel" },
    { id: "h3", name: "Tag Team Takedown #12", quality: 7.8, viral: 7.2, espnCommentary: "Elite communication between partners. This is doubles pickleball played at its peak — 11-shot coordinated point.", summary: "11-shot coordinated doubles point showing elite partner sync.", brands: ["LIFE TIME PICKLEBALL", "Recovery Cave"], arc: "teamwork" },
    { id: "h4", name: "Speed Run #34", quality: 7.5, viral: 8.0, espnCommentary: "He just went full speed through four defenders at the transition zone. That reaction time is measurably elite.", summary: "Transition zone speed burst catch-and-finish.", brands: ["HEAD"], arc: "athletic_feat" },
    { id: "h5", name: "Erne Machine #7", quality: 7.4, viral: 7.8, espnCommentary: "The erne is one of pickleball's highest-skill shots — and PickleBill nails it with textbook footwork.", summary: "Clean erne execution off a wide dink.", brands: ["JOOLA", "Recovery Cave"], arc: "skill_showcase" },
    { id: "h6", name: "Comeback King #51", quality: 7.2, viral: 6.9, espnCommentary: "Down 9-2 and he goes on a 9-0 run. That is mental toughness on display.", summary: "9-0 scoring run from a 9-2 deficit.", brands: ["LIFE TIME PICKLEBALL"], arc: "comeback" },
    { id: "h7", name: "Kitchen Sniper #18", quality: 7.0, viral: 7.1, espnCommentary: "Every dink lands within 6 inches of the NVZ line. That consistency is data-verified.", summary: "Precision dinking sequence with sub-6-inch placement.", brands: ["JOOLA"], arc: "precision" },
  ],
  brands: [
    { name: "JOOLA", count: 4 },
    { name: "LIFE TIME PICKLEBALL", count: 3 },
    { name: "Recovery Cave", count: 3 },
    { name: "Selkirk", count: 2 },
    { name: "HEAD", count: 1 },
  ],
  skillRadar: [
    { axis: "Court Coverage", value: 88 },
    { axis: "Kitchen Mastery", value: 92 },
    { axis: "Creativity", value: 79 },
    { axis: "Athleticism", value: 84 },
    { axis: "Court IQ", value: 91 },
    { axis: "Power Game", value: 76 },
  ],
  totalClips: 4097,
  totalVenues: 1,
  totalBrandsDetected: 47,
}
```

---

### Section 1 — Hero KPIs

Full-width dark hero section, `py-16 px-8`, centered.

Top row (above KPIs):
- Small eyebrow text: "PICKLE DaaS — AI Sports Intelligence Platform"
- H1: "Every Rally. Every Brand. Every Player. Automatically." — large, bold, white
- Subtext in slate-400: "Real Gemini AI analysis of pickleball highlights at scale."
- Live/Demo pill badge (top-right corner of the whole page header area)

KPI row — 4 stat cards side by side (2x2 on mobile), each card `bg-slate-900 border border-slate-800 rounded-xl p-6`:
1. **Total Clips Analyzed** — animate count-up to `4,097` on mount
2. **Avg Quality Score** — animate count-up to `7.4` (one decimal)
3. **Brands Detected** — animate count-up to `47`
4. **Players Profiled** — animate count-up to `25+`

**Animated count-up implementation:** Use `useEffect` + `requestAnimationFrame`. Each number animates from 0 to its target over 1800ms with an ease-out curve (`progress = 1 - Math.pow(1 - t, 3)`). The accent green color (`#00E676`) applies to the number itself. Label text is slate-400 below each number.

---

### Section 2 — Player Card (PickleBill)

Card: `bg-slate-900 border border-slate-800 rounded-2xl p-6 max-w-2xl mx-auto`

Left side: circular avatar placeholder (initials "PB" in a green ring, 64px), right side: player stats in two columns:
- Row 1: **Username** "PickleBill" (large, white) | **Global Rank** "#1" (green, bold)
- Row 2: **XP** "311,800" | **Level** "18 — Gold III"
- Row 3: **Badges Earned** "82" | **Clips Analyzed** "15"
- Row 4: **Avg Clip Quality** "7.4 / 10" with a thin progress bar filled to 74% in green

Below the stats, a small note in slate-500 italic: "PickleBill is The Underground's #1 ranked player and the proof-of-concept subject for Pickle DaaS."

---

### Section 3 — Performance DNA Radar Chart

Section heading: "PickleBill Performance DNA" with a green underline accent.

Use Recharts `RadarChart` with `PolarGrid`, `PolarAngleAxis`, `Radar`. Single radar trace filled with `#00E676` at 30% opacity, stroke `#00E676`, stroke width 2.

6 axes from `skillRadar` data: Court Coverage, Kitchen Mastery, Creativity, Athleticism, Court IQ, Power Game. Values 0–100. Chart is 380x380, centered in a `bg-slate-900 rounded-2xl` card. Add a subtle tooltip on hover showing the axis name and value.

---

### Section 4 — Highlights Grid

Section heading: "Top Analyzed Highlights"

Responsive grid: `grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4`

Each highlight card (`bg-slate-900 border border-slate-800 rounded-xl overflow-hidden cursor-pointer hover:border-green-500 transition-colors`):
- Top: gray placeholder thumbnail area (`bg-slate-800 h-36 flex items-center justify-center`) with a play icon and the clip name
- Quality score badge: top-right corner, `bg-green-500 text-black text-xs font-bold px-2 py-1 rounded-bl-lg`
- Bottom: clip name, brand tags as small pills (`bg-slate-700 text-slate-300 text-xs px-2 py-0.5 rounded-full`), story arc tag

**Click to expand inline:** Clicking a card should expand it in place (not a modal) by toggling a `isExpanded` state. When expanded, show:
- ESPN commentary (full text, italic, slate-300)
- Clip summary
- Viral potential score with a thin bar
- A "Collapse" link

---

### Section 5 — Brand Intelligence

Section heading: "Brand Intelligence" with subtext: "Automatically detected across all analyzed clips."

Two-column layout (stacks on mobile):

**Left — Top Brands Bar Chart:** Recharts `BarChart` horizontal. Each bar is green (`#00E676`), brand name on Y axis, count on X axis. Bar height 32px, gap 8px. Chart width 100%.

**Right — Brand Intel Copy:**
- Stat: "5 unique brands detected across 15 clips"
- Bullet list (slate-300 text, green dot bullets):
  - "JOOLA appears in 4 of 15 clips (27% brand presence)"
  - "LIFE TIME PICKLEBALL — 3 clips (venue brand)"
  - "Recovery Cave — 3 clips (health/wellness category)"
  - "Selkirk — 2 clips (paddle brand, premium tier)"
- Pitch line below in green italic: "At 1,000 venues × 4,097 clips each = 4,097,000 brand touchpoints waiting to be monetized."

---

### Section 6 — Scale Pitch

Full-width section `bg-slate-900 py-16 px-8`, centered text.

Large heading (white, 3xl–4xl): "One venue. 4,097 highlights. 15 analyzed."

Below, animated multiplier in a row:
- `4,097` clips × `1,000` venues = **`4,097,000`** data points
- The final number should be in green and large (text-4xl font-bold)

Below that, three `bg-slate-800 rounded-xl p-6` stat cards in a row:
- "~$0.004 per clip analyzed (Gemini Flash pricing)"
- "~$16K to analyze every Courtana highlight today"
- "Resell intelligence at $0.10–$1.00 per insight"

---

### Section 7 — Closing Quote

Full-width section, dark background, centered, `py-20`:

Large italic quote (text-3xl, white, max-w-3xl mx-auto):
> "What would you do with the world's largest corpus of pickleball intelligence?"

Below the quote, a thin green horizontal rule (w-24, h-1, mx-auto, bg-green-500).

---

### Section 8 — CTA

Centered section `py-12`:

Text: "Pickle DaaS is live and generating real data today."

Primary button: `bg-green-500 hover:bg-green-400 text-black font-bold px-8 py-4 rounded-xl text-lg` — label "Talk to us →" — links to `mailto:bill@courtana.com`

Below: `text-slate-500 text-sm` — "bill@courtana.com · courtana.com"

---

### Mobile Responsiveness

- All grids collapse to single column below `sm:` breakpoint
- KPI row: 2×2 grid on mobile
- Radar chart: max-width 100%, overflow hidden
- All font sizes step down one level on mobile (use responsive Tailwind classes)
- Touch targets minimum 44px height on all interactive elements

---

### No External Dependencies Beyond

- `react`, `recharts`, `@supabase/supabase-js` (only if Supabase env var is set), `tailwindcss`, `shadcn/ui` (Card, Badge components only)
- No router needed — this is a single page

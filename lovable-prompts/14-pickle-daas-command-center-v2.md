# Lovable Prompt 14: Pickle DaaS Command Center V2
# Paste this entire prompt into Lovable. Make sure workspace knowledge is loaded first.
# This is the hero product — the thing Bill shows everyone.

---

## What to Build

Build a **Pickle DaaS Command Center** — a premium dark-mode dashboard that serves as the single entry point for ALL Courtana data intelligence. This is what Bill opens on his phone every morning and what he sends to investors, venue operators, and partners.

It pulls LIVE data from GitHub Pages JSON endpoints. No hardcoded data. Real clips. Real numbers.

---

## Design System (Non-Negotiable)

- **Background:** `#0a0e17` (near-black with blue undertone)
- **Surface cards:** `#111827` with `border border-white/[0.06]`
- **Accent green:** `#00E676` (Courtana signature)
- **Accent amber:** `#F59E0B` (warnings, highlights)
- **Text primary:** `#F1F5F9`
- **Text secondary:** `#94A3B8`
- **Font:** System stack (-apple-system, Inter fallback)
- **Border radius:** `rounded-xl` on cards, `rounded-lg` on buttons
- **Hover states:** `hover:border-white/[0.12] transition-all duration-300`
- **Card pattern:** `bg-[#111827]/80 backdrop-blur-sm rounded-xl p-6 border border-white/[0.06]`
- **NO light mode. NO gradients on backgrounds. NO generic SaaS aesthetics.**
- **Skeleton loaders** while data fetches (shimmer animation, not spinners)
- **Framer Motion** for mount animations (fade-up, stagger children)
- **Mobile-first** — test at 375px width. Cards stack vertically.

---

## Data Sources (Fetch from these URLs)

All data lives at `https://picklebill.github.io/pickle-daas-data/`

```typescript
const DATA_URLS = {
  corpus: 'https://picklebill.github.io/pickle-daas-data/corpus-export.json',
  enriched: 'https://picklebill.github.io/pickle-daas-data/enriched-corpus.json',
  stats: 'https://picklebill.github.io/pickle-daas-data/dashboard-stats.json',
  players: 'https://picklebill.github.io/pickle-daas-data/player-profiles.json',
  badges: 'https://picklebill.github.io/pickle-daas-data/creative-badges.json',
  voices: 'https://picklebill.github.io/pickle-daas-data/voice-manifest.json',
} as const;
```

### TypeScript Interfaces

```typescript
interface CorpusClip {
  uuid: string;
  video_url: string;        // https://cdn.courtana.com/files/.../clip.mp4
  thumbnail: string;         // https://cdn.courtana.com/files/.../thumb.jpeg
  quality: number;           // 1-10
  viral: number;             // 1-10
  watchability: number;      // 1-10
  arc: StoryArc;
  summary: string;
  dominant_shot: ShotType;
  total_shots: number;
  brands: string[];
  badges: string[];
  ron_burgundy: string;      // Comedic AI commentary
  social_caption: string;
  skills: SkillRatings;
  model: 'gemini-2.5-flash' | 'claude-sonnet-4-20250514';
}

interface SkillRatings {
  court_coverage: number;    // 0-10
  kitchen: number;           // 0-10 — THE key metric
  creativity: number;
  athleticism: number;
  court_iq: number;
  power: number;
}

interface PlayerProfile {
  username: string;
  clipCount: number;
  avgSkills: Record<string, number>;
  topBrands: string[];
  badges: string[];
  dominantShot: string;
  avgQuality: number;
  avgViral: number;
}

interface CreativeBadge {
  name: string;
  criteria: string;
  clips: string[];           // UUID array
}

type StoryArc = 'grind_rally' | 'athletic_highlight' | 'clutch_moment' | 'pure_fun' | 'teaching_moment' | 'error_highlight' | 'dominant_performance';
type ShotType = 'dink' | 'drive' | 'volley' | 'drop' | 'serve' | 'dink_to_speed_up';
```

---

## Page Structure

### 1. Hero Stats Bar (top of page)
Horizontal row of 5 animated KPI cards. Numbers count up on mount (use `useEffect` with `requestAnimationFrame`).

| Stat | Source | Format |
|------|--------|--------|
| Total Clips | `corpus.length` | "190+" with animated count-up |
| Cost Per Clip | hardcode "$0.005" | Green text, dollar sign |
| Brands Detected | `new Set(corpus.flatMap(c => c.brands)).size` | Number |
| Players Profiled | `players.length` | Number |
| AI Models | "2" (Gemini + Claude) | With model icons |

Each card: small label on top (text-xs uppercase tracking-wider text-slate-400), big number below (text-3xl font-bold tabular-nums).

### 2. Clip Intelligence Grid
Filterable, searchable grid of clips. This is the core feature.

**Filter bar:** Horizontal scroll of pill buttons
- Story Arc: All | Grind Rally | Athletic Highlight | Clutch Moment | etc.
- Shot Type: All | Dink | Drive | Volley | Drop | Serve
- Quality: slider 1-10
- Search: text input searching `summary` field

**Clip cards** (responsive grid: 1 col mobile, 2 tablet, 3 desktop):
- Thumbnail image from `thumbnail` URL (lazy load, aspect-ratio 16/9)
- Overlay badge: quality score (top-right, green if ≥7, amber if 5-6, red if <5)
- Below image:
  - Story arc pill (color-coded: grind=blue, athletic=green, clutch=amber, fun=purple)
  - Summary text (2 lines, truncated)
  - Shot type + total shots
  - Brand pills (small, gray bg)
- **Click → expand modal:**
  - HTML5 video player (source: `video_url`)
  - 6-axis skill radar chart (Recharts RadarChart)
  - Ron Burgundy quote (italic, with 🎙️ icon)
  - Social caption (copyable)
  - Badge list
  - Model badge (Gemini blue or Claude amber)

### 3. Kitchen Mastery Spotlight
**This is the money section.** Full-width card with:
- Headline: "Kitchen Mastery — The Metric That Matters"
- Subhead: "Kitchen scores track linearly with player skill level. This is what coaches sell."
- Chart (Recharts BarChart): X-axis = skill brackets (3.0, 3.5, 4.0+), Y-axis = avg kitchen score
  - Compute from corpus: group clips by estimated skill level, average `skills.kitchen`
  - Bars colored with green gradient
- Below chart: "The 4.0 Fingerprint" callout card
  - "Speed-up → Block → Speed-up: this attack chain appears exclusively in 4.0+ footage"
  - Confidence badge: 81.9

### 4. Player Profiles Section
**Horizontal scrollable row** of player cards (like Spotify artist cards).

Each card:
- Username (bold)
- Clip count badge
- Mini radar chart (6 axes, filled area)
- Dominant shot pill
- Top 2 brands
- Avg quality score

Click → full profile modal:
- Large radar chart
- All badges earned
- Clip history (thumbnails of their clips)
- Stat comparison vs corpus average

### 5. Brand Intelligence
Two-column layout (stacks on mobile):

**Left: Top Brands bar chart**
- Horizontal bars, sorted by frequency
- Brand name + count + percentage bar
- Green fill proportional to frequency

**Right: Sponsorship Whitespace**
- Cards for brands NOT present that should be: Gatorade, Nike, Adidas, Wilson, Head
- Each card: brand name, "0 appearances", amber dashed border
- Subtext: "Potential sponsor — not yet detected in corpus"

### 6. The Pitch (bottom section)
Dark card with gradient border (green → transparent).

- "Courtana Data Intelligence"
- Logo: `<img src="https://cdn.courtana.com/static/img/Courtana_Logo.png" />`
- Animated counter: "[corpus.length] clips × 1,000 venues = [corpus.length * 1000] data points"
- Three proof points in a row:
  - "$0.005/clip" | "99% margins" | "Fully automated"
- CTA: "bill@courtana.com" (mailto link)

### 7. Data Quality Footer
Small, honest section at bottom (text-sm, muted):
- "Data from [corpus.length] clips, primarily single-venue. Confidence capped at 75% for non-random samples."
- "Verification: 20% brand detection agreement, 45% skill level agreement across re-analysis runs."
- "Aggregate patterns are reliable. Individual clip data has variance."
- Link: "View methodology →" (could link to a future page)

---

## Technical Requirements

- **React + TypeScript + Vite**
- **Tailwind CSS** (utility classes only, no custom CSS file)
- **shadcn/ui** components themed to dark mode
- **Recharts** for all charts (RadarChart, BarChart, PieChart)
- **Framer Motion** for mount animations and modal transitions
- **Lucide React** for icons
- All data fetched on mount with `useEffect` + `fetch`
- Skeleton loaders (shimmer) while loading
- Error state: "Unable to load data — check your connection" with retry button
- Mobile responsive: all grids collapse to single column at sm breakpoint
- Video player: native HTML5 `<video>` with controls, poster = thumbnail
- Lazy load images with `loading="lazy"`
- No localStorage (not supported in this environment)

---

## What This Is NOT

- NOT a booking system (Courtana is booking-agnostic)
- NOT a membership platform
- NOT replacing CourtReserve or any venue management tool
- This is a DATA INTELLIGENCE dashboard — it shows what AI can extract from pickleball video

---

## Supabase (Future-Ready)

Don't connect Supabase yet, but structure the data fetching so it's easy to swap:

```typescript
// Current: fetch from gh-pages
const fetchCorpus = async () => {
  const res = await fetch(DATA_URLS.corpus);
  return res.json() as Promise<CorpusClip[]>;
};

// Future: swap to Supabase
// const fetchCorpus = async () => {
//   const { data } = await supabase.from('clips').select('*');
//   return data as CorpusClip[];
// };
```

---

## Quality Checklist (Before Shipping)

- [ ] All data fetches from live gh-pages URLs (no hardcoded arrays)
- [ ] Skeleton loaders visible while loading
- [ ] Error state renders if fetch fails
- [ ] Video plays in modal on click
- [ ] Radar chart renders with real skill data
- [ ] Kitchen Mastery chart shows real computed averages
- [ ] Brand bar chart populates from corpus data
- [ ] Count-up animations on hero stats
- [ ] Mobile: single column, cards stack, horizontal scroll where needed
- [ ] No console errors
- [ ] Courtana logo loads from CDN
- [ ] Dark theme only — no white backgrounds anywhere

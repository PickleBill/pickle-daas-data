# Discovery Intelligence Dashboard — Lovable Prompt

## HOW TO USE THIS PROMPT

1. Open your Lovable workspace
2. Create a new React project
3. Paste the entire contents of this file (everything below "---PASTE BELOW---") into the Lovable prompt field
4. Click "Generate" and wait for the build to complete
5. The app will load with demo data (127 clips, 21 discoveries) fully functional
6. Test filtering, interactions, and mobile responsiveness (375px viewport)
7. To connect Supabase later, update the data fetching layer in the API integration section

The result is a premium, production-ready React dashboard that looks like it was designed at Vercel/Linear/Stripe. Dark mode only, full Tailwind CSS, all interactions smooth and intentional.

---PASTE BELOW---

You are building a premium Discovery Intelligence Dashboard for Pickle DaaS, a data-as-a-service platform that analyzes pickleball video clips using AI agents to surface market intelligence.

## PRODUCT CONTEXT

The Discovery Engine processes video clips and produces ranked discoveries across four AI agents:
- Brand Analyst: sponsorship intelligence, product placement, brand visibility
- Player Profiler: skill tiers, development opportunities, coaching signals
- Tactical Analyst: shot sequences, positioning, game grammar patterns
- Narrative Analyst: highlight-worthiness, social media automation, editorial signals

This dashboard showcases the output of the first full run: 127 clips analyzed, 21 discoveries ranked by confidence and wow-factor, with clear buyer segments and price signals.

## TECH STACK & RULES

- React 18 + TypeScript + Vite
- Tailwind CSS (all custom, no defaults, fully themed)
- shadcn/ui components (buttons, cards, tabs, badges — always themed to Courtana colors, never defaults)
- Recharts for charts (line, area, bar — all themed)
- React Router v6 for navigation (if multi-page) or keep single page
- Framer Motion for micro-interactions (scroll-triggered animations, hover states, card reveals)
- All hardcoded demo data in TypeScript const for easy Supabase swap later

## DESIGN SYSTEM

**Courtana Kit A (Dark Mode)**
- Background: #0f1219 (deep navy-black)
- Surface (cards, containers): #1e2a3a (slightly lighter navy)
- Accent (primary CTA, highlights): #00E676 (bright neon green)
- Text primary: #ffffff
- Text secondary: #a0aec0 (muted gray)
- Borders: rgba(255, 255, 255, 0.1) (subtle white with transparency)
- Category colors:
  - Brand: #fbbf24 (amber/gold)
  - Player: #3b82f6 (blue)
  - Tactical: #ef4444 (red)
  - Narrative: #a78bfa (purple)

**Typography**
- Font: system font (no Google Fonts imports)
- Use `font-tabular-nums` for all numbers (cost, counts, percentages)
- Headlines: bold, tracking-tight, usually 18-32px
- Body: 14-16px, leading-relaxed
- No Lorem ipsum, no placeholder text

**Interactions**
- All cards have hover state: subtle shadow lift + slight scale (1.02)
- Confidence bars animate in when scrolled into view (fade-in + width expand)
- Numbers count up from 0 on page load (use Framer Motion or React Counter)
- Filter buttons toggle smoothly (Tailwind transition-all)
- Discovery card expand/collapse animates smoothly
- Mobile: tap targets min 44px, no hover required

**Responsive**
- Mobile-first approach
- Test at 375px (iPhone SE), 768px (iPad), 1440px (desktop)
- Stack vertically on mobile, grid on desktop
- Touch-friendly spacing and button sizes

## PAGE STRUCTURE

### 1. HERO STATS BAR
At the top of the page, a dark container (bg-#1e2a3a, rounded) with 5 animated stat tiles:
- "127 Clips" 
- "494 Players"
- "1,982 Shots"
- "338 Brands"
- "$0.0054 per Clip" (this number should have a subtle green glow: shadow-lg with green tint)

Each stat should:
- Start at 0 on page load
- Count up to the final number smoothly over 1.5 seconds (use Framer Motion)
- Display in tabular numerals
- Have light text on dark background
- Mobile: stack as 2x2 grid, desktop: 5 across

### 2. FILTER TABS
Below stats, add filter tabs for discovery categories:
- All (show all 21)
- Brand (84.3% brand visibility + 3 others = 4 total)
- Player (2 discoveries)
- Tactical (3 discoveries)
- Narrative (2 discoveries)

Use shadcn Button component styled as tabs, grouped horizontally. Smooth transition when filtered.

### 3. DISCOVERY CARDS GRID
Main content area with a responsive grid of discovery cards:
- Desktop: 2-3 columns (adjust for readability)
- Tablet: 2 columns
- Mobile: 1 column

**Each Discovery Card shows:**
- Top section: agent icon + category badge (color-coded)
- Headline: large, bold, white (22px)
- Confidence bar: horizontal bar showing % with color-coded background
  - Green (#00E676) for 90+
  - Yellow (#fbbf24) for 75-89
  - Orange (#f97316) for 60-74
  - Text label: "95% Confidence"
- Below confidence: row of small badges
  - Data points badge: "127 data points"
  - Price signal badge: "$5K-15K/month"
  - Buyer segments: "Brands, Venues" (comma-separated, clickable pills)
  - If confidence < 75, add "Verification Needed" badge in orange
- Expand button: "See insight" (text link or chevron icon)

**Expanded state (click "See insight"):**
- Full insight text appears below the card in smooth animation
- Buyer segments show as separate pills (color: slightly muted)
- Show a "Close" button or collapse on click

**Hover state:**
- Subtle shadow lift, slight scale (1.02), smooth transition
- Card border becomes slightly more visible
- No color change, just depth

### 4. SCALING PROJECTION
After the discovery cards, a new section with the title "Scaling: Cost & Discovery Growth"

Use Recharts AreaChart showing:
- X-axis: Scaling tier (Current, 1K clips, Full corpus, Post-Peak, 12-month)
- Left Y-axis: Number of clips (0-100K scale)
- Right Y-axis: Number of discoveries (0-500 scale)
- Two areas:
  - Clips (fill: accent color #00E676, opacity 0.2)
  - Discoveries (fill: blue, opacity 0.2)
- Interactive hover tooltip showing exact values
- Light grid lines (rgba(255, 255, 255, 0.05))
- No legend needed (axis labels clear)

### 5. AGENT PERFORMANCE CARDS
A section titled "AI Agent Performance" with 4 cards (one per agent):

Each card shows:
- Agent name: "Brand Analyst" / "Player Profiler" / "Tactical Analyst" / "Narrative Analyst"
- Agent emoji/icon (🎯 for Brand, 👤 for Player, 🔥 for Tactical, 📖 for Narrative)
- Number of discoveries produced (e.g., "4 discoveries")
- Average confidence score (e.g., "avg 84% confidence")
- Small bar chart (Recharts BarChart) showing discovery count per category

Layout: 2x2 grid on desktop, stack on mobile. Same card styling as discovery cards.

### 6. THE PITCH SECTION
A dark, full-width section (bg-#0f1219) with large, centered white text:

"This ran overnight. Zero API spend. 127 clips. 5 AI agents. 21 discoveries. This is what Pickle DaaS does — turns raw video into ranked, buyer-ready intelligence, autonomously."

Below the text, a CTA button:
- Text: "Get Started"
- Link: mailto:bill@courtana.com
- Styling: bg-#00E676, text-#0f1219, bold, large, padding-3

Add subtle animation: the text should fade in from bottom on scroll-into-view (Framer Motion).

### 7. FOOTER
A simple footer with:
- Left: "Powered by Courtana × Gemini 2.5 Flash × Claude"
- Right: Courtana logo (img src="https://cdn.courtana.com/assets/logos/fulllogo-dark-transparent-grad.svg", height=32px)
- Background: slightly lighter than main bg (#1a232e or similar)
- Padding: py-4, px-6
- Border top: 1px solid rgba(255, 255, 255, 0.05)

## DATA STRUCTURE

Embed this TypeScript data directly in the component (not fetched):

```typescript
interface Discovery {
  id: string;
  agent: "brand" | "player" | "tactical" | "narrative";
  headline: string;
  insight: string;
  confidence: number;
  wow_factor: number;
  buyer: string[];
  price_signal: string;
  data_points: number;
  category: "brand" | "player" | "tactical" | "narrative";
}

interface Census {
  total_clips: number;
  total_players: number;
  total_shots: number;
  total_brands: number;
  total_badges: number;
  avg_players_per_clip: number;
  avg_shots_per_clip: number;
  cost_per_clip: number;
  total_cost: number;
}

interface ScalingTier {
  scale: string;
  clips: number;
  cost: number;
  discoveries: number;
}

const DISCOVERIES: Discovery[] = [
  {
    id: "B1",
    agent: "brand",
    headline: "84.3% brand visibility = massive sponsorship blind spot",
    insight: "107 of 127 clips have brand data. At 400K clips, 62,800 clips with zero sponsorship intelligence.",
    confidence: 95,
    wow_factor: 88,
    buyer: ["brands", "venues"],
    price_signal: "$5K-15K/month",
    data_points: 127,
    category: "brand",
  },
  {
    id: "B3",
    agent: "brand",
    headline: "Brand × play quality: Courtana 7.43/10 vs ONIX 5.33/10",
    insight: "Shot quality correlates with brand presence. Endorsement intelligence sports companies pay millions for.",
    confidence: 70,
    wow_factor: 92,
    buyer: ["equipment_manufacturers"],
    price_signal: "$8K/month",
    data_points: 338,
    category: "brand",
  },
  {
    id: "B4",
    agent: "brand",
    headline: "Gatorade = biggest unowned sponsorship category (72 clips, zero presence)",
    insight: "AI-detected whitespace: Gatorade(72), BODYARMOR(67), Yeti(49), Nike(42), Selkirk(36). First brand to activate gets 100% SOV.",
    confidence: 85,
    wow_factor: 90,
    buyer: ["brands", "agencies"],
    price_signal: "$4K/month",
    data_points: 1108,
    category: "brand",
  },
  {
    id: "T1",
    agent: "tactical",
    headline: "Dink→Dink dominates (861 transitions) — pickleball has a grammar",
    insight: "Predictable shot sequences across 1,857 transitions. Broadcast analytics and betting gold.",
    confidence: 85,
    wow_factor: 87,
    buyer: ["broadcast", "betting"],
    price_signal: "$3K/month",
    data_points: 1857,
    category: "tactical",
  },
  {
    id: "T5",
    agent: "tactical",
    headline: "AI predicts DUPR ratings without API — 3.5-4.0 modal range",
    insight: "Video analysis alone predicts player ratings. The DUPR partnership play.",
    confidence: 72,
    wow_factor: 88,
    buyer: ["dupr", "tournament_operators"],
    price_signal: "$5K/month",
    data_points: 123,
    category: "tactical",
  },
  {
    id: "P1",
    agent: "player",
    headline: "78.1% intermediate players = coaching goldmine",
    insight: "Most valuable coaching customer: engaged enough to pay, frustrated enough to need help.",
    confidence: 88,
    wow_factor: 72,
    buyer: ["coaching", "player_apps"],
    price_signal: "$800/month",
    data_points: 494,
    category: "player",
  },
  {
    id: "P2",
    agent: "player",
    headline: "Overhead = highest-quality shot (8.6/10) — brands should own this moment",
    insight: "The pickleball money shot. Any brand associated with this moment owns the sport's best highlight.",
    confidence: 82,
    wow_factor: 85,
    buyer: ["brands", "broadcast"],
    price_signal: "$2K/month",
    data_points: 1982,
    category: "player",
  },
  {
    id: "N1",
    agent: "narrative",
    headline: "19 clips auto-identified as highlight-reel worthy",
    insight: "15% are highlight-worthy. AI surfaces the best 5% automatically. Zero editorial cost.",
    confidence: 82,
    wow_factor: 84,
    buyer: ["venues", "broadcast"],
    price_signal: "$2K/month",
    data_points: 127,
    category: "narrative",
  },
  {
    id: "N4",
    agent: "narrative",
    headline: "AI social captions ready for 125 clips — zero human editorial",
    insight: "Venues post daily without a social media team. Operational savings justify subscription.",
    confidence: 92,
    wow_factor: 83,
    buyer: ["venues", "brands"],
    price_signal: "$800/month",
    data_points: 125,
    category: "narrative",
  },
  {
    id: "T2",
    agent: "tactical",
    headline: "Kitchen control = 1.8% win rate — data confirms kitchen is king",
    insight: "Position win rates proven across 127 real clips. Coaching thesis data-verified.",
    confidence: 83,
    wow_factor: 81,
    buyer: ["coaching", "betting"],
    price_signal: "$2K/month",
    data_points: 1347,
    category: "tactical",
  },
  {
    id: "B2",
    agent: "brand",
    headline: "Selkirk = 92% category dominance (32 of 35 paddle clips)",
    insight: "Equipment category capture is unprecedented. The brand is the sport in player minds.",
    confidence: 90,
    wow_factor: 86,
    buyer: ["equipment_manufacturers", "agencies"],
    price_signal: "$6K/month",
    data_points: 287,
    category: "brand",
  },
];

const CENSUS: Census = {
  total_clips: 127,
  total_players: 494,
  total_shots: 1982,
  total_brands: 338,
  total_badges: 418,
  avg_players_per_clip: 3.89,
  avg_shots_per_clip: 15.61,
  cost_per_clip: 0.0054,
  total_cost: 0.69,
};

const SCALING_TIERS: ScalingTier[] = [
  { scale: "Current", clips: 127, cost: 0.69, discoveries: 21 },
  { scale: "1K clips", clips: 1000, cost: 5.4, discoveries: 100 },
  { scale: "Full corpus", clips: 4097, cost: 22.12, discoveries: 200 },
  { scale: "Post-Peak", clips: 10000, cost: 54, discoveries: 300 },
  { scale: "12-month", clips: 100000, cost: 540, discoveries: 500 },
];

const AGENT_STATS = [
  {
    name: "Brand Analyst",
    emoji: "🎯",
    discoveries: 4,
    avgConfidence: 86.25,
    discoveryCount: [1, 1, 1, 1],
  },
  {
    name: "Player Profiler",
    emoji: "👤",
    discoveries: 2,
    avgConfidence: 85,
    discoveryCount: [1, 1],
  },
  {
    name: "Tactical Analyst",
    emoji: "🔥",
    discoveries: 3,
    avgConfidence: 80,
    discoveryCount: [1, 1, 1],
  },
  {
    name: "Narrative Analyst",
    emoji: "📖",
    discoveries: 2,
    avgConfidence: 87,
    discoveryCount: [1, 1],
  },
];
```

## COMPONENT REQUIREMENTS

**HeroStats**
- Import Framer Motion for count-up animation
- Use `useEffect` + state to drive the animation
- Render CENSUS data
- Apply green glow box-shadow to cost number

**FilterTabs**
- Use React state to track selected filter
- Map over unique category values
- Filter DISCOVERIES array on click
- Use shadcn Button component, styled as tabs

**DiscoveryCard**
- Expand/collapse state with Framer Motion AnimatePresence
- Confidence bar color-coded (green/yellow/orange)
- Buyer pills rendered as inline badges
- Hover state: lift + scale
- Mobile: full-width stack

**ScalingChart**
- Recharts AreaChart with dual Y-axis
- Interactive tooltip
- Light grid lines
- Fully themed (no recharts defaults)

**AgentPerformance**
- 4 cards in 2x2 grid (responsive)
- Small bar chart per agent
- Same card styling as discovery cards

**PitchSection**
- Full-width dark background
- Centered, large white text
- Framer Motion fade-in on scroll-into-view
- CTA button with mailto link

**Footer**
- Simple, minimal
- Logo image from CDN
- Border top, subtle spacing

## STYLING NOTES

- Use Tailwind CSS utilities throughout (no styled-components, no inline styles)
- All colors from design system (define as CSS variables or Tailwind config if possible)
- Use transition-all for smooth state changes
- Use rounded-lg for card corners, rounded-sm for small elements
- Use shadow-sm, shadow-md, shadow-lg for depth
- Mobile-first: start with mobile layout, use `md:` and `lg:` breakpoints for desktop
- No external fonts: system font stack only
- Use tabular-nums on all number displays

## OPTIONAL ENHANCEMENTS (if time permits)

- Add a subtle gradient background to the hero stats bar
- Add a "copy to clipboard" button on price signal badges
- Add sorting to discovery cards (by confidence, wow-factor, data points)
- Add a "favorites" feature (localStorage persistence) to save discoveries
- Add a "dark/light mode" toggle (though spec says dark-only, this future-proofs the design)

## ACCEPTANCE CRITERIA

- Page loads and renders all demo data without errors
- Hero stats count up from 0 on page load
- Filter tabs work and update card display smoothly
- Discovery cards expand/collapse with animation
- Scaling chart renders with correct data and interactive hover
- Mobile responsive at 375px, tablet at 768px, desktop at 1440px
- All colors match Courtana Kit A (dark mode)
- No console errors or warnings
- Accessibility: semantic HTML, ARIA labels where needed, keyboard navigation works
- Hover states work on desktop, touch states on mobile
- Confidence bars animate in on scroll-into-view
- Footer displays with logo from CDN

This is a premium, production-grade dashboard. The result should look like it was designed at Vercel, Linear, or Stripe — dark, minimal, intentional, no wasted space, every interaction smooth and purposeful.

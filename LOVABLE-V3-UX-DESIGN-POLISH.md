# Lovable V3 — UX Design Overhaul + Courtana Brand Consistency
_Paste this into the existing Pickle DaaS / PickleStats Hub project as a follow-up prompt_

---

Great progress on the data integration! Now let's do a serious design pass to make this look and feel like a real Courtana product — not a prototype.

## 1. Global Design System — Courtana Brand Tokens

Apply these consistently across EVERY page:

**Color palette:**
- Primary background: `#0B1120` (deep navy, almost black)
- Card background: `#131D2E` (slightly lighter navy)
- Card hover: `#1A2740` (subtle lift)
- Primary accent: `#00E676` (Courtana green — use for CTAs, active states, borders, icons)
- Secondary accent: `#00B8D4` (cyan — use for data visualizations, secondary info)
- Warning/hot: `#FF6B35` (orange — viral scores 7+, alerts)
- Text primary: `#F1F5F9` (near-white)
- Text secondary: `#94A3B8` (muted slate)
- Text muted: `#64748B` (low emphasis)
- Border: `rgba(0, 230, 118, 0.1)` (very subtle green tint)

**Typography:**
- Headings: Inter or system-ui, font-weight 700, tracking tight
- Body: Inter or system-ui, font-weight 400
- Data/numbers: tabular-nums font-variant
- Small labels: uppercase, letter-spacing 0.05em, font-weight 600, text-xs, text-secondary color

**Card system:**
- All cards: `bg-[#131D2E] rounded-xl border border-[rgba(0,230,118,0.1)] p-6`
- Hover: `hover:bg-[#1A2740] hover:border-[rgba(0,230,118,0.25)] transition-all duration-300`
- Active/selected: `border-[#00E676] shadow-[0_0_20px_rgba(0,230,118,0.15)]`
- Section headers inside cards: small green dot or line before the title

**Spacing rhythm:**
- Section gaps: `gap-8` (2rem)
- Card internal padding: `p-6`
- Between label and value: `gap-1`
- Page max-width: `max-w-7xl mx-auto`

## 2. Navigation — Sidebar Redesign

Replace the current top nav with a left sidebar (desktop) / bottom bar (mobile):

**Desktop sidebar (w-64, fixed left):**
- Courtana logo at top (from `https://cdn.courtana.com/static/brand/logo_combined_green.svg`) — if this 404s, use `https://cdn.courtana.com/static/brand/logo_combined.svg`
- Below logo: "PICKLE DaaS" label in small uppercase green text
- Nav items (vertical stack, each with icon + label):
  - 📊 Dashboard (lucide: LayoutDashboard)
  - 🎬 Highlights (lucide: Film)
  - 🧬 Player DNA (lucide: Dna)
  - 🏷️ Brands (lucide: Tag)
  - 🎙️ Voice Lab (lucide: Mic)
- Active item: green left border + green text + subtle green bg
- Inactive: muted text, no border
- Bottom of sidebar: "Powered by Courtana" small text with version number
- Sidebar collapses to icons-only on medium screens (md breakpoint)

**Mobile bottom bar:**
- Fixed bottom, 5 icon buttons
- Active icon = green, inactive = muted slate
- No labels on mobile (icons only)
- Background: `#0B1120` with top border `rgba(0,230,118,0.1)`

## 3. Dashboard Page — ESPN Broadcast Feel

**Hero section (top):**
- Full-width featured clip player — 16:9 aspect ratio, rounded-xl
- Custom video controls: a green progress bar along the bottom, play/pause button (green circle with white triangle), time display
- Overlay at top-left: Courtana logo watermark (20% opacity)
- Overlay at bottom-left: clip name + quality score badge
- Below video: 4 commentary tabs (ESPN, Hype, Ron Burgundy, Chuck Norris) — currently working, keep this

**KPI row (below hero):**
- 4 cards in a row (responsive: 2x2 on tablet, 1 column on mobile)
- Each card:
  - Small icon top-left (green, from lucide)
  - Large number (text-3xl font-bold tabular-nums)
  - Label below (small, uppercase, muted)
  - Subtle sparkline or trend arrow if applicable
- Cards: Clips Analyzed (Film icon), Avg Quality (Star icon), Top Brand (Tag icon), Avg Viral Score (TrendingUp icon)
- On hover: card lifts with green shadow glow `shadow-[0_0_30px_rgba(0,230,118,0.12)]`

**Analytics section:**
- Two-column layout (stacks on mobile):
  - Left: Skill Radar chart (use Recharts RadarChart) — green fill with cyan outline
  - Right: Story Arc distribution (horizontal bar chart or donut)
- Below: Brand Frequency horizontal bar chart — bars animate in from left on mount (stagger 200ms each)

## 4. Highlights Page — Grid Gallery

**Grid layout:** 3 columns (2 on tablet, 1 on mobile), gap-6

**Each card:**
- Video thumbnail area (16:9, rounded-t-xl)
- On hover: video plays (muted autoplay), subtle green border glow
- Quality score: pill in top-right (`bg-[#00E676] text-black font-bold rounded-full px-2 py-0.5`)
- Viral score: pill in top-left (color-coded: red `#FF6B35` for 7+, gold `#FFD700` for 5-6, slate for <5)
- Story arc tag: colored chip below video (athletic_highlight=purple, grind_rally=blue, teaching_moment=green, error_highlight=red, pure_fun=yellow)
- Ron Burgundy quote: italic text, green left border, dark bg panel
- Brand pills: row of small rounded pills at bottom (subtle, muted colors)
- Caption: below everything, text-sm, text-secondary

**Click → Modal:**
- Full-screen overlay with backdrop blur
- Large video player (max-w-4xl centered)
- Below video: tabbed commentary panel
  - Tab row: "Classic Pack" (ESPN, Hype, Ron Burgundy, Chuck Norris) | "TMNT Pack" (Leonardo, Raphael, Donatello, Michelangelo)
  - Each tab shows: character avatar/icon, commentary text, "Play Voice" button
  - While audio plays: animated waveform bars (5 thin green bars that bounce)
- Badges row: predicted badges as pills
- Close button: top-right X

## 5. Player DNA Page — Profile Card + Analytics

**Profile header:**
- Full-width card with gradient bg (`linear-gradient(135deg, #131D2E 0%, #0B1120 100%)`)
- Left side: large avatar area (placeholder circle with initials "PB" in green)
- Right side: Username "PickleBill", Rank #1, XP 283,950, Level 17, Gold III tier badge
- Below: row of stat pills (dominant shot, play style tags as colored chips)

**Skill radar (large, centered):**
- Use Recharts RadarChart with ALL 9 dimensions
- Fill: semi-transparent green
- Outline: solid cyan
- Grid lines: subtle slate
- Labels: outside the radar, white text
- Animate on mount (grow from center)

**Play Style DNA section:**
- Visual "DNA strand" or chip row showing play styles in priority order
- Largest chip = most dominant ("banger"), getting smaller
- Each chip: colored bg matching the style theme

**Coaching AI Insights:**
- Card with green left border (4px solid #00E676)
- Header: "AI Coaching Notes" with Brain icon
- List of coaching tips — NOT bullet points, use green dot indicators
- Each tip: subtle hover highlight

**Story Arc Distribution:**
- Donut chart (Recharts PieChart) showing arc breakdown
- Legend below with colored dots matching the arc colors from Highlights page

## 6. Brands Page — Sponsorship Intelligence

**3 brand cards (horizontal on desktop, vertical on mobile):**
- Brand name large + category label (small, muted)
- Appearance count: large number
- Presence bar: full-width progress bar
  - 100% = solid green
  - <100% = partial green with dark remainder
  - Animate fill on mount (0 → actual %, 800ms ease-out)
- Clip count as secondary stat

**Sponsorship ROI Insight:**
- Special callout card with gold/amber left border
- Contains the sponsorship_insight text from the data
- Small "AI Generated" badge in top-right

**Brand Detection Heatmap:**
- Table with clips as columns, brands as rows
- Green dot = detected, empty cell = not detected
- Header row shows clip short names
- Subtle grid lines

## 7. Voice Lab Page — Character Voice Showcase

**Two voice pack sections:**

**"Classic Voices" section:**
- 4 cards in a row (ESPN, Hype, Ron Burgundy, Chuck Norris)
- Each card: character name, description, waveform preview area, "Play" button
- When playing: green animated waveform bars

**"TMNT Pack" section (NEW):**
- 4 cards: Leonardo (blue accent), Raphael (red accent), Donatello (purple accent), Michelangelo (orange accent)
- Each card gets the Turtle's signature color as the accent instead of green
- Character personality tagline under the name
- Same play functionality but with character-specific commentary text
- Add a fun "COWABUNGA!" button for Michelangelo that plays just that word

**Voice selector:**
- Dropdown or tab row to pick a clip from the highlights
- Once selected, all 8 voice cards show that clip's commentary
- Play buttons use ElevenLabs API (already connected) or browser speechSynthesis fallback

## 8. Footer

- Sticky footer across all pages
- Dark bg (`#080D18`), thin green top border
- Left: "Powered by Courtana · Pickle DaaS · AI-Driven Sports Intelligence"
- Right: link to courtana.com
- Centered: "Built with AI" subtle badge

## 9. Micro-interactions & Polish

- **Page transitions**: fade-in on route change (200ms)
- **Number animations**: KPI numbers count up from 0 on mount (like an odometer)
- **Loading states**: skeleton pulse cards (dark gray rectangles that pulse) while data fetches
- **Scroll animations**: cards fade-in-up as they enter viewport (use IntersectionObserver)
- **Active nav glow**: subtle green pulse on the active sidebar item
- **Video hover preview**: 2-second autoplay preview on highlight cards
- **Toast notifications**: use shadcn/ui toast, green accent, top-right position

## 10. Mobile Responsive

- Sidebar → bottom bar on mobile
- All grids → single column
- KPI cards: 2x2 grid
- Video player: full-width, taller aspect ratio
- Modals: full-screen on mobile
- Font sizes: slightly smaller on mobile (text-sm base)
- Tap targets: minimum 44px height

# Lovable V4 — Interactive Broadcast Mode + Sport Filtering
_Paste this AFTER V3 design polish is applied. This adds the interactive "ESPN control room" feel._

---

## 1. Sport Filter Bar (NEW — Global Component)

Add a sticky filter bar below the sidebar/nav that appears on Dashboard, Highlights, and Brands pages:

**Filter bar design:**
- Horizontal row of sport pills: "All Sports", "Pickleball", "Hockey", "Tennis", "Golf", "Basketball", "Other"
- Each pill has a small sport icon (use lucide: for pickleball use `Gamepad2`, hockey use `Snowflake`, tennis use `CircleDot`, golf use `Flag`, basketball use `Circle`)
- Active pill: filled green bg, white text
- Inactive pill: outlined, muted text
- When a sport is selected, ALL data on the current page filters to that sport
- Filter state persists across page navigation (store in React context)
- Show count badge on each pill: "Pickleball (8)" — number updates dynamically
- The data source `clips-metadata.json` now has a `sport` field on each clip — use it for filtering

## 2. Dashboard — Live Broadcast Mode Toggle

Add a toggle switch in the top-right of the Dashboard page: "Standard View" ↔ "Broadcast Mode"

**Standard View** = the current dashboard layout (KPIs, radar, charts)

**Broadcast Mode** (NEW) — transforms the dashboard into an ESPN-style live production view:

**Layout (broadcast mode):**
- Full-width hero: largest video player possible (70vh height, rounded-xl)
- Below video: horizontal scrolling filmstrip of all clips (small thumbnails, 80px height)
  - Clicking a filmstrip thumb changes the main player
  - Active thumb has green border + glow
  - Filmstrip auto-scrolls to center the active clip

- Right sidebar panel (30% width on desktop, below video on mobile):
  - **Live Stats ticker** — animated rolling text showing:
    - "Quality: 8.0 | Viral: 7 | Arc: Athletic Highlight"
    - Updates when clip changes
    - Green text on dark bg, mono font, slight glow effect
  - **Commentary panel** — shows the active voice's commentary text
    - Voice selector tabs at top (ESPN, Hype, Ron Burgundy, Chuck Norris, + TMNT pack)
    - Text appears with typewriter animation (characters reveal left to right, 30ms per char)
    - "Play Voice" button triggers ElevenLabs/speechSynthesis
  - **Shot breakdown** — mini timeline showing shot types:
    - Horizontal bar with colored segments (serve=blue, drive=green, dink=yellow, overhead=red, volley=purple)
    - Each segment proportional to shot count
    - Hover shows shot details

- Bottom ticker bar (full width, 40px height):
  - Scrolling marquee text: "PICKLE DaaS LIVE • {clip_name} • Quality: {score}/10 • {brand_names} • Powered by Courtana AI"
  - Dark bg, green text, smooth infinite scroll animation
  - Speed: ~60px/second

## 3. Highlights Page — Interactive Grid with Real-Time Preview

**Hover behavior enhancement:**
- On card hover: video starts playing (muted), card scales up 2% (`scale-[1.02]`), shadow intensifies
- A small "LIVE" badge appears in top-left corner with a pulsing red dot
- Quality score ring animates (circular progress around the score number)

**Sort controls (top of grid):**
- Row of sort buttons: "Recent" | "Quality ↓" | "Viral ↓" | "Sport"
- Active sort has green underline
- Changing sort animates cards with a shuffle effect (cards fade out, reorder, fade in)

**Quick Voice Preview:**
- On each highlight card, add a small speaker icon (bottom-right)
- Clicking it plays a 5-second voice preview (uses the Ron Burgundy quote via speechSynthesis)
- While playing: icon pulses green, small waveform animation appears

## 4. Player DNA Page — Interactive Radar

**Radar chart interactivity:**
- Clicking any radar point shows a tooltip with:
  - Skill name and score
  - "How to improve" tip from coaching notes
  - Comparison to average (if available)
- Radar animates on mount: grows from center over 800ms with spring easing
- Add a "Compare" button that overlays an average player radar in cyan (semi-transparent) for contrast

**Play Style Chips — Interactive:**
- Clicking a play style chip filters the Highlights page to clips that match that style
- Chip shows a mini-count: "banger (5 clips)"
- Hover animation: chip grows and shows a tooltip with play style description

## 5. Brands Page — Interactive Heatmap

**Brand Detection Heatmap enhancement:**
- Cells are clickable — clicking a green dot opens that clip's modal
- Row hover: highlights the entire row
- Column hover: highlights the entire column
- Intersection hover: shows tooltip "JOOLA detected in Shot of the Day — Airborne"

**Brand Card interactivity:**
- Clicking a brand card filters Highlights to only show clips where that brand appears
- Presence bar has a tooltip on hover showing exact percentage and clip count
- Add a "View Clips" CTA button on each brand card

## 6. Voice Lab — Live Preview Studio

**Voice comparison mode (NEW):**
- Select a clip from dropdown
- All 8 voice cards (4 classic + 4 TMNT) show simultaneously
- "Play All" button plays each voice in sequence (3-second gap between each)
- While one voice plays, its card has an animated green border glow
- After all play, show a "Vote for Best Voice" interaction (fun, not functional — just captures which one the user clicks)

**Voice waveform visualization:**
- When audio is playing, show a real-time waveform using Web Audio API:
  ```
  const audioContext = new AudioContext()
  const analyser = audioContext.createAnalyser()
  // Connect audio source → analyser → destination
  // Draw frequency data as green bars on a canvas
  ```
- 32 bars, green color, smooth animation
- Bars scale with actual audio amplitude

## 7. Global Micro-Interactions

**Number counters:** All KPI numbers count up from 0 on mount using requestAnimationFrame. Duration: 1.5s, easeOutExpo curve.

**Scroll-triggered animations:** Cards and sections fade-in-up as they enter the viewport. Use IntersectionObserver with threshold 0.1. Stagger children by 100ms.

**Keyboard shortcuts:**
- `1-5`: Switch between pages (Dashboard, Highlights, Player DNA, Brands, Voice Lab)
- `Space`: Play/pause current video
- `B`: Toggle broadcast mode (on Dashboard)
- `←` `→`: Previous/next clip in broadcast mode filmstrip
- Show a small "?" button in bottom-right that opens a keyboard shortcut overlay

**Toast system:** Use shadcn/ui toast for status messages:
- "Playing ESPN commentary..." (when voice starts)
- "Loaded 8 clips" (when data fetches)
- "Filtered: Pickleball (8 clips)" (when sport filter changes)
- Green accent, top-right position, auto-dismiss after 3s

## 8. Performance

- Use React.lazy() for page-level code splitting (each page loads on navigation)
- Memoize expensive computations (filtered clip lists, chart data) with useMemo
- Debounce filter changes by 150ms
- Video elements: add `preload="metadata"` to prevent loading all videos at once
- Images/thumbnails: add loading="lazy"

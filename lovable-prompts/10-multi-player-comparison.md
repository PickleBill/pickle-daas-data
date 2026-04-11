# Lovable Prompt 10 — Multi-Player Comparison Dashboard

## What This Builds
A head-to-head player comparison tool showing side-by-side radar overlays, stat tables, a matchup win prediction, shot preference charts, and a growth gap analysis. Bill uses this in coaching demos and investor walkthroughs.

## Paste This Into Lovable

---

Build a **Multi-Player Comparison Dashboard** — a React app using Tailwind CSS, shadcn/ui Card components, and Recharts. Route: `/compare`.

---

### Theme & Colors

- Background: `bg-slate-950` (#020617)
- Card backgrounds: `bg-slate-900` (#0f172a)
- Card borders: `border-slate-800` (#1e293b)
- Player 1 color: `#00E676` (green — always Player 1)
- Player 2 color: `#F59E0B` (gold/amber — always Player 2)
- Player 3 color: `#60A5FA` (blue — optional third player)
- Accent text: white
- Secondary text: `text-slate-400`

---

### Hardcoded Demo Players

At the top of the component, define this array of 5 players:

```typescript
const DEMO_PLAYERS = [
  {
    id: "picklebill",
    name: "PickleBill",
    rank: 1,
    xp: 311800,
    level: 18,
    clipsAnalyzed: 15,
    avgQuality: 7.4,
    skills: {
      courtCoverage: 88,
      kitchenMastery: 92,
      creativity: 79,
      athleticism: 84,
      courtIQ: 91,
      powerGame: 76,
    },
    shotPreferences: {
      dink: 38,
      drive: 22,
      drop: 18,
      lob: 8,
      erne: 9,
      atp: 5,
    },
    dominantStyle: "Kitchen Architect",
    signatureMove: "Extended dink rally → cross-court winner",
    topBadge: "Epic Rally ×38",
    coachingNote: "Most complete player in the dataset. Kitchen mastery and Court IQ are elite-tier.",
  },
  {
    id: "pronetplayer",
    name: "ProNetPlayer",
    rank: 4,
    xp: 187400,
    level: 14,
    clipsAnalyzed: 12,
    avgQuality: 7.1,
    skills: {
      courtCoverage: 91,
      kitchenMastery: 74,
      creativity: 68,
      athleticism: 89,
      courtIQ: 77,
      powerGame: 83,
    },
    shotPreferences: {
      dink: 22,
      drive: 38,
      drop: 14,
      lob: 6,
      erne: 5,
      atp: 15,
    },
    dominantStyle: "Power Baseliner",
    signatureMove: "Hard drive → ATP finish",
    topBadge: "Speed Demon ×22",
    coachingNote: "Exceptional court coverage and athleticism. Kitchen patience is the growth lever.",
  },
  {
    id: "spindoctor",
    name: "SpinDoctor",
    rank: 7,
    xp: 142200,
    level: 12,
    clipsAnalyzed: 9,
    avgQuality: 6.8,
    skills: {
      courtCoverage: 74,
      kitchenMastery: 81,
      creativity: 94,
      athleticism: 71,
      courtIQ: 83,
      powerGame: 62,
    },
    shotPreferences: {
      dink: 41,
      drive: 14,
      drop: 24,
      lob: 12,
      erne: 7,
      atp: 2,
    },
    dominantStyle: "Creative Disruptor",
    signatureMove: "Spin lob → NVZ reset",
    topBadge: "Artisan ×19",
    coachingNote: "Highest creativity score in dataset. Athleticism and power game limit ceiling.",
  },
  {
    id: "kitchenking",
    name: "KitchenKing",
    rank: 11,
    xp: 98600,
    level: 10,
    clipsAnalyzed: 8,
    avgQuality: 6.5,
    skills: {
      courtCoverage: 69,
      kitchenMastery: 88,
      creativity: 72,
      athleticism: 66,
      courtIQ: 85,
      powerGame: 58,
    },
    shotPreferences: {
      dink: 52,
      drive: 11,
      drop: 21,
      lob: 9,
      erne: 5,
      atp: 2,
    },
    dominantStyle: "NVZ Specialist",
    signatureMove: "Deep dink sequence → patient winner",
    topBadge: "Kitchen Master ×31",
    coachingNote: "Extremely strong NVZ game. Needs athletic development to compete at higher levels.",
  },
  {
    id: "powerslammer",
    name: "PowerSlammer",
    rank: 18,
    xp: 71300,
    level: 8,
    clipsAnalyzed: 7,
    avgQuality: 6.2,
    skills: {
      courtCoverage: 62,
      kitchenMastery: 58,
      creativity: 61,
      athleticism: 87,
      courtIQ: 64,
      powerGame: 91,
    },
    shotPreferences: {
      dink: 18,
      drive: 52,
      drop: 8,
      lob: 4,
      erne: 3,
      atp: 15,
    },
    dominantStyle: "Power Hitter",
    signatureMove: "Aggressive drive → reset error by opponent",
    topBadge: "Hard Hitter ×27",
    coachingNote: "Elite power game but kitchen game is the biggest skill gap in the dataset.",
  },
]
```

---

### Component State

```typescript
const [player1Id, setPlayer1Id] = useState("picklebill")
const [player2Id, setPlayer2Id] = useState("pronetplayer")
const [player3Id, setPlayer3Id] = useState<string | null>(null)
const [showThirdPlayer, setShowThirdPlayer] = useState(false)
```

Derived: `player1 = DEMO_PLAYERS.find(p => p.id === player1Id)`, same for 2 and 3.

---

### Section 1 — Page Header

`bg-slate-900 border-b border-slate-800 px-8 py-6`:

Left: H1 "Player Comparison" text-2xl font-bold white + subtext "Head-to-head coaching intelligence" text-slate-400

Right: small pill `border border-slate-600 text-slate-400 text-xs px-3 py-1 rounded-full` — "Pickle DaaS · Powered by Courtana AI"

---

### Section 2 — Player Selector Row

Full-width card `bg-slate-900 border border-slate-800 rounded-2xl p-6 mx-8 mt-6`:

Heading: "Select Players to Compare" text-sm font-semibold text-slate-400 uppercase tracking-wider mb-4

Three selector columns (flex row, gap-4, wraps on mobile):

**Player 1 column** (green accent border `border-green-500/50`):
- Label: "● Player 1" in green text-sm font-bold
- `<select>` styled `bg-slate-800 border border-slate-700 text-white rounded-lg px-3 py-2 w-full` — options are all 5 player names mapped from DEMO_PLAYERS
- Below: mini stat row showing selected player's rank and avg quality

**Player 2 column** (gold accent border `border-yellow-500/50`):
- Label: "● Player 2" in yellow
- Same select, same mini stats

**Player 3 column** (blue accent border `border-blue-400/50`, grayed out when disabled):
- Toggle: `<button>` — "Add 3rd Player" (when off) / "Remove 3rd Player" (when on)
- If `showThirdPlayer` is true: show the select; otherwise show a dashed placeholder box with `+` icon
- Label: "● Player 3" in blue (only visible when active)

Below the selectors, a row of comparison pills showing selected player names with their respective colors: `[Green dot] PickleBill  vs  [Gold dot] ProNetPlayer`

---

### Section 3 — Radar Chart Overlay

Centered card `bg-slate-900 border border-slate-800 rounded-2xl p-8 max-w-2xl mx-auto mt-6`:

Heading: "Skill Profile Overlay" text-xl font-bold white

Use Recharts `RadarChart` (size 400×400, `cx="50%" cy="50%" outerRadius={160}`):
- `PolarGrid` with stroke `#1e293b`
- `PolarAngleAxis` with `tick={{ fill: '#94a3b8', fontSize: 12 }}`
- One `Radar` per active player:
  - Player 1: `stroke="#00E676" fill="#00E676" fillOpacity={0.15} strokeWidth={2}`
  - Player 2: `stroke="#F59E0B" fill="#F59E0B" fillOpacity={0.15} strokeWidth={2}`
  - Player 3 (if active): `stroke="#60A5FA" fill="#60A5FA" fillOpacity={0.15} strokeWidth={2}`
- `Tooltip` styled dark
- `Legend` below the chart showing colored dots + player names

The 6 axes keys: `courtCoverage`, `kitchenMastery`, `creativity`, `athleticism`, `courtIQ`, `powerGame`

Recharts requires data in the format: `[{ axis: "Kitchen Mastery", p1: 92, p2: 74 }, ...]`

Build a derived `radarData` array from the selected players' skills objects.

---

### Section 4 — Stat Comparison Table

Card `bg-slate-900 border border-slate-800 rounded-2xl overflow-hidden mt-6 mx-8`:

Heading row `bg-slate-800 px-6 py-3 grid grid-cols-4 text-xs font-semibold text-slate-400 uppercase tracking-wider`:
- Columns: "Skill" · "Player 1 [name]" (green header) · "Player 2 [name]" (gold header) · "Difference"

6 data rows (alternating `bg-slate-900` / `bg-slate-800/30`), each `px-6 py-4 grid grid-cols-4 items-center`:
- Col 1: skill name (white)
- Col 2: score with colored bar below it (green fill, proportional width in a `bg-slate-700 h-1.5 rounded-full` bar)
- Col 3: score with gold bar
- Col 4: difference — if P1 > P2 show `+N` in green; if P2 > P1 show `-N` in red; if equal show `—` in slate

Skill order: Court Coverage, Kitchen Mastery, Creativity, Athleticism, Court IQ, Power Game

Footer row `bg-slate-800 px-6 py-3 grid grid-cols-4 font-bold`:
- "Overall Score" (calculated as average of all 6 dimensions)
- P1 average (green)
- P2 average (gold)
- Delta

---

### Section 5 — Matchup Prediction

Card `bg-slate-900 border border-slate-800 rounded-2xl p-8 mt-6 mx-8`:

Heading: "Matchup Prediction" text-xl font-bold white + subtext "Based on skill profile overlap and dominant style interaction" text-slate-400 text-sm

**Prediction logic (hardcoded rules, not real ML):**
```typescript
const p1Avg = average of p1 skills
const p2Avg = average of p2 skills
const p1WinPct = Math.round(50 + (p1Avg - p2Avg) * 2.5)
// clamp between 30 and 70
```

Display:
- Large centered text: "[Player 1 name] wins **{p1WinPct}%** of the time"
- Opposing bar showing P1% in green | P2% in gold — full width, `h-8 rounded-full overflow-hidden flex`
- Below: `text-slate-400 text-sm` — "Confidence: [High/Medium/Low based on score delta]"

**Style matchup note** (text block below the bar):
Map dominant style combinations to a prediction rationale string. Examples:
- "Kitchen Architect" vs "Power Baseliner" → "Kitchen-first players neutralize power hitters at the NVZ. Expect long dink rallies. PickleBill's kitchen mastery is the deciding factor."
- "Creative Disruptor" vs "NVZ Specialist" → "Both players favor soft game — this match comes down to who makes the first unforced error."
- Default fallback: "Balanced matchup. Overall skill score difference is the strongest predictor."

---

### Section 6 — Shot Preference Comparison

Card `bg-slate-900 border border-slate-800 rounded-2xl p-8 mt-6 mx-8`:

Heading: "Shot Type Preference" text-xl font-bold white
Subheading: "Percentage of points where each shot type is the primary weapon" text-slate-400 text-sm

Use Recharts `BarChart` with `layout="vertical"` and `grouped` bars:

```typescript
const shotData = [
  { shot: "Dink", p1: player1.shotPreferences.dink, p2: player2.shotPreferences.dink },
  { shot: "Drive", p1: player1.shotPreferences.drive, p2: player2.shotPreferences.drive },
  { shot: "Drop", p1: player1.shotPreferences.drop, p2: player2.shotPreferences.drop },
  { shot: "Lob", p1: player1.shotPreferences.lob, p2: player2.shotPreferences.lob },
  { shot: "Erne", p1: player1.shotPreferences.erne, p2: player2.shotPreferences.erne },
  { shot: "ATP", p1: player1.shotPreferences.atp, p2: player2.shotPreferences.atp },
]
```

Two `Bar` components: P1 in green (`#00E676`), P2 in gold (`#F59E0B`). Bar size 16, gap 4. Y-axis shows shot names. X-axis shows percentage 0–60.

Tooltip dark-styled showing both values on hover.

---

### Section 7 — Growth Gap Analysis

Card `bg-slate-900 border border-slate-800 rounded-2xl p-8 mt-6 mx-8`:

Heading: "Growth Gap Analysis" text-xl font-bold white
Subheading: "Skills [Player 2 name] could develop to close the gap with [Player 1 name]" text-slate-400 text-sm

Compute top 3 gaps: filter skills where `player1[skill] - player2[skill] > 5`, sort descending by gap size, take top 3.

For each gap skill, render a row:
- Skill name (white font-semibold)
- Gap indicator: "[P2 name]: 74 → Target: 88 (+14 points)" in slate-300
- Coaching recommendation (hardcoded map):
  - courtCoverage: "Shadow footwork drills — court positioning patterns 3× per week"
  - kitchenMastery: "Dink consistency practice — 200 cross-court dinks per session"
  - creativity: "Introduce lob and ATP practice in game situations"
  - athleticism: "Lateral movement and split-step timing training"
  - courtIQ: "Watch high-level match footage, focus on point construction patterns"
  - powerGame: "Shoulder rotation and contact point drills for drive improvement"
- Each row has a gold left-border `border-l-2 border-yellow-500 pl-4`

If no gaps > 5 points, show: "Players have closely matched skill profiles — this is a highly competitive matchup."

---

### Section 8 — Player Bio Cards

Two cards side by side (stacks on mobile) `grid grid-cols-1 md:grid-cols-2 gap-6 mt-6 mx-8`:

Each card `bg-slate-900 border rounded-2xl p-6` — Player 1 card `border-green-500/30`, Player 2 card `border-yellow-500/30`:

- Player name (large, white, bold)
- Rank badge · XP · Level
- "Dominant Style:" value (slate-300)
- "Signature Move:" value (slate-300 italic)
- "Top Badge:" value
- "Coaching Note:" value (slate-400 text-sm italic)

---

### Mobile Responsiveness

- All `mx-8` margins reduce to `mx-4` on mobile
- Selector row stacks vertically: `flex-col` on mobile
- Stat comparison table: on mobile, show only Skill | P1 | P2 (hide Difference column) and add horizontal scroll
- Shot chart: reduce bar size to 12 on mobile, allow horizontal scroll on the chart container
- Radar chart: max-width 100%, `overflow-x: auto` container, chart stays 400px (scrollable)
- All grid layouts collapse to 1 column below `md:` breakpoint

---

### No External Dependencies Beyond

`react`, `recharts`, `tailwindcss`, `shadcn/ui` (Card, Select, Button components). No router needed — `/compare` is the root.

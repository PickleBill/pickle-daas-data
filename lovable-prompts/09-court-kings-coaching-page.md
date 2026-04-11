# Lovable Prompt 09 — Court Kings Coaching Intelligence Page

## What This Builds
A premium B2B demo page designed specifically to show Rich (CEO) and Bryan (CRO) at Court Kings what Courtana's AI intelligence layer looks like running on THEIR courts. Black/gold Court Kings branding. No Courtana green on this page.

## Paste This Into Lovable

---

Build a **Court Kings Intelligence** demo page — a React app using Tailwind CSS, shadcn/ui Card components, and Recharts. This is a premium B2B product demo, NOT a consumer app. Route: `/` (root of a new project).

---

### Theme & Colors

- Page background: `#000000` (pure black)
- Card backgrounds: `#0a0a0a` with border `#1a1a1a`
- Primary accent: `#F59E0B` (gold/amber)
- Secondary accent: `#FCD34D` (lighter gold, for highlights)
- Text: white (#FFFFFF) and `#9CA3AF` for secondary
- Danger/alert: `#EF4444` (red — used only for "gap" indicators)
- Success: `#10B981` (green — used only for "strong" indicators)
- NO green (`#00E676`) anywhere on this page — this is Court Kings, not Courtana

---

### Branded Header

Full-width header `bg-black border-b border-yellow-600/30 px-8 py-6`:

Left side:
- Crown emoji + text **"COURT KINGS INTELLIGENCE"** in gold (`#F59E0B`), font-bold, text-2xl, tracking-widest, uppercase
- Below: tagline in white text-sm: "Every match. Every player. Every shot. Automatically analyzed."

Right side:
- Small pill: `border border-yellow-600 text-yellow-500 text-xs px-3 py-1 rounded-full` — text: "Powered by Courtana AI"
- Second line in gray text-xs: "Confidential Demo — Court Kings × Courtana"

---

### Section 1 — Hero Value Statement

Full-width `py-16 px-8 text-center`:

Eyebrow in gold uppercase tracking-widest text-sm: "WHAT YOUR COURTS GENERATE"

H1 (text-4xl md:text-5xl font-black text-white max-w-3xl mx-auto):
"Turn every rally into coaching intelligence — automatically."

Subtext (text-lg text-gray-400 max-w-xl mx-auto mt-4):
"Courtana's AI analyzes every highlight clip your players create. No manual review. No extra staff. Just instant, structured intelligence on every player at every Court Kings location."

Below, three horizontal stat pills in a row (centered, `flex gap-6 justify-center mt-8 flex-wrap`):
- Gold pill: "4,097 clips analyzed at The Underground (pilot venue)"
- Gold pill: "47 brands detected automatically"
- Gold pill: "15 clips → full player DNA in < 2 minutes"

Each pill: `border border-yellow-600/50 bg-yellow-600/10 text-yellow-400 text-sm px-4 py-2 rounded-full`

---

### Section 2 — Featured Player Profile Card

Section heading (text-2xl font-bold text-white): "What a Top Player Profile Looks Like"
Subheading (text-gray-400): "This is what Courtana automatically generates for every player at your facilities."

Large card `bg-[#0a0a0a] border border-yellow-600/30 rounded-2xl p-8 max-w-3xl mx-auto`:

**Player header row:**
- Left: circular avatar placeholder — `bg-yellow-600 w-16 h-16 rounded-full flex items-center justify-center text-black font-black text-xl` — initials "PB"
- Right:
  - Name: **"PickleBill"** text-2xl font-bold white
  - Row: gold badge "Global Rank #1" + gray text "The Underground | Active 90 days"
  - Row: "XP: 311,800" (gold) · "Level 18" (white) · "82 Badges" (gray)

**Skill breakdown — horizontal bars using Recharts or plain CSS:**

Below the player header, a heading "AI-Analyzed Skill Profile" text-lg text-white font-semibold mt-6.

6 skill rows, each with: skill label (text-gray-300 w-36), progress bar (full width, `bg-gray-800 rounded-full h-3`), fill color based on score, score number on right (text-yellow-400 font-bold).

Use these exact values:
```
Kitchen Mastery    92%   #10B981 (green fill — elite tier)
Court IQ           91%   #10B981
Court Coverage     88%   #10B981
Athleticism        84%   #F59E0B (gold fill — strong tier)
Creativity         79%   #F59E0B
Power Game         76%   #F59E0B
```

Below the bars, a small legend: green dot = "Elite (80+)" · gold dot = "Strong (70–79)" · gray dot = "Developing (<70)"

**Coaching insight row** (3 cards below the bars, `grid grid-cols-3 gap-4 mt-6`):
- Card 1 (green border): "Signature Move: Kitchen dominator — wins 67% of extended dink rallies"
- Card 2 (gold border): "Top Badge: Epic Rally (earned 38×)"
- Card 3 (gold border): "Brands: JOOLA paddle · LIFE TIME gear · Recovery Cave sponsor"

Each card: `bg-[#111] border rounded-lg p-4 text-sm text-gray-300`

---

### Section 3 — Court Intelligence Leaderboard

Section heading: "What Your Top Players Look Like" (text-2xl font-bold white)
Subheading: "A live leaderboard view across all players at a facility — available from day one."

Card `bg-[#0a0a0a] border border-yellow-600/20 rounded-2xl overflow-hidden`:

Table header row `bg-yellow-600/10 px-6 py-3` — columns: Player · Clips · Avg Quality · Top Skill · Coaching Priority

5 data rows (alternating `bg-[#0a0a0a]` / `bg-[#111]`, `px-6 py-4`):

```
#1  PickleBill    15 clips   7.4/10   Kitchen Mastery   "Refine power game"
#2  ProNetPlayer  12 clips   7.1/10   Court Coverage    "Develop ATP shots"
#3  SpinDoctor    9 clips    6.8/10   Creativity        "Improve NVZ patience"
#4  KitchenKing   8 clips    6.5/10   Court IQ          "Add 3rd shot variety"
#5  PowerSlammer  7 clips    6.2/10   Power Game        "Focus on soft game"
```

Each player name in white, rank in gold, quality score colored (>7.0 green, 6.5-7.0 yellow, <6.5 gray), coaching priority in italics gray-400.

Below the table, a note in gray-500 text-sm italic: "Leaderboard auto-updates as new highlights are analyzed. No manual data entry required."

---

### Section 4 — What Your Court Generates

Section heading: "What Every Court Kings Location Generates" (text-2xl font-bold white)

3-column stat card grid (`grid grid-cols-1 md:grid-cols-3 gap-6`):

Card 1 `bg-[#0a0a0a] border border-yellow-600/30 rounded-xl p-6`:
- Gold number: "~80–120"
- Label: "new highlight clips per week per court"
- Subtext in gray: "Based on The Underground pilot data"

Card 2 `bg-[#0a0a0a] border border-yellow-600/30 rounded-xl p-6`:
- Gold number: "~400–600"
- Label: "AI-generated coaching insights per month"
- Subtext in gray: "Shot analysis, skill scores, brand detections"

Card 3 `bg-[#0a0a0a] border border-yellow-600/30 rounded-xl p-6`:
- Gold number: "~24"
- Label: "unique brands detected per 100 clips"
- Subtext in gray: "Paddle brands, apparel, venue sponsors"

Below the 3 cards, a full-width callout box `bg-yellow-600/10 border border-yellow-600/30 rounded-xl p-6 mt-2`:
- Gold bold text: "Revenue insight:"
- White text: "Every 1,000 clips analyzed = ~240 brand detection opportunities. At even a $0.50 CPM for verified brand exposure data, that's $120 in attributable intelligence value — per 1,000 clips."
- Gray italic: "This is what your courts are already generating. Courtana makes it visible."

---

### Section 5 — Revenue Impact Panel

Section heading: "The Business Case in Plain Numbers" (text-2xl font-bold white)

Two-column layout `grid grid-cols-1 md:grid-cols-2 gap-8`:

**Left — simple math breakdown:**

```
Court Kings has:     X locations
Each location:       ~100 clips/week
Per year:            ~5,200 clips/location
At 10 locations:     52,000 clips/year
At 50 locations:     260,000 clips/year
```

Present this as stacked rows with gold numbers and white labels, `font-mono` for the numbers. Add a divider line. Below:

"At $1/clip for branded intelligence reports: **$260K+ annual recurring revenue** at 50 locations."

Gold bold number, white label. No asterisk, no "projected" language — frame as "this is the math."

**Right — Coaching upsell model:**

Heading (text-lg font-semibold white): "The Coaching Tier"
Three rows with gold left-border accent:
- "AI coaching report per player: $9.99/month or included in premium membership"
- "Automated improvement plans generated weekly, no coach time required"  
- "Coaches get a dashboard — spend time coaching, not reviewing video"

---

### Section 6 — Coaching Tools Preview

Section heading: "What a Coach Sees" (text-2xl font-bold white)
Subheading: "Courtana surfaces the work. Coaches do the coaching."

Single card `bg-[#0a0a0a] border border-yellow-600/20 rounded-2xl p-8 max-w-2xl mx-auto`:

Header: "Weekly Report: PickleBill — Coach's Summary"
Subtitle in gold text-sm: "Auto-generated · Week of April 7, 2026"

3 coaching insight blocks, each with a colored left border:

**Block 1 (green border) — "Strength to leverage:"**
"Kitchen mastery score 92/100. PickleBill wins 67% of rallies that extend past 8 shots. Coach recommendation: enter more 3rd-shot drop sequences to force extended rallies."

**Block 2 (gold border) — "Growth opportunity:"**
"Power game score 76/100 — lowest dimension. 3 clips show early pop-up errors under pressure. Coach recommendation: 15 minutes of speed-up defense drills per session for 4 weeks."

**Block 3 (gold border) — "This week's focus:"**
"Improve transition zone speed. 2 clips show hesitation at the non-volley zone transition. Specific drill: shadow footwork pattern from baseline to kitchen in under 2 seconds."

Below the blocks: gray text-sm italic "This report was generated automatically from 15 video clips. Zero coach hours required to produce it."

---

### Section 7 — Deployment Reality Check

Full-width `bg-[#0a0a0a] border-y border-yellow-600/20 py-12 px-8`:

Centered heading text-2xl white: "How This Works at Court Kings"

3-step horizontal flow (stacks on mobile):

Step 1 (gold number "01"): "Players record highlights as they always do — no change to their behavior"
Step 2 (gold number "02"): "Courtana AI analyzes every clip automatically — shot by shot, brand by brand"
Step 3 (gold number "03"): "Coaches, admins, and players get intelligence dashboards — no manual review"

Between steps: gold arrow `→`

Below steps: gray text-sm "Setup time: < 1 week. No hardware. No additional staff. No change to your existing Courtana setup."

---

### Section 8 — CTA

Full-width centered section `py-20 px-8`:

Heading text-3xl font-black white max-w-2xl mx-auto:
"This is what runs automatically at every Court Kings location."

Subtext text-gray-400 mt-4 max-w-xl mx-auto:
"One integration. Every facility. Every player. Fully automated."

Primary CTA button: `bg-yellow-500 hover:bg-yellow-400 text-black font-black px-10 py-5 rounded-xl text-lg mt-8 inline-block`
Label: "Let's Talk →"
Links to: `mailto:bill@courtana.com`

Below the button: `text-gray-500 text-sm mt-4` — "bill@courtana.com"

Footer line `text-gray-700 text-xs mt-12 text-center`: "Confidential — Prepared for Court Kings leadership · courtana.com"

---

### Important Design Notes

- NO Courtana logo or Courtana green on this page — this page presents as a "Court Kings Intelligence" product
- NO pricing mentioned beyond the revenue math section
- NO competitor mentions
- Use gold sparingly as accent — not every element needs to be gold. Most text is white or gray. Gold signals importance.
- Cards should have very subtle shadows: `shadow-lg shadow-black/50`
- All interactive elements (leaderboard rows, highlight cards) should have `hover:bg-white/5 transition-colors cursor-pointer`
- Mobile: all grids collapse to single column, font sizes step down, hero H1 max text-3xl on mobile

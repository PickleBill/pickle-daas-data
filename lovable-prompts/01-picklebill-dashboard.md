# Lovable Prompt 01 — PickleBill Intelligence Dashboard

## What This Builds
The master PickleBill player dashboard. The full demo. This is the Court Kings pitch.

## Paste This Into Lovable

---

Build a PickleBill Intelligence Dashboard — a single-page React app using Mantine UI.

**Color scheme:** dark background #1a2030, card backgrounds #252d3a, green accent #00E676, text white.

**Data source:** Import the `lovable-dashboard-data.json` file (paste its contents as a JS const at the top of the component).

**Layout (top to bottom):**

1. **Player Header Card**
   - Avatar (circular), Username "PickleBill", Rank "#1 Global", XP "283,950", Level "17 | Gold III", Badges count "82"
   - Green accent on rank badge

2. **Highlights Grid** (2 columns on desktop, 1 on mobile)
   - For each highlight: thumbnail image, quality score badge (top-right, green), caption text, brand tags (small chips below)
   - On hover: show Ron Burgundy quote as a tooltip overlay
   - Clicking a thumbnail opens a modal with HTML5 video player (use the video_url field), quality score, ESPN commentary, and predicted badges

3. **Analytics Section** (2 columns)
   - Left: Recharts RadarChart with 7 skill dimensions (court_coverage, kitchen_mastery, power_game, touch_and_feel, athleticism, creativity, court_iq) from skill_radar data
   - Right: Top brands bar chart (top 5, horizontal bars, brand name on left, count on right)

4. **Story Arc Distribution** — small donut chart showing arc breakdown

5. **Top Ron Burgundy Quote** — full-width card with the quote from the highest quality clip, italic, green left border

Make it fully mobile responsive. No fake data — everything comes from the JSON.

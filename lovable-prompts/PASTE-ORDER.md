# Lovable Paste Order — Pickle DaaS
_Start here. Paste these in order. Each prompt is independent — they can go in different Lovable projects._

---

## START HERE — Highest Priority

### Prompt 09: Court Kings Coaching Intelligence Page

**When:** Before your next call with Rich + Bryan  
**Why first:** This is the $250–500K deal. Show them a live product demo before the NDA is even signed.  
**Project:** Create a new Lovable project — name it `court-kings-intelligence`  
**File to paste:** Contents of `09-court-kings-coaching-page.md`  
**After:** Share the Lovable preview URL with Rich + Bryan as a taste before the formal engagement  

**What it builds:**
- Black/gold Court Kings branding (NOT Courtana green)
- PickleBill player profile with skill bars + coaching insights
- 5-player leaderboard view showing "what your courts generate"
- Revenue impact math
- "What a coach sees" report preview
- CTA: bill@courtana.com

**Talking points when you show it:**
- "This is what runs automatically on every highlight your players create."
- "No manual review. No extra staff. Just intelligence."
- "This is already live at The Underground with 4,097 clips."

---

## INVESTOR MEETINGS

### Prompt 08: Investor Demo Page

**When:** Before your next investor meeting (fundraise tranche 1 — ~$396K of $500K raised)  
**Project:** Create a new Lovable project — name it `pickle-daas-investor`  
OR add as a new route to your existing Courtana Lovable app  
**File to paste:** Contents of `08-investor-demo-page.md`  

**What it builds:**
- Animated count-up KPIs (4,097 clips, 7.4 avg quality, 47 brands, 25+ players)
- PickleBill player card with live/demo data indicator
- Recharts radar chart (Performance DNA — 6 axes)
- Expandable highlights grid (click to reveal ESPN commentary inline)
- Brand intelligence bar chart + revenue narrative
- Scale pitch: 4,097 × 1,000 venues math
- Closing quote: "What would you do with the world's largest corpus of pickleball intelligence?"
- CTA: bill@courtana.com

**Supabase wiring (optional):** Set `VITE_SUPABASE_URL` and `VITE_SUPABASE_ANON_KEY` in Lovable's environment variables. When set, pulls live data from `pickle_daas_analyses` table and shows green "LIVE DATA" badge. Without it, runs on hardcoded demo data — fully demoable.

---

## ADVANCED ANALYTICS

### Prompt 10: Multi-Player Comparison Dashboard

**When:** After Court Kings deal progresses — use this in deeper product demos and coaching conversations  
**Project:** Add to the `court-kings-intelligence` project as a second route, OR create a new project  
**File to paste:** Contents of `10-multi-player-comparison.md`  

**What it builds:**
- Dropdown selectors for 2–3 players from 5 hardcoded demo players (PickleBill is top performer)
- Radar chart overlay with both players' skill profiles on the same chart (different colors)
- Stat comparison table with delta column
- Matchup win prediction with confidence percentage
- Shot type preference side-by-side horizontal bar charts
- Growth gap analysis with specific coaching recommendations
- Player bio cards

**Good demo script:**
1. Load PickleBill vs. PowerSlammer → radar shows the skill gap visually
2. Growth gap shows "Kitchen Mastery: 58 → Target: 92 (+34 points)"
3. Click matchup prediction: "PickleBill wins 64% of the time"
4. Show shot preferences: PowerSlammer drives 52% of points, PickleBill dinks 38%
5. Punchline: "This is what your coaches could have for every player at every facility."

---

## Dependencies and Notes

- **All 3 prompts are self-contained** — no shared state, no shared project required
- **All have hardcoded demo data** — no Supabase required to demo. Just paste and click preview.
- **Branding separation is intentional:**
  - Prompt 09 (Court Kings): black + gold `#F59E0B` — no Courtana green
  - Prompt 08 (Investor): dark slate + green `#00E676` — Courtana brand
  - Prompt 10 (Comparison): dark slate + green/gold/blue multi-player colors
  - Do NOT combine 09 with 08/10 in the same Lovable project unless you add a brand toggle
- **For Supabase live data (Prompt 08 only):** Set `VITE_SUPABASE_URL` and `VITE_SUPABASE_ANON_KEY` in Lovable's Environment Variables panel (Settings → Environment). Table needed: `pickle_daas_analyses` per the schema in `PICKLE-DAAS-CLAUDE-CODE-CONTEXT.md`
- **Prompt numbering context:** Prompts 01–07 are in earlier files in this folder. These three (08–10) are the next generation — standalone demos vs. app features.

---

## Quick Reference

| # | File | Project Name | Priority | Audience |
|---|------|-------------|----------|----------|
| 09 | `09-court-kings-coaching-page.md` | `court-kings-intelligence` | FIRST | Rich + Bryan (Court Kings) |
| 08 | `08-investor-demo-page.md` | `pickle-daas-investor` | SECOND | Investors / Scot McClintic etc |
| 10 | `10-multi-player-comparison.md` | Add to `court-kings-intelligence` | THIRD | Court Kings + coaching demos |

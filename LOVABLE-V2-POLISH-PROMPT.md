# Lovable V2 — Polish & Data Upgrade
_Paste this into the existing Pickle DaaS project as a follow-up prompt_

---

Great first build! Now upgrade the app with real data from our GitHub repo and polish the UI.

## 1. Fetch Real Data from GitHub (replace all hardcoded data)

Replace all hardcoded clip data, KPIs, and player stats with live fetches from our public GitHub repo. All these URLs are publicly accessible JSON — no auth needed:

**Dashboard data:**
```
https://raw.githubusercontent.com/PickleBill/pickle-daas-data/main/output/lovable-package/dashboard-data.json
```

**Clips metadata (8 real clips with video URLs, scores, commentary):**
```
https://raw.githubusercontent.com/PickleBill/pickle-daas-data/main/output/lovable-package/clips-metadata.json
```

**Player DNA profile:**
```
https://raw.githubusercontent.com/PickleBill/pickle-daas-data/main/output/lovable-package/player-dna.json
```

**Brand registry:**
```
https://raw.githubusercontent.com/PickleBill/pickle-daas-data/main/output/lovable-package/brand-registry.json
```

**Voice manifest (32 generated MP3s):**
```
https://raw.githubusercontent.com/PickleBill/pickle-daas-data/main/output/lovable-package/voice-manifest.json
```

On app load, fetch dashboard-data.json. On Highlights page, fetch clips-metadata.json. On Player DNA, fetch player-dna.json. On Brands, fetch brand-registry.json. Show a subtle loading skeleton while fetching. Cache the data in React state so it persists across page navigation without re-fetching.

## 2. Highlights Page — Show All 8 Real Clips

The clips-metadata.json has 8 real clips. Show all of them in a 3-column grid (2 on tablet, 1 on mobile). Each card should show:
- Video player that plays on hover (muted autoplay on hover, pause on leave)
- Quality score chip (top-right corner, green)
- Viral score chip (top-left corner, color-coded: red for 7+, gold for 5-6, gray for <5)
- Story arc tag (below video: "grind_rally" = blue, "teaching_moment" = green, "athletic_highlight" = purple, "error_highlight" = red, "pure_fun" = yellow)
- Ron Burgundy quote (italic, green left border)
- Brand chips (small pills at bottom)
- Caption text

Clicking any card opens a modal with:
- Full video player (full width)
- All 4 commentary tabs (ESPN, Hype, Ron Burgundy, Chuck Norris) — use the commentary from the analysis JSON
- Predicted badges
- "Play Voice" button that uses the ElevenLabs connection if available, or browser speechSynthesis as fallback

## 3. Player DNA Page — Richer Profile

Fetch player-dna.json and display:
- Update skill radar with ALL 9 dimensions: court_coverage (6.0), kitchen_mastery (5.0), power_game (6.0), touch_feel (5.3), athleticism (6.3), creativity (4.0), court_iq (5.7), consistency (6.0), composure_under_pressure (6.7)
- Add "Play Style DNA" section: large visual chips showing the play style tags in priority order: "banger" (most dominant, largest chip), "consistent driver", "baseliner", "net rusher", "aggressive baseliner"
- Show "Coaching AI Insights" card with green left border containing the real coaching notes: "Incorporate more soft game", "Approach the net more often", "Transition speed needs work", "Keep paddle in ready position", "Stabilize before contact on volleys"
- Add "Story Arc Distribution" donut chart: grind_rally (2), teaching_moment (3), pure_fun (2), athletic_highlight (1), error_highlight (1)

## 4. Brands Page — Sponsorship Intelligence

Fetch brand-registry.json and show:
- 3 brand cards (JOOLA, LIFE TIME PICKLEBALL, CRBN) each with: appearance count, category, presence percentage as a progress bar, clip count
- JOOLA and LIFE TIME both show 100% presence (green progress bar full)
- CRBN shows 25% presence (green bar partial)
- Add "Sponsorship ROI Insight" callout (gold border): use the sponsorship_insight text from the JSON
- Add "Brand Detection Heatmap" — simple table showing which brand appears in which clip (green dot = present, empty = absent)

## 5. Voice Lab Page — ElevenLabs Integration

If ElevenLabs is connected:
- When user clicks "Play Voice" on any voice tab, call ElevenLabs API with the commentary text and the matching voice preset
- Voice IDs: ESPN = TxGEqnHWrfWFTfGW9XjX, Hype = ErXwobaYiN019PkySvjV, Ron Burgundy = pNInz6obpgDQGcFmaJgB, Chuck Norris = VR6AewLTigWG4xSOukaG
- Show a small waveform animation while audio is generating/playing
- Add a "Generate All Voices" button that processes all 4 voices for the selected clip

If ElevenLabs is NOT connected, fall back to browser speechSynthesis.

## 6. Design Polish

- The Courtana logo is loading correctly from CDN — keep it
- Add a subtle gradient animation on the header (dark navy to slightly lighter, 10s loop)
- Make the KPI cards have a subtle green glow on hover
- Add Courtana's green accent (#00E676) as a thin top border on all cards
- Video player: add a custom play button overlay (green circle with white triangle) instead of default browser controls
- Brand frequency bars: animate them sliding in from left on page load (300ms delay between each)
- Add a footer: "Powered by Courtana · Pickle DaaS · Built with AI" with link to courtana.com

## 7. Mobile Responsive Fixes

- On mobile, the Featured Highlight should stack: video full-width on top, commentary panel full-width below
- Nav should collapse into a hamburger menu on mobile
- KPI cards: 2×2 grid on mobile instead of 4 in a row
- Highlights grid: single column on mobile

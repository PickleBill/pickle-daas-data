# Lovable Prompt — Pickle DaaS Shell Project (V1)
_Paste this into a brand new Lovable project called "Pickle DaaS"_

---

Build a "Pickle DaaS" application — an AI-powered pickleball video intelligence platform. This is a multi-page React app using shadcn/ui and Tailwind CSS.

## Branding
- App name: **Pickle DaaS** (subtitle: "Data as a Service for Pickleball")
- Primary color: #00E676 (electric green)
- Background: #0a0f1a (deep navy)
- Card backgrounds: #131d2e / #1a2535
- Text: #e0eaf8 (light blue-white)
- Muted text: #5a7090
- Accent gold: #FFD600
- Logo: Display an `<img>` tag loading from `https://cdn.courtana.com/assets/logos/fulllogo-dark-transparent-grad.svg` — this is publicly accessible, no auth needed. Place it in the top-left nav. Fallback: show text "Courtana" in green.
- Font: Inter or system font stack (-apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif)
- Vibe: ESPN meets Bloomberg Terminal. Dark, data-dense, premium.

## Navigation
Top nav bar with Courtana logo (left), "Pickle DaaS" title (center), and page links (right):
- **Dashboard** (default/home)
- **Highlights**
- **Player DNA**
- **Brands**
- **Voice Lab**

## Page 1: Dashboard (Home)
Top section — 4 KPI cards in a row:
- **Clips Analyzed**: "6" (green number, large)
- **Avg Quality**: "7.3 / 10"
- **Top Brand**: "JOOLA"
- **Viral Potential**: "6.2 avg"

Middle section — Featured highlight card (full width):
- Left 60%: HTML5 `<video>` player loading from `https://cdn.courtana.com/files/production/u/01915c59-9bb7-4683-bd53-e28bddcae12e/ce00696b-9f9b-465a-971c-dbf1334e556c.mp4`
- Right 40%: Commentary panel with tabs: ESPN | Hype | Ron Burgundy | Chuck Norris
  - ESPN tab content: "Players engage in a steady rally, exchanging consistent drives from the baseline, showcasing solid fundamental play in this indoor pickleball match."
  - Ron Burgundy tab: "By the beard of Zeus, this pickleball contest is a symphony of precision and power! The players, with their unwavering focus, deliver a spectacle of athletic prowess that truly defines 'stay classy, San Diego' on the court."
  - Chuck Norris tab: "Chuck Norris doesn't play pickleball; pickleball plays Chuck Norris."
  - Hype tab: "ABSOLUTE FIREPOWER from the baseline! This rally is NEXT LEVEL!"
- Below each commentary tab: a "🔊 Play Voice" button (use browser speechSynthesis API to read the text aloud as placeholder — real ElevenLabs integration comes later)

Bottom section — 2 columns:
- Left: Recharts RadarChart with 7 axes: Court Coverage (6.0), Kitchen Mastery (5.0), Power Game (6.0), Touch & Feel (5.3), Athleticism (6.3), Creativity (4.0), Court IQ (5.7). Green fill, dark background.
- Right: Brand frequency horizontal bar chart: "LIFE TIME PICKLEBALL" = 3, "JOOLA" = 3. Green bars on dark background.

## Page 2: Highlights
A grid of highlight cards (3 columns desktop, 1 mobile). Hardcode these 3 clips for now:

Card 1:
- Video: `https://cdn.courtana.com/files/production/u/01915c59-9bb7-4683-bd53-e28bddcae12e/0b225575-5bd7-4e7b-ac84-8b59a86cb811.mp4`
- Name: "Baseline Rally Masterclass"
- Quality: 7/10, Viral: 5/10
- Arc tag: "pure_fun" (blue chip)
- Ron Burgundy: "By the beard of Zeus, this pickleball contest is a symphony of precision and power!"
- Brands: LIFE TIME PICKLEBALL, JOOLA
- Badges: Teaching Moment

Card 2:
- Video: `https://cdn.courtana.com/files/production/u/01915c59-9bb7-4683-bd53-e28bddcae12e/f415729c-153e-4024-bdc3-9a9836752e4e.mp4`
- Name: "Drive Drop Dink Sequence"
- Quality: 7/10, Viral: 4/10
- Arc tag: "teaching_moment" (green chip)
- Ron Burgundy: "Good heavens, what a display of athleticism and paddle prowess!"
- Brands: LIFE TIME PICKLEBALL, JOOLA
- Badges: Aggressive Driver

Card 3:
- Video: `https://cdn.courtana.com/files/production/u/01915c59-9bb7-4683-bd53-e28bddcae12e/c30b464e-25b4-4029-ba30-49b1f3877f42.mp4`
- Name: "Quick Rally Gone Wrong"
- Quality: 7/10, Viral: 5/10
- Arc tag: "error_highlight" (red chip)
- Ron Burgundy: "Well, that was certainly a pickleball rally. Not quite a symphony of dinks, nor a ballet of volleys, but a rally nonetheless."
- Brands: LIFE TIME PICKLEBALL, JOOLA
- Badges: Error Highlight

Each card: dark background, green quality score chip top-right, video thumbnail that plays on hover, click opens a modal with full video + all commentary tabs + badge predictions + brand chips.

## Page 3: Player DNA
Full-page player profile for "PickleBill":

Header card:
- Large circular avatar placeholder (green border, initials "PB")
- Username: "PickleBill"
- Stats row: Rank #1 Global | XP 283,950 | Level 17 | Gold III | 82 Badges
- Subtitle: "Clips Analyzed: 3 | Dominant Shot: Drive | Style: Banger, Net Rusher"

Below — 2-column layout:
- Left: Large radar chart (same data as dashboard but bigger)
- Right: Play style tags as large colored chips: "banger", "consistent driver", "baseliner", "net rusher", "aggressive baseliner"

Below — Coaching Notes section:
- Card with green left border, title "AI Coaching Insights"
- Bullet list: "Incorporate more soft game", "Approach the net more often", "Transition speed needs work", "Keep paddle in ready position", "Stabilize before contact on volleys"

Below — Signature Clips grid (reuse the 3 clips from Highlights page, but in a compact 3-column card layout showing just thumbnail + name + quality score)

## Page 4: Brands
Brand Intelligence Dashboard:
- Title: "Brand Detection Registry"
- Subtitle: "AI-detected brands across all analyzed highlights"

Two large cards side by side:
- Card 1: "JOOLA" — 3 appearances, category: paddle, detected in clips 1/2/3, confidence: high. Show the JOOLA logo if you can find one, otherwise show a green paddle icon.
- Card 2: "LIFE TIME PICKLEBALL" — 3 appearances, category: venue/apparel, detected in clips 1/2/3, confidence: high.

Below: "Sponsorship Insight" callout box (gold border):
- "These 2 brands have 100% presence across all analyzed clips. This data powers sponsorship ROI measurement — Courtana can tell brands exactly how often their equipment appears in player highlights."

## Page 5: Voice Lab
Title: "AI Commentary Voice Lab"
Subtitle: "Generate voice commentary for any highlight using AI"

Top: Select a clip from a dropdown (list the 3 clips by name)

Below: 4 voice cards in a row, each with:
- Voice name (ESPN, Hype, Ron Burgundy, Chuck Norris)
- Icon (🎙️ 🔥 🥃 💪)
- The commentary text for the selected clip
- "🔊 Play" button using speechSynthesis
- "Coming Soon: ElevenLabs" badge in muted text below each

Bottom: "Pipeline Status" card showing:
- Gemini Analysis: ✅ Active (6 clips processed)
- ElevenLabs TTS: 🔜 API Key Needed
- Supabase Storage: 🔜 Schema Ready, Awaiting Deploy
- Auto-Voice Pipeline: 🔜 Waiting on ElevenLabs

## Global Requirements
- Fully mobile responsive (single column on mobile, 2-3 columns on desktop)
- All videos load from cdn.courtana.com — these are public URLs, no auth needed
- Use shadcn/ui components (Card, Tabs, Badge, Button, Dialog for modals)
- Use Recharts for all charts
- Smooth page transitions
- No fake loading spinners — data is hardcoded for now, make it feel instant
- All commentary text is real (from our Gemini analysis), not placeholder
- The app should feel like a premium sports analytics platform

# Pickle DaaS Discovery Engine — Architecture
**Created: April 11, 2026 | Status: Design → Claude Code build**

---

## THE IDEA IN ONE SENTENCE

Instead of manually telling AI what to find, build a system that autonomously explores the dataset from multiple angles, surfaces surprising insights, and ranks them by buyer value — then presents the best finds as proof-of-concept data products.

---

## WHY THIS MATTERS RIGHT NOW

You have 241 analyzed clips, 14-field JSON schemas, 11 mapped buyer segments, and $0.0054/clip economics. But you're manually running one analysis at a time and manually deciding what to look for. The DaaS initiative doc (Dec 2025) laid out 3 data layers — Hustle Index, Equipment Audit, Tactical Geometry — but they're still separate concepts, not a running system.

The Discovery Engine turns "Bill tells AI what to analyze" into "AI explores autonomously, Bill curates the best results."

---

## ARCHITECTURE: THE 5-AGENT SWARM

Each agent has a single lens on the same dataset. They run independently, write findings to a shared `discoveries/` folder, and a Curator agent ranks everything.

```
┌─────────────────────────────────────────────────────────┐
│                   DISCOVERY ENGINE                       │
│                                                         │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐  │
│  │ AGENT 1  │ │ AGENT 2  │ │ AGENT 3  │ │ AGENT 4  │  │
│  │ Player   │ │ Brand &  │ │ Tactical │ │ Narrative │  │
│  │ Profiler │ │ Equipment│ │ Analyst  │ │ & Viral  │  │
│  └────┬─────┘ └────┬─────┘ └────┬─────┘ └────┬─────┘  │
│       │            │            │            │          │
│       ▼            ▼            ▼            ▼          │
│  ┌─────────────────────────────────────────────────┐    │
│  │              discoveries/ (shared)               │    │
│  │  Each finding = 1 JSON with:                     │    │
│  │    insight, evidence, buyer_segments,             │    │
│  │    confidence, wow_factor, data_points            │    │
│  └──────────────────────┬──────────────────────────┘    │
│                         │                               │
│                    ┌────▼─────┐                         │
│                    │ AGENT 5  │                         │
│                    │ Curator  │                         │
│                    │ & Ranker │                         │
│                    └────┬─────┘                         │
│                         │                               │
│                    ┌────▼─────┐                         │
│                    │  OUTPUT  │                         │
│                    │ Top 10   │                         │
│                    │ Dashboard│                         │
│                    └──────────┘                         │
└─────────────────────────────────────────────────────────┘
```

### Agent 1: PLAYER PROFILER
- **Input:** All analysis JSONs (players_detected, skill_indicators, badge_intelligence)
- **Mission:** Build the deepest possible profile for every player in the dataset. Cross-clip patterns. Improvement trends over time. Predicted next badges. Strengths, weaknesses, signature moves.
- **Buyer value:** Coaching platforms, player retention (venues), DUPR enrichment
- **The "wow" output:** "PickleBill's backhand dink improved 23% across clips recorded in March vs January. At this trajectory, they'll earn the 'Kitchen Master' badge within 6 sessions."

### Agent 2: BRAND & EQUIPMENT ANALYST
- **Input:** All analysis JSONs (brand_detection, paddle_intel)
- **Mission:** Which brands appear, how often, in what contexts (winning shots? errors?). Equipment-performance correlation. Which paddles show up in the best plays vs worst plays.
- **Buyer value:** Equipment manufacturers (Selkirk, JOOLA, Engage, HEAD), sponsorship intel
- **The "wow" output:** "Selkirk Power Air paddles appear in 34% of overhead kills with a 92% success rate, vs JOOLA Perseus at 67% success. Selkirk players generate 18% more viral-worthy highlights."

### Agent 3: TACTICAL ANALYST
- **Input:** All analysis JSONs (shot_analysis, daas_signals, skill_indicators)
- **Mission:** Game state patterns. What happens after a bad dink? What's the most common error at each skill level? Rally length patterns. The "Premature Celebration Syndrome" from the DaaS doc. Win probability flows.
- **Buyer value:** Sports betting/DFS, broadcast analytics, coaching
- **The "wow" output:** "When a rally exceeds 8 shots, the player who initiated the attack wins only 31% of the time. Patience literally wins in amateur pickleball."

### Agent 4: NARRATIVE & VIRAL ANALYST
- **Input:** All analysis JSONs (storytelling, commentary, badge_intelligence)
- **Mission:** Find the clips with the best stories. Miracle recoveries, underdog moments, hilarious errors. Rank by viral potential. Generate shareable captions and social media hooks.
- **Buyer value:** Media companies, social platforms, venue marketing
- **The "wow" output:** "Clip #4c3d-9558: Player dives 6 feet for a save at 4.1G impact, then opponent celebrates prematurely and loses the point. Viral score: 95/100. Suggested caption: 'He thought it was over. It wasn't.'"

### Agent 5: CURATOR & RANKER
- **Input:** All findings from Agents 1-4
- **Mission:** Read every discovery. Score each by: (a) surprise factor, (b) data confidence, (c) buyer willingness-to-pay, (d) demonstrability. Produce a ranked Top 20 discoveries dashboard.
- **Output:** `output/discovery-engine/top-discoveries.html` — a shareable investor/partner demo

---

## THE MULTI-MODEL ANGLE (what you were riffing on)

Your instinct about "run it through 5 different AI models" is exactly right. Here's how to formalize it:

**Round 1 (now):** Gemini 2.5 Flash did the initial analysis. That's your 241 JSONs.

**Round 2 (Discovery Engine):** Claude reads the Gemini outputs and finds cross-clip patterns, correlations, and stories that Gemini couldn't see because it only saw one clip at a time. This is where the magic happens — Claude has the CORPUS view that Gemini never had.

**Round 3 (validation, future):** Take the top 10 discoveries and run the source clips through GPT-4o Vision and a second Gemini pass with different prompts. See if the findings hold. Where 2+ models agree = high confidence. Where they disagree = interesting edge case to investigate.

This is the "multiple analyses increase accuracy" pattern you saw working in the badge analytics. It works because each model has different biases, different training data, different failure modes. Ensemble > single model.

---

## THE "FRIENDS PLAYING WITH DATA" IDEA

This is actually brilliant and maps to a real product feature. Here's how it stages:

**Stage 1 (now):** Internal discovery — AI agents exploring autonomously
**Stage 2 (post-Peak launch):** "Player Report Card" — each player gets an auto-generated profile page they can share. Their friends see it, want their own, sign up to play at a Courtana venue. Viral loop.
**Stage 3 (with broadcast mode):** Live audience prompts — viewers watching a broadcast can ask "who's winning the kitchen battle?" and get real-time AI analysis. This is the ESPN-killer feature.
**Stage 4 (community):** Let groups of friends run "challenges" — who has the best backhand this month? Who improved the most? Leaderboards within friend groups. This is the social layer that makes Courtana sticky.

---

## WHAT THE AI CHIEF OF STAFF DOES

YES — this is exactly what the AI Chief of Staff role should be. Not a single agent, but an orchestration layer that:

1. **Dispatches** work to specialized agents (player profiler, brand analyst, etc.)
2. **Curates** results — ranks by business value, flags surprises
3. **Routes** findings to the right output: investor deck? venue pitch? brand partnership email?
4. **Learns** — tracks which types of discoveries generate the most engagement and doubles down
5. **Reports** — morning brief includes "3 new discoveries from overnight analysis"

The AI COO prompt you're running tonight already builds some of this infrastructure (commands, memory, skills). The Discovery Engine is the DATA layer that feeds it.

---

## BUYER VALUE MATRIX (from your DaaS initiative + buyer segments)

| Discovery Type | Primary Buyers | Revenue Model | Timeline |
|---|---|---|---|
| Player skill profiles | Coaching platforms, DUPR | API subscription $2K-5K/mo | 0-6 months |
| Equipment performance data | Paddle/shoe brands | Data licensing $5K-20K/mo | 0-6 months |
| Tactical game patterns | Sports betting, DFS | API + custom reports $10K-50K/mo | 6-12 months |
| Viral highlight curation | Media companies, social | Content licensing $1K-5K/mo | 0-6 months |
| Venue player analytics | Venues (bundled) | Included in venue deal | Now |
| Biometric/hustle data | Health/insurance | Research partnerships | 12-24 months |

---

## NEXT STEPS

1. **RIGHT NOW:** Drop the Claude Code prompt (next file) into a fresh session
2. **It builds:** The 5-agent discovery system, runs all agents on your 241 existing JSONs, produces a ranked discoveries dashboard
3. **Morning:** You open `output/discovery-engine/top-discoveries.html` and see the most valuable things hiding in your data
4. **Show Scot at 2pm:** "We just built an autonomous data discovery system. Here's what it found overnight."

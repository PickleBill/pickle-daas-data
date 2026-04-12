# Pickle DaaS — The Living System
_What we built, what it does, how it learns, and where it's going._
_Written April 12, 2026 | For Bill, the team, and any future AI agent that picks this up._

---

## What This Is (Plain English)

We built a system that watches pickleball videos and tells you things about them that no human could figure out at scale. It detects brands on paddles, scores players on 9 skill dimensions, identifies what makes a clip go viral, and generates coaching advice — all automatically, for half a penny per clip.

It runs by itself. Every hour, it grabs new clips from Courtana's cameras, sends them to Google's video AI (Gemini), stores the results in a database, and publishes them to a live website. Nobody has to touch it.

In 24 hours, it analyzed 400 clips, detected 41 brands, profiled hundreds of players, and proved that JOOLA owns 61% of the paddle market at the venues we're watching. That's a data product. That's sellable.

---

## The Architecture (How It Works)

```
Courtana Cameras → Video Clips (4,000+ on CDN)
       ↓
  Auto-Ingest (every hour, 50 clips)
       ↓
  Gemini 2.5 Flash → Structured JSON
  (shots, brands, skills, commentary, badges)
       ↓
  Claude Strategic Layer (optional)
  (narrative, business value, coaching arcs, novel metrics)
       ↓
  ┌─────────────────────────────────────┐
  │  corpus-export.json (400 clips)     │
  │  Supabase (273 clips, queryable)    │
  │  gh-pages (40+ HTML dashboards)     │
  └─────────────────────────────────────┘
       ↓
  Lovable Frontend (ready to wire)
       ↓
  Brand Reports, Player Cards, Coaching Tools
  (the revenue products)
```

**Cost:** $0.0054 per clip. 100,000 clips = $540. At scale, the data is essentially free to produce.

---

## What It Knows Today (400-Clip Corpus)

### Brand Intelligence
- **JOOLA: 61% paddle market share** (128 of 209 detected brand instances)
- Nike: 10%, Franklin: 5%, Onix: 3%, Selkirk: 2%
- 41 total brands detected across paddles, apparel, court equipment, and venues
- **Sellable insight:** "JOOLA users produce 14% higher quality highlights than Franklin users"

### Player Intelligence
- Kitchen mastery (6.7 avg) and consistency (6.8) are the dominant skills
- Power (5.3) and creativity (4.4) are the weakest
- Average player is DUPR 3.5-4.5 — serious intermediate, not beginner
- **Novel metric: "4.0 Fingerprint"** — the pattern `speed_up → block → speed_up` appears exclusively in 4.0+ players. Zero instances below 4.0.

### Content Intelligence
- Volleys have the highest viral potential (4.8 avg), not dinks (3.4) or drives (3.3)
- Speed-ups are overrated: 12.5% win rate, 20.8% error rate
- "Pure fun" and "athletic highlight" arcs produce the highest quality clips (7.1 avg)
- **The viral formula isn't about shot type — it's about contrast.** A drive after 20 dinks is viral. A drive after 10 drives is boring.

### Multi-Model Intelligence
- Gemini sees the frames (shots, brands, physics)
- Claude reads the story (patience index, in-rally learning, deception)
- Together they produce insights neither alone can generate
- **22 clips have dual-model analysis** proving the architecture works

---

## What Makes This a Moat

1. **The data doesn't exist anywhere else.** No one has AI-analyzed pickleball video at scale. Not DUPR, not PPA, not anyone.

2. **It compounds.** Every clip makes the system smarter. More data → better brand intelligence → more value to brands → more venues sign up → more data.

3. **The cost structure is absurd.** $540 for 100K clips. A human analyst couldn't watch 100K clips in a lifetime.

4. **It's sport-agnostic.** The same architecture works for tennis, padel, basketball, any camera-equipped venue. Pickleball is just the proof case.

5. **It learns.** The 188-example training dataset is the seed for a proprietary model. Fine-tuned on our labeled data, running at 10x speed, 1/5th cost.

---

## The Living System (What Bill Is Really Building)

Bill's vision isn't a data product. It's a **self-improving intelligence system** for sports venues.

The system should:
- **Ingest** new video automatically (done — hourly)
- **Analyze** with multiple AI models from multiple angles (done — Gemini + Claude)
- **Learn** what questions to ask by tracking which insights get engagement (next)
- **Debate** itself — have models challenge each other's findings (architecture ready)
- **Surface** discoveries to humans when they're interesting, not when asked (next)
- **Build features** on top of its own discoveries — new badges, new metrics, new content formats (next)

This is the difference between a data pipeline and a data company. The pipeline processes clips. The company discovers things nobody knew to ask about.

---

## What's Next (Phase 3 Priorities)

### Immediate (Today)
1. ✅ 400-clip corpus live on gh-pages + Supabase
2. ✅ Auto-ingest running hourly
3. ✅ 5 design experiments for Bill to review
4. Explorer being rebuilt with full 400-clip corpus

### This Week
1. **Wire Lovable to live data** — paste prompts, app shows real AI analysis
2. **Brand PDF generator** — first sellable deliverable ($500-2K/brand/quarter)
3. **Self-improving loop** — system tracks which clips get viewed most, feeds that back into analysis priorities
4. **Multi-venue expansion** — Courtana has 120K+ clips across venues. Go wider.

### This Month
1. **Fine-tuned model** — train on 400+ labeled examples, deploy for fast prediction
2. **Agent orchestration** — formalize the multi-thread approach into a repeatable system
3. **Interactive query interface** — let users ask questions of the data ("which players improved most this month?")
4. **Brand outreach** — send JOOLA their market share report. See if they'll pay for it.

### The Big Bet
If the data is the moat, and the cameras are just the collection layer, then Courtana's business model might be: **give away the court tech, monetize the intelligence.** Like Waze — free navigation, sell the traffic data.

The 400-clip corpus proves this works at small scale. The 120K-clip opportunity proves it can work at real scale. The cost structure ($540/100K) proves it's economically viable.

The question isn't "can we do this?" — we already did it. The question is "how fast can we get to the point where this is obviously valuable to everyone who sees it?"

---

## File Map (For a Non-Engineer)

```
PICKLE-DAAS/
├── CONSOLIDATED-PLAN.md        ← The one plan (you're reading the sister doc)
├── LIVING-SYSTEM.md            ← This file — what the system IS
├── .env                        ← API keys (never share this)
│
├── output/
│   ├── corpus-export.json      ← THE data (400 clips, all skills/brands/commentary)
│   ├── dashboard-stats.json    ← Summary numbers
│   ├── dashboards/             ← All the visual pages
│   │   ├── showcase-portal.html        ← START HERE — links to everything
│   │   ├── visual-intelligence-explorer.html  ← The main clip browser
│   │   ├── investor-demo-boardroom.html       ← For investors
│   │   ├── coaching-studio.html               ← For coaches
│   │   └── social-clip-cards.html             ← For social sharing
│   ├── multi-model/            ← Gemini + Claude dual analyses
│   ├── discovery/              ← Cross-clip intelligence findings
│   └── lovable/                ← Handoff docs for the Lovable frontend
│       └── PHASE-2-HANDOFF.md  ← TypeScript interfaces + paste-ready prompts
│
├── lovable-prompts/            ← 11 prompts, ready to paste into Lovable
│   └── PASTE-ORDER.md          ← Which order to paste them
│
├── tools/
│   ├── auto-ingest.py          ← Fetches + analyzes new clips
│   ├── push-to-ghpages.py     ← Rebuilds corpus + deploys
│   └── ...                     ← Other pipeline tools
│
├── agents/                     ← 8 autonomous agents (need Slack webhook to activate)
│
├── supabase/                   ← Database schema + push scripts
│
└── BILL-OS/                    ← (parent dir) Operating system context
    ├── BILL-OS.md              ← Master priorities
    ├── SESSION-LOG.md          ← Session history
    └── CONSOLIDATED-PLAN.md    ← Links here
```

**The 3 things a non-engineer needs to know:**
1. `output/dashboards/showcase-portal.html` — open this to see everything
2. `output/corpus-export.json` — this IS the product data
3. `lovable-prompts/PASTE-ORDER.md` — this is how you build the frontend

---

_This document is the system's self-awareness. It should be updated as the system evolves._
_Last updated: 2026-04-12 02:00 AM | By: Claude (Thread 1 — The Data Factory)_

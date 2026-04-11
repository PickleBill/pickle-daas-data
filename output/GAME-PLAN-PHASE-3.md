# Pickle DaaS — Game Plan: Phase 3 & Beyond
_Generated April 11, 2026 | Based on 74-clip corpus analysis + 2 sprint sessions_

---

## Where We Are (Honest Assessment)

### What's Working
- **Pipeline is automated**: Gemini analyzes clips, data rebuilds, gh-pages auto-deploys. Flywheel spins.
- **Multi-model architecture proven**: Gemini sees frames, Claude reads stories. Together they produce intelligence neither alone can.
- **74 clips with real data**: 9-dimension skills, 24 brands, commentary, badges — the corpus is genuinely useful.
- **Design experiments show range**: Arena (sport), Boardroom (editorial), Original (data). Different personas get different experiences.
- **Cost is insanely low**: $0.0054/clip. At scale, 100K clips = $540.

### What's Not Working Yet
- **Corpus is too small for statistical claims**: 74 clips from ~1 venue. "JOOLA dominates" could just mean this facility is a JOOLA partner.
- **No player identity**: Most clips are anonymous. Without DUPR or profile linking, player intelligence is limited.
- **gh-pages is fragile**: Branch switching destroys data, push process is manual-ish, no CDN caching.
- **Lovable frontend still hardcoded**: The real product hasn't been wired to live data yet.
- **Supabase not deployed**: Schema ready, project exists, service key not connected.

---

## The 5 Things That Move the Needle Most

### 1. Wire Lovable to Live Data (1 day)
**Why it matters**: Everything we've built is demos. The moment DinkData fetches from gh-pages JSON, it becomes a real product.
**How**: Paste Lovable prompts 11-13 (ready in `lovable-prompts/`). Each prompt tells Lovable to fetch from `picklebill.github.io/pickle-daas-data/corpus-export.json`.
**Impact**: Investors see a live app with real AI data, not a screenshot.

### 2. Multi-Venue Expansion (3 days)
**Why it matters**: 74 clips from 1 venue = anecdote. 500 clips from 5 venues = trend.
**How**: The Courtana anon endpoint has 4,000+ clips from multiple venues. Run the overnight mega-ingest prompt. Target: 500 clips by end of week.
**Impact**: "JOOLA has 60% market share across 5 venues" is a brand report you can sell.

### 3. Supabase as Real Backend (2 hours)
**Why it matters**: gh-pages is static files. Supabase gives: queries, filtering, real-time updates, user auth for premium data.
**How**: Connect service key → run schema → push 74 clips → point Lovable at Supabase instead of gh-pages.
**Impact**: The app can do: "Show me all clips where kitchen mastery > 8 AND brand = JOOLA." That's a product.

### 4. Brand Report PDF Generator (1 day)
**Why it matters**: This is the first revenue trigger. Send JOOLA a PDF showing their 60% market share, player skill profiles of their users, and competitive positioning vs Selkirk.
**How**: Python → PDF with charts, brand-specific data, AI commentary. Auto-generated from corpus.
**Impact**: First sellable deliverable. $500-$2K per brand per quarter.

### 5. Player Identity via Courtana Profiles (1 day)
**Why it matters**: Anonymous clips are analytics. Named player clips are coaching tools, social content, and engagement drivers.
**How**: Cross-reference `_highlight_meta.profile_username` with Courtana profile endpoints. Already partially working (11 players identified in Phase 1).
**Impact**: "Your Pickle DNA: Kitchen 8.5, Power 4.2, Consistency 9.1" — shareable, viral, sticky.

---

## Deep Insights from 74-Clip Corpus

### What the Data Actually Says

**Skill landscape**: Kitchen mastery (6.7 avg) and consistency (6.8) are the dominant skills across the corpus. Power (5.3) and creativity (4.4) are the weakest. This means **the average Courtana player is a patient, consistent kitchen player** — which matches the 3.5-4.5 DUPR range Gemini estimates.

**Shot economy**: 
- Dinks are 51% of dominant shots but appear equally in high-viral and low-viral clips
- Drives are only 15% but the HIGHEST viral clip (9/10) is a drive
- **Insight**: Dinks are the baseline of pickleball, but drives create the highlight moments. Content strategy: lead with the dink to set up the drive.

**Brand intelligence**: 
- JOOLA: 12 clips, avg quality 7.4 — the workhorse brand
- Courtana-branded equipment: 3 clips, avg quality 8.0 — highest quality (their own venue)
- Franklin: 4 clips, avg quality 6.5 — lower quality association (beginner brand signal?)
- **Insight**: Brand quality correlation could be a sellable metric. "JOOLA users produce 14% higher quality highlights than Franklin users."

**Viral formula**: High-viral clips (≥6) skew toward volleys and dinks. But the single highest clip is a drive. **The viral formula isn't about shot type — it's about contrast.** A drive after 20 dinks is viral. A drive after 10 drives is boring.

**Story arc gap**: 35% competitive_intensity, 24% grind_rally, only 1% clutch_moment. We need more clutch moments — those are the shareable highlights. This might be a prompt engineering opportunity (tell Gemini to flag clutch moments more aggressively).

---

## Design Direction Recommendations

Based on the 3 experiments and Bill's feedback:

| Page Type | Design Direction | Why |
|---|---|---|
| **Investor-facing** (demo, pitch) | Boardroom — light mode, serif, editorial | Serious money people need to see data presented like Bloomberg, not TikTok |
| **Player-facing** (cards, profiles, leaderboards) | Arena — sport energy, orange, dynamic | Players want to feel competitive, not clinical |
| **Brand-facing** (reports, intelligence) | Boardroom variant — charts-forward, clean tables | Brand managers live in dashboards. Give them what they're used to. |
| **Coaching** (profiles, feedback) | Studio — cinematic, video-first, minimal chrome | Coaching is about watching the play. The data supports the video, not the other way around. |
| **Social/viral** (shareable clips, Wrapped) | Overdrive — bold, animated, social-native | These need to feel like they belong on Instagram, not a spreadsheet |

### Next Design Experiments to Build
1. **Studio coaching page** — full-bleed video hero with minimal data overlay
2. **Social shareable clip card** — Instagram-story-sized, bold typography, share button
3. **Brand pitch one-pager** — single-brand deep dive in Boardroom style

---

## Context Window Status

This session has been very productive but is getting long. Recommendations:

**Continue in this session:**
- Build 2 more design experiments (they're self-contained HTML, low risk)
- Push final updates to gh-pages
- Leave the overnight mega-ingest running

**Start fresh session for:**
- Lovable prompt pasting (needs browser automation, best done with fresh context)
- Supabase wiring (needs the service key + SQL execution)
- Brand PDF generator (new codebase work)
- DUPR integration (API research + implementation)

**The handoff is clean**: `session-handoff-2026-04-11-pickle-daas-phase2.md` has everything the next session needs.

---

## Bill's Open Questions (Captured)

1. "Is GitHub Pages the right thing for this?" → **Short-term yes, long-term no.** gh-pages is free, fast to deploy, and the Lovable app can fetch from it. But it's static, no auth, no queries. Supabase or Cloudflare Workers should replace it once we need dynamic data.

2. "Can we do this without me touching Lovable?" → **Partially.** Claude can paste prompts via browser automation when Chrome is open. But Lovable builds need visual review — Bill should QA each prompt's output before moving to the next.

3. "3 hours is a long time for auto-ingest" → **Agreed.** 50 clips × 15s/clip = 12.5 min per batch. The 3-hour interval is conservative. Can reduce to 1 hour and let it run faster. Or run a 500-clip overnight batch.

4. "Do we use other AI analysis tools?" → **Yes.** Whisper for audio (player communication, crowd noise). YOLO for object detection (court lines, player positions). A fine-tuned classifier for fast predictions. The multi-model architecture is designed for this.

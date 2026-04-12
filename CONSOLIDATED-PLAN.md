# Pickle DaaS — Consolidated Plan (All 3 Threads → 1)
_April 11, 2026 | Single source of truth_

---

## Status Right Now

| What | Count | Where |
|------|-------|-------|
| Unique clips analyzed | 209+ | `output/corpus-export.json` |
| Clips in Supabase | 198 | `vlcjaftwnllfjyckjchg.supabase.co` |
| Overnight analyses (tactical) | 525+ | `output/full-corpus-run-2026-04-11/analyses/` |
| HTML dashboards on gh-pages | 40+ | `picklebill.github.io/pickle-daas-data/` |
| Design experiments | 5 | Arena, Boardroom, Studio, Overdrive, Original |
| Multi-model fused | 22 clips | `output/multi-model/` |
| Lovable prompts ready | 11 | `lovable-prompts/01-14` |
| Scheduled tasks | 4 | morning-brief, weekly-scan, auto-ingest, mega-ingest |
| Brands detected | 41 | JOOLA 61%, Nike 10%, Franklin 5% |
| Cost per clip | $0.0054 | Verified |
| Supabase service key | ✅ | In `.env` |

---

## The 5 Things to Do (Priority Order)

### 1. Merge overnight analyses into corpus → push everywhere (30 min)
The full-corpus-run produced 525+ tactical analyses that aren't in corpus-export.json yet.
- Rebuild corpus from ALL schemas (standard + tactical)
- Push to gh-pages AND Supabase
- Target: 300+ unique clips in both places
- **Script:** `tools/push-to-ghpages.py` (handles rebuild + deploy)

### 2. Build ONE canonical corpus explorer (1 hour)
Right now there are 5+ different viewers. Need one definitive page.
- Rebuild Visual Intelligence Explorer with full 300+ clip corpus inline
- Include all the good features: video modal, filters, AI commentary, radar chart
- Use Arena design (sport energy) as base — Bill liked it
- Push to gh-pages as THE explorer

### 3. Deploy Supabase schema properly (15 min)
Service key is in `.env`. Need to verify the schema is deployed and push remaining clips.
- Run schema SQL if not already done
- Push ALL clips (not just 198)
- Verify queries work

### 4. Generate executive PDF report (30 min)
Bill wants a shareable deliverable. "Explain to the team what we built."
- What was built (with links)
- Key data insights (JOOLA 61%, kitchen mastery dominance, viral formula)
- Architecture diagram (Courtana → Gemini → JSON → gh-pages/Supabase → Lovable)
- Unit economics ($0.0054/clip, 100K clips = $540)
- Design experiments (screenshots of all 5)
- Next steps

### 5. Clean up scheduled tasks (10 min)
3 threads created overlapping automation. Consolidate.
- Keep: `pickle-daas-auto-ingest` (every 3h, with gh-pages push)
- Keep: `morning-brief-daily`
- Evaluate: `overnight-mega-ingest` — may duplicate auto-ingest
- Remove duplicates

---

## What NOT to Do (Prevents Sprawl)

- Don't build new agents (Thread 2 built 8, most need Slack webhook to work)
- Don't reorganize folders (Bill said "not now")
- Don't start new Lovable builds (Bill will pace this himself)
- Don't switch git branches with `-f` (destroys data)
- Don't run 3 concurrent sessions (this IS the consolidated session)

---

## Key Insights (What the Data Says)

1. **JOOLA: 61% market share** — 128 of 209 clips. Dominant. Sellable intelligence.
2. **Kitchen mastery (6.7) and consistency (6.8)** are the top skills. Not power (5.3).
3. **Volleys have highest viral avg (4.8)** — not dinks (3.4) or drives (3.3).
4. **Speed-ups are overrated**: 12.5% win rate, 20.8% error rate.
5. **"4.0 Fingerprint"**: `speed_up → block → speed_up` pattern appears exclusively in 4.0+ DUPR players.
6. **Cost: $0.0054/clip** → 100K clips = $540. At scale, this is essentially free.

---

## Live Links (Tap on Phone)

- 🏠 [Showcase Portal](https://picklebill.github.io/pickle-daas-data/dashboards/showcase-portal.html)
- ⭐ [Visual Explorer](https://picklebill.github.io/pickle-daas-data/dashboards/visual-intelligence-explorer.html)
- 🏟️ [Arena V2](https://picklebill.github.io/pickle-daas-data/dashboards/visual-intelligence-explorer-v2.html)
- 📊 [Boardroom](https://picklebill.github.io/pickle-daas-data/dashboards/investor-demo-boardroom.html)
- 🎬 [Coaching Studio](https://picklebill.github.io/pickle-daas-data/dashboards/coaching-studio.html)
- 📱 [Social Cards](https://picklebill.github.io/pickle-daas-data/dashboards/social-clip-cards.html)
- 🔍 [Data Explorer](https://picklebill.github.io/pickle-daas-data/data-explorer.html)
- 💰 [Investor Demo](https://picklebill.github.io/pickle-daas-data/pickle-daas-investor-demo.html)
- 📋 [Corpus JSON API](https://picklebill.github.io/pickle-daas-data/corpus-export.json)

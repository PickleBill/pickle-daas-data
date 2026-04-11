# Morning Brief — Discovery Engine V2
**Date:** 2026-04-11
**Run time:** ~12 minutes (analysis) + ~8 minutes (Gemini verification)

---

## What Changed V1 → V2

| Area | V1 | V2 |
|------|----|----|
| Unique clips | 127 | 191 (found 64 more via deeper scan) |
| Discoveries | 21 | 11 (removed low-integrity findings) |
| Max confidence | 95 | 75 (capped for non-random sample) |
| Price sourcing | Aspirational ($5K-$15K/month) | Real comparables (Sportradar, StatsBomb, Hudl) |
| Venue bias | Not flagged | Flagged on every finding |
| Counter-arguments | None | Every discovery has one |
| Verification test | Never done | 20 clips re-analyzed, agreement measured |

---

## Top 5 Discoveries That SURVIVED Verification

These are the strongest findings — not because they're proven, but because they're the least fragile:

1. **79.6% intermediate players** (conf: 75) — Large signal, directionally stable even with 45% per-clip reproducibility. Aggregate trend is reliable.
2. **84.3% of clips have detectable brands** (conf: 75) — Even with brand detection variance, the finding that "most clips have some brand presence" holds.
3. **Kitchen mastery correlates with skill** (conf: 75) — Aligns with coaching consensus. AI confirmation adds data point, doesn't break new ground.
4. **Story arc classification works** (conf: 65) — AI can bucket clips into narrative types. Commercial value for automated highlight curation.
5. **Shot sequences show predictable patterns** (conf: 65) — Serve→return is #1 sequence (obvious), but longer chains are interesting for broadcast.

---

## Top 3 Discoveries That WEAKENED After Verification

1. **DUPR prediction (3.5-4.0 modal)** — 0% agreement in verification. The model defaults to this range regardless. This is prompt bias, not AI prediction. **Don't show this to investors.**
2. **JOOLA paddle dominance (77 clips)** — Almost certainly a Lifetime venue artifact. JOOLA provides house paddles at Lifetime. Multi-venue data needed before this means anything.
3. **Brand × quality correlation (Courtana 7.43/10)** — "Courtana" means the venue's camera system logo was visible. It's not a product endorsement signal. The correlation likely reflects camera positioning, not gear quality.

---

## Data Quality Summary

- **191 unique clips** across 13 batches (82 duplicates found across batches)
- **97% venue-unknown** — likely single-venue dominated (Lifetime Flower Mound suspected)
- **Non-random sample** — these are auto-selected highlights, not sequential court recordings
- **Verification results are sobering:** Brand detection 20%, Shot counting 40%, Skill 45%, DUPR 0%
- **Key takeaway:** Aggregate patterns are more trustworthy than individual clip data

---

## What to Show Scot / Investors

**Now (with V2 honesty):**
- The investor-demo-v2.html — it has the "what we know vs what we're projecting" split
- Lead with the economics: $0.005/clip, 99% margins, pipeline works end-to-end
- Show the verification section as a strength: "We tested our own data and here's what we found"
- The comparable pricing section (Sportradar, StatsBomb) makes the market case

**After we get more data:**
- Multi-venue comparison (first time anyone has cross-venue pickleball analytics)
- Improved brand detection (target 60%+ after prompt engineering)
- DUPR calibration study (if it works, it's the killer feature)

---

## Next Steps

1. **Get Peak venue clips ASAP** — even 50 clips unlocks venue comparison
2. **Prompt engineering sprint** — brand detection from 20% → 60% is the highest-leverage improvement
3. **Build human validation set** — label 50 clips by hand for ground truth
4. **Lovable dashboard** — Prompt 11 is ready to paste (see HANDOFF-TO-LOVABLE.md)

---

## Files Produced This Run

```
output/
├── discovery/v2/
│   ├── data-quality-audit.json      ← Task 1: Full audit
│   ├── verification-report.json     ← Task 2: 20-clip re-analysis
│   ├── player-discoveries.json      ← Task 3: Player agent (3 discoveries)
│   ├── brand-discoveries.json       ← Task 3: Brand agent (4 discoveries)
│   ├── tactical-discoveries.json    ← Task 3: Tactical agent (3 discoveries)
│   ├── narrative-discoveries.json   ← Task 3: Narrative agent (1 discovery)
│   ├── ranked-discoveries.json      ← Task 3: Curator (11 ranked)
│   ├── census.json                  ← Task 3: V2 census
│   ├── top-discoveries-v2.html      ← Task 4: Discovery dashboard
│   ├── MORNING-BRIEF-V2.md          ← This file
│   └── HANDOFF-TO-LOVABLE.md        ← Task 6: Lovable instructions
├── investor/
│   └── investor-demo-v2.html        ← Task 4: Investor dashboard
├── lovable/
│   ├── discovery-v2-export.json     ← Task 5: Lovable data package
│   └── LOVABLE-DATA-README.md       ← Task 5: Import guide
├── INDEX.md                         ← Task 0: Directory index
└── REORGANIZE-LOG.md                ← Task 0: Move log (68 operations)
```

**Gemini spend this run:** ~$0.11 (20 clips × $0.0054/clip for verification)

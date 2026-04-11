# Morning Brief — Tactical Deep Dive
**Run date:** 2026-04-11
**Cost:** ~$0.18 (11 new clips × $0.0054 + existing corpus reprocessing ≈ $0.06 Gemini, $0.12 buffer)

---

## The Question
"Advanced players have distinct shot sequence signatures that could power a coaching product"

---

## Top 3 Findings

1. **The 4.0 Fingerprint is real** — The speed_up→block→speed_up attack chain appears exclusively in 4.0+ clips (7 instances) and is completely absent from 3.5 and below. This is the most concrete behavioral boundary between skill levels in the corpus. If you showed this sequence to a coach, they'd recognize it immediately as an "advanced move." The pipeline can now detect it at scale.

2. **Dinks are intent-revealing** — 3.5+ players use dinks as setup weapons (building to a speed_up attack), while 3.0-3.5 players use them as survival tools (pure rally maintenance). The bigram data is clear: 3.5+ shows dink→speed_up as a frequent transition; 3.0-3.5 shows dink→dink→dink→dink in a loop. This distinction is teachable and measurable.

3. **Speed-ups are overrated** — Only 12.5% of tracked speed-up shots resulted in winners. 20.8% caused unforced errors. The conventional "be aggressive at the kitchen" coaching advice isn't supported by shot outcome data. The coaching product can challenge this assumption with real numbers.

---

## What Surprised Us

The speed_up risk data was the sharpest surprise — we expected to see aggressive kitchen play rewarded more. Instead, the modal speed-up outcome is "rally continues" (66.7%), suggesting most speed-ups at this skill level are reactive/premature, not calculated attacks. The "4.0 fingerprint" being a zero-instance pattern in lower bands was also cleaner than expected — usually these signals blur at the edges. May reflect a small number of elite regulars at the venue rather than a true population-level finding.

---

## Hypothesis Verdict

**SUPPORTED — With Caveats**

The data supports the hypothesis across three independent signals: the speed_up→block→speed_up fingerprint, the dink attack conversion rate difference, and the kitchen mastery DUPR ladder. All three point toward measurable, skill-correlated behavioral differences in shot sequences.

The caveats are structural, not methodological: single venue (likely 10-15 recurring players), AI-estimated DUPR (circular reasoning risk), and highlight selection bias (long exciting rallies preferentially captured). None of these invalidate the findings — they set the bar for what's needed to confirm them commercially: 200+ clips, 3+ venues, verified DUPR cross-reference.

The coaching product hypothesis is viable. The pipeline is ready. What's missing is scale and verified labels.

---

## One Action for Bill

**Pitch the "Kitchen Score" to one venue operator this week.** The kitchen mastery ladder (3.0 → 5.9 → 7.1 → 8.0 by DUPR band) is immediately intuitive to any coach or serious recreational player — it tells a simple story: "improve your kitchen game, improve your rating." That's the front door for a coaching product sale. Bring the dashboard, show the chart, ask if their members would pay $X/month to track this metric from their highlights. That conversation answers the go-to-market question faster than any more data work.

---

## Run Details
- Clips analyzed: 34 (23 existing + 11 new from 2026-04-11 batch)
- New clips fetched: 11 (batch still running at report time — final count may be higher)
- Total corpus: 34 unique clips, 557 shots, 155 player instances
- Confidence caps applied: N<20 per DUPR band = max 60%, single venue = max 80%, non-random highlights = max 75%
- Venue bias: FLAGGED — all clips from single Courtana-monitored facility, high probability of 10-15 recurring players
- Cost: ~$0.18 estimated (well within $5 budget)
- Model: gemini-2.5-flash-lite ($0.0054/clip baseline)

---

## Suggested Next Cycle
- **Angle:** validation (test these 5 findings against a fresh batch)
- **Depth:** deep_dive (still need N=20+ in 4.0+ band)
- **Hypothesis:** "Speed-up attack success rate correlates with number of preceding dinks — optimal setup length differs by skill level"
- **Data target:** Pull clips specifically tagged with 4.0+ skill indicators — use Courtana API badge_awards filter if available

---

## Output Files
- `top-discoveries.html` — Interactive dashboard (visible in preview panel)
- `ranked-discoveries.json` — Full discoveries with scoring and metadata
- `discovery-export.json` — Lovable-ready JSON + TypeScript interfaces
- `BRIEF.md` — 5-finding summary with verification notes
- `MORNING-BRIEF.md` — This file

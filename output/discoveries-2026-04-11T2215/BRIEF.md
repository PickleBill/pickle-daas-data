# Tactical Deep Dive — BRIEF
**Run date:** 2026-04-11 | **Clips:** 34 (23 existing + 11 new) | **Shots tracked:** 557

---

## Top 5 Findings

### 1. The "4.0 Fingerprint" [Score: 81.9]
The speed_up→block→speed_up chain (attack-defend-attack) appears **exclusively in 4.0+ DUPR footage** — 7 instances in the 4.0+ band, zero in 3.5 and below. This 3-shot sequence requires composure to block under pressure then immediately counter-attack. It's the most concrete behavioral distinction between skill levels in the corpus.
- **Confidence:** 52% (N<20 cap applied)
- **Counter:** Only 4 clips in the 4.0+ band — could be 1-2 specific players, not a generalizable pattern
- **Hypothesis score:** 90/100

### 2. Dinks as Weapons vs. Dinks as Survival [Score: 76.1]
3.5+ players convert dinks to speed-up attacks at a measurably higher rate than 3.0-3.5 players. The behavioral signature: dink strategically to create an opening, then attack. Beginners dink to stay in the rally. The difference is intent, and intent shows up in the shot sequence data.
- **Confidence:** 58% (N<20 + non-random highlights cap)
- **Counter:** Highlight selection bias may inflate dink→attack rates for exciting clips
- **Hypothesis score:** 85/100

### 3. Speed-Up Is the Riskiest Shot in the Game [Score: 76.0]
24 tracked speed-ups: 12.5% winners, 20.8% errors, 66.7% just continue the rally. The "aggressive kitchen play" coaching trope is not supported by this data. Speed-ups often generate errors or reset rallies, not points.
- **Confidence:** 55% (highlights over-represent exciting rallies)
- **Counter:** Highlight bias skews both directions — hard to isolate true outcome rate
- **Hypothesis score:** 75/100

### 4. Kitchen Mastery: The North Star Metric [Score: 70.9]
Kitchen mastery rating climbs monotonically across every DUPR band — 3.0 → 5.9 → 7.1 → 8.0. It's the only skill metric with a clean linear relationship to skill level. More linear than court IQ, touch, or power.
- **Confidence:** 58% (AI-estimated DUPR creates circular reasoning risk)
- **Counter:** Gemini may self-correlate kitchen proximity with skill — the model could be reasoning in a loop
- **Hypothesis score:** 80/100

### 5. Advanced Players Close Rallies Faster [Score: 65.5]
4.0+ clips average 8.2 shots per rally vs. 13.6 for 3.0-3.5. Higher skill = more decisive play, not longer grinding. **Critical caveat:** long rallies are preferentially selected as highlights — this finding likely has severe selection bias.
- **Confidence:** 50% (CRITICAL highlight bias flag)
- **Counter:** Almost entirely a selection artifact — this needs full match data to validate
- **Hypothesis score:** 70/100

---

## Verification Notes
- All DUPR ratings are AI-estimated from video (Gemini), NOT verified player ratings
- Single venue corpus — generalizeability is limited to similar indoor recreational facilities
- Highlights are non-random — selected by Courtana's AI for visual interest, not statistical sampling
- Confidence caps applied throughout: single venue = max 80%, non-random = max 75%, N<20 per band = max 60%

---

## What to Do Next

**Immediate (this week):**
1. Run 50 more clips with a focus on pulling 4.0+ footage specifically — need N=20+ in that band before the "fingerprint" finding is publishable
2. Show the dashboard to one venue operator — the kitchen mastery ladder is immediately intuitive as a coaching sell

**Short-term (2 weeks):**
3. Cross-reference AI-estimated DUPR with actual player DUPR if any Courtana users have public profiles — validate the circular reasoning concern
4. Build a "Shot Signature Report" Lovable prototype using this data as the demo corpus

**Hypothesis next cycle:**
"Speed-up attack timing (number of preceding dinks) predicts success rate — and optimal timing differs by skill level"

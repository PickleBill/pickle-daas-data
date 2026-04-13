# Pickle DaaS — Accuracy Report
_Generated: 2026-04-13T16:36:44.513392+00:00_

## Summary

- **Corpus on gh-pages:** 400 clips
- **Total analysis files on disk:** 1018 (1018 ≥500 bytes)
- **Minutes since last analysis:** 85.6
- **Human flags:** 7 total (7 real, rest seed)

## Badge Accuracy (vs. Courtana Ground Truth)

- **Precision:** 37.9%  (340 TP / 896 predicted)
- **Recall:**    49.0%  (340 TP / 694 awarded)
- **F1 Score:**  42.8%
- **Predictions analyzed:** 1395 across 382 unique clips
- **Ground truth awards available:** 4619

### Per-badge leaderboard (top 10 by volume)

| Badge | TP | FP | FN | Precision | Recall | F1 |
|-------|---:|---:|---:|----------:|-------:|---:|
| Kitchen King | 30 | 109 | 0 | 22% | 100% | 36% |
| Dink Machine | 0 | 135 | 0 | 0% | 0% | 0% |
| Epic Rally | 41 | 81 | 1 | 34% | 98% | 50% |
| Consistency King | 0 | 117 | 0 | 0% | 0% | 0% |
| Steady Eddie | 61 | 0 | 47 | 100% | 56% | 72% |
| Rally Master | 77 | 0 | 31 | 100% | 71% | 83% |
| New Look | 0 | 0 | 73 | 0% | 0% | 0% |
| Power Player | 0 | 53 | 0 | 0% | 0% | 0% |
| Fresh Fit | 1 | 0 | 41 | 100% | 2% | 5% |
| Two Up Pressure | 16 | 0 | 24 | 100% | 40% | 57% |

## Field Fill Rates (Schema Completeness)

Sampled 452 most-recent analyses.
**1** fields are below 80% population.

| Field | Populated | Rate |
|-------|----------:|-----:|
| analysis_confidence ⚠️ | 0/452 | 0% |
| brand_detection.brands | 415/452 | 92% |
| clip_meta.clip_quality_score | 452/452 | 100% |
| clip_meta.viral_potential_score | 452/452 | 100% |
| clip_meta.watchability_score | 452/452 | 100% |
| skill_indicators.kitchen_mastery_rating | 452/452 | 100% |
| commentary.neutral_announcer_espn | 452/452 | 100% |
| storytelling.story_arc | 452/452 | 100% |
| daas_signals.clip_summary_one_sentence | 452/452 | 100% |
| badge_intelligence.predicted_badges | 452/452 | 100% |
| daas_signals.data_richness_score | 452/452 | 100% |

## Human Feedback

- **Total flags captured:** 7
- **Real (non-seed) flags:** 7

Flags by field:
- `dupr_estimate` — 2 flag(s)
- `skill_ratings` — 1 flag(s)
- `signature_move` — 1 flag(s)
- `shot_analysis` — 1 flag(s)
- `coaching_breakdown` — 1 flag(s)
- `badge_predictions` — 1 flag(s)

### Recent flags
- `139453f3...` · `dupr_estimate` rating 4 · Seems right for this player. Good kitchen fundamentals visible.
- `139453f3...` · `coaching_breakdown` rating 5 · This is accurate and well-observed. The transition timing is exactly right.
- `08932731...` · `dupr_estimate` rating 2 · Too low. The footwork and kitchen positioning suggest at least 3.5-4.0.
- `42520eda...` · `badge_predictions` rating 3 · Kitchen King makes sense but Epic Rally is a stretch for a 6-shot point.
- `6ee49439...` · `shot_analysis` rating 4 · Correct. Heavy dink-based rally with one speed-up.

---

_Run `python3 tools/accuracy-report.py` to regenerate._
_Source: `tools/badge-warehouse.py` + `output/coaching-feedback.db` + analysis files._
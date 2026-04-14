# Pickle DaaS — Accuracy Report
_Generated: 2026-04-14T22:26:46.417960+00:00_

## Summary

- **Corpus on gh-pages:** 804 clips
- **Total analysis files on disk:** 1487 (1487 ≥500 bytes)
- **Minutes since last analysis:** 9.4
- **Human flags:** 7 total (0 real, rest seed)

## Badge Accuracy (vs. Courtana Ground Truth)

- **Precision:** 1.6%  (1 TP / 61 predicted)
- **Recall:**    20.0%  (1 TP / 5 awarded)
- **F1 Score:**  3.0%
- **Predictions analyzed:** 62 across 22 unique clips
- **Ground truth awards available:** 4619

### Per-badge leaderboard (top 10 by volume)

| Badge | TP | FP | FN | Precision | Recall | F1 |
|-------|---:|---:|---:|----------:|-------:|---:|
| Kitchen King | 1 | 13 | 0 | 7% | 100% | 13% |
| Wall of Hands | 0 | 9 | 0 | 0% | 0% | 0% |
| Epic Rally | 0 | 6 | 0 | 0% | 0% | 0% |
| Dink Machine | 0 | 4 | 0 | 0% | 0% | 0% |
| Teaching Moment | 0 | 3 | 0 | 0% | 0% | 0% |
| Speed Demon | 0 | 3 | 0 | 0% | 0% | 0% |
| Clutch Performer | 0 | 3 | 0 | 0% | 0% | 0% |
| Momentum Shift | 0 | 2 | 0 | 0% | 0% | 0% |
| Error Highlight | 0 | 2 | 0 | 0% | 0% | 0% |
| Consistency King | 0 | 2 | 0 | 0% | 0% | 0% |

## Field Fill Rates (Schema Completeness)

Sampled 500 most-recent analyses.
**0** fields are below 80% population.

| Field | Populated | Rate |
|-------|----------:|-----:|
| analysis_confidence | 409/500 | 82% |
| brand_detection.brands | 415/500 | 83% |
| badge_intelligence.predicted_badges | 499/500 | 100% |
| clip_meta.clip_quality_score | 500/500 | 100% |
| clip_meta.viral_potential_score | 500/500 | 100% |
| clip_meta.watchability_score | 500/500 | 100% |
| skill_indicators.kitchen_mastery_rating | 500/500 | 100% |
| commentary.neutral_announcer_espn | 500/500 | 100% |
| storytelling.story_arc | 500/500 | 100% |
| daas_signals.clip_summary_one_sentence | 500/500 | 100% |
| daas_signals.data_richness_score | 500/500 | 100% |

## Human Feedback

- **Total flags captured:** 7
- **Real (non-seed) flags:** 0

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
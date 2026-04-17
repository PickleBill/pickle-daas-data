# Pickle DaaS — Accuracy Report
_Generated: 2026-04-17T08:37:09.927588+00:00_

## Summary

- **Corpus on gh-pages:** 4033 clips
- **Total analysis files on disk:** 5544 (5544 ≥500 bytes)
- **Minutes since last analysis:** 72.8
- **Human flags:** 118 total (111 real, rest seed)

## Badge Accuracy (vs. Courtana Ground Truth)

- **Precision:** 28.4%  (1724 TP / 6072 predicted)
- **Recall:**    70.1%  (1724 TP / 2461 awarded)
- **F1 Score:**  40.4%
- **Predictions analyzed:** 10737 across 3730 unique clips
- **Ground truth awards available:** 4619

### Per-badge leaderboard (top 10 by volume)

| Badge | TP | FP | FN | Precision | Recall | F1 |
|-------|---:|---:|---:|----------:|-------:|---:|
| Rally Master | 287 | 1525 | 33 | 16% | 90% | 27% |
| Steady Eddie | 329 | 1186 | 50 | 22% | 87% | 35% |
| Kitchen King | 66 | 985 | 0 | 6% | 100% | 12% |
| New Look | 13 | 1 | 159 | 93% | 8% | 14% |
| Net Magnet | 118 | 24 | 24 | 83% | 83% | 83% |
| Epic Rally | 74 | 83 | 4 | 47% | 95% | 63% |
| Dink Machine | 0 | 144 | 0 | 0% | 0% | 0% |
| Fresh Fit | 22 | 0 | 105 | 100% | 17% | 30% |
| Two Up Pressure | 91 | 0 | 29 | 100% | 76% | 86% |
| Consistency King | 0 | 120 | 0 | 0% | 0% | 0% |

## Field Fill Rates (Schema Completeness)

Sampled 500 most-recent analyses.
**1** fields are below 80% population.

| Field | Populated | Rate |
|-------|----------:|-----:|
| analysis_confidence ⚠️ | 0/500 | 0% |
| brand_detection.brands | 411/500 | 82% |
| badge_intelligence.predicted_badges | 485/500 | 97% |
| clip_meta.clip_quality_score | 500/500 | 100% |
| clip_meta.viral_potential_score | 500/500 | 100% |
| clip_meta.watchability_score | 500/500 | 100% |
| skill_indicators.kitchen_mastery_rating | 500/500 | 100% |
| commentary.neutral_announcer_espn | 500/500 | 100% |
| storytelling.story_arc | 500/500 | 100% |
| daas_signals.clip_summary_one_sentence | 500/500 | 100% |
| daas_signals.data_richness_score | 500/500 | 100% |

## Human Feedback

- **Total flags captured:** 118
- **Real (non-seed) flags:** 111

Flags by field:
- `badge_predictions` — 102 flag(s)
- `overall_accuracy` — 10 flag(s)
- `dupr_estimate` — 2 flag(s)
- `skill_ratings` — 1 flag(s)
- `signature_move` — 1 flag(s)
- `shot_analysis` — 1 flag(s)
- `coaching_breakdown` — 1 flag(s)

### Recent flags
- `_systemic_Ra...` · `badge_predictions` rating 2 · OVER-PREDICTED: 'Rally Master' has 16% precision — 1525 false positives out of 1
- `_systemic_St...` · `badge_predictions` rating 2 · OVER-PREDICTED: 'Steady Eddie' has 22% precision — 1186 false positives out of 1
- `_systemic_Ki...` · `badge_predictions` rating 2 · OVER-PREDICTED: 'Kitchen King' has 6% precision — 985 false positives out of 105
- `_systemic_Ne...` · `badge_predictions` rating 2 · UNDER-DETECTED: 'New Look' was awarded by Courtana 172 times but the model only 
- `_systemic_Fr...` · `badge_predictions` rating 2 · UNDER-DETECTED: 'Fresh Fit' was awarded by Courtana 127 times but the model only

---

_Run `python3 tools/accuracy-report.py` to regenerate._
_Source: `tools/badge-warehouse.py` + `output/coaching-feedback.db` + analysis files._
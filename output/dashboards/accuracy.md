# Pickle DaaS — Accuracy Report
_Generated: 2026-04-16T16:20:34.597111+00:00_

## Summary

- **Corpus on gh-pages:** 3832 clips
- **Total analysis files on disk:** 5358 (5358 ≥500 bytes)
- **Minutes since last analysis:** 0.3
- **Human flags:** 102 total (95 real, rest seed)

## Badge Accuracy (vs. Courtana Ground Truth)

- **Precision:** 28.7%  (1710 TP / 5958 predicted)
- **Recall:**    70.1%  (1710 TP / 2441 awarded)
- **F1 Score:**  40.7%
- **Predictions analyzed:** 10496 across 3643 unique clips
- **Ground truth awards available:** 4619

### Per-badge leaderboard (top 10 by volume)

| Badge | TP | FP | FN | Precision | Recall | F1 |
|-------|---:|---:|---:|----------:|-------:|---:|
| Rally Master | 285 | 1482 | 33 | 16% | 90% | 27% |
| Steady Eddie | 323 | 1153 | 50 | 22% | 87% | 35% |
| Kitchen King | 66 | 964 | 0 | 6% | 100% | 12% |
| New Look | 13 | 1 | 158 | 93% | 8% | 14% |
| Net Magnet | 118 | 24 | 23 | 83% | 84% | 83% |
| Epic Rally | 73 | 83 | 4 | 47% | 95% | 63% |
| Dink Machine | 0 | 144 | 0 | 0% | 0% | 0% |
| Fresh Fit | 20 | 0 | 105 | 100% | 16% | 28% |
| Two Up Pressure | 91 | 0 | 29 | 100% | 76% | 86% |
| Consistency King | 0 | 120 | 0 | 0% | 0% | 0% |

## Field Fill Rates (Schema Completeness)

Sampled 500 most-recent analyses.
**2** fields are below 80% population.

| Field | Populated | Rate |
|-------|----------:|-----:|
| analysis_confidence ⚠️ | 0/500 | 0% |
| brand_detection.brands ⚠️ | 398/500 | 80% |
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

- **Total flags captured:** 102
- **Real (non-seed) flags:** 95

Flags by field:
- `badge_predictions` — 88 flag(s)
- `overall_accuracy` — 8 flag(s)
- `dupr_estimate` — 2 flag(s)
- `skill_ratings` — 1 flag(s)
- `signature_move` — 1 flag(s)
- `shot_analysis` — 1 flag(s)
- `coaching_breakdown` — 1 flag(s)

### Recent flags
- `_systemic_Ra...` · `badge_predictions` rating 2 · OVER-PREDICTED: 'Rally Master' has 16% precision — 1459 false positives out of 1
- `_systemic_St...` · `badge_predictions` rating 2 · OVER-PREDICTED: 'Steady Eddie' has 22% precision — 1132 false positives out of 1
- `_systemic_Ki...` · `badge_predictions` rating 2 · OVER-PREDICTED: 'Kitchen King' has 6% precision — 952 false positives out of 101
- `_systemic_Ne...` · `badge_predictions` rating 2 · UNDER-DETECTED: 'New Look' was awarded by Courtana 171 times but the model only 
- `_systemic_Fr...` · `badge_predictions` rating 2 · UNDER-DETECTED: 'Fresh Fit' was awarded by Courtana 125 times but the model only

---

_Run `python3 tools/accuracy-report.py` to regenerate._
_Source: `tools/badge-warehouse.py` + `output/coaching-feedback.db` + analysis files._
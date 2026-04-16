# Pickle DaaS — Accuracy Report
_Generated: 2026-04-16T12:53:17.518667+00:00_

## Summary

- **Corpus on gh-pages:** 3753 clips
- **Total analysis files on disk:** 5276 (5276 ≥500 bytes)
- **Minutes since last analysis:** 0.2
- **Human flags:** 92 total (85 real, rest seed)

## Badge Accuracy (vs. Courtana Ground Truth)

- **Precision:** 28.8%  (1652 TP / 5740 predicted)
- **Recall:**    69.6%  (1652 TP / 2372 awarded)
- **F1 Score:**  40.7%
- **Predictions analyzed:** 10210 across 3532 unique clips
- **Ground truth awards available:** 4619

### Per-badge leaderboard (top 10 by volume)

| Badge | TP | FP | FN | Precision | Recall | F1 |
|-------|---:|---:|---:|----------:|-------:|---:|
| Rally Master | 273 | 1415 | 33 | 16% | 89% | 27% |
| Steady Eddie | 313 | 1100 | 50 | 22% | 86% | 35% |
| Kitchen King | 65 | 926 | 0 | 7% | 100% | 12% |
| New Look | 12 | 1 | 155 | 92% | 7% | 13% |
| Net Magnet | 114 | 24 | 21 | 83% | 84% | 84% |
| Epic Rally | 72 | 83 | 3 | 46% | 96% | 63% |
| Dink Machine | 0 | 144 | 0 | 0% | 0% | 0% |
| Fresh Fit | 18 | 0 | 103 | 100% | 15% | 26% |
| Two Up Pressure | 91 | 0 | 29 | 100% | 76% | 86% |
| Consistency King | 0 | 120 | 0 | 0% | 0% | 0% |

## Field Fill Rates (Schema Completeness)

Sampled 500 most-recent analyses.
**2** fields are below 80% population.

| Field | Populated | Rate |
|-------|----------:|-----:|
| analysis_confidence ⚠️ | 0/500 | 0% |
| brand_detection.brands ⚠️ | 385/500 | 77% |
| badge_intelligence.predicted_badges | 488/500 | 98% |
| clip_meta.clip_quality_score | 500/500 | 100% |
| clip_meta.viral_potential_score | 500/500 | 100% |
| clip_meta.watchability_score | 500/500 | 100% |
| skill_indicators.kitchen_mastery_rating | 500/500 | 100% |
| commentary.neutral_announcer_espn | 500/500 | 100% |
| storytelling.story_arc | 500/500 | 100% |
| daas_signals.clip_summary_one_sentence | 500/500 | 100% |
| daas_signals.data_richness_score | 500/500 | 100% |

## Human Feedback

- **Total flags captured:** 92
- **Real (non-seed) flags:** 85

Flags by field:
- `badge_predictions` — 79 flag(s)
- `overall_accuracy` — 7 flag(s)
- `dupr_estimate` — 2 flag(s)
- `skill_ratings` — 1 flag(s)
- `signature_move` — 1 flag(s)
- `shot_analysis` — 1 flag(s)
- `coaching_breakdown` — 1 flag(s)

### Recent flags
- `_systemic_Ra...` · `badge_predictions` rating 2 · OVER-PREDICTED: 'Rally Master' has 16% precision — 1415 false positives out of 1
- `_systemic_St...` · `badge_predictions` rating 2 · OVER-PREDICTED: 'Steady Eddie' has 22% precision — 1100 false positives out of 1
- `_systemic_Ki...` · `badge_predictions` rating 2 · OVER-PREDICTED: 'Kitchen King' has 7% precision — 926 false positives out of 991
- `_systemic_Ne...` · `badge_predictions` rating 2 · UNDER-DETECTED: 'New Look' was awarded by Courtana 167 times but the model only 
- `_systemic_Di...` · `badge_predictions` rating 1 · HALLUCINATED BADGE: 'Dink Machine' was predicted 144 times but Courtana never aw

---

_Run `python3 tools/accuracy-report.py` to regenerate._
_Source: `tools/badge-warehouse.py` + `output/coaching-feedback.db` + analysis files._
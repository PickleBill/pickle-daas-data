# Pickle DaaS — Accuracy Report
_Generated: 2026-04-16T12:38:21.520688+00:00_

## Summary

- **Corpus on gh-pages:** 3745 clips
- **Total analysis files on disk:** 5261 (5261 ≥500 bytes)
- **Minutes since last analysis:** 0.0
- **Human flags:** 79 total (72 real, rest seed)

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
| brand_detection.brands ⚠️ | 392/500 | 78% |
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

- **Total flags captured:** 79
- **Real (non-seed) flags:** 72

Flags by field:
- `badge_predictions` — 67 flag(s)
- `overall_accuracy` — 6 flag(s)
- `dupr_estimate` — 2 flag(s)
- `skill_ratings` — 1 flag(s)
- `signature_move` — 1 flag(s)
- `shot_analysis` — 1 flag(s)
- `coaching_breakdown` — 1 flag(s)

### Recent flags
- `_systemic_Ra...` · `badge_predictions` rating 2 · OVER-PREDICTED: 'Rally Master' has 17% precision — 1260 false positives out of 1
- `_systemic_St...` · `badge_predictions` rating 2 · OVER-PREDICTED: 'Steady Eddie' has 23% precision — 984 false positives out of 12
- `_systemic_Ki...` · `badge_predictions` rating 2 · OVER-PREDICTED: 'Kitchen King' has 7% precision — 828 false positives out of 890
- `005fc717-736...` · `badge_predictions` rating 1 · Example clips where 'Rally Master' was wrongly predicted: 005fc717-736, 0065b84d
- `005fc717-736...` · `badge_predictions` rating 1 · Example clips where 'Steady Eddie' was wrongly predicted: 005fc717-736, 0065b84d

---

_Run `python3 tools/accuracy-report.py` to regenerate._
_Source: `tools/badge-warehouse.py` + `output/coaching-feedback.db` + analysis files._
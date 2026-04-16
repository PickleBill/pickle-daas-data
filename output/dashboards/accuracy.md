# Pickle DaaS — Accuracy Report
_Generated: 2026-04-16T11:09:25.841650+00:00_

## Summary

- **Corpus on gh-pages:** 3655 clips
- **Total analysis files on disk:** 5160 (5160 ≥500 bytes)
- **Minutes since last analysis:** 30.8
- **Human flags:** 79 total (72 real, rest seed)

## Badge Accuracy (vs. Courtana Ground Truth)

- **Precision:** 29.6%  (1561 TP / 5271 predicted)
- **Recall:**    69.2%  (1561 TP / 2255 awarded)
- **F1 Score:**  41.5%
- **Predictions analyzed:** 9442 across 3229 unique clips
- **Ground truth awards available:** 4619

### Per-badge leaderboard (top 10 by volume)

| Badge | TP | FP | FN | Precision | Recall | F1 |
|-------|---:|---:|---:|----------:|-------:|---:|
| Rally Master | 262 | 1260 | 33 | 17% | 89% | 29% |
| Steady Eddie | 296 | 984 | 50 | 23% | 86% | 36% |
| Kitchen King | 62 | 828 | 0 | 7% | 100% | 13% |
| New Look | 10 | 1 | 151 | 91% | 6% | 12% |
| Epic Rally | 71 | 83 | 3 | 46% | 96% | 62% |
| Net Magnet | 101 | 22 | 21 | 82% | 83% | 82% |
| Dink Machine | 0 | 143 | 0 | 0% | 0% | 0% |
| Consistency King | 0 | 120 | 0 | 0% | 0% | 0% |
| Two Up Pressure | 90 | 0 | 29 | 100% | 76% | 86% |
| Fresh Fit | 15 | 0 | 100 | 100% | 13% | 23% |

## Field Fill Rates (Schema Completeness)

Sampled 500 most-recent analyses.
**2** fields are below 80% population.

| Field | Populated | Rate |
|-------|----------:|-----:|
| analysis_confidence ⚠️ | 0/500 | 0% |
| brand_detection.brands ⚠️ | 398/500 | 80% |
| badge_intelligence.predicted_badges | 489/500 | 98% |
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
# Pickle DaaS — Accuracy Report
_Generated: 2026-04-16T03:53:16.253509+00:00_

## Summary

- **Corpus on gh-pages:** 3389 clips
- **Total analysis files on disk:** 4907 (4907 ≥500 bytes)
- **Minutes since last analysis:** 7.2
- **Human flags:** 71 total (64 real, rest seed)

## Badge Accuracy (vs. Courtana Ground Truth)

- **Precision:** 30.7%  (1561 TP / 5088 predicted)
- **Recall:**    69.2%  (1561 TP / 2255 awarded)
- **F1 Score:**  42.5%
- **Predictions analyzed:** 9089 across 3083 unique clips
- **Ground truth awards available:** 4619

### Per-badge leaderboard (top 10 by volume)

| Badge | TP | FP | FN | Precision | Recall | F1 |
|-------|---:|---:|---:|----------:|-------:|---:|
| Rally Master | 262 | 1184 | 33 | 18% | 89% | 30% |
| Steady Eddie | 296 | 922 | 50 | 24% | 86% | 38% |
| Kitchen King | 62 | 787 | 0 | 7% | 100% | 14% |
| New Look | 10 | 1 | 151 | 91% | 6% | 12% |
| Epic Rally | 71 | 83 | 3 | 46% | 96% | 62% |
| Dink Machine | 0 | 143 | 0 | 0% | 0% | 0% |
| Net Magnet | 101 | 20 | 21 | 84% | 83% | 83% |
| Consistency King | 0 | 120 | 0 | 0% | 0% | 0% |
| Two Up Pressure | 90 | 0 | 29 | 100% | 76% | 86% |
| Fresh Fit | 15 | 0 | 100 | 100% | 13% | 23% |

## Field Fill Rates (Schema Completeness)

Sampled 500 most-recent analyses.
**2** fields are below 80% population.

| Field | Populated | Rate |
|-------|----------:|-----:|
| analysis_confidence ⚠️ | 0/500 | 0% |
| brand_detection.brands ⚠️ | 396/500 | 79% |
| badge_intelligence.predicted_badges | 490/500 | 98% |
| clip_meta.clip_quality_score | 500/500 | 100% |
| clip_meta.viral_potential_score | 500/500 | 100% |
| clip_meta.watchability_score | 500/500 | 100% |
| skill_indicators.kitchen_mastery_rating | 500/500 | 100% |
| commentary.neutral_announcer_espn | 500/500 | 100% |
| storytelling.story_arc | 500/500 | 100% |
| daas_signals.clip_summary_one_sentence | 500/500 | 100% |
| daas_signals.data_richness_score | 500/500 | 100% |

## Human Feedback

- **Total flags captured:** 71
- **Real (non-seed) flags:** 64

Flags by field:
- `badge_predictions` — 60 flag(s)
- `overall_accuracy` — 5 flag(s)
- `dupr_estimate` — 2 flag(s)
- `skill_ratings` — 1 flag(s)
- `signature_move` — 1 flag(s)
- `shot_analysis` — 1 flag(s)
- `coaching_breakdown` — 1 flag(s)

### Recent flags
- `_systemic_Ra...` · `badge_predictions` rating 2 · OVER-PREDICTED: 'Rally Master' has 18% precision — 1184 false positives out of 1
- `_systemic_St...` · `badge_predictions` rating 2 · OVER-PREDICTED: 'Steady Eddie' has 24% precision — 922 false positives out of 12
- `_systemic_Ki...` · `badge_predictions` rating 2 · OVER-PREDICTED: 'Kitchen King' has 7% precision — 787 false positives out of 849
- `005fc717-736...` · `badge_predictions` rating 1 · Example clips where 'Rally Master' was wrongly predicted: 005fc717-736, 0065b84d
- `005fc717-736...` · `badge_predictions` rating 1 · Example clips where 'Steady Eddie' was wrongly predicted: 005fc717-736, 0065b84d

---

_Run `python3 tools/accuracy-report.py` to regenerate._
_Source: `tools/badge-warehouse.py` + `output/coaching-feedback.db` + analysis files._
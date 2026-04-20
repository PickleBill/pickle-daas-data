# Pickle DaaS — Accuracy Report
_Generated: 2026-04-20T07:20:34.921428+00:00_

## Summary

- **Corpus on gh-pages:** 4302 clips
- **Total analysis files on disk:** 5819 (5819 ≥500 bytes)
- **Minutes since last analysis:** 142.8
- **Human flags:** 143 total (136 real, rest seed)

## Badge Accuracy (vs. Courtana Ground Truth)

- **Precision:** 28.1%  (1838 TP / 6532 predicted)
- **Recall:**    70.8%  (1838 TP / 2595 awarded)
- **F1 Score:**  40.3%
- **Predictions analyzed:** 11660 across 4090 unique clips
- **Ground truth awards available:** 4619

### Per-badge leaderboard (top 10 by volume)

| Badge | TP | FP | FN | Precision | Recall | F1 |
|-------|---:|---:|---:|----------:|-------:|---:|
| Rally Master | 306 | 1664 | 33 | 16% | 90% | 26% |
| Steady Eddie | 349 | 1295 | 50 | 21% | 88% | 34% |
| Kitchen King | 70 | 1056 | 0 | 6% | 100% | 12% |
| Net Magnet | 131 | 25 | 25 | 84% | 84% | 84% |
| New Look | 16 | 1 | 160 | 94% | 9% | 17% |
| Epic Rally | 78 | 83 | 4 | 48% | 95% | 64% |
| Dink Machine | 0 | 146 | 0 | 0% | 0% | 0% |
| Fresh Fit | 26 | 0 | 108 | 100% | 19% | 32% |
| Two Up Pressure | 101 | 0 | 30 | 100% | 77% | 87% |
| Speed Up Specialist | 64 | 62 | 2 | 51% | 97% | 67% |

## Field Fill Rates (Schema Completeness)

Sampled 500 most-recent analyses.
**1** fields are below 80% population.

| Field | Populated | Rate |
|-------|----------:|-----:|
| analysis_confidence ⚠️ | 0/500 | 0% |
| brand_detection.brands | 424/500 | 85% |
| badge_intelligence.predicted_badges | 474/500 | 95% |
| skill_indicators.kitchen_mastery_rating | 499/500 | 100% |
| commentary.neutral_announcer_espn | 499/500 | 100% |
| storytelling.story_arc | 499/500 | 100% |
| daas_signals.clip_summary_one_sentence | 499/500 | 100% |
| daas_signals.data_richness_score | 499/500 | 100% |
| clip_meta.clip_quality_score | 500/500 | 100% |
| clip_meta.viral_potential_score | 500/500 | 100% |
| clip_meta.watchability_score | 500/500 | 100% |

## Human Feedback

- **Total flags captured:** 143
- **Real (non-seed) flags:** 136

Flags by field:
- `badge_predictions` — 125 flag(s)
- `overall_accuracy` — 12 flag(s)
- `dupr_estimate` — 2 flag(s)
- `skill_ratings` — 1 flag(s)
- `signature_move` — 1 flag(s)
- `shot_analysis` — 1 flag(s)
- `coaching_breakdown` — 1 flag(s)

### Recent flags
- `_systemic_Ra...` · `badge_predictions` rating 2 · OVER-PREDICTED: 'Rally Master' has 16% precision — 1664 false positives out of 1
- `_systemic_St...` · `badge_predictions` rating 2 · OVER-PREDICTED: 'Steady Eddie' has 21% precision — 1295 false positives out of 1
- `_systemic_Ki...` · `badge_predictions` rating 2 · OVER-PREDICTED: 'Kitchen King' has 6% precision — 1056 false positives out of 11
- `_systemic_Di...` · `badge_predictions` rating 1 · HALLUCINATED BADGE: 'Dink Machine' was predicted 146 times but Courtana never aw
- `005fc717-736...` · `badge_predictions` rating 1 · Example clips where 'Rally Master' was wrongly predicted: 005fc717-736, 0065b84d

---

_Run `python3 tools/accuracy-report.py` to regenerate._
_Source: `tools/badge-warehouse.py` + `output/coaching-feedback.db` + analysis files._
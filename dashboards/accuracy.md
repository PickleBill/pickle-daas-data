# Pickle DaaS — Accuracy Report
_Generated: 2026-04-19T18:52:42.682545+00:00_

## Summary

- **Corpus on gh-pages:** 4283 clips
- **Total analysis files on disk:** 5811 (5811 ≥500 bytes)
- **Minutes since last analysis:** 91.1
- **Human flags:** 132 total (125 real, rest seed)

## Badge Accuracy (vs. Courtana Ground Truth)

- **Precision:** 28.9%  (1838 TP / 6361 predicted)
- **Recall:**    70.8%  (1838 TP / 2595 awarded)
- **F1 Score:**  41.0%
- **Predictions analyzed:** 11302 across 3944 unique clips
- **Ground truth awards available:** 4619

### Per-badge leaderboard (top 10 by volume)

| Badge | TP | FP | FN | Precision | Recall | F1 |
|-------|---:|---:|---:|----------:|-------:|---:|
| Rally Master | 306 | 1595 | 33 | 16% | 90% | 27% |
| Steady Eddie | 349 | 1238 | 50 | 22% | 88% | 35% |
| Kitchen King | 70 | 1030 | 0 | 6% | 100% | 12% |
| Net Magnet | 131 | 24 | 25 | 84% | 84% | 84% |
| New Look | 16 | 1 | 160 | 94% | 9% | 17% |
| Epic Rally | 78 | 83 | 4 | 48% | 95% | 64% |
| Dink Machine | 0 | 145 | 0 | 0% | 0% | 0% |
| Fresh Fit | 26 | 0 | 108 | 100% | 19% | 32% |
| Two Up Pressure | 101 | 0 | 30 | 100% | 77% | 87% |
| Speed Up Specialist | 64 | 58 | 2 | 52% | 97% | 68% |

## Field Fill Rates (Schema Completeness)

Sampled 500 most-recent analyses.
**1** fields are below 80% population.

| Field | Populated | Rate |
|-------|----------:|-----:|
| analysis_confidence ⚠️ | 0/500 | 0% |
| brand_detection.brands | 426/500 | 85% |
| badge_intelligence.predicted_badges | 475/500 | 95% |
| skill_indicators.kitchen_mastery_rating | 499/500 | 100% |
| commentary.neutral_announcer_espn | 499/500 | 100% |
| storytelling.story_arc | 499/500 | 100% |
| daas_signals.clip_summary_one_sentence | 499/500 | 100% |
| daas_signals.data_richness_score | 499/500 | 100% |
| clip_meta.clip_quality_score | 500/500 | 100% |
| clip_meta.viral_potential_score | 500/500 | 100% |
| clip_meta.watchability_score | 500/500 | 100% |

## Human Feedback

- **Total flags captured:** 132
- **Real (non-seed) flags:** 125

Flags by field:
- `badge_predictions` — 115 flag(s)
- `overall_accuracy` — 11 flag(s)
- `dupr_estimate` — 2 flag(s)
- `skill_ratings` — 1 flag(s)
- `signature_move` — 1 flag(s)
- `shot_analysis` — 1 flag(s)
- `coaching_breakdown` — 1 flag(s)

### Recent flags
- `_systemic_Ra...` · `badge_predictions` rating 2 · OVER-PREDICTED: 'Rally Master' has 16% precision — 1595 false positives out of 1
- `_systemic_St...` · `badge_predictions` rating 2 · OVER-PREDICTED: 'Steady Eddie' has 22% precision — 1238 false positives out of 1
- `_systemic_Ki...` · `badge_predictions` rating 2 · OVER-PREDICTED: 'Kitchen King' has 6% precision — 1030 false positives out of 11
- `_systemic_Ne...` · `badge_predictions` rating 2 · UNDER-DETECTED: 'New Look' was awarded by Courtana 176 times but the model only 
- `_systemic_Di...` · `badge_predictions` rating 1 · HALLUCINATED BADGE: 'Dink Machine' was predicted 145 times but Courtana never aw

---

_Run `python3 tools/accuracy-report.py` to regenerate._
_Source: `tools/badge-warehouse.py` + `output/coaching-feedback.db` + analysis files._
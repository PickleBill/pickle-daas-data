# Pickle DaaS — Accuracy Report
_Generated: 2026-04-15T23:39:55.772903+00:00_

## Summary

- **Corpus on gh-pages:** 3135 clips
- **Total analysis files on disk:** 4705 (4705 ≥500 bytes)
- **Minutes since last analysis:** 2.2
- **Human flags:** 62 total (55 real, rest seed)

## Badge Accuracy (vs. Courtana Ground Truth)

- **Precision:** 31.8%  (1560 TP / 4913 predicted)
- **Recall:**    69.2%  (1560 TP / 2254 awarded)
- **F1 Score:**  43.5%
- **Predictions analyzed:** 8743 across 2956 unique clips
- **Ground truth awards available:** 4619

### Per-badge leaderboard (top 10 by volume)

| Badge | TP | FP | FN | Precision | Recall | F1 |
|-------|---:|---:|---:|----------:|-------:|---:|
| Rally Master | 262 | 1115 | 33 | 19% | 89% | 31% |
| Steady Eddie | 296 | 863 | 50 | 26% | 86% | 39% |
| Kitchen King | 62 | 749 | 0 | 8% | 100% | 14% |
| New Look | 10 | 1 | 151 | 91% | 6% | 12% |
| Epic Rally | 71 | 83 | 3 | 46% | 96% | 62% |
| Dink Machine | 0 | 143 | 0 | 0% | 0% | 0% |
| Net Magnet | 101 | 18 | 21 | 85% | 83% | 84% |
| Consistency King | 0 | 120 | 0 | 0% | 0% | 0% |
| Two Up Pressure | 90 | 0 | 29 | 100% | 76% | 86% |
| Fresh Fit | 15 | 0 | 100 | 100% | 13% | 23% |

## Field Fill Rates (Schema Completeness)

Sampled 500 most-recent analyses.
**2** fields are below 80% population.

| Field | Populated | Rate |
|-------|----------:|-----:|
| analysis_confidence ⚠️ | 0/500 | 0% |
| brand_detection.brands ⚠️ | 397/500 | 79% |
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

- **Total flags captured:** 62
- **Real (non-seed) flags:** 55

Flags by field:
- `badge_predictions` — 52 flag(s)
- `overall_accuracy` — 4 flag(s)
- `dupr_estimate` — 2 flag(s)
- `skill_ratings` — 1 flag(s)
- `signature_move` — 1 flag(s)
- `shot_analysis` — 1 flag(s)
- `coaching_breakdown` — 1 flag(s)

### Recent flags
- `_systemic_Ra...` · `badge_predictions` rating 2 · OVER-PREDICTED: 'Rally Master' has 19% precision — 1115 false positives out of 1
- `_systemic_St...` · `badge_predictions` rating 2 · OVER-PREDICTED: 'Steady Eddie' has 26% precision — 863 false positives out of 11
- `_systemic_Ki...` · `badge_predictions` rating 2 · OVER-PREDICTED: 'Kitchen King' has 8% precision — 749 false positives out of 811
- `_systemic_Ne...` · `badge_predictions` rating 2 · UNDER-DETECTED: 'New Look' was awarded by Courtana 161 times but the model only 
- `_systemic_Fr...` · `badge_predictions` rating 2 · UNDER-DETECTED: 'Fresh Fit' was awarded by Courtana 115 times but the model only

---

_Run `python3 tools/accuracy-report.py` to regenerate._
_Source: `tools/badge-warehouse.py` + `output/coaching-feedback.db` + analysis files._
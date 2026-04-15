# Pickle DaaS — Accuracy Report
_Generated: 2026-04-15T22:30:51.194197+00:00_

## Summary

- **Corpus on gh-pages:** 3131 clips
- **Total analysis files on disk:** 4640 (4640 ≥500 bytes)
- **Minutes since last analysis:** 30.6
- **Human flags:** 51 total (44 real, rest seed)

## Badge Accuracy (vs. Courtana Ground Truth)

- **Precision:** 29.8%  (1386 TP / 4648 predicted)
- **Recall:**    68.6%  (1386 TP / 2019 awarded)
- **F1 Score:**  41.6%
- **Predictions analyzed:** 8408 across 2857 unique clips
- **Ground truth awards available:** 4619

### Per-badge leaderboard (top 10 by volume)

| Badge | TP | FP | FN | Precision | Recall | F1 |
|-------|---:|---:|---:|----------:|-------:|---:|
| Rally Master | 235 | 1076 | 33 | 18% | 88% | 30% |
| Steady Eddie | 256 | 836 | 49 | 23% | 84% | 37% |
| Kitchen King | 59 | 729 | 0 | 8% | 100% | 14% |
| Epic Rally | 68 | 83 | 3 | 45% | 96% | 61% |
| New Look | 9 | 1 | 133 | 90% | 6% | 12% |
| Dink Machine | 0 | 143 | 0 | 0% | 0% | 0% |
| Net Magnet | 87 | 18 | 17 | 83% | 84% | 83% |
| Consistency King | 0 | 120 | 0 | 0% | 0% | 0% |
| Two Up Pressure | 78 | 0 | 29 | 100% | 73% | 84% |
| Fresh Fit | 15 | 0 | 91 | 100% | 14% | 25% |

## Field Fill Rates (Schema Completeness)

Sampled 500 most-recent analyses.
**1** fields are below 80% population.

| Field | Populated | Rate |
|-------|----------:|-----:|
| analysis_confidence ⚠️ | 0/500 | 0% |
| brand_detection.brands | 400/500 | 80% |
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

- **Total flags captured:** 51
- **Real (non-seed) flags:** 44

Flags by field:
- `badge_predictions` — 42 flag(s)
- `overall_accuracy` — 3 flag(s)
- `dupr_estimate` — 2 flag(s)
- `skill_ratings` — 1 flag(s)
- `signature_move` — 1 flag(s)
- `shot_analysis` — 1 flag(s)
- `coaching_breakdown` — 1 flag(s)

### Recent flags
- `_systemic_Ra...` · `badge_predictions` rating 2 · OVER-PREDICTED: 'Rally Master' has 18% precision — 1076 false positives out of 1
- `_systemic_St...` · `badge_predictions` rating 2 · OVER-PREDICTED: 'Steady Eddie' has 23% precision — 836 false positives out of 10
- `_systemic_Ki...` · `badge_predictions` rating 2 · OVER-PREDICTED: 'Kitchen King' has 8% precision — 729 false positives out of 788
- `_systemic_Ne...` · `badge_predictions` rating 2 · UNDER-DETECTED: 'New Look' was awarded by Courtana 142 times but the model only 
- `_systemic_Di...` · `badge_predictions` rating 1 · HALLUCINATED BADGE: 'Dink Machine' was predicted 143 times but Courtana never aw

---

_Run `python3 tools/accuracy-report.py` to regenerate._
_Source: `tools/badge-warehouse.py` + `output/coaching-feedback.db` + analysis files._
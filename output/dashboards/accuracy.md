# Pickle DaaS — Accuracy Report
_Generated: 2026-04-15T14:30:59.154583+00:00_

## Summary

- **Corpus on gh-pages:** 2764 clips
- **Total analysis files on disk:** 4586 (4586 ≥500 bytes)
- **Minutes since last analysis:** 200.6
- **Human flags:** 37 total (30 real, rest seed)

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
| brand_detection.brands | 402/500 | 80% |
| badge_intelligence.predicted_badges | 491/500 | 98% |
| clip_meta.clip_quality_score | 500/500 | 100% |
| clip_meta.viral_potential_score | 500/500 | 100% |
| clip_meta.watchability_score | 500/500 | 100% |
| skill_indicators.kitchen_mastery_rating | 500/500 | 100% |
| commentary.neutral_announcer_espn | 500/500 | 100% |
| storytelling.story_arc | 500/500 | 100% |
| daas_signals.clip_summary_one_sentence | 500/500 | 100% |
| daas_signals.data_richness_score | 500/500 | 100% |

## Human Feedback

- **Total flags captured:** 37
- **Real (non-seed) flags:** 30

Flags by field:
- `badge_predictions` — 29 flag(s)
- `overall_accuracy` — 2 flag(s)
- `dupr_estimate` — 2 flag(s)
- `skill_ratings` — 1 flag(s)
- `signature_move` — 1 flag(s)
- `shot_analysis` — 1 flag(s)
- `coaching_breakdown` — 1 flag(s)

### Recent flags
- `_systemic_Ki...` · `badge_predictions` rating 2 · OVER-PREDICTED: 'Kitchen King' has 13% precision — 285 false positives out of 32
- `_systemic_Di...` · `badge_predictions` rating 1 · HALLUCINATED BADGE: 'Dink Machine' was predicted 141 times but Courtana never aw
- `_systemic_Ne...` · `badge_predictions` rating 2 · UNDER-DETECTED: 'New Look' was awarded by Courtana 97 times but the model only c
- `_systemic_Fr...` · `badge_predictions` rating 2 · UNDER-DETECTED: 'Fresh Fit' was awarded by Courtana 64 times but the model only 
- `_systemic_Le...` · `badge_predictions` rating 2 · UNDER-DETECTED: 'Legendary Look' was awarded by Courtana 20 times but the model 

---

_Run `python3 tools/accuracy-report.py` to regenerate._
_Source: `tools/badge-warehouse.py` + `output/coaching-feedback.db` + analysis files._
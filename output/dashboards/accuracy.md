# Pickle DaaS — Accuracy Report
_Generated: 2026-04-15T03:19:22.654572+00:00_

## Summary

- **Corpus on gh-pages:** 1136 clips
- **Total analysis files on disk:** 1922 (1922 ≥500 bytes)
- **Minutes since last analysis:** 0.0
- **Human flags:** 27 total (20 real, rest seed)

## Badge Accuracy (vs. Courtana Ground Truth)

- **Precision:** 38.1%  (587 TP / 1539 predicted)
- **Recall:**    57.9%  (587 TP / 1014 awarded)
- **F1 Score:**  46.0%
- **Predictions analyzed:** 3453 across 1002 unique clips
- **Ground truth awards available:** 4619

### Per-badge leaderboard (top 10 by volume)

| Badge | TP | FP | FN | Precision | Recall | F1 |
|-------|---:|---:|---:|----------:|-------:|---:|
| Rally Master | 125 | 131 | 33 | 49% | 79% | 60% |
| Steady Eddie | 118 | 106 | 49 | 53% | 71% | 60% |
| Kitchen King | 39 | 199 | 0 | 16% | 100% | 28% |
| Epic Rally | 56 | 83 | 1 | 40% | 98% | 57% |
| Dink Machine | 0 | 140 | 0 | 0% | 0% | 0% |
| Consistency King | 0 | 120 | 0 | 0% | 0% | 0% |
| New Look | 0 | 0 | 86 | 0% | 0% | 0% |
| Two Up Pressure | 30 | 0 | 26 | 100% | 54% | 70% |
| Fresh Fit | 2 | 0 | 52 | 100% | 4% | 7% |
| Power Player | 0 | 53 | 0 | 0% | 0% | 0% |

## Field Fill Rates (Schema Completeness)

Sampled 500 most-recent analyses.
**1** fields are below 80% population.

| Field | Populated | Rate |
|-------|----------:|-----:|
| analysis_confidence ⚠️ | 124/500 | 25% |
| brand_detection.brands | 428/500 | 86% |
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

- **Total flags captured:** 27
- **Real (non-seed) flags:** 20

Flags by field:
- `badge_predictions` — 20 flag(s)
- `dupr_estimate` — 2 flag(s)
- `skill_ratings` — 1 flag(s)
- `signature_move` — 1 flag(s)
- `shot_analysis` — 1 flag(s)
- `overall_accuracy` — 1 flag(s)
- `coaching_breakdown` — 1 flag(s)

### Recent flags
- `00e08290-213...` · `badge_predictions` rating 1 · Example clips where 'Dink Machine' was wrongly predicted: 00e08290-213, 01fc4a04
- `0065b84d-baf...` · `badge_predictions` rating 1 · Example clips where 'Kitchen King' was wrongly predicted: 0065b84d-baf, 01fc4a04
- `00e08290-213...` · `badge_predictions` rating 1 · Example clips where 'Consistency King' was wrongly predicted: 00e08290-213, 058c
- `04214439-631...` · `badge_predictions` rating 1 · Example clips where 'Epic Rally' was wrongly predicted: 04214439-631, 06d5a65e-5
- `0026ad09-194...` · `badge_predictions` rating 1 · Example clips where 'Power Player' was wrongly predicted: 0026ad09-194, 04214439

---

_Run `python3 tools/accuracy-report.py` to regenerate._
_Source: `tools/badge-warehouse.py` + `output/coaching-feedback.db` + analysis files._
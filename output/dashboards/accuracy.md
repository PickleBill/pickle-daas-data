# Pickle DaaS — Accuracy Report
_Generated: 2026-04-15T06:12:09.190173+00:00_

## Summary

- **Corpus on gh-pages:** 1928 clips
- **Total analysis files on disk:** 3028 (3028 ≥500 bytes)
- **Minutes since last analysis:** 0.1
- **Human flags:** 27 total (20 real, rest seed)

## Badge Accuracy (vs. Courtana Ground Truth)

- **Precision:** 34.2%  (714 TP / 2088 predicted)
- **Recall:**    59.8%  (714 TP / 1193 awarded)
- **F1 Score:**  43.5%
- **Predictions analyzed:** 4434 across 1390 unique clips
- **Ground truth awards available:** 4619

### Per-badge leaderboard (top 10 by volume)

| Badge | TP | FP | FN | Precision | Recall | F1 |
|-------|---:|---:|---:|----------:|-------:|---:|
| Rally Master | 142 | 311 | 33 | 31% | 81% | 45% |
| Steady Eddie | 133 | 251 | 49 | 35% | 73% | 47% |
| Kitchen King | 43 | 285 | 0 | 13% | 100% | 23% |
| Epic Rally | 59 | 83 | 2 | 42% | 97% | 58% |
| Dink Machine | 0 | 141 | 0 | 0% | 0% | 0% |
| Consistency King | 0 | 120 | 0 | 0% | 0% | 0% |
| New Look | 1 | 0 | 96 | 100% | 1% | 2% |
| Net Magnet | 52 | 5 | 15 | 91% | 78% | 84% |
| Two Up Pressure | 37 | 0 | 28 | 100% | 57% | 72% |
| Fresh Fit | 2 | 0 | 62 | 100% | 3% | 6% |

## Field Fill Rates (Schema Completeness)

Sampled 500 most-recent analyses.
**1** fields are below 80% population.

| Field | Populated | Rate |
|-------|----------:|-----:|
| analysis_confidence ⚠️ | 0/500 | 0% |
| brand_detection.brands | 446/500 | 89% |
| badge_intelligence.predicted_badges | 469/500 | 94% |
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
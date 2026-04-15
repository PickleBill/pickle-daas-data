# Pickle DaaS — Accuracy Report
_Generated: 2026-04-15T06:49:16.307187+00:00_

## Summary

- **Corpus on gh-pages:** 2014 clips
- **Total analysis files on disk:** 3082 (3082 ≥500 bytes)
- **Minutes since last analysis:** 0.1
- **Human flags:** 37 total (30 real, rest seed)

## Badge Accuracy (vs. Courtana Ground Truth)

- **Precision:** 27.3%  (780 TP / 2861 predicted)
- **Recall:**    61.0%  (780 TP / 1279 awarded)
- **F1 Score:**  37.7%
- **Predictions analyzed:** 5623 across 1864 unique clips
- **Ground truth awards available:** 4619

### Per-badge leaderboard (top 10 by volume)

| Badge | TP | FP | FN | Precision | Recall | F1 |
|-------|---:|---:|---:|----------:|-------:|---:|
| Rally Master | 155 | 596 | 33 | 21% | 82% | 33% |
| Steady Eddie | 139 | 482 | 49 | 22% | 74% | 34% |
| Kitchen King | 48 | 452 | 0 | 10% | 100% | 18% |
| Epic Rally | 59 | 83 | 2 | 42% | 97% | 58% |
| Dink Machine | 0 | 142 | 0 | 0% | 0% | 0% |
| Consistency King | 0 | 120 | 0 | 0% | 0% | 0% |
| New Look | 1 | 0 | 97 | 100% | 1% | 2% |
| Net Magnet | 53 | 8 | 15 | 87% | 78% | 82% |
| Two Up Pressure | 45 | 0 | 29 | 100% | 61% | 76% |
| Fresh Fit | 2 | 0 | 62 | 100% | 3% | 6% |

## Field Fill Rates (Schema Completeness)

Sampled 500 most-recent analyses.
**1** fields are below 80% population.

| Field | Populated | Rate |
|-------|----------:|-----:|
| analysis_confidence ⚠️ | 0/500 | 0% |
| brand_detection.brands | 443/500 | 89% |
| badge_intelligence.predicted_badges | 471/500 | 94% |
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
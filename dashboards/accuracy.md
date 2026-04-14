# Pickle DaaS — Accuracy Report
_Generated: 2026-04-14T02:40:41.019647+00:00_

## Summary

- **Corpus on gh-pages:** 719 clips
- **Total analysis files on disk:** 1438 (1438 ≥500 bytes)
- **Minutes since last analysis:** 0.1
- **Human flags:** 10 total (3 real, rest seed)

## Badge Accuracy (vs. Courtana Ground Truth)

- **Precision:** 43.9%  (523 TP / 1191 predicted)
- **Recall:**    56.2%  (523 TP / 930 awarded)
- **F1 Score:**  49.3%
- **Predictions analyzed:** 2609 across 700 unique clips
- **Ground truth awards available:** 4619

### Per-badge leaderboard (top 10 by volume)

| Badge | TP | FP | FN | Precision | Recall | F1 |
|-------|---:|---:|---:|----------:|-------:|---:|
| Steady Eddie | 110 | 12 | 49 | 90% | 69% | 78% |
| Kitchen King | 36 | 133 | 0 | 21% | 100% | 35% |
| Rally Master | 119 | 11 | 33 | 92% | 78% | 84% |
| Dink Machine | 0 | 140 | 0 | 0% | 0% | 0% |
| Epic Rally | 55 | 83 | 1 | 40% | 98% | 57% |
| Consistency King | 0 | 120 | 0 | 0% | 0% | 0% |
| New Look | 0 | 0 | 86 | 0% | 0% | 0% |
| Power Player | 0 | 53 | 0 | 0% | 0% | 0% |
| Two Up Pressure | 25 | 0 | 26 | 100% | 49% | 66% |
| Fresh Fit | 1 | 0 | 50 | 100% | 2% | 4% |

## Field Fill Rates (Schema Completeness)

Sampled 500 most-recent analyses.
**0** fields are below 80% population.

| Field | Populated | Rate |
|-------|----------:|-----:|
| analysis_confidence | 409/500 | 82% |
| brand_detection.brands | 420/500 | 84% |
| clip_meta.clip_quality_score | 500/500 | 100% |
| clip_meta.viral_potential_score | 500/500 | 100% |
| clip_meta.watchability_score | 500/500 | 100% |
| skill_indicators.kitchen_mastery_rating | 500/500 | 100% |
| commentary.neutral_announcer_espn | 500/500 | 100% |
| storytelling.story_arc | 500/500 | 100% |
| daas_signals.clip_summary_one_sentence | 500/500 | 100% |
| badge_intelligence.predicted_badges | 500/500 | 100% |
| daas_signals.data_richness_score | 500/500 | 100% |

## Human Feedback

- **Total flags captured:** 10
- **Real (non-seed) flags:** 3

Flags by field:
- `dupr_estimate` — 3 flag(s)
- `shot_analysis` — 2 flag(s)
- `badge_predictions` — 2 flag(s)
- `skill_ratings` — 1 flag(s)
- `signature_move` — 1 flag(s)
- `coaching_breakdown` — 1 flag(s)

### Recent flags
- `f9ff7971-2cd...` · `dupr_estimate` rating 1 · Way off - these are clearly 3.0-3.5 level players
- `d647633e-db9...` · `badge_predictions` rating 3 · Some dinks present but badge feels generous - rally was mixed
- `bde93ec5-b67...` · `shot_analysis` rating 5 · Spot on - clean forehand drive, good read
- `139453f3...` · `dupr_estimate` rating 4 · Seems right for this player. Good kitchen fundamentals visible.
- `139453f3...` · `coaching_breakdown` rating 5 · This is accurate and well-observed. The transition timing is exactly right.

---

_Run `python3 tools/accuracy-report.py` to regenerate._
_Source: `tools/badge-warehouse.py` + `output/coaching-feedback.db` + analysis files._
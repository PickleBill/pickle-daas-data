# Pickle DaaS — Accuracy Report
_Generated: 2026-04-14T01:41:28.541567+00:00_

## Summary

- **Corpus on gh-pages:** 715 clips
- **Total analysis files on disk:** 1351 (1351 ≥500 bytes)
- **Minutes since last analysis:** 0.1
- **Human flags:** 10 total (3 real, rest seed)

## Badge Accuracy (vs. Courtana Ground Truth)

- **Precision:** 42.0%  (468 TP / 1113 predicted)
- **Recall:**    54.9%  (468 TP / 852 awarded)
- **F1 Score:**  47.6%
- **Predictions analyzed:** 2296 across 614 unique clips
- **Ground truth awards available:** 4619

### Per-badge leaderboard (top 10 by volume)

| Badge | TP | FP | FN | Precision | Recall | F1 |
|-------|---:|---:|---:|----------:|-------:|---:|
| Kitchen King | 33 | 127 | 0 | 21% | 100% | 34% |
| Steady Eddie | 98 | 7 | 49 | 93% | 67% | 78% |
| Rally Master | 108 | 7 | 33 | 94% | 77% | 84% |
| Dink Machine | 0 | 140 | 0 | 0% | 0% | 0% |
| Epic Rally | 50 | 83 | 1 | 38% | 98% | 54% |
| Consistency King | 0 | 120 | 0 | 0% | 0% | 0% |
| New Look | 0 | 0 | 76 | 0% | 0% | 0% |
| Power Player | 0 | 53 | 0 | 0% | 0% | 0% |
| Two Up Pressure | 24 | 0 | 26 | 100% | 48% | 65% |
| Fresh Fit | 1 | 0 | 46 | 100% | 2% | 4% |

## Field Fill Rates (Schema Completeness)

Sampled 500 most-recent analyses.
**1** fields are below 80% population.

| Field | Populated | Rate |
|-------|----------:|-----:|
| analysis_confidence ⚠️ | 322/500 | 64% |
| brand_detection.brands | 433/500 | 87% |
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
# Pickle DaaS — Accuracy Report
_Generated: 2026-04-13T17:37:28.340756+00:00_

## Summary

- **Corpus on gh-pages:** 492 clips
- **Total analysis files on disk:** 1021 (1021 ≥500 bytes)
- **Minutes since last analysis:** 22.5
- **Human flags:** 7 total (7 real, rest seed)

## Badge Accuracy (vs. Courtana Ground Truth)

- **Precision:** 37.8%  (343 TP / 908 predicted)
- **Recall:**    48.1%  (343 TP / 713 awarded)
- **F1 Score:**  42.3%
- **Predictions analyzed:** 1407 across 385 unique clips
- **Ground truth awards available:** 4619

### Per-badge leaderboard (top 10 by volume)

| Badge | TP | FP | FN | Precision | Recall | F1 |
|-------|---:|---:|---:|----------:|-------:|---:|
| Kitchen King | 30 | 111 | 0 | 21% | 100% | 35% |
| Dink Machine | 0 | 138 | 0 | 0% | 0% | 0% |
| Epic Rally | 41 | 81 | 1 | 34% | 98% | 50% |
| Consistency King | 0 | 119 | 0 | 0% | 0% | 0% |
| Steady Eddie | 62 | 0 | 49 | 100% | 56% | 72% |
| Rally Master | 78 | 0 | 32 | 100% | 71% | 83% |
| New Look | 0 | 0 | 74 | 0% | 0% | 0% |
| Power Player | 0 | 53 | 0 | 0% | 0% | 0% |
| Fresh Fit | 1 | 0 | 42 | 100% | 2% | 4% |
| Two Up Pressure | 16 | 0 | 25 | 100% | 39% | 56% |

## Field Fill Rates (Schema Completeness)

Sampled 455 most-recent analyses.
**1** fields are below 80% population.

| Field | Populated | Rate |
|-------|----------:|-----:|
| analysis_confidence ⚠️ | 0/455 | 0% |
| brand_detection.brands | 418/455 | 92% |
| clip_meta.clip_quality_score | 455/455 | 100% |
| clip_meta.viral_potential_score | 455/455 | 100% |
| clip_meta.watchability_score | 455/455 | 100% |
| skill_indicators.kitchen_mastery_rating | 455/455 | 100% |
| commentary.neutral_announcer_espn | 455/455 | 100% |
| storytelling.story_arc | 455/455 | 100% |
| daas_signals.clip_summary_one_sentence | 455/455 | 100% |
| badge_intelligence.predicted_badges | 455/455 | 100% |
| daas_signals.data_richness_score | 455/455 | 100% |

## Human Feedback

- **Total flags captured:** 7
- **Real (non-seed) flags:** 7

Flags by field:
- `dupr_estimate` — 2 flag(s)
- `skill_ratings` — 1 flag(s)
- `signature_move` — 1 flag(s)
- `shot_analysis` — 1 flag(s)
- `coaching_breakdown` — 1 flag(s)
- `badge_predictions` — 1 flag(s)

### Recent flags
- `139453f3...` · `dupr_estimate` rating 4 · Seems right for this player. Good kitchen fundamentals visible.
- `139453f3...` · `coaching_breakdown` rating 5 · This is accurate and well-observed. The transition timing is exactly right.
- `08932731...` · `dupr_estimate` rating 2 · Too low. The footwork and kitchen positioning suggest at least 3.5-4.0.
- `42520eda...` · `badge_predictions` rating 3 · Kitchen King makes sense but Epic Rally is a stretch for a 6-shot point.
- `6ee49439...` · `shot_analysis` rating 4 · Correct. Heavy dink-based rally with one speed-up.

---

_Run `python3 tools/accuracy-report.py` to regenerate._
_Source: `tools/badge-warehouse.py` + `output/coaching-feedback.db` + analysis files._
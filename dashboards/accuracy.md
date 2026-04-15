# Pickle DaaS — Accuracy Report
_Generated: 2026-04-15T03:12:32.048661+00:00_

## Summary

- **Corpus on gh-pages:** 1100 clips
- **Total analysis files on disk:** 1876 (1876 ≥500 bytes)
- **Minutes since last analysis:** 0.0
- **Human flags:** 7 total (0 real, rest seed)

## Badge Accuracy (vs. Courtana Ground Truth)

- **Precision:** 43.9%  (523 TP / 1191 predicted)
- **Recall:**    56.2%  (523 TP / 930 awarded)
- **F1 Score:**  49.3%
- **Predictions analyzed:** 2742 across 736 unique clips
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
**1** fields are below 80% population.

| Field | Populated | Rate |
|-------|----------:|-----:|
| analysis_confidence ⚠️ | 164/500 | 33% |
| brand_detection.brands | 429/500 | 86% |
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

- **Total flags captured:** 7
- **Real (non-seed) flags:** 0

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
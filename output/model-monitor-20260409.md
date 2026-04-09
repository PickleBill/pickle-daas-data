# Pickle DaaS — Model Quality Monitor
**Generated:** 2026-04-09 05:37
**Batches analyzed:** 3
**Total clips:** 18

---

## ⚠️ Regressions Detected

- **Signature Move ⚡**: batch-30-daas (9%) → picklebill-batch-001 (0%) — dropped 9%
- **Predicted Badges ⚡**: batch-30-daas (73%) → picklebill-batch-001 (67%) — dropped 6%
- **Predicted Badges ⚡**: picklebill-batch-001 (67%) → picklebill-batch-20260410 (50%) — dropped 17%

---

## Field Fill Rates by Batch

| Field | batch-30-daas | picklebill-batch-001 | picklebill-batch-20260410 |
|---|---|---|---|
| Clip Quality Score | ✅ 100% | ✅ 100% | ✅ 100% |
| Viral Potential Score | ✅ 100% | ✅ 100% | ✅ 100% |
| Watchability Score | ✅ 100% | ✅ 100% | ✅ 100% |
| Kitchen Mastery | ✅ 91% | ✅ 100% | ✅ 100% |
| Court IQ | ✅ 91% | ✅ 100% | ✅ 100% |
| Athleticism | ✅ 91% | ✅ 100% | ✅ 100% |
| Signature Move ⚡ | ❌ 9% | ❌ 0% | ❌ 0% |
| Improvement Opps | ✅ 91% | ✅ 100% | ✅ 100% |
| Play Style Tags | ✅ 91% | ✅ 100% | ✅ 100% |
| Predicted Badges ⚡ | ⚠️ 73% | ❌ 67% | ❌ 50% |
| Ron Burgundy Voice ⚡ | ⚠️ 82% | ✅ 100% | ✅ 100% |
| Social Caption | ⚠️ 82% | ✅ 100% | ✅ 100% |
| Coaching Breakdown | ⚠️ 82% | ✅ 100% | ✅ 100% |
| DUPR Estimate ⚡ | ⚠️ 82% | ✅ 100% | ✅ 100% |
| One-Sentence Summary ⚡ | ⚠️ 82% | ✅ 100% | ✅ 100% |
| Data Richness | ⚠️ 82% | ✅ 100% | ✅ 100% |
| Brand Detections | ✅ 91% | ✅ 100% | ✅ 100% |
| Story Arc | ✅ 91% | ✅ 100% | ✅ 100% |
| Narrative Summary | ✅ 91% | ✅ 100% | ✅ 100% |

---

## Quality Metrics by Batch

**batch-30-daas** (11 clips)
- Avg quality: 7.5/10 | Avg viral: 4.5/10
- Avg brands/clip: 1.3 | Avg badges/clip: 1.9
- Most common DUPR estimate: 3.0-3.5 (4 clips)

**picklebill-batch-001** (3 clips)
- Avg quality: 7.0/10 | Avg viral: 4.7/10
- Avg brands/clip: 2.0 | Avg badges/clip: 1.3
- Most common DUPR estimate: 3.0-3.5 (2 clips)

**picklebill-batch-20260410** (4 clips)
- Avg quality: 7.2/10 | Avg viral: 2.8/10
- Avg brands/clip: 2.2 | Avg badges/clip: 0.8
- Most common DUPR estimate: 3.0-3.5 (4 clips)

---

## Recommendations

Fields at <70% fill rate need prompt attention:
- **Signature Move ⚡** in `batch-30-daas`: 9% — add few-shot examples or mark REQUIRED
- **Predicted Badges ⚡** in `picklebill-batch-001`: 67% — add few-shot examples or mark REQUIRED
# Brand Detection: v1.1 vs v1.2 Comparison
**Date:** 2026-04-10 | **Clips tested:** 5 (top quality scores)

## Headline
Raw brand count similar (8 vs 8), but v1.2 dramatically improves detection quality and metadata.

## What v1.2 Added
1. **`prompt_version` field** — every analysis now self-identifies its prompt version
2. **`location_detail` per brand** — "on the net band", "on wall above courts", "on chest of player"
3. **`unidentified_products_notes`** — describes visible but unbranded items (chairs, tables, shoe colors)
4. **Specific whitespace** — v1.1 said "paddle brands"; v1.2 names Selkirk, Nike, Adidas, Gatorade, Life Time
5. **New categories** — `venue_signage`, `drink_bottle`, `wearable_tech`, etc. now available
6. **No false positives** — v1.1 counted "Courtana" watermark as a brand; v1.2 doesn't

## Per-Clip Results

| Clip | Quality | v1.1 Brands | v1.2 Brands | Delta | Notes |
|------|---------|-------------|-------------|-------|-------|
| b18ca113 | 9 | 0 | 0 | → | Both versions: no readable brands. v1.2 notes: "dark paddles, white shoes" |
| 8fe77353 | 8 | 1 (ASICS) | 2 (JOOLA x2) | ↑1 | v1.2 found JOOLA on net + back wall banner. v1.2 location_detail working |
| 2615847e | 8 | 1 (Courtana*) | 1 (PICKLEBALL) | → | *v1.1 false positive (app watermark). v1.2 found venue text on shirt |
| f4df1bb4 | 8 | 4 | 2 | ↓2 | v1.2 more conservative, didn't claim HEAD/Selkirk without clear visibility |
| 8ade4e4e | 8 | 2 (Courtana*x2) | 3 (JOOLA x3) | ↑1 | *v1.1 false positives replaced with real JOOLA detections |

## Key Takeaway
v1.2 is a better prompt even though count is flat — it's more accurate (fewer false positives), more descriptive (location + unidentified notes), and gives actionable whitespace intelligence (specific brand names, not categories).

## Next Step
The real unlock is **frame-level analysis** with v1.2's expanded FRAME_BRAND_PROMPT. Frame-by-frame analysis catches brands that flash for 1-2 seconds in video but are clearly visible in still frames. That's where v1.2's expanded category list will shine.

# Gemini Prompt Version Log

| Version | Date | Key Changes | Clips Tested | Avg Quality | Weaknesses Found |
|---------|------|-------------|-------------|-------------|-----------------|
| v1.0 | 2026-03-28 | Initial prompt — all fields: clip_meta, players_detected, shot_analysis, skill_indicators, brand_detection, storytelling, badge_intelligence, commentary, daas_signals | 0 | TBD | TBD |
| v1.2 | 2026-03-28 | Added paddle_intel sub-object (brand, model, shape, grip, lead tape), added paddle_control_rating + grip_pressure_estimate to skill_indicators | 0 | TBD | TBD |
| **v1.1** | **2026-04-10** | Added REQUIRED FIELDS block at top. Fixed `signature_move_detected` (9%→~95%) — expanded from "recurring move" to "any distinctive characteristic." Fixed `predicted_badges` (73%→~98%) — added full 18-badge taxonomy + always-predict rule. Fixed `estimated_player_rating_dupr` (82%→~99%) — added DUPR scale with default "3.5-4.0". Fixed `ron_burgundy_voice` (82%→~99%) — marked required. | 11 | 7.4/10 | signature_move(9%), badges(73%), dupr(82%), ron_burgundy(82%) |
| **v1.2** | **2026-04-10** | **Expanded brand detection to ALL visible brands.** Added `prompt_version` field to output. Expanded `brand_detection.brands[].category` from 14 to 30+ categories (drinks, vehicles, venue signage, wearable tech, fitness chains, local businesses, etc.). Added `location_detail` field per brand. Added `unidentified_products_notes`. Expanded `sponsorship_whitespace` beyond sports. Updated frame-analyzer `FRAME_BRAND_PROMPT` to match. Explicit instruction: "Report EVERY visible logo, brand name, or identifiable product." | 0 | TBD | TBD — reprocessing top 5 clips for before/after comparison |

| **v1.3** | **2026-04-10** | **Badge criteria injection + brand wildcard.** Replaced soft 18-badge list with full Courtana taxonomy (70+ gameplay badges with exact criteria text). Added system/behavioral/negative badge categories. Badge prediction rules: match Courtana's exact criteria, count shots, verify behaviors. Added `wildcard_observations` field: `unexpected_brands`, `environmental_details`, `lifestyle_signals`, `content_opportunity`, `anomaly_detected`. Added aggressive brand wildcard instruction: "false positives are acceptable — maximize brand capture." Updated frame-analyzer brand prompt to match. | 200 | TBD | Running on 200 badged clips for first precision/recall |

**v1.3 purpose:** Sprint 4 reinforcement loop. Bill's feedback: badges need Courtana's exact criteria, not our soft guesses. Brand wildcard needed for non-pickleball brands. v1.2 analyzed 200 badged clips as baseline, v1.3 will be compared against same clips.

**v1.2 purpose:** Bill's feedback: "Think beyond the obvious — clothing, shoes, what people are drinking, sunglasses, everything." v1.1 only detected pickleball equipment. v1.2 scans entire frame for ANY brand.

## How to Update This Log

1. Run `python evaluate-prompt-quality.py ./output/batch_summary_*.json`
2. Note avg fill rate and weak fields
3. Update `ANALYSIS_PROMPT` in `pickle-daas-gemini-analyzer.py`
4. Copy new prompt to `prompts/v1.X-YYYY-MM-DD.txt`
5. Add row to this table
6. Re-run on same 5 clips and compare outputs

# Gemini Prompt Version Log

| Version | Date | Key Changes | Clips Tested | Avg Quality | Weaknesses Found |
|---------|------|-------------|-------------|-------------|-----------------|
| v1.0 | 2026-03-28 | Initial prompt — all fields: clip_meta, players_detected, shot_analysis, skill_indicators, brand_detection, storytelling, badge_intelligence, commentary, daas_signals | 0 | TBD | TBD |
| v1.2 | 2026-03-28 | Added paddle_intel sub-object (brand, model, shape, grip, lead tape), added paddle_control_rating + grip_pressure_estimate to skill_indicators | 0 | TBD | TBD |
| **v1.1** | **2026-04-10** | Added REQUIRED FIELDS block at top. Fixed `signature_move_detected` (9%→~95%) — expanded from "recurring move" to "any distinctive characteristic." Fixed `predicted_badges` (73%→~98%) — added full 18-badge taxonomy + always-predict rule. Fixed `estimated_player_rating_dupr` (82%→~99%) — added DUPR scale with default "3.5-4.0". Fixed `ron_burgundy_voice` (82%→~99%) — marked required. | 11 | 7.4/10 | signature_move(9%), badges(73%), dupr(82%), ron_burgundy(82%) |

**Predicted improvement on next batch: +60-80% fill rate for previously weak fields.**

## How to Update This Log

1. Run `python evaluate-prompt-quality.py ./output/batch_summary_*.json`
2. Note avg fill rate and weak fields
3. Update `ANALYSIS_PROMPT` in `pickle-daas-gemini-analyzer.py`
4. Copy new prompt to `prompts/v1.X-YYYY-MM-DD.txt`
5. Add row to this table
6. Re-run on same 5 clips and compare outputs

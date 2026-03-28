# Gemini Prompt Version Log

| Version | Date | Key Changes | Clips Tested | Avg Quality | Weaknesses Found |
|---------|------|-------------|-------------|-------------|-----------------|
| v1.0 | 2026-03-28 | Initial prompt — all fields: clip_meta, players_detected, shot_analysis, skill_indicators, brand_detection, storytelling, badge_intelligence, commentary, daas_signals | 0 | TBD | TBD |
| v1.1 | TBD | Post-batch improvements based on evaluate-prompt-quality.py output | TBD | TBD | TBD |
| v1.2 | 2026-03-28 | Added paddle_intel sub-object (brand, model, shape, grip, lead tape), added paddle_control_rating + grip_pressure_estimate to skill_indicators | 0 | TBD | TBD |

## How to Update This Log

1. Run `python evaluate-prompt-quality.py ./output/batch_summary_*.json`
2. Note avg fill rate and weak fields
3. Update `ANALYSIS_PROMPT` in `pickle-daas-gemini-analyzer.py`
4. Copy new prompt to `prompts/v1.X-YYYY-MM-DD.txt`
5. Add row to this table
6. Re-run on same 5 clips and compare outputs

# Pickle DaaS — Tools Index

## Quick Commands
```bash
python tools/morning-brief-generator.py          # Morning brief (opens in browser)
python tools/rapid-cycle.py --depth quick_scan --angle tactical --data-slice all --output-format dashboard
python tools/rapid-cycle.py --depth quick_scan --angle brand --data-slice all --output-format dashboard
python tools/rapid-cycle.py --depth quick_scan --angle coach --data-slice high_quality --output-format dashboard
python tools/generate-overnight-prompt.py        # Generate tonight's prompt
python tools/session-closer.py                   # Close out a session
```

## Tools
| Script | What | API Keys |
|--------|------|----------|
| morning-brief-generator.py | Daily brief: hit list + corpus + threads (opens HTML) | None |
| session-closer.py | Captures session: new files, git log, next prompt | None |
| rapid-cycle.py | Pattern analysis: brand/skill/viral/tactical/coach | None (quick_scan) / Gemini (deep_dive) |
| generate-overnight-prompt.py | Picks next direction, writes paste-ready prompt | None |

## The Loop
```
morning-brief-generator.py → read brief → generate-overnight-prompt.py →
paste into Claude Code → rapid-cycle.py → session-closer.py → repeat
```

## Angles
- **brand**: JOOLA in 71% of clips. Brand co-occurrence. Investor moat story.
- **coach**: 45 clips quality≥6. Shot type + arc signals. Court Kings demo.
- **viral**: Score 2-8 (NOT boolean). 7 clips score ≥7. Shot patterns.
- **skill**: Shot-type proxy (skills dict is all-zero in corpus).
- **tactical**: Full pipeline health. $0.005/clip. Scale economics.

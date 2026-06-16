---
description: Run a fresh DaaS analysis batch in the documented script order
---
Run a fresh analysis batch following the SCRIPT REFERENCE order in CLAUDE.md.

Pre-flight:
- Confirm `.env` has the required keys (COURTANA_TOKEN, GEMINI_API_KEY). Never hardcode tokens — they load via `python-dotenv`. COURTANA_TOKEN expires/rotates, so verify it first.
- Run the API health check (see /api-check) and only proceed on `200`.
- Write all output to a NEW dated subdir under `output/` — never overwrite existing files.

Run in order:
1. `python fetch-clips-expanded.py` — fetch new clip URLs from the anon endpoint.
2. `python pickle-daas-gemini-analyzer.py` — core Gemini analysis (reads .env for keys).
3. `python aggregate-player-dna.py` — build the player DNA profile.
4. `python brand-intelligence-report.py` — brand detection aggregation.
5. `python prepare-lovable-data.py` — format data for the Lovable dashboard.

Every batch must produce JSON output + a cost log + a summary.md. At the end, report the output dir and per-clip cost (baseline: $0.0054/clip).

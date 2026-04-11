# chief@courtana.com — Agent Scripts

These scripts are the nightly automation layer for the `chief@courtana.com` AI employee.
Run them manually, or let cron call `agent-loop.py` every night automatically.

---

## Quick Start

```bash
# 1. Check credentials (always run this first)
python agents/credential-validator.py

# 2. Full nightly loop
python agents/agent-loop.py

# 3. Preview without spending money
python agents/agent-loop.py --dry-run
```

---

## Scripts

### `agent-loop.py` — Master Scheduler
The only script you need to call. Runs all others in order.

```
Step 1: credential-validator.py  → abort if required keys fail
Step 2: corpus-auto-ingest.py    → fetch and analyze new clips
Step 3: slack-ops-announcer.py   → post summary to Slack
```

**Flags:**
```bash
python agents/agent-loop.py                # Full nightly run
python agents/agent-loop.py --dry-run      # Validate creds + preview only, no Gemini
python agents/agent-loop.py --skip-slack   # Skip Slack post (useful for testing)
python agents/agent-loop.py --max-clips 5  # Limit to 5 clips (budget control)
```

**Log:** `agents/run-log.json` — every run is recorded with clips added, cost, errors.

**Cron setup (nightly 2 AM):**
```bash
0 2 * * * cd /path/to/PICKLE-DAAS && python agents/agent-loop.py >> agents/cron.log 2>&1
```

---

### `corpus-auto-ingest.py` — Nightly Clip Enrichment
Fetches new highlight groups from Courtana's API, finds clips not yet in the corpus,
analyzes each one with Gemini 2.5 Flash, and saves results.

**Key behaviors:**
- NEVER uses the `next` field from API responses (port 443 bug) — always manually increments `?page=N`
- Always sets `Accept: application/json` header
- Skips clips already in `output/enriched-corpus.json`
- Hard stops if spend exceeds $5 in one run
- Saves each batch to `output/batches/auto-YYYY-MM-DD/`

```bash
python agents/corpus-auto-ingest.py              # Normal run
python agents/corpus-auto-ingest.py --dry-run    # Preview new clips, no Gemini
python agents/corpus-auto-ingest.py --max-clips 10  # Analyze max 10 clips
```

**Cost:** ~$0.0054 per clip (Gemini 2.5 Flash, verified baseline)

**Outputs:**
- `output/batches/auto-YYYY-MM-DD/{uuid}.json` — individual clip analyses
- `output/batches/auto-YYYY-MM-DD/batch-summary.json` — run summary
- `output/auto-ingest-log.json` — running history of every ingest

---

### `credential-validator.py` — Token Health Check
Tests every credential before agents run. Color-coded: PASS / FAIL / MISS.

```bash
python agents/credential-validator.py             # Full check
python agents/credential-validator.py --required  # Exit 1 if required keys fail
python agents/credential-validator.py --json      # Machine-readable output
python agents/credential-validator.py --setup     # Walk through Gmail OAuth flow
```

**Required (agents abort without these):**
- `GEMINI_API_KEY` — Gemini 2.5 Flash analysis
- Courtana anon API — no key needed, but must be reachable

**Optional (agents skip gracefully if missing):**
- `COURTANA_TOKEN` — authenticated Courtana API
- `SLACK_BOT_TOKEN` — Slack posting
- `SLACK_OPS_CHANNEL` — target channel for ops posts
- `FIREFLIES_API_KEY` — meeting transcripts
- `NOTION_TOKEN` — deal stage sync
- `ELEVENLABS_API_KEY` — voice commentary
- `SUPABASE_URL` + `SUPABASE_ANON_KEY` — database

**Output:** `agents/last-credential-check.json` — timestamp, pass/fail for each key

---

### `slack-ops-announcer.py` — Overnight Build Announcer
Posts overnight build summaries to Slack. Reads the most recent morning brief
and the latest auto-ingest-log entry, formats it, and posts to `#ops`.

```bash
python agents/slack-ops-announcer.py                          # Auto-find latest brief
python agents/slack-ops-announcer.py --file output/briefs/MORNING-BRIEF-2026-04-11.md
python agents/slack-ops-announcer.py --channel C08XXXXXXX    # Override channel
```

**If `SLACK_BOT_TOKEN` is missing:** saves the message to `agents/pending-slack-posts.json`
instead of crashing. Once the token is added, you can manually re-post.

---

### `gmail-deal-scanner.py` — Deal Silence Detector
Scans `bill@courtana.com` for deal threads gone silent. Drafts follow-up emails.
Requires Gmail OAuth (run `credential-validator.py --setup` first).

```bash
python agents/gmail-deal-scanner.py
```

Schedule: Monday 7 AM, Thursday 3 PM.

---

## Credentials Needed

Add these to `PICKLE-DAAS/.env`:

```bash
# Required — agents won't run without these
GEMINI_API_KEY=AIza...

# Strongly recommended
SLACK_BOT_TOKEN=xoxb-...       # api.slack.com → Your Apps → OAuth Tokens
SLACK_OPS_CHANNEL=C08...       # Channel ID (right-click channel → Copy link → extract ID)
SLACK_DEALS_CHANNEL=C08...     # Channel ID for deals alerts

# Optional — used by other agents
COURTANA_TOKEN=eyJ...          # JWT from courtana.com (expires — anon endpoint works without this)
FIREFLIES_API_KEY=...          # fireflies.ai → Settings → API Key
NOTION_TOKEN=secret_...        # notion.so/my-integrations
ELEVENLABS_API_KEY=...         # ElevenLabs dashboard
SUPABASE_URL=https://...       # Supabase project URL
SUPABASE_ANON_KEY=eyJ...       # Supabase anon key
SUPABASE_SERVICE_KEY=eyJ...    # Supabase service role key

# chief@ account (once account is created)
CHIEF_EMAIL=chief@courtana.com
```

---

## Output Files

| File | What it is |
|------|-----------|
| `output/batches/auto-YYYY-MM-DD/` | Clip analyses from each nightly run |
| `output/auto-ingest-log.json` | History of every corpus ingest (clips found, cost) |
| `agents/run-log.json` | History of every full agent-loop run |
| `agents/last-credential-check.json` | Most recent credential test results |
| `agents/pending-slack-posts.json` | Slack messages queued when token was missing |
| `agents/cron.log` | Stdout from cron runs (if configured that way) |

---

## Common Issues

**"Required credentials failed — aborting"**
Run `python agents/credential-validator.py` to see which key is failing. Usually `GEMINI_API_KEY` not set.

**Slack posts not appearing**
Check `SLACK_BOT_TOKEN` and `SLACK_OPS_CHANNEL` in `.env`. Posts queue to `agents/pending-slack-posts.json` when the token is missing.

**Courtana API returning HTML instead of JSON**
The `Accept: application/json` header is already set in all scripts. If you're still getting HTML, check that the base URL is `https://courtana.com` (NOT `api.courtana.com`).

**Pagination seems to skip clips**
The scripts never use the `next` field from API responses (port 443 bug). They always build URLs as `?page=N&page_size=100`. This is intentional.

**Gemini returns 400 on a clip**
Some CDN URLs may be temporarily inaccessible. The script logs the error and continues with the next clip.

---

## Architecture Notes

- All scripts load `.env` via `python-dotenv` at startup
- Missing optional credentials print a warning and continue (never crash)
- Every run writes to a log file — check logs, not stdout, for cron debugging
- New dated output directories are always created — existing files are never overwritten
- Exponential backoff is applied on all HTTP 429 (rate limit) errors

# PICKLE-DAAS/CLAUDE.md — Data Pipeline Technical Context
_Last updated: 2026-04-09 (AI COO v2)_
_Read this before touching any script in this directory._

---

## WHAT

Pickle DaaS is a Data-as-a-Service pipeline that processes Courtana's video corpus into
structured intelligence — player DNA profiles, shot analytics, brand intelligence, coaching
feedback. Current corpus: 4,097+ highlight groups. Target: 400K clips.

**Proven cost baseline: $0.0054/clip** (Gemini 2.5 Flash, verified April 9, 2026)

---

## CRITICAL API RULES (don't skip this)

```
# ❌ WRONG — this domain doesn't exist
GET https://api.courtana.com/...

# ✅ CORRECT — always use courtana.com as base
GET https://courtana.com/app/anon-highlight-groups/?page_size=100&page=N

# Auth required endpoints
GET https://courtana.com/app/highlight-groups/
GET https://courtana.com/accounts/profiles/current/
GET https://courtana.com/accounts/profiles/action_get_leaderboard/
Headers: Authorization: Bearer {COURTANA_TOKEN}
         Accept: application/json   ← REQUIRED or you get HTML

# Pagination: NEVER use the `next` field — it has a port 443 bug
# Always construct: ?page=N&page_size=100
```

---

## ENVIRONMENT SETUP

```bash
# Required in .env (never hardcode these)
COURTANA_TOKEN=<jwt>          # Test before use — rotates/expires. Anon endpoint doesn't need this.
GEMINI_API_KEY=<key>          # Gemini 2.5 Flash
ELEVENLABS_API_KEY=<key>      # Voice pipeline

# Supabase (NOT YET DEPLOYED — schema ready)
SUPABASE_URL=<url>
SUPABASE_KEY=<service_key>
```

**Before any batch run:** `curl -s -o /dev/null -w "%{http_code}" -H "Accept: application/json" https://courtana.com/app/anon-highlight-groups/?page_size=1`
Should return `200`. If not, the API is down.

---

## WHAT'S DONE vs IN PROGRESS vs BLOCKED

### ✅ DONE
- **Full analysis pipeline:** fetch → Gemini analyze → JSON output → ElevenLabs voice → aggregate
- **14+ clip analyses** in `output/batch-30-daas/` and `output/picklebill-batch-20260410/`
- **Investor dashboard:** `output/pickle-daas-investor-demo.html` (10 sections, shareable)
- **Cost baseline:** `output/cost-summary.md` ($0.0054/clip confirmed)
- **DUPR integration research:** `output/dupr-integration-plan.md`
- **Voice commentary:** 32+ MP3s in `output/voice-commentary/`
- **Lovable prompts 01-10:** `lovable-prompts/` + `lovable-prompts/PASTE-ORDER.md`
- **Player DNA profile:** `output/picklebill-dna-profile.json`
- **Schema + push script:** `supabase/push-analysis-to-db.py` + `supabase/SUPABASE-SETUP-GUIDE.md`
- **Cost measurement tool:** `tools/measure_clip_costs.py`

### ⚠️ IN PROGRESS
- **Gemini batch (20 clips):** `output/picklebill-batch-20260410/` — may still be running; check file count
- **Supabase deployment:** Schema ready, instance not provisioned. Follow `supabase/SUPABASE-SETUP-GUIDE.md`

### ❌ BLOCKED / NOT STARTED
- DUPR API integration (research done, `tools/dupr-enrichment.py` is a skeleton — needs API credentials)
- Production Lovable build (paste lovable-prompts 01-10 in order per PASTE-ORDER.md)
- Langfuse observability (deferred to next overnight build)

---

## SCRIPT REFERENCE (run in order for a fresh batch)

```bash
# 1. Fetch new clip URLs
python fetch-clips-expanded.py                    # Gets clips from anon endpoint

# 2. Analyze with Gemini
python pickle-daas-gemini-analyzer.py             # Core analysis — reads .env for keys

# 3. Voice commentary (optional)
python elevenlabs-voice-pipeline.py               # Reads output JSONs, generates MP3s

# 4. Aggregate
python aggregate-player-dna.py                   # Builds player DNA profile from all clips
python brand-intelligence-report.py              # Brand detection aggregation

# 5. Prepare for Lovable
python prepare-lovable-data.py                   # Formats data for Lovable dashboard

# 6. Push to Supabase (BLOCKED until instance deployed)
python supabase/push-analysis-to-db.py           # Bulk push all analyses

# Measurement
python tools/measure_clip_costs.py               # Cost baseline tool
python tools/model-monitor.py                    # Model performance tracking
```

---

## OUTPUT DIRECTORY MAP

```
output/
├── batch-30-daas/              ← 11 analyzed clips (the reference batch)
├── picklebill-batch-20260410/  ← 20 clips from Apr 10 batch
├── pickle-daas-investor-demo.html  ← INVESTOR DEMO — shareable
├── pickle-daas-investor-proof-points.md  ← 250-line proof doc
├── cost-summary.md             ← $0.0054/clip headline
├── picklebill-dna-profile.json ← Full player profile
├── picklebill-intel-card.html  ← Shareable player card
├── voice-commentary/           ← 32+ MP3s
├── cost-baseline-20260409.csv  ← Per-clip cost data
├── dupr-integration-plan.md    ← DUPR API research
└── lovable-package/            ← Prepared data for Lovable
```

---

## RULES

- Never overwrite files in `output/` — always write to new dated subdirs
- Never hardcode tokens — always use `.env` + `python-dotenv`
- Every batch run should produce: JSON output + cost log + summary.md
- Check COURTANA_TOKEN before any auth API call — it expires/rotates
- See `../BILL-OS/LESSONS.md` for known API gotchas and errors

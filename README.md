# Pickle DaaS — Data as a Service Pipeline

**Built by Courtana · courtana.com · bill@courtana.com**

A complete AI-powered Data-as-a-Service pipeline for pickleball highlight analysis. Analyzes video clips using Gemini 2.5 Flash for shot detection, brand intelligence, player DNA, badge triggers, and voice commentary — at **$0.0054 per clip**.

---

## What's Built

| File / Directory | What It Is | How to Use |
|---|---|---|
| `output/pickle-daas-investor-demo.html` | **Flagship investor demo** — 10 sections, live Courtana data, interactive cost calculator, Chart.js radar, Ron Burgundy hover quotes | Open in browser before any investor call |
| `output/picklebill-intel-card.html` | **Shareable player card** — Spotify Wrapped aesthetic, Rank #1, 311,800 XP, 82 badges | Post on LinkedIn. Show to Court Kings: "this is what your players will have" |
| `output/pickle-daas-investor-proof-points.md` | **Investor proof points** — real cost data, DUPR framing, competitive comps, scale math | Use as prep doc / leave-behind |
| `lovable-prompts/PASTE-ORDER.md` | **Exact paste sequence** for Lovable projects | Start here before opening Lovable |
| `lovable-prompts/09-court-kings-coaching-page.md` | **Court Kings demo** — black/gold branding, coaching intelligence page | Paste into new Lovable project, share preview with Rich + Bryan |
| `lovable-prompts/08-investor-demo-page.md` | Investor demo Lovable page (Supabase-connected) | Paste after deploying Supabase |
| `lovable-prompts/10-multi-player-comparison.md` | Side-by-side player radar comparison | Paste after 08 |
| `output/cost-summary.md` | Cost baseline report — $/clip, scale economics | Reference for investor conversations |
| `output/dupr-integration-plan.md` | DUPR partnership + integration plan | Strategic reading; pitch angle: "DUPR knows WHO, Courtana knows WHY" |
| `supabase/SUPABASE-SETUP-GUIDE.md` | 15-min Supabase deployment guide | Follow once to unlock Lovable DB connections |
| `supabase/push-analysis-to-db.py` | Bulk analysis loader to Supabase | `python supabase/push-analysis-to-db.py output/batch-30-daas/ output/picklebill-batch-001/` |
| `tools/measure_clip_costs.py` | Cost measurement tool | `python tools/measure_clip_costs.py output/picklebill-batch-20260410/` |
| `tools/dupr-enrichment.py` | DUPR player ID → rating mapper skeleton | Extend with real DUPR API credentials |
| `prompts/v1.1-20260410.txt` | **Current analysis prompt** — use this for all new batches | Replace ANALYSIS_PROMPT in `pickle-daas-gemini-analyzer.py` |
| `prompts/PROMPT-LOG.md` | Prompt version history + fill rate tracking | Update after each batch evaluation |

---

## Analyzed Clips

| Batch | Directory | Clips | Status |
|---|---|---|---|
| batch-30-daas | `output/batch-30-daas/` | 11 | ✅ Complete |
| batch-001 | `output/picklebill-batch-001/` | 4 | ✅ Complete |
| 2026-04-10 batch | `output/picklebill-batch-20260410/` | 4/20 | ⏳ Partial |
| **Total** | | **~19** | |

---

## The Headline Number

> **$0.0054 per clip** — shot types, brand detection, player DNA, badge triggers, viral potential, Ron Burgundy voice commentary.
>
> **The entire 4,097-clip corpus = $22.12 to analyze.**
>
> At 1,000 venues: $44,928/year analysis cost vs. $60M/year brand API revenue = **1,337:1 cost-to-revenue ratio.**

---

## Quick Start

### Run a new analysis batch
```bash
python3 pickle-daas-gemini-analyzer.py --input output/batch-20260410-urls.json --output output/picklebill-batch-20260410/ --limit 20
```

### Measure costs on a batch
```bash
python3 tools/measure_clip_costs.py output/picklebill-batch-20260410/
```

### Aggregate player DNA
```bash
python3 aggregate-player-dna.py output/picklebill-batch-20260410/batch_summary_*.json
```

### Push analyses to Supabase
```bash
python3 supabase/push-analysis-to-db.py output/batch-30-daas/ output/picklebill-batch-20260410/
```

---

## Deal-Relevant Assets

| Deal | Asset | File |
|---|---|---|
| **Court Kings** (Rich + Bryan) | Lovable prompt → paste into new project → share preview | `lovable-prompts/09-court-kings-coaching-page.md` |
| **Court Kings** (demo) | Player Intel Card — "this is what your players will have" | `output/picklebill-intel-card.html` |
| **All investors** | Live investor demo with cost calculator | `output/pickle-daas-investor-demo.html` |
| **All investors** | Proof points with DUPR framing + scale math | `output/pickle-daas-investor-proof-points.md` |
| **Peak Pickleball** | Coaching intelligence section | `output/pickle-daas-investor-demo.html` section 8 |

---

## API Keys Required

Set in `.env` (never committed):

```
GEMINI_API_KEY=          # Google AI Studio
ELEVENLABS_API_KEY=      # Voice generation
COURTANA_TOKEN=          # JWT from courtana.com localStorage (for profile/leaderboard endpoints)
SUPABASE_URL=            # From Supabase project settings
SUPABASE_SERVICE_KEY=    # Service role key (server-side only)
SUPABASE_ANON_KEY=       # For Lovable frontend
```

**Note:** Clip CDN URLs (`cdn.courtana.com`) are publicly accessible — no token needed for video analysis.

---

## Courtana API Notes

- **Anonymous clips endpoint:** `https://courtana.com/app/anon-highlight-groups/?page_size=100`
- **Pagination:** Construct manually as `?page=N&page_size=100` — do NOT follow the `next` field (port 433 bug)
- **CDN thumbnails:** Replace `.mp4` with `.jpeg` in any clip URL
- **DO NOT use** `api.courtana.com` — it's NXDOMAIN. Use `courtana.com` with relative paths.

---

*Overnight build: April 9–10, 2026 · Claude Code (Chief Data Scientist mode)*

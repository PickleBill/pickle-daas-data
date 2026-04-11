# output/ Directory Index
_Reorganized 2026-04-11. See REORGANIZE-LOG.md for move history._

## Subdirectories

| Folder | Purpose | Contents |
|--------|---------|----------|
| `batches/` | All batch analysis runs | 17 batch folders (auto-ingest, fast-batch, picklebill-batch, etc.) |
| `discovery/` | Discovery Engine runs | `v1/` = original 21 discoveries, `v2/` = verified version |
| `investor/` | Investor-facing materials | Demo HTML, proof points doc |
| `dashboards/` | HTML dashboards | 15 standalone dashboards (badges, brand, coaching, etc.) |
| `player/` | Player profiles & DNA | DNA profile JSON, intel card, player cards dir |
| `brand/` | Brand intelligence | Brand detection report JSON |
| `lovable/` | Lovable-ready exports | Dashboard data, clips metadata, brand registry, voice manifests |
| `voice/` | Voice commentary | ElevenLabs output, manifests, logs |
| `tools/` | Cost logs & diagnostics | Cost CSVs, run logs, cost summary |

## Root Files (kept at top level)

| File | Why it stays |
|------|-------------|
| `corpus-export.json` | Referenced by gh-pages |
| `buyer-segments.json` | Referenced by gh-pages |
| `enriched-corpus.json` | Cross-referenced by multiple scripts |
| `*.md` files | Session handoffs, briefs, spend log |
| `*.json` data files | Working sets, broadcast clips, sport catalog |
| `*.db` files | SQLite databases (badges, coaching) |

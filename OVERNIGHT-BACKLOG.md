# PICKLE DaaS — Overnight Claude Code Build Queue
_Last updated: 2026-03-28. Read PICKLE-DAAS-CLAUDE-CODE-CONTEXT.md first._
_This file is a sequential task queue. Execute tasks in order. Mark each DONE when complete._

---

## HOW TO RUN THIS

Open Claude Code in the PICKLE-DAAS folder and say:

> "Read OVERNIGHT-BACKLOG.md and PICKLE-DAAS-CLAUDE-CODE-CONTEXT.md, then execute tasks in order starting from the first one marked TODO. Mark each task DONE when complete and move to the next."

Each task is self-contained. If a task fails, log the error inline and skip to the next.

---

## ENVIRONMENT SETUP (Do This First)

```bash
# Required
export GEMINI_API_KEY="get from https://aistudio.google.com/app/apikey"
export COURTANA_TOKEN="get from courtana.com → DevTools → localStorage → 'token'"

# Optional (for Supabase push)
export SUPABASE_URL="https://YOUR_PROJECT.supabase.co"
export SUPABASE_SERVICE_KEY="your_service_role_key"

# Install Python deps
pip install google-generativeai requests python-dotenv
```

Create a `.env` file in this folder with the above values so you don't have to re-export each session.

---

## TASK QUEUE

---

### TASK 001 — Test Gemini Analyzer on Single Clip [BLOCKED — GEMINI_API_KEY not set]

**Objective:** Verify the analyzer works end-to-end on one known highlight.

**Run:**
```bash
python pickle-daas-gemini-analyzer.py \
  --url "https://cdn.courtana.com/files/production/u/01915c59-9bb7-4683-bd53-e28bddcae12e/ce00696b-9f9b-465a-971c-dbf1334e556c.mp4" \
  --output-dir ./output/test-001
```

**Success criteria:**
- JSON file written to `./output/test-001/`
- `clip_quality_score` is a number 1-10
- `brands_detected` array exists (may be empty)
- `commentary.ron_burgundy_voice` is non-null
- `commentary.announcement_text_for_tts` is non-null

**If it fails:** Check GEMINI_API_KEY, check video URL is reachable, log error here.

**Output:** Save the raw JSON as `./output/test-001/SAMPLE_RESULT.json`

---

### TASK 002 — Add .env Support to Analyzer Script [DONE]

**Objective:** Make the script load from `.env` automatically so Bill doesn't need to export vars manually.

**Edit `pickle-daas-gemini-analyzer.py`:**
- Add `from dotenv import load_dotenv` at top
- Add `load_dotenv()` before `init_gemini()`
- Create `env.example` file:
  ```
  GEMINI_API_KEY=
  COURTANA_TOKEN=
  SUPABASE_URL=
  SUPABASE_SERVICE_KEY=
  ELEVENLABS_API_KEY=
  ```

**Output:** Updated script + `env.example` file.

---

### TASK 003 — Build Supabase Schema Script [DONE]

**Objective:** Create a runnable SQL file for the Supabase schema.

**Create `supabase-schema.sql`** with the full schema from PICKLE-DAAS-CLAUDE-CODE-CONTEXT.md:
- `pickle_daas_analyses` table
- `pickle_daas_brands` table
- `pickle_daas_player_dna` table
- All indexes
- Add `CREATE TABLE IF NOT EXISTS` guards
- Add helpful comments on each column

**Also create `supabase-seed.sql`** with:
- 1 sample analysis row (use values from TASK 001 output if available, otherwise use realistic placeholders)
- 3 sample brand rows (Selkirk, JOOLA, Engage)
- 1 PickleBill player_dna row

**Output:** `supabase-schema.sql` and `supabase-seed.sql`

---

### TASK 004 — Batch Run: PickleBill Top 20 Highlights [BLOCKED — requires GEMINI_API_KEY + COURTANA_TOKEN]

**Prerequisite:** TASK 001 succeeded. COURTANA_TOKEN is set.

**Objective:** Run the full PickleBill batch — 20 highlights through Gemini, save all results.

**Run:**
```bash
python pickle-daas-gemini-analyzer.py \
  --courtana-token "$COURTANA_TOKEN" \
  --player PickleBill \
  --limit 20 \
  --output-dir ./output/picklebill-batch-001
```

**Note:** This will take ~20-40 minutes (Gemini processing per clip). Let it run.

**Success criteria:**
- At least 15/20 clips successfully analyzed (some may fail due to video format)
- `batch_summary_*.json` file written with all results
- Batch ranked by `clip_quality_score`

**Output:** `./output/picklebill-batch-001/batch_summary_*.json`

---

### TASK 005 — Build Batch Aggregator Script [DONE]

**Objective:** Post-process batch results into a Player DNA JSON profile.

**Create `aggregate-player-dna.py`:**

Takes a batch summary JSON and outputs a single player DNA profile:

```python
#!/usr/bin/env python3
"""
Aggregates multiple Gemini analysis results into a single Player DNA profile.
Usage: python aggregate-player-dna.py ./output/picklebill-batch-001/batch_summary_*.json
"""
```

**The aggregator should calculate:**
- `avg_quality_score` across all clips
- `avg_viral_potential` across all clips
- `dominant_shot_type` (most frequent across clips)
- `play_style_tags` (union of all unique tags, sorted by frequency)
- `top_brands` (brand name + count, sorted by appearances)
- `badge_predictions` (most commonly predicted badges across clips)
- `signature_moves` (list from all clips where non-null)
- `skill_aggregate` (average of each skill_indicator field across clips)
- `best_clips` (top 5 by quality score, with URL + caption)
- `worst_clips` (bottom 3 — for coaching feedback)
- `story_arcs_distribution` (count of each story_arc type)
- `commentary_highlights` (best ron_burgundy_voice from top clip, best social_caption)

**Output format:**
```json
{
  "player_username": "PickleBill",
  "generated_at": "ISO timestamp",
  "clips_analyzed": 20,
  "player_dna": { ... },
  "brand_registry": [...],
  "top_clips": [...],
  "coaching_notes": [...]
}
```

**Save output as:** `./output/picklebill-dna-profile.json`

---

### TASK 006 — Build Brand Intelligence Report [DONE]

**Prerequisite:** TASK 004 batch output exists.

**Objective:** Create a standalone brand detection report from the batch.

**Create `brand-intelligence-report.py`:**
- Reads batch_summary JSON
- Extracts all `brand_detection.brands` arrays across all clips
- Aggregates by `brand_name` + `category`
- Builds frequency table: brand → total_appearances, total_clips_seen_in, player_sides, avg_confidence, categories
- Identifies "whitespace" brands (mentioned in `sponsorship_whitespace` fields)
- Outputs as both JSON and a readable Markdown report

**Output files:**
- `./output/brand-registry.json` — machine-readable
- `./output/brand-report.md` — human-readable, suitable for sponsor pitch

**The Markdown report should include:**
```
# Courtana Brand Intelligence Report
Generated: [date] | Clips analyzed: 20 | Player: PickleBill

## Top Brands Detected
| Brand | Category | Appearances | Confidence |
...

## Sponsorship Whitespace (Brands NOT present but relevant)
...

## Brand-Player Associations
...
```

---

### TASK 007 — Build Prompt Version Control System [DONE]

**Objective:** Track Gemini prompt versions so we can measure improvement over time.

**Create `prompts/` directory with:**

`prompts/v1.0-2026-03-28.txt` — copy of the current ANALYSIS_PROMPT from `pickle-daas-gemini-analyzer.py`

`prompts/PROMPT-LOG.md`:
```markdown
# Gemini Prompt Version Log

| Version | Date | Key Changes | Clips Tested | Avg Quality | Weaknesses Found |
|---------|------|-------------|-------------|-------------|-----------------|
| v1.0 | 2026-03-28 | Initial prompt | 0 | TBD | TBD |
```

**Also create `evaluate-prompt-quality.py`:**
- Reads a batch_summary JSON
- Scores each field's "fill rate" (% of clips where field is non-null and non-empty)
- Identifies weakest fields (fill rate < 50%)
- Outputs a field quality report
- Suggests which fields to improve in next prompt version

**Output:** `./output/prompt-quality-report.md`

---

### TASK 008 — Build ElevenLabs Voice Pipeline Script [DONE]

**Objective:** Take `announcement_text_for_tts` from any analysis JSON → generate MP3 via ElevenLabs API.

**Create `elevenlabs-voice-pipeline.py`:**

```
Usage: python elevenlabs-voice-pipeline.py --analysis ./output/test-001/analysis_*.json [--voice ron_burgundy]
```

**Features:**
- Reads analysis JSON, extracts `commentary.announcement_text_for_tts`
- Also extracts `commentary.ron_burgundy_voice` and `commentary.hype_announcer_charged` as alternatives
- Calls ElevenLabs API `/v1/text-to-speech/{voice_id}`
- Default voices to support:
  - `espn` → voice_id for broadcast-style voice (Bill suggests "Liam" or "Daniel")
  - `hype` → more energetic voice
  - `ron_burgundy` → closest available to Ron Burgundy personality
- Saves MP3 to same folder as analysis JSON
- **Optionally merges with original video using FFmpeg:**
  ```bash
  ffmpeg -i original_clip.mp4 -i commentary.mp3 -c:v copy -map 0:v -map 1:a -shortest output_with_voice.mp4
  ```

**ElevenLabs API call:**
```python
import requests

def generate_voice(text: str, voice_id: str, api_key: str) -> bytes:
    url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
    headers = {
        "Accept": "audio/mpeg",
        "Content-Type": "application/json",
        "xi-api-key": api_key
    }
    payload = {
        "text": text,
        "model_id": "eleven_monolingual_v1",
        "voice_settings": {"stability": 0.5, "similarity_boost": 0.75}
    }
    response = requests.post(url, json=payload, headers=headers)
    return response.content
```

**Add `ELEVENLABS_API_KEY` to `.env` and `env.example`**

**Output:** MP3 file + optionally merged video file.

---

### TASK 009 — Build Lovable Data Prep Script [DONE]

**Objective:** Transform raw Gemini batch output into clean JSON that Lovable apps can consume directly (no API call needed during demo).

**Create `prepare-lovable-data.py`:**

Takes batch_summary + player_dna profile and outputs `lovable-dashboard-data.json`:

```json
{
  "player": {
    "username": "PickleBill",
    "rank": 1,
    "xp": 283950,
    "level": 17,
    "rank_tier": "Gold III",
    "avatar_url": "https://cdn.courtana.com/...",
    "badges_count": 82
  },
  "highlights": [
    {
      "id": "...",
      "name": "Epic Rally #427",
      "thumbnail_url": "https://cdn.courtana.com/...",
      "video_url": "https://cdn.courtana.com/...",
      "quality_score": 8.2,
      "viral_score": 7.5,
      "caption": "...",
      "hashtags": ["#pickleball", ...],
      "brands": ["Selkirk", "JOOLA"],
      "story_arc": "clutch_moment",
      "badges_predicted": ["Epic Rally", "Kitchen King"],
      "ron_burgundy_quote": "..."
    }
  ],
  "analytics": {
    "avg_quality_score": 7.3,
    "top_shot_type": "dink",
    "dominant_play_style": "kitchen specialist",
    "top_brands": [{"brand": "Selkirk", "count": 12}, ...],
    "skill_radar": {
      "court_coverage": 8.1,
      "kitchen_mastery": 9.2,
      "creativity": 7.8,
      "athleticism": 8.5,
      "court_iq": 8.9
    },
    "story_arc_breakdown": {
      "clutch_moment": 6,
      "athletic_highlight": 5,
      "dominant_performance": 4
    },
    "viral_potential_distribution": [6.2, 7.1, 8.4, ...]
  },
  "generated_at": "ISO timestamp"
}
```

**Output:** `./output/lovable-dashboard-data.json`

---

### TASK 010 — Build Lovable Prompts Library [DONE]

**Objective:** Write the actual Lovable prompts Bill pastes to build each UI feature. These are ready-to-use, not vague descriptions.

**Create `lovable-prompts/` directory with these files:**

---

**`lovable-prompts/01-picklebill-dashboard.md`**

The master prompt to build the PickleBill Intelligence Dashboard in Lovable. Include:
- Component structure (header with player card, highlights grid, analytics section, brand row)
- Exact color scheme: dark background #252d3a, green accent #00E676
- Data source: import from `lovable-dashboard-data.json` (paste the JSON inline)
- Highlight cards with: thumbnail, quality score badge, caption, Ron Burgundy quote on hover
- Skill radar chart using recharts RadarChart
- Brand logos row (use brand names as text if logos unavailable)
- Mobile responsive

---

**`lovable-prompts/02-add-live-api.md`**

Prompt to swap static JSON for live Courtana API calls via Supabase Edge Function proxy:
- Replace static import with fetch calls to `{SUPABASE_URL}/functions/v1/courtana-proxy`
- Add loading skeletons
- Add error state with retry
- Keep existing component structure

---

**`lovable-prompts/03-highlight-video-player.md`**

Add a video player modal to the highlights grid:
- Click any thumbnail → modal opens with HTML5 video player
- Video URL from `video_url` field (cdn.courtana.com MP4)
- Show quality score, caption, badges, Ron Burgundy quote below video
- Close on escape or click outside
- Autoplay on open

---

**`lovable-prompts/04-brand-intelligence-card.md`**

Add a brand intelligence section to the dashboard:
- Horizontal scrollable brand cards
- Each card: brand name, category icon (paddle/shoe/apparel), appearance count, bar chart
- Highlight "whitespace" brands in a separate "Sponsor Opportunities" section
- Framed as: "Brands appearing in [player]'s highlights"

---

**`lovable-prompts/05-ron-burgundy-voice-button.md`**

Add a voice playback button to each highlight card:
- Small speaker icon on each highlight card
- Click → fetch commentary audio from a URL (pre-generated MP3 stored on CDN)
- OR: call ElevenLabs API directly from the browser (if API key is in env)
- Show waveform animation while playing
- Auto-stop when modal closes

---

**`lovable-prompts/06-court-kings-demo-page.md`**

Build a separate "Court Kings Intelligence Demo" page:
- Header: Court Kings branding (black/gold)
- Intro: "Powered by Courtana AI — what we can show for your players"
- Player selector: dropdown of Court Kings player names
- Same dashboard UI below
- Footer: "Ready to deploy at Court Kings. courtana.com"
- This is the page Bill shows to Rich + Bryan

---

**`lovable-prompts/07-daas-pitch-overlay.md`**

Add a "Pickle DaaS Scale" section to the bottom of the dashboard:
- Animated counter: "4,097 highlights analyzed → 4,097,000 with 1,000 venues"
- Three stat cards: Highlights Analyzed / Brands Detected / Players Profiled
- One big quote: "What would you do with the world's largest sports data corpus?"
- CTA button: "Talk to us about Pickle DaaS"

---

### TASK 011 — Prompt Quality Evaluation Run [BLOCKED — requires TASK 004 batch data]

**Prerequisite:** TASK 004 batch complete, TASK 007 evaluator script built.

**Run:**
```bash
python evaluate-prompt-quality.py ./output/picklebill-batch-001/batch_summary_*.json
```

**Review the output and:**
- Identify which fields have < 60% fill rate
- Identify which fields had surprising/wrong values
- Write a prompt improvement note in `prompts/PROMPT-LOG.md`
- Update `ANALYSIS_PROMPT` in the analyzer script for v1.1
- Save v1.1 prompt to `prompts/v1.1-2026-03-28.txt`

---

### TASK 012 — Paddle-Specific Detection Enhancement [DONE]

**Objective:** The current brand detection is generic. Pickleball paddles are the highest-value sponsorship asset. Enhance the prompt to extract maximum paddle intelligence.

**Edit `ANALYSIS_PROMPT` in the analyzer script** — in the `brand_detection` section, add a new sub-field:

```json
"paddle_intel": {
  "paddle_brand": "<brand name if detectable, e.g. Selkirk, JOOLA, Engage, HEAD, Paddletek, Franklin, Onix, Gearbox, Six Zero>",
  "paddle_model_estimate": "<specific model if visible, or null>",
  "paddle_color_scheme": "<dominant colors>",
  "paddle_shape_estimate": "elongated|standard|wide_body|unknown",
  "paddle_grip_style_observed": "two_handed|one_handed|continental|eastern|western|unknown",
  "grip_color": "<if visible>",
  "overgrip_present": "<boolean or null>",
  "lead_tape_visible": "<boolean — players who customize paddles are serious>",
  "confidence": "high|medium|low",
  "notes": "<any other observable paddle details>"
}
```

**Also add to `skill_indicators`:**
```json
"paddle_control_rating": "<1-10, based on shot quality and touch>",
"grip_pressure_estimate": "<loose|medium|firm — inferred from shot outcomes>"
```

**Bump prompt version to v1.2 and log in PROMPT-LOG.md.**

---

### TASK 013 — Unique Insights for B2B Vetting [DONE]

**Objective:** Build a "Company Intelligence" layer — things that are uniquely valuable for pitching sponsors, venues, or investors.

**Create `company-vetting-insights.py`:**

Takes batch_summary and generates insights formatted for different audiences:

```python
def generate_sponsor_pitch_data(batch: list) -> dict:
    """What brands want to know before sponsoring."""
    return {
        "dominant_brands_already_present": [...],
        "whitespace_opportunities": [...],
        "avg_brand_visibility_seconds": ...,
        "estimated_impressions_per_clip": ...,  # view_count × brands_visible
        "player_demographic_signals": [...],
        "content_formats_by_engagement": [...],
    }

def generate_venue_pitch_data(batch: list) -> dict:
    """What venue owners want to know."""
    return {
        "avg_rally_length": ...,
        "skill_level_distribution": {...},
        "most_exciting_shot_types": [...],
        "peak_play_quality_times": [...],  # if timestamp data available
        "coaching_opportunity_score": ...,
    }

def generate_investor_pitch_data(batch: list) -> dict:
    """What investors want to see."""
    return {
        "corpus_size": 4097,
        "data_richness_avg_score": ...,
        "unique_players_detected": ...,
        "brands_detected_total": ...,
        "insights_per_clip": ...,  # avg number of non-null fields
        "value_per_clip_estimate": "...",  # narrative
    }
```

**Output:** `./output/b2b-vetting-insights.json` + `./output/b2b-vetting-report.md`

---

### TASK 014 — Simple HTML Preview Dashboard [DONE]

**Objective:** Build a single static HTML file that renders the Lovable dashboard data without needing Lovable or React. Bill can open this in any browser immediately.

**Create `preview-dashboard.html`:**
- Reads `lovable-dashboard-data.json` inline (paste the data directly into a `<script>` tag as a JS variable)
- Dark theme: background #1a2030, accent #00E676
- Sections:
  1. Player header (avatar, rank, XP, badges)
  2. Highlights grid (2-3 columns, thumbnail + quality score + caption)
  3. Skill radar chart (use Chart.js from CDN)
  4. Brand bar chart (top 5 brands by appearance)
  5. Top Ron Burgundy quote (pulled from highest-quality clip)
  6. DaaS pitch line at bottom
- NO dependencies beyond Chart.js CDN
- Must work by double-clicking the file in Finder

**Output:** `preview-dashboard.html` — open directly in browser.

---

### TASK 015 — Session Summary [DONE]

**Objective:** After all above tasks are attempted, write a brief summary.

**Create `overnight-run-summary.md`:**
```markdown
# Overnight Run Summary
Date: [date]
Tasks completed: X/15
Tasks failed: X/15

## What Was Built
- [list]

## What Failed and Why
- [list]

## Recommended Next Steps for Bill
1. [most important thing to do manually]
2. [second thing]
3. [third thing]

## Files Ready to Use
- [list with one-line descriptions]

## Prompt Quality Notes
- Fields with best coverage: [list]
- Fields needing improvement: [list]
- Suggested Gemini model upgrade: yes/no and why
```

---

## NOTES FOR CLAUDE CODE

- **Model to use:** `gemini-2.5-flash` (default). Use `--model gemini-2.5-pro` for TASK 001 test only if you want to compare quality. Flash is faster and cheaper for batches.
- **Rate limiting:** Add 2-3 second sleep between batch clips. Gemini File API has upload limits.
- **Video download errors:** Some Courtana CDN URLs may require no auth (they're public) but may have CDN edge caching behavior. Retry once on failure.
- **JSON parse failures:** If Gemini returns malformed JSON, save the raw text and move on. Don't abort the batch.
- **File size:** Courtana clips are typically 10-60 seconds and under 50MB. Should be fine for Gemini File API (2GB limit).
- **Courtana token:** Bill needs to grab this from courtana.com → DevTools → Application tab → Local Storage → key `token`. It's a JWT.
- **ElevenLabs voices to use for testing:**
  - Voice IDs change — use `/v1/voices` endpoint to list available voices first
  - Look for: "Adam" (authoritative), "Josh" (deep, broadcast), "Antoni" (well-rounded)
  - For Ron Burgundy energy: look for confident, slightly pompous male voice

---

## QUICK REFERENCE: KEY FILE PATHS

```
PICKLE-DAAS/
├── pickle-daas-gemini-analyzer.py      ← Main script (TASK 001)
├── aggregate-player-dna.py             ← TASK 005
├── brand-intelligence-report.py        ← TASK 006
├── evaluate-prompt-quality.py          ← TASK 007
├── elevenlabs-voice-pipeline.py        ← TASK 008
├── prepare-lovable-data.py             ← TASK 009
├── company-vetting-insights.py         ← TASK 013
├── preview-dashboard.html              ← TASK 014
├── supabase-schema.sql                 ← TASK 003
├── supabase-seed.sql                   ← TASK 003
├── env.example                         ← TASK 002
├── prompts/
│   ├── v1.0-2026-03-28.txt
│   └── PROMPT-LOG.md
├── lovable-prompts/
│   ├── 01-picklebill-dashboard.md
│   ├── 02-add-live-api.md
│   ├── 03-highlight-video-player.md
│   ├── 04-brand-intelligence-card.md
│   ├── 05-ron-burgundy-voice-button.md
│   ├── 06-court-kings-demo-page.md
│   └── 07-daas-pitch-overlay.md
└── output/
    ├── test-001/
    ├── picklebill-batch-001/
    ├── picklebill-dna-profile.json
    ├── brand-registry.json
    ├── brand-report.md
    ├── lovable-dashboard-data.json
    ├── b2b-vetting-insights.json
    └── prompt-quality-report.md
```

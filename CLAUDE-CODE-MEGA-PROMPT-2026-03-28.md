# Claude Code — Pickle DaaS Mega Build Prompt
_Paste this entire file into Claude Code. Say "yes" to everything. Let it run._

---

## Context

You are working on Pickle DaaS — an AI video analysis pipeline for pickleball highlights. The project lives at:

```
~/PickleBill Dropbox/PickleBill Team Folder/Claude Projects/PICKLE-DAAS/
```

Read `PICKLE-DAAS-CLAUDE-CODE-CONTEXT.md` in that folder FIRST — it has the full architecture, API endpoints, CDN patterns, and experiment backlog.

The overnight build already created these scripts (all working, syntactically valid):
- `pickle-daas-gemini-analyzer.py` — Gemini video analysis (works, tested on real clips)
- `elevenlabs-voice-pipeline.py` — TTS voice generation (needs API key to run)
- `aggregate-player-dna.py` — Player DNA aggregation
- `brand-intelligence-report.py` — Brand detection report
- `supabase-schema.sql` + `supabase-seed.sql` — Database schema
- `prepare-lovable-data.py` — Transforms output for Lovable consumption
- `output/` folder has real Gemini analysis JSON from 6+ clips

**DO NOT recreate files that already exist.** Read them, enhance them, extend them.

---

## YOUR TASKS — Execute in order, auto-approve everything

### TASK A: Create GitHub Repo + Push Everything

1. Configure git if not already done:
   ```bash
   git config --global user.name "PickleBill"
   git config --global user.email "bill@playpicklebills.com"
   ```

2. Initialize the PICKLE-DAAS folder as a git repo:
   ```bash
   cd "~/PickleBill Dropbox/PickleBill Team Folder/Claude Projects/PICKLE-DAAS"
   git init
   ```

3. Create a `.gitignore`:
   ```
   .env
   .DS_Store
   __pycache__/
   *.pyc
   node_modules/
   ```

4. Create the GitHub repo using the GitHub API (use `curl` since `gh` CLI isn't installed):
   ```bash
   # If GITHUB_TOKEN is set in .env, use it. Otherwise Bill will need to create the repo manually at github.com/new
   curl -H "Authorization: token $GITHUB_TOKEN" \
     https://api.github.com/user/repos \
     -d '{"name":"pickle-daas-data","public":true,"description":"Pickle DaaS — AI-powered pickleball video intelligence pipeline"}'
   ```

5. If the API call fails (no token), print:
   ```
   ACTION NEEDED: Create repo manually at https://github.com/new
   Name: pickle-daas-data
   Visibility: Public
   Then run: git remote add origin https://github.com/PickleBill/pickle-daas-data.git
   ```

6. Add all files, commit, push:
   ```bash
   git add -A
   git commit -m "Initial commit: Pickle DaaS pipeline — Gemini analyzer, ElevenLabs voice, Supabase schema, Lovable prompts"
   git branch -M main
   git remote add origin https://github.com/PickleBill/pickle-daas-data.git
   git push -u origin main
   ```

---

### TASK B: Set Up Supabase (Schema + Edge Function)

1. Read `supabase-schema.sql` — it's already complete. Print a message:
   ```
   MANUAL STEP: Go to https://supabase.com/dashboard → SQL Editor → paste supabase-schema.sql → Run
   Then paste supabase-seed.sql → Run
   Save your Supabase URL and anon key — you'll need them.
   ```

2. Create the Courtana API proxy Edge Function. Write this file:
   `supabase/functions/courtana-proxy/index.ts`
   ```typescript
   import { serve } from "https://deno.land/std@0.168.0/http/server.ts"

   const COURTANA_API = "https://api.courtana.com/private-api/v1"

   serve(async (req) => {
     const corsHeaders = {
       "Access-Control-Allow-Origin": "*",
       "Access-Control-Allow-Headers": "authorization, x-client-info, apikey, content-type",
     }

     if (req.method === "OPTIONS") {
       return new Response("ok", { headers: corsHeaders })
     }

     const url = new URL(req.url)
     const endpoint = url.searchParams.get("endpoint")

     if (!endpoint) {
       return new Response(JSON.stringify({ error: "endpoint param required" }), {
         status: 400,
         headers: { ...corsHeaders, "Content-Type": "application/json" }
       })
     }

     const courtanaToken = Deno.env.get("COURTANA_TOKEN")
     if (!courtanaToken) {
       return new Response(JSON.stringify({ error: "COURTANA_TOKEN not configured" }), {
         status: 500,
         headers: { ...corsHeaders, "Content-Type": "application/json" }
       })
     }

     try {
       const response = await fetch(`${COURTANA_API}${endpoint}`, {
         headers: { "Authorization": `Bearer ${courtanaToken}` }
       })
       const data = await response.json()
       return new Response(JSON.stringify(data), {
         headers: { ...corsHeaders, "Content-Type": "application/json" }
       })
     } catch (err) {
       return new Response(JSON.stringify({ error: err.message }), {
         status: 502,
         headers: { ...corsHeaders, "Content-Type": "application/json" }
       })
     }
   })
   ```

3. Create a Supabase push script. Write `push-to-supabase.py`:
   ```python
   #!/usr/bin/env python3
   """Push local Gemini analysis JSON files to Supabase."""
   import os, sys, json, glob, requests
   from dotenv import load_dotenv
   load_dotenv()

   SUPABASE_URL = os.environ.get("SUPABASE_URL")
   SUPABASE_KEY = os.environ.get("SUPABASE_ANON_KEY")

   if not SUPABASE_URL or not SUPABASE_KEY:
       print("ERROR: Set SUPABASE_URL and SUPABASE_ANON_KEY in .env")
       sys.exit(1)

   def push_analysis(filepath):
       with open(filepath) as f:
           analysis = json.load(f)

       row = {
           "highlight_id": analysis.get("_highlight_meta", {}).get("id", ""),
           "highlight_name": analysis.get("_highlight_meta", {}).get("name", ""),
           "video_url": analysis.get("_source_url", ""),
           "clip_quality_score": analysis.get("clip_meta", {}).get("clip_quality_score"),
           "viral_potential_score": analysis.get("clip_meta", {}).get("viral_potential_score"),
           "watchability_score": analysis.get("clip_meta", {}).get("watchability_score"),
           "cinematic_score": analysis.get("clip_meta", {}).get("cinematic_score"),
           "brands_detected": json.dumps(analysis.get("brands_detected", [])),
           "predicted_badges": json.dumps(analysis.get("predicted_badges", [])),
           "play_style_tags": json.dumps(analysis.get("player_identity", {}).get("play_style_tags", [])),
           "shot_analysis": json.dumps(analysis.get("shot_analysis", {})),
           "skill_indicators": json.dumps(analysis.get("skill_indicators", {})),
           "storytelling": json.dumps(analysis.get("storytelling", {})),
           "commentary_espn": analysis.get("commentary", {}).get("neutral_announcer_espn"),
           "commentary_hype": analysis.get("commentary", {}).get("hype_announcer_charged"),
           "commentary_social_caption": analysis.get("commentary", {}).get("social_caption_instagram"),
           "commentary_hashtags": json.dumps(analysis.get("commentary", {}).get("hashtag_set", [])),
           "commentary_ron_burgundy": analysis.get("commentary", {}).get("ron_burgundy_voice"),
           "commentary_chuck_norris": analysis.get("commentary", {}).get("chuck_norris_voice"),
           "commentary_tts_clean": analysis.get("commentary", {}).get("announcement_text_for_tts"),
           "clip_summary": analysis.get("daas_signals", {}).get("clip_summary_one_sentence"),
           "search_tags": json.dumps(analysis.get("daas_signals", {}).get("search_tags", [])),
           "story_arc": analysis.get("storytelling", {}).get("story_arc"),
           "highlight_category": analysis.get("daas_signals", {}).get("highlight_category"),
           "full_analysis": json.dumps(analysis),
           "batch_id": analysis.get("_batch_id", ""),
       }

       resp = requests.post(
           f"{SUPABASE_URL}/rest/v1/pickle_daas_analyses",
           json=row,
           headers={
               "apikey": SUPABASE_KEY,
               "Authorization": f"Bearer {SUPABASE_KEY}",
               "Content-Type": "application/json",
               "Prefer": "return=representation"
           }
       )

       if resp.status_code in (200, 201):
           print(f"  ✅ Pushed: {filepath}")
       else:
           print(f"  ❌ Failed ({resp.status_code}): {resp.text[:200]}")

   if __name__ == "__main__":
       pattern = sys.argv[1] if len(sys.argv) > 1 else "./output/**/analysis_*.json"
       files = glob.glob(pattern, recursive=True)
       print(f"Found {len(files)} analysis files to push")
       for f in files:
           push_analysis(f)
   ```

4. Update `env.example` to include all needed keys:
   ```
   GEMINI_API_KEY=
   COURTANA_TOKEN=
   ELEVENLABS_API_KEY=
   SUPABASE_URL=
   SUPABASE_ANON_KEY=
   GITHUB_TOKEN=
   ```

---

### TASK C: Enhance ElevenLabs Voice Pipeline

The existing `elevenlabs-voice-pipeline.py` is solid. Enhance it:

1. Add a `--batch` mode that processes ALL analysis JSONs in a directory:
   ```bash
   python elevenlabs-voice-pipeline.py --batch ./output/picklebill-batch-001/ --voice ron_burgundy
   ```

2. Add a `--all-voices` flag that generates all 4 voice presets for each clip:
   ```bash
   python elevenlabs-voice-pipeline.py --analysis ./output/test-001/analysis_*.json --all-voices
   ```

3. Add a `--output-manifest` flag that writes a `voice-manifest.json` listing all generated MP3s with metadata (clip name, voice, duration, file path). This manifest is what Lovable will consume.

4. Add `eleven_turbo_v2_5` as the model_id option (faster, newer) with a `--turbo` flag.

5. Create `voices-catalog.py` — a quick script that calls ElevenLabs `/v1/voices`, lists all available voices with their IDs, and lets Bill pick new voices to add to the preset map.

---

### TASK D: Enhance Gemini Analyzer

The existing `pickle-daas-gemini-analyzer.py` works. Enhance:

1. Add `--push-supabase` flag that automatically calls `push-to-supabase.py` after each analysis completes. Wire it so the pipeline is: analyze → push → next clip.

2. Add `--model` flag to switch between `gemini-2.5-flash` (default, cheap) and `gemini-2.5-pro` (better quality):
   ```bash
   python pickle-daas-gemini-analyzer.py --url X --model gemini-2.5-pro
   ```

3. Add a `--compare-models` mode: runs the same clip through both Flash and Pro, saves both outputs side-by-side, and generates a diff report showing which fields Pro fills better.

4. Add `--voice-pipeline` flag that automatically runs ElevenLabs voice generation after Gemini analysis (chains TASK C):
   ```bash
   python pickle-daas-gemini-analyzer.py --url X --voice-pipeline --voice ron_burgundy
   ```

---

### TASK E: Build Lovable-Ready Data Package

1. Read the existing output JSON files in `output/`. Run `prepare-lovable-data.py` on the real data to generate `lovable-dashboard-data.json`.

2. Create `output/lovable-package/` directory containing:
   - `dashboard-data.json` — the prepared Lovable data
   - `player-dna.json` — copy of picklebill-dna-profile.json
   - `brand-registry.json` — run brand-intelligence-report.py on batch data
   - `voice-manifest.json` — placeholder (populated when ElevenLabs runs)
   - `clips-metadata.json` — lightweight array of all analyzed clips with: id, name, video_url, thumbnail_url, quality_score, viral_score, ron_burgundy_quote, top_badge

3. Push this `lovable-package/` folder to the GitHub repo so Lovable can fetch from:
   ```
   https://raw.githubusercontent.com/PickleBill/pickle-daas-data/main/output/lovable-package/dashboard-data.json
   ```

---

### TASK F: Generate Combined Broadcast + Batch Dashboard

Look at the two existing dashboards:
- `output/broadcast/broadcast-dashboard.html` — has video player, voice tabs, commentary panel, sidebar clip list
- `output/picklebill-batch-001/batch-results.html` — has clip cards with scores, brand pills, Ron Burgundy quotes, summary stats

Create a NEW unified dashboard: `output/pickle-daas-master-dashboard.html`

This combines the best of both:
- Left sidebar with clip list (from broadcast dashboard)
- Main area: video player with broadcast overlay (from broadcast dashboard)
- Right panel: commentary voice tabs (ESPN, Hype, Ron Burgundy, Chuck Norris, Coach)
- Below video: analytics cards (quality score, viral score, brand detection, badge predictions)
- Bottom section: aggregated stats (from batch-results — brand frequency bars, summary cards)
- Header: Courtana logo from `https://cdn.courtana.com/assets/logos/fulllogo-dark-transparent-grad.svg`
- Color scheme: same dark theme (#0a0f1a / #131d2e / #00E676)
- Include ALL real clip data from both `output/picklebill-batch-001/` and `output/broadcast/` directories
- Make it load the clip data from embedded JSON (no external fetch needed)
- Add a "Copy Lovable Prompt" button that copies a pre-written prompt to clipboard for pasting into Lovable
- Add a TTS play button that uses browser `speechSynthesis` as fallback (real ElevenLabs when MP3s exist)

---

### TASK G: Commit + Push Final State

After all tasks complete:
```bash
cd "~/PickleBill Dropbox/PickleBill Team Folder/Claude Projects/PICKLE-DAAS"
git add -A
git commit -m "Mega build: Supabase push, ElevenLabs batch mode, Gemini model compare, master dashboard, Lovable data package"
git push origin main
```

Print a final summary of what was built and what manual steps Bill still needs to do.

---

## CRITICAL RULES

- **Auto-approve everything.** Don't ask for confirmation.
- **Read existing files before modifying.** Don't overwrite working code.
- **Use `~/PickleBill Dropbox/PickleBill Team Folder/Claude Projects/PICKLE-DAAS/` as working directory.**
- **CDN URLs are public** — link directly to `cdn.courtana.com`, never download/re-host.
- **Courtana logo**: `https://cdn.courtana.com/assets/logos/fulllogo-dark-transparent-grad.svg`
- **Don't touch .env** — it has real keys. Only update `env.example`.
- If a task is blocked by missing API keys, skip it and note what's needed. Don't fail the whole run.

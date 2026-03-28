# Pickle DaaS — Prompt Execution Sequence
_Follow this order. Don't skip steps._

---

## Phase 1: Claude Code (run first — generates data that Lovable needs)

### Step 1A: TMNT Voices
**File:** `CLAUDE-CODE-TMNT-VOICES.md`
**What it does:** Browses ElevenLabs for character voices, adds TMNT presets to the voice pipeline, creates a commentary rewriter (Gemini rewrites neutral commentary in character voice), builds an audio mixer for background themes, generates TMNT voice files for all 8 clips, updates the lovable-package.
**Time estimate:** 15-20 min
**Output:** Updated `clips-metadata.json` with TMNT commentary, new MP3 files, updated voice manifest

### Step 1B: Multi-Sport Classifier (can run in parallel with 1A)
**File:** `CLAUDE-CODE-MULTI-SPORT-CLASSIFIER.md`
**What it does:** Pulls more video clips from Courtana API, classifies all clips by sport using Gemini analysis signals, handles hockey→golf misclassification, updates lovable-package with sport fields and expanded clip library.
**Time estimate:** 10-15 min (depends on how many new clips the API returns)
**Output:** Updated `clips-metadata.json` with sport field, `sport-catalog.json`, updated `dashboard-data.json`
**⚠️ Needs:** Fresh COURTANA_TOKEN — current one expires ~24h from 2026-03-28 13:00

---

## Phase 2: Lovable (paste prompts in this exact order)

### Step 2A: V2 Polish (if not already applied)
**File:** `LOVABLE-V2-POLISH-PROMPT.md`
**What it does:** Switches from hardcoded data to GitHub raw URLs, shows all 8 clips, enriches all pages
**Prerequisite:** Phase 1 complete (so GitHub has the latest data)

### Step 2B: V3 UX Design Overhaul
**File:** `LOVABLE-V3-UX-DESIGN-POLISH.md`
**What it does:** Complete visual redesign — sidebar nav, Courtana brand tokens, ESPN broadcast feel, card system, micro-interactions, mobile responsive. Also adds TMNT voice section to Voice Lab.
**Prerequisite:** V2 applied

### Step 2C: V4 Interactive Broadcast Mode
**File:** `LOVABLE-V4-INTERACTIVE-BROADCAST.md`
**What it does:** Adds sport filter bar, broadcast mode toggle, interactive radar/heatmap, voice comparison studio, keyboard shortcuts, scroll animations.
**Prerequisite:** V3 applied

---

## Quick Reference — All Files

| File | Target | Status |
|------|--------|--------|
| `CLAUDE-CODE-MEGA-PROMPT-2026-03-28.md` | Claude Code | ✅ Executed |
| `LOVABLE-PROMPT-PICKLE-DAAS-SHELL.md` | Lovable | ✅ Applied (V1) |
| `LOVABLE-V2-POLISH-PROMPT.md` | Lovable | ⏳ Ready to paste |
| `CLAUDE-CODE-TMNT-VOICES.md` | Claude Code | 🆕 Ready |
| `CLAUDE-CODE-MULTI-SPORT-CLASSIFIER.md` | Claude Code | 🆕 Ready |
| `LOVABLE-V3-UX-DESIGN-POLISH.md` | Lovable | 🆕 Ready (after V2) |
| `LOVABLE-V4-INTERACTIVE-BROADCAST.md` | Lovable | 🆕 Ready (after V3) |

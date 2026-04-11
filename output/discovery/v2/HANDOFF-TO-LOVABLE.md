# Handoff: Building the Discovery Dashboard in Lovable

## Quick Start (5 steps)

### Step 1: Create Project
- Open Lovable, create new project: **"pickle-daas-discovery"**

### Step 2: Paste Workspace Knowledge
- Go to Project Settings → Workspace Knowledge
- Paste contents from: `BILL-OS/lovable-workspace-knowledge.md`

### Step 3: Paste Prompt 11
- In the Lovable chat, paste: `lovable-prompts/11-discovery-intelligence-dashboard.md`
- This prompt builds a dark-themed discovery dashboard with:
  - Discovery cards with confidence badges
  - Verification proof section
  - Comparable pricing table
  - Revenue projection charts
  - Data quality flags

### Step 4: Swap Data
After the initial build with hardcoded data:
1. Download `output/lovable/discovery-v2-export.json`
2. Add it to the Lovable project's `public/` folder
3. Update data imports to point to the JSON file
4. See `output/lovable/LOVABLE-DATA-README.md` for field → component mapping

### Step 5: Connect Supabase (When Ready)
1. Follow `supabase/SUPABASE-SETUP-GUIDE.md` to deploy instance
2. Push data: `python supabase/push-analysis-to-db.py`
3. Replace static imports with Supabase queries (details in README)

## What the Dashboard Should Show

1. **Hero stats:** 191 clips, $0.005/clip, 11 discoveries
2. **Verification section:** 20-clip re-analysis results (the honesty flex)
3. **Discovery cards:** Ranked, color-coded by verification badge
4. **Comparable pricing:** Sportradar, StatsBomb, ShotTracker, Hudl
5. **Revenue projections:** 3-scenario chart
6. **Data quality:** Bias flags, venue distribution
7. **"What we don't know":** Honest gaps section

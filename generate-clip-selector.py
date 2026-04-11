#!/usr/bin/env python3
"""
Pickle DaaS — Clip Selector
==============================
Generates an interactive HTML page showing clip thumbnails from Courtana.
Bill can browse, click to select clips, and export a manifest for analysis.
No auth needed — uses anonymous endpoint.

USAGE:
  python generate-clip-selector.py              # First 200 clips
  python generate-clip-selector.py --count 500  # More clips
"""

import json
import glob
import os
import argparse
import requests
from datetime import datetime
from pathlib import Path

BASE_URL = "https://courtana.com"
ANON_ENDPOINT = "/app/anon-highlight-groups/"
OUTPUT_FILE = "output/clip-selector.html"


def get_already_analyzed():
    analyzed = set()
    for f in glob.glob("output/**/analysis_*.json", recursive=True):
        try:
            with open(f) as fh:
                data = json.load(fh)
            src = data.get("_source_url", "")
            if src:
                uuid = src.split("/")[-1].replace(".mp4", "")
                analyzed.add(uuid)
        except:
            continue
    return analyzed


def fetch_clips(count=200):
    """Fetch clip data from Courtana anon endpoint."""
    clips = []
    analyzed = get_already_analyzed()

    for page in range(1, 50):
        url = f"{BASE_URL}{ANON_ENDPOINT}"
        params = {"page": page, "page_size": 100}
        try:
            r = requests.get(url, params=params, headers={"Accept": "application/json"}, timeout=30)
            if r.status_code != 200:
                break
            data = r.json()
            results = data.get("results", [])
            if not results:
                break

            for group in results:
                highlights = group.get("highlights", [])
                highlight_file = group.get("highlight_file")
                if not highlight_file and highlights:
                    highlight_file = highlights[0].get("file")
                if not highlight_file:
                    continue

                uuid = highlight_file.split("/")[-1].replace(".mp4", "")
                thumbnail = group.get("thumbnail") or highlight_file.replace(".mp4", "_thumb.jpg")
                badges = group.get("badge_awards", [])
                badge_names = list(set(b.get("badge_name", "") for b in badges))
                players = list(set(b.get("profile_username", "") for b in badges if b.get("profile_username")))

                clips.append({
                    "uuid": uuid,
                    "file": highlight_file,
                    "thumbnail": thumbnail,
                    "badges": badge_names,
                    "players": players,
                    "badge_count": len(badges),
                    "analyzed": uuid in analyzed,
                    "random_id": group.get("random_id", ""),
                })

                if len(clips) >= count:
                    break

            if len(clips) >= count:
                break

            import time
            time.sleep(0.3)

        except Exception as e:
            print(f"Error page {page}: {e}")
            break

    return clips


def generate_selector(clips):
    """Generate interactive HTML clip selector."""
    analyzed_count = sum(1 for c in clips if c["analyzed"])
    new_count = len(clips) - analyzed_count

    clip_json = json.dumps(clips)

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Pickle DaaS — Clip Selector</title>
<style>
  * {{ margin:0; padding:0; box-sizing:border-box; }}
  body {{ background:#0a0a1a; color:#e0e0e0; font-family:'Inter','SF Pro',system-ui,sans-serif; padding:20px; }}
  .header {{ text-align:center; padding:20px; margin-bottom:20px; }}
  .header h1 {{ font-size:28px; font-weight:800; color:#fff; }}
  .toolbar {{ display:flex; gap:12px; justify-content:center; flex-wrap:wrap; margin-bottom:20px; padding:16px; background:#111122; border-radius:12px; }}
  .toolbar button {{ padding:8px 16px; border-radius:8px; border:none; cursor:pointer; font-size:13px; font-weight:600; transition:all 0.2s; }}
  .btn-primary {{ background:#00E676; color:#000; }}
  .btn-primary:hover {{ background:#00C853; }}
  .btn-secondary {{ background:#333; color:#fff; }}
  .btn-secondary:hover {{ background:#444; }}
  .btn-danger {{ background:#FF6B6B; color:#fff; }}
  .stats {{ display:flex; gap:20px; justify-content:center; margin-bottom:20px; font-size:13px; }}
  .stats span {{ color:#888; }}
  .stats strong {{ color:#00E676; }}
  .grid {{ display:grid; grid-template-columns:repeat(auto-fill,minmax(200px,1fr)); gap:12px; }}
  .clip {{ position:relative; border-radius:12px; overflow:hidden; cursor:pointer; transition:all 0.2s; border:2px solid transparent; }}
  .clip:hover {{ transform:scale(1.03); border-color:#4FC3F7; }}
  .clip.selected {{ border-color:#00E676; box-shadow:0 0 20px #00E67633; }}
  .clip.analyzed {{ opacity:0.5; }}
  .clip img {{ width:100%; height:140px; object-fit:cover; background:#222; display:block; }}
  .clip .overlay {{ position:absolute; bottom:0; left:0; right:0; background:linear-gradient(transparent,rgba(0,0,0,0.9)); padding:8px 10px; }}
  .clip .overlay .badges {{ font-size:10px; color:#FFD54F; }}
  .clip .overlay .player {{ font-size:11px; color:#4FC3F7; font-weight:600; }}
  .clip .check {{ position:absolute; top:8px; right:8px; width:24px; height:24px; border-radius:50%; background:#00E676; display:none; align-items:center; justify-content:center; font-size:14px; color:#000; font-weight:bold; }}
  .clip.selected .check {{ display:flex; }}
  .clip .analyzed-badge {{ position:absolute; top:8px; left:8px; background:#4FC3F7; color:#000; padding:2px 8px; border-radius:10px; font-size:10px; font-weight:600; }}
  .filters {{ display:flex; gap:8px; justify-content:center; margin-bottom:16px; flex-wrap:wrap; }}
  .filters button {{ padding:4px 12px; border-radius:16px; border:1px solid #333; background:transparent; color:#888; cursor:pointer; font-size:12px; }}
  .filters button.active {{ border-color:#00E676; color:#00E676; background:#00E67622; }}
  #export-panel {{ display:none; position:fixed; bottom:0; left:0; right:0; background:#1a1a2e; padding:16px 24px; border-top:2px solid #00E676; z-index:100; }}
  #export-panel .content {{ max-width:800px; margin:0 auto; display:flex; align-items:center; justify-content:space-between; }}
</style>
</head>
<body>

<div class="header">
    <h1>Clip Selector</h1>
    <p style="color:#888;font-size:13px;margin-top:4px">Browse Courtana clips. Click to select. Export manifest for Gemini analysis.</p>
</div>

<div class="stats">
    <span>Total: <strong>{len(clips)}</strong></span>
    <span>Already Analyzed: <strong style="color:#4FC3F7">{analyzed_count}</strong></span>
    <span>New: <strong>{new_count}</strong></span>
    <span>Selected: <strong id="selected-count">0</strong></span>
</div>

<div class="filters">
    <button class="active" onclick="filterClips('all')">All ({len(clips)})</button>
    <button onclick="filterClips('new')">New Only ({new_count})</button>
    <button onclick="filterClips('analyzed')">Analyzed ({analyzed_count})</button>
    <button onclick="filterClips('badged')">Has Badges ({sum(1 for c in clips if c['badge_count'] > 0)})</button>
</div>

<div class="toolbar">
    <button class="btn-primary" onclick="selectAllNew()">Select All New</button>
    <button class="btn-secondary" onclick="selectTop(50)">Select Top 50 New</button>
    <button class="btn-secondary" onclick="selectBadged()">Select All Badged</button>
    <button class="btn-danger" onclick="clearSelection()">Clear Selection</button>
    <button class="btn-primary" onclick="exportManifest()">Export Manifest</button>
</div>

<div class="grid" id="clip-grid"></div>

<div id="export-panel">
    <div class="content">
        <div>
            <strong id="export-count">0</strong> clips selected for analysis
            <span style="color:#888;font-size:12px;margin-left:8px">Est. cost: $<span id="export-cost">0.00</span></span>
        </div>
        <button class="btn-primary" onclick="downloadManifest()">Download manifest.json</button>
    </div>
</div>

<script>
const clips = {clip_json};
const selected = new Set();

function renderClips(filter = 'all') {{
    const grid = document.getElementById('clip-grid');
    grid.innerHTML = '';
    clips.forEach((clip, i) => {{
        if (filter === 'new' && clip.analyzed) return;
        if (filter === 'analyzed' && !clip.analyzed) return;
        if (filter === 'badged' && clip.badge_count === 0) return;

        const div = document.createElement('div');
        div.className = 'clip' + (selected.has(clip.uuid) ? ' selected' : '') + (clip.analyzed ? ' analyzed' : '');
        div.onclick = () => toggleClip(clip.uuid, div);
        div.innerHTML = `
            <img src="${{clip.thumbnail}}" onerror="this.src='data:image/svg+xml,<svg xmlns=%22http://www.w3.org/2000/svg%22 width=%22200%22 height=%22140%22><rect fill=%22%23222%22 width=%22200%22 height=%22140%22/><text x=%2250%25%22 y=%2250%25%22 fill=%22%23666%22 text-anchor=%22middle%22 dy=%22.3em%22>No thumb</text></svg>'" loading="lazy"/>
            <div class="check">✓</div>
            ${{clip.analyzed ? '<div class="analyzed-badge">✓ Done</div>' : ''}}
            <div class="overlay">
                ${{clip.players.length ? '<div class="player">' + clip.players.join(', ') + '</div>' : ''}}
                ${{clip.badges.length ? '<div class="badges">' + clip.badges.slice(0,2).join(' · ') + '</div>' : ''}}
            </div>
        `;
        grid.appendChild(div);
    }});
}}

function toggleClip(uuid, el) {{
    if (selected.has(uuid)) {{
        selected.delete(uuid);
        el.classList.remove('selected');
    }} else {{
        selected.add(uuid);
        el.classList.add('selected');
    }}
    updateCount();
}}

function updateCount() {{
    document.getElementById('selected-count').textContent = selected.size;
    document.getElementById('export-count').textContent = selected.size;
    document.getElementById('export-cost').textContent = (selected.size * 0.0054).toFixed(2);
    document.getElementById('export-panel').style.display = selected.size > 0 ? 'block' : 'none';
}}

function selectAllNew() {{
    clips.forEach(c => {{ if (!c.analyzed) selected.add(c.uuid); }});
    renderClips('new');
    updateCount();
}}

function selectTop(n) {{
    let count = 0;
    clips.forEach(c => {{ if (!c.analyzed && count < n) {{ selected.add(c.uuid); count++; }} }});
    renderClips();
    updateCount();
}}

function selectBadged() {{
    clips.forEach(c => {{ if (c.badge_count > 0 && !c.analyzed) selected.add(c.uuid); }});
    renderClips();
    updateCount();
}}

function clearSelection() {{
    selected.clear();
    renderClips();
    updateCount();
}}

function filterClips(f) {{
    document.querySelectorAll('.filters button').forEach(b => b.classList.remove('active'));
    event.target.classList.add('active');
    renderClips(f);
}}

function exportManifest() {{
    const manifest = clips.filter(c => selected.has(c.uuid)).map(c => ({{ file: c.file, uuid: c.uuid, badges: c.badges, players: c.players }}));
    const blob = new Blob([JSON.stringify(manifest, null, 2)], {{ type: 'application/json' }});
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url; a.download = 'selected-clips-manifest.json'; a.click();
}}

function downloadManifest() {{ exportManifest(); }}

renderClips();
</script>
</body>
</html>"""
    return html


def main():
    parser = argparse.ArgumentParser(description="Clip Selector Generator")
    parser.add_argument("--count", type=int, default=200, help="Number of clips to show")
    parser.add_argument("--output", default=OUTPUT_FILE)
    args = parser.parse_args()

    print(f"{'='*60}")
    print(f"Pickle DaaS — Clip Selector")
    print(f"{'='*60}")

    print(f"\nFetching {args.count} clips from Courtana...")
    clips = fetch_clips(args.count)
    print(f"  Got {len(clips)} clips ({sum(1 for c in clips if c['analyzed'])} already analyzed)")

    print(f"\nGenerating selector page...")
    html = generate_selector(clips)
    with open(args.output, "w") as f:
        f.write(html)
    print(f"  Saved: {args.output}")


if __name__ == "__main__":
    main()

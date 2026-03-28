# Claude Code — Multi-Sport Video Classifier + Expanded Clip Library
_Paste this into Claude Code. All tasks auto-approve. Read existing files before modifying._

---

## Context
Bill wants to:
1. Pull MORE videos from the Courtana CDN research repository
2. Classify them by sport (pickleball, hockey, golf, tennis, etc.)
3. Gemini analysis already outputs sport-related signals — use those to auto-classify
4. Known issue: "Sometimes hockey is golf" — Gemini occasionally misclassifies hockey as golf. Build a correction layer.

Currently we have 8 clips, all pickleball from PickleBill's account. We need to expand to other sports/users on the Courtana platform.

---

## Task A — Pull More Video Clips from Courtana API

The Courtana API can return highlight clips across all users/sports. Fetch a broader set:

```python
#!/usr/bin/env python3
"""
fetch-clips-expanded.py — Pull highlight clips from Courtana API across multiple sports/users.
Outputs a clips catalog organized by sport.
"""

import os
import json
import requests
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

COURTANA_API = "https://api.courtana.com/private-api/v1"
TOKEN = os.getenv("COURTANA_TOKEN")

if not TOKEN:
    print("ERROR: COURTANA_TOKEN not set in .env")
    exit(1)

headers = {
    "Authorization": f"Bearer {TOKEN}",
    "Content-Type": "application/json",
}


def fetch_highlights(page=1, page_size=50):
    """Fetch highlight clips from the API."""
    url = f"{COURTANA_API}/highlights/"
    params = {
        "page": page,
        "page_size": page_size,
        "ordering": "-created_at",
    }
    resp = requests.get(url, headers=headers, params=params, timeout=30)
    if resp.status_code != 200:
        print(f"API error: {resp.status_code} — {resp.text[:200]}")
        return []
    data = resp.json()
    results = data.get("results", data) if isinstance(data, dict) else data
    return results


def fetch_all_highlights(max_pages=5):
    """Paginate through all available highlights."""
    all_clips = []
    for page in range(1, max_pages + 1):
        print(f"Fetching page {page}...")
        clips = fetch_highlights(page=page)
        if not clips:
            break
        all_clips.extend(clips)
        print(f"  Got {len(clips)} clips (total: {len(all_clips)})")
        if len(clips) < 50:
            break
    return all_clips


def main():
    print("Fetching expanded clip library from Courtana API...")
    all_clips = fetch_all_highlights(max_pages=10)

    # Save raw catalog
    os.makedirs("output/expanded-clips", exist_ok=True)
    catalog_path = "output/expanded-clips/full-catalog.json"
    with open(catalog_path, "w") as f:
        json.dump(all_clips, f, indent=2)
    print(f"\nSaved {len(all_clips)} clips to {catalog_path}")

    # Extract video URLs for Gemini analysis
    video_urls = []
    for clip in all_clips:
        file_url = clip.get("file", "")
        if file_url and file_url.endswith(".mp4"):
            video_urls.append({
                "id": clip.get("id", ""),
                "name": clip.get("name", "Unknown"),
                "url": file_url,
                "created_at": clip.get("created_at", ""),
                "participants": [p.get("username", "") for p in clip.get("participants", [])],
            })

    urls_path = "output/expanded-clips/video-urls-for-analysis.json"
    with open(urls_path, "w") as f:
        json.dump(video_urls, f, indent=2)
    print(f"Extracted {len(video_urls)} video URLs to {urls_path}")


if __name__ == "__main__":
    main()
```

## Task B — Sport Classifier Script

Create `sport-classifier.py` — reads Gemini analysis JSON and classifies by sport:

```python
#!/usr/bin/env python3
"""
sport-classifier.py — Classifies clips by sport using Gemini analysis output.
Handles known misclassifications (hockey→golf) with correction rules.

Usage:
  python sport-classifier.py --batch ./output/ --output output/sport-catalog.json
"""

import os
import json
import glob
import argparse
import re

# Known misclassification corrections
# Gemini sometimes tags hockey videos as golf (both have stick-like equipment)
CORRECTION_RULES = {
    "hockey_as_golf": {
        "if_classified": "golf",
        "check_signals": ["ice", "rink", "puck", "stick", "hockey", "skate", "goal", "net", "boards", "slapshot", "face-off"],
        "reclassify_to": "hockey",
        "min_signal_matches": 2,
    },
}

# Sport detection from analysis JSON signals
SPORT_SIGNALS = {
    "pickleball": {
        "keywords": ["pickleball", "paddle", "dink", "kitchen", "non-volley", "serve", "third shot", "rally", "net", "joola", "crbn"],
        "equipment": ["paddle"],
        "court_markers": ["kitchen line", "non-volley zone", "pickleball court"],
    },
    "tennis": {
        "keywords": ["tennis", "racket", "racquet", "baseline", "forehand", "backhand", "volley", "ace", "deuce", "love"],
        "equipment": ["racket", "racquet"],
        "court_markers": ["tennis court", "clay", "hard court", "grass court"],
    },
    "hockey": {
        "keywords": ["hockey", "puck", "stick", "ice", "rink", "goal", "slapshot", "boards", "face-off", "skate"],
        "equipment": ["hockey stick", "puck"],
        "court_markers": ["ice rink", "boards", "blue line", "red line"],
    },
    "golf": {
        "keywords": ["golf", "club", "green", "fairway", "tee", "bunker", "par", "birdie", "putt", "swing"],
        "equipment": ["golf club", "golf ball"],
        "court_markers": ["golf course", "green", "fairway"],
    },
    "basketball": {
        "keywords": ["basketball", "hoop", "dribble", "layup", "dunk", "three-pointer", "free throw", "court"],
        "equipment": ["basketball"],
        "court_markers": ["basketball court", "free throw line", "three point line"],
    },
    "soccer": {
        "keywords": ["soccer", "football", "goal", "kick", "field", "penalty", "corner kick"],
        "equipment": ["soccer ball", "football"],
        "court_markers": ["soccer field", "penalty area", "goal box"],
    },
}


def extract_text_signals(analysis: dict) -> str:
    """Extract all text content from analysis for sport detection."""
    texts = []

    # Commentary
    commentary = analysis.get("commentary", {})
    for key, val in commentary.items():
        if isinstance(val, str):
            texts.append(val)

    # Storytelling
    story = analysis.get("storytelling", {})
    texts.append(str(story.get("narrative_arc_summary", "")))

    # Shot analysis
    shots = analysis.get("shot_analysis", {})
    for shot in shots.get("shots", []):
        texts.append(str(shot.get("shot_type", "")))
    texts.append(str(shots.get("dominant_shot_type", "")))

    # Skill indicators
    skills = analysis.get("skill_indicators", {})
    texts.extend([str(t) for t in skills.get("play_style_tags", [])])
    texts.append(str(skills.get("signature_move_detected", "")))

    # DaaS signals
    daas = analysis.get("daas_signals", {})
    texts.extend([str(t) for t in daas.get("search_tags", [])])
    texts.extend([str(t) for t in daas.get("content_use_cases", [])])
    texts.append(str(daas.get("clip_summary_one_sentence", "")))

    # Brand detection
    brands = analysis.get("brand_detection", {})
    for brand in brands.get("brands", []):
        texts.append(str(brand.get("brand_name", "")))
        texts.append(str(brand.get("category", "")))

    return " ".join(texts).lower()


def classify_sport(analysis: dict) -> dict:
    """Classify the sport of a clip based on Gemini analysis signals."""
    text = extract_text_signals(analysis)

    scores = {}
    for sport, signals in SPORT_SIGNALS.items():
        score = 0
        matched_keywords = []

        for kw in signals["keywords"]:
            count = text.count(kw.lower())
            if count > 0:
                score += count
                matched_keywords.append(kw)

        for eq in signals.get("equipment", []):
            if eq.lower() in text:
                score += 3  # Equipment is a strong signal
                matched_keywords.append(f"[equip]{eq}")

        for cm in signals.get("court_markers", []):
            if cm.lower() in text:
                score += 5  # Court markers are the strongest signal
                matched_keywords.append(f"[court]{cm}")

        if score > 0:
            scores[sport] = {"score": score, "keywords": matched_keywords}

    if not scores:
        return {"sport": "unknown", "confidence": "none", "scores": {}}

    # Pick top sport
    top_sport = max(scores, key=lambda s: scores[s]["score"])
    top_score = scores[top_sport]["score"]

    # Apply correction rules
    for rule_name, rule in CORRECTION_RULES.items():
        if top_sport == rule["if_classified"]:
            signal_matches = sum(1 for s in rule["check_signals"] if s in text)
            if signal_matches >= rule["min_signal_matches"]:
                print(f"  CORRECTION: {top_sport} → {rule['reclassify_to']} (matched {signal_matches} signals for {rule_name})")
                top_sport = rule["reclassify_to"]

    # Confidence levels
    if top_score >= 10:
        confidence = "high"
    elif top_score >= 5:
        confidence = "medium"
    else:
        confidence = "low"

    return {
        "sport": top_sport,
        "confidence": confidence,
        "top_score": top_score,
        "all_scores": {k: v["score"] for k, v in scores.items()},
        "matched_keywords": scores.get(top_sport, {}).get("keywords", []),
    }


def main():
    parser = argparse.ArgumentParser(description="Classify clips by sport")
    parser.add_argument("--batch", required=True, help="Directory to scan for analysis JSON files")
    parser.add_argument("--output", default="output/sport-catalog.json", help="Output catalog path")
    args = parser.parse_args()

    files = sorted(glob.glob(os.path.join(args.batch, "**/analysis_*.json"), recursive=True))
    print(f"Found {len(files)} analysis files")

    catalog = {"sports": {}, "clips": [], "generated_at": None}

    for f in files:
        with open(f) as fp:
            analysis = json.load(fp)

        clip_id = os.path.basename(f).split("_")[1][:8]
        source_url = analysis.get("_source_url", "")

        classification = classify_sport(analysis)
        sport = classification["sport"]

        entry = {
            "clip_id": clip_id,
            "source_url": source_url,
            "analysis_file": f,
            "sport": sport,
            "confidence": classification["confidence"],
            "score": classification["top_score"],
            "keywords": classification["matched_keywords"],
        }

        catalog["clips"].append(entry)

        if sport not in catalog["sports"]:
            catalog["sports"][sport] = {"count": 0, "clips": []}
        catalog["sports"][sport]["count"] += 1
        catalog["sports"][sport]["clips"].append(clip_id)

        print(f"  {clip_id}: {sport} (confidence: {classification['confidence']}, score: {classification['top_score']})")

    from datetime import datetime, timezone
    catalog["generated_at"] = datetime.now(timezone.utc).isoformat()
    catalog["total_clips"] = len(catalog["clips"])
    catalog["sport_breakdown"] = {k: v["count"] for k, v in catalog["sports"].items()}

    os.makedirs(os.path.dirname(args.output), exist_ok=True)
    with open(args.output, "w") as f:
        json.dump(catalog, f, indent=2)

    print(f"\n{'='*60}")
    print(f"Sport Classification Results:")
    for sport, data in sorted(catalog["sports"].items()):
        print(f"  {sport}: {data['count']} clips")
    print(f"Total: {len(catalog['clips'])} clips → {args.output}")


if __name__ == "__main__":
    main()
```

## Task C — Run Gemini Analysis on Expanded Clips

Use the existing `gemini-analyzer.py` (or `gemini-video-analyzer.py`) to process new clips:

```bash
# First, fetch expanded clips
python fetch-clips-expanded.py

# Check how many new clips we have
python -c "
import json
with open('output/expanded-clips/video-urls-for-analysis.json') as f:
    clips = json.load(f)

# Filter out clips we've already analyzed
import glob
existing = set()
for af in glob.glob('output/**/analysis_*.json', recursive=True):
    parts = af.split('analysis_')[1]
    clip_id = parts[:8]
    existing.add(clip_id)

new_clips = [c for c in clips if not any(e in c['url'] for e in existing)]
print(f'Already analyzed: {len(existing)} clips')
print(f'New clips to analyze: {len(new_clips)}')
print(f'Total available: {len(clips)}')

# Save the new-only list
with open('output/expanded-clips/new-clips-to-analyze.json', 'w') as f:
    json.dump(new_clips, f, indent=2)
"

# Run Gemini on new clips (batch mode, limit to first 20 to conserve API credits)
# The analyzer should already exist — check which script name is being used
ls gemini*.py

# Run batch analysis on new clips
python gemini-video-analyzer.py --batch output/expanded-clips/new-clips-to-analyze.json --limit 20 --output-dir output/expanded-clips/analyses/
```

## Task D — Classify All Clips by Sport

```bash
# Run sport classifier on ALL analyzed clips (existing + new)
python sport-classifier.py --batch ./output/ --output output/sport-catalog.json

# Generate a lovable-package update with sport classifications
python -c "
import json

with open('output/sport-catalog.json') as f:
    catalog = json.load(f)

with open('output/lovable-package/clips-metadata.json') as f:
    clips = json.load(f)

# Add sport field to existing clips
for clip in clips:
    for entry in catalog['clips']:
        if clip['id'] == entry['clip_id']:
            clip['sport'] = entry['sport']
            clip['sport_confidence'] = entry['confidence']
            break
    else:
        clip['sport'] = 'pickleball'  # Default for existing clips
        clip['sport_confidence'] = 'high'

# Add new clips from expanded analysis
import glob, os
existing_ids = {c['id'] for c in clips}
for entry in catalog['clips']:
    if entry['clip_id'] not in existing_ids and entry['source_url']:
        # Load the analysis to get commentary
        try:
            with open(entry['analysis_file']) as f:
                analysis = json.load(f)
            commentary = analysis.get('commentary', {})
            storytelling = analysis.get('storytelling', {})
            brands = [b['brand_name'] for b in analysis.get('brand_detection', {}).get('brands', [])]

            new_clip = {
                'id': entry['clip_id'],
                'name': analysis.get('daas_signals', {}).get('clip_summary_one_sentence', f'Clip {entry[\"clip_id\"]}')[:50],
                'video_url': entry['source_url'],
                'thumbnail_url': '',
                'quality_score': analysis.get('clip_meta', {}).get('clip_quality_score', 5),
                'viral_score': analysis.get('clip_meta', {}).get('viral_potential_score', 3),
                'story_arc': storytelling.get('story_arc', 'unknown'),
                'ron_burgundy_quote': commentary.get('ron_burgundy_voice', ''),
                'top_badge': None,
                'brands': brands,
                'caption': commentary.get('social_media_caption', ''),
                'sport': entry['sport'],
                'sport_confidence': entry['confidence'],
            }
            clips.append(new_clip)
        except Exception as e:
            print(f'  Error processing {entry[\"clip_id\"]}: {e}')

with open('output/lovable-package/clips-metadata.json', 'w') as f:
    json.dump(clips, f, indent=2)

print(f'Updated clips-metadata.json: {len(clips)} total clips')
print(f'Sport breakdown: {catalog.get(\"sport_breakdown\", {})}')
"
```

## Task E — Update Dashboard Data with Sport Breakdown

```bash
python -c "
import json

with open('output/lovable-package/dashboard-data.json') as f:
    dashboard = json.load(f)

with open('output/sport-catalog.json') as f:
    catalog = json.load(f)

with open('output/lovable-package/clips-metadata.json') as f:
    clips = json.load(f)

# Update KPIs
dashboard['kpis']['clips_analyzed'] = len(clips)

# Add sport breakdown to analytics
dashboard['analytics']['sport_breakdown'] = catalog.get('sport_breakdown', {})
dashboard['analytics']['total_clips_analyzed'] = len(clips)

# Recalculate averages
if clips:
    dashboard['analytics']['avg_quality_score'] = round(sum(c.get('quality_score', 0) for c in clips) / len(clips), 1)
    dashboard['analytics']['avg_viral_score'] = round(sum(c.get('viral_score', 0) for c in clips) / len(clips), 1)
    dashboard['kpis']['avg_quality_score'] = dashboard['analytics']['avg_quality_score']
    dashboard['kpis']['avg_viral_score'] = dashboard['analytics']['avg_viral_score']

with open('output/lovable-package/dashboard-data.json', 'w') as f:
    json.dump(dashboard, f, indent=2)

print('Updated dashboard-data.json with sport breakdown')
print(f'  Total clips: {len(clips)}')
print(f'  Sport breakdown: {catalog.get(\"sport_breakdown\", {})}')
"
```

## Task F — Push to GitHub

```bash
git add -A
git commit -m "feat: Multi-sport video classifier + expanded clip library

- fetch-clips-expanded.py: Pulls all available clips from Courtana API
- sport-classifier.py: Auto-classifies clips by sport using Gemini analysis signals
- Hockey-as-golf correction rule for known Gemini misclassification
- Expanded clips-metadata.json with sport field
- Dashboard data updated with sport breakdown analytics"

git push origin main
```

---

## Critical Rules
- Auto-approve everything.
- The COURTANA_TOKEN expires ~24h — if it fails, log the error and continue with what we have.
- Don't delete or overwrite existing analysis files — only add new ones.
- The hockey→golf correction is important: Gemini sees stick-like equipment and sometimes calls hockey "golf."
- Keep all existing 8 pickleball clips intact in clips-metadata.json — new clips are additive.
- If the Gemini API quota is limited, process the top 20 clips by recency first.

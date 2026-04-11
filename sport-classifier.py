#!/usr/bin/env python3
"""sport-classifier.py — Classifies clips by sport using Gemini analysis signals."""
import os, json, glob, argparse, re
from datetime import datetime, timezone

CORRECTION_RULES = {
    "hockey_as_golf": {
        "if_classified": "golf",
        "check_signals": ["ice", "rink", "puck", "stick", "hockey", "skate", "goal", "net", "boards", "slapshot", "face-off"],
        "reclassify_to": "hockey",
        "min_signal_matches": 2,
    },
}

SPORT_SIGNALS = {
    "pickleball": {
        "keywords": ["pickleball", "paddle", "dink", "kitchen", "non-volley", "serve", "third shot", "rally", "joola", "crbn"],
        "equipment": ["paddle"],
        "court_markers": ["kitchen line", "non-volley zone", "pickleball court"],
    },
    "tennis": {
        "keywords": ["tennis", "racket", "racquet", "baseline", "forehand", "backhand", "volley", "ace", "deuce"],
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
        "keywords": ["basketball", "hoop", "dribble", "layup", "dunk", "three-pointer", "free throw"],
        "equipment": ["basketball"],
        "court_markers": ["basketball court", "free throw line", "three point line"],
    },
    "soccer": {
        "keywords": ["soccer", "football", "goal", "kick", "field", "penalty", "corner kick"],
        "equipment": ["soccer ball", "football"],
        "court_markers": ["soccer field", "penalty area", "goal box"],
    },
}

def extract_text_signals(analysis):
    texts = []
    commentary = analysis.get("commentary", {})
    for key, val in commentary.items():
        if isinstance(val, str):
            texts.append(val)
    story = analysis.get("storytelling", {})
    texts.append(str(story.get("narrative_arc_summary", "")))
    shots = analysis.get("shot_analysis", {})
    for shot in shots.get("shots", []):
        texts.append(str(shot.get("shot_type", "")))
    texts.append(str(shots.get("dominant_shot_type", "")))
    skills = analysis.get("skill_indicators", {})
    texts.extend([str(t) for t in skills.get("play_style_tags", [])])
    daas = analysis.get("daas_signals", {})
    texts.extend([str(t) for t in daas.get("search_tags", [])])
    texts.append(str(daas.get("clip_summary_one_sentence", "")))
    brands = analysis.get("brand_detection", {})
    for brand in brands.get("brands", []):
        texts.append(str(brand.get("brand_name", "")))
        texts.append(str(brand.get("category", "")))
    return " ".join(texts).lower()

def classify_sport(analysis):
    text = extract_text_signals(analysis)
    scores = {}
    for sport, signals in SPORT_SIGNALS.items():
        score = 0
        matched = []
        for kw in signals["keywords"]:
            count = text.count(kw.lower())
            if count > 0:
                score += count
                matched.append(kw)
        for eq in signals.get("equipment", []):
            if eq.lower() in text:
                score += 3
                matched.append(f"[equip]{eq}")
        for cm in signals.get("court_markers", []):
            if cm.lower() in text:
                score += 5
                matched.append(f"[court]{cm}")
        if score > 0:
            scores[sport] = {"score": score, "keywords": matched}
    if not scores:
        return {"sport": "unknown", "confidence": "none", "top_score": 0, "all_scores": {}, "matched_keywords": []}
    top_sport = max(scores, key=lambda s: scores[s]["score"])
    top_score = scores[top_sport]["score"]
    for rule_name, rule in CORRECTION_RULES.items():
        if top_sport == rule["if_classified"]:
            signal_matches = sum(1 for s in rule["check_signals"] if s in text)
            if signal_matches >= rule["min_signal_matches"]:
                print(f"  CORRECTION: {top_sport} → {rule['reclassify_to']} ({signal_matches} signals for {rule_name})")
                top_sport = rule["reclassify_to"]
    confidence = "high" if top_score >= 10 else "medium" if top_score >= 5 else "low"
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
        fname = os.path.basename(f)
        parts = fname.replace("analysis_", "")
        clip_id = parts[:8] if len(parts) >= 8 else fname[:8]
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
    catalog["generated_at"] = datetime.now(timezone.utc).isoformat()
    catalog["total_clips"] = len(catalog["clips"])
    catalog["sport_breakdown"] = {k: v["count"] for k, v in catalog["sports"].items()}
    os.makedirs(os.path.dirname(args.output) if os.path.dirname(args.output) else ".", exist_ok=True)
    with open(args.output, "w") as f:
        json.dump(catalog, f, indent=2)
    print(f"\nSport Classification Results:")
    for sport, data in sorted(catalog["sports"].items()):
        print(f"  {sport}: {data['count']} clips")
    print(f"Total: {len(catalog['clips'])} clips → {args.output}")

if __name__ == "__main__":
    main()

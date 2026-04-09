#!/usr/bin/env python3
"""
Pickle DaaS — Badge Analytics Warehouse
=========================================
Central analytics DB that cross-references our model's badge predictions
against Courtana's ground truth badge awards. This is the reinforcement
learning loop: see what we get right, what we miss, and why.

USAGE:
  python tools/badge-warehouse.py ingest      # Load all data into SQLite
  python tools/badge-warehouse.py analyze     # Cross-reference predictions vs ground truth
  python tools/badge-warehouse.py dashboard   # Generate HTML analytics dashboard
  python tools/badge-warehouse.py feedback    # Generate prompt reinforcement patch
  python tools/badge-warehouse.py all         # Run everything in sequence

REQUIRES:
  - output/courtana-ground-truth/ (run tools/fetch-courtana-badges.py first)
  - output/*/analysis_*.json (existing Gemini analysis outputs)

OUTPUT:
  - output/badge-analytics.db (SQLite warehouse)
  - output/badge-analytics-dashboard.html
  - prompts/badge-reinforcement-patch.md
"""

import os
import sys
import json
import re
import sqlite3
import glob
import argparse
from datetime import datetime
from pathlib import Path
from collections import defaultdict, Counter

DB_PATH = "output/badge-analytics.db"
GROUND_TRUTH_DIR = "output/courtana-ground-truth"
ANALYSIS_DIRS = [
    "output/batch-30-daas",
    "output/picklebill-batch-001",
    "output/picklebill-batch-20260410",
    "output/test-001",
    "output/broadcast",
    "output/v1.2-reprocess",
    "output/badged-clips-analysis",
    "output/v1.3-badged-analysis",
]
BADGED_CLIPS_DIR = "output/badged-clips"


def get_db():
    """Open or create the SQLite database with schema."""
    Path(os.path.dirname(DB_PATH)).mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")

    conn.executescript("""
        CREATE TABLE IF NOT EXISTS badges (
            slug            TEXT PRIMARY KEY,
            name            TEXT NOT NULL,
            description     TEXT,
            criteria        TEXT,
            sport           TEXT,
            tier            TEXT,
            type            TEXT,
            rarity          REAL,
            file_url        TEXT,
            thumbnail_url   TEXT,
            fetched_at      TEXT NOT NULL DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS ground_truth_awards (
            id                  INTEGER PRIMARY KEY AUTOINCREMENT,
            badge_name          TEXT NOT NULL,
            badge_slug          TEXT NOT NULL,
            badge_tier          TEXT,
            profile_username    TEXT,
            highlight_group_id  TEXT,
            highlight_file_url  TEXT,
            asset_uuid          TEXT,
            gemini_reason       TEXT,
            awarded_at          TEXT,
            fetched_at          TEXT NOT NULL DEFAULT (datetime('now')),
            UNIQUE(badge_slug, highlight_group_id, profile_username)
        );

        CREATE TABLE IF NOT EXISTS predictions (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            clip_id         TEXT NOT NULL,
            clip_id_short   TEXT NOT NULL,
            batch           TEXT,
            video_url       TEXT,
            asset_uuid      TEXT,
            badge_name      TEXT NOT NULL,
            confidence      TEXT,
            reasoning       TEXT,
            prompt_version  TEXT,
            analyzed_at     TEXT,
            UNIQUE(clip_id, badge_name)
        );

        CREATE TABLE IF NOT EXISTS cross_references (
            id                  INTEGER PRIMARY KEY AUTOINCREMENT,
            clip_id             TEXT,
            asset_uuid          TEXT,
            video_url           TEXT,
            highlight_group_id  TEXT,
            predicted_badge     TEXT,
            ground_truth_badge  TEXT,
            match_type          TEXT NOT NULL,
            predicted_confidence TEXT,
            predicted_reasoning TEXT,
            courtana_reasoning  TEXT,
            created_at          TEXT NOT NULL DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS prompt_feedback (
            id                  INTEGER PRIMARY KEY AUTOINCREMENT,
            badge_slug          TEXT,
            feedback_type       TEXT NOT NULL,
            description         TEXT NOT NULL,
            our_reasoning       TEXT,
            courtana_reasoning  TEXT,
            suggested_prompt_edit TEXT,
            severity            TEXT DEFAULT 'medium',
            resolved            INTEGER DEFAULT 0,
            created_at          TEXT NOT NULL DEFAULT (datetime('now'))
        );

        -- Map asset UUIDs (from anon endpoint) to highlight group IDs
        CREATE TABLE IF NOT EXISTS uuid_group_map (
            asset_uuid          TEXT PRIMARY KEY,
            highlight_group_id  TEXT NOT NULL
        );

        CREATE INDEX IF NOT EXISTS idx_gt_asset ON ground_truth_awards(asset_uuid);
        CREATE INDEX IF NOT EXISTS idx_gt_group ON ground_truth_awards(highlight_group_id);
        CREATE INDEX IF NOT EXISTS idx_pred_asset ON predictions(asset_uuid);
        CREATE INDEX IF NOT EXISTS idx_xref_asset ON cross_references(asset_uuid);
        CREATE INDEX IF NOT EXISTS idx_uuid_group ON uuid_group_map(highlight_group_id);
    """)

    return conn


def extract_asset_uuid(url):
    """Extract the asset UUID from a CDN URL.
    Example: https://cdn.courtana.com/.../b18ca113-c853-4811-b486-ab7f56472851.mp4
    Returns: b18ca113-c853-4811-b486-ab7f56472851
    """
    if not url:
        return None
    match = re.search(r'([0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})\.\w+$', url)
    return match.group(1) if match else None


def normalize_badge_name(name):
    """Normalize badge names for matching. 'Kitchen King' → 'kitchen-king'."""
    if not name:
        return ""
    return re.sub(r'[^a-z0-9]+', '-', name.lower().strip()).strip('-')


# ============================================================
# INGEST
# ============================================================

def ingest_taxonomy(conn):
    """Load badge taxonomy from Courtana ground truth."""
    path = os.path.join(GROUND_TRUTH_DIR, "badge-taxonomy.json")
    if not os.path.exists(path):
        print("  Skip: badge-taxonomy.json not found")
        return 0

    with open(path) as f:
        badges = json.load(f)

    count = 0
    for b in badges:
        try:
            conn.execute("""
                INSERT OR REPLACE INTO badges (slug, name, description, criteria, sport, tier, type, rarity, file_url, thumbnail_url)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                b.get("slug", ""),
                b.get("name", ""),
                b.get("description", ""),
                b.get("criteria", ""),
                b.get("sport", ""),
                b.get("tier", ""),
                b.get("type", ""),
                b.get("rarity"),
                b.get("file", ""),
                b.get("thumbnail_small", ""),
            ))
            count += 1
        except Exception as e:
            print(f"  Error inserting badge {b.get('name')}: {e}")

    conn.commit()
    print(f"  Taxonomy: {count} badges loaded")
    return count


def ingest_ground_truth(conn):
    """Load highlight-badge linkage from ALL ground truth sources.

    Source 1: courtana-ground-truth/highlight-badge-linkage.json (auth endpoint, 4000+ groups)
    Source 2: badged-clips/ground-truth.json (anon endpoint, curated badged clips)
    """
    count = 0

    # Source 1: Auth endpoint linkage (existing)
    path1 = os.path.join(GROUND_TRUTH_DIR, "highlight-badge-linkage.json")
    if os.path.exists(path1):
        with open(path1) as f:
            linkage = json.load(f)
        for group in linkage:
            count += _ingest_group_awards(conn, group)

    # Source 2: Badged clips ground truth (new - from anon endpoint)
    path2 = os.path.join(BADGED_CLIPS_DIR, "ground-truth.json")
    if os.path.exists(path2):
        with open(path2) as f:
            gt_data = json.load(f)
        for group in gt_data:
            count += _ingest_group_awards(conn, group)

    conn.commit()
    print(f"  Ground truth awards: {count} badge awards loaded")
    return count


def _ingest_group_awards(conn, group):
    """Ingest badge awards from a single highlight group."""
    count = 0
    group_id = group.get("group_id", "")
    video_urls = group.get("video_urls", [])
    primary_url = group.get("primary_url", "")

    for award in group.get("badge_awards", []):
        # Try to get asset UUID from the award's highlight_file first
        highlight_file = award.get("highlight_file", "")
        asset_uuid = extract_asset_uuid(highlight_file)

        # Fallback: try primary_url, then video_urls from the group
        if not asset_uuid and primary_url:
            asset_uuid = extract_asset_uuid(primary_url)
        if not asset_uuid:
            for vurl in video_urls:
                asset_uuid = extract_asset_uuid(vurl)
                if asset_uuid:
                    break

        try:
            conn.execute("""
                INSERT OR IGNORE INTO ground_truth_awards
                (badge_name, badge_slug, badge_tier, profile_username,
                 highlight_group_id, highlight_file_url, asset_uuid,
                 gemini_reason, awarded_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                award.get("badge_name", ""),
                award.get("badge_slug", ""),
                award.get("badge_tier", ""),
                award.get("profile_username", ""),
                group_id,
                highlight_file,
                asset_uuid,
                award.get("gemini_reason", ""),
                award.get("awarded_at", ""),
            ))
            count += 1
        except Exception:
            pass  # UNIQUE constraint violations expected on re-runs

    return count


def ingest_predictions(conn):
    """Load our model's badge predictions from all analysis JSONs."""
    count = 0
    files_scanned = 0

    for batch_dir in ANALYSIS_DIRS:
        if not os.path.isdir(batch_dir):
            continue
        batch_name = os.path.basename(batch_dir)

        for fpath in glob.glob(os.path.join(batch_dir, "analysis_*.json")):
            files_scanned += 1
            try:
                with open(fpath) as f:
                    data = json.load(f)
            except Exception:
                continue

            # Extract clip ID from filename: analysis_{uuid}_{timestamp}.json
            fname = os.path.basename(fpath)
            parts = fname.replace("analysis_", "").replace(".json", "").rsplit("_", 1)
            clip_id = parts[0] if parts else ""
            clip_id_short = clip_id[:8]

            video_url = data.get("_source_url") or data.get("_cdn_url") or ""
            asset_uuid = extract_asset_uuid(video_url) or clip_id
            prompt_version = data.get("prompt_version", "")
            analyzed_at = data.get("analyzed_at", "")

            badges = data.get("badge_intelligence", {}).get("predicted_badges", [])
            for badge in badges:
                badge_name = badge.get("badge_name", "")
                if not badge_name:
                    continue
                try:
                    conn.execute("""
                        INSERT OR IGNORE INTO predictions
                        (clip_id, clip_id_short, batch, video_url, asset_uuid,
                         badge_name, confidence, reasoning, prompt_version, analyzed_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        clip_id, clip_id_short, batch_name, video_url, asset_uuid,
                        badge_name,
                        badge.get("confidence", ""),
                        badge.get("reasoning", ""),
                        prompt_version,
                        analyzed_at,
                    ))
                    count += 1
                except Exception:
                    pass

    conn.commit()
    print(f"  Predictions: {count} badge predictions from {files_scanned} analysis files")
    return count


def ingest_uuid_group_map(conn):
    """Load UUID → highlight_group_id mapping from multiple sources.

    Source 1: working-set JSONs (anon endpoint clips with group_id)
    Source 2: highlight-badge-linkage JSON (auth endpoint video_urls per group)
    Source 3: badged-clips/clip-manifest.json (curated badged clips with group_id)
    Source 4: badged-clips/ground-truth.json (video_urls per group)
    """
    count = 0

    def _insert(uuid, gid):
        nonlocal count
        if uuid and gid:
            try:
                conn.execute(
                    "INSERT OR IGNORE INTO uuid_group_map (asset_uuid, highlight_group_id) VALUES (?, ?)",
                    (uuid, gid)
                )
                count += 1
            except Exception:
                pass

    # Source 1: working-set JSONs
    for fpath in glob.glob("output/working-set-*.json"):
        with open(fpath) as f:
            items = json.load(f)
        for item in items:
            _insert(extract_asset_uuid(item.get("file", "")), item.get("group_id", ""))

    # Source 2: highlight-badge-linkage (all video URLs per group)
    linkage_path = os.path.join(GROUND_TRUTH_DIR, "highlight-badge-linkage.json")
    if os.path.exists(linkage_path):
        with open(linkage_path) as f:
            linkage = json.load(f)
        for group in linkage:
            gid = group.get("group_id", "")
            for url in group.get("video_urls", []):
                _insert(extract_asset_uuid(url), gid)

    # Source 3: badged-clips/clip-manifest.json (KEY for Sprint 4)
    manifest_path = os.path.join(BADGED_CLIPS_DIR, "clip-manifest.json")
    if os.path.exists(manifest_path):
        with open(manifest_path) as f:
            manifest = json.load(f)
        for item in manifest:
            _insert(extract_asset_uuid(item.get("url", "")), item.get("group_id", ""))

    # Source 4: badged-clips/ground-truth.json (video_urls per group)
    gt_path = os.path.join(BADGED_CLIPS_DIR, "ground-truth.json")
    if os.path.exists(gt_path):
        with open(gt_path) as f:
            gt_data = json.load(f)
        for group in gt_data:
            gid = group.get("group_id", "")
            _insert(extract_asset_uuid(group.get("primary_url", "")), gid)
            for url in group.get("video_urls", []):
                _insert(extract_asset_uuid(url), gid)

    conn.commit()
    print(f"  UUID→group map: {count} entries")
    return count


def cmd_ingest(conn):
    """Ingest all data sources."""
    print("\nINGESTING DATA")
    print("-" * 40)

    # Clear existing data for fresh ingest
    conn.executescript("""
        DELETE FROM badges;
        DELETE FROM ground_truth_awards;
        DELETE FROM predictions;
        DELETE FROM cross_references;
        DELETE FROM prompt_feedback;
        DELETE FROM uuid_group_map;
    """)

    ingest_taxonomy(conn)
    ingest_ground_truth(conn)
    ingest_predictions(conn)
    ingest_uuid_group_map(conn)


# ============================================================
# ANALYZE (cross-reference)
# ============================================================

def build_slug_lookup(conn):
    """Build a name → slug lookup from the badge taxonomy."""
    rows = conn.execute("SELECT slug, name FROM badges").fetchall()
    lookup = {}
    for row in rows:
        lookup[normalize_badge_name(row["name"])] = row["slug"]
        lookup[row["slug"]] = row["slug"]
    return lookup


def cmd_analyze(conn):
    """Cross-reference predictions against ground truth.

    Matching strategy:
    1. Our predictions have asset_uuid (from CDN video URL)
    2. uuid_group_map links asset_uuid → highlight_group_id (from working-set)
    3. ground_truth_awards has highlight_group_id → badge awards
    4. Join through highlight_group_id to compare predictions vs awards
    """
    print("\nCROSS-REFERENCE ANALYSIS")
    print("-" * 40)

    conn.execute("DELETE FROM cross_references")

    slug_lookup = build_slug_lookup(conn)

    # Get predictions with their group IDs via the UUID→group map
    pred_with_groups = conn.execute("""
        SELECT p.*, m.highlight_group_id
        FROM predictions p
        LEFT JOIN uuid_group_map m ON p.asset_uuid = m.asset_uuid
    """).fetchall()

    # Group predictions by highlight_group_id
    preds_by_group = defaultdict(list)
    unlinked_preds = []
    for p in pred_with_groups:
        gid = p["highlight_group_id"]
        if gid:
            preds_by_group[gid].append(p)
        else:
            unlinked_preds.append(p)

    # Group ground truth by highlight_group_id
    gt_by_group = defaultdict(list)
    for g in conn.execute("SELECT * FROM ground_truth_awards").fetchall():
        gt_by_group[g["highlight_group_id"]].append(g)

    # Groups with ground truth awards
    linked_groups_with_awards = set(preds_by_group.keys()) & set(gt_by_group.keys())

    # Groups that exist in the linkage (mapped via uuid_group_map) but have NO awards
    # These are groups where Courtana chose NOT to award any badges
    all_linkage_groups = {row[0] for row in conn.execute(
        "SELECT DISTINCT highlight_group_id FROM uuid_group_map"
    ).fetchall()}
    mapped_pred_groups = set(preds_by_group.keys()) & all_linkage_groups
    groups_no_awards = mapped_pred_groups - set(gt_by_group.keys())

    print(f"  Prediction groups: {len(preds_by_group)}")
    print(f"  Ground truth groups (with awards): {len(gt_by_group)}")
    print(f"  Pred groups with awards: {len(linked_groups_with_awards)}")
    print(f"  Pred groups mapped but no awards: {len(groups_no_awards)}")
    print(f"  Unlinked predictions: {len(unlinked_preds)}")

    tp = fp = fn = 0

    # Groups where Courtana awarded nothing but we predicted badges → all false positives
    for group_id in groups_no_awards:
        preds = preds_by_group[group_id]
        for pred in preds:
            fp += 1
            conn.execute("""
                INSERT INTO cross_references
                (clip_id, asset_uuid, video_url, highlight_group_id,
                 predicted_badge, ground_truth_badge, match_type,
                 predicted_confidence, predicted_reasoning, courtana_reasoning)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                pred["clip_id"], pred["asset_uuid"], pred["video_url"], group_id,
                pred["badge_name"], None, "false_positive",
                pred["confidence"], pred["reasoning"],
                "(Courtana awarded no badges for this highlight group)",
            ))

    # Groups where both predictions and awards exist
    for group_id in linked_groups_with_awards:
        preds = preds_by_group[group_id]
        gts = gt_by_group[group_id]

        # Normalize prediction badge names to slugs
        pred_slugs = {}
        for p in preds:
            slug = slug_lookup.get(normalize_badge_name(p["badge_name"]),
                                   normalize_badge_name(p["badge_name"]))
            pred_slugs[slug] = p

        # Normalize ground truth badge slugs
        gt_slugs = {}
        for g in gts:
            gt_slugs[g["badge_slug"]] = g

        # True positives + False positives
        for slug, pred in pred_slugs.items():
            if slug in gt_slugs:
                match_type = "true_positive"
                gt_badge = gt_slugs[slug]["badge_name"]
                courtana_reason = gt_slugs[slug]["gemini_reason"]
                tp += 1
            else:
                match_type = "false_positive"
                gt_badge = None
                courtana_reason = None
                fp += 1

            conn.execute("""
                INSERT INTO cross_references
                (clip_id, asset_uuid, video_url, highlight_group_id,
                 predicted_badge, ground_truth_badge, match_type,
                 predicted_confidence, predicted_reasoning, courtana_reasoning)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                pred["clip_id"], pred["asset_uuid"], pred["video_url"], group_id,
                pred["badge_name"], gt_badge, match_type,
                pred["confidence"], pred["reasoning"], courtana_reason,
            ))

        # False negatives: ground truth badges we didn't predict
        for slug, gt in gt_slugs.items():
            if slug not in pred_slugs:
                fn += 1
                conn.execute("""
                    INSERT INTO cross_references
                    (clip_id, asset_uuid, video_url, highlight_group_id,
                     predicted_badge, ground_truth_badge, match_type,
                     predicted_confidence, predicted_reasoning, courtana_reasoning)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    None, None, gt["highlight_file_url"], group_id,
                    None, gt["badge_name"], "false_negative",
                    None, None, gt["gemini_reason"],
                ))

    conn.commit()

    precision = tp / (tp + fp) if (tp + fp) > 0 else 0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0

    total_linked = len(linked_groups_with_awards) + len(groups_no_awards)
    print(f"\n  RESULTS (across {total_linked} linked groups, {len(linked_groups_with_awards)} with awards, {len(groups_no_awards)} without):")
    print(f"  True Positives:  {tp}")
    print(f"  False Positives: {fp}")
    print(f"  False Negatives: {fn}")
    print(f"  Precision:       {precision:.1%}")
    print(f"  Recall:          {recall:.1%}")
    print(f"  F1 Score:        {f1:.1%}")

    return {"tp": tp, "fp": fp, "fn": fn, "precision": precision, "recall": recall, "f1": f1}


# ============================================================
# CO-OCCURRENCE ANALYSIS
# ============================================================

def compute_cooccurrence(conn):
    """Badge co-occurrence: which badges appear together and which should but don't.

    Returns:
      cooccurrence: list of dicts {badge_a, badge_b, together_count, a_without_b, b_without_a}
      quality_flags: list of dicts {group_id, flag, badge, reasoning}
    """
    # Get all ground truth awards grouped by highlight_group_id
    awards_by_group = defaultdict(set)
    reasons_by_group_badge = {}
    for row in conn.execute(
        "SELECT highlight_group_id, badge_name, gemini_reason FROM ground_truth_awards"
    ).fetchall():
        gid = row["highlight_group_id"]
        bname = row["badge_name"]
        awards_by_group[gid].add(bname)
        reasons_by_group_badge[(gid, bname)] = row["gemini_reason"] or ""

    # Count co-occurrences
    pair_together = Counter()
    badge_total = Counter()

    for gid, badges in awards_by_group.items():
        for b in badges:
            badge_total[b] += 1
        for b1 in badges:
            for b2 in badges:
                if b1 < b2:
                    pair_together[(b1, b2)] += 1

    # Build co-occurrence table
    cooccurrence = []
    for (b1, b2), together in sorted(pair_together.items(), key=lambda x: -x[1])[:50]:
        cooccurrence.append({
            "badge_a": b1,
            "badge_b": b2,
            "together_count": together,
            "a_total": badge_total[b1],
            "b_total": badge_total[b2],
            "a_without_b": badge_total[b1] - together,
            "b_without_a": badge_total[b2] - together,
            "lift": round(together / (badge_total[b1] * badge_total[b2] / max(len(awards_by_group), 1)), 2)
            if badge_total[b1] > 0 and badge_total[b2] > 0 else 0,
        })

    # Quality flags: check if reasoning mentions a badge that wasn't awarded
    # This is Bill's "tweener without tweener badge" scenario
    quality_flags = []
    badge_keywords = {}
    for row in conn.execute("SELECT name, slug FROM badges").fetchall():
        # Build keyword map: badge name words → badge name
        words = row["name"].lower().split()
        for w in words:
            if len(w) >= 4:  # Skip short words like "the", "a"
                badge_keywords[w] = row["name"]

    for gid, badges in awards_by_group.items():
        badges_lower = {b.lower() for b in badges}
        # Check each badge's reasoning for mentions of other badges
        for badge_name in badges:
            reason = reasons_by_group_badge.get((gid, badge_name), "").lower()
            if not reason:
                continue
            # Look for badge name keywords in reasoning that aren't awarded
            for keyword, implied_badge in badge_keywords.items():
                if keyword in reason and implied_badge.lower() not in badges_lower:
                    # Avoid flagging system badges
                    system_badges = {"game on", "new look", "bronze level up", "first session",
                                     "button masher", "rare find", "badge collector", "fresh fit",
                                     "exclusive club", "century club", "one of a kind", "social butterfly",
                                     "trophy case", "top 10", "regular", "legendary look"}
                    if implied_badge.lower() not in system_badges:
                        quality_flags.append({
                            "group_id": gid,
                            "flag": "missing_implied",
                            "awarded_badge": badge_name,
                            "implied_badge": implied_badge,
                            "reasoning_excerpt": reason[:200],
                        })

    # Deduplicate quality flags per group+implied_badge
    seen = set()
    unique_flags = []
    for f in quality_flags:
        key = (f["group_id"], f["implied_badge"])
        if key not in seen:
            seen.add(key)
            unique_flags.append(f)

    return cooccurrence, unique_flags[:100]  # Cap at 100 flags


# ============================================================
# DASHBOARD
# ============================================================

def cmd_dashboard(conn):
    """Generate the badge analytics dashboard HTML."""
    print("\nGENERATING DASHBOARD")
    print("-" * 40)

    # Gather stats
    badge_count = conn.execute("SELECT COUNT(*) FROM badges").fetchone()[0]
    gt_count = conn.execute("SELECT COUNT(*) FROM ground_truth_awards").fetchone()[0]
    pred_count = conn.execute("SELECT COUNT(*) FROM predictions").fetchone()[0]
    xref_count = conn.execute("SELECT COUNT(*) FROM cross_references").fetchone()[0]
    clips_analyzed = conn.execute("SELECT COUNT(DISTINCT clip_id) FROM predictions").fetchone()[0]
    clips_linked = conn.execute("SELECT COUNT(DISTINCT asset_uuid) FROM cross_references WHERE match_type != 'false_negative'").fetchone()[0]

    # Overall metrics
    tp = conn.execute("SELECT COUNT(*) FROM cross_references WHERE match_type='true_positive'").fetchone()[0]
    fp = conn.execute("SELECT COUNT(*) FROM cross_references WHERE match_type='false_positive'").fetchone()[0]
    fn = conn.execute("SELECT COUNT(*) FROM cross_references WHERE match_type='false_negative'").fetchone()[0]
    precision = tp / (tp + fp) if (tp + fp) > 0 else 0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0

    # Per-badge metrics
    badge_metrics = []
    all_badge_slugs = set()

    # From predictions
    pred_badges = conn.execute("""
        SELECT badge_name, COUNT(*) as cnt FROM predictions GROUP BY badge_name ORDER BY cnt DESC
    """).fetchall()
    for row in pred_badges:
        all_badge_slugs.add(normalize_badge_name(row["badge_name"]))

    # From ground truth
    gt_badges = conn.execute("""
        SELECT badge_name, COUNT(*) as cnt FROM ground_truth_awards GROUP BY badge_name ORDER BY cnt DESC
    """).fetchall()

    # Per-badge precision/recall
    slug_lookup = build_slug_lookup(conn)
    badge_stats = {}

    for row in conn.execute("SELECT * FROM cross_references").fetchall():
        pred_slug = normalize_badge_name(row["predicted_badge"]) if row["predicted_badge"] else None
        gt_slug = normalize_badge_name(row["ground_truth_badge"]) if row["ground_truth_badge"] else None

        if pred_slug:
            pred_slug = slug_lookup.get(pred_slug, pred_slug)
        if gt_slug:
            gt_slug = slug_lookup.get(gt_slug, gt_slug)

        mt = row["match_type"]
        if mt == "true_positive" and pred_slug:
            badge_stats.setdefault(pred_slug, {"tp": 0, "fp": 0, "fn": 0})
            badge_stats[pred_slug]["tp"] += 1
        elif mt == "false_positive" and pred_slug:
            badge_stats.setdefault(pred_slug, {"tp": 0, "fp": 0, "fn": 0})
            badge_stats[pred_slug]["fp"] += 1
        elif mt == "false_negative" and gt_slug:
            badge_stats.setdefault(gt_slug, {"tp": 0, "fp": 0, "fn": 0})
            badge_stats[gt_slug]["fn"] += 1

    badge_metrics_list = []
    for slug, stats in sorted(badge_stats.items(), key=lambda x: -(x[1]["tp"] + x[1]["fp"] + x[1]["fn"])):
        s_tp = stats["tp"]
        s_fp = stats["fp"]
        s_fn = stats["fn"]
        s_prec = s_tp / (s_tp + s_fp) if (s_tp + s_fp) > 0 else 0
        s_rec = s_tp / (s_tp + s_fn) if (s_tp + s_fn) > 0 else 0
        s_f1 = 2 * s_prec * s_rec / (s_prec + s_rec) if (s_prec + s_rec) > 0 else 0

        # Get display name
        name_row = conn.execute("SELECT name FROM badges WHERE slug = ?", (slug,)).fetchone()
        display_name = name_row["name"] if name_row else slug.replace("-", " ").title()

        badge_metrics_list.append({
            "slug": slug, "name": display_name,
            "tp": s_tp, "fp": s_fp, "fn": s_fn,
            "precision": round(s_prec, 3), "recall": round(s_rec, 3), "f1": round(s_f1, 3),
        })

    # Criteria gap: badges in Courtana but not in our predictions
    our_predicted_slugs = {normalize_badge_name(r["badge_name"]) for r in
                          conn.execute("SELECT DISTINCT badge_name FROM predictions").fetchall()}
    our_predicted_slugs_resolved = {slug_lookup.get(s, s) for s in our_predicted_slugs}

    all_courtana_badges = conn.execute(
        "SELECT slug, name, criteria, tier, rarity FROM badges ORDER BY rarity DESC"
    ).fetchall()

    criteria_gap = []
    for b in all_courtana_badges:
        in_prompt = b["slug"] in our_predicted_slugs_resolved
        criteria_gap.append({
            "slug": b["slug"], "name": b["name"], "criteria": b["criteria"] or "",
            "tier": b["tier"], "rarity": b["rarity"] or 0, "in_our_prompt": in_prompt,
        })

    # Prediction frequency distribution
    pred_freq = {row["badge_name"]: row["cnt"] for row in pred_badges}
    gt_freq = {row["badge_name"]: row["cnt"] for row in gt_badges}

    # Confusion patterns (top mismatches)
    confusion = conn.execute("""
        SELECT predicted_badge, ground_truth_badge, COUNT(*) as cnt
        FROM cross_references
        WHERE match_type IN ('true_positive', 'false_positive')
        AND predicted_badge IS NOT NULL
        GROUP BY predicted_badge, ground_truth_badge
        ORDER BY cnt DESC
        LIMIT 20
    """).fetchall()

    # Recent mismatches
    mismatches = conn.execute("""
        SELECT * FROM cross_references
        WHERE match_type IN ('false_positive', 'false_negative')
        ORDER BY created_at DESC
        LIMIT 20
    """).fetchall()

    # Co-occurrence analysis
    cooccurrence, quality_flags = compute_cooccurrence(conn)

    # Build HTML
    html = _generate_dashboard_html(
        badge_count=badge_count, gt_count=gt_count, pred_count=pred_count,
        clips_analyzed=clips_analyzed, clips_linked=clips_linked,
        tp=tp, fp=fp, fn=fn, precision=precision, recall=recall, f1=f1,
        badge_metrics=badge_metrics_list, criteria_gap=criteria_gap,
        pred_freq=pred_freq, gt_freq=gt_freq,
        confusion=[dict(r) for r in confusion],
        mismatches=[dict(r) for r in mismatches],
        cooccurrence=cooccurrence,
        quality_flags=quality_flags,
    )

    out_path = "output/badge-analytics-dashboard.html"
    with open(out_path, "w") as f:
        f.write(html)
    size_kb = os.path.getsize(out_path) / 1024
    print(f"  Dashboard: {out_path} ({size_kb:.0f} KB)")


def _generate_dashboard_html(**data):
    """Generate the full HTML dashboard."""
    badge_metrics_json = json.dumps(data["badge_metrics"])
    criteria_gap_json = json.dumps(data["criteria_gap"][:50])  # Top 50 for display
    pred_freq_json = json.dumps(data["pred_freq"])
    gt_freq_json = json.dumps(data["gt_freq"])
    cooccurrence = data.get("cooccurrence", [])
    quality_flags = data.get("quality_flags", [])

    badges_not_in_prompt = sum(1 for c in data["criteria_gap"] if not c["in_our_prompt"])

    # Build mismatch rows
    mismatch_rows = ""
    for m in data["mismatches"]:
        mt = m["match_type"]
        pred = m["predicted_badge"] or "—"
        gt = m["ground_truth_badge"] or "—"
        pred_r = (m["predicted_reasoning"] or "")[:120]
        court_r = (m["courtana_reasoning"] or "")[:120]
        color = "#FF5252" if mt == "false_positive" else "#FFC107"
        label = "Over-predicted" if mt == "false_positive" else "Missed"
        clip_short = (m["clip_id"] or m["asset_uuid"] or "?")[:8]
        mismatch_rows += f"""<tr>
            <td>{clip_short}</td>
            <td><span style="color:{color}">{label}</span></td>
            <td>{pred}</td>
            <td>{gt}</td>
            <td style="font-size:0.8em;color:#aaa">{pred_r}</td>
            <td style="font-size:0.8em;color:#aaa">{court_r}</td>
        </tr>"""

    # Build criteria gap rows (show top 40)
    criteria_rows = ""
    for c in data["criteria_gap"][:40]:
        status = '<span style="color:#00E676">In prompt</span>' if c["in_our_prompt"] else '<span style="color:#FF5252">Missing</span>'
        tier_colors = {"platinum": "#E5E4E2", "gold": "#FFD700", "silver": "#C0C0C0", "bronze": "#CD7F32", "wood": "#8B4513", "brick": "#CB4154"}
        tier_color = tier_colors.get(c["tier"], "#888")
        criteria_rows += f"""<tr>
            <td>{c['name']}</td>
            <td><span style="color:{tier_color}">{c['tier']}</span></td>
            <td>{c['rarity']:.1f}%</td>
            <td>{status}</td>
            <td style="font-size:0.8em;color:#ccc">{c['criteria'][:100]}{'...' if len(c['criteria']) > 100 else ''}</td>
        </tr>"""

    # Per-badge metrics rows
    badge_rows = ""
    for bm in data["badge_metrics"][:20]:
        p_color = "#00E676" if bm["precision"] >= 0.5 else "#FF5252"
        r_color = "#00E676" if bm["recall"] >= 0.5 else "#FFC107"
        badge_rows += f"""<tr>
            <td>{bm['name']}</td>
            <td>{bm['tp']}</td>
            <td>{bm['fp']}</td>
            <td>{bm['fn']}</td>
            <td style="color:{p_color}">{bm['precision']:.0%}</td>
            <td style="color:{r_color}">{bm['recall']:.0%}</td>
            <td>{bm['f1']:.0%}</td>
        </tr>"""

    # Build co-occurrence rows
    cooccurrence_rows = ""
    for co in cooccurrence[:30]:
        cooccurrence_rows += f"""<tr>
            <td>{co['badge_a']}</td>
            <td>{co['badge_b']}</td>
            <td>{co['together_count']}</td>
            <td>{co['a_total']}</td>
            <td>{co['b_total']}</td>
            <td>{co['a_without_b']}</td>
            <td>{co['b_without_a']}</td>
            <td>{co['lift']}</td>
        </tr>"""

    # Build quality flag rows
    quality_flag_rows = ""
    for qf in quality_flags[:30]:
        quality_flag_rows += f"""<tr>
            <td>{qf['group_id'][:12]}</td>
            <td style="color:var(--yellow)">{qf['awarded_badge']}</td>
            <td style="color:var(--red)">{qf['implied_badge']}</td>
            <td style="font-size:0.8em;color:#aaa">{qf['reasoning_excerpt'][:150]}</td>
        </tr>"""

    # Build dynamic alert HTML
    if data["tp"] > 0:
        insight_alert = (
            f'<div class="insight"><strong>Results:</strong> {data["tp"]} true positives, '
            f'{data["fp"]} false positives, {data["fn"]} false negatives across '
            f'{data["clips_linked"]} linked clips.</div>'
        )
    else:
        insight_alert = (
            f'<div class="alert-warn" style="background:rgba(255,193,7,0.1);border:1px solid '
            f'var(--yellow);border-radius:8px;padding:16px;margin:16px 0"><strong>Over-prediction '
            f'finding:</strong> Our model predicted {data["fp"]} badges as false positives. '
            f'The criteria gap table below shows what Courtana&#39;s Gemini looks for.</div>'
        )

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Badge Analytics — Pickle DaaS</title>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.4/dist/chart.umd.min.js"></script>
<style>
  :root {{ --bg: #0A0E17; --card: #151B2B; --border: #1E2A3A; --text: #E8EAED;
           --dim: #8892A0; --green: #00E676; --red: #FF5252; --yellow: #FFC107;
           --blue: #448AFF; --purple: #B388FF; }}
  * {{ margin:0; padding:0; box-sizing:border-box; }}
  body {{ background:var(--bg); color:var(--text); font-family:'Inter',system-ui,sans-serif; padding:24px; }}
  h1 {{ font-size:1.8em; margin-bottom:8px; }}
  h2 {{ font-size:1.2em; margin:32px 0 16px; color:var(--blue); border-bottom:1px solid var(--border); padding-bottom:8px; }}
  .subtitle {{ color:var(--dim); font-size:0.9em; margin-bottom:24px; }}
  .kpi-grid {{ display:grid; grid-template-columns:repeat(auto-fit, minmax(160px,1fr)); gap:16px; margin:24px 0; }}
  .kpi {{ background:var(--card); border:1px solid var(--border); border-radius:12px; padding:20px; text-align:center; }}
  .kpi .value {{ font-size:2em; font-weight:700; }}
  .kpi .label {{ font-size:0.8em; color:var(--dim); margin-top:4px; }}
  .card {{ background:var(--card); border:1px solid var(--border); border-radius:12px; padding:24px; margin:16px 0; }}
  table {{ width:100%; border-collapse:collapse; font-size:0.85em; }}
  th {{ text-align:left; padding:8px 12px; border-bottom:2px solid var(--border); color:var(--dim); font-weight:600; }}
  td {{ padding:8px 12px; border-bottom:1px solid var(--border); }}
  tr:hover {{ background:rgba(68,138,255,0.05); }}
  .chart-container {{ max-width:800px; margin:16px auto; }}
  .alert {{ background:rgba(255,82,82,0.1); border:1px solid var(--red); border-radius:8px; padding:16px; margin:16px 0; }}
  .alert-warn {{ background:rgba(255,193,7,0.1); border-color:var(--yellow); }}
  .insight {{ background:rgba(0,230,118,0.08); border:1px solid var(--green); border-radius:8px; padding:16px; margin:16px 0; }}
</style>
</head>
<body>

<h1>Badge Analytics Warehouse</h1>
<p class="subtitle">Cross-referencing our model's badge predictions against Courtana's ground truth | Generated {datetime.now().strftime('%Y-%m-%d %H:%M')}</p>

<!-- KPIs -->
<div class="kpi-grid">
  <div class="kpi"><div class="value" style="color:var(--blue)">{data['badge_count']}</div><div class="label">Courtana Badges</div></div>
  <div class="kpi"><div class="value" style="color:var(--purple)">{data['gt_count']}</div><div class="label">Ground Truth Awards</div></div>
  <div class="kpi"><div class="value">{data['pred_count']}</div><div class="label">Our Predictions</div></div>
  <div class="kpi"><div class="value">{data['clips_analyzed']}</div><div class="label">Clips Analyzed</div></div>
  <div class="kpi"><div class="value" style="color:var(--green)">{data['clips_linked']}</div><div class="label">Clips Linked to GT</div></div>
  <div class="kpi"><div class="value" style="color:{'var(--green)' if data['precision'] >= 0.5 else 'var(--red)'}">{data['precision']:.0%}</div><div class="label">Precision</div></div>
  <div class="kpi"><div class="value" style="color:{'var(--green)' if data['recall'] >= 0.5 else 'var(--yellow)'}">{data['recall']:.0%}</div><div class="label">Recall</div></div>
  <div class="kpi"><div class="value" style="color:{'var(--green)' if data['f1'] >= 0.5 else 'var(--red)'}">{data['f1']:.0%}</div><div class="label">F1 Score</div></div>
</div>

<!-- Key Insights -->
<div class="alert">
  <strong>Taxonomy Gap:</strong> Courtana has {data['badge_count']} badges. Our prompt knows about {data['badge_count'] - badges_not_in_prompt} of them.
  <strong>{badges_not_in_prompt} badges are invisible to our model.</strong>
  Injecting Courtana's criteria text into our prompt is the single biggest improvement available.
</div>

{insight_alert}

<!-- Per-Badge Metrics -->
<h2>Per-Badge Precision & Recall</h2>
<div class="card">
  <table>
    <thead><tr><th>Badge</th><th>TP</th><th>FP</th><th>FN</th><th>Precision</th><th>Recall</th><th>F1</th></tr></thead>
    <tbody>{badge_rows or '<tr><td colspan="7" style="color:var(--dim)">No linked clips yet — need overlapping CDN URLs between our analyses and Courtana highlight groups</td></tr>'}</tbody>
  </table>
</div>

<div class="chart-container">
  <canvas id="badgeMetricsChart"></canvas>
</div>

<!-- Prediction vs Ground Truth Distribution -->
<h2>Badge Distribution: Our Predictions vs Courtana Actual</h2>
<div class="card">
  <div class="chart-container">
    <canvas id="distributionChart"></canvas>
  </div>
</div>

<!-- Criteria Gap Table -->
<h2>Courtana Badge Criteria — What Our Prompt Is Missing</h2>
<p style="color:var(--dim);margin-bottom:12px">Courtana tells its Gemini exactly what to look for per badge. These criteria should be in our prompt.</p>
<div class="card" style="max-height:600px;overflow-y:auto">
  <table>
    <thead><tr><th>Badge</th><th>Tier</th><th>Rarity</th><th>In Our Prompt?</th><th>Courtana's Criteria</th></tr></thead>
    <tbody>{criteria_rows}</tbody>
  </table>
</div>

<!-- Mismatches -->
<h2>Recent Mismatches — What We Got Wrong</h2>
<div class="card" style="max-height:500px;overflow-y:auto">
  <table>
    <thead><tr><th>Clip</th><th>Type</th><th>We Predicted</th><th>Courtana Awarded</th><th>Our Reasoning</th><th>Courtana's Reasoning</th></tr></thead>
    <tbody>{mismatch_rows or '<tr><td colspan="6" style="color:var(--dim)">No mismatches to show (either perfect accuracy or no linked clips)</td></tr>'}</tbody>
  </table>
</div>

<!-- Badge Co-occurrence Analysis -->
<h2>Badge Co-occurrence — Which Badges Appear Together?</h2>
<p style="color:var(--dim);margin-bottom:12px">When Badge A is awarded, how often is Badge B also awarded? High "lift" means they co-occur more than chance. Missing co-occurrences may indicate badges that should have been awarded.</p>
<div class="card" style="max-height:500px;overflow-y:auto">
  <table>
    <thead><tr><th>Badge A</th><th>Badge B</th><th>Together</th><th>A Total</th><th>B Total</th><th>A w/o B</th><th>B w/o A</th><th>Lift</th></tr></thead>
    <tbody>{cooccurrence_rows or '<tr><td colspan="8" style="color:var(--dim)">No co-occurrence data yet — need ground truth awards from badged clips</td></tr>'}</tbody>
  </table>
</div>

<!-- Quality Flags — Missing Implied Badges -->
<h2>Quality Flags — Missing Implied Badges</h2>
<p style="color:var(--dim);margin-bottom:12px">Cases where Courtana's reasoning for one badge implies another badge should also have been awarded, but wasn't. This is the "tweener without tweener badge" pattern.</p>
<div class="card" style="max-height:500px;overflow-y:auto">
  <table>
    <thead><tr><th>Group</th><th>Awarded Badge</th><th>Implied (Missing) Badge</th><th>Reasoning Excerpt</th></tr></thead>
    <tbody>{quality_flag_rows or '<tr><td colspan="4" style="color:var(--dim)">No quality flags detected</td></tr>'}</tbody>
  </table>
</div>

<!-- Reinforcement Loop Status -->
<h2>Reinforcement Loop Status</h2>
<div class="card">
  <p><strong>Courtana taxonomy:</strong> {data['badge_count']} badges, each with explicit criteria</p>
  <p><strong>Clips analyzed:</strong> {data['clips_analyzed']} | <strong>Linked to ground truth:</strong> {data['clips_linked']}</p>
  <p><strong>True Positives:</strong> {data['tp']} | <strong>False Positives:</strong> {data['fp']} | <strong>False Negatives:</strong> {data['fn']}</p>
  <p><strong>Co-occurrence patterns:</strong> {len(cooccurrence)} badge pairs analyzed</p>
  <p><strong>Quality flags:</strong> {len(quality_flags)} potential missing badge awards detected</p>
  <p style="margin-top:12px;color:var(--dim)">The loop: Predict → Compare → Patch prompt → Re-predict → Compare again</p>
</div>

<script>
// Per-badge metrics chart
const badgeMetrics = {badge_metrics_json};
if (badgeMetrics.length > 0) {{
  new Chart(document.getElementById('badgeMetricsChart'), {{
    type: 'bar',
    data: {{
      labels: badgeMetrics.slice(0, 15).map(b => b.name),
      datasets: [
        {{ label: 'Precision', data: badgeMetrics.slice(0, 15).map(b => b.precision), backgroundColor: '#00E676' }},
        {{ label: 'Recall', data: badgeMetrics.slice(0, 15).map(b => b.recall), backgroundColor: '#448AFF' }},
        {{ label: 'F1', data: badgeMetrics.slice(0, 15).map(b => b.f1), backgroundColor: '#B388FF' }},
      ]
    }},
    options: {{
      responsive: true,
      plugins: {{ title: {{ display: true, text: 'Per-Badge Precision / Recall / F1', color: '#E8EAED' }},
                  legend: {{ labels: {{ color: '#8892A0' }} }} }},
      scales: {{
        x: {{ ticks: {{ color: '#8892A0', maxRotation: 45 }} }},
        y: {{ min: 0, max: 1, ticks: {{ color: '#8892A0', callback: v => (v*100)+'%' }} }}
      }}
    }}
  }});
}}

// Distribution chart
const predFreq = {pred_freq_json};
const gtFreq = {gt_freq_json};
const allBadgeNames = [...new Set([...Object.keys(predFreq), ...Object.keys(gtFreq)])].sort((a,b) => (gtFreq[b]||0) - (gtFreq[a]||0)).slice(0, 20);
if (allBadgeNames.length > 0) {{
  new Chart(document.getElementById('distributionChart'), {{
    type: 'bar',
    data: {{
      labels: allBadgeNames,
      datasets: [
        {{ label: 'Our Predictions', data: allBadgeNames.map(n => predFreq[n]||0), backgroundColor: '#448AFF' }},
        {{ label: 'Courtana Actual', data: allBadgeNames.map(n => gtFreq[n]||0), backgroundColor: '#00E676' }},
      ]
    }},
    options: {{
      responsive: true,
      plugins: {{ title: {{ display: true, text: 'Badge Frequency: Model vs Ground Truth (Top 20)', color: '#E8EAED' }},
                  legend: {{ labels: {{ color: '#8892A0' }} }} }},
      scales: {{
        x: {{ ticks: {{ color: '#8892A0', maxRotation: 45 }} }},
        y: {{ ticks: {{ color: '#8892A0' }} }}
      }}
    }}
  }});
}}
</script>

</body>
</html>"""


# ============================================================
# FEEDBACK (prompt reinforcement)
# ============================================================

def cmd_feedback(conn):
    """Generate prompt reinforcement patch from cross-reference analysis."""
    print("\nGENERATING PROMPT REINFORCEMENT PATCH")
    print("-" * 40)

    conn.execute("DELETE FROM prompt_feedback")

    slug_lookup = build_slug_lookup(conn)

    # 1. Badges in Courtana but not in our predictions (missing from prompt)
    our_predicted_slugs = {slug_lookup.get(normalize_badge_name(r[0]), normalize_badge_name(r[0]))
                          for r in conn.execute("SELECT DISTINCT badge_name FROM predictions").fetchall()}

    missing_badges = conn.execute("""
        SELECT slug, name, criteria, tier, rarity FROM badges
        WHERE slug NOT IN ({})
        ORDER BY rarity DESC
    """.format(",".join(f"'{s}'" for s in our_predicted_slugs) if our_predicted_slugs else "'__none__'")).fetchall()

    for b in missing_badges:
        conn.execute("""
            INSERT INTO prompt_feedback (badge_slug, feedback_type, description, suggested_prompt_edit, severity)
            VALUES (?, ?, ?, ?, ?)
        """, (
            b["slug"],
            "missing_badge",
            f"Badge '{b['name']}' ({b['tier']}, {b['rarity']:.1f}% rarity) exists in Courtana but is not in our prompt",
            f'Add to badge taxonomy: "{b["name"]}" — Criteria: "{b["criteria"]}"',
            "high" if (b["rarity"] or 0) > 5 else "medium",
        ))

    # 2. False positive patterns
    fp_badges = conn.execute("""
        SELECT predicted_badge, COUNT(*) as cnt
        FROM cross_references WHERE match_type = 'false_positive'
        GROUP BY predicted_badge ORDER BY cnt DESC
    """).fetchall()

    for row in fp_badges:
        slug = slug_lookup.get(normalize_badge_name(row["predicted_badge"]), "")
        criteria_row = conn.execute("SELECT criteria FROM badges WHERE slug = ?", (slug,)).fetchone()
        criteria = criteria_row["criteria"] if criteria_row else "No criteria found"

        conn.execute("""
            INSERT INTO prompt_feedback (badge_slug, feedback_type, description, suggested_prompt_edit, severity)
            VALUES (?, ?, ?, ?, ?)
        """, (
            slug,
            "false_positive_pattern",
            f"'{row['predicted_badge']}' over-predicted {row['cnt']} times. Model triggers this badge too easily.",
            f'Tighten criteria for "{row["predicted_badge"]}". Courtana criteria: "{criteria}"',
            "high" if row["cnt"] >= 3 else "medium",
        ))

    # 3. False negative patterns
    fn_badges = conn.execute("""
        SELECT ground_truth_badge, COUNT(*) as cnt
        FROM cross_references WHERE match_type = 'false_negative'
        GROUP BY ground_truth_badge ORDER BY cnt DESC
    """).fetchall()

    for row in fn_badges:
        slug = normalize_badge_name(row["ground_truth_badge"])
        criteria_row = conn.execute("SELECT criteria FROM badges WHERE slug = ?", (slug,)).fetchone()
        criteria = criteria_row["criteria"] if criteria_row else "No criteria found"

        conn.execute("""
            INSERT INTO prompt_feedback (badge_slug, feedback_type, description, suggested_prompt_edit, severity)
            VALUES (?, ?, ?, ?, ?)
        """, (
            slug,
            "false_negative_pattern",
            f"'{row['ground_truth_badge']}' missed {row['cnt']} times. Courtana awarded it but our model didn't predict it.",
            f'Ensure "{row["ground_truth_badge"]}" is in prompt. Courtana criteria: "{criteria}"',
            "high" if row["cnt"] >= 3 else "medium",
        ))

    conn.commit()

    # Generate the reinforcement patch markdown
    feedback_rows = conn.execute("""
        SELECT * FROM prompt_feedback ORDER BY severity DESC, feedback_type
    """).fetchall()

    # Get full taxonomy for the patch
    all_badges = conn.execute("""
        SELECT name, slug, criteria, tier, type, rarity FROM badges
        WHERE criteria IS NOT NULL AND criteria != ''
        ORDER BY rarity DESC
    """).fetchall()

    patch = f"""# Badge Reinforcement Patch
**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M')}
**Source:** Cross-reference of {conn.execute("SELECT COUNT(*) FROM predictions").fetchone()[0]} predictions vs {conn.execute("SELECT COUNT(*) FROM ground_truth_awards").fetchone()[0]} ground truth awards

---

## Summary

- **Total Courtana badges:** {len(all_badges)}
- **Badges our model knows about:** {len(our_predicted_slugs)}
- **Badges missing from our prompt:** {len(missing_badges)}
- **Feedback records generated:** {len(feedback_rows)}

---

## Action Items

"""
    # Group by type
    by_type = defaultdict(list)
    for row in feedback_rows:
        by_type[row["feedback_type"]].append(row)

    if by_type.get("false_positive_pattern"):
        patch += "### Over-Predicted Badges (Tighten Criteria)\n\n"
        for row in by_type["false_positive_pattern"]:
            patch += f"- **{row['description']}**\n  Fix: {row['suggested_prompt_edit']}\n\n"

    if by_type.get("false_negative_pattern"):
        patch += "### Missed Badges (Add or Emphasize)\n\n"
        for row in by_type["false_negative_pattern"]:
            patch += f"- **{row['description']}**\n  Fix: {row['suggested_prompt_edit']}\n\n"

    if by_type.get("missing_badge"):
        high_priority = [r for r in by_type["missing_badge"] if r["severity"] == "high"]
        patch += f"### Missing Badges — Not in Our Prompt ({len(by_type['missing_badge'])} total, {len(high_priority)} high-priority)\n\n"
        patch += "**High-priority (>5% player rarity):**\n\n"
        for row in high_priority[:20]:
            patch += f"- {row['suggested_prompt_edit']}\n"
        if len(high_priority) > 20:
            patch += f"\n...and {len(high_priority) - 20} more high-priority badges\n"

    # Full taxonomy reference
    patch += f"""

---

## Complete Courtana Badge Taxonomy ({len(all_badges)} badges)

Copy this into the prompt's badge_intelligence section to give the model
the full picture of what badges exist and what triggers them.

| Badge | Tier | Rarity | Criteria |
|-------|------|--------|----------|
"""
    for b in all_badges:
        criteria_clean = (b["criteria"] or "").replace("|", "/").replace("\n", " ")[:120]
        patch += f"| {b['name']} | {b['tier']} | {b['rarity']:.1f}% | {criteria_clean} |\n"

    # Save
    patch_path = "prompts/badge-reinforcement-patch.md"
    Path(os.path.dirname(patch_path)).mkdir(parents=True, exist_ok=True)
    with open(patch_path, "w") as f:
        f.write(patch)

    size_kb = os.path.getsize(patch_path) / 1024
    print(f"  Patch file: {patch_path} ({size_kb:.0f} KB)")
    print(f"  Feedback records: {len(feedback_rows)}")
    print(f"  Missing badges: {len(missing_badges)}")
    print(f"  False positive patterns: {len(by_type.get('false_positive_pattern', []))}")
    print(f"  False negative patterns: {len(by_type.get('false_negative_pattern', []))}")


# ============================================================
# CLI
# ============================================================

def main():
    parser = argparse.ArgumentParser(description="Pickle DaaS Badge Analytics Warehouse")
    parser.add_argument("command", choices=["ingest", "analyze", "dashboard", "feedback", "all"],
                        help="Command to run")
    args = parser.parse_args()

    os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

    conn = get_db()

    if args.command == "all":
        cmd_ingest(conn)
        cmd_analyze(conn)
        cmd_dashboard(conn)
        cmd_feedback(conn)
    elif args.command == "ingest":
        cmd_ingest(conn)
    elif args.command == "analyze":
        cmd_analyze(conn)
    elif args.command == "dashboard":
        cmd_dashboard(conn)
    elif args.command == "feedback":
        cmd_feedback(conn)

    conn.close()
    print("\nDone.")


if __name__ == "__main__":
    main()

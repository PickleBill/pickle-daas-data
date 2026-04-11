#!/usr/bin/env python3
"""Reorganize output/ folder into structured subdirectories. Moves only — never deletes."""

import os
import shutil
from datetime import datetime

OUTPUT = os.path.join(os.path.dirname(os.path.dirname(__file__)), "output")
LOG_LINES = []

def log(msg):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}] {msg}"
    LOG_LINES.append(line)
    print(line)

def move(src_name, dest_subdir, dest_name=None):
    src = os.path.join(OUTPUT, src_name)
    if not os.path.exists(src):
        return False
    dest_dir = os.path.join(OUTPUT, dest_subdir)
    os.makedirs(dest_dir, exist_ok=True)
    final_name = dest_name or src_name
    dest = os.path.join(dest_dir, final_name)
    if os.path.exists(dest):
        log(f"SKIP (already exists): {src_name} → {dest_subdir}/{final_name}")
        return False
    shutil.move(src, dest)
    log(f"MOVED: {src_name} → {dest_subdir}/{final_name}")
    return True

# --- Batch folders → batches/ ---
for item in sorted(os.listdir(OUTPUT)):
    full = os.path.join(OUTPUT, item)
    if not os.path.isdir(full):
        continue
    if item.startswith(("batch-", "auto-ingest-", "picklebill-batch-", "fast-batch-",
                         "badged-clips", "v1.", "test-", "speed-test", "courtana-ground-truth")):
        move(item, "batches")

# --- Discovery engine V1 ---
if os.path.exists(os.path.join(OUTPUT, "discovery-engine")):
    # Move contents into discovery/v1/
    src_dir = os.path.join(OUTPUT, "discovery-engine")
    dest_dir = os.path.join(OUTPUT, "discovery", "v1")
    os.makedirs(dest_dir, exist_ok=True)
    for item in os.listdir(src_dir):
        s = os.path.join(src_dir, item)
        d = os.path.join(dest_dir, item)
        if not os.path.exists(d):
            shutil.move(s, d)
            log(f"MOVED: discovery-engine/{item} → discovery/v1/{item}")
        else:
            log(f"SKIP (exists): discovery-engine/{item}")
    # Remove empty dir
    try:
        os.rmdir(src_dir)
        log("REMOVED empty: discovery-engine/")
    except OSError:
        log("NOTE: discovery-engine/ not empty after move, leaving in place")

# --- Investor files ---
for item in os.listdir(OUTPUT):
    if "investor" in item.lower() and os.path.isfile(os.path.join(OUTPUT, item)):
        move(item, "investor")

# --- HTML dashboards ---
dashboard_files = [f for f in os.listdir(OUTPUT)
                   if f.endswith(".html") and os.path.isfile(os.path.join(OUTPUT, f))]
for f in dashboard_files:
    move(f, "dashboards")

# --- Player profiles ---
for item in os.listdir(OUTPUT):
    full = os.path.join(OUTPUT, item)
    if any(item.startswith(p) for p in ("picklebill-dna-", "picklebill-intel-", "player-")):
        move(item, "player")

# --- Brand reports ---
for item in os.listdir(OUTPUT):
    if "brand" in item.lower() and os.path.isfile(os.path.join(OUTPUT, item)):
        move(item, "brand")

# --- Lovable package ---
if os.path.isdir(os.path.join(OUTPUT, "lovable-package")):
    # Move contents into lovable/
    src_dir = os.path.join(OUTPUT, "lovable-package")
    dest_dir = os.path.join(OUTPUT, "lovable")
    os.makedirs(dest_dir, exist_ok=True)
    for item in os.listdir(src_dir):
        s = os.path.join(src_dir, item)
        d = os.path.join(dest_dir, item)
        if not os.path.exists(d):
            shutil.move(s, d)
            log(f"MOVED: lovable-package/{item} → lovable/{item}")
    try:
        os.rmdir(src_dir)
        log("REMOVED empty: lovable-package/")
    except OSError:
        log("NOTE: lovable-package/ not empty after move")

# --- Voice commentary ---
if os.path.isdir(os.path.join(OUTPUT, "voice-commentary")):
    src_dir = os.path.join(OUTPUT, "voice-commentary")
    dest_dir = os.path.join(OUTPUT, "voice")
    os.makedirs(dest_dir, exist_ok=True)
    for item in os.listdir(src_dir):
        s = os.path.join(src_dir, item)
        d = os.path.join(dest_dir, item)
        if not os.path.exists(d):
            shutil.move(s, d)
            log(f"MOVED: voice-commentary/{item} → voice/{item}")
    try:
        os.rmdir(src_dir)
        log("REMOVED empty: voice-commentary/")
    except OSError:
        log("NOTE: voice-commentary/ not empty after move")

# --- Cost/CSV files → tools/ ---
for item in os.listdir(OUTPUT):
    full = os.path.join(OUTPUT, item)
    if os.path.isfile(full) and (item.startswith("cost-") or item.endswith(".csv") or item.endswith(".log")):
        move(item, "tools")

# --- Broadcast → batches/ ---
if os.path.isdir(os.path.join(OUTPUT, "broadcast")):
    move("broadcast", "batches")

# --- Frames → batches/ ---
if os.path.isdir(os.path.join(OUTPUT, "frames")):
    move("frames", "batches")

# --- Pickle wrapped → batches/ ---
if os.path.isdir(os.path.join(OUTPUT, "pickle-wrapped")):
    move("pickle-wrapped", "batches")

# --- Player cards dir → player/ ---
if os.path.isdir(os.path.join(OUTPUT, "player-cards")):
    move("player-cards", "player")

# --- Write log ---
log_path = os.path.join(OUTPUT, "REORGANIZE-LOG.md")
with open(log_path, "w") as f:
    f.write("# Output Reorganization Log\n\n")
    f.write(f"Run: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
    for line in LOG_LINES:
        f.write(f"- {line}\n")

print(f"\nDone. {len(LOG_LINES)} operations logged to REORGANIZE-LOG.md")

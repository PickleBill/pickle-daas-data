#!/bin/bash
# Courtana DaaS Nightly Pipeline
# Runs automatically at 2 AM via cron
# Logs to agents/cron-log.txt

DAAS_DIR="/Users/billbricker/PickleBill Dropbox/PickleBill Team Folder/Claude Projects/PICKLE-DAAS"
LOG="$DAAS_DIR/agents/cron-log.txt"
PYTHON=$(which python3)

echo "$(date '+%Y-%m-%d %H:%M:%S') — Starting nightly pipeline" >> "$LOG"

cd "$DAAS_DIR" || { echo "$(date) — ERROR: Could not cd to $DAAS_DIR" >> "$LOG"; exit 1; }

if [ -f "agents/agent-loop.py" ]; then
    $PYTHON agents/agent-loop.py >> "$LOG" 2>&1
    echo "$(date '+%Y-%m-%d %H:%M:%S') — Pipeline complete" >> "$LOG"
else
    echo "$(date '+%Y-%m-%d %H:%M:%S') — agent-loop.py not ready yet, skipping" >> "$LOG"
fi

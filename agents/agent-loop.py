#!/usr/bin/env python3
"""
agent-loop.py — chief@courtana.com AI Employee
================================================
Master scheduler. Runs all agents in sequence. Designed for cron.

What it does:
  1. credential-validator.py  — abort if required keys fail
  2. corpus-auto-ingest.py    — fetch and analyze new Courtana clips
  3. slack-ops-announcer.py   — post summary to Slack #ops
  4. Writes run-log.json with timestamp, clips added, cost, errors

Usage:
  python agents/agent-loop.py                # Full run
  python agents/agent-loop.py --dry-run      # Validate only, no analysis
  python agents/agent-loop.py --skip-slack   # Skip Slack post
  python agents/agent-loop.py --max-clips 5  # Limit Gemini analysis

Cron example (nightly at 2 AM):
  0 2 * * * cd /path/to/PICKLE-DAAS && python agents/agent-loop.py >> agents/cron.log 2>&1

Log:  agents/run-log.json
"""

import os
import sys
import json
import subprocess
from pathlib import Path
from datetime import datetime

try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).parent.parent / ".env")
except ImportError:
    pass

# ---------------------------------------------------------------------------
# CONFIG
# ---------------------------------------------------------------------------

AGENTS_DIR   = Path(__file__).parent
ROOT         = AGENTS_DIR.parent
RUN_LOG_PATH = AGENTS_DIR / "run-log.json"
PYTHON       = sys.executable  # Use same Python interpreter running this script

# ---------------------------------------------------------------------------
# HELPERS
# ---------------------------------------------------------------------------

def log(msg: str):
    ts = datetime.now().strftime("%H:%M:%S")
    print(f"[{ts}] {msg}", flush=True)


def run_agent(script_name: str, extra_args: list[str] | None = None) -> dict:
    """
    Run an agent script as a subprocess. Returns result dict with:
      { name, success, returncode, stdout_tail, stderr_tail, duration_s }
    """
    script_path = AGENTS_DIR / script_name
    if not script_path.exists():
        return {
            "name": script_name,
            "success": False,
            "returncode": -1,
            "stdout_tail": "",
            "stderr_tail": f"Script not found: {script_path}",
            "duration_s": 0
        }

    cmd = [PYTHON, str(script_path)] + (extra_args or [])
    log(f"Running: {' '.join(cmd)}")

    start = datetime.now()
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            cwd=str(ROOT),
            timeout=600  # 10 minute max per agent
        )
        duration = (datetime.now() - start).total_seconds()

        # Print stdout live-ish (tail)
        if result.stdout:
            for line in result.stdout.strip().split("\n")[-20:]:
                print(f"  | {line}")

        if result.returncode != 0 and result.stderr:
            for line in result.stderr.strip().split("\n")[-10:]:
                print(f"  ! {line}")

        return {
            "name": script_name,
            "success": result.returncode == 0,
            "returncode": result.returncode,
            "stdout_tail": result.stdout.strip()[-800:] if result.stdout else "",
            "stderr_tail": result.stderr.strip()[-400:] if result.stderr else "",
            "duration_s": round(duration, 1)
        }

    except subprocess.TimeoutExpired:
        duration = (datetime.now() - start).total_seconds()
        log(f"  TIMEOUT after {duration:.0f}s")
        return {
            "name": script_name,
            "success": False,
            "returncode": -2,
            "stdout_tail": "",
            "stderr_tail": f"Timed out after {duration:.0f}s",
            "duration_s": round(duration, 1)
        }
    except Exception as e:
        duration = (datetime.now() - start).total_seconds()
        return {
            "name": script_name,
            "success": False,
            "returncode": -3,
            "stdout_tail": "",
            "stderr_tail": str(e),
            "duration_s": round(duration, 1)
        }


def read_ingest_summary() -> dict:
    """Pull clip count and cost from the most recent auto-ingest-log entry."""
    log_path = ROOT / "output" / "auto-ingest-log.json"
    if not log_path.exists():
        return {"clips_added": 0, "cost": 0.0}
    try:
        with open(log_path) as f:
            entries = json.load(f)
        if not entries:
            return {"clips_added": 0, "cost": 0.0}
        last = entries[-1]
        return {
            "clips_added": last.get("clips_analyzed", 0),
            "clips_found": last.get("clips_found", 0),
            "cost":        last.get("cost_so_far", 0.0),
            "status":      last.get("status", "?")
        }
    except Exception:
        return {"clips_added": 0, "cost": 0.0}


def save_run_log(entry: dict):
    """Append this run's record to run-log.json."""
    history = []
    if RUN_LOG_PATH.exists():
        try:
            with open(RUN_LOG_PATH) as f:
                history = json.load(f)
        except Exception:
            history = []

    history.append(entry)

    # Keep last 90 runs (~3 months of nightly runs)
    if len(history) > 90:
        history = history[-90:]

    with open(RUN_LOG_PATH, "w") as f:
        json.dump(history, f, indent=2)


# ---------------------------------------------------------------------------
# MAIN
# ---------------------------------------------------------------------------

def main():
    import argparse
    parser = argparse.ArgumentParser(description="Master agent loop for chief@courtana.com")
    parser.add_argument("--dry-run",    action="store_true", help="Validate creds only, no Gemini")
    parser.add_argument("--skip-slack", action="store_true", help="Skip Slack announcement")
    parser.add_argument("--max-clips",  type=int, default=20, help="Max clips for corpus ingest")
    args = parser.parse_args()

    run_start  = datetime.now()
    run_at     = run_start.isoformat()
    date_str   = run_start.strftime("%Y-%m-%d %H:%M")

    print("=" * 65)
    print("  agent-loop.py — chief@courtana.com")
    print(f"  {date_str} | dry_run={args.dry_run} | max_clips={args.max_clips}")
    print("=" * 65)

    agent_results = []
    run_errors    = []

    # ── STEP 1: Credential Validator ──────────────────────────────────────────
    log("\nSTEP 1/3 — credential-validator.py")
    cred_result = run_agent("credential-validator.py", ["--required"])
    agent_results.append(cred_result)

    if not cred_result["success"]:
        log("ABORT: Required credentials failed. Fix .env and re-run.")
        log(f"  Details: {cred_result['stderr_tail'][:200]}")
        run_errors.append("Credential validation failed — required keys missing or invalid")

        entry = {
            "run_at":      run_at,
            "status":      "aborted",
            "aborted_at":  "credential-validator",
            "clips_added": 0,
            "cost":        0.0,
            "errors":      run_errors,
            "agents":      agent_results,
            "duration_s":  round((datetime.now() - run_start).total_seconds(), 1)
        }
        save_run_log(entry)
        sys.exit(1)

    log("Credentials OK — continuing")

    # ── STEP 2: Corpus Auto-Ingest ─────────────────────────────────────────────
    log(f"\nSTEP 2/3 — corpus-auto-ingest.py (max_clips={args.max_clips})")
    ingest_args = ["--max-clips", str(args.max_clips)]
    if args.dry_run:
        ingest_args.append("--dry-run")

    ingest_result = run_agent("corpus-auto-ingest.py", ingest_args)
    agent_results.append(ingest_result)

    if not ingest_result["success"]:
        log("WARNING: corpus-auto-ingest failed (non-fatal, continuing)")
        run_errors.append(f"corpus-auto-ingest failed: {ingest_result['stderr_tail'][:150]}")
    else:
        log("Corpus ingest complete")

    # Read what was actually ingested
    ingest_summary = read_ingest_summary()
    log(f"  Clips added: {ingest_summary.get('clips_added', 0)}  |  "
        f"Cost: ${ingest_summary.get('cost', 0.0):.4f}")

    # ── STEP 3: Slack Announcer ────────────────────────────────────────────────
    if not args.skip_slack and not args.dry_run:
        log("\nSTEP 3/3 — slack-ops-announcer.py")
        slack_result = run_agent("slack-ops-announcer.py")
        agent_results.append(slack_result)

        if not slack_result["success"]:
            log("WARNING: Slack post failed (non-fatal)")
            run_errors.append(f"Slack post failed: {slack_result['stderr_tail'][:100]}")
        else:
            log("Slack post complete")
    else:
        reason = "dry_run" if args.dry_run else "skip_slack flag"
        log(f"\nSTEP 3/3 — Skipping Slack ({reason})")

    # ── FINAL SUMMARY ─────────────────────────────────────────────────────────
    duration = round((datetime.now() - run_start).total_seconds(), 1)

    overall_status = "success" if not run_errors else (
        "partial" if ingest_summary.get("clips_added", 0) > 0 else "failed"
    )

    entry = {
        "run_at":      run_at,
        "status":      overall_status,
        "clips_found": ingest_summary.get("clips_found", 0),
        "clips_added": ingest_summary.get("clips_added", 0),
        "cost":        ingest_summary.get("cost", 0.0),
        "errors":      run_errors,
        "agents":      [
            {k: v for k, v in r.items() if k not in ("stdout_tail", "stderr_tail")}
            for r in agent_results
        ],
        "duration_s":  duration
    }
    save_run_log(entry)

    print("\n" + "=" * 65)
    print(f"  RUN COMPLETE")
    print("=" * 65)
    print(f"  Status:        {overall_status.upper()}")
    print(f"  New clips:     {ingest_summary.get('clips_added', 0)}")
    print(f"  Cost this run: ${ingest_summary.get('cost', 0.0):.4f}")
    print(f"  Duration:      {duration}s")
    print(f"  Log:           {RUN_LOG_PATH}")

    if run_errors:
        print(f"\n  Errors ({len(run_errors)}):")
        for e in run_errors:
            print(f"    - {e}")

    print("=" * 65)

    sys.exit(0 if overall_status in ("success", "partial") else 1)


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
slack-ops-announcer.py — chief@courtana.com AI Employee
=========================================================
The notification backbone for the AI Chief of Staff system.

Bill wants to be on his phone, not his laptop. This script is how the
AI surfaces everything: completed work, decisions needed, actions only
Bill can take, links and inline content.

Supports TWO auth modes:
  1. Incoming Webhook (simplest — just one URL, no bot setup)
     Set: SLACK_WEBHOOK_URL in .env
  2. Bot Token (more control — can read channels, post to specific channels)
     Set: SLACK_BOT_TOKEN + SLACK_OPS_CHANNEL in .env

What it does each run:
  1. Reads the most recent morning brief from output/briefs/
  2. Reads pending decisions from output/pending-decisions.json
  3. Formats a rich Slack message: brief highlights + decisions + bill-only actions
  4. Posts via webhook or bot token
  5. If neither configured: saves to agents/pending-slack-posts.json

Usage:
  python agents/slack-ops-announcer.py              # Normal nightly post
  python agents/slack-ops-announcer.py --test       # Send test message
  python agents/slack-ops-announcer.py --decisions  # Post decisions digest only
  python agents/slack-ops-announcer.py --file <path> # Specific brief

Called by: agent-loop.py (nightly, after corpus-auto-ingest.py)

SETUP (5 min):
  1. Go to https://api.slack.com/apps → Create New App → From Scratch
  2. "Incoming Webhooks" → Activate → Add New Webhook to Workspace → #ops-ai
  3. Copy the webhook URL → paste into .env as SLACK_WEBHOOK_URL
"""

import os
import sys
import json
import re
import urllib.request
import urllib.error
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

ROOT               = Path(__file__).parent.parent
AGENTS_DIR         = Path(__file__).parent
PENDING_POSTS_PATH = AGENTS_DIR / "pending-slack-posts.json"
DECISIONS_PATH     = ROOT / "output" / "pending-decisions.json"

# Auth mode 1: Incoming Webhook (recommended — easiest to set up)
SLACK_WEBHOOK_URL  = os.getenv("SLACK_WEBHOOK_URL", "")

# Auth mode 2: Bot Token (needed to read channels for ideas-intake)
SLACK_BOT_TOKEN    = os.getenv("SLACK_BOT_TOKEN", "")
SLACK_OPS_CHANNEL  = os.getenv("SLACK_OPS_CHANNEL", "")

# Bill's Slack user ID for @mentions on decisions
BILL_SLACK_ID      = os.getenv("BILL_SLACK_USER_ID", "")

# Brief search locations (most recent first)
BRIEF_SEARCH_PATHS = [
    ROOT / "output" / "briefs",
    ROOT / "output",
]

# ---------------------------------------------------------------------------
# HELPERS
# ---------------------------------------------------------------------------

def log(msg: str):
    ts = datetime.now().strftime("%H:%M:%S")
    print(f"[{ts}] {msg}")


# ---------------------------------------------------------------------------
# DECISIONS QUEUE
# ---------------------------------------------------------------------------

def load_pending(clear: bool = False) -> dict:
    """Load pending decisions/bill-actions from output/pending-decisions.json."""
    if not DECISIONS_PATH.exists():
        return {"decisions": [], "bill_actions": []}
    data = json.loads(DECISIONS_PATH.read_text())
    if clear:
        DECISIONS_PATH.write_text(json.dumps({"decisions": [], "bill_actions": []}, indent=2))
    return data


def queue_decision(question: str, context: str = "", deal: str = "", deadline: str = ""):
    """Add a decision Bill must make to the pending queue."""
    pending = load_pending()
    pending.setdefault("decisions", []).append({
        "question": question, "context": context,
        "deal": deal, "deadline": deadline,
        "queued": datetime.now().isoformat(),
    })
    DECISIONS_PATH.parent.mkdir(parents=True, exist_ok=True)
    DECISIONS_PATH.write_text(json.dumps(pending, indent=2))


def queue_bill_action(action: str, context: str = "", deal: str = ""):
    """Add a Bill-only action to the pending queue."""
    pending = load_pending()
    pending.setdefault("bill_actions", []).append({
        "action": action, "context": context, "deal": deal,
        "queued": datetime.now().isoformat(),
    })
    DECISIONS_PATH.parent.mkdir(parents=True, exist_ok=True)
    DECISIONS_PATH.write_text(json.dumps(pending, indent=2))


def format_decisions_section(pending: dict) -> str:
    """Format the decisions + bill-actions as Slack mrkdwn text."""
    lines = []
    decisions = pending.get("decisions", [])
    bill_actions = pending.get("bill_actions", [])

    if not decisions and not bill_actions:
        return ""

    mention = f"<@{BILL_SLACK_ID}> " if BILL_SLACK_ID else ""

    if decisions:
        lines.append(f"\n{mention}:large_orange_circle: *Decisions Needed*")
        for d in decisions:
            tag = f" [{d['deal']}]" if d.get("deal") else ""
            deadline = f" _(by {d['deadline']})_" if d.get("deadline") else ""
            lines.append(f"  • {d['question']}{tag}{deadline}")

    if bill_actions:
        lines.append(f"\n:bust_in_silhouette: *Bill Must Do*")
        for a in bill_actions:
            tag = f" [{a['deal']}]" if a.get("deal") else ""
            lines.append(f"  • {a['action']}{tag}")

    return "\n".join(lines)


def find_most_recent_brief() -> Path | None:
    """Find the most recent MORNING-BRIEF markdown file."""
    candidates = []

    for search_dir in BRIEF_SEARCH_PATHS:
        if search_dir.exists():
            for f in search_dir.glob("MORNING-BRIEF*.md"):
                candidates.append(f)
            # Also check subdirectories named discoveries-* or briefs-*
            for subdir in search_dir.glob("discoveries-*"):
                if subdir.is_dir():
                    for f in subdir.glob("MORNING-BRIEF*.md"):
                        candidates.append(f)

    if not candidates:
        # Fallback: look for any .md in output/ with "brief" in the name
        for f in ROOT.glob("output/**/*.md"):
            if "brief" in f.name.lower() or "morning" in f.name.lower():
                candidates.append(f)

    if not candidates:
        return None

    # Return most recently modified
    return max(candidates, key=lambda f: f.stat().st_mtime)


def find_ingest_log() -> dict | None:
    """Read the most recent auto-ingest-log entry for build summary."""
    log_path = ROOT / "output" / "auto-ingest-log.json"
    if not log_path.exists():
        return None
    with open(log_path) as f:
        entries = json.load(f)
    if not entries:
        return None
    return entries[-1]  # Most recent entry


def extract_key_findings(brief_text: str, max_lines: int = 12) -> str:
    """Pull the most important lines from a morning brief for Slack."""
    lines = brief_text.split("\n")
    findings = []

    # Grab section headers and their first content line
    capture_next = False
    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue

        # Section headers (## or ###)
        if stripped.startswith("## ") or stripped.startswith("### "):
            header = stripped.lstrip("#").strip()
            # Skip boilerplate headers
            skip = ["table of contents", "contents", "generated", "footer"]
            if any(s in header.lower() for s in skip):
                continue
            findings.append(f"\n*{header}*")
            capture_next = True
            continue

        # Bullet points
        if stripped.startswith(("- ", "• ", "* ", "→ ")):
            text = stripped.lstrip("-•*→ ").strip()
            if text and len(text) > 10:
                findings.append(f"  • {text[:120]}")
                capture_next = False
            continue

        # First line after a header
        if capture_next and len(stripped) > 15:
            findings.append(f"  {stripped[:140]}")
            capture_next = False

        if len(findings) >= max_lines:
            break

    return "\n".join(findings[:max_lines])


def format_slack_message(brief_path: "Path | None", ingest_entry: "dict | None",
                          pending: dict = None) -> str:
    """Format a rich Slack message from brief + ingest log + decisions."""
    date_str = datetime.now().strftime("%A, %B %d")
    lines = [f":briefcase: *chief@courtana.com — Overnight Build | {date_str}*"]
    lines.append("─" * 40)

    # Ingest stats if available
    if ingest_entry:
        clips_found    = ingest_entry.get("clips_found", 0)
        clips_analyzed = ingest_entry.get("clips_analyzed", 0)
        cost           = ingest_entry.get("cost_so_far", 0.0)
        status         = ingest_entry.get("status", "?")
        batch_dir      = ingest_entry.get("batch_dir", "")

        lines.append(f"\n:movie_camera: *Corpus Ingest*")
        lines.append(f"  • New clips found: *{clips_found}*")
        lines.append(f"  • Clips analyzed: *{clips_analyzed}*")
        lines.append(f"  • Cost this run: *${cost:.4f}*")
        lines.append(f"  • Status: {status}")
        if batch_dir:
            batch_name = Path(batch_dir).name
            lines.append(f"  • Batch: `{batch_name}`")

    # Morning brief content
    if brief_path and brief_path.exists():
        brief_text = brief_path.read_text(encoding="utf-8")
        findings = extract_key_findings(brief_text)
        if findings:
            lines.append(f"\n:sunrise: *Morning Brief Highlights*")
            lines.append(findings)
        lines.append(f"\n_Brief: `{brief_path.name}`_")
    else:
        lines.append("\n_No morning brief found for today._")

    # Decisions + bill-only actions
    if pending is None:
        pending = load_pending()
    decisions_text = format_decisions_section(pending)
    if decisions_text:
        lines.append(decisions_text)

    lines.append(f"\n─────────────────────────────────────────")
    lines.append(f"_Run by chief@courtana.com at {datetime.now().strftime('%H:%M')} local_")

    return "\n".join(lines)


def post_via_webhook(message: str) -> bool:
    """Post via incoming webhook (simplest setup — just one URL)."""
    payload = json.dumps({"text": message, "mrkdwn": True}).encode()
    req = urllib.request.Request(
        SLACK_WEBHOOK_URL, data=payload,
        headers={"Content-Type": "application/json"}
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            body = r.read().decode()
            if body == "ok":
                log("Posted via webhook ✓")
                return True
            log(f"Webhook response: {body}")
            return False
    except Exception as e:
        log(f"Webhook error: {e}")
        return False


def post_to_slack(message: str, channel: str, token: str) -> bool:
    """Post a message to Slack via Bot Token. Returns True on success."""
    payload = json.dumps({
        "channel": channel,
        "text": message,
        "mrkdwn": True,
        "unfurl_links": False
    }).encode()

    req = urllib.request.Request(
        "https://slack.com/api/chat.postMessage",
        data=payload,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {token}"
        }
    )

    max_retries = 3
    for attempt in range(max_retries):
        try:
            with urllib.request.urlopen(req, timeout=15) as r:
                resp = json.loads(r.read())
                if resp.get("ok"):
                    return True
                else:
                    error = resp.get("error", "unknown_error")
                    log(f"Slack API error: {error}")
                    if error in ("ratelimited",):
                        time.sleep(2 ** attempt)
                        continue
                    return False
        except urllib.error.HTTPError as e:
            log(f"Slack HTTP error {e.code}: {e.reason}")
            if e.code == 429:
                import time
                time.sleep(2 ** attempt)
            else:
                return False
        except Exception as e:
            log(f"Slack request error: {e}")
            return False

    return False


def save_pending_post(message: str, channel: str):
    """Save the message to pending-slack-posts.json for later sending."""
    pending = []
    if PENDING_POSTS_PATH.exists():
        with open(PENDING_POSTS_PATH) as f:
            pending = json.load(f)

    pending.append({
        "queued_at": datetime.now().isoformat(),
        "channel": channel,
        "message": message,
        "status": "pending"
    })

    # Keep last 30 pending posts
    if len(pending) > 30:
        pending = pending[-30:]

    with open(PENDING_POSTS_PATH, "w") as f:
        json.dump(pending, f, indent=2)

    log(f"Message saved to {PENDING_POSTS_PATH} (will send when SLACK_BOT_TOKEN is configured)")


# ---------------------------------------------------------------------------
# MAIN
# ---------------------------------------------------------------------------

def main():
    import argparse
    parser = argparse.ArgumentParser(description="Post build summary to Slack")
    parser.add_argument("--file",      type=str,  help="Path to specific brief file")
    parser.add_argument("--channel",   type=str,  help="Override Slack channel ID (bot mode)")
    parser.add_argument("--test",      action="store_true", help="Send a test message to verify setup")
    parser.add_argument("--decisions", action="store_true", help="Post decisions digest only")
    args = parser.parse_args()

    print("=" * 60)
    print("  slack-ops-announcer.py — chief@courtana.com")
    print("=" * 60)

    # ── Test mode ──────────────────────────────────────────────────────────────
    if args.test:
        queue_decision("Should I post daily briefs to Slack at 7am?",
                        context="Nightly builds complete around 2am. Morning brief is ready by 7am.",
                        deal="Setup")
        queue_bill_action("Add SLACK_WEBHOOK_URL to PICKLE-DAAS/.env (5 min setup)",
                           context="One-time setup. See BILL-OS/NOTIFICATION-SETUP.md for the link.")
        pending = load_pending()
        message = (
            ":test_tube: *chief@courtana.com — TEST MESSAGE*\n"
            "If you see this, your Slack integration is working!\n"
            + format_decisions_section(pending)
            + "\n\n_Add SLACK_WEBHOOK_URL to .env to enable real builds._"
        )
        log("Sending test message...")
        _send_message(message, args.channel)
        return

    # ── Decisions-only mode ────────────────────────────────────────────────────
    if args.decisions:
        pending = load_pending()
        if not pending.get("decisions") and not pending.get("bill_actions"):
            log("No pending decisions or actions.")
            return
        message = (
            f":large_orange_circle: *Daily Decisions Digest — {datetime.now().strftime('%b %d')}*\n"
            + format_decisions_section(pending)
        )
        _send_message(message, args.channel)
        return

    # ── Normal nightly post ────────────────────────────────────────────────────
    # Find brief
    if args.file:
        brief_path = Path(args.file)
        if not brief_path.exists():
            log(f"ERROR: Specified brief not found: {args.file}")
            sys.exit(1)
    else:
        brief_path = find_most_recent_brief()
        if brief_path:
            log(f"Found brief: {brief_path.name}")
        else:
            log("No morning brief found — will post ingest stats only")

    # Load ingest log
    ingest_entry = find_ingest_log()
    if ingest_entry:
        log(f"Ingest log: {ingest_entry.get('clips_analyzed', 0)} clips, "
            f"${ingest_entry.get('cost_so_far', 0):.4f}")

    # Load decisions
    pending = load_pending()
    if pending.get("decisions") or pending.get("bill_actions"):
        log(f"Pending: {len(pending.get('decisions',[]))} decisions, "
            f"{len(pending.get('bill_actions',[]))} bill-actions")

    # Build the message
    message = format_slack_message(brief_path, ingest_entry, pending)

    log(f"\nMessage preview ({len(message)} chars):")
    print("-" * 40)
    print(message[:600] + ("..." if len(message) > 600 else ""))
    print("-" * 40)

    _send_message(message, args.channel)


def _send_message(message: str, channel_override: str = None):
    """Try webhook first, then bot token, then save to pending."""
    # Mode 1: Incoming Webhook (easiest)
    if SLACK_WEBHOOK_URL:
        success = post_via_webhook(message)
        if success:
            return
        log("Webhook failed — trying bot token...")

    # Mode 2: Bot Token
    channel = channel_override or SLACK_OPS_CHANNEL
    if SLACK_BOT_TOKEN and channel:
        success = post_to_slack(message, channel, SLACK_BOT_TOKEN)
        if success:
            log("Posted via bot token ✓")
            return
        log("Bot token post failed — saving to pending")

    # Fallback: save to file
    if not SLACK_WEBHOOK_URL and not SLACK_BOT_TOKEN:
        print("\n⚠️  No Slack credentials configured.")
        print("   Quick setup (5 min): See BILL-OS/NOTIFICATION-SETUP.md")
        print("   Or add SLACK_WEBHOOK_URL to PICKLE-DAAS/.env\n")

    save_pending_post(message, channel_override or SLACK_OPS_CHANNEL or "PENDING")
    print(f"Message saved to {PENDING_POSTS_PATH}")


if __name__ == "__main__":
    main()

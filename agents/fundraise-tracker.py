#!/usr/bin/env python3
"""
fundraise-tracker.py — chief@courtana.com AI Employee
=======================================================
Tracks fundraise progress, flags stale investors, and
posts a weekly digest to Slack.

Data source: BILL-OS/BILL-OS.md (ground truth) + Gmail (for thread activity)
Output: output/fundraise/fundraise-YYYYMMDD.json + .md summary

Usage:
  python agents/fundraise-tracker.py           # Run tracker, post to Slack
  python agents/fundraise-tracker.py --report  # Print report only, no Slack
  python agents/fundraise-tracker.py --update-raised 410000  # Update raised amount

Called by: agent-loop.py (weekly)
"""

import os
import sys
import json
import re
import urllib.request
import urllib.error
from datetime import datetime, date, timedelta
from pathlib import Path

try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).parent.parent / ".env")
except ImportError:
    pass

# ── Config ────────────────────────────────────────────────────────────────────
ROOT       = Path(__file__).parent.parent
OUTPUT_DIR = ROOT / "output" / "fundraise"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

SLACK_WEBHOOK_URL = os.getenv("SLACK_WEBHOOK_URL", "")
BILL_OS_PATH      = ROOT.parent / "BILL-OS" / "BILL-OS.md"

# ── Ground Truth (from BILL-OS.md — update this when raise progresses) ────────
RAISE_DATA = {
    "goal_tranche1": 500_000,
    "goal_tranche2": 800_000,
    "goal_total":    1_300_000,
    "valuation_t1":  5_000_000,
    "valuation_t2":  8_000_000,
    "raised_so_far": 396_000,   # Update via --update-raised
    "raised_file":   OUTPUT_DIR / "raised-amount.json",  # Persists updates
}

INVESTORS = [
    # Committed
    {"name": "Brian Mock",         "email": "unknown",                        "status": "committed",  "amount_range": "50000-100000", "notes": "In"},
    {"name": "Klaus Borum",        "email": "clausvesterbyborum@gmail.com",   "status": "committed",  "amount_range": "unknown",      "notes": "Frederick/Trackman bridge"},
    {"name": "Napier",             "email": "unknown",                        "status": "committed",  "amount_range": "unknown",      "notes": "In"},
    {"name": "Eric Begulin",       "email": "unknown",                        "status": "committed",  "amount_range": "unknown",      "notes": "In"},
    # Active pipeline
    {"name": "Henry Ciocca",       "email": "unknown",                        "status": "pipeline",   "amount_range": "unknown",      "notes": "Meeting happened Mar 26"},
    {"name": "Matt Rosenbloom",    "email": "unknown",                        "notes": "Lauf Capital", "status": "pipeline"},
    {"name": "Brent Collins",      "email": "unknown",                        "status": "pipeline",   "notes": "To close"},
    {"name": "John Rabby",         "email": "unknown",                        "status": "pipeline",   "notes": "To close"},
    {"name": "Bill Culpepper",     "email": "unknown",                        "status": "pipeline",   "notes": "To close"},
    {"name": "Scot McClintic",     "email": "scot@betfanatics.com",           "status": "pipeline",   "notes": "First call Mar 29 — follow up needed"},
    # Passed
    {"name": "Pat Newton",         "email": "pnewton@newtonperformance.com",  "status": "passed",     "notes": "Declined Mar 29, no bridge burned"},
]

STALE_DAYS_WARNING = 10
STALE_DAYS_URGENT  = 21

# ── Persistence ───────────────────────────────────────────────────────────────

def load_raised_amount() -> int:
    """Load the current raised amount from file (persists --update-raised calls)."""
    raised_file = RAISE_DATA["raised_file"]
    if isinstance(raised_file, Path) and raised_file.exists():
        try:
            data = json.loads(raised_file.read_text())
            return data.get("raised", RAISE_DATA["raised_so_far"])
        except Exception:
            pass
    return RAISE_DATA["raised_so_far"]


def save_raised_amount(amount: int):
    """Persist an updated raised amount."""
    raised_file = RAISE_DATA["raised_file"]
    if isinstance(raised_file, Path):
        raised_file.write_text(json.dumps({"raised": amount, "updated": datetime.now().isoformat()}, indent=2))
    print(f"[fundraise] Raised amount updated: ${amount:,}")


# ── Analysis ──────────────────────────────────────────────────────────────────

def compute_progress(raised: int) -> dict:
    t1_goal  = RAISE_DATA["goal_tranche1"]
    t1_pct   = round(raised / t1_goal * 100, 1)
    gap      = max(0, t1_goal - raised)
    total    = RAISE_DATA["goal_total"]

    return {
        "raised":       raised,
        "t1_goal":      t1_goal,
        "t1_pct":       t1_pct,
        "t1_gap":       gap,
        "total_goal":   total,
        "total_pct":    round(raised / total * 100, 1),
        "status_emoji": "🟢" if t1_pct >= 90 else ("🟡" if t1_pct >= 70 else "🔴"),
    }


def check_gmail_activity(investors: list) -> dict:
    """
    Try to check Gmail for recent investor email activity.
    Returns dict: {investor_name: {"last_contact_days": N, "last_subject": ""}}
    Falls back to empty dict if Gmail not configured.
    """
    results = {}
    gmail_key = os.getenv("GMAIL_OAUTH_TOKEN_PATH", "")
    if not gmail_key:
        # No Gmail — check .env for a credentials file
        creds_file = Path(__file__).parent / "credentials" / "gmail-token.json"
        if not creds_file.exists():
            return {}  # Silent fallback — Gmail not set up yet

    # Gmail API via stored OAuth token
    # This mirrors the pattern in gmail-deal-scanner.py
    try:
        import base64, email.utils
        token_file = creds_file if 'creds_file' in dir() else Path(gmail_key)
        if not token_file.exists():
            return {}
        token_data = json.loads(token_file.read_text())
        access_token = token_data.get("access_token", "")
        if not access_token:
            return {}

        for inv in investors:
            email_addr = inv.get("email", "")
            if not email_addr or email_addr == "unknown":
                continue
            name = inv["name"]
            # Search Gmail for threads with this contact
            query = urllib.parse.quote(f"from:{email_addr} OR to:{email_addr}")
            url = f"https://gmail.googleapis.com/gmail/v1/users/me/threads?q={query}&maxResults=1"
            req = urllib.request.Request(url, headers={"Authorization": f"Bearer {access_token}"})
            try:
                with urllib.request.urlopen(req, timeout=10) as r:
                    data = json.loads(r.read())
                threads = data.get("threads", [])
                if threads:
                    thread_id = threads[0]["id"]
                    thread_url = f"https://gmail.googleapis.com/gmail/v1/users/me/threads/{thread_id}"
                    req2 = urllib.request.Request(thread_url,
                                                   headers={"Authorization": f"Bearer {access_token}"})
                    with urllib.request.urlopen(req2, timeout=10) as r2:
                        thread_data = json.loads(r2.read())
                    messages = thread_data.get("messages", [])
                    if messages:
                        last_msg = messages[-1]
                        internal_date = int(last_msg.get("internalDate", 0)) // 1000
                        last_dt = datetime.fromtimestamp(internal_date)
                        days_ago = (datetime.now() - last_dt).days
                        subject = ""
                        for h in last_msg.get("payload", {}).get("headers", []):
                            if h["name"] == "Subject":
                                subject = h["value"][:80]
                                break
                        results[name] = {"last_contact_days": days_ago, "last_subject": subject}
            except Exception:
                continue
    except Exception:
        pass

    return results


def build_report(raised: int, gmail_activity: dict = None) -> dict:
    """Build the full fundraise report."""
    progress = compute_progress(raised)
    gmail_activity = gmail_activity or {}

    pipeline = [i for i in INVESTORS if i["status"] == "pipeline"]
    committed = [i for i in INVESTORS if i["status"] == "committed"]
    passed = [i for i in INVESTORS if i["status"] == "passed"]

    # Flag stale pipeline investors
    stale_warnings = []
    for inv in pipeline:
        name = inv["name"]
        activity = gmail_activity.get(name, {})
        days = activity.get("last_contact_days", None)
        if days is not None:
            if days >= STALE_DAYS_URGENT:
                stale_warnings.append({"name": name, "days": days, "level": "URGENT",
                                        "subject": activity.get("last_subject", "")})
            elif days >= STALE_DAYS_WARNING:
                stale_warnings.append({"name": name, "days": days, "level": "WARNING",
                                        "subject": activity.get("last_subject", "")})

    return {
        "generated": datetime.now().isoformat(),
        "progress": progress,
        "investors": {
            "committed": committed,
            "pipeline": pipeline,
            "passed": passed,
        },
        "stale_warnings": sorted(stale_warnings, key=lambda x: x["days"], reverse=True),
        "gmail_active": bool(gmail_activity),
    }


# ── Output ────────────────────────────────────────────────────────────────────

def write_outputs(report: dict) -> tuple:
    ts = date.today().strftime("%Y%m%d")
    p = report["progress"]

    # JSON
    json_path = OUTPUT_DIR / f"fundraise-{ts}.json"
    json_path.write_text(json.dumps(report, indent=2))

    # Markdown
    pipeline = report["investors"]["pipeline"]
    stale    = report["stale_warnings"]

    lines = [
        f"# Fundraise Status — {date.today().strftime('%B %d, %Y')}\n",
        f"**Raised:** ${p['raised']:,} / ${p['t1_goal']:,} (Tranche 1) — "
        f"**{p['t1_pct']}%** {p['status_emoji']}\n",
        f"**Gap to T1 close:** ${p['t1_gap']:,}\n",
        f"**Total goal:** ${p['total_goal']:,} ({p['total_pct']}% overall)\n",
        "\n## Pipeline\n",
    ]
    for inv in pipeline:
        lines.append(f"- **{inv['name']}** — {inv.get('notes', 'No notes')}\n")

    if stale:
        lines.append("\n## ⚠️ Stale Investors\n")
        for s in stale:
            lines.append(f"- [{s['level']}] **{s['name']}** — {s['days']}d since last contact  \n")
            if s["subject"]:
                lines.append(f"  Last: _{s['subject']}_\n")

    lines.append("\n## Committed\n")
    for inv in report["investors"]["committed"]:
        lines.append(f"- **{inv['name']}** — {inv.get('notes', '')}\n")

    md_path = OUTPUT_DIR / f"fundraise-{ts}.md"
    md_path.write_text("".join(lines))

    print(f"[output] {json_path}")
    print(f"[output] {md_path}")
    return json_path, md_path


def post_to_slack(report: dict):
    """Post fundraise digest to Slack."""
    if not SLACK_WEBHOOK_URL:
        print("[slack] No SLACK_WEBHOOK_URL — skipping")
        return
    p = report["progress"]
    stale = report["stale_warnings"]

    bar_filled = round(p["t1_pct"] / 10)
    bar = "█" * bar_filled + "░" * (10 - bar_filled)

    text = (
        f":money_with_wings: *Fundraise Update — {date.today().strftime('%b %d')}*\n"
        f"`{bar}` {p['t1_pct']}% — ${p['raised']:,} raised of ${p['t1_goal']:,}\n"
        f"Gap to close: *${p['t1_gap']:,}*\n"
    )
    if stale:
        text += "\n:warning: *Stale investors:*\n"
        for s in stale[:3]:
            text += f"  • {s['name']} — {s['days']}d no contact [{s['level']}]\n"

    payload = json.dumps({"text": text}).encode()
    req = urllib.request.Request(SLACK_WEBHOOK_URL, data=payload,
                                  headers={"Content-Type": "application/json"})
    try:
        urllib.request.urlopen(req, timeout=10)
        print("[slack] Fundraise digest posted")
    except Exception as e:
        print(f"[slack] Failed: {e}")


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    import argparse
    parser = argparse.ArgumentParser(description="Fundraise tracker")
    parser.add_argument("--report",       action="store_true", help="Print report, no Slack")
    parser.add_argument("--update-raised", type=int,           help="Update raised amount (e.g. 410000)")
    args = parser.parse_args()

    if args.update_raised:
        save_raised_amount(args.update_raised)
        return

    raised = load_raised_amount()
    print(f"[fundraise] Current raised: ${raised:,}")

    # Check Gmail for stale investors (optional — works if OAuth configured)
    gmail_activity = check_gmail_activity(INVESTORS)
    if gmail_activity:
        print(f"[gmail] Activity data for {len(gmail_activity)} investors")
    else:
        print("[gmail] Not configured — using static data only")

    # Build report
    report = build_report(raised, gmail_activity)

    # Print summary
    p = report["progress"]
    print(f"\n{'='*50}")
    print(f"Fundraise: {p['t1_pct']}% of T1 ({p['status_emoji']})")
    print(f"Raised: ${p['raised']:,}  |  Gap: ${p['t1_gap']:,}")
    if report["stale_warnings"]:
        print(f"Stale investors: {len(report['stale_warnings'])}")
    print("=" * 50)

    # Write outputs
    write_outputs(report)

    # Slack
    if not args.report:
        post_to_slack(report)

    print("\n✓ Done. Check output/fundraise/ for results.")


if __name__ == "__main__":
    main()

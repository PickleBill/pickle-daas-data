#!/usr/bin/env python3
"""
Gmail Deal Scanner — chief@courtana.com AI Employee
Scans bill@courtana.com for deal threads gone silent. Drafts follow-ups.
Run: python agents/gmail-deal-scanner.py
Schedule: Monday 7 AM, Thursday 3 PM
"""

import os
import json
import base64
from datetime import datetime, timedelta
from pathlib import Path

try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).parent.parent / ".env")
except ImportError:
    pass

ROOT = Path(__file__).parent.parent
BILL_OS = ROOT.parent / "BILL-OS"
NOW = datetime.now()

# ── Deal contacts (sourced from BILL-OS.md) ────────────────────────────────────
DEAL_CONTACTS = {
    "Peak Pickleball": {
        "emails": ["chris@peakpickleball.club", "leah@peakpickleball.club"],
        "deal_size": "Venue #1 — 6 courts, pilot 55/45",
        "urgency": "HIGH",  # Grand opening May 9
        "context": "Grand opening May 9. Hardware ship + install plan needed. Camera spec for IT guy.",
    },
    "Court Kings": {
        "emails": ["richard@courtkings.com", "bryan@courtkings.com"],
        "deal_size": "$250-500K + RevShare",
        "urgency": "MONITOR",  # Rich on vacation until ~Apr 24
        "context": "Rich on vacation until ~Apr 24. NDA + engagement goals sent. Demo ready.",
    },
    "Concord": {
        "emails": [],  # Chris Williams email not confirmed
        "deal_size": "Venue deal",
        "urgency": "MEDIUM",  # Back from SD week of Apr 14
        "context": "Chris W. back week of Apr 14. Main objection: doesn't want second system.",
    },
    "Rally Pickleball (Barrett)": {
        "emails": [],  # Need Barrett's email
        "deal_size": "Venue warm intro",
        "urgency": "MEDIUM",
        "context": "Warm venue intro — no response to original outreach. Overdue.",
    },
    "Scot McClintic": {
        "emails": [],
        "deal_size": "~$104K gap to $500K tranche",
        "urgency": "HIGH",
        "context": "First call 3/29. Need to close gap to $500K first tranche.",
    },
    "George Kaminis": {
        "emails": [],
        "deal_size": "COO engagement",
        "urgency": "MEDIUM",
        "context": "COO proposal promised — overdue.",
    },
}

# ── Draft templates ────────────────────────────────────────────────────────────
DRAFT_TEMPLATES = {
    "Peak Pickleball": {
        "subject": "[OPS-DRAFT] Peak Pickleball — Install Plan Update",
        "body": """Hi Chris + Leah,

Wanted to follow up on the hardware and install plan for the 6 courts at Peak.

[INSERT: Current status on camera spec sheet for IT guy]

We're targeting install well ahead of the May 9 grand opening. Can we lock in a time this week to finalize the layout and get the spec sheet to your IT team?

Looking forward to Peak being Courtana venue #1.

Bill""",
    },
    "Court Kings": {
        "subject": "[OPS-DRAFT] Court Kings — Ready When You're Back",
        "body": """Hi Rich / Bryan,

Just a quick note — we've been building out the Kings Court Coach demo while you've been out and it's looking sharp.

When you're back and ready, I'd love to get 30 minutes on the calendar to walk you through what's new.

Talk soon,
Bill""",
    },
    "Scot McClintic": {
        "subject": "[OPS-DRAFT] Courtana — Following Up",
        "body": """Hi Scot,

Great speaking with you on 3/29. Wanted to follow up and see where your head is at on the Courtana opportunity.

[INSERT: Specific follow-up based on call notes]

Would love to find a time to reconnect.

Bill""",
    },
}


def get_gmail_service():
    """Get authenticated Gmail service."""
    try:
        from google.oauth2.credentials import Credentials
        from google.auth.transport.requests import Request
        from googleapiclient.discovery import build

        token_path = Path(__file__).parent / "credentials" / "token.json"
        if not token_path.exists():
            return None

        creds = Credentials.from_authorized_user_file(str(token_path))
        if creds.expired and creds.refresh_token:
            creds.refresh(Request())
        return build("gmail", "v1", credentials=creds)
    except ImportError:
        return None
    except Exception as e:
        print(f"[scanner] Gmail auth failed: {e}")
        return None


def scan_thread_silence_mock():
    """Mock scan when Gmail not yet connected — uses BILL-OS data."""
    print("[scanner] Gmail not connected — running mock scan from BILL-OS data")
    results = []
    for name, contact in DEAL_CONTACTS.items():
        if contact["urgency"] in ("HIGH", "MEDIUM"):
            days_since = 14 if contact["urgency"] == "HIGH" else 8
            results.append({
                "contact": name,
                "urgency": contact["urgency"],
                "days_silent": days_since,
                "deal_size": contact["deal_size"],
                "context": contact["context"],
                "has_draft_template": name in DRAFT_TEMPLATES,
            })
    return results


def scan_gmail_for_silence(service):
    """Real Gmail scan: find contacts not heard from in 7+ days."""
    results = []
    for name, contact in DEAL_CONTACTS.items():
        if not contact["emails"]:
            continue
        for email in contact["emails"]:
            try:
                # Search for threads with this contact in last 30 days
                query = f"from:{email} OR to:{email} newer_than:30d"
                threads = service.users().threads().list(userId="me", q=query).execute()
                thread_list = threads.get("threads", [])

                if not thread_list:
                    results.append({
                        "contact": name,
                        "email": email,
                        "urgency": "URGENT",
                        "days_silent": 30,
                        "deal_size": contact["deal_size"],
                        "context": contact["context"],
                        "has_draft_template": name in DRAFT_TEMPLATES,
                    })
                else:
                    # Get most recent thread
                    latest = service.users().threads().get(
                        userId="me", id=thread_list[0]["id"], format="minimal"
                    ).execute()
                    messages = latest.get("messages", [])
                    if messages:
                        ts = int(messages[-1]["internalDate"]) / 1000
                        last_date = datetime.fromtimestamp(ts)
                        days_since = (NOW - last_date).days
                        if days_since >= 7:
                            urgency = "URGENT" if days_since >= 14 else "WARNING"
                            results.append({
                                "contact": name,
                                "email": email,
                                "urgency": urgency,
                                "days_silent": days_since,
                                "deal_size": contact["deal_size"],
                                "context": contact["context"],
                                "has_draft_template": name in DRAFT_TEMPLATES,
                            })
            except Exception as e:
                print(f"[scanner] Error checking {email}: {e}")
    return results


def create_gmail_draft(service, to_email, subject, body):
    """Create a draft in Gmail."""
    try:
        message = {
            "raw": base64.urlsafe_b64encode(
                f"To: {to_email}\nSubject: {subject}\n\n{body}".encode()
            ).decode()
        }
        draft = service.users().drafts().create(userId="me", body={"message": message}).execute()
        return draft["id"]
    except Exception as e:
        print(f"[scanner] Draft creation failed: {e}")
        return None


def post_to_slack(message: str):
    """Post summary to Slack #deals channel."""
    token = os.getenv("SLACK_BOT_TOKEN")
    channel = os.getenv("SLACK_DEALS_CHANNEL")
    if not token or not channel:
        print(f"[scanner] Slack not configured — would post:\n{message[:200]}")
        return

    import urllib.request
    payload = json.dumps({"channel": channel, "text": message}).encode()
    req = urllib.request.Request(
        "https://slack.com/api/chat.postMessage",
        data=payload,
        headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as r:
            result = json.loads(r.read())
            if result.get("ok"):
                print("[scanner] ✓ Posted to Slack #deals")
    except Exception as e:
        print(f"[scanner] Slack post failed: {e}")


def generate_report(silent_contacts: list) -> str:
    """Generate the deal silence report."""
    urgent = [c for c in silent_contacts if c["urgency"] == "URGENT"]
    warning = [c for c in silent_contacts if c["urgency"] == "WARNING"]
    monitor = [c for c in silent_contacts if c["urgency"] == "MONITOR"]

    lines = [
        f"🚨 *Deal Silence Report — {NOW.strftime('%A, %B %-d')}*",
        "",
    ]
    if urgent:
        lines.append("*🔴 URGENT (>14 days silent)*")
        for c in urgent:
            lines.append(f"  • {c['contact']} ({c['deal_size']}) — {c['days_silent']} days")
            if c.get("has_draft_template"):
                lines.append(f"    → [OPS-DRAFT] follow-up created in Gmail drafts")
    if warning:
        lines.append("\n*🟡 WARNING (7-14 days silent)*")
        for c in warning:
            lines.append(f"  • {c['contact']} ({c['deal_size']}) — {c['days_silent']} days")
    if monitor:
        lines.append("\n*⚪ MONITOR*")
        for c in monitor:
            lines.append(f"  • {c['contact']} — {c['context'][:60]}")
    if not (urgent or warning):
        lines.append("✅ All active deals have recent contact. No follow-ups needed.")

    return "\n".join(lines)


def main():
    print(f"[scanner] Deal Silence Scanner — {NOW.strftime('%Y-%m-%d %H:%M')}")
    service = get_gmail_service()

    if service:
        print("[scanner] Gmail connected — running live scan")
        silent = scan_gmail_for_silence(service)
        # Create drafts for contacts with templates
        for contact in silent:
            if contact.get("has_draft_template") and contact["contact"] in DRAFT_TEMPLATES:
                tmpl = DRAFT_TEMPLATES[contact["contact"]]
                emails = DEAL_CONTACTS[contact["contact"]]["emails"]
                if emails:
                    draft_id = create_gmail_draft(service, emails[0], tmpl["subject"], tmpl["body"])
                    if draft_id:
                        print(f"[scanner] ✓ Draft created for {contact['contact']}: {tmpl['subject']}")
    else:
        print("[scanner] Gmail not connected — mock mode (no drafts created)")
        silent = scan_thread_silence_mock()

    report = generate_report(silent)
    print("\n" + report)
    post_to_slack(report)

    # Save report
    out = ROOT / "output" / "session-logs" / f"deal-scan-{NOW.strftime('%Y%m%d-%H%M')}.md"
    out.parent.mkdir(exist_ok=True)
    out.write_text(f"# Deal Scan — {NOW.strftime('%Y-%m-%d %H:%M')}\n\n" + report.replace("*", "**"))
    print(f"\n[scanner] ✓ Report saved → {out}")


if __name__ == "__main__":
    main()

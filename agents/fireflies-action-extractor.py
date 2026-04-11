#!/usr/bin/env python3
"""
fireflies-action-extractor.py
Pulls recent Fireflies transcripts, extracts action items by person,
and writes a structured JSON + summary MD to output/actions/.
Run daily. Pairs with gmail-deal-scanner.py for full deal loop coverage.

Usage:
  python agents/fireflies-action-extractor.py
  python agents/fireflies-action-extractor.py --days 7
  python agents/fireflies-action-extractor.py --meeting-id <id>
"""

import os
import sys
import json
import re
import urllib.request
import urllib.error
from datetime import datetime, timedelta, timezone
from pathlib import Path
from dotenv import load_dotenv

# ── Config ────────────────────────────────────────────────────────────────────
ROOT = Path(__file__).parent.parent
load_dotenv(ROOT / ".env")

FIREFLIES_API_KEY = os.getenv("FIREFLIES_API_KEY", "")
SLACK_WEBHOOK_URL = os.getenv("SLACK_OPS_WEBHOOK_URL", "")  # optional
OUTPUT_DIR = ROOT / "output" / "actions"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# People to track — map display name variants to canonical name
KNOWN_PEOPLE = {
    "bill": "Bill",
    "bill bricker": "Bill",
    "billbricker": "Bill",
    "david": "David",
    "david jeflea": "David",
    "cedric": "Cedric",
    "cedric holz": "Cedric",
    "greg": "Greg",
    "chris": "Chris",
    "chris kepko": "Chris Kepko",
    "chris williams": "Chris Williams",
    "rich": "Rich (Court Kings)",
    "bryan": "Bryan (Court Kings)",
    "barrett": "Barrett (Rally)",
    "george": "George Kaminis",
    "scot": "Scot McClintic",
}

# Keywords that signal an action item
ACTION_TRIGGERS = [
    r"\bi will\b", r"\bi'll\b", r"\bwe will\b", r"\bwe'll\b",
    r"\bgoing to\b", r"\bneed to\b", r"\bshould\b", r"\bmust\b",
    r"\baction item\b", r"\bfollow up\b", r"\bsend\b", r"\bschedule\b",
    r"\bblock\b", r"\bshare\b", r"\bprepare\b", r"\bbuild\b",
    r"\bconnect\b", r"\bintroduce\b", r"\bloop in\b", r"\bping\b",
]
ACTION_PATTERN = re.compile("|".join(ACTION_TRIGGERS), re.IGNORECASE)

# Deal contacts — used to tag meeting context
DEAL_CONTEXT = {
    "peak": "Peak Pickleball",
    "kepko": "Peak Pickleball",
    "court kings": "Court Kings",
    "rich": "Court Kings",
    "concord": "Concord Pickleball",
    "williams": "Concord Pickleball",
    "rally": "Rally Pickleball",
    "barrett": "Rally Pickleball",
    "carolina": "Carolina Pickleball",
    "fundraise": "Fundraise",
    "investor": "Fundraise",
    "ciocca": "Fundraise",
    "rosenbloom": "Fundraise",
    "mclintic": "Fundraise",
    "scot": "Fundraise",
}


# ── Fireflies API ─────────────────────────────────────────────────────────────

def graphql(query: str, variables: dict = None) -> dict:
    """Execute a Fireflies GraphQL query."""
    if not FIREFLIES_API_KEY:
        raise ValueError("FIREFLIES_API_KEY not set in .env")
    payload = {"query": query}
    if variables:
        payload["variables"] = variables
    data = json.dumps(payload).encode()
    req = urllib.request.Request(
        "https://api.fireflies.ai/graphql",
        data=data,
        headers={
            "Authorization": f"Bearer {FIREFLIES_API_KEY}",
            "Content-Type": "application/json",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read())
    except urllib.error.HTTPError as e:
        body = e.read().decode()
        print(f"[fireflies] HTTP {e.code}: {body[:300]}")
        return {}
    except Exception as e:
        print(f"[fireflies] Error: {e}")
        return {}


def fetch_recent_transcripts(days: int = 3) -> list:
    """Get transcripts from the last N days."""
    since_ts = int((datetime.now(timezone.utc) - timedelta(days=days)).timestamp() * 1000)
    q = """
    query($since: Float) {
      transcripts(fromDate: $since, limit: 20) {
        id
        title
        date
        duration
        summary {
          action_items
          overview
          shorthand_bullet
        }
        sentences {
          speaker_name
          text
          start_time
        }
      }
    }
    """
    result = graphql(q, {"since": float(since_ts)})
    transcripts = result.get("data", {}).get("transcripts", [])
    print(f"[fireflies] Found {len(transcripts)} transcripts from last {days} days")
    return transcripts


def fetch_single_transcript(meeting_id: str) -> dict:
    """Get a specific transcript by ID."""
    q = """
    query($id: String!) {
      transcript(id: $id) {
        id
        title
        date
        duration
        summary {
          action_items
          overview
          shorthand_bullet
        }
        sentences {
          speaker_name
          text
          start_time
        }
      }
    }
    """
    result = graphql(q, {"id": meeting_id})
    t = result.get("data", {}).get("transcript")
    return [t] if t else []


# ── Extraction ────────────────────────────────────────────────────────────────

def normalize_speaker(name: str) -> str:
    if not name:
        return "Unknown"
    lower = name.lower().strip()
    return KNOWN_PEOPLE.get(lower, name.strip().title())


def detect_deal_context(text: str) -> str:
    lower = text.lower()
    for keyword, context in DEAL_CONTEXT.items():
        if keyword in lower:
            return context
    return "General"


def extract_from_summary(summary: dict, meeting_title: str) -> list:
    """Extract action items from Fireflies' built-in summary."""
    items = []
    raw_actions = summary.get("action_items", "") if summary else ""
    if not raw_actions:
        return items
    # Fireflies returns this as a string with bullet points
    for line in raw_actions.split("\n"):
        line = line.strip().lstrip("•-*123456789. ")
        if len(line) > 10:
            # Try to extract owner from "Bill: do X" or "@Bill do X" format
            owner = "TBD"
            m = re.match(r"^(@?\w+):\s+(.+)", line)
            if m:
                candidate = m.group(1).lstrip("@").lower()
                owner = KNOWN_PEOPLE.get(candidate, candidate.title())
                line = m.group(2)
            items.append({
                "action": line,
                "owner": owner,
                "source": "fireflies_summary",
                "context": detect_deal_context(f"{meeting_title} {line}"),
            })
    return items


def extract_from_transcript(sentences: list, meeting_title: str) -> list:
    """Extract action items from raw transcript sentences."""
    items = []
    for sent in sentences:
        text = sent.get("text", "").strip()
        speaker = normalize_speaker(sent.get("speaker_name", ""))
        if len(text) < 15:
            continue
        if ACTION_PATTERN.search(text):
            # Filter out low-signal matches
            if len(text.split()) < 4:
                continue
            items.append({
                "action": text,
                "owner": speaker,
                "source": "transcript_sentence",
                "context": detect_deal_context(f"{meeting_title} {text}"),
                "timestamp_s": sent.get("start_time", 0),
            })
    return items


def process_transcripts(transcripts: list) -> dict:
    """Process all transcripts into structured action items."""
    all_actions = []
    meetings_processed = []

    for t in transcripts:
        if not t:
            continue
        title = t.get("title", "Untitled Meeting")
        date_ms = t.get("date", 0)
        date_str = datetime.fromtimestamp(date_ms / 1000).strftime("%Y-%m-%d") if date_ms else "unknown"
        duration = t.get("duration", 0)

        print(f"  Processing: {title} ({date_str})")

        # Prefer Fireflies' own action item extraction
        summary_actions = extract_from_summary(t.get("summary"), title)
        # Supplement with our pattern matching on sentences
        raw_actions = extract_from_transcript(t.get("sentences", []), title)

        # Deduplicate: prefer summary version if similar text exists
        seen_texts = {a["action"].lower()[:50] for a in summary_actions}
        filtered_raw = [a for a in raw_actions if a["action"].lower()[:50] not in seen_texts]

        meeting_actions = summary_actions + filtered_raw[:10]  # cap raw at 10 per meeting

        for a in meeting_actions:
            a["meeting_id"] = t.get("id", "")
            a["meeting_title"] = title
            a["meeting_date"] = date_str
            a["meeting_duration_min"] = round(duration / 60) if duration else 0

        all_actions.extend(meeting_actions)
        meetings_processed.append({
            "id": t.get("id", ""),
            "title": title,
            "date": date_str,
            "actions_found": len(meeting_actions),
            "overview": (t.get("summary") or {}).get("overview", "")[:200],
        })

    # Group by owner
    by_owner = {}
    for a in all_actions:
        owner = a["owner"]
        by_owner.setdefault(owner, []).append(a)

    # Group by deal context
    by_context = {}
    for a in all_actions:
        ctx = a["context"]
        by_context.setdefault(ctx, []).append(a)

    return {
        "generated": datetime.now().isoformat(),
        "meetings_processed": meetings_processed,
        "total_actions": len(all_actions),
        "by_owner": by_owner,
        "by_context": by_context,
        "all_actions": all_actions,
    }


# ── Output ────────────────────────────────────────────────────────────────────

def write_outputs(data: dict, label: str = ""):
    ts = datetime.now().strftime("%Y%m%d-%H%M")
    label = label or ts

    # JSON
    json_path = OUTPUT_DIR / f"actions-{label}.json"
    json_path.write_text(json.dumps(data, indent=2))
    print(f"\n[output] JSON: {json_path}")

    # Markdown summary
    lines = [f"# Action Items — {label}\n", f"_{data['total_actions']} actions from {len(data['meetings_processed'])} meetings_\n"]

    # By owner section
    lines.append("\n## By Owner\n")
    for owner, actions in sorted(data["by_owner"].items()):
        lines.append(f"\n### {owner} ({len(actions)} items)\n")
        for a in actions:
            ctx_tag = f"[{a['context']}]" if a["context"] != "General" else ""
            lines.append(f"- [ ] {a['action']} {ctx_tag}  \n  _from: {a['meeting_title']} ({a['meeting_date']})_\n")

    # By deal context
    lines.append("\n---\n## By Deal Context\n")
    for ctx, actions in sorted(data["by_context"].items()):
        lines.append(f"\n### {ctx} ({len(actions)})\n")
        for a in actions[:5]:  # top 5 per context
            lines.append(f"- [ ] **{a['owner']}:** {a['action']}\n")
        if len(actions) > 5:
            lines.append(f"- _(+ {len(actions) - 5} more — see JSON)_\n")

    # Meetings processed
    lines.append("\n---\n## Meetings Processed\n")
    for m in data["meetings_processed"]:
        lines.append(f"- **{m['title']}** ({m['date']}) — {m['actions_found']} actions\n")
        if m["overview"]:
            lines.append(f"  > {m['overview']}\n")

    md_path = OUTPUT_DIR / f"actions-{label}.md"
    md_path.write_text("".join(lines))
    print(f"[output] Markdown: {md_path}")

    return json_path, md_path


def post_to_slack(data: dict):
    """Post a compact action item summary to Slack #ops."""
    if not SLACK_WEBHOOK_URL:
        return
    top_bill = [a for a in data["all_actions"] if a["owner"] == "Bill"][:3]
    top_david = [a for a in data["all_actions"] if a["owner"] == "David"][:2]

    blocks = [
        {"type": "header", "text": {"type": "plain_text", "text": "🎯 Action Items from Recent Calls"}},
        {"type": "section", "text": {"type": "mrkdwn",
            "text": f"*{data['total_actions']} actions* across {len(data['meetings_processed'])} meetings"}},
    ]
    if top_bill:
        bill_text = "\n".join(f"• {a['action'][:80]}" for a in top_bill)
        blocks.append({"type": "section", "text": {"type": "mrkdwn", "text": f"*Bill:*\n{bill_text}"}})
    if top_david:
        david_text = "\n".join(f"• {a['action'][:80]}" for a in top_david)
        blocks.append({"type": "section", "text": {"type": "mrkdwn", "text": f"*David:*\n{david_text}"}})

    payload = json.dumps({"blocks": blocks}).encode()
    req = urllib.request.Request(SLACK_WEBHOOK_URL, data=payload,
                                  headers={"Content-Type": "application/json"})
    try:
        urllib.request.urlopen(req, timeout=10)
        print("[slack] Posted action items")
    except Exception as e:
        print(f"[slack] Failed: {e}")


# ── Mock mode ─────────────────────────────────────────────────────────────────

def mock_data() -> list:
    """Return mock transcripts when API key is missing."""
    print("[mock] No FIREFLIES_API_KEY — using mock data")
    return [{
        "id": "mock-001",
        "title": "Peak Pickleball - Hardware & Install Planning",
        "date": int(datetime.now(timezone.utc).timestamp() * 1000),
        "duration": 2400,
        "summary": {
            "action_items": "David: Send camera spec sheet to Chris's IT contact\nBill: Confirm 55/45 pilot split in writing\nCedric: Finalize CourtReserve integration scope",
            "overview": "Discussed hardware shipment timing and court layout for Peak opening May 9.",
        },
        "sentences": [
            {"speaker_name": "Bill", "text": "I'll follow up with Cedric on the CourtReserve piece by Thursday.", "start_time": 120},
            {"speaker_name": "David", "text": "We need to send Chris the camera spec sheet before his IT guy starts.", "start_time": 340},
            {"speaker_name": "Bill", "text": "I should also schedule a call with Barrett at Rally this week.", "start_time": 890},
        ],
    }]


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    import argparse
    parser = argparse.ArgumentParser(description="Extract action items from Fireflies transcripts")
    parser.add_argument("--days", type=int, default=3, help="Days to look back (default: 3)")
    parser.add_argument("--meeting-id", type=str, help="Specific meeting ID to process")
    parser.add_argument("--mock", action="store_true", help="Use mock data (no API needed)")
    args = parser.parse_args()

    print("=" * 60)
    print("Fireflies Action Extractor")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print("=" * 60)

    # Fetch transcripts
    if args.mock or not FIREFLIES_API_KEY:
        transcripts = mock_data()
    elif args.meeting_id:
        transcripts = fetch_single_transcript(args.meeting_id)
    else:
        transcripts = fetch_recent_transcripts(days=args.days)

    if not transcripts:
        print("[warn] No transcripts found. Check FIREFLIES_API_KEY or try --days 7")
        return

    # Process
    data = process_transcripts(transcripts)

    # Print summary
    print(f"\nTotal actions extracted: {data['total_actions']}")
    for owner, actions in data["by_owner"].items():
        print(f"  {owner}: {len(actions)} items")

    # Write outputs
    label = f"{datetime.now().strftime('%Y%m%d')}-{args.days}d"
    if args.meeting_id:
        label = args.meeting_id[:8]
    write_outputs(data, label)

    # Slack
    post_to_slack(data)

    print("\n✓ Done. Check output/actions/ for results.")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
ideas-intake.py — chief@courtana.com AI Employee
==================================================
Bill's idea capture system. He speaks an idea into Wispr Flow on his phone,
sends it to Slack (or texts it), and this agent saves it.

INTAKE PATHS (in order of simplicity):
  1. Slack channel  — Bill messages #courtana-ideas (easiest on phone)
  2. Apple Notes    — Bill adds a note titled "Idea:" (works offline)
  3. Direct file    — Bill drop text into agents/idea-inbox.txt (Dropbox)

OUTPUT:
  → BILL-OS/brainstorm-inbox.md  (append-only, newest first)
  → output/ideas/ideas-YYYYMMDD.json (daily batch)
  → Slack confirmation back to Bill

Usage:
  python agents/ideas-intake.py              # Process all intake sources
  python agents/ideas-intake.py --slack      # Slack channel only
  python agents/ideas-intake.py --notes      # Apple Notes only
  python agents/ideas-intake.py --add "My idea text here"  # Direct add (testing)
  python agents/ideas-intake.py --show       # Show all saved ideas

Called by: agent-loop.py (every 2 hours during day, or on demand)
"""

import os
import sys
import json
import subprocess
import urllib.request
import urllib.error
from datetime import datetime, date, timezone
from pathlib import Path

try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).parent.parent / ".env")
except ImportError:
    pass

# ── Config ────────────────────────────────────────────────────────────────────
ROOT            = Path(__file__).parent.parent
BILL_OS_DIR     = ROOT.parent / "BILL-OS"
INBOX_MD        = BILL_OS_DIR / "brainstorm-inbox.md"
IDEAS_DIR       = ROOT / "output" / "ideas"
IDEAS_DIR.mkdir(parents=True, exist_ok=True)

IDEA_INBOX_TXT  = Path(__file__).parent / "idea-inbox.txt"
PROCESSED_IDS   = IDEAS_DIR / ".processed-ids.json"  # Tracks what we've already ingested

SLACK_BOT_TOKEN     = os.getenv("SLACK_BOT_TOKEN", "")
SLACK_WEBHOOK_URL   = os.getenv("SLACK_WEBHOOK_URL", "")
SLACK_IDEAS_CHANNEL = os.getenv("SLACK_IDEAS_CHANNEL", "")  # e.g. C08XXXXXXX for #courtana-ideas
BILL_SLACK_ID       = os.getenv("BILL_SLACK_USER_ID", "")


# ── Processed ID tracking ─────────────────────────────────────────────────────

def load_processed_ids() -> set:
    if not PROCESSED_IDS.exists():
        return set()
    return set(json.loads(PROCESSED_IDS.read_text()))


def save_processed_id(id_str: str):
    ids = load_processed_ids()
    ids.add(id_str)
    PROCESSED_IDS.write_text(json.dumps(sorted(ids)))


# ── Intake Sources ────────────────────────────────────────────────────────────

def intake_from_slack() -> list:
    """Read new messages from #courtana-ideas channel via Slack bot token."""
    if not SLACK_BOT_TOKEN or not SLACK_IDEAS_CHANNEL:
        if not SLACK_BOT_TOKEN:
            print("[slack-intake] SLACK_BOT_TOKEN not set")
        if not SLACK_IDEAS_CHANNEL:
            print("[slack-intake] SLACK_IDEAS_CHANNEL not set")
        return []

    processed = load_processed_ids()
    new_ideas = []

    url = f"https://slack.com/api/conversations.history?channel={SLACK_IDEAS_CHANNEL}&limit=20"
    req = urllib.request.Request(url, headers={"Authorization": f"Bearer {SLACK_BOT_TOKEN}"})
    try:
        with urllib.request.urlopen(req, timeout=10) as r:
            data = json.loads(r.read())
    except Exception as e:
        print(f"[slack-intake] Error reading channel: {e}")
        return []

    if not data.get("ok"):
        print(f"[slack-intake] Slack error: {data.get('error', 'unknown')}")
        return []

    messages = data.get("messages", [])
    for msg in messages:
        msg_id = f"slack-{msg.get('ts', '')}"
        if msg_id in processed:
            continue
        text = msg.get("text", "").strip()
        if not text or len(text) < 5:
            continue
        # Skip bot messages
        if msg.get("bot_id") or msg.get("subtype"):
            continue
        ts = float(msg.get("ts", 0))
        new_ideas.append({
            "id":       msg_id,
            "text":     text,
            "source":   "slack",
            "captured": datetime.fromtimestamp(ts).isoformat() if ts else datetime.now().isoformat(),
        })
        save_processed_id(msg_id)

    print(f"[slack-intake] {len(new_ideas)} new ideas from Slack")
    return new_ideas


def intake_from_apple_notes() -> list:
    """Read Apple Notes titled 'Idea:' or in the 'Ideas' folder."""
    new_ideas = []
    try:
        # Use osascript to read Apple Notes
        script = '''
        tell application "Notes"
            set ideaNotes to {}
            repeat with n in every note of account "iCloud"
                if name of n starts with "Idea:" or folder of n is folder "Ideas" then
                    set end of ideaNotes to {id: id of n, name: name of n, body: plaintext of n, creationDate: creation date of n as string}
                end if
            end repeat
            return ideaNotes
        end tell
        '''
        result = subprocess.run(
            ["osascript", "-e", script],
            capture_output=True, text=True, timeout=15
        )
        if result.returncode != 0:
            return []
        # Parse the AppleScript result (it's not JSON — parse manually)
        # Each note looks like: {id:x, name:y, body:z, creationDate:d}
        output = result.stdout.strip()
        if not output:
            return []
        processed = load_processed_ids()
        # Simple extraction — look for body content
        notes_raw = output.split(", {id:")
        for raw in notes_raw:
            if "body:" not in raw:
                continue
            note_id_match = raw.split(",")[0].strip().lstrip("{id:")
            note_id = f"notes-{note_id_match.strip()}"
            if note_id in processed:
                continue
            body_start = raw.find("body:") + 5
            body_end   = raw.find(", creationDate:")
            if body_start > 5 and body_end > body_start:
                body = raw[body_start:body_end].strip().strip('"')
                # Strip "Idea:" prefix if present
                clean = re.sub(r'^[Ii]dea:\s*', '', body).strip()
                if len(clean) < 10:
                    continue
                new_ideas.append({
                    "id":       note_id,
                    "text":     clean[:500],
                    "source":   "apple_notes",
                    "captured": datetime.now().isoformat(),
                })
                save_processed_id(note_id)
    except Exception as e:
        print(f"[notes-intake] {e}")
    print(f"[notes-intake] {len(new_ideas)} new ideas from Apple Notes")
    return new_ideas


def intake_from_inbox_file() -> list:
    """Read from agents/idea-inbox.txt — Bill can drop text here via Dropbox."""
    if not IDEA_INBOX_TXT.exists():
        return []
    content = IDEA_INBOX_TXT.read_text().strip()
    if not content:
        return []

    ideas = []
    processed = load_processed_ids()
    for line in content.split("\n"):
        line = line.strip()
        if not line or len(line) < 5:
            continue
        idea_id = f"file-{hash(line) % 999999}"
        if idea_id in processed:
            continue
        ideas.append({
            "id":       idea_id,
            "text":     line,
            "source":   "inbox_file",
            "captured": datetime.now().isoformat(),
        })
        save_processed_id(idea_id)

    if ideas:
        # Clear the file after reading
        IDEA_INBOX_TXT.write_text("")
        print(f"[file-intake] {len(ideas)} ideas from idea-inbox.txt (file cleared)")
    return ideas


# ── Save + Announce ────────────────────────────────────────────────────────────

def save_to_inbox(ideas: list) -> int:
    """Append ideas to brainstorm-inbox.md (newest first)."""
    if not ideas:
        return 0

    # Ensure file exists with header
    if not INBOX_MD.exists():
        INBOX_MD.write_text(
            "# Brainstorm Inbox\n"
            "_Ideas captured from Slack, Apple Notes, and voice (Wispr Flow)._\n"
            "_Reviewed in morning brief. Mark `[done]` when actioned._\n\n"
        )

    existing = INBOX_MD.read_text()
    new_lines = []
    for idea in ideas:
        dt = idea.get("captured", "")[:10]
        source = idea.get("source", "unknown")
        text = idea["text"].strip()
        new_lines.append(f"## {dt} — _{source}_\n{text}\n\n---\n")

    # Prepend after the header (find first --- or after 4th line)
    header_end = existing.find("---\n")
    if header_end > 0:
        # There are existing entries — insert after the header block
        insert_pos = header_end + 4
        updated = existing[:insert_pos] + "\n" + "".join(new_lines) + existing[insert_pos:]
    else:
        # First ideas — append after header
        updated = existing + "\n".join(new_lines)

    INBOX_MD.write_text(updated)
    print(f"[inbox] Saved {len(ideas)} ideas to brainstorm-inbox.md")
    return len(ideas)


def save_daily_json(ideas: list):
    """Save a daily batch of ideas to output/ideas/."""
    today = date.today().strftime("%Y%m%d")
    day_file = IDEAS_DIR / f"ideas-{today}.json"

    existing = []
    if day_file.exists():
        try:
            existing = json.loads(day_file.read_text())
        except Exception:
            pass

    existing.extend(ideas)
    day_file.write_text(json.dumps(existing, indent=2))


def post_confirmation_to_slack(ideas: list):
    """Post a brief confirmation that ideas were captured."""
    if not ideas or not SLACK_WEBHOOK_URL:
        return
    if len(ideas) == 1:
        text = f"💡 *Idea captured:* _{ideas[0]['text'][:120]}_"
    else:
        text = f"💡 *{len(ideas)} ideas captured* from {set(i['source'] for i in ideas)}"
    text += f"\n_Saved to brainstorm-inbox.md_"

    payload = json.dumps({"text": text}).encode()
    req = urllib.request.Request(SLACK_WEBHOOK_URL, data=payload,
                                  headers={"Content-Type": "application/json"})
    try:
        urllib.request.urlopen(req, timeout=10)
    except Exception:
        pass


def show_all_ideas():
    """Print all ideas from brainstorm-inbox.md."""
    if not INBOX_MD.exists():
        print("No ideas yet. brainstorm-inbox.md doesn't exist.")
        return
    content = INBOX_MD.read_text()
    print(content[:3000])
    lines = [l for l in content.split("\n") if l.startswith("## ")]
    print(f"\n({len(lines)} ideas total)")


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    import argparse, re
    parser = argparse.ArgumentParser(description="Ideas intake system")
    parser.add_argument("--slack",  action="store_true", help="Only check Slack channel")
    parser.add_argument("--notes",  action="store_true", help="Only check Apple Notes")
    parser.add_argument("--add",    type=str,            help="Directly add an idea (testing/manual)")
    parser.add_argument("--show",   action="store_true", help="Show all saved ideas")
    args = parser.parse_args()

    if args.show:
        show_all_ideas()
        return

    print("=" * 55)
    print("  ideas-intake.py — chief@courtana.com")
    print(f"  {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print("=" * 55)

    all_ideas = []

    # Direct add (manual or for testing)
    if args.add:
        idea = {
            "id":       f"manual-{int(datetime.now().timestamp())}",
            "text":     args.add,
            "source":   "manual",
            "captured": datetime.now().isoformat(),
        }
        all_ideas.append(idea)
        save_processed_id(idea["id"])
        print(f"[manual] Added: {args.add[:80]}")

    # Slack
    if not args.notes:
        slack_ideas = intake_from_slack()
        all_ideas.extend(slack_ideas)

    # Apple Notes
    if not args.slack:
        notes_ideas = intake_from_apple_notes()
        all_ideas.extend(notes_ideas)

    # Inbox file (always check — Bill might drop something via Dropbox)
    if not args.slack and not args.notes:
        file_ideas = intake_from_inbox_file()
        all_ideas.extend(file_ideas)

    if not all_ideas:
        print("No new ideas found.")
        return

    print(f"\nTotal new ideas: {len(all_ideas)}")
    for idea in all_ideas:
        print(f"  [{idea['source']}] {idea['text'][:80]}")

    # Save
    save_to_inbox(all_ideas)
    save_daily_json(all_ideas)
    post_confirmation_to_slack(all_ideas)

    print(f"\n✓ Saved to {INBOX_MD}")


if __name__ == "__main__":
    main()

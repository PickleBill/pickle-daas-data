#!/usr/bin/env python3
"""
credential-validator.py — chief@courtana.com AI Employee
==========================================================
Tests all tokens before any agent runs. Run this first after adding new credentials.

Usage:
  python agents/credential-validator.py
  python agents/credential-validator.py --setup       (walks through Gmail OAuth)
  python agents/credential-validator.py --required    (exit 1 if required keys fail)
  python agents/credential-validator.py --json        (output machine-readable JSON)

Exit codes:
  0 — All required credentials pass
  1 — One or more required credentials failed

Required: GEMINI_API_KEY, Courtana API (anon)
Optional: COURTANA_TOKEN, SLACK_BOT_TOKEN, FIREFLIES_API_KEY, NOTION_TOKEN, etc.
"""

import os
import sys
import json
import argparse
import urllib.request
import urllib.error
from pathlib import Path
from datetime import datetime

try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).parent.parent / ".env")
except ImportError:
    pass

ROOT      = Path(__file__).parent.parent
CREDS_DIR = Path(__file__).parent / "credentials"
CREDS_DIR.mkdir(exist_ok=True)

STATUS_PATH = Path(__file__).parent / "last-credential-check.json"

# ANSI color codes (auto-disabled when not a tty)
USE_COLOR = sys.stdout.isatty()
GREEN  = "\033[92m" if USE_COLOR else ""
RED    = "\033[91m" if USE_COLOR else ""
YELLOW = "\033[93m" if USE_COLOR else ""
RESET  = "\033[0m"  if USE_COLOR else ""

# Required credentials — agent-loop.py will abort if any of these fail
REQUIRED_KEYS = {"Courtana API (anon)", "Gemini API"}


def check(name, fn):
    """Run a credential test. Returns ('pass'|'fail'|'missing', detail_str)."""
    try:
        result = fn()
        icon = f"{GREEN}PASS{RESET}"
        print(f"  {icon}  {name}: {result}")
        return "pass", str(result)
    except ValueError as e:
        # ValueError = credential missing/not set
        icon = f"{YELLOW}MISS{RESET}"
        msg = str(e)
        print(f"  {icon}  {name}: {msg}")
        return "missing", msg
    except Exception as e:
        icon = f"{RED}FAIL{RESET}"
        msg = str(e)[:120]
        print(f"  {icon}  {name}: {msg}")
        return "fail", msg


def test_courtana_api():
    url = "https://courtana.com/app/anon-highlight-groups/?page_size=1"
    req = urllib.request.Request(url, headers={"Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=10) as r:
        data = json.loads(r.read())
        count = data.get("count", "?")
        return f"{count} total highlight groups"


def test_courtana_auth():
    token = os.getenv("COURTANA_TOKEN")
    if not token:
        raise ValueError("COURTANA_TOKEN not set")
    url = "https://courtana.com/accounts/profiles/current/"
    req = urllib.request.Request(url, headers={
        "Accept": "application/json",
        "Authorization": f"Bearer {token}"
    })
    with urllib.request.urlopen(req, timeout=10) as r:
        data = json.loads(r.read())
        return f"authenticated as user_id={data.get('id','?')}"


def test_gemini():
    key = os.getenv("GEMINI_API_KEY")
    if not key:
        raise ValueError("GEMINI_API_KEY not set")
    payload = json.dumps({"contents": [{"parts": [{"text": "Say OK"}]}]}).encode()
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={key}"
    req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=15) as r:
        data = json.loads(r.read())
        return data["candidates"][0]["content"]["parts"][0]["text"].strip()[:30]


def test_elevenlabs():
    key = os.getenv("ELEVENLABS_API_KEY")
    if not key:
        raise ValueError("ELEVENLABS_API_KEY not set")
    req = urllib.request.Request(
        "https://api.elevenlabs.io/v1/user",
        headers={"xi-api-key": key}
    )
    with urllib.request.urlopen(req, timeout=10) as r:
        data = json.loads(r.read())
        return f"subscription={data.get('subscription',{}).get('tier','?')}"


def test_gmail():
    """Test Gmail OAuth token."""
    token_path = CREDS_DIR / "token.json"
    if not token_path.exists():
        raise ValueError("No token.json — run with --setup first")
    token_data = json.loads(token_path.read_text())
    if "access_token" not in token_data:
        raise ValueError("token.json missing access_token")
    # Quick test: list labels
    req = urllib.request.Request(
        "https://gmail.googleapis.com/gmail/v1/users/me/labels",
        headers={"Authorization": f"Bearer {token_data['access_token']}"}
    )
    with urllib.request.urlopen(req, timeout=10) as r:
        data = json.loads(r.read())
        return f"{len(data.get('labels', []))} labels accessible"


def test_slack():
    token = os.getenv("SLACK_BOT_TOKEN")
    if not token:
        raise ValueError("SLACK_BOT_TOKEN not set")
    req = urllib.request.Request(
        "https://slack.com/api/auth.test",
        headers={"Authorization": f"Bearer {token}"}
    )
    with urllib.request.urlopen(req, timeout=10) as r:
        data = json.loads(r.read())
        if not data.get("ok"):
            raise ValueError(data.get("error", "unknown error"))
        return f"bot={data.get('bot_id','?')} team={data.get('team','?')}"


def test_fireflies():
    key = os.getenv("FIREFLIES_API_KEY")
    if not key:
        raise ValueError("FIREFLIES_API_KEY not set")
    payload = json.dumps({"query": "{ user { name email } }"}).encode()
    req = urllib.request.Request(
        "https://api.fireflies.ai/graphql",
        data=payload,
        headers={"Content-Type": "application/json", "Authorization": f"Bearer {key}"}
    )
    with urllib.request.urlopen(req, timeout=10) as r:
        data = json.loads(r.read())
        user = data.get("data", {}).get("user", {})
        return f"{user.get('name','?')} <{user.get('email','?')}>"


def test_notion():
    token = os.getenv("NOTION_TOKEN")
    if not token:
        raise ValueError("NOTION_TOKEN not set")
    req = urllib.request.Request(
        "https://api.notion.com/v1/users/me",
        headers={"Authorization": f"Bearer {token}", "Notion-Version": "2022-06-28"}
    )
    with urllib.request.urlopen(req, timeout=10) as r:
        data = json.loads(r.read())
        return f"{data.get('name','?')} ({data.get('type','?')})"


def test_supabase():
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_ANON_KEY")
    if not url or not key:
        raise ValueError("SUPABASE_URL or SUPABASE_ANON_KEY not set")
    req = urllib.request.Request(
        f"{url}/rest/v1/",
        headers={"apikey": key, "Authorization": f"Bearer {key}"}
    )
    with urllib.request.urlopen(req, timeout=10) as r:
        return f"connected to {url.split('//')[1].split('.')[0]}"


def setup_gmail_oauth():
    """Walk through Gmail OAuth flow to generate token.json."""
    creds_json = CREDS_DIR / "credentials.json"
    if not creds_json.exists():
        print("\n[setup] credentials.json not found in agents/credentials/")
        print("  1. Go to console.cloud.google.com")
        print("  2. Create project: 'Courtana Chief of Staff'")
        print("  3. Enable: Gmail API, Calendar API, Drive API")
        print("  4. Create OAuth 2.0 credentials (Desktop app)")
        print("  5. Download credentials.json → place in PICKLE-DAAS/agents/credentials/")
        print("  6. Re-run: python agents/credential-validator.py --setup")
        return

    try:
        from google_auth_oauthlib.flow import InstalledAppFlow
        from google.auth.transport.requests import Request
        from google.oauth2.credentials import Credentials

        SCOPES = [
            "https://www.googleapis.com/auth/gmail.readonly",
            "https://www.googleapis.com/auth/gmail.compose",
            "https://www.googleapis.com/auth/calendar.readonly",
            "https://www.googleapis.com/auth/drive.readonly",
        ]

        creds = None
        token_path = CREDS_DIR / "token.json"
        if token_path.exists():
            creds = Credentials.from_authorized_user_file(str(token_path), SCOPES)
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(str(creds_json), SCOPES)
                creds = flow.run_local_server(port=0)
            token_path.write_text(creds.to_json())
        print(f"[setup] ✓ OAuth complete. Token saved to {token_path}")

    except ImportError:
        print("[setup] Install: pip install google-auth-oauthlib google-auth-httplib2 google-api-python-client")


def main():
    parser = argparse.ArgumentParser(description="Validate all chief@courtana.com credentials")
    parser.add_argument("--setup",    action="store_true", help="Walk through Gmail OAuth setup")
    parser.add_argument("--required", action="store_true", help="Exit 1 if any REQUIRED key fails")
    parser.add_argument("--json",     action="store_true", help="Output machine-readable JSON")
    args = parser.parse_args()

    if args.setup:
        setup_gmail_oauth()
        return

    print("=" * 60)
    print("  chief@courtana.com — Credential Validator")
    print(f"  {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

    results = {}

    print("\n[Always Required — must pass before agents run]")
    results["Courtana API (anon)"] = check("Courtana API (anon)", test_courtana_api)
    results["Gemini API"]          = check("Gemini API",          test_gemini)

    print("\n[Auth Required — check these next]")
    results["Courtana API (auth)"] = check("Courtana API (auth)", test_courtana_auth)
    results["ElevenLabs"]          = check("ElevenLabs",          test_elevenlabs)

    print("\n[chief@ Account — set up when account exists]")
    results["Gmail OAuth"] = check("Gmail OAuth",  test_gmail)
    results["Slack Bot"]   = check("Slack Bot",    test_slack)
    results["Fireflies"]   = check("Fireflies",    test_fireflies)
    results["Notion"]      = check("Notion",        test_notion)
    results["Supabase"]    = check("Supabase",      test_supabase)

    # Tally results
    passing = sum(1 for s, _ in results.values() if s == "pass")
    missing = sum(1 for s, _ in results.values() if s == "missing")
    failing = sum(1 for s, _ in results.values() if s == "fail")
    total   = len(results)

    required_ok = all(
        results.get(k, ("fail",))[0] == "pass"
        for k in REQUIRED_KEYS
    )

    print(f"\n{'='*60}")
    print(f"  {passing}/{total} pass  |  {missing} missing  |  {failing} fail")
    if required_ok:
        print(f"  {GREEN}Required credentials OK — agents can run.{RESET}")
    else:
        failed_req = [k for k in REQUIRED_KEYS if results.get(k, ("fail",))[0] != "pass"]
        print(f"  {RED}REQUIRED FAIL: {', '.join(failed_req)}{RESET}")
        print(f"  Agents cannot run until these are resolved.")
    print("=" * 60)

    # Save status JSON
    status_record = {
        "checked_at": datetime.now().isoformat(),
        "required_ok": required_ok,
        "passing": passing,
        "missing": missing,
        "failing": failing,
        "total": total,
        "details": {k: {"status": s, "detail": d} for k, (s, d) in results.items()}
    }
    with open(STATUS_PATH, "w") as f:
        json.dump(status_record, f, indent=2)

    if args.json:
        print(json.dumps(status_record, indent=2))

    # Exit code
    if args.required and not required_ok:
        sys.exit(1)
    elif not args.required and failing > 0 and required_ok is False:
        sys.exit(1)
    else:
        sys.exit(0)


if __name__ == "__main__":
    main()

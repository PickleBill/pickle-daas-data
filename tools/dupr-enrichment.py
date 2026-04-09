#!/usr/bin/env python3
"""
dupr-enrichment.py — Courtana Pickle DaaS
==========================================
Maps Courtana player usernames → DUPR player profiles,
then updates the pickle_daas_player_dna table in Supabase.

Usage:
  # Dry run — shows matches without writing to Supabase
  python tools/dupr-enrichment.py --dry-run

  # Enrich all players who are missing a dupr_id
  python tools/dupr-enrichment.py

  # Enrich a single player by Courtana username
  python tools/dupr-enrichment.py --player PickleBill

  # Force-refresh a player even if dupr_id already exists
  python tools/dupr-enrichment.py --player PickleBill --force

Environment variables required:
  SUPABASE_URL        — e.g. https://xxxx.supabase.co
  SUPABASE_KEY        — service role key (not anon key)
  DUPR_API_KEY        — from DUPR partnership agreement [REQUIRED for full fetch]
                        Optional in --dry-run mode (falls back to public scrape)

Install dependencies:
  pip install requests supabase python-dotenv
"""

import os
import sys
import time
import argparse
import json
import re
import logging
from typing import Optional

import requests
from dotenv import load_dotenv
from supabase import create_client, Client

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

load_dotenv()

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")
DUPR_API_KEY = os.environ.get("DUPR_API_KEY")

# DUPR API base — replace with actual base URL from your partnership agreement
# As of mid-2025, the known base was https://api.mydupr.com/v1
# [VERIFY] this endpoint when your partnership agreement is active
DUPR_API_BASE = os.environ.get("DUPR_API_BASE", "https://api.mydupr.com/v1")

# Public DUPR player search page (fallback for dry-run / name matching only)
# This is the web search endpoint — not for production data pulls
DUPR_PUBLIC_SEARCH = "https://mydupr.com/api/player-search"  # [VERIFY]

REQUEST_TIMEOUT = 10       # seconds
RATE_LIMIT_DELAY = 1.0     # seconds between DUPR API calls — be polite
MAX_RETRIES = 3

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Supabase helpers
# ---------------------------------------------------------------------------

def get_supabase_client() -> Client:
    """Initialize and return the Supabase client."""
    if not SUPABASE_URL or not SUPABASE_KEY:
        log.error("Missing SUPABASE_URL or SUPABASE_KEY environment variables.")
        sys.exit(1)
    return create_client(SUPABASE_URL, SUPABASE_KEY)


def fetch_players_needing_enrichment(sb: Client, player_username: Optional[str] = None, force: bool = False) -> list:
    """
    Fetch players from pickle_daas_player_dna who need DUPR enrichment.

    - If player_username is set, fetch just that player.
    - If force=False, skip players who already have a dupr_id.
    - Returns list of player dicts.
    """
    query = sb.table("pickle_daas_player_dna").select(
        "id, player_username, dupr_id, dupr_rating_singles, dupr_rating_doubles"
    )

    if player_username:
        query = query.eq("player_username", player_username)
    elif not force:
        # Only players without a dupr_id
        query = query.is_("dupr_id", "null")

    result = query.execute()

    if result.data is None:
        log.warning("No players found matching query.")
        return []

    log.info(f"Found {len(result.data)} player(s) to process.")
    return result.data


def update_player_dupr(sb: Client, player_id: str, dupr_data: dict, dry_run: bool = False) -> bool:
    """
    Write DUPR enrichment data back to pickle_daas_player_dna.

    dupr_data should contain some or all of:
      dupr_id, dupr_rating_singles, dupr_rating_doubles,
      dupr_verified_at, dupr_match_confidence
    """
    if dry_run:
        log.info(f"  [DRY RUN] Would update player {player_id} with: {json.dumps(dupr_data, indent=2)}")
        return True

    try:
        result = sb.table("pickle_daas_player_dna").update(dupr_data).eq("id", player_id).execute()
        if result.data:
            log.info(f"  Updated player {player_id} in Supabase.")
            return True
        else:
            log.warning(f"  Update returned no data for player {player_id}.")
            return False
    except Exception as e:
        log.error(f"  Supabase update failed for {player_id}: {e}")
        return False


# ---------------------------------------------------------------------------
# DUPR API helpers
# ---------------------------------------------------------------------------

def _dupr_headers() -> dict:
    """Return auth headers for DUPR API calls."""
    if not DUPR_API_KEY:
        raise EnvironmentError(
            "DUPR_API_KEY is not set. "
            "This is required for live API calls. "
            "For dry-run / name matching, use --dry-run flag."
        )
    return {
        "Authorization": f"Bearer {DUPR_API_KEY}",
        "Content-Type": "application/json",
        "Accept": "application/json",
    }


def search_dupr_player(name: str, dry_run: bool = False) -> Optional[dict]:
    """
    Search DUPR for a player by full name.

    Returns the best-match player dict, or None if no confident match found.

    Response shape expected from DUPR API:
    {
      "players": [
        {
          "id": "dupr-123456",
          "fullName": "Bill Bricker",
          "singlesRating": 4.85,
          "doublesRating": 4.92,
          "ratingVerified": true,
          "location": "Phoenix, AZ",
          ...
        }
      ]
    }
    [VERIFY] actual response shape from your partnership docs.
    """
    endpoint = f"{DUPR_API_BASE}/player/search"
    params = {"query": name, "limit": 5}

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            if dry_run and not DUPR_API_KEY:
                # In dry-run mode without API key, return a stub match for demonstration
                log.info(f"  [DRY RUN] Would search DUPR for: '{name}'")
                return {
                    "id": "DRY_RUN_ID",
                    "fullName": name,
                    "singlesRating": None,
                    "doublesRating": None,
                    "ratingVerified": False,
                    "_dry_run": True,
                }

            headers = _dupr_headers()
            resp = requests.get(endpoint, headers=headers, params=params, timeout=REQUEST_TIMEOUT)
            resp.raise_for_status()
            data = resp.json()

            players = data.get("players", [])
            if not players:
                log.info(f"  No DUPR players found for '{name}'.")
                return None

            # Return the first (best-ranked) match
            # TODO: improve match confidence by comparing location, known associates, etc.
            best = players[0]
            log.info(f"  DUPR match: '{best.get('fullName')}' (id={best.get('id')}, singles={best.get('singlesRating')})")
            return best

        except requests.HTTPError as e:
            if resp.status_code == 429:
                wait = 2 ** attempt
                log.warning(f"  Rate limited by DUPR. Waiting {wait}s... (attempt {attempt}/{MAX_RETRIES})")
                time.sleep(wait)
            else:
                log.error(f"  DUPR HTTP error on attempt {attempt}: {e}")
                if attempt == MAX_RETRIES:
                    return None
        except requests.RequestException as e:
            log.error(f"  Request error on attempt {attempt}: {e}")
            if attempt == MAX_RETRIES:
                return None
        time.sleep(RATE_LIMIT_DELAY)

    return None


def fetch_dupr_player_detail(dupr_id: str) -> Optional[dict]:
    """
    Fetch full player detail from DUPR by their internal ID.

    Returns enriched player dict with rating history, match count, etc.
    [VERIFY] actual endpoint path and response shape from your partnership docs.
    """
    endpoint = f"{DUPR_API_BASE}/player/{dupr_id}"

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            headers = _dupr_headers()
            resp = requests.get(endpoint, headers=headers, timeout=REQUEST_TIMEOUT)
            resp.raise_for_status()
            return resp.json()

        except requests.HTTPError as e:
            if resp.status_code == 404:
                log.warning(f"  DUPR player {dupr_id} not found (404).")
                return None
            elif resp.status_code == 429:
                wait = 2 ** attempt
                log.warning(f"  Rate limited. Waiting {wait}s...")
                time.sleep(wait)
            else:
                log.error(f"  HTTP error fetching player {dupr_id}: {e}")
                if attempt == MAX_RETRIES:
                    return None
        except requests.RequestException as e:
            log.error(f"  Request error: {e}")
            if attempt == MAX_RETRIES:
                return None

        time.sleep(RATE_LIMIT_DELAY)

    return None


# ---------------------------------------------------------------------------
# Name resolution: Courtana username → real name for DUPR search
# ---------------------------------------------------------------------------

def resolve_display_name(player_username: str) -> str:
    """
    Map a Courtana username to a likely real name for DUPR search.

    Strategy (in order):
    1. Hard-coded known mappings (for top players where identity is confirmed)
    2. Strip common prefixes/suffixes (Coach_, PB_, etc.)
    3. Fall back to username as-is

    Extend KNOWN_MAPPINGS as you confirm player identities.
    """
    KNOWN_MAPPINGS = {
        "PickleBill": "Bill Bricker",
        # Add more as players confirm their DUPR identity
        # "CoachnBlock": "Nathan Block",
        # "Chintan": "Chintan Mehta",
    }

    if player_username in KNOWN_MAPPINGS:
        resolved = KNOWN_MAPPINGS[player_username]
        log.info(f"  Name resolved via known mapping: {player_username} → {resolved}")
        return resolved

    # Attempt naive cleanup: remove common prefixes, split on camel case or underscores
    name = player_username
    name = re.sub(r"^(Coach_|PB_|Pickle_|Pro_)", "", name, flags=re.IGNORECASE)
    name = re.sub(r"_", " ", name)
    # Split CamelCase: "PickleBill" → "Pickle Bill"
    name = re.sub(r"([a-z])([A-Z])", r"\1 \2", name)

    log.info(f"  Name resolved via heuristic: {player_username} → {name}")
    return name


# ---------------------------------------------------------------------------
# Core enrichment loop
# ---------------------------------------------------------------------------

def enrich_player(sb: Client, player: dict, dry_run: bool = False) -> bool:
    """
    Enrich a single player record with DUPR data.

    Returns True if enrichment succeeded (or dry-run), False on failure.
    """
    username = player["player_username"]
    player_id = player["id"]

    log.info(f"Processing: {username}")

    # Step 1: Resolve to a real name suitable for DUPR search
    display_name = resolve_display_name(username)

    # Step 2: Search DUPR for the player
    match = search_dupr_player(display_name, dry_run=dry_run)
    if not match:
        log.warning(f"  No DUPR match found for '{username}' (searched as '{display_name}'). Skipping.")
        return False

    dupr_id = match.get("id")

    # Step 3: Fetch detailed player data if we have a real API key and non-dry-run ID
    if not dry_run and dupr_id and not match.get("_dry_run"):
        detail = fetch_dupr_player_detail(dupr_id)
        if detail:
            match.update(detail)

    # Step 4: Build the Supabase update payload
    dupr_data = {
        "dupr_id": dupr_id if not match.get("_dry_run") else None,
        "dupr_rating_singles": match.get("singlesRating"),
        "dupr_rating_doubles": match.get("doublesRating"),
        "dupr_verified_at": "now()" if match.get("ratingVerified") else None,
        "dupr_match_confidence": "probable",  # upgrade to 'confirmed' when player self-links
    }

    # Remove None values to avoid overwriting existing data with nulls unintentionally
    dupr_data = {k: v for k, v in dupr_data.items() if v is not None}

    # Step 5: Write to Supabase
    success = update_player_dupr(sb, player_id, dupr_data, dry_run=dry_run)

    time.sleep(RATE_LIMIT_DELAY)  # Be polite to DUPR API
    return success


def run_enrichment(player_username: Optional[str] = None, dry_run: bool = False, force: bool = False):
    """Main entry point: enrich one or all players."""
    log.info("=== DUPR Enrichment Pipeline ===")
    if dry_run:
        log.info("MODE: DRY RUN — no writes to Supabase")
    else:
        log.info("MODE: LIVE — will write to Supabase")

    sb = get_supabase_client()

    players = fetch_players_needing_enrichment(sb, player_username=player_username, force=force)
    if not players:
        log.info("No players to enrich. Done.")
        return

    results = {"success": 0, "skipped": 0, "failed": 0}

    for player in players:
        try:
            ok = enrich_player(sb, player, dry_run=dry_run)
            if ok:
                results["success"] += 1
            else:
                results["skipped"] += 1
        except Exception as e:
            log.error(f"Unexpected error processing {player.get('player_username')}: {e}")
            results["failed"] += 1

    log.info("=== Enrichment Complete ===")
    log.info(f"  Success: {results['success']}")
    log.info(f"  Skipped: {results['skipped']}")
    log.info(f"  Failed:  {results['failed']}")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def parse_args():
    parser = argparse.ArgumentParser(
        description="Enrich Courtana player profiles with DUPR ratings."
    )
    parser.add_argument(
        "--player",
        type=str,
        default=None,
        help="Courtana username to enrich (default: all players missing dupr_id)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would happen without writing to Supabase",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Re-enrich players even if they already have a dupr_id",
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    run_enrichment(
        player_username=args.player,
        dry_run=args.dry_run,
        force=args.force,
    )

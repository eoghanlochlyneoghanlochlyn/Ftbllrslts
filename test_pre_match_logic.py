import json
import re
from datetime import datetime, timezone

import requests


CACHE_FILE = "matches_cache.json"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 Chrome/131.0 Safari/537.36"
    )
}


def load_cache():
    try:
        with open(CACHE_FILE, "r", encoding="utf-8") as file:
            return json.load(file)

    except FileNotFoundError:
        print("Cache file not found.")
        return {}

    except json.JSONDecodeError:
        print("Cache file contains invalid JSON.")
        return {}


def parse_utc_datetime(value):
    if not value:
        return None

    try:
        if value.endswith("Z"):
            value = value[:-1] + "+00:00"

        dt = datetime.fromisoformat(value)

        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)

        return dt.astimezone(timezone.utc)

    except ValueError:
        return None


def get_minutes_until_kickoff(utc_time):
    kickoff = parse_utc_datetime(utc_time)

    if kickoff is None:
        return None

    now = datetime.now(timezone.utc)

    seconds_remaining = (
        kickoff - now
    ).total_seconds()

    return seconds_remaining / 60


def fetch_match_page(match_id):
    url = f"https://www.fotmob.com/match/{match_id}"

    try:
        response = requests.get(
            url,
            headers=HEADERS,
            timeout=20,
        )

        if response.status_code != 200:
            print(
                f"  Could not fetch match page. "
                f"HTTP status: {response.status_code}"
            )
            return None

        match = re.search(
            r'<script id="__NEXT_DATA__" type="application/json">(.*?)</script>',
            response.text,
            re.DOTALL,
        )

        if not match:
            print("  __NEXT_DATA__ not found.")
            return None

        return json.loads(match.group(1))

    except requests.RequestException as exc:
        print(f"  Request error: {exc}")
        return None

    except json.JSONDecodeError:
        print("  Invalid JSON in __NEXT_DATA__.")
        return None


def get_lineup_info(match_id):
    data = fetch_match_page(match_id)

    if not data:
        return {
            "available": False,
            "lineup_type": None,
            "home_starters": 0,
            "away_starters": 0,
        }

    try:
        page = data["props"]["pageProps"]
        content = page.get("content", {})
        lineup = content.get("lineup") or {}

        lineup_type = lineup.get("lineupType")

        home_team = lineup.get("homeTeam") or {}
        away_team = lineup.get("awayTeam") or {}

        home_starters = home_team.get("starters") or []
        away_starters = away_team.get("starters") or []

        both_teams_have_starters = (
            isinstance(home_starters, list)
            and len(home_starters) > 0
            and isinstance(away_starters, list)
            and len(away_starters) > 0
        )

        is_confirmed = (
            str(lineup_type).lower() == "confirmed"
        )

        available = (
            is_confirmed
            and both_teams_have_starters
        )

        return {
            "available": available,
            "lineup_type": lineup_type,
            "home_starters": len(home_starters),
            "away_starters": len(away_starters),
        }

    except (KeyError, TypeError, AttributeError):
        return {
            "available": False,
            "lineup_type": None,
            "home_starters": 0,
            "away_starters": 0,
        }


def evaluate_match(match_id, match):
    home = match.get("home", "Unknown")
    away = match.get("away", "Unknown")

    status = match.get("status", "")
    pre_match_sent = match.get("pre_match_sent", False)
    utc_time = match.get("utc_time")

    minutes_until = get_minutes_until_kickoff(utc_time)

    print()
    print("=" * 70)
    print(f"{home} 🆚 {away}")
    print(f"Match ID: {match_id}")
    print(f"Status: {status}")
    print(f"UTC kickoff: {utc_time}")

    if minutes_until is None:
        print("Minutes until kickoff: Unknown")
        print("Decision: WAIT")
        return

    print(
        f"Minutes until kickoff: "
        f"{minutes_until:.1f}"
    )

    if pre_match_sent:
        print("Pre-match already sent: True")
        print("Decision: ALREADY SENT")
        return

    print("Pre-match already sent: False")

    if status != "Upcoming":
        print("Decision: WAIT")
        print("Reason: Match is not Upcoming")
        return

    lineup_info = get_lineup_info(match_id)

    lineup_available = lineup_info["available"]
    lineup_type = lineup_info["lineup_type"]

    print(f"FotMob lineupType: {lineup_type}")
    print(
        "Home starters: "
        f"{lineup_info['home_starters']}"
    )
    print(
        "Away starters: "
        f"{lineup_info['away_starters']}"
    )

    print(
        f"Both official lineups available: "
        f"{lineup_available}"
    )

    eligible_by_lineup = lineup_available

    eligible_by_one_hour = (
        minutes_until <= 60
        and minutes_until >= 0
    )

    print(
        f"Eligible by official lineups: "
        f"{eligible_by_lineup}"
    )

    print(
        f"Eligible by one-hour rule: "
        f"{eligible_by_one_hour}"
    )

    if eligible_by_lineup:
        print("Decision: SEND")
        print(
            "Reason: Both official lineups are confirmed."
        )

    elif eligible_by_one_hour:
        print("Decision: SEND")
        print(
            "Reason: One hour or less remains "
            "until kickoff."
        )

    else:
        print("Decision: WAIT")
        print(
            "Reason: Official lineups are not confirmed "
            "and more than one hour remains."
        )


def main():
    print("Pre-match logic test")
    print("=" * 70)

    cache = load_cache()

    if not cache:
        print("No matches found in cache.")
        return

    print(f"Cached matches: {len(cache)}")

    for match_id, match in cache.items():
        evaluate_match(match_id, match)

    print()
    print("=" * 70)
    print("Test completed. No Telegram message was sent.")


if __name__ == "__main__":
    main()

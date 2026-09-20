import json
import re
import sys
from datetime import date, datetime, time, timedelta, timezone
from zoneinfo import ZoneInfo

import requests

FOTMOB_URL = "https://www.fotmob.com/matches"
IRAN_TZ = ZoneInfo("Asia/Tehran")
TARGET_DATE = date(2026, 9, 20)

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/131.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/json;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Referer": "https://www.fotmob.com/",
    "Cache-Control": "no-cache",
    "Pragma": "no-cache",
}

TIMEOUT = 30


def fetch_matches_page(target_date):
    url = f"{FOTMOB_URL}?date={target_date.isoformat()}"

    response = requests.get(
        url,
        headers=HEADERS,
        timeout=TIMEOUT,
    )
    response.raise_for_status()

    return response.url, response.text


def extract_json_scripts(html):
    scripts = []

    next_data = re.search(
        r'<script[^>]+id=["\']__NEXT_DATA__["\'][^>]*>(.*?)</script>',
        html,
        re.DOTALL | re.IGNORECASE,
    )

    if next_data:
        try:
            scripts.append(json.loads(next_data.group(1)))
        except json.JSONDecodeError:
            pass

    for match in re.finditer(
        r"<script[^>]*>(.*?)</script>",
        html,
        re.DOTALL | re.IGNORECASE,
    ):
        text = match.group(1).strip()

        if not text or len(text) < 2:
            continue

        if text.startswith("{") or text.startswith("["):
            try:
                scripts.append(json.loads(text))
            except json.JSONDecodeError:
                continue

    return scripts


def parse_datetime(value):
    if value is None:
        return None

    if isinstance(value, (int, float)):
        timestamp = float(value)

        if timestamp > 100_000_000_000:
            timestamp /= 1000

        try:
            return datetime.fromtimestamp(timestamp, tz=timezone.utc)
        except (ValueError, OSError, OverflowError):
            return None

    if not isinstance(value, str):
        return None

    value = value.strip()

    if not value:
        return None

    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))

        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)

        return parsed.astimezone(timezone.utc)
    except ValueError:
        return None


def get_team(team):
    if not isinstance(team, dict):
        return None

    team_id = (
        team.get("id")
        or team.get("teamId")
        or team.get("teamID")
        or team.get("team_id")
    )

    name = (
        team.get("name")
        or team.get("longName")
        or team.get("shortName")
        or team.get("title")
    )

    if not name and isinstance(team.get("name"), dict):
        name = team["name"].get("text") or team["name"].get("value")

    if team_id is None and not name:
        return None

    return {
        "id": str(team_id) if team_id is not None else None,
        "name": str(name) if name else None,
    }


def get_match_time(obj):
    for key in (
        "matchTimeUTC",
        "utcTime",
        "startTime",
        "kickoff",
        "timeUTC",
        "date",
    ):
        if key in obj:
            parsed = parse_datetime(obj.get(key))
            if parsed:
                return parsed

    status = obj.get("status")
    if isinstance(status, dict):
        for key in ("utcTime", "matchTimeUTC", "startTime"):
            parsed = parse_datetime(status.get(key))
            if parsed:
                return parsed

    return None


def get_teams(obj):
    home = (
        obj.get("homeTeam")
        or obj.get("home")
        or obj.get("home_team")
    )
    away = (
        obj.get("awayTeam")
        or obj.get("away")
        or obj.get("away_team")
    )

    home = get_team(home)
    away = get_team(away)

    if home and away:
        return home, away

    return None, None


def get_match_id(obj):
    for key in ("matchId", "matchID", "id", "match_id"):
        value = obj.get(key)

        if value is not None and not isinstance(value, dict):
            return str(value)

    return None


def looks_like_match(obj):
    if not isinstance(obj, dict):
        return False

    home, away = get_teams(obj)

    if not home or not away:
        return False

    if not get_match_time(obj):
        return False

    return get_match_id(obj) is not None


def walk_matches(value, found):
    if isinstance(value, dict):
        if looks_like_match(value):
            match_id = get_match_id(value)

            if match_id:
                found[match_id] = value

        for child in value.values():
            walk_matches(child, found)

    elif isinstance(value, list):
        for child in value:
            walk_matches(child, found)


def get_competition(obj):
    candidates = (
        obj.get("league"),
        obj.get("tournament"),
        obj.get("competition"),
        obj.get("parentLeague"),
    )

    for item in candidates:
        if isinstance(item, dict):
            name = (
                item.get("name")
                or item.get("longName")
                or item.get("title")
            )
            league_id = (
                item.get("id")
                or item.get("leagueId")
                or item.get("primaryId")
            )

            if name or league_id:
                return {
                    "id": str(league_id) if league_id is not None else None,
                    "name": str(name) if name else None,
                }

    return None


def build_match(obj):
    home, away = get_teams(obj)
    match_time = get_match_time(obj)

    if not home or not away or not match_time:
        return None

    iran_time = match_time.astimezone(IRAN_TZ)

    if iran_time.date() != TARGET_DATE:
        return None

    competition = get_competition(obj)

    return {
        "id": get_match_id(obj),
        "home_team": home["name"],
        "home_team_id": home["id"],
        "away_team": away["name"],
        "away_team_id": away["id"],
        "competition": competition["name"] if competition else None,
        "competition_id": competition["id"] if competition else None,
        "kickoff_iran": iran_time.strftime("%Y-%m-%d %H:%M:%S"),
        "kickoff_utc": match_time.isoformat(),
        "url": f"https://www.fotmob.com/match/{get_match_id(obj)}",
    }


def main():
    print("=" * 90)
    print("FotMob - ALL MATCHES FOR 2026-09-20")
    print("Timezone: Asia/Tehran")
    print("=" * 90)
    print()

    try:
        final_url, html = fetch_matches_page(TARGET_DATE)
    except requests.RequestException as exc:
        print(f"ERROR: Could not read FotMob matches page: {exc}")
        sys.exit(1)

    print(f"URL: {final_url}")
    print(f"HTML length: {len(html):,}")
    print()

    scripts = extract_json_scripts(html)

    if not scripts:
        print("ERROR: No JSON data was found in the FotMob page.")
        sys.exit(1)

    found = {}

    for data in scripts:
        walk_matches(data, found)

    matches = []

    for obj in found.values():
        match = build_match(obj)

        if match:
            matches.append(match)

    matches.sort(key=lambda item: item["kickoff_iran"])

    print(f"Matches found: {len(matches)}")
    print()

    for index, match in enumerate(matches, start=1):
        print(
            f"{index:03d}. "
            f"{match['home_team']} vs {match['away_team']} | "
            f"{match['kickoff_iran'][11:16]}"
        )
        print(f"     Match ID    : {match['id']}")
        print(f"     Competition : {match['competition']}")
        print(f"     URL         : {match['url']}")
        print()

    print("=" * 90)
    print("JSON")
    print("=" * 90)
    print(json.dumps(matches, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

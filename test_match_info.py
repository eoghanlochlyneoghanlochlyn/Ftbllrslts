# test_next_24h_fotmob.py

import json
import re
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

import requests
from bs4 import BeautifulSoup


FOTMOB_URL = "https://www.fotmob.com/matches"
IRAN_TZ = ZoneInfo("Asia/Tehran")

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/140.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,"
              "image/avif,image/webp,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Cache-Control": "no-cache",
}


def fetch_page(date_value: datetime) -> str:
    """
    Gets the normal FotMob matches webpage for a specific calendar date.
    No FotMob API endpoint is used.
    """
    date_str = date_value.strftime("%Y%m%d")
    url = f"{FOTMOB_URL}?date={date_str}"

    response = requests.get(
        url,
        headers=HEADERS,
        timeout=30,
    )
    response.raise_for_status()

    return response.text


def extract_next_data(html: str):
    """
    Extracts the standard Next.js __NEXT_DATA__ JSON from FotMob HTML.
    """
    soup = BeautifulSoup(html, "html.parser")

    script = soup.find("script", id="__NEXT_DATA__")

    if script and script.string:
        try:
            return json.loads(script.string)
        except json.JSONDecodeError:
            pass

    # Fallback in case the script contents are split/escaped.
    raw = html

    match = re.search(
        r'<script[^>]+id="__NEXT_DATA__"[^>]*>(.*?)</script>',
        raw,
        re.DOTALL,
    )

    if match:
        try:
            return json.loads(match.group(1))
        except json.JSONDecodeError:
            pass

    raise RuntimeError("Could not find valid __NEXT_DATA__ in FotMob HTML.")


def parse_datetime(value):
    """
    Converts common FotMob date/time formats to UTC-aware datetime.
    """
    if value is None:
        return None

    # Unix timestamp
    if isinstance(value, (int, float)):
        try:
            # milliseconds
            if value > 10_000_000_000:
                return datetime.fromtimestamp(value / 1000, tz=timezone.utc)

            # seconds
            if value > 1_000_000_000:
                return datetime.fromtimestamp(value, tz=timezone.utc)
        except (ValueError, OSError, OverflowError):
            return None

    if not isinstance(value, str):
        return None

    text = value.strip()

    if not text:
        return None

    # ISO 8601
    try:
        iso = text.replace("Z", "+00:00")
        dt = datetime.fromisoformat(iso)

        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)

        return dt.astimezone(timezone.utc)

    except ValueError:
        pass

    # Common FotMob-like formats
    formats = (
        "%Y-%m-%dT%H:%M:%S.%fZ",
        "%Y-%m-%dT%H:%M:%SZ",
        "%Y-%m-%d %H:%M:%S",
    )

    for fmt in formats:
        try:
            return datetime.strptime(text, fmt).replace(tzinfo=timezone.utc)
        except ValueError:
            continue

    return None


def get_team_name(team):
    if not isinstance(team, dict):
        return None

    for key in (
        "name",
        "shortName",
        "longName",
        "teamName",
    ):
        value = team.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()

    return None


def get_match_time(match):
    """
    Tries several known time locations used in FotMob data.
    """

    status = match.get("status")

    if isinstance(status, dict):
        for key in (
            "utcTime",
            "kickoffTime",
            "startTime",
            "time",
        ):
            dt = parse_datetime(status.get(key))
            if dt:
                return dt

    for key in (
        "utcTime",
        "startTime",
        "kickoffTime",
        "dateTime",
        "time",
        "timeTS",
        "timestamp",
        "startTimestamp",
    ):
        dt = parse_datetime(match.get(key))
        if dt:
            return dt

    return None


def get_match_id(match):
    for key in (
        "id",
        "matchId",
        "eventId",
    ):
        value = match.get(key)

        if value is not None:
            return str(value)

    return None


def extract_teams(match):
    """
    Supports several FotMob object layouts.
    """

    home = None
    away = None

    for home_key, away_key in (
        ("homeTeam", "awayTeam"),
        ("home", "away"),
    ):
        if home is None and isinstance(match.get(home_key), dict):
            home = match.get(home_key)

        if away is None and isinstance(match.get(away_key), dict):
            away = match.get(away_key)

    home_name = get_team_name(home)
    away_name = get_team_name(away)

    if not home_name or not away_name:
        return None, None

    return home_name, away_name


def get_league_name(match):
    for key in (
        "league",
        "competition",
        "tournament",
    ):
        value = match.get(key)

        if isinstance(value, dict):
            for name_key in (
                "name",
                "displayName",
                "shortName",
            ):
                name = value.get(name_key)

                if isinstance(name, str) and name.strip():
                    return name.strip()

        elif isinstance(value, str) and value.strip():
            return value.strip()

    return "نامشخص"


def looks_like_match(obj):
    if not isinstance(obj, dict):
        return False

    match_id = get_match_id(obj)

    if not match_id:
        return False

    home_name, away_name = extract_teams(obj)

    if not home_name or not away_name:
        return False

    match_time = get_match_time(obj)

    if not match_time:
        return False

    return True


def walk_json(obj, found):
    """
    Recursively scans the entire Next.js JSON tree and finds
    match-like objects regardless of their exact nesting.
    """

    if isinstance(obj, dict):

        if looks_like_match(obj):
            match_id = get_match_id(obj)

            # Keep one object per match id.
            if match_id not in found:
                found[match_id] = obj

        for value in obj.values():
            walk_json(value, found)

    elif isinstance(obj, list):

        for item in obj:
            walk_json(item, found)


def normalize_match(match):
    match_id = get_match_id(match)

    home_name, away_name = extract_teams(match)

    utc_time = get_match_time(match)

    if not match_id or not home_name or not away_name or not utc_time:
        return None

    iran_time = utc_time.astimezone(IRAN_TZ)

    return {
        "id": match_id,
        "home": home_name,
        "away": away_name,
        "league": get_league_name(match),
        "utc": utc_time,
        "iran": iran_time,
    }


def get_matches_for_date(date_value):
    html = fetch_page(date_value)
    data = extract_next_data(html)

    found = {}
    walk_json(data, found)

    matches = []

    for raw_match in found.values():
        normalized = normalize_match(raw_match)

        if normalized:
            matches.append(normalized)

    matches.sort(key=lambda x: x["utc"])

    return matches


def main():
    now_iran = datetime.now(IRAN_TZ)
    end_iran = now_iran + timedelta(hours=24)

    print("=" * 80)
    print("FotMob - مسابقات 24 ساعت آینده")
    print("=" * 80)
    print(f"زمان فعلی ایران : {now_iran:%Y-%m-%d %H:%M:%S}")
    print(f"تا                 : {end_iran:%Y-%m-%d %H:%M:%S}")
    print()

    # فقط دو روز تقویمی که بازه 24 ساعته می‌تواند داخلشان باشد.
    dates_to_check = {
        now_iran.date(),
        end_iran.date(),
    }

    all_matches = {}

    for current_date in sorted(dates_to_check):
        date_dt = datetime.combine(
            current_date,
            datetime.min.time(),
            tzinfo=IRAN_TZ,
        )

        print(f"در حال بررسی صفحه فوت‌موب برای {current_date} ...")

        try:
            matches = get_matches_for_date(date_dt)

        except Exception as exc:
            print(f"خطا در دریافت {current_date}: {exc}")
            continue

        for match in matches:
            # شناسه مسابقه را یکتا می‌کنیم.
            all_matches[match["id"]] = match

    # فقط بازی‌هایی که شروعشان در 24 ساعت آینده است.
    selected = []

    for match in all_matches.values():
        start = match["iran"]

        if now_iran <= start <= end_iran:
            selected.append(match)

    selected.sort(key=lambda x: x["iran"])

    print()
    print("=" * 80)
    print(f"تعداد مسابقات پیدا شده: {len(selected)}")
    print("=" * 80)

    for index, match in enumerate(selected, start=1):
        iran_time = match["iran"]

        print(
            f"{index:03d}. "
            f"{iran_time:%Y-%m-%d %H:%M} | "
            f"{match['home']} - {match['away']} | "
            f"{match['league']} | "
            f"ID: {match['id']}"
        )

    print()
    print("پایان تست.")


if __name__ == "__main__":
    main()

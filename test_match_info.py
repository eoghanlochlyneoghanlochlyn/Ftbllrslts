import json
import re
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timedelta, timezone
from html import unescape
from urllib.parse import urljoin

import requests


FOTMOB_BASE_URL = "https://www.fotmob.com"
MATCHES_URL = f"{FOTMOB_BASE_URL}/matches"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/131.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Referer": f"{FOTMOB_BASE_URL}/",
    "Cache-Control": "no-cache",
    "Pragma": "no-cache",
}

REQUEST_TIMEOUT = 30
MAX_WORKERS = 12

MATCH_HREF_RE = re.compile(
    r"""href=["'](/matches/[^"'#?]+)""",
    re.IGNORECASE,
)

NEXT_DATA_RE = re.compile(
    r"""<script[^>]+id=["']__NEXT_DATA__["'][^>]*>(.*?)</script>""",
    re.DOTALL | re.IGNORECASE,
)


def get_html(url):
    response = requests.get(
        url,
        headers=HEADERS,
        timeout=REQUEST_TIMEOUT,
    )
    response.raise_for_status()
    return response.text


def extract_match_urls(html):
    urls = set()

    for match in MATCH_HREF_RE.finditer(html):
        href = unescape(match.group(1)).strip()

        if href.startswith("/matches/"):
            urls.add(urljoin(FOTMOB_BASE_URL, href))

    return sorted(urls)


def extract_next_data(html):
    match = NEXT_DATA_RE.search(html)

    if not match:
        return None

    try:
        return json.loads(match.group(1))
    except json.JSONDecodeError:
        return None


def get_page_props(data):
    if not isinstance(data, dict):
        return {}

    props = data.get("props")

    if not isinstance(props, dict):
        return {}

    page_props = props.get("pageProps")

    if not isinstance(page_props, dict):
        return {}

    return page_props


def get_general(page_props):
    general = page_props.get("general")

    if isinstance(general, dict):
        return general

    data = page_props.get("data")

    if isinstance(data, dict):
        general = data.get("general")

        if isinstance(general, dict):
            return general

    return {}


def get_content(page_props):
    candidates = [
        page_props.get("content"),
        (
            page_props.get("data", {}).get("content")
            if isinstance(page_props.get("data"), dict)
            else None
        ),
        (
            page_props.get("match", {}).get("content")
            if isinstance(page_props.get("match"), dict)
            else None
        ),
        page_props.get("matchData"),
    ]

    for candidate in candidates:
        if isinstance(candidate, dict):
            return candidate

    return {}


def get_team_name(team):
    if not isinstance(team, dict):
        return None

    for key in ("longName", "name", "shortName", "title"):
        value = team.get(key)

        if value:
            return str(value)

    return None


def get_team_id(team):
    if not isinstance(team, dict):
        return None

    for key in ("id", "teamId", "teamID", "team_id"):
        value = team.get(key)

        if value is not None:
            return str(value)

    return None


def parse_datetime(value):
    if value is None:
        return None

    if isinstance(value, (int, float)):
        timestamp = float(value)

        if timestamp > 100000000000:
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
        pass

    for fmt in (
        "%Y-%m-%dT%H:%M:%S.%fZ",
        "%Y-%m-%dT%H:%M:%SZ",
        "%Y-%m-%d %H:%M:%S",
    ):
        try:
            return datetime.strptime(value, fmt).replace(tzinfo=timezone.utc)
        except ValueError:
            continue

    return None


def get_match_time(general):
    for key in (
        "matchTimeUTC",
        "matchTime",
        "startTime",
        "utcTime",
        "kickoff",
    ):
        value = general.get(key)

        if value:
            return value

    return None


def get_id(general, keys):
    for key in keys:
        value = general.get(key)

        if value is not None:
            return str(value)

    return None


def get_stage(content):
    match_facts = content.get("matchFacts")

    if not isinstance(match_facts, dict):
        return None

    info_box = match_facts.get("infoBox")

    if not isinstance(info_box, dict):
        return None

    tournament = info_box.get("Tournament")

    if not isinstance(tournament, dict):
        return None

    for key in ("roundName", "round", "stage", "name"):
        value = tournament.get(key)

        if value:
            return str(value)

    return None


def read_match_page(url):
    try:
        html = get_html(url)
    except Exception as exc:
        return {"url": url, "error": str(exc)}

    data = extract_next_data(html)

    if not isinstance(data, dict):
        return {"url": url, "error": "__NEXT_DATA__ not found"}

    page_props = get_page_props(data)
    general = get_general(page_props)

    if not general:
        return {"url": url, "error": "general not found"}

    content = get_content(page_props)

    home_team = general.get("homeTeam")
    away_team = general.get("awayTeam")

    raw_time = get_match_time(general)
    match_time = parse_datetime(raw_time)

    return {
        "match_id": get_id(general, ("matchId", "matchID", "id")),
        "match_time_utc": (
            match_time.isoformat() if match_time else None
        ),
        "home_team": get_team_name(home_team),
        "away_team": get_team_name(away_team),
        "home_team_id": get_team_id(home_team),
        "away_team_id": get_team_id(away_team),
        "league_id": get_id(general, ("leagueId", "leagueID")),
        "parent_league_id": get_id(
            general,
            ("parentLeagueId", "parentLeagueID"),
        ),
        "stage": get_stage(content),
        "url": url,
        "error": None,
    }


def main():
    now = datetime.now(timezone.utc)
    window_start = now
    window_end = now + timedelta(hours=24)

    print("=" * 100)
    print("FotMob - MATCHES IN NEXT 24 HOURS")
    print("=" * 100)
    print()
    print(f"Current UTC : {window_start.isoformat()}")
    print(f"Window end  : {window_end.isoformat()}")
    print()
    print("SOURCE: FotMob website /matches pages + match HTML + __NEXT_DATA__")
    print("NO FotMob API ENDPOINT IS USED.")
    print()

    # The 24-hour window can cross a UTC date boundary.
    dates = [
        window_start.date() + timedelta(days=-1),
        window_start.date(),
        window_start.date() + timedelta(days=1),
    ]

    print("1) Discovering match links from FotMob website pages...")

    match_urls = set()

    for date_value in dates:
        date_text = date_value.isoformat()
        url = f"{MATCHES_URL}?date={date_text}"

        try:
            html = get_html(url)
            page_urls = extract_match_urls(html)
        except Exception as exc:
            print(f"  ERROR {date_text}: {exc}")
            continue

        print(f"  {date_text}: {len(page_urls)} match links")

        match_urls.update(page_urls)

    print()
    print(f"Unique match pages: {len(match_urls)}")
    print()

    if not match_urls:
        print("ERROR: FotMob /matches HTML contained no match links.")
        sys.exit(1)

    print("2) Reading match pages and extracting general.matchTimeUTC...")
    print(f"   Workers: {MAX_WORKERS}")
    print()

    matches = []
    errors = []

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = {
            executor.submit(read_match_page, url): url
            for url in sorted(match_urls)
        }

        total = len(futures)

        for index, future in enumerate(as_completed(futures), start=1):
            url = futures[future]

            try:
                result = future.result()
            except Exception as exc:
                errors.append({"url": url, "error": str(exc)})
                continue

            if result.get("error"):
                errors.append(result)
                continue

            match_time = parse_datetime(result.get("match_time_utc"))

            if match_time is None:
                errors.append(
                    {
                        "url": url,
                        "error": "matchTimeUTC not found",
                    }
                )
                continue

            if window_start <= match_time <= window_end:
                matches.append(result)

            if index % 25 == 0 or index == total:
                print(
                    f"  Processed {index}/{total} | "
                    f"in 24h: {len(matches)} | "
                    f"errors: {len(errors)}"
                )

    matches.sort(
        key=lambda item: parse_datetime(item["match_time_utc"])
        or datetime.max.replace(tzinfo=timezone.utc)
    )

    print()
    print("=" * 100)
    print(f"FOUND {len(matches)} MATCHES IN NEXT 24 HOURS")
    print("=" * 100)
    print()

    for index, match in enumerate(matches, start=1):
        print(
            f"{index:03d}. "
            f"{match.get('home_team', '?')} vs "
            f"{match.get('away_team', '?')}"
        )
        print(f"     Match ID      : {match.get('match_id')}")
        print(f"     Kickoff UTC   : {match.get('match_time_utc')}")
        print(f"     Home Team ID  : {match.get('home_team_id')}")
        print(f"     Away Team ID  : {match.get('away_team_id')}")
        print(f"     League ID     : {match.get('league_id')}")
        print(f"     Parent League : {match.get('parent_league_id')}")
        print(f"     Stage         : {match.get('stage')}")
        print(f"     URL           : {match.get('url')}")
        print()

    print("=" * 100)
    print("JSON OUTPUT")
    print("=" * 100)
    print(json.dumps(matches, ensure_ascii=False, indent=2))

    print()
    print("=" * 100)
    print("SUMMARY")
    print("=" * 100)
    print(f"Match links discovered : {len(match_urls)}")
    print(f"Matches in next 24h    : {len(matches)}")
    print(f"Pages with errors      : {len(errors)}")

    if errors:
        print()
        print("First errors:")

        for error in errors[:20]:
            print(
                f"- {error.get('url')}: "
                f"{error.get('error')}"
            )


if __name__ == "__main__":
    main()

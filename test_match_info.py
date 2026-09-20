import json
import re
import sys
import xml.etree.ElementTree as ET
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timedelta, timezone
from urllib.parse import urlparse

import requests

FOTMOB_BASE_URL = "https://www.fotmob.com"
SITEMAP_INDEX_URL = f"{FOTMOB_BASE_URL}/sitemap/en/matches.xml"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/131.0.0.0 Safari/537.36"
    ),
    "Accept": "application/xml,text/xml,text/html,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Referer": f"{FOTMOB_BASE_URL}/",
    "Cache-Control": "no-cache",
    "Pragma": "no-cache",
}

REQUEST_TIMEOUT = 30
MAX_WORKERS = 12


def get_url(url):
    response = requests.get(url, headers=HEADERS, timeout=REQUEST_TIMEOUT)
    response.raise_for_status()
    return response.text


def extract_xml_urls(xml_text):
    root = ET.fromstring(xml_text)
    return [
        element.text.strip()
        for element in root.iter()
        if element.tag.endswith("loc") and element.text
    ]


def extract_next_data(html):
    match = re.search(
        r"""<script[^>]+id=["']__NEXT_DATA__["'][^>]*>(.*?)</script>""",
        html,
        re.DOTALL | re.IGNORECASE,
    )
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
    return page_props if isinstance(page_props, dict) else {}


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


def get_id(general, keys):
    for key in keys:
        value = general.get(key)
        if value is not None:
            return str(value)

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
        html = get_url(url)
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
    raw_time = get_match_time(general)
    match_time = parse_datetime(raw_time)

    return {
        "match_id": get_id(general, ("matchId", "matchID", "id")),
        "match_time_utc": match_time.isoformat() if match_time else None,
        "home_team": get_team_name(general.get("homeTeam")),
        "away_team": get_team_name(general.get("awayTeam")),
        "home_team_id": get_team_id(general.get("homeTeam")),
        "away_team_id": get_team_id(general.get("awayTeam")),
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
    window_end = now + timedelta(hours=24)

    print("=" * 100)
    print("FotMob - MATCHES IN NEXT 24 HOURS")
    print("=" * 100)
    print()
    print(f"Current UTC : {now.isoformat()}")
    print(f"Window end  : {window_end.isoformat()}")
    print()
    print("SOURCE: FotMob website sitemap + match HTML + __NEXT_DATA__")
    print("NO FotMob API ENDPOINT IS USED.")
    print()

    print("1) Reading FotMob matches sitemap index...")

    try:
        index_xml = get_url(SITEMAP_INDEX_URL)
        child_sitemaps = extract_xml_urls(index_xml)
    except Exception as exc:
        print(f"ERROR: Could not read sitemap index: {exc}")
        sys.exit(1)

    print(f"Child sitemaps found: {len(child_sitemaps)}")
    print()

    if not child_sitemaps:
        print("ERROR: Sitemap index contains no child sitemaps.")
        sys.exit(1)

    print("2) Reading sitemap structure only...")
    print("   Match pages are NOT crawled yet.")
    print()

    # The sitemap contains many historical/future match URLs. Crawling every
    # URL is far too expensive, so first inspect only a small sample of each
    # child sitemap. This test is specifically for determining whether the
    # sitemap itself gives us a usable way to narrow the candidates.
    sample_size = 5
    sampled_urls = set()

    for index, sitemap_url in enumerate(child_sitemaps, start=1):
        try:
            urls = extract_xml_urls(get_url(sitemap_url))
        except Exception as exc:
            print(f"  [{index}/{len(child_sitemaps)}] ERROR: {exc}")
            continue

        match_urls = [
            url for url in urls
            if urlparse(url).path.startswith("/matches/")
        ]

        if match_urls:
            sampled_urls.update(match_urls[:sample_size])

        print(
            f"  [{index}/{len(child_sitemaps)}] "
            f"match URLs: {len(match_urls)} | "
            f"sampled: {min(len(match_urls), sample_size)}"
        )

    print()
    print(f"Sampled unique match pages: {len(sampled_urls)}")
    print()

    if not sampled_urls:
        print("ERROR: No /matches/ URLs were found in the sitemap.")
        sys.exit(1)

    print("3) Reading only the sampled match pages...")
    print(f"   Workers: {MAX_WORKERS}")
    print("   Time is read from matchTimeUTC on the actual FotMob page.")
    print()

    matches = []
    errors = []

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = {
            executor.submit(read_match_page, url): url
            for url in sorted(sampled_urls)
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
                errors.append({
                    "url": url,
                    "error": "matchTimeUTC not found",
                })
                continue

            if now <= match_time <= window_end:
                matches.append(result)

            if index % 100 == 0 or index == total:
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
    print(f"Match pages sampled    : {len(sampled_urls)}")
    print(f"Matches in next 24h    : {len(matches)}")
    print(f"Pages with errors      : {len(errors)}")

    if errors:
        print()
        print("First errors:")
        for error in errors[:20]:
            print(f"- {error.get('url')}: {error.get('error')}")


if __name__ == "__main__":
    main()

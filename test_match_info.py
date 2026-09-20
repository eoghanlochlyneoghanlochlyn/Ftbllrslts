import json
import re
import xml.etree.ElementTree as ET

import requests


SITEMAP_URL = "https://www.fotmob.com/sitemap/en/matches.xml"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/131.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Referer": "https://www.fotmob.com/",
    "Cache-Control": "no-cache",
    "Pragma": "no-cache",
}

MAX_CHILD_SITEMAPS = 3
MAX_MATCH_URLS = 5


def get(url):
    print()
    print("=" * 100)
    print("GET:", url)

    response = requests.get(url, headers=HEADERS, timeout=30)

    print("STATUS:", response.status_code)
    print("FINAL URL:", response.url)
    print("CONTENT TYPE:", response.headers.get("content-type"))
    print("LENGTH:", len(response.text))

    response.raise_for_status()
    return response.text


def local_name(tag):
    return tag.rsplit("}", 1)[-1]


def parse_sitemap(text):
    root = ET.fromstring(text)

    sitemap_urls = []
    match_urls = []

    for element in root:
        element_name = local_name(element.tag)
        loc = None

        for child in element:
            if local_name(child.tag) == "loc":
                loc = (child.text or "").strip()
                break

        if not loc:
            continue

        if element_name == "sitemap":
            sitemap_urls.append(loc)
        elif element_name == "url":
            match_urls.append(loc)

    return sitemap_urls, match_urls


def collect_match_urls():
    root_text = get(SITEMAP_URL)
    sitemap_urls, direct_urls = parse_sitemap(root_text)

    print()
    print("ROOT CHILD SITEMAPS:", len(sitemap_urls))
    print("ROOT DIRECT MATCH URLS:", len(direct_urls))

    if direct_urls:
        return direct_urls[:MAX_MATCH_URLS]

    result = []

    for sitemap_url in sitemap_urls[:MAX_CHILD_SITEMAPS]:
        try:
            child_text = get(sitemap_url)
            _, child_match_urls = parse_sitemap(child_text)

            print("CHILD MATCH URLS:", len(child_match_urls))

            for url in child_match_urls:
                if url not in result:
                    result.append(url)

                if len(result) >= MAX_MATCH_URLS:
                    return result
        except Exception as error:
            print("CHILD SITEMAP ERROR:", repr(error))

    return result


def extract_next_data(html):
    pattern = re.compile(
        r"""<script[^>]+id=["']__NEXT_DATA__["'][^>]*>(.*?)</script>""",
        re.IGNORECASE | re.DOTALL,
    )

    match = pattern.search(html)

    if not match:
        return None

    try:
        return json.loads(match.group(1).strip())
    except json.JSONDecodeError as error:
        print("NEXT_DATA JSON ERROR:", error)
        return None


def extract_event_jsonld(html):
    pattern = re.compile(
        r"""<script[^>]*id=["']eventJSONLD["'][^>]*>(.*?)</script>""",
        re.IGNORECASE | re.DOTALL,
    )

    match = pattern.search(html)

    if not match:
        return None

    raw = match.group(1).strip()

    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return raw


def find_path(data, wanted_keys, path="root", results=None):
    if results is None:
        results = []

    if isinstance(data, dict):
        for key, value in data.items():
            current = f"{path}.{key}"

            if key in wanted_keys:
                results.append((current, value))

            find_path(value, wanted_keys, current, results)

    elif isinstance(data, list):
        for index, value in enumerate(data):
            find_path(value, wanted_keys, f"{path}[{index}]", results)

    return results


def get_first(data, keys):
    for path, value in find_path(data, set(keys)):
        if value is not None and value != "":
            return path, value

    return None, None


def get_by_path(data, parts):
    current = data

    for part in parts:
        if not isinstance(current, dict) or part not in current:
            return None
        current = current[part]

    return current


def find_match_content(data):
    candidates = [
        (
            "root.props.pageProps.content",
            get_by_path(data, ["props", "pageProps", "content"]),
        ),
        (
            "root.props.pageProps.data.content",
            get_by_path(data, ["props", "pageProps", "data", "content"]),
        ),
        (
            "root.props.pageProps.match.content",
            get_by_path(data, ["props", "pageProps", "match", "content"]),
        ),
        (
            "root.props.pageProps.matchData",
            get_by_path(data, ["props", "pageProps", "matchData"]),
        ),
    ]

    for path, value in candidates:
        if isinstance(value, dict) and any(
            key in value
            for key in ("matchFacts", "lineup", "stats", "header", "general")
        ):
            return path, value

    return None, None


def team_summary(team):
    if not isinstance(team, dict):
        return None

    return {
        "id": team.get("id") or team.get("teamId") or team.get("teamID"),
        "name": (
            team.get("longName")
            or team.get("name")
            or team.get("shortName")
            or team.get("title")
        ),
        "shortName": team.get("shortName"),
    }


def print_value(label, path, value, limit=2500):
    print()
    print(label)
    print("PATH:", path)

    try:
        output = json.dumps(value, ensure_ascii=False, indent=2)
    except Exception:
        output = repr(value)

    if len(output) > limit:
        output = output[:limit] + "\n... [TRUNCATED]"

    print(output)


def inspect_match(url):
    print()
    print("#" * 100)
    print("MATCH PAGE")
    print(url)
    print("#" * 100)

    html = get(url)

    markers = [
        "__NEXT_DATA__",
        "matchFacts",
        "lineup",
        "lineups",
        "eventJSONLD",
        "application/ld+json",
        "matchId",
        "matchID",
        "homeTeam",
        "awayTeam",
        "tournament",
        "league",
        "startTime",
        "matchTimeUTC",
    ]

    print()
    print("HTML MARKERS")
    for marker in markers:
        print(f"  {marker}: {marker in html}")

    data = extract_next_data(html)

    if data is None:
        print()
        print("ERROR: __NEXT_DATA__ was not found or was invalid.")
        return False

    print()
    print("__NEXT_DATA__: VALID")

    content_path, content = find_match_content(data)

    if content is not None:
        print()
        print("MATCH CONTENT FOUND")
        print("CONTENT PATH:", content_path)
        print("CONTENT TOP KEYS:", list(content.keys())[:80])
    else:
        print()
        print("MATCH CONTENT: NOT FOUND")

    wanted = {
        "matchId",
        "matchID",
        "matchTimeUTC",
        "matchTime",
        "startTime",
        "utcTime",
        "kickoff",
        "status",
        "homeTeam",
        "awayTeam",
        "tournament",
        "league",
        "competition",
        "uniqueTournament",
        "leagueId",
        "tournamentId",
        "uniqueTournamentId",
        "competitionId",
        "competitionID",
        "parentLeagueId",
        "stage",
        "round",
        "roundName",
        "tournamentStage",
        "season",
        "seasonName",
        "legInfo",
        "leg",
    }

    results = find_path(data, wanted)

    print()
    print("KEY FIELD DISCOVERY")
    print("TOTAL MATCHING FIELDS:", len(results))

    for path, value in results[:120]:
        if isinstance(value, (dict, list)):
            print_value("FIELD", path, value, limit=1200)
        else:
            print("FIELD:", path)
            print("VALUE:", repr(value))

    print()
    print("=" * 100)
    print("NORMALIZED MATCH SUMMARY")
    print("=" * 100)

    match_id_path, match_id = get_first(data, ["matchId", "matchID"])

    time_path, match_time = get_first(
        data,
        ["matchTimeUTC", "matchTime", "startTime", "utcTime", "kickoff"],
    )

    home_path, home_team = get_first(data, ["homeTeam"])
    away_path, away_team = get_first(data, ["awayTeam"])

    tournament_path, tournament = get_first(
        data,
        ["tournament", "league", "competition", "uniqueTournament"],
    )

    stage_path, stage = get_first(
        data,
        ["stage", "round", "roundName", "tournamentStage"],
    )

    print("MATCH ID:", match_id)
    print("MATCH ID PATH:", match_id_path)
    print("TIME:", repr(match_time))
    print("TIME PATH:", time_path)
    print("HOME TEAM:", json.dumps(team_summary(home_team), ensure_ascii=False))
    print("HOME TEAM PATH:", home_path)
    print("AWAY TEAM:", json.dumps(team_summary(away_team), ensure_ascii=False))
    print("AWAY TEAM PATH:", away_path)
    print("TOURNAMENT:", json.dumps(tournament, ensure_ascii=False)[:2000])
    print("TOURNAMENT PATH:", tournament_path)
    print("STAGE:", json.dumps(stage, ensure_ascii=False)[:2000])
    print("STAGE PATH:", stage_path)

    if content is not None:
        match_facts = content.get("matchFacts", {})
        leg_info = None

        if isinstance(match_facts, dict):
            info_box = match_facts.get("infoBox", {})
            if isinstance(info_box, dict):
                leg_info = info_box.get("legInfo")

        if leg_info is not None:
            print_value(
                "LEG INFO FROM MATCH CONTENT",
                f"{content_path}.matchFacts.infoBox.legInfo",
                leg_info,
                limit=3000,
            )
        else:
            print("LEG INFO: NOT FOUND AT matchFacts.infoBox.legInfo")

    event_jsonld = extract_event_jsonld(html)

    print()
    print("EVENT JSON-LD")
    if event_jsonld is None:
        print("NOT FOUND")
    else:
        print(json.dumps(event_jsonld, ensure_ascii=False, indent=2)[:4000])

    return True


def main():
    print("=" * 100)
    print("FOTMOB WEBSITE STRUCTURE TEST - PAGE DATA")
    print("=" * 100)
    print("SOURCE: FotMob website HTML + __NEXT_DATA__")
    print("NO FotMob API ENDPOINT IS USED.")

    try:
        urls = collect_match_urls()
    except Exception as error:
        print()
        print("SITEMAP ERROR:", repr(error))
        return

    print()
    print("=" * 100)
    print("MATCH URLS SELECTED FOR TEST")
    print("=" * 100)

    if not urls:
        print("NO MATCH URL FOUND.")
        return

    for index, url in enumerate(urls, start=1):
        print(f"{index}. {url}")

    successful = 0

    for url in urls:
        try:
            if inspect_match(url):
                successful += 1
        except Exception as error:
            print()
            print("MATCH TEST ERROR:", repr(error))

    print()
    print("=" * 100)
    print("TEST FINISHED")
    print("=" * 100)
    print("PAGES TESTED:", len(urls))
    print("SUCCESSFUL:", successful)


if __name__ == "__main__":
    main()

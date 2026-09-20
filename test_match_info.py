import json
import re
import xml.etree.ElementTree as ET

import requests


SITEMAP_URL = "https://www.fotmob.com/sitemap/en/matches.xml"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 "
        "(KHTML, like Gecko) "
        "Chrome/131.0.0.0 Safari/537.36"
    ),
    "Accept": (
        "text/html,application/xhtml+xml,"
        "application/xml;q=0.9,*/*;q=0.8"
    ),
    "Accept-Language": "en-US,en;q=0.9",
    "Referer": "https://www.fotmob.com/",
    "Cache-Control": "no-cache",
    "Pragma": "no-cache",
}


def get(url):
    print()
    print("=" * 80)
    print("GET:", url)

    response = requests.get(
        url,
        headers=HEADERS,
        timeout=30,
    )

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

    print()
    print("ROOT:", local_name(root.tag))
    print("CHILD SITEMAPS:", len(sitemap_urls))
    print("DIRECT URLS:", len(match_urls))

    return sitemap_urls, match_urls


def find_match_url(sitemap_urls, direct_urls):
    if direct_urls:
        return direct_urls[0]

    for sitemap_url in sitemap_urls[:20]:
        try:
            child_text = get(sitemap_url)
        except Exception as error:
            print("CHILD SITEMAP ERROR:", error)
            continue

        child_sitemaps, child_match_urls = parse_sitemap(child_text)

        if child_match_urls:
            return child_match_urls[0]

        for second_url in child_sitemaps[:20]:
            try:
                second_text = get(second_url)
            except Exception as error:
                print("SECOND LEVEL SITEMAP ERROR:", error)
                continue

            _, second_match_urls = parse_sitemap(second_text)

            if second_match_urls:
                return second_match_urls[0]

    return None


def extract_script_blocks(html):
    pattern = re.compile(
        r"""<script(?:\\s[^>]*)?>(.*?)</script>""",
        re.IGNORECASE | re.DOTALL,
    )
    return pattern.findall(html)


def extract_json_scripts(html):
    scripts = extract_script_blocks(html)
    parsed = []

    for index, raw in enumerate(scripts):
        text = raw.strip()

        if not text:
            continue

        if not (
            text.startswith("{")
            or text.startswith("[")
        ):
            continue

        try:
            data = json.loads(text)
        except Exception:
            continue

        parsed.append((index, data))

    return parsed


def find_values(data, wanted_keys, path="root", results=None):
    if results is None:
        results = []

    if isinstance(data, dict):
        for key, value in data.items():
            current_path = f"{path}.{key}"

            if key in wanted_keys:
                results.append((current_path, value))

            find_values(
                value,
                wanted_keys,
                current_path,
                results,
            )

    elif isinstance(data, list):
        for index, value in enumerate(data):
            find_values(
                value,
                wanted_keys,
                f"{path}[{index}]",
                results,
            )

    return results


def contains_match_data(data):
    wanted = {
        "matchFacts",
        "lineup",
        "lineups",
        "stats",
        "header",
        "general",
        "homeTeam",
        "awayTeam",
        "matchId",
        "matchID",
    }

    return bool(find_values(data, wanted))


def show_value(path, value, limit=1500):
    if isinstance(value, (dict, list)):
        try:
            output = json.dumps(
                value,
                ensure_ascii=False,
                indent=2,
            )
        except Exception:
            output = repr(value)
    else:
        output = repr(value)

    if len(output) > limit:
        output = output[:limit] + "\\n... [TRUNCATED]"

    print()
    print(path)
    print(output)


def main():
    print("=" * 80)
    print("FOTMOB WEBSITE STRUCTURE TEST")
    print("=" * 80)

    try:
        sitemap_text = get(SITEMAP_URL)
        sitemap_urls, direct_urls = parse_sitemap(sitemap_text)
    except Exception as error:
        print()
        print("SITEMAP ERROR:", error)
        return

    match_url = find_match_url(
        sitemap_urls,
        direct_urls,
    )

    if not match_url:
        print()
        print("NO MATCH URL FOUND IN SITEMAP")
        return

    print()
    print("=" * 80)
    print("REAL MATCH URL")
    print("=" * 80)
    print(match_url)

    try:
        html = get(match_url)
    except Exception as error:
        print()
        print("MATCH PAGE ERROR:", error)
        return

    print()
    print("=" * 80)
    print("HTML MARKERS")
    print("=" * 80)

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
    ]

    for marker in markers:
        print(f"{marker}: {marker in html}")

    scripts = extract_script_blocks(html)

    print()
    print("TOTAL SCRIPT BLOCKS:", len(scripts))

    json_scripts = extract_json_scripts(html)

    print("PARSED JSON SCRIPT BLOCKS:", len(json_scripts))

    wanted_keys = {
        "matchFacts",
        "lineup",
        "lineups",
        "stats",
        "header",
        "general",
        "matchId",
        "matchID",
        "homeTeam",
        "awayTeam",
        "matchTimeUTC",
        "matchTime",
        "startTime",
        "utcTime",
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
    }

    found_any = False

    print()
    print("=" * 80)
    print("MATCH-RELATED JSON DATA")
    print("=" * 80)

    for script_index, data in json_scripts:
        if not contains_match_data(data):
            continue

        found_any = True

        print()
        print("-" * 80)
        print("SCRIPT INDEX:", script_index)
        print("TOP TYPE:", type(data).__name__)

        results = find_values(
            data,
            wanted_keys,
        )

        for path, value in results[:80]:
            show_value(path, value)

        if len(results) > 80:
            print()
            print(
                f"... {len(results) - 80} additional matching values omitted"
            )

    if not found_any:
        print("NO MATCH-RELATED JSON SCRIPT BLOCK FOUND")

    print()
    print("=" * 80)
    print("NEXT DATA TAG CHECK")
    print("=" * 80)

    next_pattern = re.compile(
        r"""<script[^>]+id=["']__NEXT_DATA__["'][^>]*>(.*?)</script>""",
        re.IGNORECASE | re.DOTALL,
    )

    next_match = next_pattern.search(html)

    if next_match:
        print("__NEXT_DATA__: FOUND")

        try:
            next_data = json.loads(next_match.group(1).strip())
            print("NEXT_DATA JSON: VALID")

            results = find_values(
                next_data,
                wanted_keys,
            )

            print("IMPORTANT VALUES:", len(results))

            for path, value in results[:80]:
                show_value(path, value)
        except Exception as error:
            print("NEXT_DATA JSON ERROR:", error)
    else:
        print("__NEXT_DATA__: NOT FOUND")

    print()
    print("=" * 80)
    print("TEST FINISHED")
    print("=" * 80)


if __name__ == "__main__":
    main()

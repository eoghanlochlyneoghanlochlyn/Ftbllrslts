import json
import re
import html as html_module

import requests


MATCH_ID = "3370572"
MATCH_URL = "https://www.fotmob.com/matches/argentina-vs-france/1hox8a#3370572"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/140.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9",
}


def clean_text(value):
    if value is None:
        return ""

    return re.sub(r"\s+", " ", str(value)).strip()


def get_nested(data, *keys):
    current = data

    for key in keys:
        if not isinstance(current, dict):
            return None

        current = current.get(key)

    return current


def find_all_dicts_with_key(data, key, path="root"):
    results = []

    if isinstance(data, dict):
        if key in data:
            results.append((path, data))

        for child_key, child_value in data.items():
            results.extend(
                find_all_dicts_with_key(
                    child_value,
                    key,
                    f"{path}.{child_key}",
                )
            )

    elif isinstance(data, list):
        for index, item in enumerate(data):
            results.extend(
                find_all_dicts_with_key(
                    item,
                    key,
                    f"{path}[{index}]",
                )
            )

    return results


def extract_next_data(page_text):
    """
    استخراج __NEXT_DATA__ از HTML صفحه FotMob.
    """

    patterns = [
        r'<script id="__NEXT_DATA__" type="application/json">(.*?)</script>',
        r'<script id="__NEXT_DATA__"[^>]*>(.*?)</script>',
    ]

    for pattern in patterns:
        match = re.search(
            pattern,
            page_text,
            flags=re.DOTALL | re.IGNORECASE,
        )

        if not match:
            continue

        raw_json = html_module.unescape(match.group(1))

        try:
            return json.loads(raw_json)
        except Exception as exc:
            print(f"Could not parse __NEXT_DATA__: {exc}")

    return None


def fetch_data():
    print("=" * 80)
    print("FETCHING API")
    print("=" * 80)

    api_url = (
        f"https://www.fotmob.com/api/matchDetails"
        f"?matchId={MATCH_ID}"
    )

    response = requests.get(
        api_url,
        headers=HEADERS,
        timeout=30,
    )

    print(f"API URL: {api_url}")
    print(f"API HTTP status: {response.status_code}")
    print(f"API response length: {len(response.text)}")

    if response.status_code == 200:
        try:
            data = response.json()
            print("Using API JSON.")
            return data
        except Exception as exc:
            print(f"API JSON parse failed: {exc}")

    print()
    print("=" * 80)
    print("FETCHING FOTMOB PAGE FALLBACK")
    print("=" * 80)

    page_response = requests.get(
        MATCH_URL,
        headers=HEADERS,
        timeout=30,
    )

    print(f"Page HTTP status: {page_response.status_code}")
    print(f"Final URL: {page_response.url}")
    print(f"Page response length: {len(page_response.text)}")

    if page_response.status_code != 200:
        print("Page request failed.")
        return None

    data = extract_next_data(page_response.text)

    if data is None:
        print("__NEXT_DATA__ not found or invalid.")
        return None

    print("__NEXT_DATA__ extracted successfully.")

    return data


def print_basic_structure(data):
    print()
    print("=" * 80)
    print("TOP-LEVEL STRUCTURE")
    print("=" * 80)

    if not isinstance(data, dict):
        print("Root is not a dictionary.")
        return

    for key in data.keys():
        print(f"  - {key}")


def print_matchfacts_structure(data):
    print()
    print("=" * 80)
    print("MATCHFACTS STRUCTURE")
    print("=" * 80)

    matchfacts = get_nested(
        data,
        "content",
        "matchFacts",
    )

    if not isinstance(matchfacts, dict):
        print("content.matchFacts not found at direct path.")

        # در NEXT_DATA ممکن است داده داخل pageProps باشد.
        page_props = data.get("props", {}).get("pageProps", {})

        if isinstance(page_props, dict):
            matchfacts = get_nested(
                page_props,
                "content",
                "matchFacts",
            )

    if not isinstance(matchfacts, dict):
        print("Could not locate matchFacts.")
        return

    print("matchFacts keys:")

    for key, value in matchfacts.items():
        if isinstance(value, list):
            print(f"  - {key}: list ({len(value)} items)")
        elif isinstance(value, dict):
            print(f"  - {key}: dict")
        else:
            print(f"  - {key}: {type(value).__name__}")


def locate_content(data):
    candidates = [
        data,
        get_nested(data, "props", "pageProps"),
        get_nested(data, "pageProps"),
    ]

    for candidate in candidates:
        if not isinstance(candidate, dict):
            continue

        if isinstance(candidate.get("content"), dict):
            return candidate["content"]

    return None


def locate_matchfacts(data):
    content = locate_content(data)

    if isinstance(content, dict):
        matchfacts = content.get("matchFacts")

        if isinstance(matchfacts, dict):
            return matchfacts

    candidates = [
        data,
        get_nested(data, "props", "pageProps"),
        get_nested(data, "pageProps"),
    ]

    for candidate in candidates:
        if not isinstance(candidate, dict):
            continue

        if isinstance(candidate.get("matchFacts"), dict):
            return candidate["matchFacts"]

    return None


def locate_stats(data):
    content = locate_content(data)

    if isinstance(content, dict) and "stats" in content:
        return content["stats"]

    candidates = [
        data,
        get_nested(data, "props", "pageProps"),
        get_nested(data, "pageProps"),
    ]

    for candidate in candidates:
        if not isinstance(candidate, dict):
            continue

        if "stats" in candidate:
            return candidate["stats"]

    return None


def print_event_periods(data):
    print()
    print("=" * 80)
    print("MATCH EVENT PERIODS")
    print("=" * 80)

    matchfacts = locate_matchfacts(data)

    if not isinstance(matchfacts, dict):
        print("matchFacts not found.")
        return

    events = matchfacts.get("events")

    if not isinstance(events, list):
        print("matchFacts.events is not a list.")

        for key, value in matchfacts.items():
            if isinstance(value, list) and value:
                if isinstance(value[0], dict):
                    print(f"Possible event list: {key}")
        return

    print(f"Events count: {len(events)}")
    print()

    periods = {}

    for index, event in enumerate(events):
        if not isinstance(event, dict):
            continue

        period = event.get("period")
        event_type = event.get("type")
        minute = event.get("time")
        shootout = event.get("isPenaltyShootoutEvent")

        periods[str(period)] = periods.get(str(period), 0) + 1

        print(
            f"[{index:02d}] "
            f"period={period!r} | "
            f"type={event_type!r} | "
            f"time={minute!r} | "
            f"isPenaltyShootoutEvent={shootout!r}"
        )

    print()
    print("Period summary:")

    for period, count in periods.items():
        print(f"  {period}: {count}")


def print_penalty_data(data):
    print()
    print("=" * 80)
    print("PENALTY DATA")
    print("=" * 80)

    matchfacts = locate_matchfacts(data)
    content = locate_content(data)

    locations = []

    if isinstance(content, dict):
        locations.append(
            ("content.penalties", content.get("penalties"))
        )

    if isinstance(matchfacts, dict):
        locations.append(
            (
                "matchFacts.penalties",
                matchfacts.get("penalties"),
            )
        )

    for name, value in locations:
        if value is not None:
            print(f"{name}:")
            print(
                json.dumps(
                    value,
                    ensure_ascii=False,
                    indent=2,
                )
            )

    print()
    print("Recursive search inside matchFacts only:")

    if isinstance(matchfacts, dict):
        results = find_all_dicts_with_key(
            matchfacts,
            "penalties",
            "matchFacts",
        )

        if results:
            for path, obj in results:
                print(f"FOUND at: {path}")
                print(
                    json.dumps(
                        obj,
                        ensure_ascii=False,
                        indent=2,
                    )
                )
                print("-" * 80)
        else:
            print("No penalties key found inside matchFacts.")


def print_stats_raw(data):
    print()
    print("=" * 80)
    print("RAW STATS")
    print("=" * 80)

    stats = locate_stats(data)

    if stats is None:
        print("Stats not found.")
        return

    print(f"Stats type: {type(stats).__name__}")

    if isinstance(stats, dict):
        print("Stats keys:")
        for key in stats.keys():
            print(f"  - {key}")

    print()
    print("All stat objects:")
    print()

    results = find_all_dicts_with_key(
        stats,
        "title",
        "content.stats",
    )

    if not results:
        print("No stat objects with title found.")
        return

    for index, (path, obj) in enumerate(results, 1):
        print("-" * 80)
        print(f"STAT #{index}")
        print(f"Path: {path}")
        print(f"Title: {obj.get('title')!r}")

        for key in (
            "stats",
            "period",
            "type",
            "value",
            "values",
            "home",
            "away",
            "name",
        ):
            if key in obj:
                print(f"{key}: {obj[key]!r}")

        print(
            json.dumps(
                obj,
                ensure_ascii=False,
                indent=2,
            )
        )


def main():
    print("=" * 80)
    print("FOTMOB ARGENTINA vs FRANCE 2022 - DIAGNOSTIC TEST")
    print("=" * 80)
    print(f"Match ID: {MATCH_ID}")
    print(f"URL: {MATCH_URL}")

    data = fetch_data()

    if data is None:
        print()
        print("Could not retrieve match data.")
        return

    print_basic_structure(data)
    print_matchfacts_structure(data)
    print_event_periods(data)
    print_penalty_data(data)
    print_stats_raw(data)

    print()
    print("=" * 80)
    print("TEST FINISHED")
    print("=" * 80)


if __name__ == "__main__":
    main()

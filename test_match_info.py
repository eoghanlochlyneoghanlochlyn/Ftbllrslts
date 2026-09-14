import json
import re
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
    """
    فقط برای تست:
    تمام دیکشنری‌هایی را که کلید مشخص دارند پیدا می‌کند
    و مسیرشان را هم چاپ می‌کند.
    """
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


def fetch_api():
    url = f"https://www.fotmob.com/api/matchDetails?matchId={MATCH_ID}"

    print("=" * 80)
    print("FETCHING API")
    print("=" * 80)
    print(url)

    response = requests.get(
        url,
        headers=HEADERS,
        timeout=30,
    )

    print(f"HTTP status: {response.status_code}")
    print(f"Response length: {len(response.text)}")

    if response.status_code != 200:
        print("API did not return HTTP 200.")
        return None

    try:
        data = response.json()
    except Exception as exc:
        print(f"Could not parse JSON: {exc}")
        return None

    print("JSON parsed successfully.")

    return data


def print_basic_structure(data):
    print()
    print("=" * 80)
    print("TOP-LEVEL STRUCTURE")
    print("=" * 80)

    if not isinstance(data, dict):
        print("Root is not a dictionary.")
        return

    print("Top-level keys:")

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
        print("content.matchFacts not found.")
        return

    print("matchFacts keys:")

    for key in matchfacts.keys():
        value = matchfacts[key]

        if isinstance(value, list):
            print(f"  - {key}: list ({len(value)} items)")
        elif isinstance(value, dict):
            print(f"  - {key}: dict")
        else:
            print(f"  - {key}: {type(value).__name__}")


def print_event_periods(data):
    print()
    print("=" * 80)
    print("MATCH EVENT PERIODS")
    print("=" * 80)

    matchfacts = get_nested(
        data,
        "content",
        "matchFacts",
    )

    if not isinstance(matchfacts, dict):
        print("matchFacts not found.")
        return

    events = matchfacts.get("events")

    if not isinstance(events, list):
        print("matchFacts.events is not a list.")
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

        periods.setdefault(str(period), 0)
        periods[str(period)] += 1

        print(
            f"[{index:02d}] "
            f"period={period!r} | "
            f"type={event_type!r} | "
            f"time={minute!r} | "
            f"isPenaltyShootoutEvent={event.get('isPenaltyShootoutEvent')!r}"
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

    # فقط بخش‌های مربوط به match اصلی را بررسی می‌کنیم.
    locations = [
        ("content.penalties", get_nested(data, "content", "penalties")),
        (
            "content.matchFacts.penalties",
            get_nested(
                data,
                "content",
                "matchFacts",
                "penalties",
            ),
        ),
        (
            "content.matchFacts.events.penalties",
            get_nested(
                data,
                "content",
                "matchFacts",
                "events",
                "penalties",
            ),
        ),
    ]

    found = False

    for name, value in locations:
        if value is not None:
            found = True
            print(f"{name}:")
            print(json.dumps(value, ensure_ascii=False, indent=2))

    if not found:
        print("No direct penalties field found in the expected locations.")

    print()
    print("Searching recursively ONLY inside content.matchFacts...")
    print()

    matchfacts = get_nested(
        data,
        "content",
        "matchFacts",
    )

    if isinstance(matchfacts, dict):
        results = find_all_dicts_with_key(
            matchfacts,
            "penalties",
            "content.matchFacts",
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
            print("No 'penalties' key found inside matchFacts.")


def print_stats_raw(data):
    print()
    print("=" * 80)
    print("RAW STATS")
    print("=" * 80)

    stats = get_nested(
        data,
        "content",
        "stats",
    )

    if stats is None:
        print("content.stats not found.")
        return

    print(f"stats type: {type(stats).__name__}")

    if isinstance(stats, dict):
        print("stats keys:")
        for key in stats.keys():
            print(f"  - {key}")

    print()
    print("Searching for stat objects with 'title'...")
    print()

    results = find_all_dicts_with_key(
        stats,
        "title",
        "content.stats",
    )

    if not results:
        print("No objects with 'title' found.")
        return

    for index, (path, obj) in enumerate(results, 1):
        title = obj.get("title")

        print("-" * 80)
        print(f"STAT #{index}")
        print(f"Path: {path}")
        print(f"Title: {title!r}")

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

        # برای اینکه خروجی بیش از حد شلوغ نشود،
        # فقط کل object را برای statهای مهم چاپ می‌کنیم.
        title_normalized = clean_text(title).lower()

        important_titles = {
            "shots",
            "total shots",
            "shots on target",
            "possession",
            "ball possession",
            "expected goals",
            "xg",
            "big chances",
            "accurate passes",
            "passes",
            "total passes",
        }

        if title_normalized in important_titles:
            print()
            print("FULL OBJECT:")
            print(
                json.dumps(
                    obj,
                    ensure_ascii=False,
                    indent=2,
                )
            )


def print_specific_stat_search(data):
    print()
    print("=" * 80)
    print("IMPORTANT STAT SEARCH")
    print("=" * 80)

    stats = get_nested(
        data,
        "content",
        "stats",
    )

    if stats is None:
        print("content.stats not found.")
        return

    wanted = {
        "shots",
        "total shots",
        "shots on target",
        "possession",
        "ball possession",
        "expected goals",
        "xg",
        "big chances",
        "accurate passes",
        "passes",
        "total passes",
    }

    results = find_all_dicts_with_key(
        stats,
        "title",
        "content.stats",
    )

    for path, obj in results:
        title = clean_text(obj.get("title")).lower()

        if title not in wanted:
            continue

        print()
        print(f"TITLE: {obj.get('title')}")
        print(f"PATH: {path}")

        print("period:", repr(obj.get("period")))
        print("stats:", repr(obj.get("stats")))
        print("value:", repr(obj.get("value")))
        print("values:", repr(obj.get("values")))

        print("FULL:")
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

    data = fetch_api()

    if data is None:
        print()
        print("Could not retrieve API data.")
        return

    print_basic_structure(data)
    print_matchfacts_structure(data)
    print_event_periods(data)
    print_penalty_data(data)
    print_stats_raw(data)
    print_specific_stat_search(data)

    print()
    print("=" * 80)
    print("TEST FINISHED")
    print("=" * 80)


if __name__ == "__main__":
    main()

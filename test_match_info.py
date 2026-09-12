import json
import requests


MATCH_ID = "5811755"
MATCH_URL = f"https://www.fotmob.com/match/{MATCH_ID}"


def find_events(obj, path="root"):
    """
    همه بخش‌هایی که کلید events دارند را به صورت بازگشتی پیدا می‌کند.
    """

    results = []

    if isinstance(obj, dict):

        for key, value in obj.items():

            current_path = f"{path}.{key}"

            if key.lower() == "events":
                results.append(
                    (
                        current_path,
                        value,
                    )
                )

            results.extend(
                find_events(
                    value,
                    current_path,
                )
            )

    elif isinstance(obj, list):

        for index, value in enumerate(obj):

            current_path = f"{path}[{index}]"

            results.extend(
                find_events(
                    value,
                    current_path,
                )
            )

    return results


def print_event_details(events, path):

    print()
    print("=" * 80)
    print("EVENTS PATH:")
    print(path)
    print("=" * 80)

    print(
        f"EVENTS TYPE: {type(events).__name__}"
    )

    if isinstance(events, list):

        print(
            f"EVENT COUNT: {len(events)}"
        )

        for index, event in enumerate(events):

            print()
            print("-" * 80)
            print(
                f"EVENT #{index + 1}"
            )
            print("-" * 80)

            print(
                json.dumps(
                    event,
                    ensure_ascii=False,
                    indent=2,
                )
            )

    elif isinstance(events, dict):

        print(
            json.dumps(
                events,
                ensure_ascii=False,
                indent=2,
            )
        )

    else:

        print(events)


def main():

    print()
    print("#" * 70)
    print("FOTMOB → MATCH EVENTS STRUCTURE TEST")
    print("#" * 70)

    print()
    print("MATCH ID:", MATCH_ID)
    print("URL:", MATCH_URL)

    headers = {
        "User-Agent": (
            "Mozilla/5.0 "
            "(Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 "
            "(KHTML, like Gecko) "
            "Chrome/140.0 Safari/537.36"
        ),
        "Accept-Language": "en-US,en;q=0.9",
    }

    print()
    print("=" * 70)
    print("FETCHING FOTMOB MATCH")
    print("=" * 70)

    response = requests.get(
        MATCH_URL,
        headers=headers,
        timeout=30,
    )

    print(
        "HTTP:",
        response.status_code,
    )

    print(
        "HTML:",
        len(response.text),
        "bytes",
    )

    response.raise_for_status()

    html = response.text

    marker = (
        '<script id="__NEXT_DATA__" '
        'type="application/json">'
    )

    start = html.find(marker)

    if start == -1:

        print()
        print(
            "ERROR: __NEXT_DATA__ not found."
        )

        return

    start += len(marker)

    end = html.find(
        "</script>",
        start,
    )

    if end == -1:

        print()
        print(
            "ERROR: __NEXT_DATA__ closing tag not found."
        )

        return

    raw_json = html[start:end]

    try:

        root = json.loads(
            raw_json
        )

    except json.JSONDecodeError as exc:

        print()
        print(
            "ERROR: Could not decode __NEXT_DATA__."
        )

        print(exc)

        return

    print()
    print(
        "NEXT_DATA extracted successfully."
    )

    # ------------------------------------------------------------
    # ذخیره JSON کامل برای بررسی احتمالی بعدی
    # ------------------------------------------------------------

    with open(
        "match_5811755_raw.json",
        "w",
        encoding="utf-8",
    ) as file:

        json.dump(
            root,
            file,
            ensure_ascii=False,
            indent=2,
        )

    print(
        "Raw JSON saved:",
        "match_5811755_raw.json",
    )

    # ------------------------------------------------------------
    # پیدا کردن همه بخش‌های events
    # ------------------------------------------------------------

    print()
    print("=" * 70)
    print("SEARCHING FOR EVENTS")
    print("=" * 70)

    event_sections = find_events(root)

    print()
    print(
        "EVENT SECTIONS FOUND:",
        len(event_sections),
    )

    if not event_sections:

        print()
        print(
            "No key named 'events' was found."
        )

        print()
        print(
            "The complete raw JSON was saved, "
            "so we can inspect alternative structures."
        )

        return

    # ------------------------------------------------------------
    # چاپ رویدادها
    # ------------------------------------------------------------

    for path, events in event_sections:

        print_event_details(
            events,
            path,
        )

    # ------------------------------------------------------------
    # جستجوی چند کلید مهم در کل JSON
    # ------------------------------------------------------------

    interesting_keys = {
        "goals",
        "goal",
        "assist",
        "assists",
        "redCard",
        "redCards",
        "card",
        "cards",
        "ownGoal",
        "ownGoals",
        "playerId",
        "player",
    }

    found_keys = {}

    def search_interesting_keys(
        obj,
        path="root",
    ):

        if isinstance(obj, dict):

            for key, value in obj.items():

                key_lower = str(key).lower()

                if (
                    key_lower in {
                        item.lower()
                        for item in interesting_keys
                    }
                ):

                    if key_lower not in found_keys:

                        found_keys[key_lower] = []

                    found_keys[key_lower].append(
                        (
                            f"{path}.{key}",
                            value,
                        )
                    )

                search_interesting_keys(
                    value,
                    f"{path}.{key}",
                )

        elif isinstance(obj, list):

            for index, value in enumerate(obj):

                search_interesting_keys(
                    value,
                    f"{path}[{index}]",
                )

    search_interesting_keys(root)

    print()
    print("=" * 80)
    print("INTERESTING EVENT-RELATED KEYS FOUND")
    print("=" * 80)

    if not found_keys:

        print(
            "No obvious event-related keys found."
        )

    else:

        for key, matches in found_keys.items():

            print()
            print(
                f"KEY: {key}"
            )

            print(
                f"OCCURRENCES: {len(matches)}"
            )

            for path, value in matches[:20]:

                print()
                print(
                    "PATH:",
                    path,
                )

                print(
                    json.dumps(
                        value,
                        ensure_ascii=False,
                        indent=2,
                    )
                )

                print(
                    "-" * 60
                )

    print()
    print("#" * 70)
    print("TEST FINISHED")
    print("#" * 70)


if __name__ == "__main__":
    main()

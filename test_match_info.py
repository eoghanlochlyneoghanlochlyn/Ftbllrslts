import json
import re
from pprint import pprint

import requests


MATCH_URL = (
    "https://www.fotmob.com/"
    "matches/pfc-lokomotiv-sofia-1929-vs-cherno-more-varna/"
    "3eb7s8#5760493"
)

MATCH_ID = "5760493"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/131.0.0.0 Safari/537.36"
    ),
    "Accept": (
        "text/html,application/xhtml+xml,"
        "application/json"
    ),
    "Accept-Language": "en-US,en;q=0.9",
    "Cache-Control": "no-cache",
    "Pragma": "no-cache",
}


def fetch_match_page():
    print("Fetching FotMob match page...")

    url = MATCH_URL.split("#")[0]

    response = requests.get(
        url,
        headers=HEADERS,
        params={
            "_lineup_test": "1"
        },
        timeout=30,
    )

    print(f"Page status: {response.status_code}")

    response.raise_for_status()

    match = re.search(
        r'<script id="__NEXT_DATA__" '
        r'type="application/json">(.*?)</script>',
        response.text,
        re.DOTALL,
    )

    if not match:
        raise RuntimeError(
            "__NEXT_DATA__ was not found."
        )

    return json.loads(match.group(1))


def fetch_match_details_api():
    print()
    print("Fetching FotMob matchDetails API...")

    url = (
        "https://www.fotmob.com/"
        "api/data/matchDetails"
    )

    response = requests.get(
        url,
        headers={
            **HEADERS,
            "Accept": "application/json",
            "Referer": MATCH_URL.split("#")[0],
        },
        params={
            "matchId": MATCH_ID,
            "_lineup_test": "1",
        },
        timeout=30,
    )

    print(f"API status: {response.status_code}")

    response.raise_for_status()

    return response.json()


def find_lineup_objects(obj, path="root"):
    found = []

    if isinstance(obj, dict):

        # Any object containing one of these keys
        # may be a lineup-related object.
        if (
            "lineupType" in obj
            or "homeTeam" in obj
            or "awayTeam" in obj
        ):
            found.append(
                (path, obj)
            )

        for key, value in obj.items():

            found.extend(
                find_lineup_objects(
                    value,
                    f"{path}.{key}"
                )
            )

    elif isinstance(obj, list):

        for index, value in enumerate(obj):

            found.extend(
                find_lineup_objects(
                    value,
                    f"{path}[{index}]"
                )
            )

    return found


def print_team_details(team, label):

    print()
    print(f"{label}:")
    print("-" * 50)

    if not isinstance(team, dict):
        print("NOT A DICT")
        return

    print(
        "Keys:",
        list(team.keys())
    )

    # Search for possible confirmation fields.
    possible_fields = [
        "confirmed",
        "isConfirmed",
        "lineupConfirmed",
        "confirmedLineup",
        "status",
        "lineupStatus",
        "type",
        "formation",
        "manager",
        "coach",
    ]

    print()
    print("Possible status fields:")

    for field in possible_fields:

        if field in team:

            print(
                f"  {field}:",
                repr(team.get(field))
            )

    starters = team.get("starters")

    print()
    print("Starters:")

    if isinstance(starters, list):

        print(
            f"  Count: {len(starters)}"
        )

        if starters:

            print()
            print(
                "  First starter:"
            )

            pprint(
                starters[0]
            )

            print()
            print(
                "  First starter keys:"
            )

            print(
                list(
                    starters[0].keys()
                )
            )

    else:

        print(
            "  NOT A LIST"
        )


def inspect_lineup(path, lineup):

    print()
    print("=" * 100)
    print("LINEUP OBJECT")
    print("=" * 100)

    print()
    print("Path:")
    print(path)

    print()
    print("Object keys:")
    print(
        list(lineup.keys())
    )

    print()
    print("lineupType:")
    print(
        repr(
            lineup.get(
                "lineupType"
            )
        )
    )

    print()
    print("source:")
    print(
        repr(
            lineup.get(
                "source"
            )
        )
    )

    print_team_details(
        lineup.get("homeTeam"),
        "HOME TEAM"
    )

    print_team_details(
        lineup.get("awayTeam"),
        "AWAY TEAM"
    )

    print()
    print("=" * 100)
    print("FULL LINEUP OBJECT")
    print("=" * 100)

    print(
        json.dumps(
            lineup,
            ensure_ascii=False,
            indent=2
        )
    )


def inspect_source(source_name, data):

    print()
    print("#" * 100)
    print(
        f"SEARCHING {source_name}"
    )
    print("#" * 100)

    objects = find_lineup_objects(
        data
    )

    print()
    print(
        f"Potential lineup objects found: "
        f"{len(objects)}"
    )

    processed = set()

    for path, lineup in objects:

        object_id = id(lineup)

        if object_id in processed:
            continue

        processed.add(object_id)

        inspect_lineup(
            path,
            lineup
        )

    return objects


def main():

    print()
    print("FotMob Lineup Structure Test")
    print("=" * 100)

    print()
    print("Match URL:")
    print(MATCH_URL)

    print()
    print("Match ID:")
    print(MATCH_ID)

    # --------------------------------------------------
    # PAGE
    # --------------------------------------------------

    page_data = fetch_match_page()

    page_objects = inspect_source(
        "__NEXT_DATA__",
        page_data
    )

    # --------------------------------------------------
    # API
    # --------------------------------------------------

    api_data = fetch_match_details_api()

    api_objects = inspect_source(
        "matchDetails API",
        api_data
    )

    # --------------------------------------------------
    # SAVE RAW DATA
    # --------------------------------------------------

    output = {
        "match_url": MATCH_URL,
        "match_id": MATCH_ID,
        "page_data": page_data,
        "api_data": api_data,
        "page_lineup_count": len(
            page_objects
        ),
        "api_lineup_count": len(
            api_objects
        ),
    }

    output_file = (
        "fotmob_lineup_test_output.json"
    )

    with open(
        output_file,
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            output,
            file,
            ensure_ascii=False,
            indent=2
        )

    print()
    print("=" * 100)
    print(
        f"Full raw data saved to: "
        f"{output_file}"
    )
    print("=" * 100)

    print()
    print("TEST COMPLETED.")
    print()
    print(
        "حالا خروجی کامل GitHub Actions "
        "این فایل را بفرست."
    )


if __name__ == "__main__":
    main()

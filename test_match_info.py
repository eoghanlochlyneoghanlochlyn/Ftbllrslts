import json

from fotmob import (
    fetch_match_page,
    extract_next_data,
)


MATCH_ID = "6054373"


def contains_goal_data(value):

    if isinstance(value, dict):

        text = json.dumps(
            value,
            ensure_ascii=False
        ).lower()

        keywords = (
            '"goal"',
            '"isgoal"',
            '"newscore"',
            '"owngoal"',
            '"eventid"',
        )

        return any(
            keyword in text
            for keyword in keywords
        )

    return False


def search_raw(value, path="root", results=None):

    if results is None:
        results = []

    if isinstance(value, dict):

        for key, child in value.items():

            child_path = f"{path}.{key}"

            if isinstance(child, (dict, list)):

                if contains_goal_data(child):

                    results.append(
                        (
                            child_path,
                            child
                        )
                    )

                search_raw(
                    child,
                    child_path,
                    results
                )

    elif isinstance(value, list):

        for index, child in enumerate(value):

            child_path = f"{path}[{index}]"

            if isinstance(child, (dict, list)):

                if contains_goal_data(child):

                    results.append(
                        (
                            child_path,
                            child
                        )
                    )

                search_raw(
                    child,
                    child_path,
                    results
                )

    return results


def print_possible_event_lists(value, path="root"):

    if isinstance(value, dict):

        for key, child in value.items():

            child_path = f"{path}.{key}"

            if isinstance(child, list):

                dict_items = [
                    item
                    for item in child
                    if isinstance(item, dict)
                ]

                if len(dict_items) >= 2:

                    event_like = 0

                    for item in dict_items:

                        keys = set(item.keys())

                        if (
                            "type" in keys
                            or "eventId" in keys
                            or "id" in keys
                            or "time" in keys
                            or "newScore" in keys
                            or "homeScore" in keys
                            or "awayScore" in keys
                        ):
                            event_like += 1

                    if event_like >= 2:

                        print("\n" + "=" * 100)
                        print(
                            f"POSSIBLE EVENT LIST: {child_path}"
                        )
                        print(
                            f"ITEM COUNT: {len(child)}"
                        )
                        print("=" * 100)

                        for index, item in enumerate(
                            child,
                            start=1
                        ):

                            print(
                                f"\n--- ITEM #{index} ---"
                            )

                            print(
                                json.dumps(
                                    item,
                                    ensure_ascii=False,
                                    indent=2
                                )
                            )

            if isinstance(child, (dict, list)):

                print_possible_event_lists(
                    child,
                    child_path
                )

    elif isinstance(value, list):

        for index, child in enumerate(value):

            child_path = f"{path}[{index}]"

            if isinstance(child, (dict, list)):

                print_possible_event_lists(
                    child,
                    child_path
                )


def main():

    print("=" * 100)
    print(
        f"RAW FOTMOB DATA TEST | MATCH ID: {MATCH_ID}"
    )
    print("=" * 100)

    print("\n[1] Fetching FotMob page...")

    page = fetch_match_page(MATCH_ID)

    if not page:

        print(
            "[ERROR] Could not fetch FotMob page."
        )

        return

    print("[OK] FotMob page fetched.")

    print(
        f"Page length: {len(page)}"
    )

    print("\n[2] Extracting NEXT_DATA...")

    data = extract_next_data(page)

    if not isinstance(data, dict):

        print(
            "[ERROR] Could not extract NEXT_DATA."
        )

        return

    print("[OK] NEXT_DATA extracted.")

    print(
        f"Top-level keys: {list(data.keys())}"
    )

    print(
        "\n[3] Searching for possible raw event lists..."
    )

    print_possible_event_lists(data)

    print(
        "\n[4] Searching for goal-related raw structures..."
    )

    results = search_raw(data)

    print(
        f"\nFound {len(results)} goal-related structures."
    )

    for index, (path, value) in enumerate(
        results,
        start=1
    ):

        print("\n" + "#" * 100)
        print(
            f"GOAL-RELATED STRUCTURE #{index}"
        )
        print(
            f"PATH: {path}"
        )
        print("#" * 100)

        try:

            text = json.dumps(
                value,
                ensure_ascii=False,
                indent=2
            )

            # برای جلوگیری از خروجی بسیار عظیم
            if len(text) > 15000:

                print(
                    text[:15000]
                )

                print(
                    f"\n...[TRUNCATED] total size={len(text)} characters..."
                )

            else:

                print(text)

        except Exception as exc:

            print(
                f"[ERROR] Could not print structure: {exc}"
            )

    print("\n" + "=" * 100)
    print("TEST FINISHED")
    print("=" * 100)


if __name__ == "__main__":
    main()

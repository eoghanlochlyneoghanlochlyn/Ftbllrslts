import json

from fotmob import (
    fetch_match_page,
    extract_next_data,
)


MATCH_ID = "6054373"


def search_goal_data(value, path="root", results=None):

    if results is None:
        results = []

    if isinstance(value, dict):

        event_type = value.get("type")

        has_new_score = "newScore" in value
        has_event_id = (
            "eventId" in value
            or "eventID" in value
        )
        has_score = (
            "homeScore" in value
            or "awayScore" in value
        )

        is_goal = (
            isinstance(event_type, str)
            and event_type.lower() == "goal"
        )

        if (
            is_goal
            or has_new_score
            or (
                has_event_id
                and has_score
            )
        ):

            results.append(
                (
                    path,
                    value
                )
            )

        for key, child in value.items():

            child_path = f"{path}.{key}"

            if isinstance(child, (dict, list)):

                search_goal_data(
                    child,
                    child_path,
                    results
                )

    elif isinstance(value, list):

        for index, child in enumerate(value):

            child_path = f"{path}[{index}]"

            if isinstance(child, (dict, list)):

                search_goal_data(
                    child,
                    child_path,
                    results
                )

    return results


def print_compact_event(path, value):

    print("\n" + "-" * 100)
    print(f"PATH: {path}")
    print("-" * 100)

    fields = (
        "id",
        "eventId",
        "eventID",
        "incidentId",
        "incidentID",
        "type",
        "time",
        "minute",
        "minutesAdded",
        "minutesAddedInput",
        "timeStr",
        "halfStrShort",
        "isHome",
        "playerId",
        "assistPlayerId",
        "homeScore",
        "awayScore",
        "newScore",
        "isGoal",
        "ownGoal",
        "reactKey",
    )

    for field in fields:

        if field in value:

            print(
                f"{field}: "
                f"{json.dumps(value[field], ensure_ascii=False)}"
            )

    player = value.get("player")

    if isinstance(player, dict):

        print(
            "player:",
            json.dumps(
                {
                    "id": player.get("id"),
                    "name": player.get("name"),
                },
                ensure_ascii=False
            )
        )

    else:

        player_name = value.get("playerName")

        if player_name is not None:

            print(
                f"playerName: {player_name}"
            )


def main():

    print("=" * 100)
    print(
        f"GOAL LOCATION TEST | MATCH ID: {MATCH_ID}"
    )
    print("=" * 100)

    print("\n[1] Fetching FotMob page...")

    page = fetch_match_page(MATCH_ID)

    if not page:

        print(
            "[ERROR] Could not fetch FotMob page."
        )

        return

    print(
        f"[OK] Page fetched | length={len(page)}"
    )

    print("\n[2] Extracting NEXT_DATA...")

    data = extract_next_data(page)

    if not isinstance(data, dict):

        print(
            "[ERROR] Could not extract NEXT_DATA."
        )

        return

    print("[OK] NEXT_DATA extracted.")

    print("\n[3] Searching for goal/score structures...")

    results = search_goal_data(data)

    print(
        f"[OK] Found {len(results)} matching structures."
    )

    for index, (path, value) in enumerate(
        results,
        start=1
    ):

        print("\n" + "=" * 100)
        print(
            f"RESULT #{index}"
        )
        print("=" * 100)

        print_compact_event(
            path,
            value
        )

    print("\n" + "=" * 100)
    print("TEST FINISHED")
    print("=" * 100)


if __name__ == "__main__":
    main()

import json

from fotmob import (
    fetch_match_page,
    extract_next_data,
    extract_events_from_data,
)


MATCH_ID = "6054373"


def get_event_unique_id(event):

    if not isinstance(event, dict):
        return None

    for key in (
        "id",
        "eventId",
        "eventID",
        "incidentId",
        "incidentID",
    ):

        value = event.get(key)

        if value is None:
            continue

        if isinstance(value, bool):
            continue

        if str(value).strip() == "0":
            continue

        return value

    return None


def dedupe_events(events):

    result = []
    seen = set()

    for event in events:

        if not isinstance(event, dict):
            continue

        react_key = event.get("reactKey")

        if (
            react_key is not None
            and str(react_key).strip()
        ):

            key = (
                "reactKey",
                str(react_key),
            )

        else:

            event_id = get_event_unique_id(
                event
            )

            if (
                event_id is not None
                and str(event_id).strip() != "0"
            ):

                key = (
                    "id",
                    str(event_id),
                )

            else:

                key = (
                    "fallback",
                    str(event.get("type", "")),
                    str(event.get("playerId", "")),
                    str(event.get("time", "")),
                    str(event.get("minute", "")),
                    str(event.get("isHome", "")),
                )

        if key in seen:
            continue

        seen.add(key)
        result.append(event)

    return result


def is_goal(event):

    if not isinstance(event, dict):
        return False

    event_type = event.get("type")

    if isinstance(event_type, str):

        if "goal" in event_type.lower():
            return True

    if event.get("isGoal") is True:
        return True

    return False


def get_player_name(event):

    player = event.get("player")

    if isinstance(player, dict):

        name = player.get("name")

        if name:
            return name

    return (
        event.get("playerName")
        or event.get("name")
        or "Unknown"
    )


def get_goal_minute(event):

    time_str = event.get("timeStr")

    if time_str is not None:
        return str(time_str)

    time_value = event.get("time")

    if time_value is not None:
        return str(time_value)

    return "?"


def print_event(index, event):

    print(
        f"\n#{index}"
    )

    print(
        f"  type: {event.get('type')}"
    )

    print(
        f"  minute: {get_goal_minute(event)}"
    )

    print(
        f"  player: {get_player_name(event)}"
    )

    print(
        f"  reactKey: {event.get('reactKey')}"
    )

    print(
        f"  id: {event.get('id')}"
    )

    print(
        f"  eventId: {event.get('eventId')}"
    )

    print(
        f"  isHome: {event.get('isHome')}"
    )

    print(
        f"  homeScore: {event.get('homeScore')}"
    )

    print(
        f"  awayScore: {event.get('awayScore')}"
    )

    print(
        f"  newScore: {event.get('newScore')}"
    )


def main():

    print("=" * 100)
    print(
        f"DEDUPE TEST | MATCH ID: {MATCH_ID}"
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

    print(
        "[OK] NEXT_DATA extracted."
    )

    print("\n[3] Extracting events...")

    events = extract_events_from_data(data)

    if not isinstance(events, list):

        print(
            "[ERROR] extract_events_from_data() "
            "did not return a list."
        )

        return

    print(
        f"[OK] Extracted events: {len(events)}"
    )

    print("\n[4] Running reactKey-based deduplication...")

    deduped_events = dedupe_events(events)

    print(
        f"[OK] Events after dedupe: "
        f"{len(deduped_events)}"
    )

    print("\n" + "=" * 100)
    print("ALL EVENTS AFTER DEDUPE")
    print("=" * 100)

    for index, event in enumerate(
        deduped_events,
        start=1
    ):

        print_event(
            index,
            event
        )

    goals = [
        event
        for event in deduped_events
        if is_goal(event)
    ]

    print("\n" + "=" * 100)
    print(
        f"GOALS AFTER DEDUPE: {len(goals)}"
    )
    print("=" * 100)

    for index, goal in enumerate(
        goals,
        start=1
    ):

        print_event(
            index,
            goal
        )

    print("\n" + "=" * 100)
    print("EXPECTED GOALS")
    print("=" * 100)

    expected_goals = [
        ("5", "Taha Yassine Khenissi"),
        ("8", "Oumar Gonzalez"),
        ("23", "Moussa Diarra"),
        ("87", "Renné Rivas"),
        ("90 + 7", "Christian Benteke"),
    ]

    for index, (minute, player) in enumerate(
        expected_goals,
        start=1
    ):

        print(
            f"{index}. {minute}' - {player}"
        )

    print("\n" + "=" * 100)
    print("GOAL COUNT CHECK")
    print("=" * 100)

    if len(goals) == 5:

        print(
            "[PASS] All 5 goals are present."
        )

    else:

        print(
            "[FAIL] Expected 5 goals, "
            f"but found {len(goals)}."
        )

    print("\n" + "=" * 100)
    print("TEST FINISHED")
    print("=" * 100)


if __name__ == "__main__":
    main()

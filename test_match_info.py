import json

import fotmob


MATCH_ID = "6054373"


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

        return player.get(
            "name",
            "Unknown"
        )

    return (
        event.get("playerName")
        or event.get("name")
        or "Unknown"
    )


def get_minute(event):

    if event.get("timeStr") is not None:

        return str(
            event.get("timeStr")
        )

    if event.get("time") is not None:

        return str(
            event.get("time")
        )

    if event.get("minute") is not None:

        return str(
            event.get("minute")
        )

    return "?"


def print_goal(index, event):

    print(
        f"  {index}. "
        f"{get_minute(event)}' - "
        f"{get_player_name(event)}"
    )

    print(
        f"     type={event.get('type')} "
        f"eventId={event.get('eventId')} "
        f"id={event.get('id')} "
        f"reactKey={event.get('reactKey')}"
    )

    print(
        f"     score="
        f"{event.get('homeScore')}-"
        f"{event.get('awayScore')} "
        f"newScore={event.get('newScore')}"
    )


def collect_goal_candidates(
    value,
    path="root",
    results=None,
    seen_objects=None,
):

    if results is None:
        results = []

    if seen_objects is None:
        seen_objects = set()

    if isinstance(value, dict):

        object_id = id(value)

        if object_id in seen_objects:
            return results

        seen_objects.add(object_id)

        if is_goal(value):

            results.append(
                (
                    path,
                    value
                )
            )

        for key, child in value.items():

            child_path = (
                f"{path}.{key}"
            )

            if isinstance(
                child,
                (dict, list)
            ):

                collect_goal_candidates(
                    child,
                    child_path,
                    results,
                    seen_objects,
                )

    elif isinstance(value, list):

        object_id = id(value)

        if object_id in seen_objects:
            return results

        seen_objects.add(object_id)

        for index, child in enumerate(
            value
        ):

            child_path = (
                f"{path}[{index}]"
            )

            if isinstance(
                child,
                (dict, list)
            ):

                collect_goal_candidates(
                    child,
                    child_path,
                    results,
                    seen_objects,
                )

    return results


def dedupe_by_react_key(events):

    result = []
    seen = set()

    for event in events:

        if not isinstance(event, dict):
            continue

        react_key = event.get(
            "reactKey"
        )

        if (
            react_key is not None
            and str(react_key).strip()
        ):

            key = (
                "reactKey",
                str(react_key),
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


def main():

    print("=" * 100)
    print(
        f"EVENT PIPELINE TEST | MATCH ID: {MATCH_ID}"
    )
    print("=" * 100)

    # ------------------------------------------------------------------
    # STEP 1
    # ------------------------------------------------------------------

    print("\n[1] Fetching FotMob page...")

    page = fotmob.fetch_match_page(
        MATCH_ID
    )

    if not page:

        print(
            "[ERROR] Could not fetch FotMob page."
        )

        return

    print(
        f"[OK] Page fetched | length={len(page)}"
    )

    # ------------------------------------------------------------------
    # STEP 2
    # ------------------------------------------------------------------

    print("\n[2] Extracting NEXT_DATA...")

    data = fotmob.extract_next_data(
        page
    )

    if not isinstance(data, dict):

        print(
            "[ERROR] Could not extract NEXT_DATA."
        )

        return

    print(
        "[OK] NEXT_DATA extracted."
    )

    # ------------------------------------------------------------------
    # STEP 3
    # ------------------------------------------------------------------

    print(
        "\n[3] Searching entire NEXT_DATA "
        "for raw goal dictionaries..."
    )

    raw_goal_results = collect_goal_candidates(
        data
    )

    print(
        f"[OK] Raw goal dictionaries found: "
        f"{len(raw_goal_results)}"
    )

    print(
        "\nRAW GOALS:"
    )

    for index, (
        path,
        event
    ) in enumerate(
        raw_goal_results,
        start=1
    ):

        print(
            f"\nRAW RESULT #{index}"
        )

        print(
            f"  PATH: {path}"
        )

        print_goal(
            index,
            event
        )

    # ------------------------------------------------------------------
    # STEP 4
    # ------------------------------------------------------------------

    print(
        "\n" + "=" * 100
    )

    print(
        "[4] Calling extract_events_from_data()"
    )

    print(
        "=" * 100
    )

    extracted_events = (
        fotmob.extract_events_from_data(
            data
        )
    )

    if not isinstance(
        extracted_events,
        list
    ):

        print(
            "[ERROR] "
            "extract_events_from_data() "
            "did not return a list."
        )

        return

    print(
        f"[OK] Extracted events: "
        f"{len(extracted_events)}"
    )

    extracted_goals = [
        event
        for event in extracted_events
        if is_goal(event)
    ]

    print(
        f"[INFO] Goals returned by "
        f"extract_events_from_data(): "
        f"{len(extracted_goals)}"
    )

    print(
        "\nEXTRACTED GOALS:"
    )

    for index, event in enumerate(
        extracted_goals,
        start=1
    ):

        print_goal(
            index,
            event
        )

    # ------------------------------------------------------------------
    # STEP 5
    # ------------------------------------------------------------------

    print(
        "\n" + "=" * 100
    )

    print(
        "[5] Testing reactKey-based deduplication"
    )

    print(
        "=" * 100
    )

    deduped_events = dedupe_by_react_key(
        extracted_events
    )

    deduped_goals = [
        event
        for event in deduped_events
        if is_goal(event)
    ]

    print(
        f"[INFO] Events before dedupe: "
        f"{len(extracted_events)}"
    )

    print(
        f"[INFO] Events after dedupe: "
        f"{len(deduped_events)}"
    )

    print(
        f"[INFO] Goals before dedupe: "
        f"{len(extracted_goals)}"
    )

    print(
        f"[INFO] Goals after dedupe: "
        f"{len(deduped_goals)}"
    )

    print(
        "\nDEDUPED GOALS:"
    )

    for index, event in enumerate(
        deduped_goals,
        start=1
    ):

        print_goal(
            index,
            event
        )

    # ------------------------------------------------------------------
    # STEP 6
    # ------------------------------------------------------------------

    print(
        "\n" + "=" * 100
    )

    print(
        "[6] FINAL DIAGNOSIS"
    )

    print(
        "=" * 100
    )

    raw_goal_count = len(
        raw_goal_results
    )

    extracted_goal_count = len(
        extracted_goals
    )

    deduped_goal_count = len(
        deduped_goals
    )

    print(
        f"\nRaw NEXT_DATA goals: "
        f"{raw_goal_count}"
    )

    print(
        f"extract_events_from_data goals: "
        f"{extracted_goal_count}"
    )

    print(
        f"reactKey dedupe goals: "
        f"{deduped_goal_count}"
    )

    if raw_goal_count >= 5:

        if extracted_goal_count < raw_goal_count:

            print(
                "\n[DIAGNOSIS] "
                "The missing goals disappear "
                "inside extract_events_from_data()."
            )

            print(
                "The problem is BEFORE "
                "the final dedupe step."
            )

        elif deduped_goal_count < extracted_goal_count:

            print(
                "\n[DIAGNOSIS] "
                "The missing goals disappear "
                "during deduplication."
            )

            print(
                "The problem is in the dedupe logic."
            )

        else:

            print(
                "\n[DIAGNOSIS] "
                "All raw goals survived "
                "the extraction pipeline."
            )

    else:

        print(
            "\n[WARNING] "
            "Fewer than 5 raw goals were found."
        )

        print(
            "The FotMob page structure may have "
            "changed or the test data may differ."
        )

    print(
        "\n" + "=" * 100
    )

    print(
        "TEST FINISHED"
    )

    print(
        "=" * 100
    )


if __name__ == "__main__":
    main()

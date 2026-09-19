from fotmob import (
    fetch_match_api,
    fetch_match_page,
    extract_next_data,
    extract_events_from_data,
)


MATCH_ID = "6054373"


def get_raw_events():
    print("=" * 80)
    print(f"RAW EVENTS TEST | MATCH ID: {MATCH_ID}")
    print("=" * 80)

    print("\n[1] Trying FotMob API...")

    data = fetch_match_api(MATCH_ID)

    if isinstance(data, dict):
        print("[OK] API returned data.")

        events = extract_events_from_data(data)

        if events:
            print(
                f"[OK] Extracted {len(events)} events from API data."
            )
            return events

        print(
            "[INFO] API data returned, but no events found."
        )

    else:
        print("[INFO] API did not return usable data.")

    print("\n[2] Trying FotMob page...")

    page = fetch_match_page(MATCH_ID)

    if not page:
        print("[ERROR] Could not fetch FotMob page.")
        return []

    print("[OK] FotMob page fetched.")

    next_data = extract_next_data(page)

    if not isinstance(next_data, dict):
        print("[ERROR] Could not extract NEXT_DATA.")
        return []

    print("[OK] NEXT_DATA extracted.")

    events = extract_events_from_data(next_data)

    print(
        f"[OK] Extracted {len(events)} events from page data."
    )

    return events


def show_event(event, index):
    print("\n" + "-" * 80)
    print(f"EVENT #{index}")
    print("-" * 80)

    if not isinstance(event, dict):
        print("Event is not a dictionary:")
        print(repr(event))
        return

    important_keys = [
        "id",
        "eventId",
        "eventID",
        "incidentId",
        "incidentID",
        "type",
        "eventType",
        "incidentType",
        "playerId",
        "playerName",
        "name",
        "time",
        "minute",
        "isHome",
        "homeScore",
        "awayScore",
        "newScore",
        "assistPlayerId",
        "isGoal",
        "card",
        "cardType",
        "period",
        "periodName",
        "periodType",
        "matchPeriod",
        "stage",
        "stageName",
    ]

    print("IMPORTANT FIELDS:")

    for key in important_keys:

        if key in event:
            print(
                f"  {key}: {repr(event.get(key))}"
            )

    print("\nALL RAW FIELDS:")

    for key, value in event.items():
        print(
            f"  {key}: {repr(value)}"
        )


def main():

    events = get_raw_events()

    print("\n" + "=" * 80)
    print(f"TOTAL EVENTS: {len(events)}")
    print("=" * 80)

    if not events:
        print("No events found.")
        return

    for index, event in enumerate(events, start=1):
        show_event(event, index)

    print("\n" + "=" * 80)
    print("TEST FINISHED")
    print("=" * 80)


if __name__ == "__main__":
    main()

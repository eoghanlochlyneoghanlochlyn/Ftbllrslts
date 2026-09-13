from datetime import datetime, timedelta, timezone

from event_detector import (
    detect_state_changes,
    get_player_events,
)
from formatter import (
    build_event_message,
    build_lineup_message,
)
from fotmob import (
    fetch_match_data,
    get_match_snapshot,
)
from match_manager import get_enabled_matches
from state_manager import (
    get_match_state,
    load_state,
    save_state,
    update_match_state,
)
from telegram_sender import send_long_message


FALLBACK_MINUTES = 30


def is_lineup_confirmed(snapshot):
    lineup_type = str(
        snapshot.get(
            "lineup_type",
            "",
        )
    ).lower()

    home_starters = snapshot.get(
        "home_starters",
        [],
    )

    away_starters = snapshot.get(
        "away_starters",
        [],
    )

    confirmed_type = lineup_type in (
        "confirmed",
        "standard",
    )

    return (
        confirmed_type
        and len(home_starters) >= 11
        and len(away_starters) >= 11
    )


def parse_start_time(value):
    if not value:
        return None

    try:

        value = str(value)

        if value.endswith("Z"):
            value = value[:-1] + "+00:00"

        dt = datetime.fromisoformat(value)

        if dt.tzinfo is None:
            dt = dt.replace(
                tzinfo=timezone.utc
            )

        return dt

    except Exception:
        return None


def fallback_time_reached(snapshot):
    start = parse_start_time(
        snapshot.get("start")
    )

    if start is None:
        return False

    now = datetime.now(timezone.utc)

    return now >= (
        start - timedelta(
            minutes=FALLBACK_MINUTES
        )
    )


def send_lineup_if_needed(
    match_id,
    snapshot,
    match_state,
):
    if match_state.get("lineup_sent"):
        return False

    confirmed = is_lineup_confirmed(
        snapshot
    )

    fallback = fallback_time_reached(
        snapshot
    )

    if not confirmed and not fallback:
        return False

    print(
        f"[{match_id}] Sending lineup message."
    )

    message = build_lineup_message(
        snapshot,
        player_events={},
        show_rating=False,
    )

    send_long_message(message)

    match_state["lineup_sent"] = True

    if not confirmed:
        match_state["fallback_sent"] = True

    return True


def process_live_events(
    match_id,
    root,
    snapshot,
    match_state,
):
    changes = detect_state_changes(
        match_state,
        root,
        snapshot,
    )

    new_events = changes.get(
        "new_events",
        [],
    )

    if not new_events:
        return

    for event in new_events:

        message = build_event_message(
            snapshot,
            event,
        )

        if not message:
            continue

        print(
            f"[{match_id}] New event detected."
        )

        send_long_message(message)


def process_match(
    match,
    state,
):
    match_id = str(
        match.get("id")
    )

    if not match_id:
        return

    print("")
    print("=" * 70)
    print(
        f"PROCESSING MATCH {match_id}"
    )
    print("=" * 70)

    try:

        root = fetch_match_data(
            match_id
        )

        snapshot = get_match_snapshot(
            root
        )

        print(
            f"{snapshot.get('home')} "
            f"vs "
            f"{snapshot.get('away')}"
        )

        print(
            "Lineup type:",
            snapshot.get("lineup_type"),
        )

        print(
            "Starters:",
            len(snapshot.get("home_starters", [])),
            "/",
            len(snapshot.get("away_starters", [])),
        )

        match_state = get_match_state(
            state,
            match_id,
        )

        # ------------------------------------------------
        # ترکیب
        # ------------------------------------------------

        send_lineup_if_needed(
            match_id,
            snapshot,
            match_state,
        )

        # ------------------------------------------------
        # رویدادهای جدید
        # ------------------------------------------------

        if match_state.get("lineup_sent"):

            process_live_events(
                match_id,
                root,
                snapshot,
                match_state,
            )

        # ------------------------------------------------
        # پایان بازی
        # ------------------------------------------------

        finished = snapshot.get(
            "finished",
            False,
        )

        if finished:

            if not match_state.get(
                "finished_sent"
            ):

                player_events = (
                    get_player_events(root)
                )

                final_message = build_lineup_message(
                    snapshot,
                    player_events=player_events,
                    show_rating=True,
                )

                send_long_message(
                    final_message
                )

                match_state[
                    "finished_sent"
                ] = True

        # ------------------------------------------------
        # ذخیره وضعیت رویدادها
        # ------------------------------------------------

        from event_detector import get_event_keys

        match_state[
            "event_keys"
        ] = get_event_keys(
            snapshot.get(
                "events",
                [],
            )
        )

        match_state[
            "finished"
        ] = finished

        update_match_state(
            state,
            match_id,
            **match_state,
        )

    except Exception as error:

        print(
            f"[{match_id}] ERROR: "
            f"{type(error).__name__}: {error}"
        )


def main():
    print("")
    print("#" * 70)
    print("FOOTBALL ALERTS")
    print("#" * 70)

    matches = get_enabled_matches()

    if not matches:

        print(
            "No enabled matches."
        )

        return

    state = load_state()

    for match in matches:

        process_match(
            match,
            state,
        )

    save_state(state)

    print("")
    print(
        "State saved successfully."
    )


if __name__ == "__main__":
    main()

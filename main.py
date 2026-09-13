from datetime import datetime, timedelta, timezone

from event_detector import (
    detect_state_changes,
    get_event_keys,
    get_player_events,
)
from formatter import (
    build_event_message,
    build_lineup_message,
    build_goal_message,
    build_cancelled_goal_message,
    build_half_time_message,
    build_start_message,
    build_red_card_message,
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
    get_current_score,
    sync_goals_with_current_events,
)
from telegram_sender import send_long_message


FALLBACK_MINUTES = 30


# ============================================================
# ترکیب
# ============================================================

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

    if message:
        send_long_message(
            message
        )

    match_state["lineup_sent"] = True

    if not confirmed:
        match_state["fallback_sent"] = True

    return True


# ============================================================
# ابزارهای داخلی گل
# ============================================================

def get_saved_goal_key(goal):
    if not isinstance(
        goal,
        dict,
    ):
        return None

    value = goal.get(
        "event_key"
    )

    if value is None:
        value = goal.get(
            "key"
        )

    if value is None:
        value = goal.get(
            "id"
        )

    if value is None:
        return None

    return str(value)


def get_cancelled_goal_key(cancelled_goal):
    if not isinstance(
        cancelled_goal,
        dict,
    ):
        return None

    value = cancelled_goal.get(
        "goal_key"
    )

    if value is None:
        value = cancelled_goal.get(
            "event_key"
        )

    if value is None:
        value = cancelled_goal.get(
            "key"
        )

    if value is None:
        value = cancelled_goal.get(
            "id"
        )

    if value is None:
        return None

    return str(value)


# ============================================================
# Live events
# ============================================================

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

    # --------------------------------------------------------
    # وضعیت فعلی بازی
    # --------------------------------------------------------

    current_started = changes.get(
        "current_started",
        False,
    )

    current_half_time = changes.get(
        "current_half_time",
        False,
    )

    current_finished = changes.get(
        "current_finished",
        False,
    )

    # --------------------------------------------------------
    # شروع بازی
    # --------------------------------------------------------

    if (
        changes.get(
            "started",
            False,
        )
        and not match_state.get(
            "started",
            False,
        )
    ):
        message = build_start_message(
            snapshot
        )

        if message:
            print(
                f"[{match_id}] Match started."
            )

            send_long_message(
                message
            )

        match_state["started"] = True

    # --------------------------------------------------------
    # گل‌های جدید
    # --------------------------------------------------------

    new_goal_info = changes.get(
        "new_goal_info",
        [],
    )

    # کلید گل‌هایی که قبل از این poll
    # در state وجود داشتند.
    previous_goal_keys = {
        get_saved_goal_key(goal)
        for goal in match_state.get(
            "goals",
            [],
        )
        if get_saved_goal_key(goal)
        is not None
    }

    # --------------------------------------------------------
    # VAR
    # --------------------------------------------------------

    cancelled_goals = changes.get(
        "cancelled_goals",
        [],
    )

    cancelled_goal_keys = []

    for cancelled_goal in cancelled_goals:

        goal_key = get_cancelled_goal_key(
            cancelled_goal
        )

        if goal_key is not None:
            cancelled_goal_keys.append(
                goal_key
            )

    # --------------------------------------------------------
    # ذخیره گل‌ها و اعمال VAR روی state
    # --------------------------------------------------------

    sync_goals_with_current_events(
        match_state,
        new_goal_info,
        cancelled_goal_keys,
    )

    # --------------------------------------------------------
    # نتیجه فعلی
    # --------------------------------------------------------

    score = get_current_score(
        match_state
    )

    # --------------------------------------------------------
    # ارسال گل‌های جدید
    # --------------------------------------------------------

    for goal_info in new_goal_info:

        if not isinstance(
            goal_info,
            dict,
        ):
            continue

        goal_key = goal_info.get(
            "event_key"
        )

        if goal_key is not None:
            goal_key = str(
                goal_key
            )

        # اگر گل قبل از این اجرا در state بوده،
        # دوباره ارسال نشود.
        if (
            goal_key is not None
            and goal_key in previous_goal_keys
        ):
            continue

        # اگر همین گل در همین poll بلافاصله
        # توسط VAR مردود شده، پیام گل معمولی نفرست.
        if (
            goal_key is not None
            and goal_key in cancelled_goal_keys
        ):
            continue

        event = goal_info.get(
            "event"
        )

        if not isinstance(
            event,
            dict,
        ):
            event = {}

        message = build_goal_message(
            snapshot,
            event,
            score=score,
        )

        if not message:
            continue

        print(
            f"[{match_id}] New goal detected."
        )

        send_long_message(
            message
        )

    # --------------------------------------------------------
    # گل‌های مردودشده توسط VAR
    # --------------------------------------------------------

    for cancelled_goal in cancelled_goals:

        if not isinstance(
            cancelled_goal,
            dict,
        ):
            continue

        goal_key = get_cancelled_goal_key(
            cancelled_goal
        )

        if goal_key is None:
            continue

        # پیدا کردن گل ذخیره‌شده
        saved_goal = None

        for goal in match_state.get(
            "goals",
            [],
        ):

            if (
                get_saved_goal_key(goal)
                == goal_key
            ):
                saved_goal = goal
                break

        original_event = (
            cancelled_goal.get(
                "goal_event"
            )
        )

        if not isinstance(
            original_event,
            dict,
        ):
            original_event = {}

        minute = cancelled_goal.get(
            "minute"
        )

        if minute is None and saved_goal:
            minute = saved_goal.get(
                "minute"
            )

        is_home = cancelled_goal.get(
            "is_home"
        )

        if is_home is None and saved_goal:
            is_home = saved_goal.get(
                "is_home"
            )

        cancellation_data = {
            "goal_event": original_event,
            "minute": minute,
            "is_home": is_home,
        }

        score = get_current_score(
            match_state
        )

        message = build_cancelled_goal_message(
            snapshot,
            cancellation_data,
            score=score,
        )

        if not message:
            continue

        print(
            f"[{match_id}] Goal cancelled by VAR."
        )

        send_long_message(
            message
        )

    # --------------------------------------------------------
    # نیمه اول
    # --------------------------------------------------------

    if (
        changes.get(
            "half_time",
            False,
        )
        and not match_state.get(
            "half_time",
            False,
        )
    ):
        message = build_half_time_message(
            snapshot
        )

        if message:
            print(
                f"[{match_id}] Half time."
            )

            send_long_message(
                message
            )

        match_state["half_time"] = True

    # --------------------------------------------------------
    # کارت قرمز
    # --------------------------------------------------------

    new_red_cards = changes.get(
        "new_red_cards",
        [],
    )

    red_card_keys = set()

    for event in new_red_cards:

        if not isinstance(
            event,
            dict,
        ):
            continue

        message = build_red_card_message(
            snapshot,
            event,
        )

        if message:
            print(
                f"[{match_id}] Red card detected."
            )

            send_long_message(
                message
            )

        key = (
            event.get("key")
            or event.get("event_key")
            or event.get("id")
            or event.get("eventId")
        )

        if key is not None:
            red_card_keys.add(
                str(key)
            )

    # --------------------------------------------------------
    # سایر eventهای جدید
    # --------------------------------------------------------

    new_events = changes.get(
        "new_events",
        [],
    )

    handled_goal_keys = {
        str(
            goal_info.get(
                "event_key"
            )
        )
        for goal_info in new_goal_info
        if (
            isinstance(
                goal_info,
                dict,
            )
            and goal_info.get(
                "event_key"
            ) is not None
        )
    }

    handled_var_goal_keys = {
        str(key)
        for key in cancelled_goal_keys
    }

    for event in new_events:

        if not isinstance(
            event,
            dict,
        ):
            continue

        event_key = (
            event.get("key")
            or event.get("event_key")
            or event.get("id")
            or event.get("eventId")
        )

        if event_key is not None:
            event_key = str(
                event_key
            )

        # گل قبلاً جداگانه ارسال شده.
        if (
            event_key is not None
            and event_key in handled_goal_keys
        ):
            continue

        # VAR مربوط به لغو گل قبلاً جداگانه ارسال شده.
        if (
            event_key is not None
            and event_key in handled_var_goal_keys
        ):
            continue

        # کارت قرمز قبلاً جداگانه ارسال شده.
        if (
            event_key is not None
            and event_key in red_card_keys
        ):
            continue

        message = build_event_message(
            snapshot,
            event,
        )

        if not message:
            continue

        print(
            f"[{match_id}] New event detected."
        )

        send_long_message(
            message
        )

    # --------------------------------------------------------
    # به‌روزرسانی وضعیت بازی
    # --------------------------------------------------------

    if current_started:
        match_state["started"] = True

    if current_half_time:
        match_state["half_time"] = True

    if current_finished:
        match_state["finished"] = True

    return changes


# ============================================================
# پردازش مسابقه
# ============================================================

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
            snapshot.get(
                "lineup_type"
            ),
        )

        print(
            "Starters:",
            len(
                snapshot.get(
                    "home_starters",
                    [],
                )
            ),
            "/",
            len(
                snapshot.get(
                    "away_starters",
                    [],
                )
            ),
        )

        print(
            "Started:",
            snapshot.get(
                "started",
                False,
            ),
        )

        print(
            "Half time:",
            snapshot.get(
                "half_time",
                False,
            ),
        )

        print(
            "Finished:",
            snapshot.get(
                "finished",
                False,
            ),
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
        # رویدادهای زنده
        # ------------------------------------------------

        if match_state.get(
            "lineup_sent"
        ):
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
                "finished_sent",
                False,
            ):

                player_events = (
                    get_player_events(
                        root
                    )
                )

                final_message = (
                    build_lineup_message(
                        snapshot,
                        player_events=player_events,
                        show_rating=True,
                    )
                )

                if final_message:
                    send_long_message(
                        final_message
                    )

                print(
                    f"[{match_id}] Final message sent."
                )

                match_state[
                    "finished_sent"
                ] = True

        # ------------------------------------------------
        # ذخیره کلید eventهای فعلی
        # ------------------------------------------------

        current_event_keys = (
            get_event_keys(
                snapshot.get(
                    "events",
                    [],
                )
            )
        )

        match_state[
            "event_keys"
        ] = current_event_keys

        match_state[
            "finished"
        ] = finished

        update_match_state(
            state,
            match_id,
            **match_state,
        )

        # ------------------------------------------------
        # نمایش نتیجه فعلی در لاگ
        # ------------------------------------------------

        score = get_current_score(
            match_state
        )

        print(
            f"[{match_id}] Current score: "
            f"{score.get('home', 0)} - "
            f"{score.get('away', 0)}"
        )

    except Exception as error:

        print(
            f"[{match_id}] ERROR: "
            f"{type(error).__name__}: {error}"
        )


# ============================================================
# Main
# ============================================================

def main():
    print("")
    print("#" * 70)
    print("FOOTBALL ALERTS")
    print("#" * 70)

    matches = get_enabled_matches()

    print(
        f"Enabled matches: {len(matches)}"
    )

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

    save_state(
        state
    )

    print("")
    print(
        "State saved successfully."
    )


if __name__ == "__main__":
    main()

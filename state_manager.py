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
    # شروع بازی
    # --------------------------------------------------------

    if (
        changes.get("started", False)
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

    # --------------------------------------------------------
    # گل‌های مردودشده
    #
    # event_detector ممکن است اطلاعات مختلفی برگرداند.
    # state_manager فقط کلید گل مردود را لازم دارد.
    # --------------------------------------------------------

    cancelled_goals = changes.get(
        "cancelled_goals",
        [],
    )

    cancelled_goal_keys = []

    for cancelled_goal in cancelled_goals:

        if not isinstance(
            cancelled_goal,
            dict,
        ):
            continue

        key = (
            cancelled_goal.get(
                "key"
            )
            or cancelled_goal.get(
                "event_key"
            )
            or cancelled_goal.get(
                "id"
            )
        )

        if key is not None:
            cancelled_goal_keys.append(
                str(key)
            )

    # --------------------------------------------------------
    # هماهنگ کردن گل‌ها با state
    # --------------------------------------------------------

    previous_cancelled_keys = {
        str(
            goal.get(
                "event_key"
            )
        )
        for goal in match_state.get(
            "goals",
            [],
        )
        if (
            isinstance(
                goal,
                dict,
            )
            and goal.get(
                "cancelled",
                False,
            )
        )
    }

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
    #
    # فقط گل‌هایی که در همین اجرای برنامه جدیداً
    # وارد state شده‌اند باید ارسال شوند.
    # --------------------------------------------------------

    for goal_info in new_goal_info:

        if not isinstance(
            goal_info,
            dict,
        ):
            continue

        event = goal_info.get(
            "event"
        )

        if not isinstance(
            event,
            dict,
        ):
            event = goal_info

        goal_key = (
            goal_info.get(
                "event_key"
            )
        )

        # اگر گل از قبل در state وجود داشته،
        # نباید دوباره پیام بفرستیم.
        already_existed = False

        if goal_key:

            for old_goal in match_state.get(
                "goals",
                [],
            ):

                if not isinstance(
                    old_goal,
                    dict,
                ):
                    continue

                if (
                    old_goal.get(
                        "event_key"
                    )
                    == goal_key
                ):
                    # چون sync همین الان گل را اضافه کرده،
                    # تشخیص اینکه قبلاً وجود داشته یا نه
                    # از روی event_keys انجام می‌شود.
                    if goal_key in (
                        match_state.get(
                            "_goals_sent_this_run",
                            [],
                        )
                    ):
                        already_existed = True

                    break

        if already_existed:
            continue

        # ----------------------------------------------------
        # علامت موقت برای جلوگیری از ارسال تکراری
        # ----------------------------------------------------

        sent_this_run = match_state.setdefault(
            "_goals_sent_this_run",
            [],
        )

        if goal_key in sent_this_run:
            continue

        sent_this_run.append(
            goal_key
        )

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
    # VAR / گل مردودشده
    # --------------------------------------------------------

    for cancelled_goal in cancelled_goals:

        if not isinstance(
            cancelled_goal,
            dict,
        ):
            continue

        goal_key = (
            cancelled_goal.get(
                "key"
            )
            or cancelled_goal.get(
                "event_key"
            )
            or cancelled_goal.get(
                "id"
            )
        )

        if goal_key is None:
            continue

        goal_key = str(
            goal_key
        )

        # اگر این گل قبلاً مردود شده،
        # دوباره پیام VAR نفرست.
        if goal_key in previous_cancelled_keys:
            continue

        # ----------------------------------------------------
        # پیدا کردن گل اصلی در state
        # ----------------------------------------------------

        saved_goal = None

        for goal in match_state.get(
            "goals",
            [],
        ):

            if not isinstance(
                goal,
                dict,
            ):
                continue

            if str(
                goal.get(
                    "event_key"
                )
            ) == goal_key:

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
            original_event = (
                cancelled_goal.get(
                    "event"
                )
            )

        if not isinstance(
            original_event,
            dict,
        ):
            original_event = {}

        cancellation_data = {
            "goal_event": original_event,
            "minute": (
                cancelled_goal.get(
                    "minute"
                )
                if cancelled_goal.get(
                    "minute"
                ) is not None
                else (
                    saved_goal.get(
                        "minute"
                    )
                    if saved_goal
                    else None
                )
            ),
            "is_home": (
                cancelled_goal.get(
                    "is_home"
                )
                if cancelled_goal.get(
                    "is_home"
                ) is not None
                else (
                    saved_goal.get(
                        "is_home"
                    )
                    if saved_goal
                    else None
                )
            ),
        }

        # نتیجه بعد از لغو گل
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
        changes.get("half_time", False)
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

        if not message:
            continue

        print(
            f"[{match_id}] Red card detected."
        )

        send_long_message(
            message
        )

    # --------------------------------------------------------
    # سایر eventها
    # --------------------------------------------------------

    new_events = changes.get(
        "new_events",
        [],
    )

    handled_goal_keys = {
        str(
            goal.get(
                "event_key"
            )
        )
        for goal in new_goal_info
        if (
            isinstance(
                goal,
                dict,
            )
            and goal.get(
                "event_key"
            ) is not None
        )
    }

    handled_red_card_keys = set()

    for event in new_red_cards:

        if not isinstance(
            event,
            dict,
        ):
            continue

        key = (
            event.get(
                "key"
            )
            or event.get(
                "event_key"
            )
            or event.get(
                "id"
            )
        )

        if key is not None:
            handled_red_card_keys.add(
                str(key)
            )

    for event in new_events:

        if not isinstance(
            event,
            dict,
        ):
            continue

        event_key = (
            event.get(
                "key"
            )
            or event.get(
                "event_key"
            )
            or event.get(
                "id"
            )
        )

        if event_key is not None:
            event_key = str(
                event_key
            )

        # گل‌ها قبلاً جداگانه ارسال شدند.
        if (
            event_key is not None
            and event_key in handled_goal_keys
        ):
            continue

        # کارت قرمز هم جداگانه ارسال شد.
        if (
            event_key is not None
            and event_key in handled_red_card_keys
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
    # وضعیت مسابقه
    # --------------------------------------------------------

    if changes.get(
        "current_started",
        False,
    ):
        match_state["started"] = True

    if changes.get(
        "current_half_time",
        False,
    ):
        match_state["half_time"] = True

    if changes.get(
        "current_finished",
        False,
    ):
        match_state["finished"] = True

    # --------------------------------------------------------
    # پاک کردن متغیر موقت
    # --------------------------------------------------------

    match_state.pop(
        "_goals_sent_this_run",
        None,
    )

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
                "finished_sent"
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
        # ذخیره event keyها
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
        # نمایش نتیجه در لاگ
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

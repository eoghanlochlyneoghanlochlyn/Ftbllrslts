import time


from fotmob import (
    get_match_events,
    get_match_snapshot,
)

from match_manager import (
    get_enabled_matches,
    get_match_id,
    get_match_url,
)

from state_manager import (
    add_event_keys,
    add_goal,
    cancel_goal,
    get_current_score,
    get_match_state,
    load_state,
    save_state,
)

from event_detector import (
    detect_state_changes,
    event_key,
)

from formatter import (
    build_cancelled_goal_message,
    build_final_message,
    build_goal_message,
    build_half_time_message,
    build_lineup_message,
    build_red_card_message,
    build_start_message,
)

from telegram_sender import (
    send_long_message,
)


# =========================================================
# تنظیمات
# =========================================================

POLL_INTERVAL = 60


# =========================================================
# ابزارهای event
# =========================================================

def get_event_key_safe(event):

    try:

        return event_key(
            event
        )

    except Exception:

        return None


def get_goal_event_from_cancellation(
    cancelled_goal,
):

    if not isinstance(
        cancelled_goal,
        dict,
    ):
        return None

    return cancelled_goal.get(
        "goal_event"
    )


def get_goal_key_from_cancellation(
    cancelled_goal,
):

    if not isinstance(
        cancelled_goal,
        dict,
    ):
        return None

    key = cancelled_goal.get(
        "goal_key"
    )

    if key is not None:
        return str(key)

    event = get_goal_event_from_cancellation(
        cancelled_goal
    )

    return get_event_key_safe(
        event
    )


# =========================================================
# نتیجه قبل / بعد گل
# =========================================================

def get_goal_score_before_event(
    match_state,
):

    return get_current_score(
        match_state
    )


def get_goal_score_after_event(
    match_state,
    goal_info,
):

    # ابتدا گل را وارد state می‌کنیم
    add_goal(
        match_state,
        goal_info,
    )

    return get_current_score(
        match_state
    )


# =========================================================
# پردازش eventهای زنده
# =========================================================

def process_live_events(
    snapshot,
    match_state,
    changes,
):

    # -----------------------------------------------------
    # event keys
    # -----------------------------------------------------

    new_event_keys = (
        changes.get(
            "event_keys",
            [],
        )
    )

    add_event_keys(
        match_state,
        new_event_keys,
    )

    # -----------------------------------------------------
    # گل‌ها
    # -----------------------------------------------------

    for goal_info in (
        changes.get(
            "goals",
            []
        )
    ):

        if not isinstance(
            goal_info,
            dict,
        ):
            continue

        goal_key = goal_info.get(
            "event_key"
        )

        if goal_key is None:
            continue

        # اگر قبلاً در state هست،
        # دوباره ارسال نکن
        existing_goal = None

        for goal in (
            match_state.get(
                "goals",
                [],
            )
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
            ) == str(
                goal_key
            ):

                existing_goal = goal
                break

        if existing_goal is not None:
            continue

        # -------------------------------------------------
        # مهم:
        # گل را اول به state اضافه می‌کنیم
        # تا نتیجه پیام همین گل درست باشد.
        # -------------------------------------------------

        score_after = (
            get_goal_score_after_event(
                match_state,
                goal_info,
            )
        )

        event = goal_info.get(
            "event"
        )

        if not isinstance(
            event,
            dict,
        ):
            continue

        print(
            "[GOAL] "
            f"{snapshot.get('home', 'Home')} "
            f"- "
            f"{snapshot.get('away', 'Away')}"
        )

        message = build_goal_message(
            snapshot,
            event,
            score_after,
        )

        if message:

            send_long_message(
                message
            )

    # -----------------------------------------------------
    # گل‌های مردود
    # -----------------------------------------------------

    for cancelled_goal in (
        changes.get(
            "cancelled_goals",
            []
        )
    ):

        goal_key = (
            get_goal_key_from_cancellation(
                cancelled_goal
            )
        )

        if goal_key is None:
            continue

        goal_event = (
            get_goal_event_from_cancellation(
                cancelled_goal
            )
        )

        if not isinstance(
            goal_event,
            dict,
        ):
            continue

        # اگر گل در state وجود دارد،
        # آن را مردود می‌کنیم.
        goal = None

        for item in (
            match_state.get(
                "goals",
                [],
            )
        ):

            if not isinstance(
                item,
                dict,
            ):
                continue

            if str(
                item.get(
                    "event_key"
                )
            ) == str(
                goal_key
            ):

                goal = item
                break

        was_cancelled = False

        if goal is not None:

            was_cancelled = bool(
                goal.get(
                    "cancelled",
                    False,
                )
            )

            if not was_cancelled:

                cancel_goal(
                    match_state,
                    goal_key,
                )

        if was_cancelled:
            continue

        score_after_cancel = (
            get_current_score(
                match_state
            )
        )

        message = (
            build_cancelled_goal_message(
                snapshot,
                cancelled_goal,
                score_after_cancel,
            )
        )

        if message:

            send_long_message(
                message
            )

    # -----------------------------------------------------
    # کارت قرمز
    # -----------------------------------------------------

    for event in (
        changes.get(
            "red_cards",
            []
        )
    ):

        if not isinstance(
            event,
            dict,
        ):
            continue

        message = (
            build_red_card_message(
                snapshot,
                event,
            )
        )

        if message:

            send_long_message(
                message
            )


# =========================================================
# پردازش یک مسابقه
# =========================================================

def process_match(
    state,
    match,
):

    match_id = get_match_id(
        match
    )

    match_url = get_match_url(
        match
    )

    if not match_id:

        print(
            "Match ID not found."
        )

        return

    if not match_url:

        print(
            f"[{match_id}] Match URL not found."
        )

        return

    match_state = get_match_state(
        state,
        match_id,
    )

    # -----------------------------------------------------
    # snapshot
    # -----------------------------------------------------

    snapshot = get_match_snapshot(
        match_url
    )

    if not snapshot:

        print(
            f"[{match_id}] "
            "Could not get match snapshot."
        )

        return

    home_name = (
        snapshot.get(
            "home"
        )
        or "Home"
    )

    away_name = (
        snapshot.get(
            "away"
        )
        or "Away"
    )

    print(
        f"\n[{match_id}] "
        f"{home_name} vs {away_name}"
    )

    print(
        "Started:",
        snapshot.get(
            "started"
        ),
    )

    print(
        "Half time:",
        snapshot.get(
            "half_time"
        ),
    )

    print(
        "Finished:",
        snapshot.get(
            "finished"
        ),
    )

    print(
        "Score:",
        snapshot.get(
            "score"
        ),
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

    # -----------------------------------------------------
    # ترکیب رسمی
    # -----------------------------------------------------

    lineup_type = str(
        snapshot.get(
            "lineup_type"
        )
        or ""
    ).lower()

    home_starters = snapshot.get(
        "home_starters",
        [],
    )

    away_starters = snapshot.get(
        "away_starters",
        [],
    )

    valid_lineup = (
        len(home_starters) == 11
        and len(away_starters) == 11
        and lineup_type in (
            "standard",
            "confirmed",
        )
    )

    if (
        valid_lineup
        and not match_state.get(
            "lineup_sent",
            False,
        )
    ):

        print(
            f"[{match_id}] "
            "Sending lineup message."
        )

        message = build_lineup_message(
            snapshot,
            show_rating=False,
        )

        if message:

            send_long_message(
                message
            )

            match_state[
                "lineup_sent"
            ] = True

    # -----------------------------------------------------
    # eventهای مسابقه
    # -----------------------------------------------------

    events = get_match_events(
        match_url
    )

    print(
        f"[{match_id}] "
        f"Events found: {len(events)}"
    )

    # -----------------------------------------------------
    # تشخیص تغییرات
    # -----------------------------------------------------

    changes = detect_state_changes(
        match_state,
        events,
        snapshot,
    )

    # -----------------------------------------------------
    # شروع بازی
    # -----------------------------------------------------

    if (
        changes.get(
            "start"
        )
        and not match_state.get(
            "started",
            False,
        )
    ):

        print(
            f"[{match_id}] "
            "Match started."
        )

        message = build_start_message(
            snapshot
        )

        if message:

            send_long_message(
                message
            )

        match_state[
            "started"
        ] = True

    elif snapshot.get(
        "started"
    ):

        match_state[
            "started"
        ] = True

    # -----------------------------------------------------
    # نیمه اول
    # -----------------------------------------------------

    if (
        changes.get(
            "half_time"
        )
        and not match_state.get(
            "half_time",
            False,
        )
    ):

        print(
            f"[{match_id}] "
            "Half time."
        )

        score = get_current_score(
            match_state
        )

        # اگر state هنوز همه گل‌ها را ندارد،
        # برای بازی‌ای که وسط کار به ربات اضافه شده
        # از نتیجه FotMob استفاده می‌کنیم.
        if not score or (
            score.get("home", 0) == 0
            and score.get("away", 0) == 0
            and snapshot.get("score")
        ):

            score = snapshot.get(
                "score"
            )

        message = (
            build_half_time_message(
                snapshot,
                score,
            )
        )

        if message:

            send_long_message(
                message
            )

        match_state[
            "half_time"
        ] = True

    elif snapshot.get(
        "half_time"
    ):

        match_state[
            "half_time"
        ] = True

    # -----------------------------------------------------
    # eventهای زنده
    # -----------------------------------------------------

    process_live_events(
        snapshot,
        match_state,
        changes,
    )

    # -----------------------------------------------------
    # پایان بازی
    # -----------------------------------------------------

    if snapshot.get(
        "finished"
    ):

        if not match_state.get(
            "finished",
            False,
        ):

            match_state[
                "finished"
            ] = True

        if not match_state.get(
            "finished_sent",
            False,
        ):

            print(
                f"[{match_id}] "
                "Final message sent."
            )

            # اگر state تمام گل‌ها را دارد،
            # نتیجه را از state بگیر.
            final_score = get_current_score(
                match_state
            )

            # اگر state خالی بوده ولی FotMob
            # نتیجه نهایی دارد، از FotMob استفاده کن.
            if (
                final_score.get("home", 0) == 0
                and final_score.get("away", 0) == 0
                and snapshot.get("score")
            ):

                final_score = snapshot.get(
                    "score"
                )

            message = build_final_message(
                snapshot,
                final_score,
            )

            if message:

                send_long_message(
                    message
                )

                match_state[
                    "finished_sent"
                ] = True


# =========================================================
# main
# =========================================================

def main():

    state = load_state()

    matches = get_enabled_matches()

    if not matches:

        print(
            "No enabled matches."
        )

        save_state(
            state
        )

        return

    print(
        f"Enabled matches: {len(matches)}"
    )

    for match in matches:

        try:

            process_match(
                state,
                match,
            )

        except Exception as error:

            match_id = get_match_id(
                match
            )

            print(
                f"[{match_id}] "
                f"Error: {error}"
            )

    save_state(
        state
    )


# =========================================================
# اجرا
# =========================================================

if __name__ == "__main__":

    main()

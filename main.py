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
    build_final_lineup_message,
    build_final_stats_message,
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
        # event خام گل
        # -------------------------------------------------

        event = goal_info.get(
            "event"
        )

        print(
            "\n"
            "=================================================="
        )

        print(
            "[GOAL DEBUG]"
        )

        print(
            "Goal key:",
            goal_key,
        )

        print(
            "Goal info:",
            goal_info,
        )

        print(
            "Raw event:",
            event,
        )

        print(
            "Snapshot home:",
            snapshot.get(
                "home"
            ),
        )

        print(
            "Snapshot away:",
            snapshot.get(
                "away"
            ),
        )

        print(
            "Snapshot score:",
            snapshot.get(
                "score"
            ),
        )

        print(
            "Score BEFORE:",
            get_current_score(
                match_state
            ),
        )

        # -------------------------------------------------
        # ثبت گل و محاسبه نتیجه بعد از گل
        # -------------------------------------------------

        score_after = (
            get_goal_score_after_event(
                match_state,
                goal_info,
            )
        )

        print(
            "Score AFTER:",
            score_after,
        )

        print(
            "State goals:",
            match_state.get(
                "goals",
                [],
            ),
        )

        print(
            "=================================================="
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

    # برای formatterهای نهایی و detector
    # eventها را مستقیماً نگه می‌داریم.
    snapshot[
        "events"
    ] = events

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
                "Sending final lineup/performance message."
            )

            # اگر state تمام گل‌ها را دارد،
            # نتیجه را از state می‌گیریم.
            final_score = get_current_score(
                match_state
            )

            # اگر state خالی بوده ولی FotMob
            # نتیجه نهایی دارد، از FotMob استفاده می‌کنیم.
            if (
                final_score.get("home", 0) == 0
                and final_score.get("away", 0) == 0
                and snapshot.get("score")
            ):

                final_score = snapshot.get(
                    "score"
                )

            # -------------------------------------------------
            # پیام اول:
            # ترکیب + امتیاز + گل + پاس گل + OG
            # -------------------------------------------------

            final_lineup_message = (
                build_final_lineup_message(
                    snapshot,
                    events,
                )
            )

            lineup_sent = False

            if final_lineup_message:

                send_long_message(
                    final_lineup_message
                )

                lineup_sent = True

            # -------------------------------------------------
            # پیام دوم:
            # آمار بازی
            # -------------------------------------------------

            print(
                f"[{match_id}] "
                "Sending final stats message."
            )

            final_stats_message = (
                build_final_stats_message(
                    snapshot,
                    final_score,
                )
            )

            stats_sent = False

            if final_stats_message:

                send_long_message(
                    final_stats_message
                )

                stats_sent = True

            # فقط وقتی هر دو پیام ساخته و ارسال شدند
            # وضعیت نهایی ثبت می‌شود.
            if (
                lineup_sent
                and stats_sent
            ):

                match_state[
                    "finished_sent"
                ] = True

                print(
                    f"[{match_id}] "
                    "Final messages sent."
                )


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

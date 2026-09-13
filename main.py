import time

from fotmob import (
    get_match_snapshot,
    get_match_events,
)

from match_manager import (
    get_match_id,
    get_match_url,
    get_enabled_matches,
)

from state_manager import (
    load_state,
    save_state,
    get_match_state,
    add_event_keys,
    add_goal,
    find_goal,
    cancel_goal,
    get_current_score,
)

from event_detector import (
    detect_state_changes,
    event_key,
)

from formatter import (
    build_lineup_message,
    build_start_message,
    build_goal_message,
    build_cancelled_goal_message,
    build_half_time_message,
    build_red_card_message,
    build_finish_message,
)

from telegram_sender import (
    send_long_message,
)


POLL_INTERVAL = 60


# ============================================================
# ابزارهای گل مردود
# ============================================================

def get_goal_key_from_cancellation(
    cancelled_goal,
):
    if not isinstance(
        cancelled_goal,
        dict,
    ):
        return None

    goal_key = cancelled_goal.get(
        "goal_key"
    )

    if goal_key is not None:
        return str(goal_key)

    goal_event = cancelled_goal.get(
        "goal_event"
    )

    if not isinstance(
        goal_event,
        dict,
    ):
        return None

    return event_key(
        goal_event
    )


def get_goal_event_from_cancellation(
    cancelled_goal,
):
    if not isinstance(
        cancelled_goal,
        dict,
    ):
        return None

    goal_event = cancelled_goal.get(
        "goal_event"
    )

    if isinstance(
        goal_event,
        dict,
    ):
        return goal_event

    return None


# ============================================================
# کلید event
# ============================================================

def get_event_key_safe(event):
    try:
        return event_key(event)
    except Exception:
        return None


# ============================================================
# نتیجه قبل و بعد از گل
# ============================================================

def get_goal_score_before_event(
    match_state,
    goal_event,
):
    """
    نتیجه قبل از ثبت گل را از state محاسبه می‌کند.
    """

    return get_current_score(
        match_state
    )


def get_goal_score_after_event(
    match_state,
    goal_event,
):
    """
    ابتدا گل را به صورت موقت به state اضافه می‌کند
    و سپس نتیجه جدید را محاسبه می‌کند.

    توجه:
    این تابع برای محاسبه است و خودش گل را ثبت نمی‌کند.
    """

    from copy import deepcopy

    temporary_state = deepcopy(
        match_state
    )

    from event_detector import get_goal_info

    goal_info = get_goal_info(
        goal_event
    )

    if goal_info is not None:
        add_goal(
            temporary_state,
            goal_info,
        )

    return get_current_score(
        temporary_state
    )


# ============================================================
# پردازش eventهای زنده
# ============================================================

def process_live_events(
    snapshot,
    match_state,
    changes,
):
    # --------------------------------------------------------
    # گل‌های جدید
    # --------------------------------------------------------

    for goal_event in (
        changes.get(
            "new_goals",
            [],
        )
    ):

        goal_key = get_event_key_safe(
            goal_event
        )

        if goal_key is None:
            continue

        # اگر قبلاً گل ثبت شده، دوباره ارسال نکن.
        existing_goal = find_goal(
            match_state,
            goal_key,
        )

        if existing_goal is not None:
            continue

        # نتیجه قبل از گل
        score_before = (
            get_goal_score_before_event(
                match_state,
                goal_event,
            )
        )

        from event_detector import (
            get_goal_info,
        )

        goal_info = get_goal_info(
            goal_event
        )

        if goal_info is None:
            continue

        # ثبت گل
        add_goal(
            match_state,
            goal_info,
        )

        # نتیجه بعد از گل
        score_after = get_current_score(
            match_state
        )

        message = build_goal_message(
            snapshot,
            goal_event,
            score_after,
        )

        if message:
            print(
                f"[{snapshot.get('match_id')}] "
                "Goal detected."
            )

            send_long_message(
                message
            )

    # --------------------------------------------------------
    # گل‌های مردود شده توسط VAR
    # --------------------------------------------------------

    for cancelled_goal in (
        changes.get(
            "cancelled_goals",
            [],
        )
    ):

        goal_key = (
            get_goal_key_from_cancellation(
                cancelled_goal
            )
        )

        if goal_key is None:
            continue

        goal = find_goal(
            match_state,
            goal_key,
        )

        # اگر گل در state وجود نداشته باشد،
        # چیزی برای لغو کردن نداریم.
        if goal is None:
            continue

        # VAR قبلاً پردازش شده.
        if goal.get(
            "cancelled",
            False,
        ):
            continue

        cancel_goal(
            match_state,
            goal_key,
        )

        current_score = get_current_score(
            match_state
        )

        message = (
            build_cancelled_goal_message(
                snapshot,
                cancelled_goal,
                current_score,
            )
        )

        if message:
            print(
                f"[{snapshot.get('match_id')}] "
                "Cancelled goal detected."
            )

            send_long_message(
                message
            )

    # --------------------------------------------------------
    # کارت قرمز
    # --------------------------------------------------------

    for red_card in (
        changes.get(
            "new_red_cards",
            [],
        )
    ):

        key = get_event_key_safe(
            red_card
        )

        if key is None:
            continue

        message = build_red_card_message(
            snapshot,
            red_card,
        )

        if message:
            print(
                f"[{snapshot.get('match_id')}] "
                "Red card detected."
            )

            send_long_message(
                message
            )


# ============================================================
# پردازش یک مسابقه
# ============================================================

def process_match(
    match_config,
    state,
):
    match_id = get_match_id(
        match_config
    )

    if match_id is None:
        print(
            "Could not determine match ID."
        )
        return

    match_id = str(
        match_id
    )

    match_url = get_match_url(
        match_config
    )

    if not match_url:
        print(
            f"[{match_id}] "
            "Could not determine match URL."
        )
        return

    match_state = get_match_state(
        state,
        match_id,
    )

    # --------------------------------------------------------
    # دریافت snapshot
    # --------------------------------------------------------

    snapshot = get_match_snapshot(
        match_url
    )

    if not snapshot:
        print(
            f"[{match_id}] "
            "Could not get match snapshot."
        )
        return

    # ID را برای لاگ و سایر بخش‌ها نگه می‌داریم.
    snapshot["match_id"] = match_id

    # --------------------------------------------------------
    # دریافت eventها
    # --------------------------------------------------------

    try:
        events = get_match_events(
            match_url
        )

    except Exception as exc:
        print(
            f"[{match_id}] "
            f"Could not get events: {exc}"
        )

        events = []

    if not isinstance(
        events,
        list,
    ):
        events = []

    # --------------------------------------------------------
    # مهم:
    # eventها باید داخل snapshot قرار بگیرند.
    # event_detector از snapshot["events"] می‌خواند.
    # --------------------------------------------------------

    snapshot["events"] = events

    # --------------------------------------------------------
    # اطلاعات لاگ
    # --------------------------------------------------------

    home_name = (
        snapshot.get("home")
        or "Home"
    )

    away_name = (
        snapshot.get("away")
        or "Away"
    )

    print(
        f"[{match_id}] "
        f"{home_name} vs {away_name}"
    )

    print(
        f"Started: "
        f"{snapshot.get('started', False)}"
    )

    print(
        f"Half time: "
        f"{snapshot.get('half_time', False)}"
    )

    print(
        f"Finished: "
        f"{snapshot.get('finished', False)}"
    )

    print(
        f"Events: {len(events)}"
    )

    # --------------------------------------------------------
    # تشخیص تغییرات
    # --------------------------------------------------------

    changes = detect_state_changes(
        match_state,
        snapshot,
    )

    # --------------------------------------------------------
    # ترکیب رسمی
    # --------------------------------------------------------

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

    valid_lineup = (
        lineup_type
        in (
            "standard",
            "confirmed",
        )
        and len(home_starters) == 11
        and len(away_starters) == 11
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

    # --------------------------------------------------------
    # شروع بازی
    # --------------------------------------------------------

    if changes.get(
        "started",
        False,
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

    # --------------------------------------------------------
    # نیمه اول
    # --------------------------------------------------------

    if changes.get(
        "half_time",
        False,
    ):

        print(
            f"[{match_id}] "
            "Half time."
        )

        score = get_current_score(
            match_state
        )

        message = build_half_time_message(
            snapshot,
            score,
        )

        if message:
            send_long_message(
                message
            )

    # --------------------------------------------------------
    # eventهای زنده
    # --------------------------------------------------------

    process_live_events(
        snapshot,
        match_state,
        changes,
    )

    # --------------------------------------------------------
    # ثبت تمام eventهای فعلی
    #
    # این کار باعث می‌شود در poll بعدی eventهای قدیمی
    # دوباره به عنوان event جدید شناخته نشوند.
    # --------------------------------------------------------

    add_event_keys(
        match_state,
        changes.get(
            "current_event_keys",
            [],
        ),
    )

    # --------------------------------------------------------
    # به‌روزرسانی وضعیت بازی
    # --------------------------------------------------------

    match_state[
        "started"
    ] = changes.get(
        "current_started",
        match_state.get(
            "started",
            False,
        ),
    )

    match_state[
        "half_time"
    ] = changes.get(
        "current_half_time",
        match_state.get(
            "half_time",
            False,
        ),
    )

    match_state[
        "finished"
    ] = changes.get(
        "current_finished",
        match_state.get(
            "finished",
            False,
        ),
    )

    # --------------------------------------------------------
    # پایان بازی
    # --------------------------------------------------------

    current_finished = changes.get(
        "current_finished",
        False,
    )

    if (
        current_finished
        and not match_state.get(
            "finished_sent",
            False,
        )
    ):

        print(
            f"[{match_id}] "
            "Final message sent."
        )

        final_score = get_current_score(
            match_state
        )

        message = build_finish_message(
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

        match_state[
            "finished"
        ] = True


# ============================================================
# اجرای اصلی
# ============================================================

def main():
    state = load_state()

    matches = get_enabled_matches()

    if not matches:
        print(
            "No enabled matches."
        )
        save_state(state)
        return

    for match_config in matches:

        try:

            process_match(
                match_config,
                state,
            )

        except Exception as exc:

            match_id = get_match_id(
                match_config
            )

            print(
                f"[{match_id}] "
                f"Error: {exc}"
            )

    save_state(
        state
    )


if __name__ == "__main__":
    main()

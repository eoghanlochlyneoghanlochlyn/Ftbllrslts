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
    find_goal,
    get_current_score,
    get_match_state,
    load_state,
    mark_goal_update_complete,
    save_state,
    set_goal_message_id,
)

from event_detector import (
    detect_state_changes,
    event_key,
)

from formatter import (
    build_cancelled_goal_message,
    build_final_lineup_rich_message,
    build_final_stats_rich_message,
    build_goal_message,
    build_half_time_message,
    build_lineup_rich_message,
    build_red_card_message,
    build_start_message,
)

from telegram_sender import (
    edit_rich_message,
    send_long_message,
    send_rich_message,
    send_telegram,
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
# Telegram helpers
# =========================================================

def get_telegram_message_id(
    response
):

    if not isinstance(
        response,
        dict,
    ):
        return None

    if response.get(
        "ok"
    ) is not True:
        return None

    result = response.get(
        "result"
    )

    if not isinstance(
        result,
        dict,
    ):
        return None

    message_id = result.get(
        "message_id"
    )

    if message_id is None:
        return None

    try:

        return int(
            message_id
        )

    except (
        TypeError,
        ValueError,
    ):

        return None


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
# آماده‌سازی اطلاعات گل
# =========================================================

def prepare_goal_info(
    goal_info,
):

    if not isinstance(
        goal_info,
        dict,
    ):
        return goal_info

    event = goal_info.get(
        "event"
    )

    if not isinstance(
        event,
        dict,
    ):
        return goal_info

    # نام بازیکن از event_detector داخل goal_info
    # قرار گرفته است. اینجا فقط برای سازگاری با
    # stateهای قدیمی fallback داریم.

    if not goal_info.get(
        "player_name"
    ):

        player = event.get(
            "player"
        )

        if isinstance(
            player,
            dict,
        ):

            goal_info[
                "player_name"
            ] = (
                player.get(
                    "name"
                )
                or player.get(
                    "shortName"
                )
                or ""
            )

        else:

            goal_info[
                "player_name"
            ] = (
                event.get(
                    "playerName"
                )
                or ""
            )

    if not goal_info.get(
        "assist_player_name"
    ):

        assist_player = event.get(
            "assistPlayer"
        )

        if isinstance(
            assist_player,
            dict,
        ):

            goal_info[
                "assist_player_name"
            ] = (
                assist_player.get(
                    "name"
                )
                or assist_player.get(
                    "shortName"
                )
                or ""
            )

        else:

            goal_info[
                "assist_player_name"
            ] = (
                event.get(
                    "assistPlayerName"
                )
                or ""
            )

    return goal_info


# =========================================================
# پردازش گل جدید
# =========================================================

def process_new_goal(
    snapshot,
    match_state,
    goal_info,
):

    if not isinstance(
        goal_info,
        dict,
    ):
        return False

    goal_key = goal_info.get(
        "event_key"
    )

    if goal_key is None:
        return False

    goal_info = prepare_goal_info(
        goal_info
    )

    event = goal_info.get(
        "event"
    )

    if not isinstance(
        event,
        dict,
    ):
        return False

    existing_goal = find_goal(
        match_state,
        goal_key,
    )

    # -----------------------------------------------------
    # اگر قبلاً state ساخته شده ولی پیام هنوز ثبت نشده،
    # یعنی احتمالاً اجرای قبلی هنگام ارسال شکست خورده.
    #
    # در این حالت نباید پیام جدید را به‌عنوان گل جدید
    # تشخیص بدهیم؛ همان گل را دوباره ارسال می‌کنیم.
    # -----------------------------------------------------

    if existing_goal is not None:

        existing_message_id = (
            existing_goal.get(
                "telegram_message_id"
            )
        )

        if existing_message_id is not None:

            return True

    # -----------------------------------------------------
    # اصلاح is_home برای گل به خودی
    # -----------------------------------------------------

    if goal_info.get(
        "own_goal",
        False,
    ):

        event_is_home = event.get(
            "isHome"
        )

        if isinstance(
            event_is_home,
            bool,
        ):

            goal_info[
                "is_home"
            ] = not event_is_home

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

    # -----------------------------------------------------
    # ثبت موقت گل برای محاسبه score
    # -----------------------------------------------------

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

    if not message:

        print(
            "[GOAL] Goal message is empty."
        )

        return False

    try:

        response = send_telegram(
            message
        )

        message_id = (
            get_telegram_message_id(
                response
            )
        )

        if message_id is None:

            print(
                "[GOAL] Telegram response "
                "did not contain message_id."
            )

            return False

        set_goal_message_id(
            match_state,
            goal_key,
            message_id,
        )

        add_event_keys(
            match_state,
            [
                goal_key
            ],
        )

        print(
            "[GOAL] Message sent successfully."
        )

        print(
            "[GOAL] Telegram message_id:",
            message_id,
        )

        return True

    except Exception as error:

        print(
            "[GOAL] Telegram send failed:",
            error,
        )

        # نکته مهم:
        # event_key عمداً اینجا ثبت نمی‌شود.
        # اجرای بعدی دوباره تلاش خواهد کرد.

        return False


# =========================================================
# پردازش اطلاعات به‌روزشده گل
# =========================================================

def process_updated_goal(
    snapshot,
    match_state,
    goal_info,
):

    if not isinstance(
        goal_info,
        dict,
    ):
        return False

    goal_key = goal_info.get(
        "event_key"
    )

    if goal_key is None:
        return False

    goal_info = prepare_goal_info(
        goal_info
    )

    event = goal_info.get(
        "event"
    )

    if not isinstance(
        event,
        dict,
    ):
        return False

    existing_goal = find_goal(
        match_state,
        goal_key,
    )

    if existing_goal is None:
        return False

    old_player_name = (
        existing_goal.get(
            "player_name"
        )
    )

    new_player_name = (
        goal_info.get(
            "player_name"
        )
    )

    print(
        "[GOAL UPDATE]"
    )

    print(
        "Goal key:",
        goal_key,
    )

    print(
        "Old player:",
        old_player_name,
    )

    print(
        "New player:",
        new_player_name,
    )

    # -----------------------------------------------------
    # add_goal اطلاعات جدید را داخل state merge می‌کند.
    # -----------------------------------------------------

    add_goal(
        match_state,
        goal_info,
    )

    existing_goal = find_goal(
        match_state,
        goal_key,
    )

    if existing_goal is None:
        return False

    message_id = existing_goal.get(
        "telegram_message_id"
    )

    if message_id is None:

        print(
            "[GOAL UPDATE] "
            "No previous Telegram message_id."
        )

        return False

    # اگر هنوز نام واقعی نداریم، edit نکن.
    needs_update = bool(
        existing_goal.get(
            "needs_update",
            False,
        )
    )

    if not needs_update:

        return False

    # -----------------------------------------------------
    # score را از state می‌گیریم.
    # -----------------------------------------------------

    score = get_current_score(
        match_state
    )

    rich_message = (
        build_goal_message(
            snapshot,
            event,
            score,
        )
    )

    # build_goal_message در پروژه فعلی متن معمولی است.
    # برای editRich باید rich_message معتبر داشته باشیم.
    #
    # بنابراین متن را در قالب markdown-rich قرار می‌دهیم.
    # Telegram Rich Messages این حالت را پشتیبانی می‌کند.

    if not rich_message:

        return False

    rich_message_payload = {
        "markdown": rich_message,
    }

    try:

        response = edit_rich_message(
            message_id,
            rich_message_payload,
        )

        if not isinstance(
            response,
            dict,
        ):
            return False

        if response.get(
            "ok"
        ) is not True:

            return False

        mark_goal_update_complete(
            match_state,
            goal_key,
        )

        print(
            "[GOAL UPDATE] "
            "Previous Telegram message edited."
        )

        print(
            "[GOAL UPDATE] "
            "message_id:",
            message_id,
        )

        return True

    except Exception as error:

        print(
            "[GOAL UPDATE] "
            f"Telegram edit failed: {error}"
        )

        # needs_update همچنان True باقی می‌ماند.
        # اجرای بعدی دوباره تلاش می‌کند.

        return False


# =========================================================
# پردازش eventهای زنده
# =========================================================

def process_live_events(
    snapshot,
    match_state,
    changes,
):

    # -----------------------------------------------------
    # گل‌های جدید
    #
    # مهم:
    # event_key قبل از ارسال پیام ثبت نمی‌شود.
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

        process_new_goal(
            snapshot,
            match_state,
            goal_info,
        )

    # -----------------------------------------------------
    # گل‌هایی که اطلاعاتشان بعداً کامل شده
    # -----------------------------------------------------

    for goal_info in (
        changes.get(
            "updated_goals",
            []
        )
    ):

        if not isinstance(
            goal_info,
            dict,
        ):
            continue

        process_updated_goal(
            snapshot,
            match_state,
            goal_info,
        )

    # -----------------------------------------------------
    # eventهای غیرگل
    #
    # فقط بعد از موفقیت ارسال event_key ثبت می‌شود.
    # -----------------------------------------------------

    previous_keys = {
        str(key)
        for key in (
            match_state.get(
                "event_keys",
                [],
            )
        )
    }

    for event in (
        changes.get(
            "events",
            []
        )
    ):

        if not isinstance(
            event,
            dict,
        ):
            continue

        key = get_event_key_safe(
            event
        )

        if key is None:
            continue

        if str(key) in previous_keys:
            continue

        event_type = (
            event.get(
                "type"
            )
            or ""
        )

        # goal قبلاً در بخش بالا پردازش شده.
        # اگر ارسال موفق شده باشد key ثبت شده است.
        if (
            "goal" in str(
                event_type
            ).lower()
            or event.get(
                "isGoal"
            ) is True
        ):

            continue

        # کارت‌ها
        is_red_card = False

        if key in {
            str(item)
            for item in (
                changes.get(
                    "event_keys",
                    []
                )
            )
        }:

            for red_card in (
                changes.get(
                    "red_cards",
                    []
                )
            ):

                if (
                    get_event_key_safe(
                        red_card
                    )
                    == key
                ):

                    is_red_card = True

                    message = (
                        build_red_card_message(
                            snapshot,
                            red_card,
                        )
                    )

                    if not message:
                        continue

                    try:

                        send_long_message(
                            message
                        )

                        add_event_keys(
                            match_state,
                            [
                                key
                            ],
                        )

                        previous_keys.add(
                            str(key)
                        )

                    except Exception as error:

                        print(
                            "[RED CARD] "
                            f"Send failed: {error}"
                        )

                    break

        if is_red_card:
            continue

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

        goal = find_goal(
            match_state,
            goal_key,
        )

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

            try:

                send_long_message(
                    message
                )

            except Exception as error:

                print(
                    "[CANCELLED GOAL] "
                    f"Send failed: {error}"
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
            "Sending lineup rich message."
        )

        rich_message = (
            build_lineup_rich_message(
                snapshot,
                show_rating=False,
            )
        )

        if rich_message:

            try:

                response = send_rich_message(
                    rich_message
                )

                if isinstance(
                    response,
                    dict,
                ) and response.get(
                    "ok"
                ) is True:

                    match_state[
                        "lineup_sent"
                    ] = True

            except Exception as error:

                print(
                    f"[{match_id}] "
                    f"Lineup send failed: {error}"
                )

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

            try:

                send_long_message(
                    message
                )

                match_state[
                    "started"
                ] = True

            except Exception as error:

                print(
                    f"[{match_id}] "
                    f"Start message failed: {error}"
                )

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

            try:

                send_long_message(
                    message
                )

                match_state[
                    "half_time"
                ] = True

            except Exception as error:

                print(
                    f"[{match_id}] "
                    f"Half-time message failed: {error}"
                )

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

            final_score = get_current_score(
                match_state
            )

            if (
                final_score.get("home", 0) == 0
                and final_score.get("away", 0) == 0
                and snapshot.get("score")
            ):

                final_score = snapshot.get(
                    "score"
                )

            # -------------------------------------------------
            # پیام اول
            # -------------------------------------------------

            final_lineup_message = (
                build_final_lineup_rich_message(
                    snapshot,
                    events,
                )
            )

            lineup_sent = False

            if final_lineup_message:

                try:

                    response = send_rich_message(
                        final_lineup_message
                    )

                    lineup_sent = (
                        isinstance(
                            response,
                            dict,
                        )
                        and response.get(
                            "ok"
                        ) is True
                    )

                except Exception as error:

                    print(
                        f"[{match_id}] "
                        f"Final lineup send failed: {error}"
                    )

            # -------------------------------------------------
            # پیام دوم
            # -------------------------------------------------

            print(
                f"[{match_id}] "
                "Sending final stats rich message."
            )

            final_stats_message = (
                build_final_stats_rich_message(
                    snapshot,
                    final_score,
                )
            )

            stats_sent = False

            if final_stats_message:

                try:

                    response = send_rich_message(
                        final_stats_message
                    )

                    stats_sent = (
                        isinstance(
                            response,
                            dict,
                        )
                        and response.get(
                            "ok"
                        ) is True
                    )

                except Exception as error:

                    print(
                        f"[{match_id}] "
                        f"Final stats send failed: {error}"
                    )

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

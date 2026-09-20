import os
import time
from datetime import datetime, timezone

from fotmob import (
    is_final_result_ready,
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
    get_event_time,
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
# ابزارهای کمکی
# =========================================================

def get_telegram_message_id(response):

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

    return message_id


def get_event_key_safe(event):

    try:

        return event_key(
            event
        )

    except Exception:

        return None


# =========================================================
# آماده‌سازی اطلاعات گل
# =========================================================

def prepare_goal_info(goal_info):

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

    return goal_info


# =========================================================
# پیدا کردن اطلاعات گل مردود
# =========================================================

def get_goal_key_from_cancellation(
    cancelled_goal,
):

    if not isinstance(
        cancelled_goal,
        dict,
    ):
        return None

    for key in (
        "event_key",
        "goal_key",
        "key",
    ):

        value = cancelled_goal.get(
            key
        )

        if value is not None:
            return value

    event = cancelled_goal.get(
        "event"
    )

    if isinstance(
        event,
        dict,
    ):

        return get_event_key_safe(
            event
        )

    return None


def get_goal_event_from_cancellation(
    cancelled_goal,
):

    if not isinstance(
        cancelled_goal,
        dict,
    ):
        return None

    event = cancelled_goal.get(
        "event"
    )

    if isinstance(
        event,
        dict,
    ):
        return event

    return cancelled_goal


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

    if existing_goal is not None:

        message_id = existing_goal.get(
            "telegram_message_id"
        )

        if message_id is not None:

            print(
                "[GOAL] "
                "Goal already has Telegram message."
            )

            return True

    print()
    print(
        "[GOAL] New goal detected."
    )

    print(
        "[GOAL] Event key:",
        goal_key,
    )

    print(
        "[GOAL] Player:",
        goal_info.get(
            "player_name"
        ),
    )

    print(
        "[GOAL] Minute:",
        goal_info.get(
            "minute"
        ),
    )

    print(
        "[GOAL] Is home:",
        goal_info.get(
            "is_home"
        ),
    )

    # -----------------------------------------------------
    # ذخیره گل در state
    # -----------------------------------------------------

    add_goal(
        match_state,
        goal_info,
    )

    score = get_current_score(
        match_state
    )

    message = build_goal_message(
        snapshot,
        event,
        score,
    )

    if not message:

        print(
            "[GOAL] "
            "Could not build Telegram message."
        )

        return False

    try:

        telegram_started_at = time.monotonic()

        print(
            "[GOAL] "
            "Sending Telegram message..."
        )

        response = send_telegram(
            message
        )

        telegram_finished_at = time.monotonic()

        print(
            "[GOAL] Timing: Telegram send =",
            f"{telegram_finished_at - telegram_started_at:.2f}s",
        )

        message_id = get_telegram_message_id(
            response
        )

        if message_id is None:

            print(
                "[GOAL] "
                "Telegram response did not contain "
                "a valid message_id."
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

    print()
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
    # merge اطلاعات جدید داخل state
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

    needs_update = bool(
        existing_goal.get(
            "needs_update",
            False,
        )
    )

    if not needs_update:
        return False

    score = get_current_score(
        match_state
    )

    rich_message = build_goal_message(
        snapshot,
        event,
        score,
    )

    if not rich_message:
        return False

    rich_message_payload = {
        "markdown": rich_message,
    }

    try:

        telegram_started_at = time.monotonic()

        print(
            "[GOAL UPDATE] "
            "Editing Telegram message..."
        )

        response = edit_rich_message(
            message_id,
            rich_message_payload,
        )

        telegram_finished_at = time.monotonic()

        print(
            "[GOAL UPDATE] "
            "Timing: Telegram edit =",
            f"{telegram_finished_at - telegram_started_at:.2f}s",
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
    # همه eventهای جدید را با ترتیب زمانی خودشان پردازش کن.
    #
    # قبلاً ابتدا همه گل‌ها و بعد همه کارت‌های قرمز پردازش
    # می‌شدند؛ در نتیجه اگر کارت قرمز دقیقه 6 و گل دقیقه 26
    # در یک اجرا پیدا می‌شدند، کارت قرمز بعد از گل ارسال می‌شد.
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

    goal_infos_by_key = {}

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

        if goal_key is not None:
            goal_infos_by_key[
                str(goal_key)
            ] = goal_info

    red_cards_by_key = {}

    for red_card in (
        changes.get(
            "red_cards",
            []
        )
    ):

        if not isinstance(
            red_card,
            dict,
        ):
            continue

        red_card_key = get_event_key_safe(
            red_card
        )

        if red_card_key is not None:
            red_cards_by_key[
                str(red_card_key)
            ] = red_card

    new_events = []

    for index, event in enumerate(
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

        key = str(key)

        if key in previous_keys:
            continue

        new_events.append(
            (
                index,
                event,
                key,
            )
        )

    def event_sort_key(item):

        index, event, key = item

        event_time = get_event_time(
            event
        )

        if event_time is None:
            event_time = float(
                "inf"
            )

        return (
            event_time,
            index,
        )

    new_events.sort(
        key=event_sort_key
    )

    for index, event, key in new_events:

        # -------------------------------------------------
        # گل
        # -------------------------------------------------

        goal_info = goal_infos_by_key.get(
            key
        )

        if goal_info is not None:

            process_new_goal(
                snapshot,
                match_state,
                goal_info,
            )

            continue

        # -------------------------------------------------
        # کارت قرمز
        # -------------------------------------------------

        red_card = red_cards_by_key.get(
            key
        )

        if red_card is not None:

            score = get_current_score(
                match_state
            )

            message = build_red_card_message(
                snapshot,
                red_card,
                score,
            )

            if not message:
                continue

            try:

                telegram_started_at = (
                    time.monotonic()
                )

                send_long_message(
                    message
                )

                telegram_finished_at = (
                    time.monotonic()
                )

                print(
                    "[RED CARD] "
                    "Timing: Telegram send =",
                    f"{telegram_finished_at - telegram_started_at:.2f}s",
                )

                add_event_keys(
                    match_state,
                    [
                        key
                    ],
                )

                previous_keys.add(
                    key
                )

            except Exception as error:

                print(
                    "[RED CARD] "
                    f"Send failed: {error}"
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

                telegram_started_at = (
                    time.monotonic()
                )

                send_long_message(
                    message
                )

                telegram_finished_at = (
                    time.monotonic()
                )

                print(
                    "[CANCELLED GOAL] "
                    "Timing: Telegram send =",
                    f"{telegram_finished_at - telegram_started_at:.2f}s",
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

    process_started_at = time.monotonic()

    process_started_iso = (
        datetime.now(
            timezone.utc
        ).isoformat()
    )

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
            f"[{match_id}] "
            "Match URL not found."
        )

        return

    print()
    print(
        f"[{match_id}] "
        "Processing started at UTC:",
        process_started_iso,
    )

    print(
        f"[{match_id}] "
        "GitHub run:",
        os.getenv(
            "GITHUB_RUN_ID",
            "unknown",
        ),
    )

    match_state = get_match_state(
        state,
        match_id,
    )

    # -----------------------------------------------------
    # snapshot
    # -----------------------------------------------------

    snapshot_started_at = time.monotonic()

    snapshot = get_match_snapshot(
        match_url
    )

    snapshot_finished_at = time.monotonic()

    print(
        f"[{match_id}] "
        "Timing: snapshot fetch =",
        f"{snapshot_finished_at - snapshot_started_at:.2f}s",
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

                telegram_started_at = (
                    time.monotonic()
                )

                response = send_rich_message(
                    rich_message
                )

                telegram_finished_at = (
                    time.monotonic()
                )

                print(
                    f"[{match_id}] "
                    "Timing: lineup Telegram send =",
                    f"{telegram_finished_at - telegram_started_at:.2f}s",
                )

                if (
                    isinstance(
                        response,
                        dict,
                    )
                    and response.get(
                        "ok"
                    ) is True
                ):

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

    events_started_at = time.monotonic()

    events = get_match_events(
        match_url
    )

    events_finished_at = time.monotonic()

    print(
        f"[{match_id}] "
        f"Events found: {len(events)}"
    )

    print(
        f"[{match_id}] "
        "Timing: events fetch =",
        f"{events_finished_at - events_started_at:.2f}s",
    )

    snapshot[
        "events"
    ] = events

    # -----------------------------------------------------
    # تشخیص تغییرات
    # -----------------------------------------------------

    detect_started_at = time.monotonic()

    changes = detect_state_changes(
        match_state,
        events,
        snapshot,
    )

    detect_finished_at = time.monotonic()

    print(
        f"[{match_id}] "
        "Timing: event detection =",
        f"{detect_finished_at - detect_started_at:.2f}s",
    )

    print(
        f"[{match_id}] "
        "Changes:",
        "goals=",
        len(
            changes.get(
                "goals",
                [],
            )
        ),
        "updated_goals=",
        len(
            changes.get(
                "updated_goals",
                [],
            )
        ),
        "events=",
        len(
            changes.get(
                "events",
                [],
            )
        ),
        "red_cards=",
        len(
            changes.get(
                "red_cards",
                [],
            )
        ),
        "cancelled_goals=",
        len(
            changes.get(
                "cancelled_goals",
                [],
            )
        ),
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

                telegram_started_at = (
                    time.monotonic()
                )

                send_long_message(
                    message
                )

                telegram_finished_at = (
                    time.monotonic()
                )

                print(
                    f"[{match_id}] "
                    "Timing: start Telegram send =",
                    f"{telegram_finished_at - telegram_started_at:.2f}s",
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
            score.get(
                "home",
                0,
            ) == 0
            and score.get(
                "away",
                0,
            ) == 0
            and snapshot.get(
                "score"
            )
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

                telegram_started_at = (
                    time.monotonic()
                )

                send_long_message(
                    message
                )

                telegram_finished_at = (
                    time.monotonic()
                )

                print(
                    f"[{match_id}] "
                    "Timing: half-time Telegram send =",
                    f"{telegram_finished_at - telegram_started_at:.2f}s",
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

    live_events_started_at = time.monotonic()

    process_live_events(
        snapshot,
        match_state,
        changes,
    )

    live_events_finished_at = time.monotonic()

    print(
        f"[{match_id}] "
        "Timing: live event processing =",
        f"{live_events_finished_at - live_events_started_at:.2f}s",
    )

    # -----------------------------------------------------
    # پایان بازی
    # -----------------------------------------------------

    if is_final_result_ready(snapshot):

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
                final_score.get(
                    "home",
                    0,
                ) == 0
                and final_score.get(
                    "away",
                    0,
                ) == 0
                and snapshot.get(
                    "score"
                )
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

                    telegram_started_at = (
                        time.monotonic()
                    )

                    response = send_rich_message(
                        final_lineup_message
                    )

                    telegram_finished_at = (
                        time.monotonic()
                    )

                    print(
                        f"[{match_id}] "
                        "Timing: final lineup Telegram send =",
                        f"{telegram_finished_at - telegram_started_at:.2f}s",
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

                    telegram_started_at = (
                        time.monotonic()
                    )

                    response = send_rich_message(
                        final_stats_message
                    )

                    telegram_finished_at = (
                        time.monotonic()
                    )

                    print(
                        f"[{match_id}] "
                        "Timing: final stats Telegram send =",
                        f"{telegram_finished_at - telegram_started_at:.2f}s",
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

    process_finished_at = time.monotonic()

    print(
        f"[{match_id}] "
        "Total process_match duration =",
        f"{process_finished_at - process_started_at:.2f}s",
    )


# =========================================================
# main
# =========================================================

def main():

    run_started_at = time.monotonic()

    print()
    print(
        "========================================"
    )

    print(
        "[RUN] Started at UTC:",
        datetime.now(
            timezone.utc
        ).isoformat(),
    )

    print(
        "[RUN] GitHub run:",
        os.getenv(
            "GITHUB_RUN_ID",
            "unknown",
        ),
    )

    print(
        "[RUN] GitHub run attempt:",
        os.getenv(
            "GITHUB_RUN_ATTEMPT",
            "unknown",
        ),
    )

    print(
        "========================================"
    )

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

        match_started_at = time.monotonic()

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

        match_finished_at = time.monotonic()

        match_id = get_match_id(
            match
        )

        print(
            f"[{match_id}] "
            "Total match loop duration =",
            f"{match_finished_at - match_started_at:.2f}s",
        )

    save_started_at = time.monotonic()

    save_state(
        state
    )

    save_finished_at = time.monotonic()

    print(
        "[RUN] Timing: save_state =",
        f"{save_finished_at - save_started_at:.2f}s",
    )

    run_finished_at = time.monotonic()

    print(
        "[RUN] Finished at UTC:",
        datetime.now(
            timezone.utc
        ).isoformat(),
    )

    print(
        "[RUN] Total duration:",
        f"{run_finished_at - run_started_at:.2f}s",
    )

    print(
        "========================================"
    )


# =========================================================
# اجرا
# =========================================================

if __name__ == "__main__":

    main()

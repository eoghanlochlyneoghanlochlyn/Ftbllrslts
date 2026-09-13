import time

from fotmob import (
    get_match_snapshot,
    get_match_events,
)

from match_manager import (
    load_matches,
    get_match_id,
    get_match_url,
    get_enabled_matches,
)

from state_manager import (
    load_state,
    save_state,
    get_match_state,
    update_match_state,
    add_event_keys,
    add_goal,
    find_goal,
    cancel_goal,
    get_current_score,
)

from event_detector import (
    detect_state_changes,
    get_event_unique_id,
    event_key,
)

from formatter import (
    build_lineup_message,
    build_start_message,
    build_goal_message,
    build_cancelled_goal_message,
    build_half_time_message,
    build_red_card_message,
    build_event_message,
)

from telegram_sender import send_long_message


# ---------------------------------------------------------
# تنظیمات
# ---------------------------------------------------------

POLL_INTERVAL = 60


# ---------------------------------------------------------
# ابزارهای کمکی
# ---------------------------------------------------------

def get_goal_key_from_cancellation(cancelled_goal):
    """
    کلید گل لغوشده را از اطلاعات VAR استخراج می‌کند.
    """
    if not isinstance(cancelled_goal, dict):
        return None

    return (
        cancelled_goal.get("goal_key")
        or cancelled_goal.get("event_key")
        or cancelled_goal.get("id")
    )


def get_goal_event_from_cancellation(cancelled_goal):
    """
    خود event مربوط به گل لغوشده را استخراج می‌کند.
    """
    if not isinstance(cancelled_goal, dict):
        return None

    return cancelled_goal.get("goal_event")


def is_same_event_key(event, key):
    """
    بررسی می‌کند آیا event همان کلید مشخص‌شده را دارد یا نه.
    """
    if event is None or key is None:
        return False

    try:
        return event_key(event) == str(key)
    except Exception:
        return False


def get_event_key_safe(event):
    """
    گرفتن event key بدون اینکه خراب شدن یک event کل پردازش را متوقف کند.
    """
    try:
        return event_key(event)
    except Exception:
        return None


def get_goal_score_before_event(match_state, goal_info):
    """
    نتیجه را تا قبل از این گل محاسبه می‌کند.

    هدف:
    اگر گل اول بازی در دقیقه 68 باشد، نتیجه پیام باید 0-1 باشد،
    نه نتیجه نهایی 1-1.
    """

    goals = match_state.get("goals", [])

    home_score = 0
    away_score = 0

    target_key = goal_info.get("event_key")

    for goal in goals:
        if not isinstance(goal, dict):
            continue

        if goal.get("cancelled", False):
            continue

        # خود گل فعلی را در محاسبه لحاظ نکن
        if target_key is not None:
            if str(goal.get("event_key")) == str(target_key):
                continue

        is_home = goal.get("is_home")

        if is_home is None:
            continue

        own_goal = bool(goal.get("own_goal", False))

        if own_goal:
            if is_home:
                away_score += 1
            else:
                home_score += 1
        else:
            if is_home:
                home_score += 1
            else:
                away_score += 1

    return {
        "home": home_score,
        "away": away_score,
    }


def get_goal_score_after_event(match_state, goal_info):
    """
    نتیجه بعد از ثبت گل را برمی‌گرداند.
    """

    score = get_goal_score_before_event(match_state, goal_info)

    is_home = goal_info.get("is_home")

    if is_home is None:
        return score

    own_goal = bool(goal_info.get("own_goal", False))

    if own_goal:
        if is_home:
            score["away"] += 1
        else:
            score["home"] += 1
    else:
        if is_home:
            score["home"] += 1
        else:
            score["away"] += 1

    return score


# ---------------------------------------------------------
# پردازش رویدادهای زنده
# ---------------------------------------------------------

def process_live_events(
    match_id,
    snapshot,
    match_state,
    changes,
):
    """
    رویدادهای جدید بازی را پردازش می‌کند.
    """

    new_events = changes.get("new_events", [])
    new_goal_info = changes.get("new_goal_info", [])
    cancelled_goals = changes.get("cancelled_goals", [])
    new_red_cards = changes.get("new_red_cards", [])

    # -----------------------------------------------------
    # کلید گل‌هایی که همین بررسی لغو شده‌اند
    # -----------------------------------------------------

    cancelled_goal_keys = set()

    for cancelled_goal in cancelled_goals:
        key = get_goal_key_from_cancellation(cancelled_goal)

        if key is not None:
            cancelled_goal_keys.add(str(key))

    # -----------------------------------------------------
    # ثبت گل‌های جدید
    #
    # نکته:
    # قبل از ثبت، کلیدهای قبلی را نگه می‌داریم تا بفهمیم
    # کدام گل واقعاً برای اولین بار وارد state شده.
    # -----------------------------------------------------

    previous_goal_keys = {
        str(goal.get("event_key"))
        for goal in match_state.get("goals", [])
        if isinstance(goal, dict)
        and goal.get("event_key") is not None
    }

    newly_added_goals = []

    for goal_info in new_goal_info:
        if not isinstance(goal_info, dict):
            continue

        goal_key = goal_info.get("event_key")

        if goal_key is None:
            continue

        goal_key = str(goal_key)

        existing_goal = find_goal(match_state, goal_key)

        if existing_goal is None:
            added_goal = add_goal(match_state, goal_info)

            if added_goal is not None:
                newly_added_goals.append(goal_info)

        elif goal_key not in previous_goal_keys:
            newly_added_goals.append(goal_info)

    # -----------------------------------------------------
    # اعمال لغو گل‌ها
    # -----------------------------------------------------

    for cancelled_goal in cancelled_goals:
        goal_key = get_goal_key_from_cancellation(cancelled_goal)

        if goal_key is None:
            continue

        cancel_goal(match_state, str(goal_key))

    # -----------------------------------------------------
    # گل‌های جدید
    # -----------------------------------------------------

    sent_goal_keys = set()

    for goal_info in newly_added_goals:

        goal_key = goal_info.get("event_key")

        if goal_key is None:
            continue

        goal_key = str(goal_key)

        # اگر همین الان توسط VAR لغو شده، پیام گل معمولی نفرست
        if goal_key in cancelled_goal_keys:
            continue

        # جلوگیری از ارسال دوباره
        if goal_key in sent_goal_keys:
            continue

        # ---------------------------------------------
        # نتیجه قبل از گل
        # ---------------------------------------------

        score_before = get_goal_score_before_event(
            match_state,
            goal_info,
        )

        # ---------------------------------------------
        # نتیجه بعد از گل
        # ---------------------------------------------

        score_after = get_goal_score_after_event(
            match_state,
            goal_info,
        )

        event = goal_info.get("event")

        if event is None:
            continue

        print(f"[{match_id}] New goal detected.")

        message = build_goal_message(
            snapshot,
            event,
            score=score_after,
        )

        if message:
            send_long_message(message)

        sent_goal_keys.add(goal_key)

    # -----------------------------------------------------
    # VAR / گل‌های لغوشده
    # -----------------------------------------------------

    sent_cancelled_keys = set()

    for cancelled_goal in cancelled_goals:

        goal_key = get_goal_key_from_cancellation(cancelled_goal)

        if goal_key is None:
            continue

        goal_key = str(goal_key)

        if goal_key in sent_cancelled_keys:
            continue

        saved_goal = find_goal(match_state, goal_key)

        goal_event = get_goal_event_from_cancellation(
            cancelled_goal
        )

        # اگر event از detector موجود نبود، از state استفاده کن
        if goal_event is None and saved_goal is not None:
            goal_event = saved_goal.get("event")

        if goal_event is None:
            continue

        # -------------------------------------------------
        # نتیجه بعد از حذف گل
        # -------------------------------------------------

        score = get_current_score(match_state)

        print(f"[{match_id}] Cancelled goal detected.")

        cancellation_data = {
            "goal_event": goal_event,
            "goal_key": goal_key,
            "minute": (
                cancelled_goal.get("minute")
                if isinstance(cancelled_goal, dict)
                else None
            ),
            "is_home": (
                cancelled_goal.get("is_home")
                if isinstance(cancelled_goal, dict)
                else None
            ),
        }

        message = build_cancelled_goal_message(
            snapshot,
            cancellation_data,
            score=score,
        )

        if message:
            send_long_message(message)

        sent_cancelled_keys.add(goal_key)

    # -----------------------------------------------------
    # کارت قرمز
    # -----------------------------------------------------

    handled_red_card_keys = set()

    for red_card in new_red_cards:

        red_key = get_event_key_safe(red_card)

        if red_key is None:
            continue

        red_key = str(red_key)

        if red_key in handled_red_card_keys:
            continue

        print(f"[{match_id}] New red card detected.")

        message = build_red_card_message(
            snapshot,
            red_card,
        )

        if message:
            send_long_message(message)

        handled_red_card_keys.add(red_key)

    # -----------------------------------------------------
    # رویدادهای عمومی
    #
    # اینجا باید گل‌ها، VAR و کارت قرمز را حذف کنیم تا
    # دوباره ارسال نشوند.
    # -----------------------------------------------------

    handled_event_keys = set()

    # گل‌هایی که در همین poll پردازش شدند
    for goal_info in new_goal_info:
        if not isinstance(goal_info, dict):
            continue

        key = goal_info.get("event_key")

        if key is not None:
            handled_event_keys.add(str(key))

    # گل‌هایی که VAR آن‌ها را لغو کرده
    for cancelled_goal in cancelled_goals:
        key = get_goal_key_from_cancellation(cancelled_goal)

        if key is not None:
            handled_event_keys.add(str(key))

        var_event = cancelled_goal.get("var_event")

        if var_event is not None:
            var_key = get_event_key_safe(var_event)

            if var_key is not None:
                handled_event_keys.add(str(var_key))

    # کارت قرمز
    for red_card in new_red_cards:
        key = get_event_key_safe(red_card)

        if key is not None:
            handled_event_keys.add(str(key))

    # -----------------------------------------------------
    # ارسال سایر eventها
    # -----------------------------------------------------

    for event in new_events:

        key = get_event_key_safe(event)

        if key is not None:
            key = str(key)

            if key in handled_event_keys:
                continue

        # اگر event مربوط به گل است، قبلاً پردازش شده
        event_type = str(
            event.get("type", "")
        ).lower()

        if event_type == "goal":
            continue

        # اگر VAR است، قبلاً در بخش VAR پردازش شده
        if event_type == "var":
            continue

        # اگر کارت قرمز است، قبلاً پردازش شده
        if event_type == "card":

            card_type = str(
                event.get("card", "")
            ).lower()

            if card_type in {
                "red",
                "redcard",
                "red_card",
            }:
                continue

        print(f"[{match_id}] New event detected.")

        message = build_event_message(
            snapshot,
            event,
        )

        if message:
            send_long_message(message)


# ---------------------------------------------------------
# پردازش یک مسابقه
# ---------------------------------------------------------

def process_match(match, state):
    match_id = get_match_id(match)

    if match_id is None:
        print("Match ID not found.")
        return

    match_id = str(match_id)

    match_url = get_match_url(match)

    if not match_url:
        print(f"[{match_id}] Match URL not found.")
        return

    # -----------------------------------------------------
    # دریافت اطلاعات بازی
    # -----------------------------------------------------

    snapshot = get_match_snapshot(match_url)

    if not snapshot:
        print(f"[{match_id}] Could not get match snapshot.")
        return

    print(f"FotMob {match_id}: HTTP 200")
    print()

    home_name = snapshot.get(
        "home_team",
        "Home",
    )

    away_name = snapshot.get(
        "away_team",
        "Away",
    )

    lineup_type = snapshot.get(
        "lineup_type"
    )

    home_starters = snapshot.get(
        "home_starters",
        []
    )

    away_starters = snapshot.get(
        "away_starters",
        []
    )

    started = bool(
        snapshot.get("started", False)
    )

    half_time = bool(
        snapshot.get("half_time", False)
    )

    finished = bool(
        snapshot.get("finished", False)
    )

    print(f"{home_name} vs {away_name}")
    print()
    print(f"Lineup type: {lineup_type}")
    print(
        f"Starters: "
        f"{len(home_starters)} / "
        f"{len(away_starters)}"
    )
    print(f"Started: {started}")
    print(f"Half time: {half_time}")
    print(f"Finished: {finished}")
    print()

    # -----------------------------------------------------
    # state مربوط به همین مسابقه
    # -----------------------------------------------------

    match_state = get_match_state(
        state,
        match_id,
    )

    # -----------------------------------------------------
    # ترکیب
    # -----------------------------------------------------

    has_lineup = (
        lineup_type in {
            "standard",
            "confirmed",
        }
        and len(home_starters) == 11
        and len(away_starters) == 11
    )

    if has_lineup and not match_state.get(
        "lineup_sent",
        False,
    ):

        print(
            f"[{match_id}] "
            f"Sending lineup message."
        )

        message = build_lineup_message(
            snapshot
        )

        if message:
            send_long_message(message)

        match_state["lineup_sent"] = True

    # -----------------------------------------------------
    # دریافت eventهای فعلی
    # -----------------------------------------------------

    events = get_match_events(
        match_url
    )

    if events is None:
        events = []

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

    current_started = bool(
        changes.get(
            "current_started",
            started,
        )
    )

    if (
        current_started
        and not match_state.get(
            "started",
            False,
        )
    ):

        print(
            f"[{match_id}] Match started."
        )

        message = build_start_message(
            snapshot
        )

        if message:
            send_long_message(message)

        match_state["started"] = True

    # -----------------------------------------------------
    # نیمه
    # -----------------------------------------------------

    current_half_time = bool(
        changes.get(
            "current_half_time",
            half_time,
        )
    )

    if (
        current_half_time
        and not match_state.get(
            "half_time",
            False,
        )
    ):

        print(
            f"[{match_id}] "
            f"Half time detected."
        )

        message = build_half_time_message(
            snapshot
        )

        if message:
            send_long_message(message)

        match_state["half_time"] = True

    # -----------------------------------------------------
    # پردازش eventها
    # -----------------------------------------------------

    process_live_events(
        match_id,
        snapshot,
        match_state,
        changes,
    )

    # -----------------------------------------------------
    # پایان بازی
    # -----------------------------------------------------

    current_finished = bool(
        changes.get(
            "current_finished",
            finished,
        )
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
            f"Final message sent."
        )

        message = build_lineup_message(
            snapshot,
            include_ratings=True,
        )

        if message:
            send_long_message(message)

        match_state["finished"] = True
        match_state["finished_sent"] = True

        score = get_current_score(
            match_state
        )

        print(
            f"[{match_id}] "
            f"Current score: "
            f"{score.get('home', 0)} - "
            f"{score.get('away', 0)}"
        )

    # -----------------------------------------------------
    # ذخیره event keyهای فعلی
    # -----------------------------------------------------

    current_event_keys = changes.get(
        "current_event_keys",
        [],
    )

    add_event_keys(
        match_state,
        current_event_keys,
    )

    # -----------------------------------------------------
    # ذخیره وضعیت
    # -----------------------------------------------------

    state["matches"][match_id] = match_state


# ---------------------------------------------------------
# اجرای اصلی
# ---------------------------------------------------------

def main():

    matches = load_matches()

    enabled_matches = get_enabled_matches(
        matches
    )

    if not enabled_matches:
        print("No enabled matches found.")
        return

    state = load_state()

    for match in enabled_matches:

        try:

            process_match(
                match,
                state,
            )

        except Exception as error:

            match_id = get_match_id(match)

            print(
                f"[{match_id}] "
                f"Error: {error}"
            )

    save_state(state)


if __name__ == "__main__":
    main()

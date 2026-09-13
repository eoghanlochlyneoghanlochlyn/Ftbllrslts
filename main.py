import json
import os


STATE_FILE = "state.json"


def default_state():
    return {
        "matches": {}
    }


def default_match_state():
    return {
        "lineup_sent": False,
        "fallback_sent": False,
        "started": False,
        "half_time": False,
        "finished": False,
        "finished_sent": False,
        "event_keys": [],
        "goals": [],
    }


def load_state():
    if not os.path.exists(STATE_FILE):
        return default_state()

    try:

        with open(
            STATE_FILE,
            "r",
            encoding="utf-8",
        ) as file:

            data = json.load(file)

        if not isinstance(data, dict):
            return default_state()

        if not isinstance(
            data.get("matches"),
            dict,
        ):
            data["matches"] = {}

        # --------------------------------------------------------
        # تکمیل وضعیت مسابقه‌های قدیمی
        # --------------------------------------------------------

        for match_id, match_state in data["matches"].items():

            if not isinstance(match_state, dict):
                data["matches"][match_id] = (
                    default_match_state()
                )
                continue

            defaults = default_match_state()

            for key, value in defaults.items():

                if key not in match_state:
                    match_state[key] = value

            # اطمینان از نوع درست داده‌ها

            if not isinstance(
                match_state.get("event_keys"),
                list,
            ):
                match_state["event_keys"] = []

            if not isinstance(
                match_state.get("goals"),
                list,
            ):
                match_state["goals"] = []

        return data

    except (
        json.JSONDecodeError,
        OSError,
    ):
        return default_state()


def save_state(state):
    temporary_file = (
        STATE_FILE + ".tmp"
    )

    with open(
        temporary_file,
        "w",
        encoding="utf-8",
    ) as file:

        json.dump(
            state,
            file,
            ensure_ascii=False,
            indent=2,
        )

    os.replace(
        temporary_file,
        STATE_FILE,
    )


def get_match_state(state, match_id):
    match_id = str(match_id)

    matches = state.setdefault(
        "matches",
        {},
    )

    if match_id not in matches:

        matches[match_id] = (
            default_match_state()
        )

    match_state = matches[match_id]

    # --------------------------------------------------------
    # اگر state قدیمی باشد، فیلدهای جدید اضافه می‌شوند
    # --------------------------------------------------------

    defaults = default_match_state()

    for key, value in defaults.items():

        if key not in match_state:
            match_state[key] = value

    if not isinstance(
        match_state.get("event_keys"),
        list,
    ):
        match_state["event_keys"] = []

    if not isinstance(
        match_state.get("goals"),
        list,
    ):
        match_state["goals"] = []

    return match_state


def update_match_state(
    state,
    match_id,
    **updates,
):
    match_state = get_match_state(
        state,
        match_id,
    )

    match_state.update(updates)

    return match_state


# ============================================================
# Event helpers
# ============================================================

def has_event(
    state,
    match_id,
    event_key,
):
    match_state = get_match_state(
        state,
        match_id,
    )

    return event_key in match_state["event_keys"]


def add_event_keys(
    state,
    match_id,
    event_keys,
):
    match_state = get_match_state(
        state,
        match_id,
    )

    existing = set(
        match_state["event_keys"]
    )

    for key in event_keys:

        if key is None:
            continue

        if key not in existing:

            match_state["event_keys"].append(
                key
            )

            existing.add(key)

    return match_state


# ============================================================
# Goal helpers
# ============================================================

def _goal_key(goal):
    if not isinstance(goal, dict):
        return None

    return (
        goal.get("key")
        or goal.get("event_key")
        or goal.get("id")
    )


def find_goal(
    state,
    match_id,
    goal_key,
):
    match_state = get_match_state(
        state,
        match_id,
    )

    for goal in match_state["goals"]:

        if _goal_key(goal) == goal_key:
            return goal

    return None


def add_goal(
    state,
    match_id,
    goal,
):
    if not isinstance(goal, dict):
        return None

    match_state = get_match_state(
        state,
        match_id,
    )

    goal_key = _goal_key(goal)

    if goal_key is not None:

        existing = find_goal(
            state,
            match_id,
            goal_key,
        )

        if existing is not None:
            return existing

    goal_copy = dict(goal)

    if "cancelled" not in goal_copy:
        goal_copy["cancelled"] = False

    match_state["goals"].append(
        goal_copy
    )

    return goal_copy


def cancel_goal(
    state,
    match_id,
    goal_key=None,
    goal=None,
):
    match_state = get_match_state(
        state,
        match_id,
    )

    target = None

    if goal_key is not None:

        target = find_goal(
            state,
            match_id,
            goal_key,
        )

    if target is None and isinstance(
        goal,
        dict,
    ):

        # اگر کلید مستقیم پیدا نشد،
        # بر اساس شناسه/بازیکن/دقیقه/تیم
        # تلاش می‌کنیم گل قبلی را پیدا کنیم.

        goal_id = _goal_key(goal)

        if goal_id is not None:

            target = find_goal(
                state,
                match_id,
                goal_id,
            )

        if target is None:

            player_id = goal.get(
                "player_id"
            )

            team_id = goal.get(
                "team_id"
            )

            minute = goal.get(
                "minute"
            )

            for saved_goal in match_state[
                "goals"
            ]:

                if saved_goal.get(
                    "cancelled",
                    False,
                ):
                    continue

                if (
                    player_id is not None
                    and saved_goal.get(
                        "player_id"
                    ) != player_id
                ):
                    continue

                if (
                    team_id is not None
                    and saved_goal.get(
                        "team_id"
                    ) != team_id
                ):
                    continue

                if (
                    minute is not None
                    and saved_goal.get(
                        "minute"
                    ) != minute
                ):
                    continue

                target = saved_goal
                break

    if target is None:
        return None

    target["cancelled"] = True

    return target


def is_goal_cancelled(goal):
    if not isinstance(goal, dict):
        return False

    return bool(
        goal.get("cancelled", False)
    )


def get_valid_goals(
    state,
    match_id,
):
    match_state = get_match_state(
        state,
        match_id,
    )

    return [
        goal
        for goal in match_state["goals"]
        if not is_goal_cancelled(goal)
    ]


def get_cancelled_goals(
    state,
    match_id,
):
    match_state = get_match_state(
        state,
        match_id,
    )

    return [
        goal
        for goal in match_state["goals"]
        if is_goal_cancelled(goal)
    ]


# ============================================================
# Score calculation
# ============================================================

def get_current_score(
    state,
    match_id,
):
    match_state = get_match_state(
        state,
        match_id,
    )

    home_score = 0
    away_score = 0

    for goal in match_state["goals"]:

        if is_goal_cancelled(goal):
            continue

        is_home = goal.get(
            "is_home"
        )

        # ----------------------------------------------------
        # گل به خودی
        # ----------------------------------------------------

        if goal.get(
            "own_goal",
            False,
        ):

            if is_home is True:
                away_score += 1
            elif is_home is False:
                home_score += 1

            continue

        # ----------------------------------------------------
        # گل معمولی
        # ----------------------------------------------------

        if is_home is True:
            home_score += 1

        elif is_home is False:
            away_score += 1

    return {
        "home": home_score,
        "away": away_score,
    }


# ============================================================
# Synchronize goals with current FotMob events
# ============================================================

def sync_goals_with_current_events(
    state,
    match_id,
    goals=None,
    cancelled_goals=None,
):
    """
    گل‌های جدید را در state ثبت می‌کند و
    گل‌هایی را که بعداً مردود شده‌اند علامت می‌زند.

    این تابع عمداً گل مردودشده را حذف نمی‌کند.
    چون باید بدانیم قبلاً برای آن گل پیام ارسال شده
    تا بتوانیم بعداً پیام «گل مردود شد» بفرستیم.
    """

    if goals is None:
        goals = []

    if cancelled_goals is None:
        cancelled_goals = []

    match_state = get_match_state(
        state,
        match_id,
    )

    added_goals = []
    newly_cancelled = []

    # --------------------------------------------------------
    # ثبت گل‌های جدید
    # --------------------------------------------------------

    for goal in goals:

        if not isinstance(goal, dict):
            continue

        goal_key = _goal_key(goal)

        existing = None

        if goal_key is not None:

            existing = find_goal(
                state,
                match_id,
                goal_key,
            )

        if existing is None:

            saved_goal = add_goal(
                state,
                match_id,
                goal,
            )

            if saved_goal is not None:
                added_goals.append(
                    saved_goal
                )

    # --------------------------------------------------------
    # ثبت گل‌های مردودشده
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

        target = None

        # ابتدا با کلید دقیق جست‌وجو می‌کنیم.

        if goal_key is not None:

            target = find_goal(
                state,
                match_id,
                goal_key,
            )

        # ----------------------------------------------------
        # اگر کلید متفاوت بود، بر اساس اطلاعات گل
        # تلاش می‌کنیم گل قبلی را پیدا کنیم.
        # ----------------------------------------------------

        if target is None:

            player_id = (
                cancelled_goal.get(
                    "player_id"
                )
            )

            team_id = (
                cancelled_goal.get(
                    "team_id"
                )
            )

            minute = (
                cancelled_goal.get(
                    "minute"
                )
            )

            for saved_goal in match_state[
                "goals"
            ]:

                if is_goal_cancelled(
                    saved_goal
                ):
                    continue

                if (
                    player_id is not None
                    and saved_goal.get(
                        "player_id"
                    ) != player_id
                ):
                    continue

                if (
                    team_id is not None
                    and saved_goal.get(
                        "team_id"
                    ) != team_id
                ):
                    continue

                if (
                    minute is not None
                    and saved_goal.get(
                        "minute"
                    ) != minute
                ):
                    continue

                target = saved_goal
                break

        if target is None:
            continue

        if not is_goal_cancelled(
            target
        ):

            target["cancelled"] = True

            newly_cancelled.append(
                target
            )

    return {
        "added_goals": added_goals,
        "newly_cancelled": newly_cancelled,
        "score": get_current_score(
            state,
            match_id,
        ),
    }


# ============================================================
# Optional cleanup
# ============================================================

def remove_old_match(
    state,
    match_id,
):
    match_id = str(match_id)

    matches = state.setdefault(
        "matches",
        {},
    )

    if match_id in matches:
        del matches[match_id]

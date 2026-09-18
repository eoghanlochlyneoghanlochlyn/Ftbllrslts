import json
import os


STATE_FILE = "state.json"


# ============================================================
# وضعیت پیش‌فرض
# ============================================================

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


# ============================================================
# بارگذاری و ذخیره state
# ============================================================

def load_state():

    if not os.path.exists(
        STATE_FILE
    ):
        return default_state()

    try:

        with open(
            STATE_FILE,
            "r",
            encoding="utf-8",
        ) as file:

            state = json.load(
                file
            )

    except (
        json.JSONDecodeError,
        OSError,
        TypeError,
    ):

        return default_state()

    if not isinstance(
        state,
        dict,
    ):
        return default_state()

    if not isinstance(
        state.get("matches"),
        dict,
    ):

        state["matches"] = {}

    return state


def save_state(state):

    temp_file = (
        STATE_FILE
        + ".tmp"
    )

    try:

        with open(
            temp_file,
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
            temp_file,
            STATE_FILE,
        )

    except OSError:

        if os.path.exists(
            temp_file
        ):

            try:
                os.remove(
                    temp_file
                )

            except OSError:
                pass

        raise


# ============================================================
# وضعیت مسابقه
# ============================================================

def get_match_state(
    state,
    match_id,
):

    match_id = str(
        match_id
    )

    matches = state.setdefault(
        "matches",
        {},
    )

    if match_id not in matches:

        matches[
            match_id
        ] = default_match_state()

    match_state = matches[
        match_id
    ]

    if not isinstance(
        match_state,
        dict,
    ):

        match_state = (
            default_match_state()
        )

        matches[
            match_id
        ] = match_state

    defaults = (
        default_match_state()
    )

    for key, value in defaults.items():

        if key not in match_state:

            if isinstance(
                value,
                list,
            ):

                match_state[
                    key
                ] = []

            else:

                match_state[
                    key
                ] = value

    if not isinstance(
        match_state.get(
            "event_keys"
        ),
        list,
    ):

        match_state[
            "event_keys"
        ] = []

    if not isinstance(
        match_state.get(
            "goals"
        ),
        list,
    ):

        match_state[
            "goals"
        ] = []

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

    for key, value in updates.items():

        match_state[
            key
        ] = value

    return match_state


# ============================================================
# Eventها
# ============================================================

def has_event(
    match_state,
    event_key,
):

    if event_key is None:
        return False

    event_key = str(
        event_key
    )

    return event_key in (
        match_state.get(
            "event_keys",
            [],
        )
    )


def add_event_keys(
    match_state,
    event_keys,
):

    current = (
        match_state.setdefault(
            "event_keys",
            [],
        )
    )

    if not isinstance(
        current,
        list,
    ):

        current = []

        match_state[
            "event_keys"
        ] = current

    existing = {
        str(key)
        for key in current
    }

    for key in (
        event_keys or []
    ):

        if key is None:
            continue

        key = str(
            key
        )

        if key not in existing:

            current.append(
                key
            )

            existing.add(
                key
            )

    return match_state


# ============================================================
# گل‌ها
# ============================================================

def find_goal(
    match_state,
    goal_key,
):

    if goal_key is None:
        return None

    goal_key = str(
        goal_key
    )

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
        ) == goal_key:

            return goal

    return None


def _is_missing_player_name(
    player_name
):
    if player_name is None:
        return True

    if not isinstance(
        player_name,
        str,
    ):
        return False

    normalized = (
        player_name
        .strip()
        .lower()
    )

    return normalized in (
        "",
        "<tbd>",
        "tbd",
        "unknown",
        "unknown player",
    )


def add_goal(
    match_state,
    goal_info,
):

    if not isinstance(
        goal_info,
        dict,
    ):
        return None

    goal_key = goal_info.get(
        "event_key"
    )

    if goal_key is None:
        return None

    goal_key = str(
        goal_key
    )

    existing = find_goal(
        match_state,
        goal_key,
    )

    # --------------------------------------------------------
    # اگر گل قبلاً ثبت شده، اطلاعات جدید آن را به‌روزرسانی کن.
    #
    # این بخش برای حالتی مهم است که FotMob ابتدا گل را بدون
    # نام بازیکن برگرداند و در اجرای بعد نام واقعی را اضافه کند.
    # --------------------------------------------------------

    if existing is not None:

        new_player_id = goal_info.get(
            "player_id"
        )

        if new_player_id is not None:

            if existing.get(
                "player_id"
            ) is None:

                existing[
                    "player_id"
                ] = new_player_id

        new_assist_player_id = (
            goal_info.get(
                "assist_player_id"
            )
        )

        if new_assist_player_id is not None:

            if existing.get(
                "assist_player_id"
            ) is None:

                existing[
                    "assist_player_id"
                ] = new_assist_player_id

        new_player_name = goal_info.get(
            "player_name"
        )

        if not _is_missing_player_name(
            new_player_name
        ):

            old_player_name = existing.get(
                "player_name"
            )

            if _is_missing_player_name(
                old_player_name
            ):

                existing[
                    "player_name"
                ] = new_player_name

                existing[
                    "needs_update"
                ] = True

        new_assist_player_name = (
            goal_info.get(
                "assist_player_name"
            )
        )

        if not _is_missing_player_name(
            new_assist_player_name
        ):

            old_assist_player_name = (
                existing.get(
                    "assist_player_name"
                )
            )

            if _is_missing_player_name(
                old_assist_player_name
            ):

                existing[
                    "assist_player_name"
                ] = new_assist_player_name

        # اگر اطلاعات دیگری بعداً کامل شد، آنها را نیز
        # فقط در صورت وجود مقدار معتبر به‌روزرسانی کن.

        if (
            existing.get("minute") is None
            and goal_info.get("minute") is not None
        ):

            existing[
                "minute"
            ] = goal_info.get(
                "minute"
            )

        if (
            existing.get("is_home") is None
            and goal_info.get("is_home") is not None
        ):

            existing[
                "is_home"
            ] = goal_info.get(
                "is_home"
            )

        if goal_info.get(
            "event"
        ) is not None:

            existing[
                "event"
            ] = goal_info.get(
                "event"
            )

        return existing

    # --------------------------------------------------------
    # گل جدید
    # --------------------------------------------------------

    goal = {
        "event_key": goal_key,

        "player_id": goal_info.get(
            "player_id"
        ),

        "player_name": goal_info.get(
            "player_name"
        ),

        "assist_player_id": (
            goal_info.get(
                "assist_player_id"
            )
        ),

        "assist_player_name": (
            goal_info.get(
                "assist_player_name"
            )
        ),

        "is_home": goal_info.get(
            "is_home"
        ),

        "minute": goal_info.get(
            "minute"
        ),

        "penalty": bool(
            goal_info.get(
                "penalty",
                False,
            )
        ),

        "own_goal": bool(
            goal_info.get(
                "own_goal",
                False,
            )
        ),

        "cancelled": False,

        # شناسه پیام تلگرام را فعلاً None می‌گذاریم.
        # در مرحله telegram_sender/main مقدار واقعی آن ثبت خواهد شد.
        "telegram_message_id": None,

        # اگر نام بازیکن ناقص باشد، در اجرای بعد باید بررسی شود.
        "needs_update": _is_missing_player_name(
            goal_info.get(
                "player_name"
            )
        ),

        "event": goal_info.get(
            "event"
        ),
    }

    match_state.setdefault(
        "goals",
        [],
    ).append(
        goal
    )

    return goal


def update_goal(
    match_state,
    goal_key,
    **updates,
):

    goal = find_goal(
        match_state,
        goal_key,
    )

    if goal is None:
        return None

    for key, value in updates.items():

        if value is None:
            continue

        goal[
            key
        ] = value

    return goal


def set_goal_message_id(
    match_state,
    goal_key,
    message_id,
):

    goal = find_goal(
        match_state,
        goal_key,
    )

    if goal is None:
        return None

    if message_id is not None:

        goal[
            "telegram_message_id"
        ] = message_id

    return goal


def mark_goal_update_complete(
    match_state,
    goal_key,
):

    goal = find_goal(
        match_state,
        goal_key,
    )

    if goal is None:
        return None

    goal[
        "needs_update"
    ] = False

    return goal


def cancel_goal(
    match_state,
    goal_key,
):

    goal = find_goal(
        match_state,
        goal_key,
    )

    if goal is None:
        return False

    goal[
        "cancelled"
    ] = True

    return True


def is_goal_cancelled(
    match_state,
    goal_key,
):

    goal = find_goal(
        match_state,
        goal_key,
    )

    if goal is None:
        return False

    return bool(
        goal.get(
            "cancelled",
            False,
        )
    )


def get_valid_goals(
    match_state,
):

    return [
        goal
        for goal in (
            match_state.get(
                "goals",
                [],
            )
        )
        if (
            isinstance(
                goal,
                dict,
            )
            and not goal.get(
                "cancelled",
                False,
            )
        )
    ]


def get_cancelled_goals(
    match_state,
):

    return [
        goal
        for goal in (
            match_state.get(
                "goals",
                [],
            )
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
    ]


# ============================================================
# نتیجه فعلی بر اساس گل‌های ثبت‌شده
# ============================================================

def get_current_score(
    match_state,
):

    home_score = 0
    away_score = 0

    for goal in get_valid_goals(
        match_state
    ):

        is_home = goal.get(
            "is_home"
        )

        own_goal = bool(
            goal.get(
                "own_goal",
                False,
            )
        )

        if is_home is None:
            continue

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


# ============================================================
# هماهنگ کردن گل‌ها
# ============================================================

def sync_goals_with_current_events(
    match_state,
    current_goal_infos,
    cancelled_goal_keys=None,
):

    for goal_info in (
        current_goal_infos or []
    ):

        if not isinstance(
            goal_info,
            dict,
        ):
            continue

        add_goal(
            match_state,
            goal_info,
        )

    for goal_key in (
        cancelled_goal_keys or []
    ):

        if goal_key is None:
            continue

        cancel_goal(
            match_state,
            str(goal_key),
        )

    return match_state

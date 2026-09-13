import json
import os


STATE_FILE = "state.json"


# --------------------------------------------------------
# وضعیت پیش‌فرض
# --------------------------------------------------------

def default_state():
    return {
        "matches": {}
    }


def default_match_state():
    return {
        # ترکیب
        "lineup_sent": False,
        "fallback_sent": False,

        # وضعیت مسابقه
        "started": False,
        "half_time": False,
        "finished": False,

        # پیام پایان
        "finished_sent": False,

        # تمام eventهایی که تا این لحظه دیده‌ایم
        "event_keys": [],

        # گل‌هایی که قبلاً به عنوان گل معتبر ثبت شده‌اند
        #
        # ساختار هر گل:
        #
        # {
        #   "event_key": "...",
        #   "player_id": "...",
        #   "is_home": true,
        #   "minute": 67,
        #   "cancelled": false
        # }
        #
        "goals": [],
    }


# --------------------------------------------------------
# بارگذاری state
# --------------------------------------------------------

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

        if not isinstance(
            data,
            dict,
        ):
            return default_state()

        if not isinstance(
            data.get("matches"),
            dict,
        ):
            data["matches"] = {}

        # ------------------------------------------------
        # سازگار کردن stateهای قدیمی
        # ------------------------------------------------

        for match_id, match_state in data[
            "matches"
        ].items():

            if not isinstance(
                match_state,
                dict,
            ):
                data["matches"][
                    match_id
                ] = default_match_state()

                continue

            defaults = default_match_state()

            for key, value in defaults.items():

                if key not in match_state:
                    match_state[key] = value

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

        return data

    except (
        json.JSONDecodeError,
        OSError,
    ):
        return default_state()


# --------------------------------------------------------
# ذخیره state
# --------------------------------------------------------

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


# --------------------------------------------------------
# گرفتن state یک مسابقه
# --------------------------------------------------------

def get_match_state(
    state,
    match_id,
):
    match_id = str(match_id)

    matches = state.setdefault(
        "matches",
        {},
    )

    if match_id not in matches:

        matches[match_id] = (
            default_match_state()
        )

    else:

        # اگر state قدیمی باشد،
        # فیلدهای جدید را اضافه می‌کنیم.
        defaults = default_match_state()

        for key, value in defaults.items():

            if key not in matches[
                match_id
            ]:

                matches[
                    match_id
                ][key] = value

        if not isinstance(
            matches[match_id].get(
                "event_keys"
            ),
            list,
        ):
            matches[
                match_id
            ]["event_keys"] = []

        if not isinstance(
            matches[match_id].get(
                "goals"
            ),
            list,
        ):
            matches[
                match_id
            ]["goals"] = []

    return matches[match_id]


# --------------------------------------------------------
# تغییر state
# --------------------------------------------------------

def update_match_state(
    state,
    match_id,
    **updates,
):
    match_state = get_match_state(
        state,
        match_id,
    )

    match_state.update(
        updates
    )

    return match_state


# --------------------------------------------------------
# مدیریت eventها
# --------------------------------------------------------

def has_event(
    match_state,
    event_key,
):
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
    """
    event keyهای جدید را به state اضافه می‌کند.
    """

    existing = set(
        match_state.get(
            "event_keys",
            [],
        )
    )

    for key in event_keys or []:

        if key is None:
            continue

        existing.add(
            str(key)
        )

    match_state[
        "event_keys"
    ] = list(existing)


# --------------------------------------------------------
# مدیریت گل‌ها
# --------------------------------------------------------

def find_goal(
    match_state,
    goal_key,
):
    """
    یک گل را بر اساس event_key پیدا می‌کند.
    """

    if not goal_key:
        return None

    for goal in match_state.get(
        "goals",
        [],
    ):

        if not isinstance(
            goal,
            dict,
        ):
            continue

        if (
            goal.get(
                "event_key"
            )
            == goal_key
        ):
            return goal

    return None


def add_goal(
    match_state,
    goal_info,
):
    """
    یک گل جدید را در state ثبت می‌کند.

    اگر گل قبلاً ثبت شده باشد،
    دوباره اضافه نمی‌شود.
    """

    if not isinstance(
        goal_info,
        dict,
    ):
        return None

    goal_key = goal_info.get(
        "event_key"
    )

    if not goal_key:
        return None

    existing = find_goal(
        match_state,
        goal_key,
    )

    if existing is not None:
        return existing

    goal = {
        "event_key": goal_key,
        "player_id": goal_info.get(
            "player_id"
        ),
        "assist_player_id": (
            goal_info.get(
                "assist_player_id"
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
    }

    match_state.setdefault(
        "goals",
        [],
    ).append(goal)

    return goal


def cancel_goal(
    match_state,
    goal_key,
):
    """
    یک گل را مردود می‌کند.

    خود گل را از state حذف نمی‌کنیم؛
    فقط cancelled=True می‌گذاریم.

    این کار مهم است چون بعداً می‌توانیم بفهمیم
    که این گل قبلاً ارسال شده بوده و بعداً توسط VAR
    لغو شده است.
    """

    goal = find_goal(
        match_state,
        goal_key,
    )

    if goal is None:
        return None

    goal[
        "cancelled"
    ] = True

    return goal


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

    return goal.get(
        "cancelled",
        False,
    ) is True


def get_valid_goals(
    match_state,
):
    """
    فقط گل‌هایی که هنوز معتبر هستند.
    """

    return [
        goal
        for goal in match_state.get(
            "goals",
            [],
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
    """
    گل‌هایی که قبلاً ثبت شده‌اند ولی
    بعداً توسط VAR مردود شده‌اند.
    """

    return [
        goal
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
    ]


# --------------------------------------------------------
# محاسبه نتیجه از گل‌های معتبر
# --------------------------------------------------------

def get_current_score(
    match_state,
):
    """
    نتیجه را فقط از گل‌های معتبر state محاسبه می‌کند.

    بنابراین اگر VAR یک گل را مردود کند،
    نتیجه خودکار اصلاح می‌شود.
    """

    home_score = 0
    away_score = 0

    for goal in get_valid_goals(
        match_state
    ):

        is_home = goal.get(
            "is_home"
        )

        # ------------------------------------------------
        # گل به خودی
        #
        # اگر بازیکن تیم میزبان گل به خودی زده باشد،
        # امتیاز برای تیم مهمان حساب می‌شود و برعکس.
        # ------------------------------------------------

        if goal.get(
            "own_goal",
            False,
        ):

            if is_home is True:
                away_score += 1

            elif is_home is False:
                home_score += 1

            continue

        if is_home is True:
            home_score += 1

        elif is_home is False:
            away_score += 1

    return {
        "home": home_score,
        "away": away_score,
    }


# --------------------------------------------------------
# اصلاح state با اطلاعات فعلی فوت‌موب
# --------------------------------------------------------

def sync_goals_with_current_events(
    match_state,
    current_goal_infos,
    cancelled_goal_keys=None,
):
    """
    state گل‌ها را با وضعیت فعلی فوت‌موب هماهنگ می‌کند.

    این تابع دو کار انجام می‌دهد:

    1. گل‌های جدید را ثبت می‌کند.
    2. گل‌هایی را که فوت‌موب حالا مردود اعلام کرده،
       cancelled می‌کند.

    current_goal_infos باید فقط گل‌هایی باشد که
    event_detector آنها را معتبر تشخیص داده است.
    """

    current_goal_infos = (
        current_goal_infos
        or []
    )

    cancelled_goal_keys = set(
        cancelled_goal_keys
        or []
    )

    # ----------------------------------------------------
    # ثبت گل‌های جدید
    # ----------------------------------------------------

    for goal_info in current_goal_infos:

        if not isinstance(
            goal_info,
            dict,
        ):
            continue

        add_goal(
            match_state,
            goal_info,
        )

    # ----------------------------------------------------
    # علامت‌گذاری گل‌های مردود
    # ----------------------------------------------------

    for goal_key in (
        cancelled_goal_keys
    ):

        cancel_goal(
            match_state,
            goal_key,
        )

    return match_state


# --------------------------------------------------------
# پاک‌سازی اختیاری
# --------------------------------------------------------

def remove_old_match(
    state,
    match_id,
):
    """
    در صورت نیاز می‌توانیم state مسابقه‌ای که دیگر
    تحت نظارت نیست را حذف کنیم.

    فعلاً main از این تابع استفاده نمی‌کند.
    """

    match_id = str(match_id)

    matches = state.get(
        "matches",
        {},
    )

    matches.pop(
        match_id,
        None,
    )

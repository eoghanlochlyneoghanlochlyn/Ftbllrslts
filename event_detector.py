from fotmob import (
    clean_text,
    get_event_assist_player_id,
    get_event_player_id,
    get_match_events,
)


# --------------------------------------------------------
# ابزارهای عمومی
# --------------------------------------------------------

def get_event_type(event):
    if not isinstance(event, dict):
        return ""

    return clean_text(
        event.get("type")
    ).lower()


def get_event_time(event):
    if not isinstance(event, dict):
        return None

    value = event.get("time")

    if value is None:
        value = event.get("minute")

    if value is None:
        value = event.get("elapsed")

    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def get_event_team(event):
    """
    تعیین می‌کند رویداد مربوط به تیم میزبان است یا مهمان.

    در فوت‌موب معمولاً isHome وجود دارد.
    """

    if not isinstance(event, dict):
        return None

    value = event.get("isHome")

    if isinstance(value, bool):
        return value

    # بعضی ساختارهای فوت‌موب ممکن است home داشته باشند.
    value = event.get("home")

    if isinstance(value, bool):
        return value

    return None


def get_event_unique_id(event):
    if not isinstance(event, dict):
        return None

    for key in (
        "id",
        "eventId",
        "eventID",
    ):
        value = event.get(key)

        if value is not None:
            return str(value)

    return None


# --------------------------------------------------------
# VAR
# --------------------------------------------------------

def is_cancelled_goal_event(event):
    if not isinstance(event, dict):
        return False

    event_type = get_event_type(event)

    if event_type != "var":
        return False

    decision = event.get("decision")

    if not isinstance(decision, dict):
        return False

    keys = decision.get("key")

    if isinstance(keys, list):

        for key in keys:

            key = clean_text(key).lower()

            if key == "var_goal_cancelled":
                return True

    elif isinstance(keys, str):

        if "var_goal_cancelled" in keys.lower():
            return True

    return False


def get_cancelled_var_events(events):
    """
    تمام رویدادهای VAR که گل را مردود کرده‌اند.
    """

    return [
        event
        for event in events
        if is_cancelled_goal_event(event)
    ]


def _same_team(first_event, second_event):
    """
    اگر برای هر دو رویداد اطلاعات تیم وجود داشته باشد،
    بررسی می‌کند که مربوط به یک تیم هستند یا نه.
    """

    first_team = get_event_team(first_event)
    second_team = get_event_team(second_event)

    if first_team is None or second_team is None:
        return True

    return first_team == second_team


def _same_player(first_event, second_event):
    first_player = get_event_player_id(first_event)
    second_player = get_event_player_id(second_event)

    if first_player is None or second_player is None:
        return False

    return str(first_player) == str(second_player)


def _time_difference(first_event, second_event):
    first_time = get_event_time(first_event)
    second_time = get_event_time(second_event)

    if first_time is None or second_time is None:
        return None

    return abs(first_time - second_time)


def find_cancelled_goal(
    var_event,
    goal_events,
):
    """
    تلاش می‌کند مشخص کند VAR مربوط به کدام گل بوده است.

    اولویت تشخیص:

    1. شناسه بازیکن + تیم
    2. تیم + زمان نزدیک
    3. بازیکن + زمان نزدیک

    عمداً فقط آخرین گل را حذف نمی‌کنیم؛
    چون ممکن است بین گل و VAR گل دیگری هم ثبت شده باشد.
    """

    if not is_cancelled_goal_event(var_event):
        return None

    candidates = []

    for goal in goal_events:

        if not isinstance(goal, dict):
            continue

        if get_event_type(goal) != "goal":
            continue

        if goal.get(
            "isPenaltyShootoutEvent"
        ) is True:
            continue

        if not _same_team(
            var_event,
            goal,
        ):
            continue

        same_player = _same_player(
            var_event,
            goal,
        )

        difference = _time_difference(
            var_event,
            goal,
        )

        # ------------------------------------------------
        # بهترین حالت:
        # بازیکن یکسان است.
        # ------------------------------------------------

        if same_player:

            if difference is None:
                score = 100

            elif difference <= 5:
                score = 1000 - difference

            else:
                score = 500 - difference

            candidates.append(
                (
                    score,
                    goal,
                )
            )

            continue

        # ------------------------------------------------
        # اگر بازیکن در VAR مشخص نیست،
        # از تیم + زمان استفاده می‌کنیم.
        # ------------------------------------------------

        if difference is not None:

            if difference <= 5:

                score = 100 - difference

                candidates.append(
                    (
                        score,
                        goal,
                    )
                )

    if not candidates:
        return None

    candidates.sort(
        key=lambda item: item[0],
        reverse=True,
    )

    return candidates[0][1]


def detect_cancelled_goals(events):
    """
    خروجی:

    [
        {
            "var_event": ...,
            "goal_event": ...
        }
    ]

    این اطلاعات بعداً توسط state_manager برای
    اصلاح وضعیت گل استفاده می‌شود.
    """

    if not events:
        return []

    goal_events = [
        event
        for event in events
        if (
            isinstance(event, dict)
            and get_event_type(event) == "goal"
            and event.get(
                "isPenaltyShootoutEvent"
            ) is not True
        )
    ]

    cancelled = []

    for var_event in get_cancelled_var_events(
        events
    ):

        goal_event = find_cancelled_goal(
            var_event,
            goal_events,
        )

        if goal_event is None:
            continue

        cancelled.append(
            {
                "var_event": var_event,
                "goal_event": goal_event,
            }
        )

    return cancelled


def get_cancelled_goal_keys(events):
    """
    کلید گل‌هایی که در حال حاضر توسط VAR مردود شده‌اند.
    """

    cancelled = detect_cancelled_goals(
        events
    )

    keys = set()

    for item in cancelled:

        goal = item.get(
            "goal_event"
        )

        if goal is None:
            continue

        keys.add(
            event_key(goal)
        )

    return keys


# --------------------------------------------------------
# پنالتی و گل به خودی
# --------------------------------------------------------

def is_penalty_goal(event):
    if not isinstance(event, dict):
        return False

    if clean_text(
        event.get("goalDescriptionKey")
    ).lower() == "penalty":
        return True

    if clean_text(
        event.get("goalDescription")
    ).lower() == "penalty":
        return True

    shotmap = event.get("shotmapEvent")

    if isinstance(shotmap, dict):

        if clean_text(
            shotmap.get("situation")
        ).lower() == "penalty":
            return True

    return False


def is_own_goal(event):
    if not isinstance(event, dict):
        return False

    if event.get("ownGoal") is True:
        return True

    shotmap = event.get("shotmapEvent")

    if isinstance(shotmap, dict):

        return (
            shotmap.get("isOwnGoal")
            is True
        )

    return False


# --------------------------------------------------------
# کارت قرمز
# --------------------------------------------------------

def is_red_card_event(event):
    if not isinstance(event, dict):
        return False

    if get_event_type(event) != "card":
        return False

    card = clean_text(
        event.get("card")
    ).lower()

    if card not in (
        "red",
        "redcard",
        "red_card",
    ):
        return False

    description = event.get(
        "cardDescription"
    )

    if isinstance(description, dict):

        localized_key = clean_text(
            description.get(
                "localizedKey"
            )
        ).lower()

        default_text = clean_text(
            description.get(
                "defaultText"
            )
        ).lower()

        if localized_key == "coach":
            return False

        if default_text == "coach":
            return False

    return True


# --------------------------------------------------------
# کلید پایدار رویداد
# --------------------------------------------------------

def event_key(event):
    """
    یک کلید نسبتاً پایدار برای هر رویداد می‌سازد.

    نکته مهم:
    نسخه قبلی از index استفاده می‌کرد.
    این کار خطرناک بود، چون با اضافه شدن یک event جدید،
    index رویدادهای قبلی ممکن بود تغییر کند.

    اولویت:
    1. id خود رویداد
    2. eventId
    3. ترکیب type/player/time/team/description
    """

    if not isinstance(event, dict):
        return "unknown"

    event_id = get_event_unique_id(event)

    if event_id is not None:
        return f"id:{event_id}"

    event_type = get_event_type(
        event
    )

    player_id = get_event_player_id(
        event
    )

    assist_id = get_event_assist_player_id(
        event
    )

    event_time = get_event_time(
        event
    )

    is_home = get_event_team(
        event
    )

    goal_description = clean_text(
        event.get(
            "goalDescriptionKey"
        )
    ).lower()

    card = clean_text(
        event.get("card")
    ).lower()

    decision = event.get(
        "decision"
    )

    decision_key = ""

    if isinstance(decision, dict):

        value = decision.get(
            "key"
        )

        if isinstance(value, list):

            decision_key = ",".join(
                sorted(
                    clean_text(item).lower()
                    for item in value
                )
            )

        else:
            decision_key = clean_text(
                value
            ).lower()

    return (
        f"type={event_type}|"
        f"player={player_id}|"
        f"assist={assist_id}|"
        f"time={event_time}|"
        f"home={is_home}|"
        f"goal={goal_description}|"
        f"card={card}|"
        f"decision={decision_key}"
    )


def get_event_keys(events):
    return [
        event_key(event)
        for event in (events or [])
    ]


def detect_new_events(
    previous_events,
    current_events,
):
    """
    فقط eventهایی را برمی‌گرداند که قبلاً دیده نشده‌اند.
    """

    previous = set(
        previous_events or []
    )

    new_events = []

    for event in current_events or []:

        key = event_key(event)

        if key not in previous:
            new_events.append(event)

    return new_events


# --------------------------------------------------------
# گل
# --------------------------------------------------------

def is_valid_goal(event):
    if not isinstance(event, dict):
        return False

    if get_event_type(event) != "goal":
        return False

    if event.get(
        "isPenaltyShootoutEvent"
    ) is True:
        return False

    return True


def detect_goals(events):
    """
    تمام گل‌های معتبر موجود در لیست eventها.
    گل‌های مردودشده توسط VAR حذف می‌شوند.
    """

    if not events:
        return []

    cancelled_goal_keys = (
        get_cancelled_goal_keys(events)
    )

    goals = []

    for event in events:

        if not is_valid_goal(event):
            continue

        key = event_key(event)

        if key in cancelled_goal_keys:
            continue

        goals.append(event)

    return goals


def detect_new_goals(
    previous_event_keys,
    current_events,
):
    """
    گل‌هایی که از آخرین بررسی جدید هستند.

    نکته:
    اگر یک گل در یک poll دیده شود و چند دقیقه بعد VAR
    آن را لغو کند، خود گل قبلاً در state ثبت شده و
    detect_cancelled_goals آن را پیدا می‌کند.
    """

    new_events = detect_new_events(
        previous_event_keys,
        current_events,
    )

    return [
        event
        for event in new_events
        if is_valid_goal(event)
    ]


# --------------------------------------------------------
# کارت قرمز
# --------------------------------------------------------

def detect_red_cards(events):
    return [
        event
        for event in events
        if is_red_card_event(event)
    ]


# --------------------------------------------------------
# اطلاعات رویداد برای formatter
# --------------------------------------------------------

def get_goal_minute(event):
    """
    دقیقه گل را از event استخراج می‌کند.

    در صورت وجود وقت اضافه، همان مقدار اصلی فوت‌موب
    حفظ می‌شود.
    """

    if not isinstance(event, dict):
        return None

    value = get_event_time(event)

    if value is not None:
        return value

    # چند fallback احتمالی
    for key in (
        "minute",
        "elapsedTime",
        "matchTime",
    ):

        value = event.get(key)

        if value is not None:
            try:
                return int(value)
            except (
                TypeError,
                ValueError,
            ):
                pass

    return None


def get_goal_player_id(event):
    return get_event_player_id(
        event
    )


def get_goal_assist_player_id(event):
    return get_event_assist_player_id(
        event
    )


def get_goal_team_is_home(event):
    return get_event_team(
        event
    )


def get_goal_info(event):
    """
    اطلاعات کامل یک گل برای formatter.
    """

    if not is_valid_goal(event):
        return None

    return {
        "event": event,
        "event_key": event_key(event),
        "player_id": get_goal_player_id(
            event
        ),
        "assist_player_id": (
            get_goal_assist_player_id(
                event
            )
        ),
        "is_home": get_goal_team_is_home(
            event
        ),
        "minute": get_goal_minute(
            event
        ),
        "penalty": is_penalty_goal(
            event
        ),
        "own_goal": is_own_goal(
            event
        ),
    }


# --------------------------------------------------------
# آمار بازیکنان
# --------------------------------------------------------

def get_player_events(root):
    """
    آمار گل، پاس گل و کارت قرمز بازیکنان.

    گل‌هایی که VAR آنها را مردود کرده، در آمار نهایی
    بازیکن حساب نمی‌شوند.
    """

    events = get_match_events(root)

    player_events = {}

    def ensure(player_id):

        if player_id is None:
            return None

        if player_id not in player_events:

            player_events[player_id] = {
                "goals": 0,
                "penalty_goals": 0,
                "assists": 0,
                "red_cards": 0,
            }

        return player_events[player_id]

    cancelled_goal_keys = (
        get_cancelled_goal_keys(events)
    )

    for event in events:

        if not isinstance(event, dict):
            continue

        event_type = get_event_type(
            event
        )

        if event_type == "goal":

            if event.get(
                "isPenaltyShootoutEvent"
            ) is True:
                continue

            # گل مردودشده نباید در آمار حساب شود.
            if (
                event_key(event)
                in cancelled_goal_keys
            ):
                continue

            player_id = (
                get_event_player_id(
                    event
                )
            )

            if player_id is None:
                continue

            data = ensure(
                player_id
            )

            data["goals"] += 1

            if is_penalty_goal(
                event
            ):
                data["penalty_goals"] += 1

            assist_id = (
                get_event_assist_player_id(
                    event
                )
            )

            if assist_id is not None:

                assist_data = ensure(
                    assist_id
                )

                assist_data[
                    "assists"
                ] += 1

        elif event_type == "card":

            if not is_red_card_event(
                event
            ):
                continue

            player_id = (
                get_event_player_id(
                    event
                )
            )

            if player_id is None:
                continue

            data = ensure(
                player_id
            )

            data["red_cards"] += 1

    return player_events


# --------------------------------------------------------
# وضعیت بازی
# --------------------------------------------------------

def _find_status_objects(root):
    """
    چند مسیر احتمالی برای status فوت‌موب.
    چون ساختار بعضی مسابقات ممکن است کمی متفاوت باشد.
    """

    objects = []

    if not isinstance(root, dict):
        return objects

    props = root.get(
        "props"
    )

    if isinstance(props, dict):

        page_props = props.get(
            "pageProps"
        )

        if isinstance(
            page_props,
            dict,
        ):

            content = page_props.get(
                "content"
            )

            if isinstance(
                content,
                dict,
            ):

                header = content.get(
                    "header"
                )

                if isinstance(
                    header,
                    dict,
                ):
                    status = header.get(
                        "status"
                    )

                    if isinstance(
                        status,
                        dict,
                    ):
                        objects.append(
                            status
                        )

                status = content.get(
                    "status"
                )

                if isinstance(
                    status,
                    dict,
                ):
                    objects.append(
                        status
                    )

    return objects


def get_match_status_key(root):
    """
    وضعیت فعلی بازی را به یک کلید ساده تبدیل می‌کند.

    مثال‌های احتمالی:
    NOT_STARTED
    LIVE
    HT
    FINISHED
    """

    for status in _find_status_objects(
        root
    ):

        reason = status.get(
            "reason"
        )

        if isinstance(
            reason,
            dict,
        ):

            short = clean_text(
                reason.get(
                    "short"
                )
            ).upper()

            if short:
                return short

            long_text = clean_text(
                reason.get(
                    "long"
                )
            ).upper()

            if long_text:
                return long_text

        short = clean_text(
            status.get(
                "short"
            )
        ).upper()

        if short:
            return short

        name = clean_text(
            status.get(
                "name"
            )
        ).upper()

        if name:
            return name

    return ""


def is_match_started(
    root,
    snapshot=None,
):
    """
    بررسی شروع شدن بازی.

    snapshot اگر شامل status ساده باشد، اول بررسی می‌شود.
    """

    if isinstance(
        snapshot,
        dict,
    ):

        status = clean_text(
            snapshot.get(
                "status"
            )
        ).lower()

        if status in (
            "live",
            "started",
            "inplay",
            "in_play",
        ):
            return True

        if snapshot.get(
            "finished"
        ) is True:
            return True

    status_key = get_match_status_key(
        root
    )

    if status_key in (
        "LIVE",
        "1H",
        "2H",
        "ET",
        "P",
        "HT",
        "FT",
        "AET",
        "PEN",
        "FINISHED",
    ):
        return True

    # بررسی چند وضعیت متنی احتمالی
    status_lower = status_key.lower()

    if any(
        word in status_lower
        for word in (
            "live",
            "started",
            "in progress",
            "halftime",
            "half time",
            "finished",
        )
    ):
        return True

    return False


def is_half_time(
    root,
    snapshot=None,
):
    if isinstance(
        snapshot,
        dict,
    ):

        status = clean_text(
            snapshot.get(
                "status"
            )
        ).lower()

        if status in (
            "ht",
            "halftime",
            "half_time",
        ):
            return True

    status_key = get_match_status_key(
        root
    )

    normalized = status_key.lower()

    return normalized in (
        "ht",
        "halftime",
        "half time",
        "half_time",
    )


# --------------------------------------------------------
# تغییر وضعیت
# --------------------------------------------------------

def detect_state_changes(
    previous_state,
    root,
    snapshot,
):
    """
    تمام تغییرات مهم از آخرین poll را پیدا می‌کند.

    previous_state باید از state_manager بیاید.

    این تابع عمداً خودش state را تغییر نمی‌دهد.
    فقط می‌گوید چه اتفاقی افتاده.
    """

    previous_state = (
        previous_state
        or {}
    )

    snapshot = (
        snapshot
        or {}
    )

    current_events = snapshot.get(
        "events",
        [],
    )

    previous_event_keys = (
        previous_state.get(
            "event_keys",
            [],
        )
    )

    new_events = detect_new_events(
        previous_event_keys,
        current_events,
    )

    previous_finished = (
        previous_state.get(
            "finished",
            False,
        )
    )

    current_finished = (
        snapshot.get(
            "finished",
            False,
        )
    )

    previous_started = (
        previous_state.get(
            "started",
            False,
        )
    )

    current_started = is_match_started(
        root,
        snapshot,
    )

    previous_half_time = (
        previous_state.get(
            "half_time",
            False,
        )
    )

    current_half_time = is_half_time(
        root,
        snapshot,
    )

    # ----------------------------------------------------
    # گل‌های جدید
    # ----------------------------------------------------

    new_goals = [
        event
        for event in new_events
        if is_valid_goal(event)
    ]

    # ----------------------------------------------------
    # VARهایی که تازه آمده‌اند
    # ----------------------------------------------------

    new_var_events = [
        event
        for event in new_events
        if is_cancelled_goal_event(
            event
        )
    ]

    # ----------------------------------------------------
    # گل‌های مردود شده
    #
    # فقط VARهای جدید بررسی می‌شوند تا یک VAR قدیمی
    # در هر poll دوباره به عنوان اتفاق جدید برنگردد.
    # ----------------------------------------------------

    cancelled_goals = []

    if new_var_events:

        goal_events = [
            event
            for event in current_events
            if is_valid_goal(event)
        ]

        for var_event in new_var_events:

            goal_event = (
                find_cancelled_goal(
                    var_event,
                    goal_events,
                )
            )

            if goal_event is None:
                continue

            cancelled_goals.append(
                {
                    "var_event": var_event,
                    "goal_event": goal_event,
                    "goal_key": event_key(
                        goal_event
                    ),
                    "minute": get_goal_minute(
                        goal_event
                    ),
                    "player_id": (
                        get_event_player_id(
                            goal_event
                        )
                    ),
                    "is_home": (
                        get_event_team(
                            goal_event
                        )
                    ),
                }
            )

    changes = {
        # همه eventهای جدید
        "new_events": new_events,

        # گل‌های جدید
        "new_goals": new_goals,

        # اطلاعات کامل گل‌های جدید
        "new_goal_info": [
            get_goal_info(event)
            for event in new_goals
        ],

        # VARهای مربوط به لغو گل
        "cancelled_goals": cancelled_goals,

        # کارت قرمز
        "new_red_cards": (
            detect_red_cards(
                new_events
            )
        ),

        # شروع بازی
        "started": (
            current_started
            and not previous_started
        ),

        # نیمه اول تمام شده
        "half_time": (
            current_half_time
            and not previous_half_time
        ),

        # بازی تمام شده
        "finished": (
            current_finished
            and not previous_finished
        ),

        # وضعیت فعلی برای state_manager
        "current_started": current_started,
        "current_half_time": current_half_time,
        "current_finished": current_finished,

        # کلیدهای فعلی eventها
        "current_event_keys": (
            get_event_keys(
                current_events
            )
        ),
    }

    return changes

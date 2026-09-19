import re

from fotmob import (
    clean_text,
    get_event_assist_player_id,
    get_event_player_id,
    get_event_unique_id,
)


# =========================================================
# ابزارهای عمومی
# =========================================================

def first_non_empty(*values):

    for value in values:

        if value is None:
            continue

        if isinstance(
            value,
            str,
        ):

            value = value.strip()

            if value:
                return value

        elif value not in (
            "",
            None,
        ):

            return value

    return ""


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
        "player unknown",
        "بازیکن نامشخص",
    )


def get_event_player_name(
    event
):

    if not isinstance(
        event,
        dict,
    ):
        return ""

    player = event.get(
        "player"
    )

    if isinstance(
        player,
        dict,
    ):

        name = first_non_empty(
            player.get("name"),
            player.get("shortName"),
            player.get("displayName"),
        )

        if name:
            return str(name)

    return str(
        first_non_empty(
            event.get("playerName"),
            event.get("player_name"),
            event.get("name"),
        )
        or ""
    )


def get_event_assist_player_name(
    event
):

    if not isinstance(
        event,
        dict,
    ):
        return ""

    player = event.get(
        "assistPlayer"
    )

    if isinstance(
        player,
        dict,
    ):

        name = first_non_empty(
            player.get("name"),
            player.get("shortName"),
            player.get("displayName"),
        )

        if name:
            return str(name)

    assist = event.get(
        "assist"
    )

    if isinstance(
        assist,
        dict,
    ):

        name = first_non_empty(
            assist.get("name"),
            assist.get("shortName"),
            assist.get("displayName"),
        )

        if name:
            return str(name)

    return str(
        first_non_empty(
            event.get("assistPlayerName"),
            event.get("assist_player_name"),
        )
        or ""
    )


# =========================================================
# نوع event
# =========================================================

def get_event_type(event):

    if not isinstance(
        event,
        dict,
    ):
        return ""

    value = first_non_empty(
        event.get("type"),
        event.get("eventType"),
        event.get("incidentType"),
        event.get("incident"),
    )

    if isinstance(
        value,
        dict,
    ):

        value = first_non_empty(
            value.get("name"),
            value.get("type"),
        )

    value = clean_text(
        value
    ).lower()

    if (
        "goal" in value
        or event.get("isGoal") is True
    ):
        return "goal"

    if (
        "card" in value
        or event.get("card") is not None
        or event.get("cardType") is not None
    ):
        return "card"

    if "var" in value:
        return "var"

    return value


# =========================================================
# زمان event
# =========================================================

def get_event_time(event):

    if not isinstance(
        event,
        dict,
    ):
        return None

    for key in (
        "time",
        "minute",
        "elapsed",
        "eventTime",
        "timeValue",
    ):

        value = event.get(
            key
        )

        if value is None:
            continue

        if isinstance(
            value,
            (int, float),
        ):
            return float(
                value
            )

        match = re.search(
            r"(\d+)",
            str(value),
        )

        if match:

            try:
                return float(
                    match.group(1)
                )
            except (
                TypeError,
                ValueError,
            ):
                pass

    return None


def get_event_minute_text(event):

    if not isinstance(
        event,
        dict,
    ):
        return ""

    for key in (
        "timeStr",
        "minute",
        "time",
        "displayTime",
        "eventTime",
    ):

        value = event.get(
            key
        )

        if value is None:
            continue

        value = clean_text(
            value
        )

        if value:
            return value

    return ""


def get_goal_minute(event):

    text = get_event_minute_text(
        event
    )

    if text:
        return text

    value = get_event_time(
        event
    )

    if value is None:
        return None

    if float(value).is_integer():
        return str(
            int(value)
        )

    return str(value)


# =========================================================
# تیم event
# =========================================================

def get_event_team(event):

    if not isinstance(
        event,
        dict,
    ):
        return None

    value = event.get(
        "isHome"
    )

    if isinstance(
        value,
        bool,
    ):
        return value

    value = event.get(
        "home"
    )

    if isinstance(
        value,
        bool,
    ):
        return value

    team = event.get(
        "team"
    )

    if isinstance(
        team,
        dict,
    ):

        value = team.get(
            "isHome"
        )

        if isinstance(
            value,
            bool,
        ):
            return value

        value = team.get(
            "home"
        )

        if isinstance(
            value,
            bool,
        ):
            return value

    return None


# =========================================================
# event key
# =========================================================

def event_key(event):

    if not isinstance(
        event,
        dict,
    ):
        return None

    # reactKey در داده‌های FotMob برای eventهای واقعی یکتا است.
    # باید قبل از eventId بررسی شود، چون eventId در بعضی بازی‌ها
    # برای چند event مختلف مقدار 0 دارد.
    react_key = event.get(
        "reactKey"
    )

    if react_key is not None and str(
        react_key
    ).strip():

        return f"react:{react_key}"

    unique_id = get_event_unique_id(
        event
    )

    # صفر در FotMob می‌تواند شناسه placeholder باشد؛ در این
    # حالت به fallback پایین می‌رویم تا چند event یکی نشوند.
    if (
        unique_id is not None
        and str(unique_id) != "0"
    ):
        return f"id:{unique_id}"

    event_type = get_event_type(
        event
    )

    player_id = get_event_player_id(
        event
    )

    team = get_event_team(
        event
    )

    minute = get_event_time(
        event
    )

    description = clean_text(
        first_non_empty(
            event.get("description"),
            event.get("text"),
            event.get("incidentDescription"),
        )
    )

    return (
        f"{event_type}|"
        f"{player_id}|"
        f"{team}|"
        f"{minute}|"
        f"{description}"
    )


# =========================================================
# گل مردود
# =========================================================

def is_cancelled_goal_event(event):

    if not isinstance(
        event,
        dict,
    ):
        return False

    for key in (
        "cancelled",
        "canceled",
        "isCancelled",
        "isCanceled",
        "goalCancelled",
        "goalCanceled",
    ):

        if event.get(
            key
        ) is True:
            return True

    text = " ".join(
        [
            clean_text(
                event.get(
                    "description"
                )
            ),
            clean_text(
                event.get(
                    "text"
                )
            ),
            clean_text(
                event.get(
                    "incidentDescription"
                )
            ),
            clean_text(
                event.get(
                    "reason"
                )
            ),
        ]
    ).lower()

    if any(
        phrase in text
        for phrase in (
            "goal disallowed",
            "goal cancelled",
            "goal canceled",
            "goal ruled out",
            "disallowed goal",
            "cancelled goal",
            "canceled goal",
        )
    ):
        return True

    return False


def get_cancelled_var_events(events):

    result = []

    for event in events or []:

        if not isinstance(
            event,
            dict,
        ):
            continue

        if (
            get_event_type(event)
            == "var"
        ):

            result.append(
                event
            )

    return result


def _same_team(
    event_a,
    event_b,
):

    a = get_event_team(
        event_a
    )

    b = get_event_team(
        event_b
    )

    if a is None or b is None:
        return True

    return a == b


def _same_player(
    event_a,
    event_b,
):

    a = get_event_player_id(
        event_a
    )

    b = get_event_player_id(
        event_b
    )

    if a is None or b is None:
        return True

    return str(a) == str(b)


def _time_difference(
    event_a,
    event_b,
):

    a = get_event_time(
        event_a
    )

    b = get_event_time(
        event_b
    )

    if a is None or b is None:
        return 999999

    return abs(
        float(a) - float(b)
    )


def find_cancelled_goal(
    goal_event,
    events,
):

    for event in events or []:

        if not isinstance(
            event,
            dict,
        ):
            continue

        if get_event_type(
            event
        ) != "var":
            continue

        if not _same_team(
            goal_event,
            event,
        ):
            continue

        if not _same_player(
            goal_event,
            event,
        ):
            continue

        if _time_difference(
            goal_event,
            event,
        ) > 3:
            continue

        if is_cancelled_goal_event(
            event
        ):

            return event

        text = " ".join(
            [
                clean_text(
                    event.get(
                        "description"
                    )
                ),
                clean_text(
                    event.get(
                        "text"
                    )
                ),
                clean_text(
                    event.get(
                        "reason"
                    )
                ),
            ]
        ).lower()

        if any(
            phrase in text
            for phrase in (
                "disallowed",
                "cancelled",
                "canceled",
                "ruled out",
            )
        ):

            return event

    return None


def detect_cancelled_goals(events):

    result = []

    for goal_event in events or []:

        if not isinstance(
            goal_event,
            dict,
        ):
            continue

        if get_event_type(
            goal_event
        ) != "goal":
            continue

        if is_cancelled_goal_event(
            goal_event
        ):

            result.append(
                {
                    "goal_key": event_key(
                        goal_event
                    ),
                    "goal_event": goal_event,
                    "is_home": get_event_team(
                        goal_event
                    ),
                    "minute": get_goal_minute(
                        goal_event
                    ),
                }
            )

            continue

        var_event = find_cancelled_goal(
            goal_event,
            events,
        )

        if var_event is not None:

            result.append(
                {
                    "goal_key": event_key(
                        goal_event
                    ),
                    "goal_event": goal_event,
                    "var_event": var_event,
                    "is_home": get_event_team(
                        goal_event
                    ),
                    "minute": get_goal_minute(
                        goal_event
                    ),
                }
            )

    return result


def get_cancelled_goal_keys(events):

    return [
        item.get(
            "goal_key"
        )
        for item in detect_cancelled_goals(
            events
        )
        if item.get(
            "goal_key"
        )
    ]


# =========================================================
# پنالتی / گل به خودی
# =========================================================

def is_penalty_goal(event):

    if not isinstance(
        event,
        dict,
    ):
        return False

    key = clean_text(
        event.get(
            "goalDescriptionKey"
        )
    ).lower()

    description = clean_text(
        event.get(
            "goalDescription"
        )
    ).lower()

    if "penalty" in key:
        return True

    if "penalty" in description:
        return True

    shotmap = event.get(
        "shotmapEvent"
    )

    if isinstance(
        shotmap,
        dict,
    ):

        situation = clean_text(
            shotmap.get(
                "situation"
            )
        ).lower()

        if situation == "penalty":
            return True

        if shotmap.get(
            "isPenalty"
        ) is True:
            return True

    return False


def is_own_goal(event):

    if not isinstance(
        event,
        dict,
    ):
        return False

    if event.get(
        "ownGoal"
    ) is True:
        return True

    if event.get(
        "isOwnGoal"
    ) is True:
        return True

    shotmap = event.get(
        "shotmapEvent"
    )

    if isinstance(
        shotmap,
        dict,
    ):

        if shotmap.get(
            "isOwnGoal"
        ) is True:
            return True

        if shotmap.get(
            "ownGoal"
        ) is True:
            return True

    description = clean_text(
        first_non_empty(
            event.get(
                "goalDescription"
            ),
            event.get(
                "description"
            ),
            event.get(
                "text"
            ),
        )
    ).lower()

    if (
        "own goal" in description
        or "own_goal" in description
        or "autogol" in description
    ):
        return True

    return False


# =========================================================
# کارت قرمز
# =========================================================

def is_red_card_event(event):

    if not isinstance(
        event,
        dict,
    ):
        return False

    event_type = get_event_type(
        event
    )

    if event_type in (
        "red_card",
        "redcard",
        "red card",
        "card",
    ):

        card = clean_text(
            first_non_empty(
                event.get(
                    "card"
                ),
                event.get(
                    "cardType"
                ),
                event.get(
                    "cardName"
                ),
            )
        ).lower()

        if (
            event_type
            != "card"
            or "red" in card
        ):
            return True

    card = clean_text(
        first_non_empty(
            event.get(
                "card"
            ),
            event.get(
                "cardType"
            ),
            event.get(
                "cardName"
            ),
        )
    ).lower()

    if "red" in card:
        return True

    text = clean_text(
        first_non_empty(
            event.get(
                "description"
            ),
            event.get(
                "text"
            ),
        )
    ).lower()

    if "red card" in text:
        return True

    return False


# =========================================================
# اطلاعات کامل گل
# =========================================================

def get_goal_info(event):

    if not isinstance(
        event,
        dict,
    ):
        return None

    if get_event_type(
        event
    ) != "goal":
        return None

    if is_cancelled_goal_event(
        event
    ):
        return None

    team = get_event_team(
        event
    )

    return {
        "event": event,

        "event_key": event_key(
            event
        ),

        "event_id": get_event_unique_id(
            event
        ),

        "player_id": get_event_player_id(
            event
        ),

        "player_name": get_event_player_name(
            event
        ),

        "assist_player_id": (
            get_event_assist_player_id(
                event
            )
        ),

        "assist_player_name": (
            get_event_assist_player_name(
                event
            )
        ),

        "minute": get_goal_minute(
            event
        ),

        "minute_value": get_event_time(
            event
        ),

        "is_home": team,

        "penalty": is_penalty_goal(
            event
        ),

        "own_goal": is_own_goal(
            event
        ),
    }


# =========================================================
# Event keys
# =========================================================

def get_event_keys(events):

    result = []

    for event in events or []:

        key = event_key(
            event
        )

        if key is not None:
            result.append(
                key
            )

    return result


# =========================================================
# تشخیص eventهای جدید
# =========================================================

def detect_new_events(
    previous_event_keys,
    events,
):

    previous = {
        str(key)
        for key in (
            previous_event_keys
            or []
        )
    }

    result = []

    for event in events or []:

        key = event_key(
            event
        )

        if key is None:
            continue

        if key in previous:
            continue

        result.append(
            event
        )

    return result


# =========================================================
# تشخیص تغییر اطلاعات گل‌های قبلی
# =========================================================

def detect_updated_goals(
    match_state,
    events,
):

    result = []

    if not isinstance(
        match_state,
        dict,
    ):
        return result

    previous_goals = (
        match_state.get(
            "goals",
            [],
        )
    )

    if not isinstance(
        previous_goals,
        list,
    ):
        return result

    goals_by_key = {}

    for goal in previous_goals:

        if not isinstance(
            goal,
            dict,
        ):
            continue

        key = goal.get(
            "event_key"
        )

        if key is None:
            continue

        goals_by_key[
            str(key)
        ] = goal

    for event in events or []:

        if not isinstance(
            event,
            dict,
        ):
            continue

        if get_event_type(
            event
        ) != "goal":
            continue

        if is_cancelled_goal_event(
            event
        ):
            continue

        key = event_key(
            event
        )

        if key is None:
            continue

        existing = goals_by_key.get(
            str(key)
        )

        if existing is None:
            continue

        new_player_name = (
            get_event_player_name(
                event
            )
        )

        new_assist_name = (
            get_event_assist_player_name(
                event
            )
        )

        old_player_name = existing.get(
            "player_name"
        )

        old_assist_name = existing.get(
            "assist_player_name"
        )

        player_improved = (
            _is_missing_player_name(
                old_player_name
            )
            and not _is_missing_player_name(
                new_player_name
            )
        )

        assist_improved = (
            _is_missing_player_name(
                old_assist_name
            )
            and not _is_missing_player_name(
                new_assist_name
            )
        )

        player_id_improved = (
            existing.get(
                "player_id"
            ) is None
            and get_event_player_id(
                event
            ) is not None
        )

        assist_id_improved = (
            existing.get(
                "assist_player_id"
            ) is None
            and get_event_assist_player_id(
                event
            ) is not None
        )

        if (
            player_improved
            or assist_improved
            or player_id_improved
            or assist_id_improved
        ):

            result.append(
                get_goal_info(
                    event
                )
            )

    return result


# =========================================================
# تغییرات state
# =========================================================

def detect_state_changes(
    match_state,
    events,
    snapshot=None,
):

    if not isinstance(
        match_state,
        dict,
    ):
        match_state = {}

    events = events or []

    previous_keys = (
        match_state.get(
            "event_keys",
            [],
        )
    )

    new_events = detect_new_events(
        previous_keys,
        events,
    )

    updated_goals = detect_updated_goals(
        match_state,
        events,
    )

    changes = {
        "events": new_events,

        "event_keys": get_event_keys(
            new_events
        ),

        "goals": [],

        "updated_goals": updated_goals,

        "cancelled_goals": [],

        "red_cards": [],

        "start": False,

        "half_time": False,

        "finished": False,
    }

    # -----------------------------------------------------
    # وضعیت کلی
    # -----------------------------------------------------

    if isinstance(
        snapshot,
        dict,
    ):

        if (
            snapshot.get(
                "started"
            )
            and not match_state.get(
                "started",
                False,
            )
        ):

            changes[
                "start"
            ] = True

        if (
            snapshot.get(
                "half_time"
            )
            and not match_state.get(
                "half_time",
                False,
            )
        ):

            changes[
                "half_time"
            ] = True

        if (
            snapshot.get(
                "finished"
            )
            and not match_state.get(
                "finished",
                False,
            )
        ):

            changes[
                "finished"
            ] = True

    # -----------------------------------------------------
    # eventهای جدید
    # -----------------------------------------------------

    for event in new_events:

        event_type = get_event_type(
            event
        )

        if event_type == "goal":

            goal_info = get_goal_info(
                event
            )

            if goal_info is not None:

                changes[
                    "goals"
                ].append(
                    goal_info
                )

        elif event_type == "card":

            if is_red_card_event(
                event
            ):

                changes[
                    "red_cards"
                ].append(
                    event
                )

    # -----------------------------------------------------
    # گل‌های مردود
    # -----------------------------------------------------

    cancelled = detect_cancelled_goals(
        events
    )

    previous_cancelled = set()

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

        if goal.get(
            "cancelled"
        ):

            key = goal.get(
                "event_key"
            )

            if key is not None:

                previous_cancelled.add(
                    str(key)
                )

    for item in cancelled:

        key = item.get(
            "goal_key"
        )

        if key is None:
            continue

        if str(key) not in previous_cancelled:

            changes[
                "cancelled_goals"
            ].append(
                item
            )

    return changes

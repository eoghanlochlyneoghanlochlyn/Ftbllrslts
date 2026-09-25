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

def _collect_event_text(event):
    """Collect human-readable text from an event, including nested decision/reason fields."""
    parts = []

    def walk(value, depth=0):
        if depth > 3:
            return

        if isinstance(value, str):
            value = clean_text(value)
            if value:
                parts.append(value)
            return

        if isinstance(value, (int, float, bool)) or value is None:
            return

        if isinstance(value, dict):
            preferred = (
                "description",
                "text",
                "incidentDescription",
                "reason",
                "decision",
                "label",
                "title",
                "name",
                "value",
                "type",
            )

            for key in preferred:
                if key in value:
                    walk(value.get(key), depth + 1)

            for key, child in value.items():
                if key not in preferred:
                    walk(child, depth + 1)

            return

        if isinstance(value, list):
            for child in value:
                walk(child, depth + 1)

    walk(event)
    return " ".join(parts)


def _normalized_event_text(event):
    return clean_text(
        _collect_event_text(event)
    ).lower()


def _explicit_goal_cancellation_text(text):
    """
    True only for an explicit final decision that a goal was cancelled.
    A generic VAR review/check is deliberately not enough.
    """
    if not text:
        return False

    text = re.sub(r"\s+", " ", text).strip()

    positive_patterns = (
        r"\bgoal\s+(?:has\s+been\s+)?ruled\s+out\b",
        r"\bgoal\s+(?:has\s+been\s+)?disallowed\b",
        r"\bgoal\s+(?:has\s+been\s+)?cancelled\b",
        r"\bgoal\s+(?:has\s+been\s+)?canceled\b",
        r"\bdisallowed\s+goal\b",
        r"\bcancelled\s+goal\b",
        r"\bcanceled\s+goal\b",
        r"\bgoal\s+ruled\s+out\b",
    )

    return any(
        re.search(pattern, text)
        for pattern in positive_patterns
    )


def _extract_cancellation_reason(event):
    """
    Extract FotMob's explicit reason when it is present, without guessing.
    """
    text = _normalized_event_text(event)

    if not _explicit_goal_cancellation_text(text):
        return None

    reason_patterns = (
        ("foul", "foul"),
        ("offside", "offside"),
        ("handball", "handball"),
        ("simulation", "simulation"),
        ("dangerous play", "dangerous play"),
        ("keeper interference", "keeper interference"),
        ("goalkeeper interference", "goalkeeper interference"),
    )

    for needle, reason in reason_patterns:
        if needle in text:
            return reason

    return None


def get_var_decision(event):
    """
    Return a structured VAR decision.

    Important:
    - 'VAR check', 'VAR review', and generic 'VAR' are NOT cancellations.
    - Only FotMob's explicit goal-cancellation wording is accepted.
    """
    if not isinstance(event, dict):
        return {
            "is_var": False,
            "is_goal_cancellation": False,
            "reason": None,
        }

    if get_event_type(event) != "var":
        return {
            "is_var": False,
            "is_goal_cancellation": False,
            "reason": None,
        }

    text = _normalized_event_text(event)

    # Explicit structured flags are authoritative when present.
    explicit_cancel = any(
        event.get(key) is True
        for key in (
            "goalCancelled",
            "goalCanceled",
            "isGoalCancelled",
            "isGoalCanceled",
        )
    )

    is_goal_cancellation = (
        explicit_cancel
        or _explicit_goal_cancellation_text(text)
    )

    return {
        "is_var": True,
        "is_goal_cancellation": is_goal_cancellation,
        "reason": _extract_cancellation_reason(event),
        "text": text,
    }


def is_cancelled_goal_event(event):
    if not isinstance(event, dict):
        return False

    # Explicit flags on the goal itself remain authoritative.
    for key in (
        "cancelled",
        "canceled",
        "isCancelled",
        "isCanceled",
        "goalCancelled",
        "goalCanceled",
        "isGoalCancelled",
        "isGoalCanceled",
    ):
        if event.get(key) is True:
            return True

    return _explicit_goal_cancellation_text(
        _normalized_event_text(event)
    )


def get_cancelled_var_events(events):
    result = []

    for event in events or []:
        if not isinstance(event, dict):
            continue

        if get_event_type(event) == "var":
            decision = get_var_decision(event)

            if decision["is_goal_cancellation"]:
                result.append(event)

    return result


def _same_team_strict(event_a, event_b):
    a = get_event_team(event_a)
    b = get_event_team(event_b)

    if a is None or b is None:
        return None

    return a == b


def _same_player_strict(event_a, event_b):
    a = get_event_player_id(event_a)
    b = get_event_player_id(event_b)

    if a is None or b is None:
        return None

    return str(a) == str(b)


def _event_minute_value(event):
    if not isinstance(event, dict):
        return None

    value = event.get("time")
    if value is None:
        value = event.get("minute")

    if isinstance(value, (int, float)):
        return float(value)

    if isinstance(value, str):
        import re

        match = re.search(r"\d+(?:\.\d+)?", value)
        if match:
            try:
                return float(match.group(0))
            except ValueError:
                return None

    return None


def _time_difference(event_a, event_b):
    minute_a = _event_minute_value(event_a)
    minute_b = _event_minute_value(event_b)

    if minute_a is None or minute_b is None:
        return 0.0

    return abs(minute_a - minute_b)


def _goal_var_match_score(goal_event, var_event):
    """
    Higher score = stronger evidence that this VAR decision belongs to this goal.

    A VAR decision must already be an explicit goal cancellation before this
    function is used. We never infer cancellation from proximity alone.
    """
    score = 0

    same_team = _same_team_strict(goal_event, var_event)
    if same_team is False:
        return None
    if same_team is True:
        score += 40

    same_player = _same_player_strict(goal_event, var_event)
    if same_player is False:
        return None
    if same_player is True:
        score += 60

    time_diff = _time_difference(goal_event, var_event)

    # زمان فقط برای اولویت‌بندی گزینه‌هاست و هرگز نباید باعث شود
    # یک گل که بعد از بررسی طولانی مردود شده، از تشخیص خارج شود.
    # بنابراین هیچ سقف زمانی برای VAR -> Goal نداریم.
    if time_diff <= 1:
        score += 30
    elif time_diff <= 2:
        score += 20
    elif time_diff <= 3:
        score += 15
    elif time_diff <= 5:
        score += 10
    elif time_diff <= 10:
        score += 5
    else:
        score += 1

    return score


def find_cancelled_goal(
    goal_event,
    events,
):
    if not isinstance(goal_event, dict):
        return None

    best = None
    best_score = -1

    for event in events or []:
        if not isinstance(event, dict):
            continue

        if get_event_type(event) != "var":
            continue

        decision = get_var_decision(event)
        if not decision["is_goal_cancellation"]:
            continue

        score = _goal_var_match_score(
            goal_event,
            event,
        )

        if score is not None and score > best_score:
            best = event
            best_score = score

    return best


def _stored_goal_to_event(goal):
    if not isinstance(goal, dict):
        return None

    event = goal.get("event")
    if isinstance(event, dict):
        return event

    # Backward-compatible reconstruction for old state entries.
    event = {
        "type": "goal",
        "player": {
            "id": goal.get("player_id"),
            "name": goal.get("player_name"),
        },
        "isHome": goal.get("is_home"),
        "time": goal.get("minute"),
        "reactKey": goal.get("event_key"),
    }

    return event


def _find_best_goal_for_var(var_event, goal_events):
    best = None
    best_score = -1

    for goal_event, stored_goal in goal_events:
        if not isinstance(goal_event, dict):
            continue

        if get_event_type(goal_event) != "goal":
            continue

        if is_cancelled_goal_event(goal_event):
            continue

        score = _goal_var_match_score(
            goal_event,
            var_event,
        )

        if score is not None and score > best_score:
            best = (goal_event, stored_goal)
            best_score = score

    return best


def detect_cancelled_goals(
    events,
    match_state=None,
):
    """
    Detect only confirmed goal cancellations.

    The function considers both the current FotMob event list and goals already
    stored in state. This is essential because FotMob may publish the original
    goal first and add the final VAR decision on a later polling run.
    """
    events = events or []
    result = []
    seen_goal_keys = set()

    goal_events = []

    for event in events:
        if (
            isinstance(event, dict)
            and get_event_type(event) == "goal"
            and not is_cancelled_goal_event(event)
        ):
            goal_events.append((event, None))

    if isinstance(match_state, dict):
        for stored_goal in match_state.get("goals", []):
            if not isinstance(stored_goal, dict):
                continue

            if stored_goal.get("cancelled"):
                continue

            stored_event = _stored_goal_to_event(stored_goal)
            if not isinstance(stored_event, dict):
                continue

            goal_events.append((stored_event, stored_goal))

    # Explicitly cancelled goal events can be handled without a separate VAR
    # event. They are authoritative and do not require proximity matching.
    for event in events:
        if (
            isinstance(event, dict)
            and get_event_type(event) == "goal"
            and is_cancelled_goal_event(event)
        ):
            key = event_key(event)
            if key is None or str(key) in seen_goal_keys:
                continue

            seen_goal_keys.add(str(key))
            result.append({
                "goal_key": key,
                "goal_event": event,
                "is_home": get_event_team(event),
                "minute": get_goal_minute(event),
                "cancel_reason": _extract_cancellation_reason(event),
                "cancelled_by_var": False,
            })

    # A VAR cancellation is accepted only after get_var_decision() confirms
    # an explicit final goal-cancellation phrase/flag.
    for var_event in get_cancelled_var_events(events):
        match = _find_best_goal_for_var(
            var_event,
            goal_events,
        )

        if match is None:
            continue

        goal_event, stored_goal = match

        goal_key = (
            stored_goal.get("event_key")
            if isinstance(stored_goal, dict)
            else event_key(goal_event)
        )

        if goal_key is None:
            goal_key = event_key(goal_event)

        if goal_key is None or str(goal_key) in seen_goal_keys:
            continue

        seen_goal_keys.add(str(goal_key))

        decision = get_var_decision(var_event)

        result.append({
            "goal_key": goal_key,
            "goal_event": goal_event,
            "var_event": var_event,
            "is_home": get_event_team(goal_event),
            "minute": get_goal_minute(goal_event),
            "cancel_reason": decision.get("reason"),
            "cancelled_by_var": True,
            "var_text": decision.get("text", ""),
        })

    return result


def get_cancelled_goal_keys(events, match_state=None):
    return [
        item.get("goal_key")
        for item in detect_cancelled_goals(
            events,
            match_state,
        )
        if item.get("goal_key")
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

def _pending_tbd_goal_match(
    event,
    previous_goals,
):
    """
    Fallback identity for a goal whose scorer was initially unknown.

    FotMob normally keeps the same reactKey when it enriches an event, but
    the live feed can also replace/rebuild the event. In that case the event
    key may change. We only bridge that gap when the evidence is unique:
    - stored goal is still waiting for an update;
    - both events belong to the same team;
    - the goal minute matches;
    - a known player id never conflicts;
    - exactly one pending goal is a candidate.

    If more than one candidate exists, we deliberately do not guess.
    """
    if not isinstance(event, dict):
        return None

    if get_event_type(event) != "goal":
        return None

    if is_cancelled_goal_event(event):
        return None

    new_player_name = get_event_player_name(event)
    new_player_id = get_event_player_id(event)

    if _is_missing_player_name(new_player_name):
        return None

    new_team = get_event_team(event)
    new_minute = get_event_time(event)

    if new_team is None or new_minute is None:
        return None

    candidates = []

    for stored_goal in previous_goals or []:
        if not isinstance(stored_goal, dict):
            continue

        if stored_goal.get("cancelled"):
            continue

        if not stored_goal.get("needs_update"):
            continue

        if stored_goal.get("telegram_message_id") is None:
            continue

        if not _is_missing_player_name(stored_goal.get("player_name")):
            continue

        old_event = _stored_goal_to_event(stored_goal)
        if not isinstance(old_event, dict):
            continue

        old_team = get_event_team(old_event)
        old_minute = get_event_time(old_event)

        if old_team is None or old_minute is None:
            continue

        if old_team != new_team or old_minute != new_minute:
            continue

        old_player_id = stored_goal.get("player_id")
        if old_player_id is not None and new_player_id is not None:
            if str(old_player_id) != str(new_player_id):
                continue

        candidates.append(stored_goal)

    if len(candidates) != 1:
        return None

    return candidates[0]


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

        matched_by_fallback = False

        if existing is None:
            existing = _pending_tbd_goal_match(
                event,
                previous_goals,
            )
            matched_by_fallback = existing is not None

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

        old_assist_name = (
            existing.get(
                "assist_player_name"
            )
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

            goal_info = get_goal_info(event)

            if not isinstance(goal_info, dict):
                continue

            if matched_by_fallback:
                # Preserve the original state/message identity. The current
                # FotMob event may have received a new reactKey.
                goal_info["_new_event_key"] = key
                goal_info["event_key"] = existing.get("event_key")

            result.append(goal_info)

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
        events,
        match_state,
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

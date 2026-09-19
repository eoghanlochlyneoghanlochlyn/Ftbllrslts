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

    unique_id = get_event_unique_id(
        event
    )

    if unique_id is not None:
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

    event_type = clean_text(
        first_non_empty(
            event.get("type"),
            event.get("eventType"),
            event.get("incidentType"),
            event.get("incident"),
        )
    ).lower()

    card_value = clean_text(
        first_non_empty(
            event.get("card"),
            event.get("cardType"),
            event.get("cardName"),
            event.get("cardTypeName"),
        )
    ).lower()

    description = clean_text(
        first_non_empty(
            event.get("description"),
            event.get("text"),
            event.get("incidentDescription"),
            event.get("reason"),
        )
    ).lower()

    # -----------------------------------------------------
    # سیگنال اول:
    # نوع event مستقیماً red card را اعلام کرده
    # -----------------------------------------------------

    explicit_red_type = (
        "redcard" in event_type
        or "red_card" in event_type
        or "red card" in event_type
    )

    # -----------------------------------------------------
    # سیگنال دوم:
    # فیلد کارت، red را اعلام کرده
    # -----------------------------------------------------

    explicit_red_card = (
        "red" in card_value
        and (
            "card" in card_value
            or "dismiss" in card_value
            or "sent" in card_value
        )
    )

    # -----------------------------------------------------
    # سیگنال سوم:
    # متن event اخراج / کارت قرمز را اعلام کرده
    # -----------------------------------------------------

    red_text = (
        "red card" in description
        or "red-card" in description
        or "sent off" in description
        or "sent-off" in description
        or "dismissed" in description
    )

    # -----------------------------------------------------
    # سیگنال چهارم:
    # کارت زرد دوم
    # -----------------------------------------------------

    second_yellow = (
        "second yellow" in event_type
        or "second_yellow" in event_type
        or "second yellow" in card_value
        or "second_yellow" in card_value
        or "yellow red" in card_value
        or "yellow-red" in card_value
        or "second yellow" in description
        or "second_yellow" in description
    )

    # -----------------------------------------------------
    # نتیجه
    #
    # اگر FotMob صراحتاً red card را در type داده باشد،
    # همان سیگنال معتبر است.
    #
    # اگر type فقط card باشد، باید یک سیگنال مستقل
    # دیگر مثل cardType یا متن red وجود داشته باشد.
    # -----------------------------------------------------

    if explicit_red_type:
        return True

    if second_yellow:
        return True

    if (
        event_type == "card"
        and explicit_red_card
    ):
        return True

    if (
        event_type == "card"
        and red_text
    ):
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
# تشخیص چندسیگناله شروع بازی
# =========================================================

def _normalize_period_value(value):

    if isinstance(
        value,
        dict,
    ):

        value = first_non_empty(
            value.get("name"),
            value.get("type"),
            value.get("key"),
            value.get("value"),
        )

    return clean_text(
        value
    ).lower()


def _is_live_period(value):

    normalized = _normalize_period_value(
        value
    )

    if not normalized:
        return False

    compact = (
        normalized
        .replace(" ", "")
        .replace("_", "")
        .replace("-", "")
    )

    return (
        compact in (
            "1h",
            "2h",
            "1sthalf",
            "2ndhalf",
            "firsthalf",
            "secondhalf",
            "extratime",
            "extratime1",
            "extratime2",
            "firstextra",
            "secondextra",
            "firstextrahalf",
            "secondextrahalf",
            "et",
            "aet",
            "penaltyshootout",
            "shootout",
        )
        or "firsthalf" in compact
        or "secondhalf" in compact
        or "extrahalf" in compact
        or "halfextra" in compact
        or "penaltyshootout" in compact
    )


def _snapshot_has_live_period(snapshot):

    if not isinstance(
        snapshot,
        dict,
    ):
        return False

    current_period = snapshot.get(
        "current_period"
    )

    if _is_live_period(
        current_period
    ):
        return True

    periods = snapshot.get(
        "periods"
    )

    if isinstance(
        periods,
        list,
    ):

        for period in periods:

            if _is_live_period(
                period
            ):
                return True

    elif periods is not None:

        if _is_live_period(
            periods
        ):
            return True

    return False


def _get_snapshot_score(snapshot):

    if not isinstance(
        snapshot,
        dict,
    ):
        return None

    score = snapshot.get(
        "score"
    )

    if not isinstance(
        score,
        dict,
    ):
        return None

    try:

        home = int(
            score.get(
                "home",
                0,
            )
            or 0
        )

        away = int(
            score.get(
                "away",
                0,
            )
            or 0
        )

    except (
        TypeError,
        ValueError,
    ):

        return None

    return {
        "home": max(
            0,
            home,
        ),
        "away": max(
            0,
            away,
        ),
    }


def _get_state_score(match_state):

    if not isinstance(
        match_state,
        dict,
    ):
        return {
            "home": 0,
            "away": 0,
        }

    score = {
        "home": 0,
        "away": 0,
    }

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
            continue

        is_home = goal.get(
            "is_home"
        )

        if is_home is True:
            score["home"] += 1

        elif is_home is False:
            score["away"] += 1

    return score


def _get_score_signal(
    snapshot,
    match_state,
    event=None,
):

    snapshot_score = _get_snapshot_score(
        snapshot
    )

    if snapshot_score is None:
        return None

    state_score = _get_state_score(
        match_state
    )

    home_delta = (
        snapshot_score["home"]
        - state_score["home"]
    )

    away_delta = (
        snapshot_score["away"]
        - state_score["away"]
    )

    if home_delta <= 0 and away_delta <= 0:
        return None

    event_team = None

    if isinstance(
        event,
        dict,
    ):
        event_team = get_event_team(
            event
        )

    if (
        event_team is True
        and home_delta > 0
    ):
        return "home_score"

    if (
        event_team is False
        and away_delta > 0
    ):
        return "away_score"

    if (
        event_team is None
        and (
            home_delta > 0
            or away_delta > 0
        )
    ):
        return "score"

    return None


def _goal_event_signal(event):

    if not isinstance(
        event,
        dict,
    ):
        return False

    raw_type = clean_text(
        first_non_empty(
            event.get("type"),
            event.get("eventType"),
            event.get("incidentType"),
            event.get("incident"),
        )
    ).lower()

    if "goal" in raw_type:
        return True

    if event.get(
        "isGoal"
    ) is True:
        return True

    goal_key = clean_text(
        event.get(
            "goalDescriptionKey"
        )
    ).lower()

    goal_description = clean_text(
        event.get(
            "goalDescription"
        )
    ).lower()

    if goal_key or goal_description:
        return True

    return False


def _goal_metadata_signal(event):

    if not isinstance(
        event,
        dict,
    ):
        return False

    has_team = (
        get_event_team(
            event
        ) in (
            True,
            False,
        )
    )

    has_time = (
        get_event_time(
            event
        ) is not None
    )

    has_player = (
        get_event_player_id(
            event
        ) is not None
        or not _is_missing_player_name(
            get_event_player_name(
                event
            )
        )
    )

    return (
        has_team
        and (
            has_time
            or has_player
        )
    )


def _is_reliable_goal_event(
    event,
    snapshot,
    match_state,
):

    if not isinstance(
        event,
        dict,
    ):
        return False

    if get_event_type(
        event
    ) != "goal":
        return False

    if is_cancelled_goal_event(
        event
    ):
        return False

    direct_goal = _goal_event_signal(
        event
    )

    score_signal = _get_score_signal(
        snapshot,
        match_state,
        event,
    )

    metadata_signal = _goal_metadata_signal(
        event
    )

    # -----------------------------------------------------
    # رویداد صریح گل، قوی‌ترین سیگنال است.
    #
    # بنابراین اگر FotMob واقعاً event گل را داده باشد،
    # حتی اگر score هنوز در snapshot تغییر نکرده باشد،
    # گل را از دست نمی‌دهیم.
    # -----------------------------------------------------

    if direct_goal:
        return True

    # -----------------------------------------------------
    # fallback برای event ناقص:
    #
    # تغییر score
    # +
    # اطلاعات معتبر تیم و زمان/بازیکن
    # -----------------------------------------------------

    if (
        score_signal is not None
        and metadata_signal
    ):
        return True

    return False


# =========================================================
# سیگنال زنده برای شروع بازی
# =========================================================

def _event_has_live_start_signal(event):

    if not isinstance(
        event,
        dict,
    ):
        return False

    event_type = get_event_type(
        event
    )

    normalized_type = clean_text(
        event_type
    ).lower()

    compact_type = (
        normalized_type
        .replace(" ", "")
        .replace("_", "")
        .replace("-", "")
    )

    # -----------------------------------------------------
    # سیگنال مستقیم شروع
    # -----------------------------------------------------

    if compact_type in (
        "matchstarted",
        "matchstart",
        "kickoff",
        "start",
        "started",
        "firsthalf",
        "secondhalf",
    ):
        return True

    # -----------------------------------------------------
    # رویدادهای قطعی داخل بازی
    # -----------------------------------------------------

    if event_type == "goal":
        return True

    if event_type == "card":
        return True

    if compact_type in (
        "substitution",
        "sub",
        "penalty",
        "penaltyawarded",
        "redcard",
        "yellowredcard",
    ):
        return True

    # -----------------------------------------------------
    # VAR فقط در صورت وجود نشانه زمانی/دوره بازی
    # -----------------------------------------------------

    if event_type == "var":

        event_time = get_event_time(
            event
        )

        if (
            event_time is not None
            and event_time >= 0
        ):
            return True

        if any(
            _is_live_period(
                event.get(key)
            )
            for key in (
                "period",
                "periodName",
                "periodType",
                "matchPeriod",
                "stage",
                "stageName",
            )
        ):
            return True

    # -----------------------------------------------------
    # event ناشناخته ولی دارای مشخصات معتبر بازی
    # -----------------------------------------------------

    event_time = get_event_time(
        event
    )

    if (
        event_time is not None
        and event_time >= 0
    ):

        has_team = (
            get_event_team(
                event
            )
            is not None
        )

        has_player = (
            get_event_player_id(
                event
            )
            is not None
        )

        has_type = bool(
            normalized_type
        )

        if (
            has_team
            or has_player
            or has_type
        ):

            ignored_types = (
                "lineup",
                "lineups",
                "formation",
                "player",
                "players",
                "preview",
                "pre-match",
                "prematch",
            )

            if not any(
                ignored in normalized_type
                for ignored in ignored_types
            ):
                return True

    return False


def _find_live_start_event(events):

    for event in events or []:

        if _event_has_live_start_signal(
            event
        ):
            return event

    return None


def detect_start_signal(
    snapshot,
    events,
):

    # -----------------------------------------------------
    # سیگنال 1: وضعیت رسمی FotMob
    # -----------------------------------------------------

    if (
        isinstance(
            snapshot,
            dict,
        )
        and snapshot.get(
            "started"
        )
    ):
        return "status"

    # -----------------------------------------------------
    # سیگنال 2: دوره زنده مسابقه
    # -----------------------------------------------------

    if _snapshot_has_live_period(
        snapshot
    ):
        return "period"

    # -----------------------------------------------------
    # سیگنال 3: نتیجه غیرصفر
    # -----------------------------------------------------

    score = _get_snapshot_score(
        snapshot
    )

    if (
        score is not None
        and (
            score["home"] > 0
            or score["away"] > 0
        )
    ):
        return "score"

    # -----------------------------------------------------
    # سیگنال 4: event زنده
    # -----------------------------------------------------

    live_event = _find_live_start_event(
        events
    )

    if live_event is not None:
        return "live_event"

    return None


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

        "start_reason": None,

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

        # -------------------------------------------------
        # شروع بازی
        # -------------------------------------------------

        if not match_state.get(
            "started",
            False,
        ):

            start_reason = detect_start_signal(
                snapshot,
                events,
            )

            if start_reason is not None:

                changes[
                    "start"
                ] = True

                changes[
                    "start_reason"
                ] = start_reason

        # -------------------------------------------------
        # نیمه‌وقت
        # -------------------------------------------------

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

        # -------------------------------------------------
        # پایان بازی
        # -------------------------------------------------

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

        # -------------------------------------------------
        # گل
        # -------------------------------------------------

        if event_type == "goal":

            if _is_reliable_goal_event(
                event,
                snapshot,
                match_state,
            ):

                goal_info = get_goal_info(
                    event
                )

                if goal_info is not None:

                    changes[
                        "goals"
                    ].append(
                        goal_info
                    )

        # -------------------------------------------------
        # کارت قرمز
        # -------------------------------------------------

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

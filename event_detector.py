from fotmob import (
    clean_text,
    get_event_assist_player_id,
    get_event_player_id,
    get_match_events,
)


def is_cancelled_goal_event(event):
    if not isinstance(event, dict):
        return False

    event_type = clean_text(
        event.get("type")
    ).lower()

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
        return shotmap.get("isOwnGoal") is True

    return False


def is_red_card_event(event):
    if not isinstance(event, dict):
        return False

    if clean_text(
        event.get("type")
    ).lower() != "card":
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
            description.get("localizedKey")
        ).lower()

        default_text = clean_text(
            description.get("defaultText")
        ).lower()

        if localized_key == "coach":
            return False

        if default_text == "coach":
            return False

    return True


def event_key(event, index):
    if not isinstance(event, dict):
        return f"unknown:{index}"

    event_id = event.get("id")

    if event_id is not None:
        return f"id:{event_id}"

    event_type = clean_text(
        event.get("type")
    ).lower()

    player_id = get_event_player_id(event)

    time = event.get("time")

    return (
        f"{event_type}:"
        f"{player_id}:"
        f"{time}:"
        f"{index}"
    )


def get_event_keys(events):
    return [
        event_key(event, index)
        for index, event in enumerate(events)
    ]


def detect_new_events(previous_events, current_events):
    previous = set(previous_events or [])

    new_events = []

    for index, event in enumerate(current_events or []):

        key = event_key(
            event,
            index,
        )

        if key not in previous:
            new_events.append(event)

    return new_events


def detect_goals(events):
    goals = []

    for event in events:

        if not isinstance(event, dict):
            continue

        if clean_text(
            event.get("type")
        ).lower() != "goal":
            continue

        if event.get(
            "isPenaltyShootoutEvent"
        ) is True:
            continue

        goals.append(event)

    return goals


def detect_red_cards(events):
    return [
        event
        for event in events
        if is_red_card_event(event)
    ]


def get_player_events(root):
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

    cancelled_ids = set()

    for event in events:

        if is_cancelled_goal_event(event):

            player_id = get_event_player_id(event)

            if player_id is not None:
                cancelled_ids.add(player_id)

    for event in events:

        if not isinstance(event, dict):
            continue

        event_type = clean_text(
            event.get("type")
        ).lower()

        if event_type == "goal":

            player_id = get_event_player_id(event)

            if player_id is None:
                continue

            if event.get(
                "isPenaltyShootoutEvent"
            ) is True:
                continue

            if player_id in cancelled_ids:
                continue

            data = ensure(player_id)

            data["goals"] += 1

            if is_penalty_goal(event):
                data["penalty_goals"] += 1

            assist_id = get_event_assist_player_id(event)

            if assist_id is not None:

                assist_data = ensure(assist_id)

                assist_data["assists"] += 1

        elif event_type == "card":

            if not is_red_card_event(event):
                continue

            player_id = get_event_player_id(event)

            if player_id is None:
                continue

            data = ensure(player_id)

            data["red_cards"] += 1

    return player_events


def detect_state_changes(
    previous_state,
    root,
    snapshot,
):
    previous_state = previous_state or {}

    current_events = snapshot.get(
        "events",
        [],
    )

    previous_event_keys = previous_state.get(
        "event_keys",
        [],
    )

    new_events = detect_new_events(
        previous_event_keys,
        current_events,
    )

    previous_finished = previous_state.get(
        "finished",
        False,
    )

    current_finished = snapshot.get(
        "finished",
        False,
    )

    changes = {
        "new_events": new_events,
        "new_goals": detect_goals(new_events),
        "new_red_cards": detect_red_cards(new_events),
        "finished": (
            current_finished
            and not previous_finished
        ),
    }

    return changes

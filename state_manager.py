import json
import os


STATE_FILE = "state.json"


def default_state():
    return {
        "matches": {}
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

        matches[match_id] = {
            "lineup_sent": False,
            "fallback_sent": False,
            "finished_sent": False,
            "event_keys": [],
            "finished": False,
        }

    return matches[match_id]


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

import json
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent
TEAMS_FILE = BASE_DIR / "teams.json"


def _load_teams():
    print(
        "TEAM TRANSLATION LOAD DEBUG | "
        f"file={TEAMS_FILE}"
    )

    if not TEAMS_FILE.exists():
        print(
            "TEAM TRANSLATION LOAD DEBUG | "
            "exists=False"
        )
        return {}

    try:
        file_size = TEAMS_FILE.stat().st_size
    except OSError as exc:
        print(
            "TEAM TRANSLATION LOAD DEBUG | "
            f"stat_error={exc!r}"
        )
        return {}

    print(
        "TEAM TRANSLATION LOAD DEBUG | "
        f"exists=True | size={file_size}"
    )

    try:
        with open(
            TEAMS_FILE,
            "r",
            encoding="utf-8",
        ) as file:
            data = json.load(file)

    except OSError as exc:
        print(
            "TEAM TRANSLATION LOAD DEBUG | "
            f"open_error={exc!r}"
        )
        return {}

    except json.JSONDecodeError as exc:
        print(
            "TEAM TRANSLATION LOAD DEBUG | "
            f"json_error={exc!r}"
        )
        return {}

    print(
        "TEAM TRANSLATION LOAD DEBUG | "
        f"data_type={type(data).__name__}"
    )

    if isinstance(data, list):
        print(
            "TEAM TRANSLATION LOAD DEBUG | "
            f"record_count={len(data)}"
        )

        if data:
            print(
                "TEAM TRANSLATION LOAD DEBUG | "
                f"first_record={data[0]!r}"
            )
    else:
        print(
            "TEAM TRANSLATION LOAD DEBUG | "
            "expected=list"
        )
        return {}

    result = {}
    valid_count = 0
    invalid_count = 0

    for team in data:

        if not isinstance(team, dict):
            invalid_count += 1
            continue

        team_id = team.get("id")
        persian = team.get("persian")

        if team_id is None or not persian:
            invalid_count += 1
            continue

        result[str(team_id)] = str(persian)
        valid_count += 1

    print(
        "TEAM TRANSLATION LOAD DEBUG | "
        f"valid_count={valid_count} | "
        f"invalid_count={invalid_count}"
    )

    for debug_id in ("8560", "8371"):

        print(
            "TEAM TRANSLATION LOAD DEBUG | "
            f"id={debug_id} | "
            f"translation={result.get(debug_id)!r}"
        )

    return result


_TEAM_TRANSLATIONS = _load_teams()


def get_persian_team_name(
    team_id,
    fallback_name="",
):
    if team_id is not None:

        translated = _TEAM_TRANSLATIONS.get(
            str(team_id)
        )

        if translated:
            return translated

    return fallback_name or ""

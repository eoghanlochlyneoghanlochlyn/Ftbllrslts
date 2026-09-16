```python
import json
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent
TEAMS_FILE = BASE_DIR / "teams.json"


def _load_teams():
    try:
        with open(
            TEAMS_FILE,
            "r",
            encoding="utf-8",
        ) as file:
            data = json.load(file)

    except (
        OSError,
        json.JSONDecodeError,
    ):
        return {}

    if not isinstance(data, list):
        return {}

    result = {}

    for team in data:

        if not isinstance(team, dict):
            continue

        team_id = team.get("id")
        persian = team.get("persian")

        if team_id is None:
            continue

        if not persian:
            continue

        result[str(team_id)] = str(
            persian
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
```

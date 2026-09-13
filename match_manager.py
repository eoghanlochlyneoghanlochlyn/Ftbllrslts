import json
import os


MATCHES_FILE = "matches.json"


def load_matches():
    if not os.path.exists(MATCHES_FILE):
        return []

    with open(
        MATCHES_FILE,
        "r",
        encoding="utf-8",
    ) as file:

        data = json.load(file)

    if isinstance(data, list):
        return data

    if isinstance(data, dict):

        matches = data.get("matches")

        if isinstance(matches, list):
            return matches

    return []


def get_match_id(match):
    if not isinstance(match, dict):
        return ""

    value = match.get("id")

    if value is None:
        return ""

    return str(value)


def get_match_url(match):
    if not isinstance(match, dict):
        return ""

    url = match.get("url")

    if url:
        return str(url).strip()

    match_id = get_match_id(match)

    if match_id:
        return (
            f"https://www.fotmob.com/match/"
            f"{match_id}"
        )

    return ""


def get_enabled_matches():
    matches = load_matches()

    enabled = []

    for match in matches:

        if not isinstance(match, dict):
            continue

        if match.get("enabled", True) is False:
            continue

        match_id = get_match_id(match)

        if not match_id:
            continue

        enabled.append(match)

    return enabled

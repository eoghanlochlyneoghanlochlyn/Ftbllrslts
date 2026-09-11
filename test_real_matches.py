import json
from datetime import datetime, timezone


import requests


CACHE_FILE = "matches_cache.json"


TARGET_MATCH_IDS = {
    "5868059",
    "5749679",
    "5881169",
    "5802935",
}


HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/131.0 Safari/537.36"
    )
}


def load_cache():
    try:
        with open(
            CACHE_FILE,
            "r",
            encoding="utf-8",
        ) as file:
            return json.load(file)

    except FileNotFoundError:
        print("Cache file not found.")
        return {}

    except json.JSONDecodeError:
        print("Cache file contains invalid JSON.")
        return {}


def save_cache(cache):
    with open(
        CACHE_FILE,
        "w",
        encoding="utf-8",
    ) as file:
        json.dump(
            cache,
            file,
            ensure_ascii=False,
            indent=2,
        )


def fetch_matches(date_string):
    url = (
        "https://www.fotmob.com/"
        "api/data/matches"
        f"?date={date_string}"
    )

    print(
        f"Downloading matches for {date_string}..."
    )

    response = requests.get(
        url,
        headers=HEADERS,
        timeout=30,
    )

    print(
        f"Status code: {response.status_code}"
    )

    response.raise_for_status()

    return response.json()


def determine_status(match):
    status = (
        match.get("status")
        or {}
    )

    if status.get("cancelled"):
        return "Cancelled"

    if status.get("finished"):
        return "Finished"

    if status.get("started"):
        return "Live"

    return "Upcoming"


def determine_score(match):
    status = (
        match.get("status")
        or {}
    )

    score = status.get(
        "scoreStr"
    )

    if score:
        return str(score)

    return "-"


def create_match_record(match):
    match_id = str(
        match.get("id")
    )

    league_name = str(
        match.get("leagueName")
        or ""
    ).strip()

    if not league_name:
        league = match.get(
            "league"
        )

        if isinstance(
            league,
            dict,
        ):
            league_name = str(
                league.get("name")
                or ""
            ).strip()

    home = (
        match.get("home")
        or {}
    )

    away = (
        match.get("away")
        or {}
    )

    status_data = (
        match.get("status")
        or {}
    )

    utc_time = (
        status_data.get(
            "utcTime"
        )
    )

    status = determine_status(
        match
    )

    score = determine_score(
        match
    )

    return {
        "id": match_id,
        "date": "20260911",
        "league": league_name,
        "home": str(
            home.get("name")
            or "Unknown"
        ),
        "away": str(
            away.get("name")
            or "Unknown"
        ),
        "home_id": home.get(
            "id"
        ),
        "away_id": away.get(
            "id"
        ),
        "utc_time": utc_time,
        "iran_time": None,
        "status": status,
        "score": score,
        "url": (
            f"https://www.fotmob.com/"
            f"match/{match_id}"
        ),
        "pre_match_sent": False,
        "lineup_sent": False,
        "finished_sent": False,
        "sent_goal_ids": [],
        "last_status": status,
        "last_score": score,
    }


def main():
    print(
        "Real Match Test"
    )

    print(
        "=" * 90
    )

    cache = load_cache()

    data = fetch_matches(
        "20260911"
    )

    found_matches = {}

    for league in (
        data.get("leagues")
        or []
    ):
        matches = (
            league.get("matches")
            or []
        )

        for match in matches:
            match_id = str(
                match.get("id")
            )

            if (
                match_id
                in TARGET_MATCH_IDS
            ):
                found_matches[
                    match_id
                ] = match

    print()
    print(
        f"Target matches requested: "
        f"{len(TARGET_MATCH_IDS)}"
    )

    print(
        f"Target matches found: "
        f"{len(found_matches)}"
    )

    print()

    missing = (
        TARGET_MATCH_IDS
        - set(found_matches.keys())
    )

    if missing:
        print(
            "WARNING: These match IDs "
            "were not found:"
        )

        for match_id in sorted(
            missing
        ):
            print(
                f"  {match_id}"
            )

        print()

    for match_id in sorted(
        found_matches.keys()
    ):
        match = found_matches[
            match_id
        ]

        new_record = (
            create_match_record(
                match
            )
        )

        old_record = cache.get(
            match_id
        )

        if old_record:
            new_record[
                "pre_match_sent"
            ] = old_record.get(
                "pre_match_sent",
                False,
            )

            new_record[
                "lineup_sent"
            ] = old_record.get(
                "lineup_sent",
                False,
            )

            new_record[
                "finished_sent"
            ] = old_record.get(
                "finished_sent",
                False,
            )

            new_record[
                "sent_goal_ids"
            ] = old_record.get(
                "sent_goal_ids",
                [],
            )

            new_record[
                "last_pre_match_sent_at"
            ] = old_record.get(
                "last_pre_match_sent_at"
            )

        cache[
            match_id
        ] = new_record

        print(
            f"FOUND: "
            f"{new_record['home']} 🆚 "
            f"{new_record['away']}"
        )

        print(
            f"  ID: {match_id}"
        )

        print(
            f"  League: "
            f"{new_record['league']}"
        )

        print(
            f"  UTC: "
            f"{new_record['utc_time']}"
        )

        print(
            f"  Status: "
            f"{new_record['status']}"
        )

        print(
            f"  Score: "
            f"{new_record['score']}"
        )

        print()

    if not found_matches:
        print(
            "No target matches were found."
        )

        return

    save_cache(cache)

    print(
        "=" * 90
    )

    print(
        "matches_cache.json updated."
    )

    print(
        f"Total cached matches: "
        f"{len(cache)}"
    )

    print(
        "=" * 90
    )


if __name__ == "__main__":
    main()

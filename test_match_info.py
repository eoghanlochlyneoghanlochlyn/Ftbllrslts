import json
import requests

from collections import defaultdict
from datetime import datetime
from zoneinfo import ZoneInfo


IRAN_TZ = ZoneInfo("Asia/Tehran")

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/140.0.0.0 Safari/537.36"
    )
}


def fetch_matches_for_date(date):
    url = f"https://www.fotmob.com/api/data/matches?date={date}"

    print()
    print(f"Downloading matches for {date}...")

    response = requests.get(url, headers=HEADERS, timeout=30)

    print("Status code:", response.status_code)
    response.raise_for_status()

    return response.json()


def clean_value(value):
    if isinstance(value, (dict, list)):
        return json.dumps(value, ensure_ascii=False, sort_keys=True)
    return str(value)


def get_team_name(team):
    if not isinstance(team, dict):
        return "Unknown"

    return (
        team.get("longName")
        or team.get("name")
        or team.get("shortName")
        or "Unknown"
    )


def utc_to_iran(utc_time):
    if not utc_time:
        return "Unknown"

    try:
        dt = datetime.fromisoformat(utc_time.replace("Z", "+00:00"))
        return dt.astimezone(IRAN_TZ).strftime("%Y-%m-%d %H:%M")
    except Exception:
        return "Unknown"


def main():
    now_iran = datetime.now(IRAN_TZ)
    date = now_iran.strftime("%Y%m%d")

    data = fetch_matches_for_date(date)

    print()
    print("=" * 120)
    print("FOTMOB COMPETITION ID DISCOVERY TEST")
    print("=" * 120)
    print("Iran now:", now_iran.strftime("%Y-%m-%d %H:%M:%S"))
    print("Date:", date)

    leagues = data.get("leagues", [])
    total_matches = sum(len(league.get("matches", [])) for league in leagues)

    print("Leagues:", len(leagues))
    print("Total matches:", total_matches)
    print("=" * 120)

    print()
    print("ALL COMPETITIONS FOUND TODAY")
    print("-" * 120)

    for league in leagues:
        league_name = league.get("name", "Unknown League")

        # Print every possible ID-like field directly present on the league object.
        id_fields = {
            key: value
            for key, value in league.items()
            if "id" in str(key).lower()
        }

        print()
        print(f"COMPETITION: {league_name}")
        print(f"  ID fields: {clean_value(id_fields)}")
        print(f"  Top-level keys: {', '.join(sorted(league.keys()))}")
        print(f"  Matches: {len(league.get('matches', []))}")

        # Show one representative match so we can see whether the competition
        # identity is also repeated inside each match.
        matches = league.get("matches", [])
        if matches:
            sample = matches[0]

            match_id_fields = {
                key: value
                for key, value in sample.items()
                if "id" in str(key).lower()
            }

            print(
                f"  Sample: {get_team_name(sample.get('home'))} vs "
                f"{get_team_name(sample.get('away'))}"
            )
            print(f"  Match ID fields: {clean_value(match_id_fields)}")
            print(
                f"  tournamentStage: "
                f"{clean_value(sample.get('tournamentStage', 'MISSING'))}"
            )

    print()
    print("=" * 120)
    print("TARGET ID CROSS-CHECK")
    print("=" * 120)

    try:
        with open("auto_matches.json", "r", encoding="utf-8") as file:
            config = json.load(file)
    except Exception as exc:
        print("Could not read auto_matches.json:", exc)
        return

    configured_ids = {
        str(item.get("id"))
        for item in config.get("competitions", [])
        if item.get("id") is not None
    }

    print("Configured competition IDs:")
    print("  " + ", ".join(sorted(configured_ids, key=lambda x: (len(x), x))))

    found_candidates = defaultdict(list)

    for league in leagues:
        league_name = league.get("name", "Unknown League")

        for key, value in league.items():
            if "id" in str(key).lower() and value is not None:
                value_str = str(value)

                if value_str in configured_ids:
                    found_candidates[value_str].append(
                        (league_name, key, value)
                    )

    print()
    if found_candidates:
        print("Configured IDs found directly in today's endpoint:")
        for competition_id, hits in sorted(found_candidates.items()):
            for league_name, key, value in hits:
                print(
                    f"  {competition_id} -> {league_name} "
                    f"({key}={value})"
                )
    else:
        print(
            "NONE of the configured IDs were found directly in the league "
            "objects."
        )

    print()
    print("=" * 120)
    print("END OF COMPETITION ID DISCOVERY TEST")
    print("=" * 120)


if __name__ == "__main__":
    main()

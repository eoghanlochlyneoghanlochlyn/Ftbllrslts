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


def utc_to_iran(utc_time):
    if not utc_time:
        return "Unknown"

    try:
        dt = datetime.fromisoformat(utc_time.replace("Z", "+00:00"))
        return dt.astimezone(IRAN_TZ).strftime("%Y-%m-%d %H:%M")
    except Exception:
        return "Unknown"


def get_team_name(team):
    if not isinstance(team, dict):
        return "Unknown"

    return (
        team.get("longName")
        or team.get("name")
        or team.get("shortName")
        or "Unknown"
    )


def fetch_matches_for_date(date):
    url = f"https://www.fotmob.com/api/data/matches?date={date}"

    print()
    print(f"Downloading matches for {date}...")

    response = requests.get(url, headers=HEADERS, timeout=30)

    print("Status code:", response.status_code)
    response.raise_for_status()

    return response.json()


def get_stage_value(match):
    value = match.get("tournamentStage")

    if value is None:
        return "MISSING"

    if isinstance(value, (dict, list)):
        return json.dumps(value, ensure_ascii=False, sort_keys=True)

    return str(value)


def main():
    now_iran = datetime.now(IRAN_TZ)
    date = now_iran.strftime("%Y%m%d")

    data = fetch_matches_for_date(date)

    grouped = defaultdict(lambda: defaultdict(list))
    total_matches = 0

    for league in data.get("leagues", []):
        league_name = league.get("name", "Unknown League")
        league_id = (
            league.get("primaryId")
            or league.get("id")
            or league.get("leagueId")
            or league.get("competitionId")
        )

        for match in league.get("matches", []):
            total_matches += 1

            stage = get_stage_value(match)

            grouped[(str(league_id), league_name)][stage].append(
                {
                    "id": match.get("id"),
                    "home": get_team_name(match.get("home")),
                    "away": get_team_name(match.get("away")),
                    "utc": match.get("status", {}).get("utcTime"),
                    "iran": utc_to_iran(
                        match.get("status", {}).get("utcTime")
                    ),
                }
            )

    print()
    print("=" * 110)
    print("FOTMOB TOURNAMENT STAGE GROUPING TEST")
    print("=" * 110)
    print("Iran now:", now_iran.strftime("%Y-%m-%d %H:%M:%S"))
    print("Date:", date)
    print("Total matches:", total_matches)
    print("Unique competitions:", len(grouped))
    print("=" * 110)

    for (league_id, league_name), stages in sorted(
        grouped.items(),
        key=lambda item: (item[0][1].lower(), item[0][0]),
    ):
        print()
        print("-" * 110)
        print(f"{league_name} (competition ID: {league_id})")
        print("-" * 110)

        for stage, matches in sorted(stages.items(), key=lambda item: item[0]):
            print(f"  tournamentStage = {stage!r} | matches = {len(matches)}")

            for match in matches[:3]:
                print(
                    f"    - {match['home']} vs {match['away']} "
                    f"| match={match['id']} "
                    f"| Iran={match['iran']}"
                )

            if len(matches) > 3:
                print(f"    ... +{len(matches) - 3} more")

    print()
    print("=" * 110)
    print("END OF GROUPING TEST")
    print("=" * 110)


if __name__ == "__main__":
    main()

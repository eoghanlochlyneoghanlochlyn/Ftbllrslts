import json
import requests

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
        dt = datetime.fromisoformat(
            utc_time.replace("Z", "+00:00")
        )
        return dt.astimezone(IRAN_TZ).strftime("%Y-%m-%d %H:%M")
    except Exception:
        return "Unknown"


def find_stage_like_fields(value, path=""):
    """فقط فیلدهایی را پیدا می‌کند که احتمال دارد اطلاعات مرحله/راند داشته باشند."""
    found = []

    if isinstance(value, dict):
        for key, child in value.items():
            child_path = f"{path}.{key}" if path else key
            key_lower = str(key).lower()

            if any(
                token in key_lower
                for token in (
                    "stage",
                    "round",
                    "phase",
                    "leg",
                    "aggregate",
                    "matchday",
                    "matchweek",
                )
            ):
                found.append(
                    {
                        "path": child_path,
                        "value": child,
                    }
                )

            found.extend(
                find_stage_like_fields(
                    child,
                    child_path,
                )
            )

    elif isinstance(value, list):
        for index, child in enumerate(value):
            found.extend(
                find_stage_like_fields(
                    child,
                    f"{path}[{index}]",
                )
            )

    return found


def get_team_name(team):
    if not isinstance(team, dict):
        return "Unknown"

    return (
        team.get("longName")
        or team.get("name")
        or team.get("shortName")
        or "Unknown"
    )


def get_match_time(match):
    status = match.get("status", {})
    utc_time = status.get("utcTime")

    return utc_time, utc_to_iran(utc_time)


def fetch_matches_for_date(date):
    url = (
        "https://www.fotmob.com/api/data/matches"
        f"?date={date}"
    )

    print()
    print(f"Downloading matches for {date}...")

    response = requests.get(
        url,
        headers=HEADERS,
        timeout=30,
    )

    print("Status code:", response.status_code)
    response.raise_for_status()

    return response.json()


def main():
    now_iran = datetime.now(IRAN_TZ)

    # فقط یک روز را بررسی می‌کنیم تا تست سریع بماند.
    date = now_iran.strftime("%Y%m%d")

    data = fetch_matches_for_date(date)

    all_matches = []

    for league in data.get("leagues", []):
        league_name = league.get("name", "Unknown League")
        league_id = (
            league.get("id")
            or league.get("leagueId")
            or league.get("competitionId")
        )

        for match in league.get("matches", []):
            all_matches.append(
                {
                    "league": league_name,
                    "league_id": league_id,
                    "match": match,
                }
            )

    print()
    print("=" * 100)
    print("RAW MATCH LIST STRUCTURE TEST")
    print("=" * 100)
    print("Iran now:", now_iran.strftime("%Y-%m-%d %H:%M:%S"))
    print("Total matches:", len(all_matches))
    print("Only the first 15 matches will be inspected.")
    print("=" * 100)

    for index, item in enumerate(all_matches[:15], start=1):
        match = item["match"]
        home = get_team_name(match.get("home"))
        away = get_team_name(match.get("away"))
        utc_time, iran_time = get_match_time(match)

        print()
        print("-" * 100)
        print(f"{index}. {home} 🆚 {away}")
        print(f"Competition: {item['league']}")
        print(f"Competition ID: {item['league_id']}")
        print(f"Match ID: {match.get('id')}")
        print(f"UTC: {utc_time}")
        print(f"Iran: {iran_time}")

        print()
        print("TOP-LEVEL MATCH KEYS:")
        print(
            json.dumps(
                list(match.keys()),
                ensure_ascii=False,
                indent=2,
            )
        )

        print()
        print("STAGE / ROUND / LEG / AGGREGATE-LIKE FIELDS:")
        stage_fields = find_stage_like_fields(match)

        if stage_fields:
            print(
                json.dumps(
                    stage_fields,
                    ensure_ascii=False,
                    indent=2,
                )
            )
        else:
            print("NONE FOUND")

        print()
        print("RAW MATCH OBJECT:")
        print(
            json.dumps(
                match,
                ensure_ascii=False,
                indent=2,
            )
        )

    print()
    print("=" * 100)
    print("END OF STRUCTURE TEST")
    print("=" * 100)


if __name__ == "__main__":
    main()

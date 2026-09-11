import requests

from datetime import datetime
from zoneinfo import ZoneInfo


DATE = "20260910"


TARGET_TEAMS = {
    8650: "Liverpool",
    9825: "Arsenal",
    8456: "Manchester City",
    10260: "Manchester United",
    8455: "Chelsea",
    8586: "Tottenham Hotspur",
    9885: "Juventus",
    8564: "AC Milan",
    8636: "Inter Milan",
    9823: "Bayern Munich",
    9789: "Borussia Dortmund",
    9847: "Paris Saint-Germain",
    8633: "Real Madrid",
    8634: "Barcelona",
    9906: "Atlético Madrid",
}


URL = f"https://www.fotmob.com/api/data/matches?date={DATE}"


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

        return dt.astimezone(
            ZoneInfo("Asia/Tehran")
        ).strftime("%Y-%m-%d %H:%M")

    except Exception:
        return "Unknown"


def get_match_status(match):
    status = match.get("status", {})

    if status.get("cancelled"):
        return "Cancelled"

    if status.get("finished"):
        return "Finished"

    if status.get("started"):
        return "Live"

    return "Upcoming"


def is_target_match(match):
    home = match.get("home", {})
    away = match.get("away", {})

    home_id = home.get("id")
    away_id = away.get("id")

    return (
        home_id in TARGET_TEAMS
        or away_id in TARGET_TEAMS
    )


def format_match(match, league_name):
    home = match.get("home", {})
    away = match.get("away", {})
    status = match.get("status", {})

    home_id = home.get("id")
    away_id = away.get("id")

    home_name = home.get("longName") or home.get("name", "Unknown")
    away_name = away.get("longName") or away.get("name", "Unknown")

    utc_time = status.get("utcTime")

    home_score = home.get("score")
    away_score = away.get("score")

    match_status = get_match_status(match)

    if match_status == "Upcoming":
        score_text = "-"

    else:
        score_text = (
            f"{home_score if home_score is not None else 0}"
            f" - "
            f"{away_score if away_score is not None else 0}"
        )

    return {
        "id": match.get("id"),
        "league": league_name,
        "home": home_name,
        "away": away_name,
        "home_id": home_id,
        "away_id": away_id,
        "utc_time": utc_time,
        "iran_time": utc_to_iran(utc_time),
        "status": match_status,
        "score": score_text,
        "url": f"https://www.fotmob.com/match/{match.get('id')}",
    }


def main():
    print(f"Downloading matches for {DATE}...")

    response = requests.get(
        URL,
        headers=HEADERS,
        timeout=30,
    )

    print("Status code:", response.status_code)

    if response.status_code != 200:
        raise Exception(
            f"FotMob request failed: {response.status_code}"
        )

    data = response.json()

    found_matches = []

    for league in data.get("leagues", []):
        league_name = league.get("name", "Unknown League")

        for match in league.get("matches", []):
            if not is_target_match(match):
                continue

            found_matches.append(
                format_match(
                    match,
                    league_name,
                )
            )

    found_matches.sort(
        key=lambda match: match.get("utc_time") or ""
    )

    print("")
    print("=" * 60)
    print(f"Target matches found: {len(found_matches)}")
    print("=" * 60)
    print("")

    if not found_matches:
        print("No target matches found.")
        return

    for index, match in enumerate(found_matches, start=1):
        print(f"{index}. {match['home']} 🆚 {match['away']}")
        print(f"   Competition: {match['league']}")
        print(f"   Match ID: {match['id']}")
        print(f"   UTC: {match['utc_time']}")
        print(f"   Iran: {match['iran_time']}")
        print(f"   Status: {match['status']}")
        print(f"   Score: {match['score']}")
        print(f"   URL: {match['url']}")
        print("")


if __name__ == "__main__":
    main()

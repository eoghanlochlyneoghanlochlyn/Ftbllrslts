import requests

from datetime import datetime, timedelta
from zoneinfo import ZoneInfo


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

    return (
        home.get("id") in TARGET_TEAMS
        or away.get("id") in TARGET_TEAMS
    )


def format_match(match, league_name, date):
    home = match.get("home", {})
    away = match.get("away", {})
    status = match.get("status", {})

    home_name = (
        home.get("longName")
        or home.get("name")
        or "Unknown"
    )

    away_name = (
        away.get("longName")
        or away.get("name")
        or "Unknown"
    )

    match_status = get_match_status(match)

    home_score = home.get("score")
    away_score = away.get("score")

    if match_status == "Upcoming":
        score_text = "-"
    else:
        score_text = (
            f"{home_score if home_score is not None else 0}"
            f" - "
            f"{away_score if away_score is not None else 0}"
        )

    utc_time = status.get("utcTime")

    return {
        "id": match.get("id"),
        "date": date,
        "league": league_name,
        "home": home_name,
        "away": away_name,
        "home_id": home.get("id"),
        "away_id": away.get("id"),
        "utc_time": utc_time,
        "iran_time": utc_to_iran(utc_time),
        "status": match_status,
        "score": score_text,
        "url": f"https://www.fotmob.com/match/{match.get('id')}",
    }


def fetch_matches_for_date(date):
    url = (
        "https://www.fotmob.com/api/data/matches"
        f"?date={date}"
    )

    print(f"Downloading matches for {date}...")

    response = requests.get(
        url,
        headers=HEADERS,
        timeout=30,
    )

    print("Status code:", response.status_code)

    if response.status_code != 200:
        print(f"Failed to download matches for {date}")
        return []

    data = response.json()

    found_matches = []

    for league in data.get("leagues", []):
        league_name = league.get(
            "name",
            "Unknown League",
        )

        for match in league.get("matches", []):
            if not is_target_match(match):
                continue

            found_matches.append(
                format_match(
                    match,
                    league_name,
                    date,
                )
            )

    return found_matches


def main():
    today = datetime.now(
        ZoneInfo("Asia/Tehran")
    ).date()

    dates = [
        today,
        today + timedelta(days=1),
    ]

    all_matches = []

    for current_date in dates:
        date_string = current_date.strftime("%Y%m%d")

        matches = fetch_matches_for_date(date_string)

        all_matches.extend(matches)

    all_matches.sort(
        key=lambda match: match.get("utc_time") or ""
    )

    print("")
    print("=" * 60)
    print(f"Target matches found: {len(all_matches)}")
    print("=" * 60)
    print("")

    if not all_matches:
        print("No target matches found.")
        return

    for index, match in enumerate(
        all_matches,
        start=1,
    ):
        print(
            f"{index}. "
            f"{match['home']} 🆚 {match['away']}"
        )

        print(f"   Competition: {match['league']}")
        print(f"   Match ID: {match['id']}")
        print(f"   Date: {match['date']}")
        print(f"   UTC: {match['utc_time']}")
        print(f"   Iran: {match['iran_time']}")
        print(f"   Status: {match['status']}")
        print(f"   Score: {match['score']}")
        print(f"   URL: {match['url']}")
        print("")


if __name__ == "__main__":
    main()

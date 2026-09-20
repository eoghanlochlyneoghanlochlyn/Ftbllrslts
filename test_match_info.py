import json
import requests

from datetime import datetime, timedelta
from zoneinfo import ZoneInfo


IRAN_TZ = ZoneInfo("Asia/Tehran")
AUTO_MATCHES_FILE = "auto_matches.json"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/140.0.0.0 Safari/537.36"
    )
}


def load_auto_config():
    with open(AUTO_MATCHES_FILE, "r", encoding="utf-8") as file:
        return json.load(file)


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


def get_match_status(match):
    status = match.get("status", {})

    if status.get("cancelled"):
        return "Cancelled"

    if status.get("finished"):
        return "Finished"

    if status.get("started"):
        return "Live"

    return "Upcoming"


def get_competition_id(league):
    value = (
        league.get("id")
        or league.get("leagueId")
        or league.get("competitionId")
    )

    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def get_stage_text(match, league):
    candidates = [
        match.get("stage"),
        match.get("round"),
        match.get("roundName"),
        match.get("stageName"),
        league.get("stage"),
        league.get("round"),
        league.get("roundName"),
        league.get("stageName"),
    ]

    for value in candidates:
        if isinstance(value, dict):
            value = (
                value.get("name")
                or value.get("slug")
                or value.get("type")
            )

        if value:
            return str(value)

    return ""


def normalize_stage(value):
    if not value:
        return ""

    text = str(value).strip().lower()
    text = text.replace("-", "_").replace(" ", "_")

    aliases = {
        "roundof16": "round_of_16",
        "last_16": "round_of_16",
        "last16": "round_of_16",
        "quarterfinal": "quarter_final",
        "quarterfinals": "quarter_final",
        "semifinal": "semi_final",
        "semifinals": "semi_final",
    }

    return aliases.get(text, text)


def team_name(team):
    if not isinstance(team, dict):
        return ""

    return (
        team.get("longName")
        or team.get("name")
        or team.get("shortName")
        or ""
    ).strip()


def team_name_matches(team, names):
    actual = team_name(team).lower()

    if not actual:
        return False

    for name in names:
        wanted = str(name).strip().lower()

        if (
            actual == wanted
            or actual in wanted
            or wanted in actual
        ):
            return True

    return False


def get_match_rule_reasons(match, league, config):
    return ["all_matches"]

def format_match(match, league, date, reasons):
    home = match.get("home", {})
    away = match.get("away", {})
    status = match.get("status", {})

    home_name = team_name(home) or "Unknown"
    away_name = team_name(away) or "Unknown"

    match_status = get_match_status(match)

    if match_status == "Upcoming":
        score_text = "-"
    else:
        score_text = (
            f"{home.get('score', 0)} - "
            f"{away.get('score', 0)}"
        )

    utc_time = status.get("utcTime")

    return {
        "id": match.get("id"),
        "date": date,
        "league": league.get(
            "name",
            "Unknown League",
        ),
        "competition_id": get_competition_id(league),
        "stage": get_stage_text(match, league),
        "home": home_name,
        "away": away_name,
        "home_id": home.get("id"),
        "away_id": away.get("id"),
        "utc_time": utc_time,
        "iran_time": utc_to_iran(utc_time),
        "status": match_status,
        "score": score_text,
        "reasons": reasons,
        "url": (
            f"https://www.fotmob.com/match/"
            f"{match.get('id')}"
        ),
    }


def fetch_matches_for_date(date, config):
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

    print(
        "Status code:",
        response.status_code,
    )

    response.raise_for_status()

    data = response.json()
    found_matches = []

    for league in data.get("leagues", []):
        for match in league.get("matches", []):
            reasons = get_match_rule_reasons(
                match,
                league,
                config,
            )

            if not reasons:
                continue

            found_matches.append(
                format_match(
                    match,
                    league,
                    date,
                    reasons,
                )
            )

    return found_matches


def build_auto_matches(matches):
    result = []
    seen = set()

    for match in matches:
        match_id = match.get("id")

        if match_id is None:
            continue

        match_id = str(match_id)

        if match_id in seen:
            continue

        seen.add(match_id)

        result.append(
            {
                "id": match_id,
                "url": match.get("url"),
                "enabled": True,
            }
        )

    return result


def main():
    config = load_auto_config()

    now_iran = datetime.now(IRAN_TZ)

    window_hours = float(
        config.get("window_hours", 24)
    )

    window_end = (
        now_iran
        + timedelta(hours=window_hours)
    )

    dates = [now_iran.date()]

    if window_end.date() > now_iran.date():
        dates.append(window_end.date())

    all_matches = []

    for current_date in dates:
        all_matches.extend(
            fetch_matches_for_date(
                current_date.strftime("%Y%m%d"),
                config,
            )
        )

    # پنجره زمانی دقیق بر اساس ساعت ایران
    filtered_matches = []

    for match in all_matches:
        utc_time = match.get("utc_time")

        if not utc_time:
            continue

        try:
            match_time = datetime.fromisoformat(
                utc_time.replace("Z", "+00:00")
            ).astimezone(IRAN_TZ)
        except Exception:
            continue

        if (
            now_iran
            <= match_time
            <= window_end
        ):
            filtered_matches.append(match)

    filtered_matches.sort(
        key=lambda match: match.get("utc_time") or ""
    )

    auto_matches = build_auto_matches(
        filtered_matches
    )

    print()
    print("=" * 80)
    print("AUTO MATCH EXTRACTION")
    print("=" * 80)
    print(
        "Iran now:",
        now_iran.strftime(
            "%Y-%m-%d %H:%M:%S"
        ),
    )
    print(
        "Window:",
        f"{window_hours:g} hours",
    )
    print(
        "Matches found:",
        len(filtered_matches),
    )
    print("=" * 80)

    for index, match in enumerate(
        filtered_matches,
        start=1,
    ):
        print()
        print(
            f"{index}. "
            f"{match['home']} 🆚 {match['away']}"
        )
        print(
            f"   Competition: "
            f"{match['league']}"
        )
        print(
            f"   Competition ID: "
            f"{match['competition_id']}"
        )
        print(
            f"   Stage: "
            f"{match['stage'] or 'Unknown'}"
        )
        print(
            f"   Match ID: "
            f"{match['id']}"
        )
        print(
            f"   Iran: "
            f"{match['iran_time']}"
        )
        print(
            f"   Status: "
            f"{match['status']}"
        )
        print(
            f"   Score: "
            f"{match['score']}"
        )
        print(
            "   Reason: "
            + " | ".join(match["reasons"])
        )
        print(
            f"   URL: "
            f"{match['url']}"
        )

    print()
    print("=" * 80)
    print("AUTO MATCHES JSON")
    print("=" * 80)

    print(
        json.dumps(
            auto_matches,
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()

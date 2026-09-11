import json
import re
from datetime import datetime, timezone

import requests


CACHE_FILE = "matches_cache.json"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 Chrome/131.0 Safari/537.36"
    )
}


PERSIAN_LEAGUES = {
    "Premier League": "لیگ برتر انگلیس",
    "LaLiga": "لالیگا",
    "Serie A": "سری آ ایتالیا",
    "Bundesliga": "بوندس‌لیگا",
    "Ligue 1": "لیگ یک فرانسه",
    "Champions League": "لیگ قهرمانان اروپا",
    "Europa League": "لیگ اروپا",
    "Conference League": "لیگ کنفرانس اروپا",
    "FA Cup": "جام حذفی انگلیس",
    "EFL Cup": "جام اتحادیه انگلیس",
    "Copa del Rey": "جام حذفی اسپانیا",
    "DFB Pokal": "جام حذفی آلمان",
    "Coppa Italia": "جام حذفی ایتالیا",
    "Coupe de France": "جام حذفی فرانسه",
}


PERSIAN_TEAM_NAMES = {
    "Manchester United": "منچستریونایتد",
    "Manchester City": "منچسترسیتی",
    "Liverpool": "لیورپول",
    "Arsenal": "آرسنال",
    "Chelsea": "چلسی",
    "Tottenham Hotspur": "تاتنهام",
    "Juventus": "یوونتوس",
    "AC Milan": "میلان",
    "Inter Milan": "اینتر",
    "Inter": "اینتر",
    "Bayern Munich": "بایرن مونیخ",
    "Borussia Dortmund": "بوروسیا دورتموند",
    "Paris Saint-Germain": "پاری‌سن‌ژرمن",
    "PSG": "پاری‌سن‌ژرمن",
    "Real Madrid": "رئال مادرید",
    "Barcelona": "بارسلونا",
    "Atletico Madrid": "اتلتیکومادرید",
    "Atlético Madrid": "اتلتیکومادرید",
    "Hull City": "هال سیتی",
    "Fulham": "فولام",
    "Everton": "اورتون",
    "Sunderland": "ساندرلند",
    "Lazio": "لاتزیو",
    "Milan": "میلان",
}


def load_cache():
    try:
        with open(CACHE_FILE, "r", encoding="utf-8") as file:
            return json.load(file)

    except FileNotFoundError:
        print("Cache file not found.")
        return {}

    except json.JSONDecodeError:
        print("Cache file contains invalid JSON.")
        return {}


def parse_utc_datetime(value):
    if not value:
        return None

    try:
        if value.endswith("Z"):
            value = value[:-1] + "+00:00"

        dt = datetime.fromisoformat(value)

        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)

        return dt.astimezone(timezone.utc)

    except (ValueError, TypeError):
        return None


def format_iran_time(utc_time):
    dt = parse_utc_datetime(utc_time)

    if dt is None:
        return "نامشخص"

    from datetime import timedelta

    iran_time = dt + timedelta(hours=3, minutes=30)

    return iran_time.strftime("%H:%M")


def fetch_match_page(match_id):
    url = f"https://www.fotmob.com/match/{match_id}"

    try:
        response = requests.get(
            url,
            headers=HEADERS,
            timeout=20,
        )

        if response.status_code != 200:
            print(
                f"Could not fetch match {match_id}. "
                f"HTTP status: {response.status_code}"
            )
            return None

        match = re.search(
            r'<script id="__NEXT_DATA__" type="application/json">(.*?)</script>',
            response.text,
            re.DOTALL,
        )

        if not match:
            print(f"__NEXT_DATA__ not found for match {match_id}.")
            return None

        return json.loads(match.group(1))

    except requests.RequestException as exc:
        print(f"Request error for match {match_id}: {exc}")
        return None

    except json.JSONDecodeError:
        print(f"Invalid JSON for match {match_id}.")
        return None


def get_page_data(data):
    try:
        return data["props"]["pageProps"]

    except (KeyError, TypeError):
        return {}


def get_lineup_data(page):
    content = page.get("content") or {}
    lineup = content.get("lineup") or {}

    return lineup


def get_team_name(team_data, fallback_name):
    if not isinstance(team_data, dict):
        return fallback_name

    for key in ("name", "teamName", "shortName"):
        value = team_data.get(key)

        if value:
            return str(value)

    return fallback_name


def get_coach_name(team_data):
    if not isinstance(team_data, dict):
        return "Unknown"

    coach = team_data.get("coach")

    if isinstance(coach, dict):
        for key in ("name", "shortName", "fullName"):
            value = coach.get(key)

            if value:
                return str(value)

    if isinstance(coach, str) and coach.strip():
        return coach.strip()

    return "Unknown"


def get_formation(team_data):
    if not isinstance(team_data, dict):
        return "Unknown"

    for key in ("formation", "expectedFormation"):
        value = team_data.get(key)

        if value:
            return str(value)

    return "Unknown"


def get_starters(team_data):
    if not isinstance(team_data, dict):
        return []

    starters = team_data.get("starters")

    if isinstance(starters, list):
        return starters

    return []


def get_player_name(player):
    if not isinstance(player, dict):
        return "Unknown"

    for key in (
        "name",
        "playerName",
        "shortName",
        "fullName",
    ):
        value = player.get(key)

        if value:
            return str(value)

    player_info = player.get("player")

    if isinstance(player_info, dict):
        for key in (
            "name",
            "shortName",
            "fullName",
        ):
            value = player_info.get(key)

            if value:
                return str(value)

    return "Unknown"


def get_player_position(player):
    if not isinstance(player, dict):
        return ""

    for key in ("position", "role", "positionName"):
        value = player.get(key)

        if value:
            return str(value)

    return ""


def get_player_number(player):
    if not isinstance(player, dict):
        return ""

    for key in ("shirtNumber", "number", "jerseyNumber"):
        value = player.get(key)

        if value is not None:
            return str(value)

    return ""


def format_player(player):
    name = get_player_name(player)
    number = get_player_number(player)

    if number:
        return f"{number}. {name}"

    return name


def translate_league(league_name):
    if not league_name:
        return "نامشخص"

    return PERSIAN_LEAGUES.get(
        league_name,
        league_name,
    )


def translate_team(team_name):
    if not team_name:
        return "نامشخص"

    return PERSIAN_TEAM_NAMES.get(
        team_name,
        team_name,
    )


def build_team_section(team_name, team_data):
    lines = []

    lines.append(team_name)

    coach = get_coach_name(team_data)
    formation = get_formation(team_data)
    starters = get_starters(team_data)

    lines.append(f"Coach: {coach}")
    lines.append(f"Formation: {formation}")

    if starters:
        lines.append("")
        lines.append("Starting XI:")

        for player in starters:
            lines.append(format_player(player))

    return "\n".join(lines)


def build_pre_match_post(match, page, lineup):
    home = match.get("home", "Unknown")
    away = match.get("away", "Unknown")
    league = match.get("league", "Unknown")
    utc_time = match.get("utc_time")

    home_team_data = lineup.get("homeTeam") or {}
    away_team_data = lineup.get("awayTeam") or {}

    lineup_type = str(
        lineup.get("lineupType") or ""
    ).lower()

    official_lineups = (
        lineup_type == "confirmed"
        and len(get_starters(home_team_data)) > 0
        and len(get_starters(away_team_data)) > 0
    )

    persian_league = translate_league(league)
    persian_home = translate_team(home)
    persian_away = translate_team(away)
    iran_time = format_iran_time(utc_time)

    lines = []

    lines.append(f"🏆 {persian_league}")
    lines.append("")
    lines.append(
        f"{persian_home} 🆚 {persian_away}"
    )
    lines.append("")
    lines.append(
        f"⏰ {iran_time} به وقت ایران"
    )
    lines.append("")
    lines.append("━━━━━━━━━━━━━━━━━━━━━━")
    lines.append("")

    if official_lineups:
        lines.append(
            build_team_section(
                home,
                home_team_data,
            )
        )

        lines.append("")
        lines.append("━━━━━━━━━━━━━━━━━━━━━━")
        lines.append("")

        lines.append(
            build_team_section(
                away,
                away_team_data,
            )
        )

    else:
        lines.append(
            "ترکیب رسمی هنوز اعلام نشده است."
        )

    return "\n".join(lines)


def process_match(match_id, match):
    print()
    print("=" * 80)
    print(
        f"{match.get('home', 'Unknown')} "
        f"🆚 "
        f"{match.get('away', 'Unknown')}"
    )
    print(f"Match ID: {match_id}")

    if match.get("status") != "Upcoming":
        print("Skipped: Match is not Upcoming.")
        return

    data = fetch_match_page(match_id)

    if not data:
        print("Skipped: Could not fetch match page.")
        return

    page = get_page_data(data)
    lineup = get_lineup_data(page)

    lineup_type = lineup.get("lineupType")

    home_team = lineup.get("homeTeam") or {}
    away_team = lineup.get("awayTeam") or {}

    home_starters = get_starters(home_team)
    away_starters = get_starters(away_team)

    official_lineups = (
        str(lineup_type).lower() == "confirmed"
        and len(home_starters) > 0
        and len(away_starters) > 0
    )

    print(f"FotMob lineupType: {lineup_type}")
    print(f"Home starters: {len(home_starters)}")
    print(f"Away starters: {len(away_starters)}")
    print(f"Official lineups: {official_lineups}")

    post = build_pre_match_post(
        match=match,
        page=page,
        lineup=lineup,
    )

    print()
    print("GENERATED TELEGRAM POST")
    print("-" * 80)
    print(post)
    print("-" * 80)


def main():
    print("Pre-match Post Generator Test")
    print("=" * 80)

    cache = load_cache()

    if not cache:
        print("No matches found in cache.")
        return

    print(f"Cached matches: {len(cache)}")

    for match_id, match in cache.items():
        process_match(match_id, match)

    print()
    print("=" * 80)
    print("Test completed. No Telegram message was sent.")


if __name__ == "__main__":
    main()

import asyncio
import json
import re
from datetime import datetime, timezone, timedelta

import requests

from telegram_sender import send_telegram_message


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
    "Milan": "میلان",
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
    "Paderborn": "پادربورن",
    "Rayo Vallecano": "رایو وایکانو",
    "Rayo Vallecano de Madrid": "رایو وایکانو",
    "Sabah FK": "صباح",
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
        print(
            "Cache file contains invalid JSON."
        )
        return {}


def save_cache(cache):
    try:
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

        print("Cache saved successfully.")
        return True

    except OSError as exc:
        print(
            f"Could not save cache: {exc}"
        )
        return False


def parse_utc_datetime(value):
    if not value:
        return None

    try:
        if (
            isinstance(value, str)
            and value.endswith("Z")
        ):
            value = (
                value[:-1]
                + "+00:00"
            )

        dt = datetime.fromisoformat(value)

        if dt.tzinfo is None:
            dt = dt.replace(
                tzinfo=timezone.utc
            )

        return dt.astimezone(
            timezone.utc
        )

    except (
        ValueError,
        TypeError,
    ):
        return None


def get_minutes_until_kickoff(utc_time):
    kickoff = parse_utc_datetime(
        utc_time
    )

    if kickoff is None:
        return None

    now = datetime.now(
        timezone.utc
    )

    remaining_seconds = (
        kickoff - now
    ).total_seconds()

    return remaining_seconds / 60


def format_remaining_time(minutes_until):
    if minutes_until is None:
        return "نامشخص"

    if minutes_until < 0:
        return (
            "شروع شده یا زمان آن گذشته است"
        )

    total_minutes = int(
        minutes_until
    )

    hours = total_minutes // 60
    minutes = total_minutes % 60

    if hours > 0:
        return (
            f"{hours} ساعت و "
            f"{minutes} دقیقه"
        )

    return f"{minutes} دقیقه"


def format_iran_time(utc_time):
    dt = parse_utc_datetime(
        utc_time
    )

    if dt is None:
        return "نامشخص"

    iran_time = dt + timedelta(
        hours=3,
        minutes=30,
    )

    return iran_time.strftime(
        "%H:%M"
    )


def fetch_match_page(match_id):
    url = (
        f"https://www.fotmob.com/"
        f"match/{match_id}"
    )

    try:
        response = requests.get(
            url,
            headers=HEADERS,
            timeout=20,
        )

        if response.status_code != 200:
            print(
                f"Could not fetch match "
                f"{match_id}. "
                f"HTTP status: "
                f"{response.status_code}"
            )
            return None

        match = re.search(
            r'<script id="__NEXT_DATA__" '
            r'type="application/json">'
            r'(.*?)'
            r'</script>',
            response.text,
            re.DOTALL,
        )

        if not match:
            print(
                f"__NEXT_DATA__ not found "
                f"for match {match_id}."
            )
            return None

        return json.loads(
            match.group(1)
        )

    except requests.RequestException as exc:
        print(
            f"Request error for match "
            f"{match_id}: {exc}"
        )
        return None

    except json.JSONDecodeError:
        print(
            f"Invalid JSON for match "
            f"{match_id}."
        )
        return None


def get_page_data(data):
    try:
        return data[
            "props"
        ][
            "pageProps"
        ]

    except (
        KeyError,
        TypeError,
    ):
        return {}


def get_lineup_data(page):
    content = (
        page.get("content")
        or {}
    )

    lineup = (
        content.get("lineup")
        or {}
    )

    return lineup


def get_coach_name(team_data):
    if not isinstance(
        team_data,
        dict,
    ):
        return "Unknown"

    coach = team_data.get(
        "coach"
    )

    if isinstance(
        coach,
        dict,
    ):
        for key in (
            "name",
            "shortName",
            "fullName",
        ):
            value = coach.get(
                key
            )

            if value:
                return str(
                    value
                )

    if (
        isinstance(
            coach,
            str,
        )
        and coach.strip()
    ):
        return coach.strip()

    return "Unknown"


def get_formation(team_data):
    if not isinstance(
        team_data,
        dict,
    ):
        return "Unknown"

    for key in (
        "formation",
        "expectedFormation",
    ):
        value = team_data.get(
            key
        )

        if value:
            return str(
                value
            )

    return "Unknown"


def get_starters(team_data):
    if not isinstance(
        team_data,
        dict,
    ):
        return []

    starters = team_data.get(
        "starters"
    )

    if isinstance(
        starters,
        list,
    ):
        return starters

    return []


def get_player_name(player):
    if not isinstance(
        player,
        dict,
    ):
        return "Unknown"

    for key in (
        "name",
        "playerName",
        "shortName",
        "fullName",
    ):
        value = player.get(
            key
        )

        if value:
            return str(
                value
            )

    nested_player = player.get(
        "player"
    )

    if isinstance(
        nested_player,
        dict,
    ):
        for key in (
            "name",
            "shortName",
            "fullName",
        ):
            value = nested_player.get(
                key
            )

            if value:
                return str(
                    value
                )

    return "Unknown"


def get_player_number(player):
    if not isinstance(
        player,
        dict,
    ):
        return ""

    for key in (
        "shirtNumber",
        "number",
        "jerseyNumber",
    ):
        value = player.get(
            key
        )

        if value is not None:
            return str(
                value
            )

    return ""


def format_player(player):
    name = get_player_name(
        player
    )

    number = get_player_number(
        player
    )

    if number:
        return (
            f"{number}. {name}"
        )

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


def has_official_lineups(lineup):
    if not isinstance(
        lineup,
        dict,
    ):
        return False

    lineup_type = str(
        lineup.get(
            "lineupType"
        )
        or ""
    ).lower()

    if lineup_type != "confirmed":
        return False

    home_team = (
        lineup.get("homeTeam")
        or {}
    )

    away_team = (
        lineup.get("awayTeam")
        or {}
    )

    home_starters = get_starters(
        home_team
    )

    away_starters = get_starters(
        away_team
    )

    return (
        len(home_starters) > 0
        and len(away_starters) > 0
    )


def is_match_eligible(
    match,
    lineup,
    minutes_until,
):
    if match.get(
        "pre_match_sent",
        False,
    ):
        return (
            False,
            "Pre-match message "
            "was already sent.",
        )

    status = str(
        match.get("status")
        or ""
    ).strip()

    if status != "Upcoming":
        return (
            False,
            f"Match status is "
            f"{status}.",
        )

    if has_official_lineups(
        lineup
    ):
        return (
            True,
            "Both official lineups "
            "are confirmed.",
        )

    if minutes_until is None:
        return (
            False,
            "Kickoff time is "
            "unavailable.",
        )

    if (
        0
        <= minutes_until
        <= 60
    ):
        return (
            True,
            "One hour or less "
            "remains until kickoff.",
        )

    if minutes_until < 0:
        return (
            False,
            "Kickoff time has "
            "already passed.",
        )

    return (
        False,
        "Official lineups are "
        "unavailable and more "
        "than one hour remains.",
    )


def build_team_section(
    team_name,
    team_data,
):
    lines = []

    lines.append(
        team_name
    )

    coach = get_coach_name(
        team_data
    )

    formation = get_formation(
        team_data
    )

    starters = get_starters(
        team_data
    )

    lines.append(
        f"Coach: {coach}"
    )

    lines.append(
        f"Formation: {formation}"
    )

    if starters:
        lines.append("")
        lines.append(
            "Starting XI:"
        )

        for player in starters:
            lines.append(
                format_player(
                    player
                )
            )

    return "\n".join(
        lines
    )


def build_pre_match_post(
    match,
    lineup,
):
    home = match.get(
        "home",
        "Unknown",
    )

    away = match.get(
        "away",
        "Unknown",
    )

    league = match.get(
        "league",
        "Unknown",
    )

    utc_time = match.get(
        "utc_time"
    )

    home_team_data = (
        lineup.get("homeTeam")
        or {}
    )

    away_team_data = (
        lineup.get("awayTeam")
        or {}
    )

    official_lineups = (
        has_official_lineups(
            lineup
        )
    )

    persian_league = (
        translate_league(
            league
        )
    )

    persian_home = (
        translate_team(
            home
        )
    )

    persian_away = (
        translate_team(
            away
        )
    )

    iran_time = (
        format_iran_time(
            utc_time
        )
    )

    lines = []

    lines.append(
        f"🏆 {persian_league}"
    )

    lines.append("")

    lines.append(
        f"{persian_home} 🆚 "
        f"{persian_away}"
    )

    lines.append("")

    lines.append(
        f"⏰ {iran_time} "
        f"به وقت ایران"
    )

    lines.append("")

    lines.append(
        "━━━━━━━━━━━━━━━━━━━━━━"
    )

    lines.append("")

    if official_lineups:
        lines.append(
            build_team_section(
                home,
                home_team_data,
            )
        )

        lines.append("")

        lines.append(
            "━━━━━━━━━━━━━━━━━━━━━━"
        )

        lines.append("")

        lines.append(
            build_team_section(
                away,
                away_team_data,
            )
        )

    else:
        lines.append(
            "ترکیب رسمی هنوز "
            "اعلام نشده است."
        )

    return "\n".join(
        lines
    )


async def process_match(
    match_id,
    match,
):
    home = match.get(
        "home",
        "Unknown",
    )

    away = match.get(
        "away",
        "Unknown",
    )

    print()
    print(
        "=" * 90
    )

    print(
        f"{home} 🆚 {away}"
    )

    print(
        f"Match ID: {match_id}"
    )

    status = match.get(
        "status",
        "",
    )

    pre_match_sent = match.get(
        "pre_match_sent",
        False,
    )

    utc_time = match.get(
        "utc_time"
    )

    minutes_until = (
        get_minutes_until_kickoff(
            utc_time
        )
    )

    print(
        f"Status: {status}"
    )

    print(
        "Pre-match already sent: "
        f"{pre_match_sent}"
    )

    print(
        f"UTC kickoff: {utc_time}"
    )

    if minutes_until is None:
        print(
            "Minutes until kickoff: "
            "Unknown"
        )

    else:
        print(
            "Minutes until kickoff: "
            f"{minutes_until:.1f}"
        )

        print(
            "Remaining time: "
            f"{format_remaining_time(minutes_until)}"
        )

    if pre_match_sent:
        print(
            "Decision: ALREADY SENT"
        )

        print(
            "Reason: Pre-match "
            "message was already sent."
        )

        return False

    if status != "Upcoming":
        print(
            "Decision: WAIT"
        )

        print(
            f"Reason: Match status "
            f"is {status}."
        )

        return False

    data = fetch_match_page(
        match_id
    )

    if not data:
        print(
            "Decision: WAIT"
        )

        print(
            "Reason: Could not fetch "
            "FotMob match page."
        )

        return False

    page = get_page_data(
        data
    )

    lineup = get_lineup_data(
        page
    )

    lineup_type = lineup.get(
        "lineupType"
    )

    home_team = (
        lineup.get("homeTeam")
        or {}
    )

    away_team = (
        lineup.get("awayTeam")
        or {}
    )

    home_starters = get_starters(
        home_team
    )

    away_starters = get_starters(
        away_team
    )

    official_lineups = (
        has_official_lineups(
            lineup
        )
    )

    print(
        f"FotMob lineupType: "
        f"{lineup_type}"
    )

    print(
        f"Home starters: "
        f"{len(home_starters)}"
    )

    print(
        f"Away starters: "
        f"{len(away_starters)}"
    )

    print(
        f"Official lineups: "
        f"{official_lineups}"
    )

    eligible, reason = (
        is_match_eligible(
            match=match,
            lineup=lineup,
            minutes_until=minutes_until,
        )
    )

    print(
        f"Decision reason: "
        f"{reason}"
    )

    if not eligible:
        print(
            "Decision: WAIT"
        )

        print(
            "No Telegram post "
            "generated."
        )

        return False

    print(
        "Decision: SEND"
    )

    print(
        "This match is eligible "
        "for a pre-match post."
    )

    post = build_pre_match_post(
        match=match,
        lineup=lineup,
    )

    print()
    print(
        "GENERATED TELEGRAM POST"
    )

    print(
        "-" * 90
    )

    print(post)

    print(
        "-" * 90
    )

    print()
    print(
        "Sending message to Telegram..."
    )

    sent = await send_telegram_message(
        post
    )

    if not sent:
        print(
            "Telegram send failed."
        )

        print(
            "pre_match_sent will "
            "remain False."
        )

        return False

    match[
        "pre_match_sent"
    ] = True

    match[
        "last_pre_match_sent_at"
    ] = datetime.now(
        timezone.utc
    ).isoformat()

    print(
        "pre_match_sent set to True."
    )

    return True


async def main():
    print(
        "Pre-match Post Generator"
    )

    print(
        "=" * 90
    )

    cache = load_cache()

    if not cache:
        print(
            "No matches found "
            "in cache."
        )
        return

    print(
        f"Cached matches: "
        f"{len(cache)}"
    )

    cache_changed = False

    for match_id, match in cache.items():
        sent = await process_match(
            match_id,
            match,
        )

        if sent:
            cache_changed = True

    if cache_changed:
        print()
        print(
            "Saving updated cache..."
        )

        save_cache(cache)

    else:
        print()
        print(
            "No cache changes "
            "were necessary."
        )

    print()
    print(
        "=" * 90
    )

    print(
        "Pre-match processing "
        "completed."
    )


if __name__ == "__main__":
    asyncio.run(
        main()
    )

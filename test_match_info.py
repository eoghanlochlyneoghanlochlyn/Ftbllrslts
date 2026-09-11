import os
import re
import json
import asyncio
import requests

from datetime import datetime, timezone
from zoneinfo import ZoneInfo
from telegram import Bot


MATCH_ID = "6106293"

URL = f"https://www.fotmob.com/match/{MATCH_ID}"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/140.0.0.0 Safari/537.36"
    )
}


TEAM_NAMES_FA = {
    "Manchester United": "منچستریونایتد",
    "Sabah FK": "صباح",
    "Sabah": "صباح",
}


COMPETITION_NAMES_FA = {
    "Champions League": "لیگ قهرمانان اروپا",
    "Europa League": "لیگ اروپا",
    "Premier League": "لیگ برتر انگلیس",
    "LaLiga": "لالیگا",
    "Serie A": "سری آ",
    "Bundesliga": "بوندسلیگا",
    "Ligue 1": "لیگ یک فرانسه",
}


def get_next_data(html):
    match = re.search(
        r'<script id="__NEXT_DATA__" type="application/json">(.*?)</script>',
        html,
        re.DOTALL,
    )

    if not match:
        return None

    return json.loads(match.group(1))


def translate_team_name(name):
    return TEAM_NAMES_FA.get(name, name)


def translate_competition_name(name):
    return COMPETITION_NAMES_FA.get(name, name)


def get_match_time_iran(general):
    candidates = [
        general.get("matchTime"),
        general.get("matchTimeUTC"),
        general.get("utcTime"),
        general.get("matchDate"),
    ]

    for value in candidates:
        if not value:
            continue

        try:
            dt = datetime.fromisoformat(
                str(value).replace("Z", "+00:00")
            )

            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)

            return dt.astimezone(
                ZoneInfo("Asia/Tehran")
            ).strftime("%Y-%m-%d %H:%M")

        except Exception:
            pass

    match_name = general.get("matchName", "")

    match = re.search(
        r"([A-Z][a-z]{2}, [A-Z][a-z]{2} \d{1,2}, \d{4}, \d{2}:\d{2} UTC)",
        match_name,
    )

    if match:
        try:
            dt = datetime.strptime(
                match.group(1),
                "%a, %b %d, %Y, %H:%M UTC",
            ).replace(tzinfo=timezone.utc)

            return dt.astimezone(
                ZoneInfo("Asia/Tehran")
            ).strftime("%Y-%m-%d %H:%M")

        except Exception:
            pass

    return "Unknown"


def get_coach_name(team):
    coach = team.get("coach")

    if not coach:
        return "Unknown"

    if isinstance(coach, str):
        return coach

    if isinstance(coach, dict):
        for key in [
            "name",
            "fullName",
            "shortName",
            "displayName",
        ]:
            if coach.get(key):
                return coach[key]

        first_name = coach.get("firstName", "")
        last_name = coach.get("lastName", "")

        full_name = f"{first_name} {last_name}".strip()

        if full_name:
            return full_name

    return "Unknown"


def get_player_rating(player):
    performance = player.get("performance")

    if isinstance(performance, dict):
        rating = performance.get("rating")

        if rating is not None:
            return rating

    return "-"


def sort_players(players):
    return sorted(
        players,
        key=lambda player: (
            player.get("horizontalLayout", {}).get("x", 0),
            player.get("horizontalLayout", {}).get("y", 0),
        ),
    )


def get_short_player_name(player):
    name = player.get("name", "-")

    parts = name.split()

    if len(parts) <= 1:
        return name

    return parts[-1]


def build_compact_lineup(team, show_ratings=False):
    starters = sort_players(team.get("starters", []))

    if not starters:
        return "Lineup unavailable"

    lines = []

    current_x = None
    current_line = []

    for player in starters:
        layout = player.get("horizontalLayout", {})
        x = layout.get("x", 0)

        if current_x is None:
            current_x = x

        if abs(x - current_x) > 0.12:
            if current_line:
                lines.append(" · ".join(current_line))

            current_line = []
            current_x = x

        player_name = get_short_player_name(player)

        if show_ratings:
            rating = get_player_rating(player)
            player_name = f"{player_name} {rating}"

        current_line.append(player_name)

    if current_line:
        lines.append(" · ".join(current_line))

    return "\n".join(lines)


def build_team_block(team, show_ratings=False):
    team_name = team.get("name", "-")
    coach_name = get_coach_name(team)
    formation = team.get("formation", "-")

    lines = []

    lines.append(
        f"🔴 {team_name}"
    )

    lines.append(
        f"Coach: {coach_name}"
    )

    lines.append(
        f"Formation: {formation}"
    )

    if show_ratings:
        team_rating = team.get("rating")

        if team_rating is not None:
            lines.append(
                f"Team rating: {team_rating}"
            )

    lines.append("")
    lines.append(
        build_compact_lineup(
            team,
            show_ratings=show_ratings,
        )
    )

    return "\n".join(lines)


def get_score(general, header):
    home_score = None
    away_score = None

    possible_sources = [
        header,
        general,
    ]

    for source in possible_sources:
        if not isinstance(source, dict):
            continue

        if home_score is None:
            home_score = source.get("homeScore")

        if away_score is None:
            away_score = source.get("awayScore")

        if home_score is None:
            home_score = source.get("homeTeamScore")

        if away_score is None:
            away_score = source.get("awayTeamScore")

    return home_score, away_score


def build_message(general, header, lineup):
    home_team = lineup.get("homeTeam", {})
    away_team = lineup.get("awayTeam", {})

    league_name = general.get("leagueName", "Unknown")
    league_name_fa = translate_competition_name(league_name)

    home_name = home_team.get("name", "Home")
    away_name = away_team.get("name", "Away")

    home_name_fa = translate_team_name(home_name)
    away_name_fa = translate_team_name(away_name)

    match_time = get_match_time_iran(general)

    finished = bool(general.get("finished", False))
    started = bool(general.get("started", False))

    lines = []

    if finished:
        home_score, away_score = get_score(
            general,
            header,
        )

        lines.append(f"🏆 {league_name_fa}")
        lines.append("")
        lines.append(
            f"{home_name_fa} {home_score if home_score is not None else '-'} "
            f"🆚 "
            f"{away_score if away_score is not None else '-'} {away_name_fa}"
        )
        lines.append("")
        lines.append(
            f"⏰ {match_time}"
        )
        lines.append("")
        lines.append("━━━━━━━━━━━━━━━━━━━━━━")
        lines.append("")

        lines.append(
            build_team_block(
                home_team,
                show_ratings=True,
            )
        )

        lines.append("")
        lines.append("━━━━━━━━━━━━━━━━━━━━━━")
        lines.append("")

        lines.append(
            build_team_block(
                away_team,
                show_ratings=True,
            )
        )

    else:
        lines.append(f"🏆 {league_name_fa}")
        lines.append("")
        lines.append(
            f"{home_name_fa} 🆚 {away_name_fa}"
        )
        lines.append("")
        lines.append(
            f"⏰ {match_time}"
        )
        lines.append("")
        lines.append("━━━━━━━━━━━━━━━━━━━━━━")
        lines.append("")

        lines.append(
            build_team_block(
                home_team,
                show_ratings=False,
            )
        )

        lines.append("")
        lines.append("━━━━━━━━━━━━━━━━━━━━━━")
        lines.append("")

        lines.append(
            build_team_block(
                away_team,
                show_ratings=False,
            )
        )

    return "\n".join(lines)


async def send_to_telegram(message):
    bot = Bot(os.environ["TELEGRAMBOT"])

    await bot.send_message(
        chat_id=os.environ["TELEGRAMCHANNEL"],
        text=message,
    )


def main():
    print("Downloading FotMob page...")

    response = requests.get(
        URL,
        headers=HEADERS,
        timeout=30,
    )

    if response.status_code != 200:
        raise Exception(
            f"FotMob request failed: {response.status_code}"
        )

    data = get_next_data(response.text)

    if not data:
        raise Exception("NEXT_DATA not found")

    page = data["props"]["pageProps"]

    general = page["general"]
    header = page.get("header", {})
    lineup = page["content"]["lineup"]

    message = build_message(
        general,
        header,
        lineup,
    )

    print("")
    print(message)
    print("")

    asyncio.run(
        send_to_telegram(message)
    )

    print("Telegram message sent successfully.")


if __name__ == "__main__":
    main()

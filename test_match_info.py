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


def get_next_data(html):
    match = re.search(
        r'<script id="__NEXT_DATA__" type="application/json">(.*?)</script>',
        html,
        re.DOTALL,
    )

    if not match:
        return None

    return json.loads(match.group(1))


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


def player_rating(player):
    performance = player.get("performance")

    if isinstance(performance, dict):
        return performance.get("rating", "-")

    return "-"


def sort_players(players):
    return sorted(
        players,
        key=lambda player: (
            player.get("horizontalLayout", {}).get("x", 0),
            player.get("horizontalLayout", {}).get("y", 0),
        ),
    )


def build_pitch_lineup(team):
    starters = sort_players(team.get("starters", []))

    if not starters:
        return "اطلاعات ترکیب موجود نیست"

    lines = []

    lines.append("📋 ترکیب روی زمین")

    for player in starters:
        layout = player.get("horizontalLayout", {})
        x = layout.get("x", 0)
        y = layout.get("y", 0)

        lines.append(
            f"{player.get('name', '-')}"
            f" | #{player.get('shirtNumber', '-')}"
            f" | موقعیت: {x:.2f}/{y:.2f}"
        )

    return "\n".join(lines)


def build_team(team):
    lines = []

    lines.append(f"🏟 Team: {team.get('name', '-')}")
    lines.append(f"📐 Formation: {team.get('formation', '-')}")
    lines.append(f"⭐ Team Rating: {team.get('rating')}")
    lines.append(f"👥 Average Age: {team.get('averageStarterAge')}")
    lines.append("")

    lines.append("🟢 Starting XI")

    starters = sort_players(team.get("starters", []))

    for player in starters:
        lines.append(
            f"#{str(player.get('shirtNumber', '-')):>2}  "
            f"{player.get('name', '-')}"
            f" ({player_rating(player)})"
        )

    lines.append("")
    lines.append("🪑 Bench")

    substitutes = team.get("subs", [])

    if substitutes:
        for player in substitutes:
            lines.append(
                f"#{player.get('shirtNumber', '-')}"
                f" {player.get('name', '-')}"
            )
    else:
        lines.append("اطلاعات نیمکت در دادهٔ فوت‌موب موجود نیست")

    unavailable = team.get("unavailable", [])

    if unavailable:
        lines.append("")
        lines.append("❌ Unavailable")

        for player in unavailable:
            reason = ""

            unavailability = player.get("unavailability")

            if isinstance(unavailability, dict):
                reason = unavailability.get("label", "")

            player_name = player.get("name", "-")

            if reason:
                lines.append(f"{player_name} — {reason}")
            else:
                lines.append(player_name)

    lines.append("")
    lines.append(build_pitch_lineup(team))

    return "\n".join(lines)


def build_message(general, lineup):
    home_team = lineup.get("homeTeam", {})
    away_team = lineup.get("awayTeam", {})

    message = []

    message.append("🏆 MATCH INFORMATION")
    message.append("")

    message.append(
        f"League : {general.get('leagueName', '-')}"
    )

    message.append(
        f"Match  : {general.get('matchName', '-')}"
    )

    message.append(
        f"Time 🇮🇷 : {get_match_time_iran(general)}"
    )

    message.append(
        f"Started : {general.get('started', False)}"
    )

    message.append(
        f"Finished : {general.get('finished', False)}"
    )

    message.append("")
    message.append("━━━━━━━━━━━━━━━━━━━━━━")
    message.append("")

    message.append(build_team(home_team))

    message.append("")
    message.append("━━━━━━━━━━━━━━━━━━━━━━")
    message.append("")

    message.append(build_team(away_team))

    return "\n".join(message)


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
    content = page["content"]
    lineup = content["lineup"]

    message = build_message(
        general,
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

import os
import re
import json
import asyncio
import requests

from datetime import datetime
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


def iran_time(utc_time):
    if not utc_time:
        return "Unknown"

    try:
        dt = datetime.fromisoformat(
            utc_time.replace("Z", "+00:00")
        )

        return dt.astimezone(
            ZoneInfo("Asia/Tehran")
        ).strftime("%Y-%m-%d %H:%M")

    except:
        return utc_time


def player_rating(player):

    perf = player.get("performance")

    if isinstance(perf, dict):
        return perf.get("rating")

    return "-"


def build_team(team):

    lines = []

    lines.append(f"🏟 Team: {team['name']}")
    lines.append(f"📐 Formation: {team['formation']}")
    lines.append(f"⭐ Team Rating: {team.get('rating')}")
    lines.append(f"👥 Average Age: {team.get('averageStarterAge')}")
    lines.append("")

    lines.append("🟢 Starting XI")

    starters = sorted(
        team["starters"],
        key=lambda p: (
            p["horizontalLayout"]["x"],
            p["horizontalLayout"]["y"],
        ),
    )

    for p in starters:

        lines.append(
            f"#{p['shirtNumber']:>2}  "
            f"{p['name']} "
            f"({player_rating(p)})"
        )

    lines.append("")
    lines.append("🪑 Bench")

    for p in team.get("subs", []):

        lines.append(
            f"#{p.get('shirtNumber','-')} "
            f"{p['name']}"
        )

    unavailable = team.get("unavailable", [])

    if unavailable:

        lines.append("")
        lines.append("❌ Unavailable")

        for p in unavailable:

            reason = ""

            if isinstance(p.get("unavailability"), dict):
                reason = p["unavailability"].get("label", "")

            lines.append(
                f"{p['name']} {reason}"
            )

    return "\n".join(lines)


def build_message(general, lineup):

    home = lineup["homeTeam"]
    away = lineup["awayTeam"]

    message = []

    message.append("🏆 MATCH INFORMATION")
    message.append("")

    message.append(f"League : {general.get('leagueName')}")
    message.append(f"Match  : {general.get('matchName')}")
    message.append(f"Time 🇮🇷 : {iran_time(general.get('matchTime'))}")

    message.append(
        f"Started : {general.get('started')}"
    )

    message.append(
        f"Finished : {general.get('finished')}"
    )

    message.append("")
    message.append("━━━━━━━━━━━━━━━━━━━━━━")
    message.append("")
    message.append(build_team(home))
    message.append("")
    message.append("━━━━━━━━━━━━━━━━━━━━━━")
    message.append("")
    message.append(build_team(away))

    return "\n".join(message)


async def send(message):

    bot = Bot(os.environ["TELEGRAMBOT"])

    await bot.send_message(
        chat_id=os.environ["TELEGRAMCHANNEL"],
        text=message,
    )


def main():

    print("Downloading...")

    response = requests.get(
        URL,
        headers=HEADERS,
        timeout=30,
    )

    if response.status_code != 200:
        raise Exception("FotMob request failed")

    data = get_next_data(response.text)

    if not data:
        raise Exception("NEXT_DATA not found")

    page = data["props"]["pageProps"]

    general = page["general"]

    lineup = page["content"]["lineup"]

    message = build_message(
        general,
        lineup,
    )

    print(message)

    asyncio.run(
        send(message)
    )

    print("\nTelegram message sent successfully.")


if __name__ == "__main__":
    main()

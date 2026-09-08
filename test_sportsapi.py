import os
import json
import requests


API_KEY = os.getenv("BIGBALLS_API_KEY")

MATCH_ID = "f11c25d9-7e10-4cd0-b8fa-9b39827768ce"

BASE_URL = "https://api.bigballsdata.com/v1"

HEADERS = {
    "Authorization": f"Bearer {API_KEY}"
}


def get_json(url, params=None):
    response = requests.get(
        url,
        headers=HEADERS,
        params=params,
        timeout=30
    )

    print(f"HTTP {response.status_code} | {url}")

    response.raise_for_status()

    return response.json()


def value(stats, key):
    item = stats.get(key)

    if isinstance(item, dict):
        return item.get("value", "-")

    return item if item is not None else "-"


# ---------------------------------------------------------
# اطلاعات اصلی مسابقه
# ---------------------------------------------------------

match = get_json(
    f"{BASE_URL}/stored/matches/{MATCH_ID}"
)

match_data = match.get("data", match)

home = match_data.get("home", {})
away = match_data.get("away", {})

score = match_data.get("score") or {}

print("\n" + "=" * 50)
print("🏟 اطلاعات مسابقه")
print("=" * 50)

print(
    f"{home.get('name', '?')} "
    f"{score.get('home', '?')} - {score.get('away', '?')} "
    f"{away.get('name', '?')}"
)

print(f"لیگ: {match_data.get('league', '-')}")
print(f"زمان: {match_data.get('kickoff_utc', '-')}")
print(f"وضعیت: {match_data.get('status', '-')}")
print(f"شناسه: {MATCH_ID}")


# ---------------------------------------------------------
# رویدادها
# ---------------------------------------------------------

events = get_json(
    f"{BASE_URL}/matches/{MATCH_ID}/events",
    params={"sport": "football"}
)

event_list = events.get("data", [])

print("\n" + "=" * 50)
print(f"⚽ رویدادها ({len(event_list)})")
print("=" * 50)

for event in event_list:

    event_type = event.get("event_type", event.get("type", "-"))

    player = event.get("player_name")

    if not player:
        player_data = event.get("player", {})
        if isinstance(player_data, dict):
            player = player_data.get("name")

    team = event.get("team_name")

    if not team:
        team_data = event.get("team", {})
        if isinstance(team_data, dict):
            team = team_data.get("name")

    minute = event.get("minute", event.get("time", "-"))

    assist = event.get("assist_player_name")

    if not assist:
        assist_data = event.get("assist_player", {})
        if isinstance(assist_data, dict):
            assist = assist_data.get("name")

    print(
        f"{event_type} | "
        f"{minute}' | "
        f"{player or '-'} | "
        f"{team or '-'}"
        + (f" | پاس گل: {assist}" if assist else "")
    )


# ---------------------------------------------------------
# ترکیب
# ---------------------------------------------------------

lineups = get_json(
    f"{BASE_URL}/stored/matches/{MATCH_ID}/lineups"
)

lineup_data = lineups.get("data", {})

print("\n" + "=" * 50)
print("👥 ترکیب")
print("=" * 50)


for side, team_name in [
    ("home", home.get("name", "میزبان")),
    ("away", away.get("name", "مهمان"))
]:

    team_lineup = lineup_data.get(side, {})

    if not isinstance(team_lineup, dict):
        continue

    starters = team_lineup.get("starters", [])
    bench = team_lineup.get("bench", [])

    print(f"\n{team_name}")

    print(
        "فیکس: "
        + ", ".join(
            player.get("name", "?")
            for player in starters
            if isinstance(player, dict)
        )
    )

    print(
        "ذخیره: "
        + ", ".join(
            player.get("name", "?")
            for player in bench
            if isinstance(player, dict)
        )
    )


# ---------------------------------------------------------
# آمار تیمی و بازیکنان
# ---------------------------------------------------------

stats_response = get_json(
    f"{BASE_URL}/stored/matches/{MATCH_ID}/stats"
)

stats_data = stats_response.get("data", {})

team_stats = stats_data.get("team_stats", {})
players = stats_data.get("players", [])


# ---------------------------------------------------------
# آمار تیمی
# ---------------------------------------------------------

print("\n" + "=" * 50)
print("📊 آمار تیمی")
print("=" * 50)


for team_key, team_name in [
    ("home", home.get("name", "میزبان")),
    ("away", away.get("name", "مهمان"))
]:

    stats = team_stats.get(team_key, {})

    if not isinstance(stats, dict):
        continue

    print(f"\n{team_name}")

    important_stats = [
        ("Possession", "مالکیت"),
        ("SHOTS", "شوت"),
        ("ON GOAL", "شوت در چارچوب"),
        ("Passes", "پاس"),
        ("Pass Completion %", "دقت پاس"),
        ("Corner Kicks", "کرنر"),
        ("Fouls", "خطا"),
        ("Yellow Cards", "کارت زرد"),
        ("Red Cards", "کارت قرمز"),
        ("Offsides", "آفساید"),
        ("Tackles", "تکل"),
        ("Interceptions", "قطع توپ"),
    ]

    for key, label in important_stats:

        if key in stats:
            print(f"{label}: {stats[key]}")


# ---------------------------------------------------------
# آمار بازیکنان
# ---------------------------------------------------------

print("\n" + "=" * 50)
print(f"👤 آمار بازیکنان ({len(players)})")
print("=" * 50)


for player in players:

    if not isinstance(player, dict):
        continue

    name = player.get("name", "?")
    team = player.get("team_name", "?")
    position = player.get("position", "-")

    player_stats = player.get("stats", {})

    print(
        f"\n{name} | {team} | {position}"
    )

    important_player_stats = [
        ("minutes", "دقیقه"),
        ("rating", "امتیاز"),
        ("goals", "گل"),
        ("assists", "پاس گل"),
        ("shots_total", "شوت"),
        ("shots_on", "در چارچوب"),
        ("passes_total", "پاس"),
        ("passes_key", "پاس کلیدی"),
        ("pass_accuracy", "دقت پاس"),
        ("dribbles_success", "دریبل موفق"),
        ("duels_won", "دوئل موفق"),
        ("tackles_total", "تکل"),
        ("interceptions", "قطع توپ"),
        ("fouls_committed", "خطا"),
        ("yellow_cards", "کارت زرد"),
        ("red_cards", "کارت قرمز"),
    ]

    values = []

    for key, label in important_player_stats:

        if key in player_stats:
            values.append(
                f"{label}: {value(player_stats, key)}"
            )

    print(" | ".join(values))


print("\n" + "=" * 50)
print("✅ پایان گزارش")
print("=" * 50)

import os
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


def get_stat_value(stats, key):
    item = stats.get(key)

    if isinstance(item, dict):
        return item.get("value", "-")

    if item is None:
        return "-"

    return item


# =========================================================
# اطلاعات اصلی مسابقه
# =========================================================

match_response = get_json(
    f"{BASE_URL}/stored/matches/{MATCH_ID}"
)

match = match_response.get("data", match_response)

home = match.get("home", {})
away = match.get("away", {})

score = match.get("score") or {}

home_name = home.get("name", "میزبان")
away_name = away.get("name", "مهمان")

print("\n" + "=" * 50)
print("🏟 اطلاعات مسابقه")
print("=" * 50)

print(
    f"{home_name} "
    f"{score.get('home', '?')} - {score.get('away', '?')} "
    f"{away_name}"
)

print(f"لیگ: {match.get('league', '-')}")
print(f"زمان: {match.get('kickoff_utc', '-')}")
print(f"وضعیت: {match.get('status', '-')}")
print(f"شناسه: {MATCH_ID}")


# =========================================================
# رویدادها
# =========================================================

events_response = get_json(
    f"{BASE_URL}/matches/{MATCH_ID}/events",
    params={"sport": "football"}
)

events = events_response.get("data", [])

print("\n" + "=" * 50)
print(f"⚽ رویدادها ({len(events)})")
print("=" * 50)

for event in events:

    event_type = (
        event.get("event_type")
        or event.get("type")
        or event.get("event")
        or "-"
    )

    player = event.get("player_name")

    if not player:
        player_data = event.get("player")

        if isinstance(player_data, dict):
            player = player_data.get("name")

    team = event.get("team_name")

    if not team:
        team_data = event.get("team")

        if isinstance(team_data, dict):
            team = team_data.get("name")

    minute = (
        event.get("minute")
        or event.get("minute_display")
        or event.get("time")
        or event.get("elapsed")
        or "-"
    )

    assist = event.get("assist_player_name")

    if not assist:
        assist_data = event.get("assist_player")

        if isinstance(assist_data, dict):
            assist = assist_data.get("name")

    line = (
        f"{event_type} | "
        f"{minute}' | "
        f"{player or '-'} | "
        f"{team or '-'}"
    )

    if assist:
        line += f" | پاس گل: {assist}"

    print(line)


# =========================================================
# ترکیب
# =========================================================

lineups_response = get_json(
    f"{BASE_URL}/stored/matches/{MATCH_ID}/lineups"
)

lineups = lineups_response.get("data", {})

print("\n" + "=" * 50)
print("👥 ترکیب")
print("=" * 50)


for side, team_name in [
    ("home", home_name),
    ("away", away_name)
]:

    team_lineup = lineups.get(side)

    if not isinstance(team_lineup, dict):
        print(f"\n{team_name}: اطلاعات ترکیب موجود نیست")
        continue

    starters = team_lineup.get("starters", [])
    bench = team_lineup.get("bench", [])

    print(f"\n{team_name}")

    starter_names = []

    for player in starters:
        if isinstance(player, dict):
            name = player.get("name", "?")
            starter_names.append(name)

    bench_names = []

    for player in bench:
        if isinstance(player, dict):
            name = player.get("name", "?")
            bench_names.append(name)

    print(
        "فیکس: "
        + (", ".join(starter_names) if starter_names else "-")
    )

    print(
        "ذخیره: "
        + (", ".join(bench_names) if bench_names else "-")
    )


# =========================================================
# آمار
# =========================================================

stats_response = get_json(
    f"{BASE_URL}/stored/matches/{MATCH_ID}/stats"
)

stats_data = stats_response.get("data", {})

team_stats = stats_data.get("team_stats", [])
players = stats_data.get("players", [])

print("\n" + "=" * 50)
print("📊 آمار تیمی")
print("=" * 50)


# ---------------------------------------------------------
# team_stats واقعی به صورت LIST است
# ---------------------------------------------------------

if isinstance(team_stats, list):

    for team in team_stats:

        if not isinstance(team, dict):
            continue

        team_id = team.get("team_id")
        team_name = team.get("team_name")

        if not team_name:

            if team_id == home.get("id"):
                team_name = home_name

            elif team_id == away.get("id"):
                team_name = away_name

        team_name = team_name or "تیم"

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
            ("Clearances", "دفع توپ"),
        ]

        for key, label in important_stats:

            if key in team:
                print(
                    f"{label}: {get_stat_value(team, key)}"
                )


elif isinstance(team_stats, dict):

    for team_key, team_name in [
        ("home", home_name),
        ("away", away_name)
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
            ("Clearances", "دفع توپ"),
        ]

        for key, label in important_stats:

            if key in stats:
                print(
                    f"{label}: {get_stat_value(stats, key)}"
                )


else:

    print("ساختار آمار تیمی ناشناخته است.")


# =========================================================
# آمار بازیکنان
# =========================================================

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
                f"{label}: {get_stat_value(player_stats, key)}"
            )

    if values:
        print(" | ".join(values))


# =========================================================
# پایان
# =========================================================

print("\n" + "=" * 50)
print("✅ گزارش کامل شد")
print("=" * 50)

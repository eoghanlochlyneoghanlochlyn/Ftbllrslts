import os
import requests


API_KEY = os.getenv("BIGBALLS_API_KEY")

MATCH_ID = "f11c25d9-7e10-4cd0-b8fa-9b39827768ce"

BASE_URL = "https://api.bigballsdata.com/v1"

HEADERS = {
    "Authorization": f"Bearer {API_KEY}"
}


# ============================================================
# ابزارهای عمومی
# ============================================================

def get_json(url, params=None):
    response = requests.get(
        url,
        headers=HEADERS,
        params=params,
        timeout=30
    )

    print(f"HTTP {response.status_code} | {response.url}")

    response.raise_for_status()

    return response.json()


def show(value):
    if value is None or value == "":
        return "-"

    return str(value)


def print_separator(title):
    print()
    print("=" * 70)
    print(title)
    print("=" * 70)


# ============================================================
# بررسی کلید API
# ============================================================

if not API_KEY:
    print("❌ BIGBALLS_API_KEY پیدا نشد.")

    raise SystemExit(1)


# ============================================================
# 1. اطلاعات مسابقه
# ============================================================

match_response = get_json(
    f"{BASE_URL}/stored/matches/{MATCH_ID}"
)

match = match_response.get("data", {})

home = match.get("home", {})
away = match.get("away", {})

home_name = home.get("name", "میزبان")
away_name = away.get("name", "مهمان")

score = match.get("score") or {}

home_score = score.get("home", "-")
away_score = score.get("away", "-")

print_separator("🏟 اطلاعات مسابقه")

print(
    f"{home_name} {home_score} - {away_score} {away_name}"
)

print(f"لیگ: {show(match.get('league'))}")
print(f"زمان: {show(match.get('kickoff_utc'))}")
print(f"وضعیت: {show(match.get('status'))}")
print(f"دور: {show(match.get('round'))}")
print(f"شناسه: {show(match.get('id'))}")


# ============================================================
# 2. رویدادهای مسابقه
# ============================================================

events_response = get_json(
    f"{BASE_URL}/matches/{MATCH_ID}/events",
    params={
        "sport": "football"
    }
)

events = events_response.get("data", [])

print_separator(
    f"⚽ رویدادهای مسابقه ({len(events)})"
)

if not events:
    print("رویدادی ثبت نشده است.")

else:
    for event in events:

        elapsed = event.get("elapsed")

        elapsed_extra = event.get("elapsed_extra")

        if elapsed is None:
            minute = "-"

        elif elapsed_extra is not None:
            minute = f"{elapsed}+{elapsed_extra}"

        else:
            minute = str(elapsed)

        event_type = show(
            event.get("event_type")
        )

        event_detail = show(
            event.get("event_detail")
        )

        team = show(
            event.get("team")
        )

        player = show(
            event.get("player_name")
        )

        assist = show(
            event.get("assist_name")
        )

        print()
        print(f"⏱ {minute}'")
        print(f"رویداد: {event_type}")

        if event_detail != "-":
            print(f"جزئیات: {event_detail}")

        print(f"تیم: {team}")
        print(f"بازیکن: {player}")
        print(f"پاس گل: {assist}")


# ============================================================
# 3. ترکیب دو تیم
# ============================================================

lineups_response = get_json(
    f"{BASE_URL}/stored/matches/{MATCH_ID}/lineups"
)

lineups_data = lineups_response.get("data", {})
lineups_meta = lineups_response.get("meta", {})

print_separator("👥 ترکیب")

print(
    f"وضعیت داده ترکیب: "
    f"{show(lineups_meta.get('available'))}"
)

print(
    f"نوع داده ترکیب: "
    f"{show(lineups_meta.get('lineup_shape'))}"
)

formation = lineups_meta.get("formation") or {}

home_formation = formation.get("home")
away_formation = formation.get("away")

print(
    f"آرایش {home_name}: "
    f"{show(home_formation)}"
)

print(
    f"آرایش {away_name}: "
    f"{show(away_formation)}"
)


def print_lineup(team_name, players):

    print()
    print(f"🏟 {team_name}")

    if not players:
        print("اطلاعات ترکیب موجود نیست.")

        return

    starters = []
    substitutes = []

    for player in players:

        if player.get("starter") is True:
            starters.append(player)

        else:
            substitutes.append(player)

    print()
    print("🔹 ترکیب اصلی")

    for player in starters:

        name = show(
            player.get("name")
        )

        position = show(
            player.get("position")
        )

        jersey_number = show(
            player.get("jersey_number")
        )

        player_id = show(
            player.get("player_id")
        )

        print(
            f"{jersey_number} | "
            f"{name} | "
            f"{position} | "
            f"{player_id}"
        )

    print()
    print("🔹 نیمکت")

    for player in substitutes:

        name = show(
            player.get("name")
        )

        position = show(
            player.get("position")
        )

        jersey_number = show(
            player.get("jersey_number")
        )

        player_id = show(
            player.get("player_id")
        )

        print(
            f"{jersey_number} | "
            f"{name} | "
            f"{position} | "
            f"{player_id}"
        )


home_lineup = lineups_data.get("home", [])
away_lineup = lineups_data.get("away", [])

print_lineup(
    home_name,
    home_lineup
)

print_lineup(
    away_name,
    away_lineup
)


# ============================================================
# 4. آمار تیمی
# ============================================================

stats_response = get_json(
    f"{BASE_URL}/stored/matches/{MATCH_ID}/stats"
)

stats_data = stats_response.get("data", {})

team_stats = stats_data.get("team_stats", [])

print_separator("📊 آمار تیمی")

print(
    f"تعداد رکوردهای آمار تیمی: "
    f"{len(team_stats)}"
)


team_stats_grouped = {}

for stat in team_stats:

    team_name = stat.get("team_name", "نامشخص")

    if team_name not in team_stats_grouped:
        team_stats_grouped[team_name] = []

    team_stats_grouped[team_name].append(stat)


for team_name, stats in team_stats_grouped.items():

    print()
    print(f"🔹 {team_name}")

    for stat in stats:

        label = stat.get("label")

        if not label:
            label = stat.get("field")

        value = stat.get("display_value")

        if value is None:
            value = "-"

        print(
            f"{show(label)}: {show(value)}"
        )


# ============================================================
# 5. آمار بازیکنان
# ============================================================

players = stats_data.get("players", [])

print_separator(
    f"👤 آمار بازیکنان ({len(players)})"
)


for player in players:

    name = (
        player.get("name")
        or player.get("player_name")
        or player.get("display_name")
        or "نامشخص"
    )

    print()
    print(f"👤 {name}")

    basic_fields = [
        "id",
        "position",
        "jersey_number",
        "team_id",
        "team_name",
        "headshot_url"
    ]

    for field in basic_fields:

        if field in player:

            print(
                f"{field}: "
                f"{show(player.get(field))}"
            )

    player_stats = player.get("stats")

    if not isinstance(player_stats, dict):
        continue

    print("آمار:")

    for key, stat in player_stats.items():

        if isinstance(stat, dict):

            label = stat.get("label", key)

            value = stat.get("value", "-")

            print(
                f"  {show(label)}: "
                f"{show(value)}"
            )

        else:

            print(
                f"  {key}: "
                f"{show(stat)}"
            )


print()
print("=" * 70)
print("✅ پایان تست")
print("=" * 70)

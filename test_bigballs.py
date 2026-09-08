import os
import requests


API_KEY = os.getenv("BIGBALLS_API_KEY")

MATCH_ID = "f11c25d9-7e10-4cd0-b8fa-9b39827768ce"

BASE_URL = "https://api.bigballsdata.com/v1"

HEADERS = {
    "Authorization": f"Bearer {API_KEY}"
}


# =========================================================
# درخواست به API
# =========================================================

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


# =========================================================
# مقداردهی امن
# =========================================================

def show(value):
    if value is None:
        return "-"
    return str(value)


# =========================================================
# تبدیل زمان رسمی API به دقیقه مسابقه
#
# طبق OpenAPI:
# clock.elapsed_seconds
# clock.added_seconds
# clock.period
# =========================================================

def format_clock(clock):

    if not isinstance(clock, dict):
        return "-"

    elapsed = clock.get("elapsed_seconds")

    if elapsed is None:
        return "-"

    minutes = elapsed // 60
    seconds = elapsed % 60

    added = clock.get("added_seconds")

    if added and added > 0:
        base_minute = 45 if minutes > 45 and minutes < 90 else 90

        if minutes >= 90:
            return f"90+{minutes - 90}"

        if minutes >= 45:
            return f"45+{minutes - 45}"

        return f"{minutes}+{added}"

    return f"{minutes}:{seconds:02d}"


# =========================================================
# اطلاعات اصلی مسابقه
# =========================================================

match_response = get_json(
    f"{BASE_URL}/stored/matches/{MATCH_ID}"
)

match = match_response.get("data", {})

home = match.get("home", {})
away = match.get("away", {})

home_name = home.get("name", "میزبان")
away_name = away.get("name", "مهمان")

score = match.get("score") or {}

print()
print("=" * 70)
print("🏟 اطلاعات مسابقه")
print("=" * 70)

print(
    f"{home_name} "
    f"{show(score.get('home'))} - {show(score.get('away'))} "
    f"{away_name}"
)

print(f"لیگ: {show(match.get('league'))}")
print(f"زمان: {show(match.get('kickoff_utc'))}")
print(f"وضعیت: {show(match.get('status'))}")
print(f"شناسه: {MATCH_ID}")


# =========================================================
# رویدادهای مسابقه
# =========================================================

events_response = get_json(
    f"{BASE_URL}/matches/{MATCH_ID}/events",
    params={
        "sport": "football"
    }
)

events = events_response.get("data", [])

print()
print("=" * 70)
print(f"⚽ رویدادهای مسابقه ({len(events)})")
print("=" * 70)

if not events:

    print("هیچ رویدادی توسط API برنگشته است.")

else:

    for event in events:

        event_type = event.get("type", "-")

        clock = event.get("clock", {})

        minute = format_clock(clock)

        team_id = event.get("team_id")
        player_id = event.get("player_id")
        related_player_id = event.get("related_player_id")

        description = event.get("description")

        print()
        print(
            f"{minute} | {event_type}"
        )

        print(
            f"تیم: {show(team_id)}"
        )

        print(
            f"بازیکن: {show(player_id)}"
        )

        print(
            f"بازیکن مرتبط: {show(related_player_id)}"
        )

        if description:
            print(
                f"توضیح: {description}"
            )


# =========================================================
# ترکیب
# =========================================================

lineups_response = get_json(
    f"{BASE_URL}/stored/matches/{MATCH_ID}/lineups"
)

lineups_data = lineups_response.get("data", {})
lineups_meta = lineups_response.get("meta", {})

print()
print("=" * 70)
print("👥 ترکیب")
print("=" * 70)

print(
    f"وضعیت داده ترکیب: "
    f"{show(lineups_meta.get('available'))}"
)

if lineups_meta.get("coverage_note"):
    print(
        f"توضیح پوشش: "
        f"{lineups_meta.get('coverage_note')}"
    )


# ---------------------------------------------------------
# طبق OpenAPI:
#
# data:
#   home: [{field, value}]
#   away: [{field, value}]
#
# ---------------------------------------------------------

for side, team_name in [
    ("home", home_name),
    ("away", away_name)
]:

    print()
    print(f"🏠 {team_name}")

    lineup = lineups_data.get(side, [])

    if not lineup:
        print("اطلاعاتی موجود نیست.")
        continue

    if isinstance(lineup, list):

        for item in lineup:

            if not isinstance(item, dict):
                print(show(item))
                continue

            field = item.get("field")
            value = item.get("value")

            print(
                f"{show(field)}: {show(value)}"
            )

    else:

        print(show(lineup))


# =========================================================
# آمار مسابقه
# =========================================================

stats_response = get_json(
    f"{BASE_URL}/stored/matches/{MATCH_ID}/stats"
)

stats_data = stats_response.get("data", {})

team_stats = stats_data.get("team_stats", [])
players = stats_data.get("players", [])

print()
print("=" * 70)
print("📊 آمار تیمی")
print("=" * 70)

print(
    f"تعداد رکوردهای آمار تیمی: {len(team_stats)}"
)


# ---------------------------------------------------------
# آمار تیمی
#
# طبق OpenAPI هر رکورد:
# team_id
# team_name
# team_logo_url
# field
# label
# display_value
# fetched_at
# ---------------------------------------------------------

if not team_stats:

    print("هیچ آمار تیمی برنگشته است.")

else:

    current_team = None

    for stat in team_stats:

        if not isinstance(stat, dict):
            continue

        team_name = stat.get("team_name")

        if team_name != current_team:

            current_team = team_name

            print()
            print(
                f"🔹 {show(team_name)}"
            )

        label = stat.get("label")
        field = stat.get("field")
        display_value = stat.get("display_value")

        if label:

            print(
                f"{label}: {show(display_value)}"
            )

        else:

            print(
                f"{show(field)}: {show(display_value)}"
            )


# =========================================================
# آمار بازیکنان
# =========================================================

print()
print("=" * 70)
print(f"👤 آمار بازیکنان ({len(players)})")
print("=" * 70)


if not players:

    print("هیچ آمار بازیکنی برنگشته است.")

else:

    for player in players:

        if not isinstance(player, dict):
            continue

        name = (
            player.get("name")
            or player.get("player_name")
            or player.get("display_name")
            or "نامشخص"
        )

        print()
        print(f"👤 {name}")

        # -------------------------------------------------
        # اطلاعات عمومی بازیکن
        # -------------------------------------------------

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
                    f"{field}: {show(player.get(field))}"
                )

        # -------------------------------------------------
        # آمار بازیکن
        #
        # چون OpenAPI فعلی players را به صورت object عمومی
        # تعریف کرده، هیچ کلید آماری را حدس نمی‌زنیم.
        # تمام کلیدهایی که API واقعاً فرستاده چاپ می‌شوند.
        # -------------------------------------------------

        player_stats = player.get("stats")

        if isinstance(player_stats, dict):

            print("آمار:")

            for key, stat in player_stats.items():

                if isinstance(stat, dict):

                    label = stat.get("label")
                    value = stat.get("value")

                    if label is not None:

                        print(
                            f"  {label}: {show(value)}"
                        )

                    else:

                        print(
                            f"  {key}: {show(value)}"
                        )

                else:

                    print(
                        f"  {key}: {show(stat)}"
                    )

        elif player_stats is not None:

            print(
                f"آمار: {show(player_stats)}"
            )


# =========================================================
# پایان
# =========================================================

print()
print("=" * 70)
print("✅ گزارش تمام شد")
print("=" * 70)

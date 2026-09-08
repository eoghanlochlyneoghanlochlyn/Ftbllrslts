import os
import requests


# ============================================================
# تنظیمات
# ============================================================

API_KEY = os.getenv("BIGBALLS_API_KEY")

BASE_URL = "https://api.bigballsdata.com/v1"

MATCH_ID = "f11c25d9-7e10-4cd0-b8fa-9b39827768ce"

HEADERS = {
    "Authorization": f"Bearer {API_KEY}"
}


# ============================================================
# درخواست به API
# ============================================================

def get_json(url, params=None):
    response = requests.get(
        url,
        headers=HEADERS,
        params=params,
        timeout=30
    )

    response.raise_for_status()

    return response.json()


# ============================================================
# دریافت اطلاعات پایه مسابقه
# ============================================================

def get_match_info(match_id):
    response = get_json(
        f"{BASE_URL}/stored/matches/{match_id}"
    )

    return response.get("data", {})


# ============================================================
# دریافت رویدادهای مسابقه
# ============================================================

def get_match_events(match_id):
    response = get_json(
        f"{BASE_URL}/matches/{match_id}/events",
        params={
            "sport": "football"
        }
    )

    return response.get("data", [])


# ============================================================
# دریافت ترکیب
# ============================================================

def get_match_lineups(match_id):
    response = get_json(
        f"{BASE_URL}/stored/matches/{match_id}/lineups"
    )

    data = response.get("data", {})
    meta = response.get("meta", {})

    return {
        "home": data.get("home", []),
        "away": data.get("away", []),
        "available": meta.get("available", False),
        "lineup_shape": meta.get("lineup_shape"),
        "formation": meta.get("formation", {})
    }


# ============================================================
# دریافت آمار مسابقه
# ============================================================

def get_match_stats(match_id):
    response = get_json(
        f"{BASE_URL}/stored/matches/{match_id}/stats"
    )

    data = response.get("data", {})

    return {
        "team_stats": data.get("team_stats", []),
        "players": data.get("players", [])
    }


# ============================================================
# ساخت اطلاعات کامل مسابقه
# ============================================================

def get_match_data(match_id):

    match = get_match_info(match_id)

    events = get_match_events(match_id)

    lineups = get_match_lineups(match_id)

    stats = get_match_stats(match_id)

    return {
        "match": match,
        "events": events,
        "lineups": lineups,
        "stats": stats
    }


# ============================================================
# نمایش تستی اطلاعات
# ============================================================

def print_match_data(data):

    match = data["match"]
    events = data["events"]
    lineups = data["lineups"]
    stats = data["stats"]

    home = match.get("home", {})
    away = match.get("away", {})

    score = match.get("score") or {}

    print()
    print("=" * 70)
    print("🏟 اطلاعات مسابقه")
    print("=" * 70)

    print(
        f'{home.get("name", "-")} '
        f'{score.get("home", "-")} - '
        f'{score.get("away", "-")} '
        f'{away.get("name", "-")}'
    )

    print(f'لیگ: {match.get("league", "-")}')
    print(f'زمان: {match.get("kickoff_utc", "-")}')
    print(f'وضعیت: {match.get("status", "-")}')
    print(f'شناسه: {match.get("id", "-")}')

    # --------------------------------------------------------
    # رویدادها
    # --------------------------------------------------------

    print()
    print("=" * 70)
    print(f"⚽ رویدادها ({len(events)})")
    print("=" * 70)

    for event in events:

        elapsed = event.get("elapsed")

        elapsed_extra = event.get("elapsed_extra")

        if elapsed is None:
            minute = "-"

        elif elapsed_extra is not None:
            minute = f"{elapsed}+{elapsed_extra}"

        else:
            minute = str(elapsed)

        print(
            f'{minute}\' | '
            f'{event.get("event_type", "-")} | '
            f'{event.get("team", "-")} | '
            f'{event.get("player_name", "-")} | '
            f'پاس گل: {event.get("assist_name", "-")}'
        )

    # --------------------------------------------------------
    # ترکیب
    # --------------------------------------------------------

    print()
    print("=" * 70)
    print("👥 ترکیب")
    print("=" * 70)

    print(
        f'داده موجود: {lineups.get("available", False)}'
    )

    formation = lineups.get("formation", {})

    print(
        f'آرایش {home.get("name", "-")}: '
        f'{formation.get("home", "-")}'
    )

    print(
        f'آرایش {away.get("name", "-")}: '
        f'{formation.get("away", "-")}'
    )

    for side, team in [
        ("home", home),
        ("away", away)
    ]:

        players = lineups.get(side, [])

        print()
        print(f'🏟 {team.get("name", "-")}')

        starters = [
            player
            for player in players
            if player.get("starter") is True
        ]

        substitutes = [
            player
            for player in players
            if player.get("starter") is not True
        ]

        print()
        print("🔹 ترکیب اصلی")

        for player in starters:

            print(
                f'{player.get("jersey_number", "-")} | '
                f'{player.get("name", "-")} | '
                f'{player.get("position", "-")} | '
                f'{player.get("player_id", "-")}'
            )

        print()
        print("🔹 نیمکت")

        for player in substitutes:

            print(
                f'{player.get("jersey_number", "-")} | '
                f'{player.get("name", "-")} | '
                f'{player.get("position", "-")} | '
                f'{player.get("player_id", "-")}'
            )

    # --------------------------------------------------------
    # آمار تیمی
    # --------------------------------------------------------

    team_stats = stats["team_stats"]

    print()
    print("=" * 70)
    print(f"📊 آمار تیمی ({len(team_stats)})")
    print("=" * 70)

    for stat in team_stats:

        team_name = stat.get("team_name", "-")

        label = stat.get("label")

        if not label:
            label = stat.get("field", "-")

        value = stat.get("display_value")

        if value is None:
            value = "-"

        print(
            f'{team_name} | '
            f'{label}: {value}'
        )

    # --------------------------------------------------------
    # آمار بازیکنان
    # --------------------------------------------------------

    players = stats["players"]

    print()
    print("=" * 70)
    print(f"👤 آمار بازیکنان ({len(players)})")
    print("=" * 70)

    for player in players:

        name = (
            player.get("name")
            or player.get("player_name")
            or player.get("display_name")
            or "نامشخص"
        )

        print()
        print(f"👤 {name}")

        print(
            f'تیم: {player.get("team_name", "-")}'
        )

        print(
            f'پست: {player.get("position", "-")}'
        )

        player_stats = player.get("stats")

        if not isinstance(player_stats, dict):
            continue

        for key, stat in player_stats.items():

            if isinstance(stat, dict):

                label = stat.get("label", key)

                value = stat.get("value", "-")

                print(
                    f'  {label}: {value}'
                )

            else:

                print(
                    f'  {key}: {stat}'
                )


# ============================================================
# اجرای تست
# ============================================================

if __name__ == "__main__":

    if not API_KEY:
        print("❌ BIGBALLS_API_KEY پیدا نشد.")

        raise SystemExit(1)

    print("🔄 دریافت اطلاعات مسابقه...")

    try:

        match_data = get_match_data(MATCH_ID)

        print_match_data(match_data)

        print()
        print("=" * 70)
        print("✅ دریافت کامل اطلاعات مسابقه با موفقیت انجام شد.")
        print("=" * 70)

    except requests.HTTPError as error:

        print()
        print("❌ خطای HTTP:")
        print(error)

        raise SystemExit(1)

    except requests.RequestException as error:

        print()
        print("❌ خطای ارتباط با API:")
        print(error)

        raise SystemExit(1)

    except Exception as error:

        print()
        print("❌ خطای غیرمنتظره:")
        print(error)

        raise SystemExit(1)

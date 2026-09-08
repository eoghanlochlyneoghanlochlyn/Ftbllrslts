import os
import json
import requests


# ============================================================
# تنظیمات
# ============================================================

API_KEY = os.getenv("BIGBALLS_API_KEY")

BASE_URL = "https://api.bigballsdata.com"

HEADERS = {
    "Authorization": f"Bearer {API_KEY}"
}


# ============================================================
# شناسه آخرین بازی یوونتوس و میلان
# Juventus 1 - 1 AC Milan
# 2026-09-06
# ============================================================

MATCH_ID = "f11c25d9-7e10-4cd0-b8fa-9b39827768ce"


# ============================================================
# درخواست به API
# ============================================================

def get_api(endpoint, params=None):

    url = f"{BASE_URL}{endpoint}"

    try:
        response = requests.get(
            url,
            headers=HEADERS,
            params=params,
            timeout=30,
        )
    except requests.RequestException as e:
        print(f"❌ خطای اتصال:")
        print(e)
        return None

    print()
    print(f"GET {response.url}")
    print(f"HTTP: {response.status_code}")

    if response.status_code != 200:
        print("❌ پاسخ خطا:")
        print(response.text)
        return None

    try:
        return response.json()
    except ValueError:
        print("❌ پاسخ JSON معتبر نیست.")
        print(response.text)
        return None


# ============================================================
# چاپ JSON مرتب
# ============================================================

def print_json(title, data):

    print()
    print("=" * 80)
    print(title)
    print("=" * 80)

    if data is None:
        print("❌ داده‌ای دریافت نشد.")
        return

    print(
        json.dumps(
            data,
            indent=2,
            ensure_ascii=False
        )
    )


# ============================================================
# اطلاعات پایه مسابقه
# ============================================================

def get_match():

    return get_api(
        f"/v1/stored/matches/{MATCH_ID}"
    )


# ============================================================
# رویدادهای مسابقه
#
# گل
# کارت
# تعویض
# و سایر رویدادها
# ============================================================

def get_events():

    return get_api(
        f"/v1/matches/{MATCH_ID}/events",
        {
            "sport": "football"
        }
    )


# ============================================================
# ترکیب‌ها
# ============================================================

def get_lineups():

    return get_api(
        f"/v1/stored/matches/{MATCH_ID}/lineups"
    )


# ============================================================
# آمار تیمی و بازیکنان
# ============================================================

def get_stats():

    return get_api(
        f"/v1/stored/matches/{MATCH_ID}/stats"
    )


# ============================================================
# جزئیات بازی از events
# ============================================================

def print_events(events):

    if not events:
        return

    data = events.get("data")

    if not isinstance(data, list):
        return

    print()
    print("=" * 80)
    print("⚽ رویدادهای مسابقه")
    print("=" * 80)

    if not data:
        print("هیچ رویدادی ثبت نشده است.")
        return

    for index, event in enumerate(data, 1):

        print()
        print(f"رویداد {index}")
        print("-" * 50)

        if isinstance(event, dict):

            # چند فیلد رایج را اول نمایش می‌دهیم
            preferred_fields = [
                "minute",
                "period",
                "clock",
                "type",
                "event_type",
                "player",
                "player_name",
                "team",
                "team_name",
                "assist",
                "assist_name",
                "description",
            ]

            printed = set()

            for field in preferred_fields:

                if field not in event:
                    continue

                value = event[field]

                if value is None:
                    continue

                print(f"{field}: {value}")
                printed.add(field)

            # اگر فیلدهای دیگری هم وجود داشتند
            # آنها را هم نشان می‌دهیم
            for key, value in event.items():

                if key in printed:
                    continue

                print(f"{key}: {value}")


# ============================================================
# نمایش ترکیب‌ها
# ============================================================

def print_lineups(lineups):

    if not lineups:
        return

    print()
    print("=" * 80)
    print("👥 ترکیب تیم‌ها")
    print("=" * 80)

    data = lineups.get("data")

    if not isinstance(data, dict):
        print("ساختار ترکیب قابل شناسایی نیست.")
        return

    meta = lineups.get("meta")

    if isinstance(meta, dict):

        available = meta.get("available")

        print(
            f"داده ترکیب در API موجود است: {available}"
        )

        if meta.get("coverage_note"):
            print(
                f"توضیح: {meta.get('coverage_note')}"
            )

    for side in ["home", "away"]:

        players = data.get(side)

        print()
        print("-" * 80)
        print(
            "ترکیب میزبان"
            if side == "home"
            else "ترکیب مهمان"
        )
        print("-" * 80)

        if not players:
            print("اطلاعاتی وجود ندارد.")
            continue

        for player in players:

            if not isinstance(player, dict):
                print(player)
                continue

            print()

            # ساختار رسمی endpoint به شکل
            # field / value است.
            if "field" in player:

                field = player.get("field")
                value = player.get("value")

                print(
                    f"{field}: {value}"
                )

            else:

                print(
                    json.dumps(
                        player,
                        ensure_ascii=False
                    )
                )


# ============================================================
# نمایش آمار تیمی
# ============================================================

def print_team_stats(stats):

    if not stats:
        return

    data = stats.get("data")

    if not isinstance(data, dict):
        return

    team_stats = data.get("team_stats")

    print()
    print("=" * 80)
    print("📊 آمار تیمی")
    print("=" * 80)

    if not team_stats:
        print("آمار تیمی موجود نیست.")
        return

    current_team = None

    for stat in team_stats:

        if not isinstance(stat, dict):
            continue

        team_name = stat.get(
            "team_name",
            "نامشخص"
        )

        if team_name != current_team:

            print()
            print("-" * 60)
            print(team_name)
            print("-" * 60)

            current_team = team_name

        field = stat.get(
            "label"
        ) or stat.get(
            "field",
            "نامشخص"
        )

        value = stat.get(
            "display_value"
        )

        if value is None:
            value = stat.get("value")

        print(
            f"{field}: {value}"
        )


# ============================================================
# نمایش آمار بازیکنان
# ============================================================

def print_player_stats(stats):

    if not stats:
        return

    data = stats.get("data")

    if not isinstance(data, dict):
        return

    players = data.get("players")

    print()
    print("=" * 80)
    print("👤 آمار بازیکنان")
    print("=" * 80)

    if not players:
        print("آمار بازیکنان موجود نیست.")
        return

    for index, player in enumerate(players, 1):

        print()
        print("-" * 60)
        print(f"بازیکن {index}")
        print("-" * 60)

        if isinstance(player, dict):

            print(
                json.dumps(
                    player,
                    indent=2,
                    ensure_ascii=False
                )
            )

        else:

            print(player)


# ============================================================
# خلاصه اطلاعات مسابقه
# ============================================================

def print_match_summary(match):

    if not match:
        return

    data = match.get("data", match)

    if not isinstance(data, dict):
        return

    print()
    print("=" * 80)
    print("🏟 اطلاعات مسابقه")
    print("=" * 80)

    home = data.get("home") or {}
    away = data.get("away") or {}
    score = data.get("score") or {}

    print(
        f"میزبان: {home.get('name', 'نامشخص')}"
    )

    print(
        f"مهمان: {away.get('name', 'نامشخص')}"
    )

    print(
        f"نتیجه: "
        f"{score.get('home', '?')} - "
        f"{score.get('away', '?')}"
    )

    print(
        f"لیگ: {data.get('league', 'نامشخص')}"
    )

    print(
        f"زمان: "
        f"{data.get('kickoff_utc', 'نامشخص')}"
    )

    print(
        f"وضعیت: "
        f"{data.get('status', 'نامشخص')}"
    )

    print(
        f"شناسه مسابقه: "
        f"{data.get('id', MATCH_ID)}"
    )


# ============================================================
# اجرای اصلی
# ============================================================

def main():

    if not API_KEY:

        print(
            "❌ BIGBALLS_API_KEY پیدا نشد."
        )

        return

    print("=" * 80)
    print("⚽ اطلاعات کامل Juventus - AC Milan")
    print("=" * 80)

    print()
    print(f"Match ID: {MATCH_ID}")

    # --------------------------------------------------------
    # 1. اطلاعات پایه مسابقه
    # --------------------------------------------------------

    match = get_match()

    print_match_summary(match)

    # --------------------------------------------------------
    # 2. رویدادها
    # --------------------------------------------------------

    events = get_events()

    print_events(events)

    # --------------------------------------------------------
    # 3. ترکیب
    # --------------------------------------------------------

    lineups = get_lineups()

    print_lineups(lineups)

    # --------------------------------------------------------
    # 4. آمار
    # --------------------------------------------------------

    stats = get_stats()

    print_team_stats(stats)

    print_player_stats(stats)

    # --------------------------------------------------------
    # پایان
    # --------------------------------------------------------

    print()
    print("=" * 80)
    print("📦 داده خام API")
    print("=" * 80)

    print()
    print("----- MATCH -----")
    print_json(
        "اطلاعات خام مسابقه",
        match
    )

    print()
    print("----- EVENTS -----")
    print_json(
        "رویدادهای خام",
        events
    )

    print()
    print("----- LINEUPS -----")
    print_json(
        "ترکیب خام",
        lineups
    )

    print()
    print("----- STATS -----")
    print_json(
        "آمار خام",
        stats
    )

    print()
    print("=" * 80)
    print("✅ پایان")
    print("=" * 80)


if __name__ == "__main__":
    main()

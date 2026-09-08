import os
import requests
from datetime import datetime, timezone


# ============================================================
# تنظیمات
# ============================================================

API_KEY = os.getenv("BIGBALLS_API_KEY")

BASE_URL = "https://api.bigballsdata.com/v1"

HEADERS = {
    "Authorization": f"Bearer {API_KEY}"
}


# ============================================================
# ۱۵ تیم موردنظر
# ============================================================

TRACKED_TEAMS = {
    "Liverpool",
    "Arsenal",
    "Manchester City",
    "Manchester United",
    "Chelsea",
    "Tottenham Hotspur",
    "Juventus",
    "AC Milan",
    "Inter Milan",
    "Bayern Munich",
    "Borussia Dortmund",
    "Paris Saint-Germain",
    "Real Madrid",
    "Barcelona",
    "Atlético Madrid",
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
# دریافت مسابقات آینده
# ============================================================

def get_upcoming_matches():

    response = get_json(
        f"{BASE_URL}/matches",
        params={
            "sport": "football",
            "status": "scheduled",
            "limit": 200
        }
    )

    return response.get("data", [])


# ============================================================
# پیدا کردن تیم موردنظر
# ============================================================

def get_tracked_team(match):

    home = match.get("home") or {}
    away = match.get("away") or {}

    home_name = home.get("name")
    away_name = away.get("name")

    if home_name in TRACKED_TEAMS:
        return home_name

    if away_name in TRACKED_TEAMS:
        return away_name

    return None


# ============================================================
# تبدیل زمان مسابقه
# ============================================================

def parse_kickoff(kickoff_utc):

    if not kickoff_utc:
        return None

    try:

        return datetime.fromisoformat(
            kickoff_utc.replace("Z", "+00:00")
        )

    except ValueError:

        return None


# ============================================================
# پیدا کردن مسابقاتی که حداکثر یک ساعت تا شروعشان مانده
# ============================================================

def get_matches_near_kickoff(matches):

    now = datetime.now(timezone.utc)

    near_matches = []

    for match in matches:

        if not get_tracked_team(match):
            continue

        kickoff = parse_kickoff(
            match.get("kickoff_utc")
        )

        if kickoff is None:
            continue

        seconds_until_kickoff = (
            kickoff - now
        ).total_seconds()

        # فقط مسابقاتی که:
        # از همین لحظه تا یک ساعت آینده شروع می‌شوند

        if 0 <= seconds_until_kickoff <= 3600:

            near_matches.append(
                match
            )

    return near_matches


# ============================================================
# دریافت ترکیب
# ============================================================

def get_lineups(match_id):

    response = get_json(
        f"{BASE_URL}/stored/matches/{match_id}/lineups"
    )

    data = response.get("data") or {}
    meta = response.get("meta") or {}

    return {
        "home": data.get("home") or [],
        "away": data.get("away") or [],
        "available": meta.get(
            "available",
            False
        ),
        "formation": meta.get(
            "formation",
            {}
        )
    }


# ============================================================
# نمایش ترکیب یک تیم
# ============================================================

def print_team_lineup(
    team_name,
    players,
    formation
):

    print()
    print(f"🏟️ {team_name}")

    if formation:
        print(
            f"📐 آرایش: "
            f"{formation}"
        )

    print()
    print("🔵 ترکیب اصلی:")

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

    if starters:

        for player in starters:

            number = player.get(
                "jersey_number",
                "-"
            )

            name = player.get(
                "name",
                "-"
            )

            position = player.get(
                "position",
                "-"
            )

            print(
                f"  {number}. "
                f"{name} "
                f"({position})"
            )

    else:

        print(
            "  بازیکن اطلاعاتی ندارد."
        )

    print()
    print("🟡 نیمکت:")

    if substitutes:

        for player in substitutes:

            number = player.get(
                "jersey_number",
                "-"
            )

            name = player.get(
                "name",
                "-"
            )

            position = player.get(
                "position",
                "-"
            )

            print(
                f"  {number}. "
                f"{name} "
                f"({position})"
            )

    else:

        print(
            "  بازیکن اطلاعاتی ندارد."
        )


# ============================================================
# بررسی ترکیب مسابقات نزدیک
# ============================================================

def check_lineups(matches):

    for match in matches:

        match_id = match.get("id")

        home = match.get("home") or {}
        away = match.get("away") or {}

        home_name = home.get(
            "name",
            "-"
        )

        away_name = away.get(
            "name",
            "-"
        )

        kickoff = parse_kickoff(
            match.get("kickoff_utc")
        )

        now = datetime.now(timezone.utc)

        minutes_left = (
            kickoff - now
        ).total_seconds() / 60

        print()
        print("=" * 70)

        print(
            f"⚽ {home_name} "
            f"vs "
            f"{away_name}"
        )

        print(
            f"🏆 لیگ: "
            f"{match.get('league', '-')}"
        )

        print(
            f"🕐 شروع: "
            f"{match.get('kickoff_utc', '-')}"
        )

        print(
            f"⏳ زمان باقی‌مانده: "
            f"{minutes_left:.1f} دقیقه"
        )

        print(
            f"🆔 شناسه: "
            f"{match_id}"
        )

        print("=" * 70)

        try:

            lineups = get_lineups(
                match_id
            )

        except requests.HTTPError as error:

            print()
            print(
                "❌ خطا در دریافت ترکیب:"
            )

            print(error)

            continue

        if not lineups["available"]:

            print()
            print(
                "⏳ ترکیب رسمی هنوز منتشر نشده."
            )

            continue

        print()
        print(
            "✅ ترکیب رسمی منتشر شده."
        )

        formation = (
            lineups["formation"]
            or {}
        )

        home_formation = formation.get(
            "home"
        )

        away_formation = formation.get(
            "away"
        )

        print_team_lineup(
            home_name,
            lineups["home"],
            home_formation
        )

        print_team_lineup(
            away_name,
            lineups["away"],
            away_formation
        )


# ============================================================
# اجرای اصلی
# ============================================================

def main():

    if not API_KEY:

        print(
            "❌ BIGBALLS_API_KEY پیدا نشد."
        )

        raise SystemExit(1)

    print(
        "🔄 دریافت مسابقات آینده فوتبال..."
    )

    try:

        all_matches = (
            get_upcoming_matches()
        )

    except requests.HTTPError as error:

        print()
        print("❌ خطای HTTP:")
        print(error)

        raise SystemExit(1)

    except requests.RequestException as error:

        print()
        print(
            "❌ خطای ارتباط با API:"
        )

        print(error)

        raise SystemExit(1)

    near_matches = (
        get_matches_near_kickoff(
            all_matches
        )
    )

    print()
    print("=" * 70)

    print(
        f"⚽ مسابقات مربوط به ۱۵ تیم: "
        f"{sum(1 for match in all_matches if get_tracked_team(match))}"
    )

    print(
        f"⏳ مسابقات در یک ساعت آینده: "
        f"{len(near_matches)}"
    )

    print("=" * 70)

    if not near_matches:

        print()
        print(
            "ℹ️ در یک ساعت آینده "
            "مسابقه‌ای از ۱۵ تیم نداریم."
        )

        return

    check_lineups(
        near_matches
    )

    print()
    print("=" * 70)
    print(
        "✅ بررسی ترکیب‌ها تمام شد."
    )
    print("=" * 70)


# ============================================================
# اجرا
# ============================================================

if __name__ == "__main__":
    main()

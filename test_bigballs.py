import os
import requests

API_KEY = os.environ.get("BIGBALLS_API_KEY")

BASE_URL = "https://api.bigballsdata.com"

HEADERS = {
    "Authorization": f"Bearer {API_KEY}"
}


# ============================================================
# تیم‌های موردنظر
# ============================================================

TARGET_TEAMS = {
    "epl": [
        "Liverpool",
        "Arsenal",
        "Manchester City",
        "Manchester United",
        "Chelsea",
        "Tottenham Hotspur",
    ],

    "seriea": [
        "Juventus",
        "AC Milan",
        "Inter",
    ],

    "bundesliga": [
        "Bayern Munich",
        "Borussia Dortmund",
    ],

    "ligue1": [
        "Paris Saint-Germain",
    ],

    "laliga": [
        "Real Madrid",
        "Barcelona",
        "Atletico Madrid",
    ],
}


# ============================================================
# بررسی کلید
# ============================================================

if not API_KEY:
    print("❌ کلید BIGBALLS_API_KEY پیدا نشد.")
    exit(1)


# ============================================================
# دریافت تیم‌های هر لیگ
# ============================================================

print("=" * 70)
print("⚽ پیدا کردن شناسه تیم‌های موردنظر")
print("=" * 70)


found_teams = {}


for league, wanted_names in TARGET_TEAMS.items():

    print()
    print("=" * 70)
    print(f"🏆 لیگ: {league}")
    print("=" * 70)

    url = f"{BASE_URL}/v1/teams"

    params = {
        "sport": "football",
        "league": league,
    }

    try:
        response = requests.get(
            url,
            headers=HEADERS,
            params=params,
            timeout=20
        )

    except requests.RequestException as e:
        print("❌ خطا در اتصال:")
        print(e)
        continue

    print(f"HTTP: {response.status_code}")

    if response.status_code != 200:
        print("❌ دریافت تیم‌ها ناموفق بود.")
        print(response.text)
        continue

    try:
        data = response.json()

    except ValueError:
        print("❌ پاسخ دریافتی JSON نیست.")
        print(response.text)
        continue

    teams = data.get("data", [])

    print(f"📊 تعداد تیم‌های دریافت‌شده: {len(teams)}")

    found_teams[league] = {}

    # --------------------------------------------------------
    # جستجوی تیم‌های موردنظر
    # --------------------------------------------------------

    for wanted_name in wanted_names:

        found = None

        wanted_lower = wanted_name.lower().strip()

        for team in teams:

            team_name = str(
                team.get("name", "")
            ).strip()

            if team_name.lower() == wanted_lower:
                found = team
                break

        if found:

            team_id = found.get("id")
            team_name = found.get("name")

            found_teams[league][team_name] = team_id

            print()
            print(f"✅ {team_name}")
            print(f"   شناسه: {team_id}")

        else:

            print()
            print(f"❌ پیدا نشد: {wanted_name}")


# ============================================================
# نمایش خلاصه نهایی
# ============================================================

print()
print("=" * 70)
print("📋 خلاصه نهایی شناسه تیم‌ها")
print("=" * 70)


for league, teams in found_teams.items():

    print()
    print(f"🏆 {league}")

    if not teams:
        print("   هیچ تیمی پیدا نشد.")
        continue

    for team_name, team_id in teams.items():

        print(
            f"   {team_name}: {team_id}"
        )


print()
print("=" * 70)
print("🏁 تست تمام شد.")
print("=" * 70)

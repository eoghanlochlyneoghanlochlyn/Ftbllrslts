import os
import requests

API_KEY = os.environ.get("BIGBALLS_API_KEY")

BASE_URL = "https://api.bigballsdata.com"

HEADERS = {
    "Authorization": f"Bearer {API_KEY}"
}


# ============================================================
# بررسی کلید
# ============================================================

if not API_KEY:
    print("❌ کلید BIGBALLS_API_KEY پیدا نشد.")
    exit(1)


# ============================================================
# لیگ‌هایی که باید بررسی شوند
# ============================================================

LEAGUES = {
    "seriea": "سری آ",
    "laliga": "لالیگا",
}


# ============================================================
# جستجوی نام تیم
# ============================================================

SEARCH_NAMES = [
    "Inter",
    "Atletico",
]


print("=" * 70)
print("🔎 پیدا کردن نام دقیق اینتر و اتلتیکو مادرید")
print("=" * 70)


for league_id, league_name in LEAGUES.items():

    print()
    print("=" * 70)
    print(f"🏆 {league_name} ({league_id})")
    print("=" * 70)

    url = f"{BASE_URL}/v1/teams"

    params = {
        "sport": "football",
        "league": league_id,
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
        print("❌ درخواست ناموفق بود.")
        print(response.text)
        continue

    try:
        data = response.json()

    except ValueError:
        print("❌ پاسخ JSON نیست.")
        print(response.text)
        continue

    teams = data.get("data", [])

    print(f"📊 تعداد تیم‌ها: {len(teams)}")
    print()

    found_any = False

    for team in teams:

        name = str(team.get("name", "")).strip()

        name_lower = name.lower()

        for search_name in SEARCH_NAMES:

            if search_name.lower() in name_lower:

                print(f"✅ نام ثبت‌شده: {name}")
                print(f"   شناسه: {team.get('id')}")
                print()

                found_any = True
                break

    if not found_any:

        print("❌ مورد مشابهی پیدا نشد.")


print()
print("=" * 70)
print("🏁 تست تمام شد.")
print("=" * 70)

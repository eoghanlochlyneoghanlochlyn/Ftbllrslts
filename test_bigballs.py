import os
import requests

API_KEY = os.environ.get("BIGBALLS_API_KEY")

BASE_URL = "https://api.bigballsdata.com"

HEADERS = {
    "Authorization": f"Bearer {API_KEY}"
}


# ============================================================
# تنظیمات
# ============================================================

LEAGUE = "epl"

SELECTED_TEAMS = {
    "d1b0b567-a653-43f6-8d47-d230c447650f": "Arsenal",
    "544de6be-906a-40c9-8d32-17ed7239348f": "Chelsea",
}


# ============================================================
# بررسی کلید
# ============================================================

if not API_KEY:
    print("❌ کلید BIGBALLS_API_KEY پیدا نشد.")
    exit(1)


# ============================================================
# دریافت مسابقات لیگ
# ============================================================

print("=" * 70)
print("⚽ تست انتخاب تیم‌های مشخص")
print("=" * 70)

print()
print(f"🏆 لیگ: {LEAGUE}")
print("👥 تیم‌های انتخاب‌شده:")

for team_id, team_name in SELECTED_TEAMS.items():
    print(f"   - {team_name}")

print()
print("=" * 70)
print("📡 دریافت مسابقات...")
print("=" * 70)


url = f"{BASE_URL}/v1/matches"

params = {
    "sport": "football",
    "league": LEAGUE
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
    exit(1)


print()
print(f"HTTP: {response.status_code}")


if response.status_code != 200:
    print("❌ دریافت مسابقات ناموفق بود.")
    print(response.text)
    exit(1)


try:
    data = response.json()

except ValueError:
    print("❌ پاسخ دریافتی JSON نیست.")
    print(response.text)
    exit(1)


matches = data.get("data", [])

print(f"✅ تعداد کل مسابقات دریافت‌شده: {len(matches)}")


# ============================================================
# پیدا کردن مسابقات تیم‌های انتخاب‌شده
# ============================================================

selected_matches = []

for match in matches:

    home = match.get("home") or {}
    away = match.get("away") or {}

    home_id = home.get("id")
    away_id = away.get("id")

    if home_id in SELECTED_TEAMS or away_id in SELECTED_TEAMS:
        selected_matches.append(match)


# ============================================================
# نمایش نتیجه
# ============================================================

print()
print("=" * 70)
print("🎯 مسابقات مربوط به تیم‌های انتخاب‌شده")
print("=" * 70)

print()

if not selected_matches:

    print("❌ هیچ مسابقه‌ای پیدا نشد.")

else:

    print(
        f"✅ تعداد مسابقات پیدا‌شده: {len(selected_matches)}"
    )

    print()

    for index, match in enumerate(selected_matches, start=1):

        match_id = match.get("id")
        status = match.get("status")
        score = match.get("score")

        home = match.get("home") or {}
        away = match.get("away") or {}

        home_name = home.get("name", "نامشخص")
        away_name = away.get("name", "نامشخص")

        home_id = home.get("id")
        away_id = away.get("id")

        selected_team_name = None

        if home_id in SELECTED_TEAMS:
            selected_team_name = SELECTED_TEAMS[home_id]

        elif away_id in SELECTED_TEAMS:
            selected_team_name = SELECTED_TEAMS[away_id]

        print("-" * 70)
        print(f"مسابقه {index}")
        print(f"تیم انتخاب‌شده: {selected_team_name}")
        print(f"مسابقه: {home_name} - {away_name}")
        print(f"وضعیت: {status}")
        print(f"نتیجه: {score}")
        print(f"شناسه مسابقه: {match_id}")


print()
print("=" * 70)
print("🏁 تست تمام شد.")
print("=" * 70)

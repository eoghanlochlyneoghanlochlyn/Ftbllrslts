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
# دریافت تیم‌های لالیگا
# ============================================================

print("=" * 70)
print("🇪🇸 فهرست تیم‌های لالیگا")
print("=" * 70)

url = f"{BASE_URL}/v1/teams"

params = {
    "sport": "football",
    "league": "laliga",
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
    print("❌ دریافت تیم‌ها ناموفق بود.")
    print(response.text)
    exit(1)


try:
    data = response.json()

except ValueError:
    print("❌ پاسخ دریافتی JSON نیست.")
    print(response.text)
    exit(1)


teams = data.get("data", [])

print()
print(f"📊 تعداد تیم‌ها: {len(teams)}")
print()


# ============================================================
# نمایش تیم‌ها
# ============================================================

for index, team in enumerate(teams, start=1):

    name = team.get("name", "نامشخص")
    team_id = team.get("id")

    print(
        f"{index:02d}. {name}"
    )

    print(
        f"    شناسه: {team_id}"
    )

    print()


# ============================================================
# پایان
# ============================================================

print("=" * 70)
print("🏁 تست تمام شد.")
print("=" * 70)

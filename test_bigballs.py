import os
import requests

API_KEY = os.environ.get("BIGBALLS_API_KEY")

print("=" * 60)
print("⚽ تست دریافت مسابقات فوتبال از Big Balls Sports Data")
print("=" * 60)

if not API_KEY:
    print("❌ کلید BIGBALLS_API_KEY پیدا نشد.")
    exit(1)

URL = "https://api.bigballsdata.com/v1/matches"

HEADERS = {
    "Authorization": f"Bearer {API_KEY}"
}

PARAMS = {
    "sport": "football"
}

try:
    response = requests.get(
        URL,
        headers=HEADERS,
        params=PARAMS,
        timeout=20
    )

    print(f"HTTP: {response.status_code}")
    print()

    if response.status_code != 200:
        print("❌ درخواست ناموفق بود.")
        print(response.text)
        exit(1)

    data = response.json()

    print("✅ دریافت مسابقات موفق بود.")
    print()

    matches = data.get("data", [])

    print(f"⚽ تعداد مسابقات دریافت‌شده: {len(matches)}")
    print()

    if not matches:
        print("⚠️ هیچ مسابقه‌ای برنگشت.")
        print()
        print("پاسخ کامل API:")
        print(data)
        exit(0)

    print("=" * 60)

    for i, match in enumerate(matches[:20], start=1):

        match_id = match.get("id", "نامشخص")

        home = match.get("home", {})
        away = match.get("away", {})

        if isinstance(home, dict):
            home_name = home.get("name", "نامشخص")
        else:
            home_name = str(home)

        if isinstance(away, dict):
            away_name = away.get("name", "نامشخص")
        else:
            away_name = str(away)

        score = match.get("score", {})
        status = match.get("status", "نامشخص")
        kickoff = match.get("kickoff_utc", "نامشخص")
        league = match.get("league", "نامشخص")

        print(f"#{i}")
        print(f"مسابقه: {home_name} - {away_name}")
        print(f"شناسه: {match_id}")
        print(f"زمان: {kickoff}")
        print(f"وضعیت: {status}")
        print(f"نتیجه: {score}")
        print(f"لیگ: {league}")
        print("-" * 60)

except requests.RequestException as e:
    print("❌ خطا در اتصال به سرور:")
    print(e)

except Exception as e:
    print("❌ خطای غیرمنتظره:")
    print(e)

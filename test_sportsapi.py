import os
import requests


API_KEY = os.environ.get("SPORTS_API_KEY")

if not API_KEY:
    print("❌ کلید SPORTS_API_KEY پیدا نشد.")
    exit(1)


URL = "https://api.sportsapi.app/v2/livescores"

HEADERS = {
    "Authorization": f"Bearer {API_KEY}"
}


print("=" * 50)
print("⚽ تست اتصال به SportsAPI")
print("=" * 50)

try:
    response = requests.get(
        URL,
        headers=HEADERS,
        params={"sport": "football"},
        timeout=20
    )

    print(f"HTTP: {response.status_code}")
    print()

    if response.status_code != 200:
        print("❌ درخواست ناموفق بود.")
        print(response.text)
        exit(1)

    data = response.json()

    print("✅ اتصال به SportsAPI موفق بود.")
    print()

    matches = data.get("data", [])

    print(f"⚽ تعداد مسابقات زنده: {len(matches)}")
    print()

    for match in matches[:10]:
        home = match.get("home", {}).get("name", "نامشخص")
        away = match.get("away", {}).get("name", "نامشخص")

        home_score = match.get("homeScore", {}).get("current", 0)
        away_score = match.get("awayScore", {}).get("current", 0)

        status = match.get("status", {}).get("type", "نامشخص")

        print(f"{home} {home_score} - {away_score} {away}")
        print(f"وضعیت: {status}")
        print(f"شناسه مسابقه: {match.get('id')}")
        print("-" * 40)

except requests.RequestException as e:
    print("❌ خطا در اتصال:")
    print(e)

except Exception as e:
    print("❌ خطای غیرمنتظره:")
    print(e)

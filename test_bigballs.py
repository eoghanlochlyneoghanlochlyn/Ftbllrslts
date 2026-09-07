import os
import requests
import json

API_KEY = os.environ.get("BIGBALLS_API_KEY")

BASE_URL = "https://api.bigballsdata.com"

HEADERS = {
    "Authorization": f"Bearer {API_KEY}"
}


print("=" * 70)
print("⚽ تست فیلتر مسابقات لیگ برتر انگلیس")
print("=" * 70)


if not API_KEY:
    print("❌ کلید BIGBALLS_API_KEY پیدا نشد.")
    exit(1)


url = f"{BASE_URL}/v1/matches"

params = {
    "sport": "football",
    "league": "epl"
}


try:
    response = requests.get(
        url,
        headers=HEADERS,
        params=params,
        timeout=20
    )

    print(f"HTTP: {response.status_code}")
    print()

    if response.status_code != 200:
        print("❌ درخواست ناموفق بود.")
        print(response.text)
        exit(1)

    data = response.json()

    print("✅ درخواست موفق بود.")
    print()

    matches = data.get("data", [])

    print(f"📊 تعداد مسابقات دریافت‌شده: {len(matches)}")
    print()

    for index, match in enumerate(matches, start=1):

        print("-" * 70)
        print(f"مسابقه {index}")

        print(
            "شناسه:",
            match.get("id")
        )

        print(
            "لیگ:",
            match.get("league")
        )

        print(
            "وضعیت:",
            match.get("status")
        )

        home = match.get("home", {})
        away = match.get("away", {})

        print(
            "میزبان:",
            home.get("name"),
            "| شناسه:",
            home.get("id")
        )

        print(
            "میهمان:",
            away.get("name"),
            "| شناسه:",
            away.get("id")
        )

        print(
            "نتیجه:",
            match.get("score")
        )

    print()
    print("=" * 70)
    print("پاسخ خام API")
    print("=" * 70)
    print(json.dumps(data, ensure_ascii=False, indent=2))

except requests.RequestException as e:
    print("❌ خطا در اتصال:")
    print(e)
    exit(1)

except ValueError:
    print("❌ پاسخ دریافتی JSON نیست.")
    print(response.text)
    exit(1)


print()
print("=" * 70)
print("🏁 تست تمام شد.")
print("=" * 70)

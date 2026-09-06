import os
import requests


API_KEY = os.environ.get("SPORTS_API_KEY")

if not API_KEY:
    print("❌ کلید SPORTS_API_KEY پیدا نشد.")
    print("کلید را در GitHub Secrets با همین نام ساخته‌ای؟")
    exit(1)


URL = "https://v3.football.api-sports.io/status"

HEADERS = {
    "x-apisports-key": API_KEY
}


print("=" * 50)
print("⚽ تست اتصال به API فوتبال")
print("=" * 50)

try:
    response = requests.get(
        URL,
        headers=HEADERS,
        timeout=20
    )

    print(f"HTTP: {response.status_code}")
    print()

    if response.status_code != 200:
        print("❌ اتصال موفق نبود.")
        print(response.text)
        exit(1)

    data = response.json()

    print("✅ اتصال به API موفق بود.")
    print()

    print("پاسخ API:")
    print(data)

except requests.RequestException as e:
    print("❌ خطا در اتصال:")
    print(e)

except Exception as e:
    print("❌ خطای غیرمنتظره:")
    print(e)

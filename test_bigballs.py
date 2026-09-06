import os
import requests

API_KEY = os.environ.get("BIGBALLS_API_KEY")

print("=" * 50)
print("⚽ تست اتصال به Big Balls Sports Data")
print("=" * 50)

if not API_KEY:
    print("❌ کلید BIGBALLS_API_KEY پیدا نشد.")
    exit(1)

URL = "https://api.bigballsdata.com/v1/user/me"

HEADERS = {
    "Authorization": f"Bearer {API_KEY}"
}

try:
    response = requests.get(
        URL,
        headers=HEADERS,
        timeout=20
    )

    print(f"HTTP: {response.status_code}")
    print()

    print("پاسخ خام:")
    print(response.text)
    print()

    if response.status_code == 200:
        data = response.json()

        print("✅ اتصال و احراز هویت موفق بود.")
        print()

        user_data = data.get("data", {})
        limits = user_data.get("limits", {})

        print(f"پلن: {user_data.get('plan', 'نامشخص')}")
        print(f"اتصال گیت‌هاب: {user_data.get('github_connected', 'نامشخص')}")
        print(f"سهمیه در دقیقه: {limits.get('per_minute', 'نامشخص')}")
        print(f"سهمیه روزانه: {limits.get('per_day', 'نامشخص')}")

    else:
        print("❌ درخواست ناموفق بود.")

except requests.RequestException as e:
    print("❌ خطا در اتصال به سرور:")
    print(e)

except Exception as e:
    print("❌ خطای غیرمنتظره:")
    print(e)

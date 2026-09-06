import os
import requests
import json

API_KEY = os.environ.get("BIGBALLS_API_KEY")

MATCH_ID = "81e729fe-277e-4e91-b490-3cb14d253025"

BASE_URL = "https://api.bigballsdata.com"

HEADERS = {
    "Authorization": f"Bearer {API_KEY}"
}

print("=" * 70)
print("⚽ تست کامل مسابقه Everton - Manchester United")
print("=" * 70)

if not API_KEY:
    print("❌ کلید BIGBALLS_API_KEY پیدا نشد.")
    exit(1)


def request_api(name, url, params=None):
    print()
    print("=" * 70)
    print(name)
    print("=" * 70)
    print(f"URL: {url}")

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
            return None

        try:
            data = response.json()
        except ValueError:
            print("❌ پاسخ JSON نیست.")
            print(response.text)
            return None

        print("✅ درخواست موفق بود.")
        print()
        print("پاسخ کامل:")
        print(json.dumps(data, ensure_ascii=False, indent=2))

        return data

    except requests.RequestException as e:
        print("❌ خطا در اتصال:")
        print(e)
        return None


if not API_KEY:
    exit(1)


# --------------------------------------------------
# ۱. جزئیات مسابقه
# --------------------------------------------------

request_api(
    "۱. جزئیات مسابقه",
    f"{BASE_URL}/v1/matches/{MATCH_ID}",
    {
        "sport": "football"
    }
)


# --------------------------------------------------
# ۲. رویدادهای مسابقه
# --------------------------------------------------

request_api(
    "۲. رویدادهای مسابقه؛ گل، کارت، تعویض و...",
    f"{BASE_URL}/v1/matches/{MATCH_ID}/events",
    {
        "sport": "football"
    }
)


# --------------------------------------------------
# ۳. ترکیب مسابقه
# --------------------------------------------------

request_api(
    "۳. ترکیب تیم‌ها",
    f"{BASE_URL}/v1/stored/matches/{MATCH_ID}/lineups"
)


print()
print("=" * 70)
print("🏁 تست تمام شد.")
print("=" * 70)

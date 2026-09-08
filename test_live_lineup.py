import os
import json
import requests


API_KEY = os.getenv("BIGBALLS_API_KEY")

BASE_URL = "https://api.bigballsdata.com/v1"

HEADERS = {
    "Authorization": f"Bearer {API_KEY}"
}


def get_json(url, params=None):

    response = requests.get(
        url,
        headers=HEADERS,
        params=params,
        timeout=30
    )

    print("HTTP:", response.status_code)

    response.raise_for_status()

    return response.json()


print("🔎 در حال بررسی مسابقات ذخیره‌شده...")

response = get_json(
    f"{BASE_URL}/stored/matches",
    params={
        "sport": "football",
        "limit": 200
    }
)

matches = response.get("data", [])

print()
print("📥 تعداد مسابقات دریافت‌شده:", len(matches))

print()
print("🔎 بررسی ترکیب مسابقات...")
print("=" * 80)

found = 0

for match in matches:

    match_id = match.get("id")

    home = match.get("home", {})
    away = match.get("away", {})

    home_name = home.get("name", "")
    away_name = away.get("name", "")

    if not match_id:
        continue

    lineup_url = (
        f"{BASE_URL}/stored/matches/"
        f"{match_id}/lineups"
    )

    try:

        lineup_response = requests.get(
            lineup_url,
            headers=HEADERS,
            timeout=30
        )

        if lineup_response.status_code != 200:
            continue

        lineup_data = lineup_response.json()

        meta = lineup_data.get("meta", {})
        data = lineup_data.get("data", {})

        available = meta.get("available", False)

        home_lineup = data.get("home", [])
        away_lineup = data.get("away", [])

        if available and (home_lineup or away_lineup):

            found += 1

            print()
            print("✅ مسابقه دارای ترکیب پیدا شد:")
            print(
                f"{home_name} vs {away_name}"
            )
            print("🆔 Match ID:", match_id)
            print()
            print(
                json.dumps(
                    lineup_data,
                    ensure_ascii=False,
                    indent=2
                )
            )

            print()
            print("-" * 80)

            if found >= 5:
                break

    except Exception:
        continue


print()
print("=" * 80)

if found == 0:

    print("❌ هیچ مسابقه‌ای با ترکیب موجود پیدا نشد.")

else:

    print(
        f"🎯 تعداد مسابقات دارای ترکیب پیدا‌شده: {found}"
    )

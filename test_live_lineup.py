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


print("🔎 در حال پیدا کردن Porto vs Manchester City...")

response = get_json(
    f"{BASE_URL}/matches",
    params={
        "sport": "football",
        "status": "scheduled",
        "limit": 200
    }
)

matches = response.get("data", [])

target = None

for match in matches:

    home = match.get("home", {}).get("name", "")
    away = match.get("away", {}).get("name", "")

    if (
        home == "FC Porto"
        and away == "Manchester City"
    ):
        target = match
        break


if not target:

    print("❌ مسابقه Porto vs Manchester City پیدا نشد.")

    print("\nمسابقات مشابه:")

    for match in matches:

        home = match.get("home", {}).get("name", "")
        away = match.get("away", {}).get("name", "")

        if (
            "Porto" in home
            or "Porto" in away
            or "Manchester City" in home
            or "Manchester City" in away
        ):
            print(
                match.get("id"),
                "|",
                home,
                "vs",
                away
            )

    raise SystemExit


match_id = target.get("id")

print()
print("✅ مسابقه پیدا شد:")
print(
    target.get("home", {}).get("name"),
    "vs",
    target.get("away", {}).get("name")
)
print("🆔 Match ID:", match_id)
print("⏰ Kickoff:", target.get("kickoff_utc"))
print("🏆 League:", target.get("league"))

print()
print("🔎 بررسی ترکیب...")
print(
    f"{BASE_URL}/stored/matches/{match_id}/lineups"
)

lineup_response = requests.get(
    f"{BASE_URL}/stored/matches/{match_id}/lineups",
    headers=HEADERS,
    timeout=30
)

print()
print("📡 HTTP Status:", lineup_response.status_code)

print()
print("📦 پاسخ خام API:")
print("=" * 80)

try:

    lineup_data = lineup_response.json()

    print(
        json.dumps(
            lineup_data,
            ensure_ascii=False,
            indent=2
        )
    )

except ValueError:

    print(lineup_response.text)

print("=" * 80)

import json
import requests


BASE_URL = "https://www.sofascore.com/api/v1"


def get_json(url):

    response = requests.get(
        url,
        timeout=30,
        headers={
            "User-Agent": "Mozilla/5.0"
        }
    )

    print("HTTP:", response.status_code)

    response.raise_for_status()

    return response.json()


print("🔎 در حال پیدا کردن مسابقه Porto vs Manchester City...")

# مسابقات لیگ قهرمانان اروپا
tournament_id = 7

# فصل جاری
season_id = 76986

url = (
    f"{BASE_URL}/sport/football/"
    f"scheduled-events/2026-09-08"
)

response = requests.get(
    url,
    timeout=30,
    headers={
        "User-Agent": "Mozilla/5.0"
    }
)

print("HTTP:", response.status_code)

response.raise_for_status()

data = response.json()

events = data.get("events", [])

target = None

for event in events:

    home = event.get("homeTeam", {}).get("name", "")
    away = event.get("awayTeam", {}).get("name", "")

    if (
        home == "FC Porto"
        and away == "Manchester City"
    ):
        target = event
        break


if not target:

    print("❌ مسابقه پیدا نشد.")

    print("\nمسابقات مربوط به Porto یا Manchester City:")

    for event in events:

        home = event.get("homeTeam", {}).get("name", "")
        away = event.get("awayTeam", {}).get("name", "")

        if (
            "Porto" in home
            or "Porto" in away
            or "Manchester City" in home
            or "Manchester City" in away
        ):

            print(
                event.get("id"),
                "|",
                home,
                "vs",
                away
            )

    raise SystemExit


match_id = target["id"]

print()
print("✅ مسابقه پیدا شد:")
print(
    target["homeTeam"]["name"],
    "vs",
    target["awayTeam"]["name"]
)

print("🆔 Event ID:", match_id)

print()
print("⏰ زمان شروع:")
print(target.get("startTimestamp"))

print()
print("=" * 80)
print("📦 اطلاعات کامل مسابقه")
print("=" * 80)

full_data_url = f"{BASE_URL}/event/{match_id}"

full_data = get_json(full_data_url)

print(
    json.dumps(
        full_data,
        ensure_ascii=False,
        indent=2
    )
)


print()
print("=" * 80)
print("👥 ترکیب")
print("=" * 80)

lineups_url = f"{BASE_URL}/event/{match_id}/lineups"

lineups = get_json(lineups_url)

print(
    json.dumps(
        lineups,
        ensure_ascii=False,
        indent=2
    )
)


print()
print("=" * 80)
print("⚽ اتفاقات مسابقه")
print("=" * 80)

incidents_url = f"{BASE_URL}/event/{match_id}/incidents"

incidents = get_json(incidents_url)

print(
    json.dumps(
        incidents,
        ensure_ascii=False,
        indent=2
    )
)


print()
print("=" * 80)
print("📊 آمار مسابقه")
print("=" * 80)

statistics_url = f"{BASE_URL}/event/{match_id}/statistics"

statistics = get_json(statistics_url)

print(
    json.dumps(
        statistics,
        ensure_ascii=False,
        indent=2
    )
)

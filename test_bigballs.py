import os
import json
import requests

API_KEY = os.getenv("BIGBALLS_API_KEY")

MATCH_ID = "f11c25d9-7e10-4cd0-b8fa-9b39827768ce"

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

    print(f"HTTP {response.status_code} | {response.url}")

    response.raise_for_status()

    return response.json()


def print_json(title, data):
    print()
    print("=" * 70)
    print(title)
    print("=" * 70)

    print(
        json.dumps(
            data,
            ensure_ascii=False,
            indent=2
        )
    )


# ============================================================
# بررسی متغیر API
# ============================================================

if not API_KEY:
    print("❌ متغیر BIGBALLS_API_KEY پیدا نشد.")
    raise SystemExit(1)


# ============================================================
# اطلاعات مسابقه
# ============================================================

match_response = get_json(
    f"{BASE_URL}/stored/matches/{MATCH_ID}"
)

print_json(
    "RAW MATCH RESPONSE",
    match_response
)


# ============================================================
# رویدادهای مسابقه
# ============================================================

events_response = get_json(
    f"{BASE_URL}/matches/{MATCH_ID}/events",
    params={
        "sport": "football"
    }
)

print_json(
    "RAW EVENTS RESPONSE",
    events_response
)


# ============================================================
# ترکیب مسابقه
# ============================================================

lineups_response = get_json(
    f"{BASE_URL}/stored/matches/{MATCH_ID}/lineups"
)

print_json(
    "RAW LINEUPS RESPONSE",
    lineups_response
)

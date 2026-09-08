import os
import json
import requests


API_KEY = os.getenv("BIGBALLS_API_KEY")

BASE_URL = "https://api.bigballsdata.com/v1"

MATCH_ID = "6df94920-30e2-49f2-b61f-db072cdcfb25"

HEADERS = {
    "Authorization": f"Bearer {API_KEY}"
}


url = f"{BASE_URL}/stored/matches/{MATCH_ID}/lineups"

print("🔎 درخواست به:")
print(url)
print()

response = requests.get(
    url,
    headers=HEADERS,
    timeout=30
)

print("📡 HTTP Status:", response.status_code)
print()

print("📦 پاسخ خام API:")
print("=" * 80)

try:
    data = response.json()

    print(
        json.dumps(
            data,
            ensure_ascii=False,
            indent=2
        )
    )

except ValueError:
    print(response.text)

print("=" * 80)

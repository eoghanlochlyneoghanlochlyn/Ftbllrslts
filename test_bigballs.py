import os
import json
import requests

API_KEY = os.environ["BIGBALLS_API_KEY"]

BASE_URL = "https://api.bigballsdata.com/v1"

HEADERS = {
    "Authorization": f"Bearer {API_KEY}"
}

TEAMS = {
    "Liverpool": "74a9c474-32e5-4b48-b9c0-b67122a1617a",
    "Arsenal": "d1b0b567-a653-43f6-8d47-d230c447650f",
    "Manchester City": "c12cf38c-1e19-4095-b367-c4ef2a184bb4",
    "Manchester United": "7aa8f8ce-df72-41bd-ac07-d8699514f9e0",
    "Chelsea": "544de6be-906a-40c9-8d32-17ed7239348f",
    "Tottenham Hotspur": "e03f803f-cd23-4db0-a79a-318f58734c7c",
    "Juventus": "1afc40a5-a6a6-41fc-85ff-95ac9c140733",
    "AC Milan": "f6d37fa6-81ad-4c70-bea5-ddde2e839331",
    "Inter Milan": "325dc8ae-18ee-437a-868e-a106b44d5383",
    "Bayern Munich": "26bff15e-9d29-490a-99bb-d925266acff0",
    "Borussia Dortmund": "aff07d0d-86d0-47e4-858a-94dd2dc96535",
    "Paris Saint-Germain": "50bd2f6b-e64f-469b-a4e2-867bfdab0476",
    "Real Madrid": "e0dcfb37-2786-4270-894a-af7c411627f9",
    "Barcelona": "b7fe0fa7-e9ec-4c48-8b15-941b258aeb5d",
    "Atlético Madrid": "9fe82092-5ef1-4101-b8e3-2ab08f41b82e",
}

print("=" * 70)
print("🔎 بررسی ساختار پاسخ مسابقات")
print("=" * 70)

for team_name, team_id in TEAMS.items():

    print(f"\n🏟 تیم: {team_name}")

    try:
        response = requests.get(
            f"{BASE_URL}/matches",
            headers=HEADERS,
            params={
                "sport": "football",
                "team_id": team_id,
                "status": "finished",
                "limit": 1,
            },
            timeout=20,
        )

    except requests.RequestException as e:
        print("خطای اتصال:")
        print(e)
        continue

    print("HTTP:", response.status_code)

    if response.status_code != 200:
        print(response.text)
        continue

    try:
        body = response.json()
    except Exception:
        print("پاسخ JSON نبود:")
        print(response.text)
        continue

    data = body.get("data", [])

    if not data:
        print("هیچ مسابقه‌ای برنگشت.")
        continue

    print("\n================ اولین مسابقه خام ================\n")
    print(json.dumps(data[0], indent=2, ensure_ascii=False))
    print("\n==================================================")

    # فقط اولین مورد را چاپ می‌کنیم
    break

print("\nپایان تست.")

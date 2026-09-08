import os
import json
import requests


API_KEY = os.getenv("BIGBALLS_API_KEY")

BASE_URL = "https://api.bigballsdata.com"

HEADERS = {
    "Authorization": f"Bearer {API_KEY}"
}


LIVERPOOL_ID = "74a9c474-32e5-4b48-b9c0-b67122a1617a"


def main():

    if not API_KEY:
        print("❌ BIGBALLS_API_KEY پیدا نشد.")
        return

    url = f"{BASE_URL}/v1/teams/{LIVERPOOL_ID}/matches"

    params = {
        "sport": "football",
        "limit": 10,
    }

    print("=" * 70)
    print("🔎 بررسی ساختار پاسخ مسابقات Liverpool")
    print("=" * 70)

    print()
    print("URL:")
    print(url)

    print()
    print("PARAMS:")
    print(params)

    response = requests.get(
        url,
        headers=HEADERS,
        params=params,
        timeout=30,
    )

    print()
    print(f"HTTP: {response.status_code}")

    print()
    print("=" * 70)
    print("📦 پاسخ خام API")
    print("=" * 70)

    try:
        data = response.json()

        print(
            json.dumps(
                data,
                indent=2,
                ensure_ascii=False
            )
        )

    except Exception:
        print(response.text)


if __name__ == "__main__":
    main()

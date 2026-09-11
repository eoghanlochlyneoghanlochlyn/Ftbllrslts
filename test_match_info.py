import requests
import json
from datetime import datetime, timezone
from zoneinfo import ZoneInfo


DATE = "20260910"

URL = f"https://www.fotmob.com/api/data/matches?date={DATE}"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/140.0.0.0 Safari/537.36"
    )
}


def main():
    print(f"Downloading matches for {DATE}...")

    response = requests.get(
        URL,
        headers=HEADERS,
        timeout=30,
    )

    print("Status code:", response.status_code)

    if response.status_code != 200:
        raise Exception("FotMob request failed")

    data = response.json()

    print("Top-level keys:")
    print(data.keys())

    print("\nFull response structure preview:\n")

    print(
        json.dumps(
            data,
            indent=2,
            ensure_ascii=False,
        )[:15000]
    )


if __name__ == "__main__":
    main()

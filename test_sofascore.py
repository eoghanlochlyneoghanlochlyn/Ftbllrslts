import requests
import json

MATCH_ID = 4653711

URL = f"https://www.fotmob.com/api/data/matchDetails?matchId={MATCH_ID}"

def main():
    print("Connecting to FotMob...")

    response = requests.get(
        URL,
        headers={
            "User-Agent": "Mozilla/5.0"
        },
        timeout=30
    )

    print("Status:", response.status_code)

    if response.status_code != 200:
        print(response.text[:1000])
        return

    data = response.json()

    print("\n=== MATCH STATUS ===")

    status = data.get("header", {}).get("status", {})

    print("Started:", status.get("started"))
    print("Finished:", status.get("finished"))
    print("Cancelled:", status.get("cancelled"))
    print("Score:", status.get("scoreStr"))
    print("Reason:", status.get("reason", {}).get("long"))

    print("\n=== MATCH TIME ===")

    halfs = status.get("halfs", {})

    print("First half started:", halfs.get("firstHalfStarted"))
    print("First half ended:", halfs.get("firstHalfEnded"))
    print("Second half started:", halfs.get("secondHalfStarted"))
    print("Second half ended:", halfs.get("secondHalfEnded"))
    print("Game ended:", halfs.get("gameEnded"))

    print("\n=== BASIC INFO ===")

    general = data.get("general", {})

    print("Match:", general.get("matchName"))
    print("Home:", general.get("homeTeam", {}).get("name"))
    print("Away:", general.get("awayTeam", {}).get("name"))

    print("\n=== RAW KEYS ===")
    print(list(data.keys()))


if __name__ == "__main__":
    main()

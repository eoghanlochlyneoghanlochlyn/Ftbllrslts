import requests

MATCH_ID = 4653711

URL = "https://www.fotmob.com/api/matchDetails"

def main():
    print("Connecting to FotMob...")

    response = requests.get(
        URL,
        params={"matchId": MATCH_ID},
        timeout=30
    )

    print("Status:", response.status_code)
    print()

    if response.status_code == 200:
        data = response.json()

        general = data.get("general", {})
        header = data.get("header", {})
        status = header.get("status", {})

        print("Match:", general.get("matchName"))
        print("Started:", status.get("started"))
        print("Finished:", status.get("finished"))
        print("Score:", status.get("scoreStr"))
        print("Reason:", status.get("reason", {}).get("long"))

    else:
        print(response.text[:1000])


if __name__ == "__main__":
    main()

from curl_cffi import requests
import json
import time

MATCH_ID = "4653711"

URL = f"https://www.fotmob.com/api/matchDetails?matchId={MATCH_ID}"


def get_match():
    response = requests.get(
        URL,
        impersonate="chrome"
    )

    print("Status:", response.status_code)

    if response.status_code != 200:
        print(response.text)
        return None

    return response.json()


def main():
    print("Connecting to FotMob...")

    data = get_match()

    if not data:
        return

    general = data.get("general", {})
    header = data.get("header", {})
    status = header.get("status", {})

    print("\n==============================")
    print("MATCH")
    print("==============================")

    print("Match:", general.get("matchName"))
    print("Match ID:", general.get("matchId"))

    print("\nTeams:")
    for team in header.get("teams", []):
        print(
            f"  {team.get('name')}: "
            f"{team.get('score')}"
        )

    print("\nStatus:")
    print("  Started:", status.get("started"))
    print("  Finished:", status.get("finished"))
    print("  Cancelled:", status.get("cancelled"))
    print("  Score:", status.get("scoreStr"))
    print("  Reason:", status.get("reason", {}).get("long"))
    print("  Ended:", status.get("halfs", {}).get("gameEnded"))

    print("\nChecking important fields...")

    if status.get("finished") is True:
        print("🏁 MATCH FINISHED")
    else:
        print("🟢 MATCH NOT FINISHED")


if __name__ == "__main__":
    main()

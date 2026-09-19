import json
import requests


LEAGUE_ID = 42
SEASON = "2026/2027"

URL = (
    f"https://www.fotmob.com/api/data/leagues"
    f"?id={LEAGUE_ID}&season={SEASON}"
)


def print_round_info(data):
    details = data.get("details", {})
    fixture_info = data.get("fixtureInfo", {})

    print("\n========== COMPETITION ==========")
    print("Name:", details.get("name"))
    print("Short name:", details.get("shortName"))
    print("Country:", details.get("country"))

    print("\n========== ACTIVE ROUND ==========")
    active_round = fixture_info.get("activeRound")
    print(json.dumps(active_round, ensure_ascii=False, indent=2))

    print("\n========== ALL ROUNDS ==========")
    rounds = fixture_info.get("rounds")

    if isinstance(rounds, list):
        print("Round count:", len(rounds))

        for index, item in enumerate(rounds, 1):
            print(f"\n--- Round {index} ---")
            print(json.dumps(item, ensure_ascii=False, indent=2))
    else:
        print("No rounds list found.")

    print("\n========== PLAYOFF ==========")
    playoff = fixture_info.get("playoff")

    if playoff is None:
        print("playoff = None")
    else:
        print(json.dumps(playoff, ensure_ascii=False, indent=2))

    print("\n========== FIXTURE ROUND DATA ==========")

    fixtures = data.get("fixtures", [])

    if isinstance(fixtures, list):
        print("Fixture count:", len(fixtures))

        found = 0

        for index, fixture in enumerate(fixtures):
            if not isinstance(fixture, dict):
                continue

            round_value = fixture.get("round")
            round_name = fixture.get("roundName")

            if round_value is not None or round_name is not None:
                found += 1

                print(f"\n--- Fixture {index + 1} ---")
                print("Round:", round_value)
                print("Round name:", round_name)

                if found >= 30:
                    print("\nOnly first 30 fixtures with round information shown.")
                    break
    else:
        print("No fixtures list found.")


def main():
    print("Fetching:")
    print(URL)

    response = requests.get(
        URL,
        timeout=30,
        headers={
            "User-Agent": "Mozilla/5.0"
        },
    )

    print("\nHTTP status:", response.status_code)

    response.raise_for_status()

    data = response.json()

    print_round_info(data)


if __name__ == "__main__":
    main()

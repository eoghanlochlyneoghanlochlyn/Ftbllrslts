import json
import requests


LEAGUE_ID = 42
SEASON = "2026/2027"

URL = (
    f"https://www.fotmob.com/api/data/leagues"
    f"?id={LEAGUE_ID}&season={SEASON}"
)


def find_key(obj, target_key, path="root"):
    if isinstance(obj, dict):
        for key, value in obj.items():
            current_path = f"{path}.{key}"

            if key == target_key:
                yield current_path, value

            yield from find_key(value, target_key, current_path)

    elif isinstance(obj, list):
        for index, value in enumerate(obj):
            current_path = f"{path}[{index}]"
            yield from find_key(value, target_key, current_path)


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

    print("\n========== ROOT KEYS ==========")
    print(list(data.keys()))

    print("\n========== SEARCH: fixtureInfo ==========")

    fixture_info_results = list(find_key(data, "fixtureInfo"))

    print("Found:", len(fixture_info_results))

    for index, (path, value) in enumerate(fixture_info_results, 1):
        print(f"\n--- fixtureInfo #{index} ---")
        print("Path:", path)

        if isinstance(value, dict):
            print("Keys:", list(value.keys()))
        else:
            print("Type:", type(value).__name__)

        print(json.dumps(value, ensure_ascii=False, indent=2)[:15000])

    print("\n========== SEARCH: rounds ==========")

    rounds_results = list(find_key(data, "rounds"))

    print("Found:", len(rounds_results))

    for index, (path, value) in enumerate(rounds_results, 1):
        print(f"\n--- rounds #{index} ---")
        print("Path:", path)

        if isinstance(value, list):
            print("Count:", len(value))

            for round_index, item in enumerate(value, 1):
                print(f"\nRound {round_index}:")
                print(json.dumps(item, ensure_ascii=False, indent=2))
        else:
            print("Type:", type(value).__name__)
            print(json.dumps(value, ensure_ascii=False, indent=2))

    print("\n========== SEARCH: activeRound ==========")

    active_round_results = list(find_key(data, "activeRound"))

    print("Found:", len(active_round_results))

    for index, (path, value) in enumerate(active_round_results, 1):
        print(f"\n--- activeRound #{index} ---")
        print("Path:", path)
        print(json.dumps(value, ensure_ascii=False, indent=2))

    print("\n========== SEARCH: playoff ==========")

    playoff_results = list(find_key(data, "playoff"))

    print("Found:", len(playoff_results))

    for index, (path, value) in enumerate(playoff_results, 1):
        print(f"\n--- playoff #{index} ---")
        print("Path:", path)
        print(json.dumps(value, ensure_ascii=False, indent=2)[:10000])


if __name__ == "__main__":
    main()

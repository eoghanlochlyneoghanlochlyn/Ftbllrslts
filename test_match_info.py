import json
import re
import requests


MATCH_URL = "https://www.fotmob.com/matches/coventry-city-vs-nottingham-forest/2y16ft#5795463"


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


def extract_next_data(html):
    match = re.search(
        r'<script id="__NEXT_DATA__" type="application/json">(.*?)</script>',
        html,
        re.DOTALL,
    )

    if not match:
        raise RuntimeError("__NEXT_DATA__ was not found.")

    return json.loads(match.group(1))


def main():
    print("Match URL:")
    print(MATCH_URL)

    response = requests.get(
        MATCH_URL,
        timeout=45,
        headers={
            "User-Agent": "Mozilla/5.0",
        },
    )

    print("\nHTTP status:", response.status_code)
    print("Response length:", len(response.text))

    response.raise_for_status()

    data = extract_next_data(response.text)

    # ---------------------------------------------------------
    # Find Tournament objects
    # ---------------------------------------------------------

    tournament_results = list(find_key(data, "Tournament"))

    print("\nTournament objects found:", len(tournament_results))

    if not tournament_results:
        print("\nTournament information was not found.")
        return

    # Usually the useful one is inside:
    # root.props.pageProps.content.matchFacts.infoBox.Tournament

    for path, tournament in tournament_results:

        if not isinstance(tournament, dict):
            continue

        if "leagueName" not in tournament:
            continue

        print("\n========== RESULT ==========")

        print("Path:", path)

        print("Competition:", tournament.get("leagueName"))
        print("Round:", tournament.get("round"))
        print("Round name:", tournament.get("roundName"))

        # -----------------------------------------------------
        # legInfo
        # -----------------------------------------------------

        info_box_results = list(find_key(data, "infoBox"))

        leg_info = None

        for info_path, info_box in info_box_results:
            if not isinstance(info_box, dict):
                continue

            if info_box.get("Tournament") is tournament:
                leg_info = info_box.get("legInfo")
                break

        print("Leg info:", leg_info)

        print("\n========== RAW TOURNAMENT ==========")

        print(
            json.dumps(
                tournament,
                ensure_ascii=False,
                indent=2,
            )
        )

        break


if __name__ == "__main__":
    main()

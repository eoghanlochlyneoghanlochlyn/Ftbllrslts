import json
import re
import requests


MATCH_ID = "6106264"

URL = f"https://www.fotmob.com/match/{MATCH_ID}"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/140.0.0.0 Safari/537.36"
    )
}


def get_next_data(html):
    match = re.search(
        r'<script id="__NEXT_DATA__" type="application/json">(.*?)</script>',
        html,
        re.DOTALL,
    )

    if not match:
        return None

    return json.loads(match.group(1))


def print_player(player, number):
    name = player.get("name", "Unknown")
    shirt_number = player.get("shirtNumber")
    position_id = player.get("positionId")
    rating = None

    performance = player.get("performance")

    if isinstance(performance, dict):
        rating = performance.get("rating")

    print(
        f"{number}. {name}"
        f" | #{shirt_number}"
        f" | positionId={position_id}"
        f" | rating={rating}"
    )


def print_team(team, label):
    print()
    print("=" * 60)
    print(label)
    print("=" * 60)

    print(f"Team: {team.get('name')}")
    print(f"Formation: {team.get('formation')}")

    starters = team.get("starters", [])
    substitutes = team.get("substitutes", [])

    print()
    print(f"STARTERS ({len(starters)}):")

    for index, player in enumerate(starters, start=1):
        print_player(player, index)

    print()
    print(f"SUBSTITUTES ({len(substitutes)}):")

    for index, player in enumerate(substitutes, start=1):
        print_player(player, index)


def main():
    print("FOTMOB LINEUP TEST")
    print("=" * 60)

    print(f"Match ID: {MATCH_ID}")
    print(f"URL: {URL}")
    print()

    try:
        response = requests.get(
            URL,
            headers=HEADERS,
            timeout=30,
        )
    except Exception as e:
        print("REQUEST ERROR")
        print(e)
        return

    print(f"HTTP STATUS: {response.status_code}")
    print(f"HTML LENGTH: {len(response.text)}")

    if response.status_code != 200:
        print()
        print("FotMob request failed.")
        return

    data = get_next_data(response.text)

    if not data:
        print()
        print("NEXT_DATA NOT FOUND")
        return

    print("NEXT_DATA JSON OK")

    try:
        page_props = data["props"]["pageProps"]
    except (KeyError, TypeError):
        print()
        print("PAGE PROPS NOT FOUND")
        return

    general = page_props.get("general", {})
    header = page_props.get("header", {})
    content = page_props.get("content", {})

    print()
    print("=" * 60)
    print("MATCH INFORMATION")
    print("=" * 60)

    print(f"Match ID: {general.get('matchId')}")
    print(f"Match name: {general.get('matchName')}")
    print(f"League: {general.get('leagueName')}")
    print(f"Time: {general.get('matchTime')}")
    print(f"Started: {general.get('started')}")
    print(f"Finished: {general.get('finished')}")

    lineup = content.get("lineup")

    print()
    print("=" * 60)
    print("LINEUP INFORMATION")
    print("=" * 60)

    if not lineup:
        print("LINEUP NOT AVAILABLE")
        return

    print("Lineup available: YES")
    print(f"Lineup ID: {lineup.get('matchId')}")
    print(f"Lineup type: {lineup.get('lineupType')}")
    print(f"Source: {lineup.get('source')}")

    available_filters = lineup.get("availableFilters")

    if available_filters:
        print(f"Available filters: {available_filters}")

    home_team = lineup.get("homeTeam")
    away_team = lineup.get("awayTeam")

    if not home_team:
        print()
        print("HOME TEAM DATA NOT FOUND")
    else:
        print_team(home_team, "HOME TEAM")

    if not away_team:
        print()
        print("AWAY TEAM DATA NOT FOUND")
    else:
        print_team(away_team, "AWAY TEAM")

    print()
    print("=" * 60)
    print("TEST FINISHED")
    print("=" * 60)


if __name__ == "__main__":
    main()

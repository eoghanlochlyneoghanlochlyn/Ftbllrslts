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
        re.DOTALL
    )

    if not match:
        return None

    return json.loads(match.group(1))


def print_team(team, label):
    print()
    print("=" * 60)
    print(label)
    print("=" * 60)

    print(f"Team: {team.get('name')}")
    print(f"Formation: {team.get('formation')}")

    starters = team.get("starters", [])
    subs = team.get("subs", [])

    print()
    print(f"STARTERS ({len(starters)}):")

    for index, player in enumerate(starters, 1):
        name = player.get("name")
        number = player.get("shirtNumber")
        position_id = player.get("positionId")
        rating = player.get("performance", {}).get("rating")

        print(
            f"{index}. {name} | "
            f"#{number} | "
            f"positionId={position_id} | "
            f"rating={rating}"
        )

    print()
    print(f"SUBSTITUTES ({len(subs)}):")

    for index, player in enumerate(subs, 1):
        name = player.get("name")
        number = player.get("shirtNumber")
        position_id = player.get("positionId")
        rating = player.get("performance", {}).get("rating")

        print(
            f"{index}. {name} | "
            f"#{number} | "
            f"positionId={position_id} | "
            f"rating={rating}"
        )


def main():
    print("FOTMOB LINEUP TEST")
    print("=" * 60)

    print(f"Match ID: {MATCH_ID}")
    print("Requesting FotMob...")

    response = requests.get(
        URL,
        headers=HEADERS,
        timeout=30
    )

    print(f"HTTP STATUS: {response.status_code}")

    response.raise_for_status()

    data = get_next_data(response.text)

    if data is None:
        print("ERROR: __NEXT_DATA__ NOT FOUND")
        return

    page_props = data.get("props", {}).get("pageProps", {})
    general = page_props.get("general", {})
    content = page_props.get("content", {})
    lineup = content.get("lineup")

    print("NEXT_DATA JSON OK")

    print()
    print(f"Match: {general.get('matchName')}")
    print(f"Started: {general.get('started')}")
    print(f"Finished: {general.get('finished')}")

    if not lineup:
        print()
        print("LINEUP NOT AVAILABLE")
        return

    print()
    print(f"Lineup type: {lineup.get('lineupType')}")
    print(f"Source: {lineup.get('source')}")

    home_team = lineup.get("homeTeam", {})
    away_team = lineup.get("awayTeam", {})

    print_team(home_team, "HOME TEAM")
    print_team(away_team, "AWAY TEAM")

    print()
    print("=" * 60)
    print("TEST FINISHED")
    print("=" * 60)


if __name__ == "__main__":
    main()

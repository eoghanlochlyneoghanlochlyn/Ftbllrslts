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
    pattern = r'<script id="__NEXT_DATA__" type="application/json">(.*?)</script>'

    match = re.search(pattern, html, re.DOTALL)

    if not match:
        return None

    return json.loads(match.group(1))


def print_player(player, index, category):
    print()
    print("-" * 70)
    print(f"{category} #{index}")
    print("-" * 70)

    if not isinstance(player, dict):
        print("Player data is not a dictionary:")
        print(player)
        return

    print("KEYS:")
    for key in player.keys():
        print(f"  - {key}")

    print()
    print("VALUES:")

    for key, value in player.items():

        if isinstance(value, (dict, list)):
            print(f"  {key}: {json.dumps(value, ensure_ascii=False)}")
        else:
            print(f"  {key}: {value}")


def print_team_lineup(team, team_name):
    print()
    print("=" * 80)
    print(f"{team_name}")
    print("=" * 80)

    if not isinstance(team, dict):
        print("Team data is not a dictionary.")
        print(team)
        return

    print(f"Team name: {team.get('name')}")
    print(f"Team ID: {team.get('id')}")
    print(f"Formation: {team.get('formation')}")

    starters = team.get("starters", [])
    substitutes = team.get("subs", [])

    print()
    print(f"STARTERS COUNT: {len(starters)}")
    print(f"SUBS COUNT: {len(substitutes)}")

    print()
    print("STARTERS STRUCTURE")

    if not starters:
        print("No starters found.")
    else:
        for index, player in enumerate(starters, 1):
            print_player(player, index, "STARTER")

    print()
    print("SUBSTITUTES STRUCTURE")

    if not substitutes:
        print("No substitutes found.")
    else:
        for index, player in enumerate(substitutes, 1):
            print_player(player, index, "SUBSTITUTE")


def main():
    print("=" * 80)
    print("FOTMOB MATCH INFO TEST")
    print("=" * 80)

    print()
    print(f"Match ID: {MATCH_ID}")
    print(f"URL: {URL}")

    print()
    print("Requesting FotMob...")

    response = requests.get(
        URL,
        headers=HEADERS,
        timeout=30
    )

    print(f"HTTP STATUS: {response.status_code}")
    print(f"HTML LENGTH: {len(response.text)}")

    response.raise_for_status()

    print()
    print("Extracting __NEXT_DATA__...")

    data = get_next_data(response.text)

    if data is None:
        print("ERROR: __NEXT_DATA__ NOT FOUND")
        return

    print("NEXT_DATA JSON OK")

    page_props = data.get("props", {}).get("pageProps", {})

    print()
    print("PAGE PROPS:")
    print(list(page_props.keys()))

    general = page_props.get("general", {})
    header = page_props.get("header", {})
    content = page_props.get("content", {})

    print()
    print("=" * 80)
    print("MATCH INFORMATION")
    print("=" * 80)

    print(f"Match ID: {general.get('matchId')}")
    print(f"Match: {general.get('matchName')}")
    print(f"League: {general.get('leagueName')}")
    print(f"Started: {general.get('started')}")
    print(f"Finished: {general.get('finished')}")

    lineup = content.get("lineup")

    print()
    print("=" * 80)
    print("LINEUP INFORMATION")
    print("=" * 80)

    if not lineup:
        print("LINEUP NOT AVAILABLE")
        print()
        print("TEST FINISHED")
        return

    print(f"Lineup type: {lineup.get('lineupType')}")
    print(f"Source: {lineup.get('source')}")

    print()
    print("Available filters:")
    print(lineup.get("availableFilters"))

    home_team = lineup.get("homeTeam", {})
    away_team = lineup.get("awayTeam", {})

    print_team_lineup(
        home_team,
        "HOME TEAM"
    )

    print_team_lineup(
        away_team,
        "AWAY TEAM"
    )

    print()
    print("=" * 80)
    print("RAW LINEUP TOP-LEVEL KEYS")
    print("=" * 80)

    print(list(lineup.keys()))

    print()
    print("=" * 80)
    print("HTML KEYWORD COUNTS")
    print("=" * 80)

    html = response.text

    keywords = [
        "lineupType",
        "starters",
        "substitutes",
        "bench",
        "predicted",
        "standard",
    ]

    for keyword in keywords:
        print(
            f"{keyword}: "
            f"{html.count(keyword)}"
        )

    print()
    print("=" * 80)
    print("TEST FINISHED")
    print("=" * 80)


if __name__ == "__main__":
    main()

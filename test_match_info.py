import json
import re
import requests
import time


MATCH_IDS = [
    6106400,
    6106237,
    6099342,
    6106404,
    6106242,
    5802923,
    5749667,
    5868047,
    5881154,
    5749665,
    5852780,
    5161884,
    5898847,
    5904728,
    5961833,
    5970091,
    4667793,
    4653714,
    4653718,
    4947828,
    4947832,
]


HEADERS = {
    "User-Agent": "Mozilla/5.0"
}


positions = {}


print("TEST STARTED")


for match_id in MATCH_IDS:

    print(f"Checking match {match_id}...")

    try:
        url = f"https://www.fotmob.com/match/{match_id}"

        response = requests.get(
            url,
            headers=HEADERS,
            timeout=30
        )

        if response.status_code != 200:
            print(f"HTTP ERROR: {response.status_code}")
            continue

        match = re.search(
            r'<script id="__NEXT_DATA__" type="application/json">(.*?)</script>',
            response.text,
            re.DOTALL
        )

        if not match:
            print("NEXT_DATA NOT FOUND")
            continue

        data = json.loads(match.group(1))

        page_props = data["props"]["pageProps"]
        content = page_props["content"]

        lineup = content.get("lineup")

        if not lineup:
            print("NO LINEUP")
            continue

        for side in ["homeTeam", "awayTeam"]:

            team = lineup.get(side)

            if not team:
                continue

            team_name = team.get("name")
            formation = team.get("formation")

            for player in team.get("starters", []):

                position_id = player.get("positionId")

                if position_id is None:
                    continue

                if position_id not in positions:
                    positions[position_id] = []

                horizontal = player.get("horizontalLayout")
                vertical = player.get("verticalLayout")

                positions[position_id].append({
                    "player": player.get("name"),
                    "team": team_name,
                    "formation": formation,
                    "horizontal": horizontal,
                    "vertical": vertical
                })

        time.sleep(1)

    except Exception as error:
        print("ERROR:", repr(error))


print()
print("=" * 100)
print("POSITION ID ANALYSIS")
print("=" * 100)


for position_id in sorted(positions):

    print()
    print(f"POSITION ID: {position_id}")
    print("-" * 100)

    for item in positions[position_id]:

        print(
            f'{item["player"]} | '
            f'{item["team"]} | '
            f'Formation={item["formation"]} | '
            f'H={item["horizontal"]} | '
            f'V={item["vertical"]}'
        )


print()
print("=" * 100)
print("TOTAL UNIQUE POSITION IDS:", len(positions))
print("=" * 100)

print("TEST FINISHED")

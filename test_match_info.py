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


unique_ids = set()


print("TEST STARTED")


for match_id in MATCH_IDS:

    print()
    print("=" * 90)
    print(f"MATCH {match_id}")
    print("=" * 90)

    url = f"https://www.fotmob.com/match/{match_id}"

    try:
        response = requests.get(
            url,
            headers=HEADERS,
            timeout=30
        )

        print("HTTP:", response.status_code)

        if response.status_code != 200:
            print("REQUEST FAILED")
            continue

        html = response.text

        next_data_match = re.search(
            r'<script id="__NEXT_DATA__" type="application/json">(.*?)</script>',
            html,
            re.DOTALL
        )

        if not next_data_match:
            print("NEXT_DATA NOT FOUND")
            continue

        data = json.loads(next_data_match.group(1))

        page_props = data["props"]["pageProps"]

        content = page_props["content"]

        match_name = page_props.get("general", {}).get(
            "matchName",
            f"Match {match_id}"
        )

        lineup = content.get("lineup")

        if not lineup:
            print("NO LINEUP")
            continue

        print("Match:", match_name)
        print("Lineup type:", lineup.get("lineupType"))

        for side in ["homeTeam", "awayTeam"]:

            team = lineup.get(side)

            if not team:
                continue

            print()
            print("-" * 70)
            print(team.get("name"))
            print("Formation:", team.get("formation"))
            print("-" * 70)

            starters = team.get("starters", [])

            if not starters:
                print("NO STARTERS")
                continue

            for player in starters:

                position_id = player.get("positionId")

                if position_id is not None:
                    unique_ids.add(position_id)

                print(
                    f"{str(position_id):>3} | "
                    f"usual={str(player.get('usualPlayingPositionId')):>3} | "
                    f"{player.get('name', 'Unknown'):<25} | "
                    f"H={player.get('horizontalLayout')} | "
                    f"V={player.get('verticalLayout')}"
                )

        time.sleep(1)

    except Exception as error:
        print("ERROR:", repr(error))


print()
print("=" * 90)
print("UNIQUE POSITION IDS")
print("=" * 90)

for position_id in sorted(unique_ids):
    print(position_id)


print()
print("TOTAL UNIQUE POSITION IDS:", len(unique_ids))
print("TEST FINISHED")

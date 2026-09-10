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

for match_id in MATCH_IDS:

    print("\n" + "=" * 90)
    print(f"MATCH {match_id}")
    print("=" * 90)

    url = f"https://www.fotmob.com/match/{match_id}"

    try:
        r = requests.get(url, headers=HEADERS, timeout=30)

        if r.status_code != 200:
            print("HTTP:", r.status_code)
            continue

        m = re.search(
            r'<script id="__NEXT_DATA__" type="application/json">(.*?)</script>',
            r.text,
            re.DOTALL
        )

        if not m:
            print("NEXT_DATA NOT FOUND")
            continue

        data = json.loads(m.group(1))

        content = data["props"]["pageProps"]["content"]

        print("Match:", content["seo"]["title"])

        lineup = content.get("lineup")

        if not lineup:
            print("NO LINEUP")
            continue

        for side in ["homeTeam", "awayTeam"]:

            team = lineup.get(side)

            if not team:
                continue

            print("\n")
            print("-" * 70)
            print(team["name"])
            print("Formation:", team.get("formation"))
            print("-" * 70)

            for p in team.get("starters", []):

                pid = p.get("positionId")
                unique_ids.add(pid)

                print(
                    f"{pid:>3} | "
                    f"usual={p.get('usualPlayingPositionId')} | "
                    f"{p['name']:<25} | "
                    f"H={p.get('horizontalLayout')} | "
                    f"V={p.get('verticalLayout')}"
                )

        time.sleep(1)

    except Exception as e:
        print(e)

print("\n")
print("=" * 90)
print("UNIQUE POSITION IDS")
print("=" * 90)

print(sorted(unique_ids))

import json
import re
import requests

MATCH_ID = "6106264"

URL = f"https://www.fotmob.com/match/{MATCH_ID}"

HEADERS = {
    "User-Agent": "Mozilla/5.0"
}


print("TEST STARTED")

response = requests.get(URL, headers=HEADERS, timeout=30)

print("HTTP:", response.status_code)

html = response.text

match = re.search(
    r'<script id="__NEXT_DATA__" type="application/json">(.*?)</script>',
    html,
    re.DOTALL
)

if not match:
    print("NEXT_DATA NOT FOUND")
    raise SystemExit(1)

data = json.loads(match.group(1))

lineup = data["props"]["pageProps"]["content"]["lineup"]

print("LINEUP:", lineup.get("lineupType"))
print()

for team_key in ["homeTeam", "awayTeam"]:

    team = lineup.get(team_key, {})

    print("=" * 50)
    print(team.get("name"))
    print("=" * 50)

    for player in team.get("starters", []):

        print(
            f'{player.get("name")} | '
            f'positionId={player.get("positionId")} | '
            f'keys={list(player.keys())}'
        )

print()
print("TEST FINISHED")

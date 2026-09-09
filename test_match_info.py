import json
import re
import requests


MATCH_ID = "6106264"
URL = f"https://www.fotmob.com/match/{MATCH_ID}"


print("FOTMOB POSITION ID TEST")
print(f"Match ID: {MATCH_ID}")
print("Requesting FotMob...")

response = requests.get(
    URL,
    headers={
        "User-Agent": "Mozilla/5.0"
    },
    timeout=30
)

print(f"HTTP STATUS: {response.status_code}")

if response.status_code != 200:
    print("ERROR: Could not load FotMob page.")
    raise SystemExit(1)


html = response.text

match = re.search(
    r'<script id="__NEXT_DATA__" type="application/json">(.*?)</script>',
    html,
    re.DOTALL
)

if not match:
    print("ERROR: __NEXT_DATA__ not found.")
    raise SystemExit(1)


data = json.loads(match.group(1))

print("NEXT_DATA JSON OK")
print()


# --------------------------------------------------
# پیدا کردن lineup
# --------------------------------------------------

content = data.get("props", {}).get("pageProps", {}).get("content", {})
lineup = content.get("lineup", {})

if not lineup:
    print("ERROR: lineup not found.")
    raise SystemExit(1)


print("LINEUP FOUND")
print()


# --------------------------------------------------
# بررسی positionId بازیکنان اصلی
# --------------------------------------------------

for side in ["home", "away"]:

    team_data = lineup.get(side, {})

    team_name = team_data.get("teamName", "Unknown")

    print(f"{side.upper()} TEAM: {team_name}")

    starters = team_data.get("starters", [])

    for player in starters:

        name = player.get("name")
        position_id = player.get("positionId")

        print(
            f"{name} -> positionId={position_id}"
        )

    print()


# --------------------------------------------------
# جستجوی اطلاعات مربوط به positionId داخل کل JSON
# --------------------------------------------------

position_ids = set()

for side in ["home", "away"]:

    team_data = lineup.get(side, {})

    for player in team_data.get("starters", []):

        position_id = player.get("positionId")

        if position_id is not None:
            position_ids.add(position_id)


print("POSITION IDs FOUND:")
print(sorted(position_ids))
print()


print("SEARCHING FOR POSITION DEFINITIONS...")
print()


# --------------------------------------------------
# جستجوی هر positionId در ساختار JSON
# --------------------------------------------------

def search_position_ids(obj, path="root"):

    if isinstance(obj, dict):

        for key, value in obj.items():

            # اگر کلید احتمالاً مربوط به position باشد
            key_lower = str(key).lower()

            if (
                "position" in key_lower
                or "role" in key_lower
                or "formation" in key_lower
            ):
                text = str(value)

                found = [
                    pid for pid in position_ids
                    if str(pid) in text
                ]

                if found:
                    print(
                        f"[FOUND] {path}.{key}"
                    )
                    print(
                        f"  position IDs: {found}"
                    )
                    print(
                        f"  value: {text[:500]}"
                    )
                    print()

            search_position_ids(
                value,
                f"{path}.{key}"
            )

    elif isinstance(obj, list):

        for index, value in enumerate(obj):

            search_position_ids(
                value,
                f"{path}[{index}]"
            )


search_position_ids(data)


print("TEST FINISHED")

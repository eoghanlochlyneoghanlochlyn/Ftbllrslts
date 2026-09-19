import json
import re
import requests

MATCH_URLS = [
"https://www.fotmob.com/matches/athletic-club-vs-deportivo-alaves/2qet5l#5868071",
"https://www.fotmob.com/matches/inter-vs-roma/2hby2d#5749681",
"https://www.fotmob.com/matches/borussia-dortmund-vs-vfb-stuttgart/3bs0n0#5881177",
"https://www.fotmob.com/matches/angers-vs-troyes/2se1ur#5802937",
"https://www.fotmob.com/matches/al-ahli-vs-mamelodi-sundowns-fc/euc04#6072167",
"https://www.fotmob.com/matches/barcelona-vs-eintracht-frankfurt/2ta1eo#4947146",
"https://www.fotmob.com/matches/real-madrid-vs-benfica/2sumx7#5161859",
"https://www.fotmob.com/matches/real-madrid-vs-benfica/2sumx7#5161860",
"https://www.fotmob.com/matches/manchester-city-vs-real-madrid/2ey0nu#5205731",
"https://www.fotmob.com/matches/manchester-city-vs-real-madrid/2ey0nu#5205732",
"https://www.fotmob.com/matches/real-madrid-vs-bayern-munchen/2tes97#5205791",
"https://www.fotmob.com/matches/real-madrid-vs-bayern-munchen/2tes97#5205792",
"https://www.fotmob.com/matches/bayern-munchen-vs-paris-saint-germain/376tlg#5205811",
"https://www.fotmob.com/matches/bayern-munchen-vs-paris-saint-germain/376tlg#5205812",
"https://www.fotmob.com/matches/arsenal-vs-paris-saint-germain/377nyb#5205834",
]

def find_tournament(obj):
if isinstance(obj, dict):
if (
"leagueName" in obj
and ("round" in obj or "roundName" in obj)
):
return obj

```
    for value in obj.values():
        result = find_tournament(value)

        if result is not None:
            return result

elif isinstance(obj, list):
    for value in obj:
        result = find_tournament(value)

        if result is not None:
            return result

return None
```

def find_info_box(obj):
if isinstance(obj, dict):
if "Tournament" in obj and isinstance(obj["Tournament"], dict):
return obj

```
    for value in obj.values():
        result = find_info_box(value)

        if result is not None:
            return result

elif isinstance(obj, list):
    for value in obj:
        result = find_info_box(value)

        if result is not None:
            return result

return None
```

def extract_next_data(html):
match = re.search(
r'<script id="__NEXT_DATA__" type="application/json">(.*?)</script>',
html,
re.DOTALL,
)

```
if not match:
    raise RuntimeError("__NEXT_DATA__ was not found.")

return json.loads(match.group(1))
```

def main():
session = requests.Session()

```
session.headers.update(
    {
        "User-Agent": "Mozilla/5.0",
    }
)

print()
print("=" * 90)
print("FotMob Competition / Round Summary")
print("=" * 90)
print()

for index, url in enumerate(MATCH_URLS, start=1):
    try:
        response = session.get(
            url,
            timeout=45,
        )

        response.raise_for_status()

        data = extract_next_data(response.text)

        tournament = find_tournament(data)

        if tournament is None:
            print(
                f"{index:02d}. ERROR | Tournament not found | {url}"
            )
            continue

        competition = tournament.get("leagueName")
        round_value = (
            tournament.get("roundName")
            or tournament.get("round")
        )

        info_box = find_info_box(data)

        leg_info = None

        if info_box is not None:
            leg_info = info_box.get("legInfo")

        leg_text = ""

        if isinstance(leg_info, dict):
            localized = leg_info.get("localizedString")

            if isinstance(localized, dict):
                leg_text = localized.get("fallback") or ""

            if not leg_text:
                leg_text = str(
                    leg_info.get("leg")
                    or leg_info.get("legNumber")
                    or ""
                )

        print(
            f"{index:02d}. "
            f"{competition} | "
            f"Round: {round_value} | "
            f"Leg: {leg_text or '-'}"
        )

    except Exception as e:
        print(
            f"{index:02d}. ERROR | "
            f"{type(e).__name__}: {e}"
        )

print()
print("=" * 90)
print("Test finished.")
print("=" * 90)
```

if **name** == "**main**":
main()

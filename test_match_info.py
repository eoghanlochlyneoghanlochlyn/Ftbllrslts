import json
import re
import requests

MATCH_URLS = [
"https://www.fotmob.com/matches/real-madrid-vs-benfica/2sumx7#5161859",
"https://www.fotmob.com/matches/real-madrid-vs-benfica/2sumx7#5161860",
"https://www.fotmob.com/matches/manchester-city-vs-real-madrid/2ey0nu#5205731",
"https://www.fotmob.com/matches/manchester-city-vs-real-madrid/2ey0nu#5205732",
"https://www.fotmob.com/matches/real-madrid-vs-bayern-munchen/2tes97#5205791",
"https://www.fotmob.com/matches/real-madrid-vs-bayern-munchen/2tes97#5205792",
"https://www.fotmob.com/matches/bayern-munchen-vs-paris-saint-germain/376tlg#5205811",
"https://www.fotmob.com/matches/bayern-munchen-vs-paris-saint-germain/376tlg#5205812",
]

def get_next_data(html):
pattern = r'<script id="__NEXT_DATA__" type="application/json">(.*?)</script>'
match = re.search(pattern, html, re.DOTALL)

```
if not match:
    return None

return json.loads(match.group(1))
```

def find_info_box(obj):
if isinstance(obj, dict):
match_facts = obj.get("matchFacts")

```
    if isinstance(match_facts, dict):
        info_box = match_facts.get("infoBox")

        if isinstance(info_box, dict):
            return info_box

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

def print_matching_keys(obj, path="root"):
if isinstance(obj, dict):
for key, value in obj.items():
key_text = str(key).lower()

```
        if (
            "aggregate" in key_text
            or "leg" in key_text
            or "penalty" in key_text
        ):
            print()
            print("PATH:", path + "." + str(key))
            print(json.dumps(value, ensure_ascii=False, indent=2))

        if isinstance(value, (dict, list)):
            print_matching_keys(
                value,
                path + "." + str(key),
            )

elif isinstance(obj, list):
    for index, value in enumerate(obj):
        if isinstance(value, (dict, list)):
            print_matching_keys(
                value,
                path + "[" + str(index) + "]",
            )
```

def main():
session = requests.Session()

```
session.headers.update(
    {
        "User-Agent": "Mozilla/5.0",
        "Accept-Language": "en-US,en;q=0.9",
    }
)

for index, url in enumerate(MATCH_URLS, start=1):
    print()
    print("=" * 100)
    print("MATCH", index)
    print(url)
    print("=" * 100)

    try:
        response = session.get(
            url,
            timeout=45,
        )

        response.raise_for_status()

        data = get_next_data(response.text)

        if data is None:
            print("ERROR: __NEXT_DATA__ not found")
            continue

        info_box = find_info_box(data)

        if info_box is None:
            print("ERROR: infoBox not found")
            continue

        tournament = info_box.get("Tournament")

        print()
        print("TOURNAMENT:")
        print(
            json.dumps(
                tournament,
                ensure_ascii=False,
                indent=2,
            )
        )

        print()
        print("LEG INFO:")
        print(
            json.dumps(
                info_box.get("legInfo"),
                ensure_ascii=False,
                indent=2,
            )
        )

        print()
        print("AGGREGATE / LEG / PENALTY:")
        print_matching_keys(info_box)

    except Exception as error:
        print(
            "ERROR:",
            type(error).__name__,
            str(error),
        )
```

if **name** == "**main**":
main()

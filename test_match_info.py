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
match = re.search(
r'<script id="__NEXT_DATA__" type="application/json">(.*?)</script>',
html,
re.DOTALL,
)

```
if not match:
    return None

return json.loads(match.group(1))
```

def find_info_box(obj):
if isinstance(obj, dict):

```
    if "matchFacts" in obj and isinstance(obj["matchFacts"], dict):
        match_facts = obj["matchFacts"]

        if "infoBox" in match_facts and isinstance(
            match_facts["infoBox"],
            dict,
        ):
            return match_facts["infoBox"]

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

def print_relevant_data(obj, path="root"):
if isinstance(obj, dict):

```
    for key, value in obj.items():

        key_lower = str(key).lower()

        if any(
            word in key_lower
            for word in (
                "aggregate",
                "leg",
                "score",
                "penalty",
            )
        ):
            print()
            print(f"PATH: {path}.{key}")
            print(json.dumps(value, ensure_ascii=False, indent=2))

        if isinstance(value, (dict, list)):
            print_relevant_data(
                value,
                f"{path}.{key}",
            )

elif isinstance(obj, list):

    for index, value in enumerate(obj):
        if isinstance(value, (dict, list)):
            print_relevant_data(
                value,
                f"{path}[{index}]",
            )
```

def main():
session = requests.Session()

```
session.headers.update(
    {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 "
            "(KHTML, like Gecko) "
            "Chrome/140.0.0.0 Safari/537.36"
        ),
        "Accept-Language": "en-US,en;q=0.9",
    }
)

for index, url in enumerate(MATCH_URLS, start=1):

    print()
    print("=" * 100)
    print(f"MATCH {index}")
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
        print("RELEVANT AGGREGATE / LEG / SCORE / PENALTY DATA:")
        print_relevant_data(info_box)

    except Exception as e:
        print(
            f"ERROR: {type(e).__name__}: {e}"
        )
```

if **name** == "**main**":
main()

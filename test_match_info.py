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
        re.DOTALL,
    )

    if not match:
        return None

    return json.loads(match.group(1))


def inspect_structure(obj, path=""):
    if isinstance(obj, dict):
        for key, value in obj.items():
            current_path = f"{path}.{key}" if path else key

            if isinstance(value, list):
                print(
                    f"LIST  | {current_path} | "
                    f"items={len(value)}"
                )

                if value and isinstance(value[0], dict):
                    print(
                        f"       first item keys: "
                        f"{list(value[0].keys())}"
                    )

            elif isinstance(value, dict):
                print(f"DICT  | {current_path}")

                inspect_structure(value, current_path)


def main():
    print("FOTMOB LINEUP STRUCTURE TEST")
    print("=" * 60)

    print(f"Match ID: {MATCH_ID}")
    print(f"URL: {URL}")
    print()

    try:
        response = requests.get(
            URL,
            headers=HEADERS,
            timeout=30,
        )
    except Exception as e:
        print("REQUEST ERROR")
        print(e)
        return

    print(f"HTTP STATUS: {response.status_code}")
    print(f"HTML LENGTH: {len(response.text)}")

    if response.status_code != 200:
        print()
        print("FotMob request failed.")
        return

    data = get_next_data(response.text)

    if not data:
        print()
        print("NEXT_DATA NOT FOUND")
        return

    print("NEXT_DATA JSON OK")

    try:
        page_props = data["props"]["pageProps"]
        content = page_props["content"]
        lineup = content["lineup"]
    except (KeyError, TypeError):
        print()
        print("LINEUP STRUCTURE NOT FOUND")
        return

    print()
    print("=" * 60)
    print("LINEUP TOP-LEVEL KEYS")
    print("=" * 60)

    print(list(lineup.keys()))

    home_team = lineup.get("homeTeam")
    away_team = lineup.get("awayTeam")

    for label, team in [
        ("HOME TEAM", home_team),
        ("AWAY TEAM", away_team),
    ]:
        print()
        print("=" * 60)
        print(label)
        print("=" * 60)

        if not team:
            print("TEAM DATA NOT FOUND")
            continue

        print("TEAM KEYS:")
        print(list(team.keys()))

        print()
        print("STRUCTURE:")
        inspect_structure(team)

    print()
    print("=" * 60)
    print("TEST FINISHED")
    print("=" * 60)


if __name__ == "__main__":
    main()

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

    if not match:
        return None

    return json.loads(match.group(1))


def key_is_relevant(key):
    normalized = re.sub(r"[^a-z0-9]", "", str(key).lower())

    return normalized in {
        "aggregate",
        "aggregatescore",
        "aggregatescores",
        "penalty",
        "penalties",
        "penaltyscore",
        "penaltyscores",
        "penaltyshootout",
        "score",
        "result",
        "winner",
        "match",
        "leg",
    }


def print_relevant_data(obj, path="root", depth=0):
    if depth > 12:
        return

    if isinstance(obj, dict):
        for key, value in obj.items():
            current_path = path + "." + str(key)

            if key_is_relevant(key):
                print()
                print("-" * 100)
                print("FOUND:", current_path)
                print("-" * 100)
                print(
                    json.dumps(
                        value,
                        ensure_ascii=False,
                        indent=2,
                    )
                )

            if isinstance(value, (dict, list)):
                print_relevant_data(
                    value,
                    current_path,
                    depth + 1,
                )

    elif isinstance(obj, list):
        for index, value in enumerate(obj):
            if isinstance(value, (dict, list)):
                print_relevant_data(
                    value,
                    path + "[" + str(index) + "]",
                    depth + 1,
                )


def main():
    session = requests.Session()

    session.headers.update(
        {
            "User-Agent": "Mozilla/5.0",
            "Accept-Language": "en-US,en;q=0.9",
        }
    )

    for number, url in enumerate(MATCH_URLS, 1):
        print()
        print("=" * 100)
        print("MATCH", number)
        print(url)
        print("=" * 100)

        try:
            response = session.get(url, timeout=45)

            print("HTTP:", response.status_code)
            print("LENGTH:", len(response.text))

            response.raise_for_status()

            data = get_next_data(response.text)

            if data is None:
                print("ERROR: NEXT DATA NOT FOUND")
                continue

            print()
            print("SEARCHING ENTIRE __NEXT_DATA__...")
            print_relevant_data(data)

        except Exception as error:
            print()
            print("ERROR:", type(error).__name__)
            print(str(error))


if __name__ == "__main__":
    main()

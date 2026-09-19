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


def get_info_box(data):
    try:
        return data["props"]["pageProps"]["content"]["matchFacts"]["infoBox"]
    except (KeyError, TypeError):
        return None


def print_keys(obj, path=""):
    if isinstance(obj, dict):
        for key, value in obj.items():
            key_text = str(key).lower()

            if (
                "aggregate" in key_text
                or "leg" in key_text
                or "penalty" in key_text
            ):
                print()
                print("FOUND:", path + "." + str(key))
                print(json.dumps(value, ensure_ascii=False, indent=2))

            if isinstance(value, (dict, list)):
                print_keys(value, path + "." + str(key))

    elif isinstance(obj, list):
        for index, value in enumerate(obj):
            if isinstance(value, (dict, list)):
                print_keys(value, path + "[" + str(index) + "]")


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
        print("=" * 90)
        print("MATCH", number)
        print(url)
        print("=" * 90)

        try:
            response = session.get(url, timeout=45)

            print("HTTP:", response.status_code)
            print("LENGTH:", len(response.text))

            response.raise_for_status()

            data = get_next_data(response.text)

            if data is None:
                print("ERROR: NEXT DATA NOT FOUND")
                continue

            info_box = get_info_box(data)

            if info_box is None:
                print("ERROR: INFO BOX NOT FOUND")
                continue

            tournament = info_box.get("Tournament")
            leg_info = info_box.get("legInfo")

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
                    leg_info,
                    ensure_ascii=False,
                    indent=2,
                )
            )

            print()
            print("AGGREGATE / LEG / PENALTY RELATED DATA:")

            print_keys(info_box, "infoBox")

        except Exception as error:
            print()
            print("ERROR:", type(error).__name__)
            print(str(error))


if __name__ == "__main__":
    main()

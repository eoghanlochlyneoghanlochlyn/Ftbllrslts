import json
import re
import requests


MATCH_URLS = [
    # Europa League 2024/25 - Roma vs Porto
    "https://www.fotmob.com/matches/roma-vs-fc-porto/2tfyxz",

    # Europa League 2024/25 - Bodo/Glimt vs Twente
    "https://www.fotmob.com/matches/bodoglimt-vs-fc-twente/2e68pm",

    # Europa League 2024/25 - Manchester United vs Lyon
    "https://www.fotmob.com/matches/lyon-vs-manchester-united/3b6jpk",

    # Champions League 2025/26 - Real Madrid vs Benfica
    "https://www.fotmob.com/matches/real-madrid-vs-benfica/2sumx7#5161859",

    # Champions League 2025/26 - Manchester City vs Real Madrid
    "https://www.fotmob.com/matches/manchester-city-vs-real-madrid/2ey0nu#5205731",

    # Champions League 2025/26 - Bayern Munich vs Real Madrid
    "https://www.fotmob.com/matches/real-madrid-vs-bayern-munchen/2tes97#5205791",
]


SPECIAL_KEYS = {
    "aggregate",
    "aggregatescore",
    "aggregatescores",
    "aggregate_score",
    "aggregateScore",
    "aggregateScores",
    "penalty",
    "penalties",
    "penaltyscore",
    "penaltyscores",
    "penalty_score",
    "penaltyScore",
    "penaltyScores",
    "winner",
    "winnerteam",
    "winnerTeam",
    "result",
    "matchresult",
    "matchResult",
    "leg",
    "leginfo",
    "legInfo",
    "bestof",
    "bestOf",
    "secondleg",
    "secondLeg",
    "firstleg",
    "firstLeg",
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


def walk_special_keys(obj, path="root", depth=0, results=None):
    if results is None:
        results = []

    if depth > 15:
        return results

    if isinstance(obj, dict):
        for key, value in obj.items():
            key_text = str(key)
            normalized = key_text.lower()

            if (
                normalized in {x.lower() for x in SPECIAL_KEYS}
                or "aggregate" in normalized
                or "penalty" in normalized
                or normalized in {
                    "winner",
                    "winnerteam",
                    "result",
                    "matchresult",
                    "leg",
                    "leginfo",
                    "bestof",
                }
            ):
                results.append(
                    (
                        path + "." + key_text,
                        value,
                    )
                )

            if isinstance(value, (dict, list)):
                walk_special_keys(
                    value,
                    path + "." + key_text,
                    depth + 1,
                    results,
                )

    elif isinstance(obj, list):
        for index, value in enumerate(obj):
            if isinstance(value, (dict, list)):
                walk_special_keys(
                    value,
                    path + "[" + str(index) + "]",
                    depth + 1,
                    results,
                )

    return results


def get_info_box(data):
    try:
        return (
            data["props"]
            ["pageProps"]
            ["content"]
            ["matchFacts"]
            ["infoBox"]
        )
    except (KeyError, TypeError):
        return {}


def print_basic_info(data):
    page_props = data["props"]["pageProps"]

    header = page_props.get("header", {})
    info_box = get_info_box(data)

    print()
    print("BASIC MATCH DATA")
    print("-" * 100)

    teams = header.get("teams", [])

    if isinstance(teams, list):
        for index, team in enumerate(teams):
            if not isinstance(team, dict):
                continue

            print(
                f"TEAM {index + 1}:",
                team.get("name"),
                "| score =",
                team.get("score"),
                "| id =",
                team.get("id"),
            )

    tournament = info_box.get("Tournament")

    print()
    print(
        "TOURNAMENT:",
        json.dumps(
            tournament,
            ensure_ascii=False,
            indent=2,
        ),
    )

    print()
    print(
        "LEG INFO:",
        json.dumps(
            info_box.get("legInfo"),
            ensure_ascii=False,
            indent=2,
        ),
    )


def print_special_data(data):
    print()
    print("SPECIAL DATA")
    print("-" * 100)

    results = walk_special_keys(data)

    if not results:
        print("NO SPECIAL DATA FOUND")
        return

    seen = set()

    for path, value in results:
        key = (
            path,
            json.dumps(
                value,
                ensure_ascii=False,
                sort_keys=True,
                default=str,
            ),
        )

        if key in seen:
            continue

        seen.add(key)

        print()
        print("PATH:")
        print(path)

        print("VALUE:")
        print(
            json.dumps(
                value,
                ensure_ascii=False,
                indent=2,
                default=str,
            )
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
        print("=" * 110)
        print("MATCH", number)
        print(url)
        print("=" * 110)

        try:
            response = session.get(
                url,
                timeout=45,
            )

            print("HTTP:", response.status_code)
            print("LENGTH:", len(response.text))

            response.raise_for_status()

            data = get_next_data(response.text)

            if data is None:
                print("ERROR: __NEXT_DATA__ NOT FOUND")
                continue

            print_basic_info(data)
            print_special_data(data)

        except Exception as error:
            print()
            print("ERROR:", type(error).__name__)
            print(str(error))


if __name__ == "__main__":
    main()

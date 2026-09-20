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


def get_match_data(data):
    try:
        page_props = data["props"]["pageProps"]
        return page_props
    except (KeyError, TypeError):
        return None


def print_team_form(team_form, teams):
    if not isinstance(team_form, list):
        print("TEAM FORM: not found")
        return

    print()
    print("TEAM FORM")
    print("-" * 100)

    for team_index, matches in enumerate(team_form):
        team_name = "UNKNOWN"

        if isinstance(teams, list) and team_index < len(teams):
            team = teams[team_index]

            if isinstance(team, dict):
                team_name = (
                    team.get("name")
                    or team.get("teamName")
                    or team.get("shortName")
                    or "UNKNOWN"
                )

        print()
        print("TEAM:", team_name)
        print()

        if not isinstance(matches, list):
            print(matches)
            continue

        for index, item in enumerate(matches):
            if not isinstance(item, dict):
                print(index, ":", item)
                continue

            print("MATCH", index + 1)
            print(
                json.dumps(
                    item,
                    ensure_ascii=False,
                    indent=2,
                )
            )


def print_header_scores(header):
    print()
    print("CURRENT MATCH HEADER")
    print("-" * 100)

    teams = header.get("teams")

    if not isinstance(teams, list):
        print("TEAMS NOT FOUND")
        return

    for index, team in enumerate(teams):
        if not isinstance(team, dict):
            continue

        print(
            index,
            "|",
            team.get("name"),
            "| score =",
            team.get("score"),
            "| id =",
            team.get("id"),
        )


def print_leg_info(info_box):
    print()
    print("TOURNAMENT / LEG")
    print("-" * 100)

    tournament = info_box.get("Tournament")
    leg_info = info_box.get("legInfo")

    print(
        "TOURNAMENT:",
        json.dumps(
            tournament,
            ensure_ascii=False,
            indent=2,
        ),
    )

    print(
        "LEG INFO:",
        json.dumps(
            leg_info,
            ensure_ascii=False,
            indent=2,
        ),
    )


def find_match_related_data(obj, path="root", depth=0):
    if depth > 8:
        return

    if isinstance(obj, dict):
        for key, value in obj.items():
            key_text = str(key).lower()

            if key_text in {
                "aggregate",
                "aggregatescore",
                "aggregatescores",
                "penaltyscore",
                "penaltyscores",
                "winner",
                "winnerteam",
            }:
                print()
                print("SPECIAL KEY:", path + "." + str(key))
                print(
                    json.dumps(
                        value,
                        ensure_ascii=False,
                        indent=2,
                    )
                )

            if isinstance(value, (dict, list)):
                find_match_related_data(
                    value,
                    path + "." + str(key),
                    depth + 1,
                )

    elif isinstance(obj, list):
        for index, value in enumerate(obj):
            if isinstance(value, (dict, list)):
                find_match_related_data(
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

            page_props = get_match_data(data)

            if page_props is None:
                print("ERROR: PAGE PROPS NOT FOUND")
                continue

            header = page_props.get("header", {})
            content = page_props.get("content", {})
            match_facts = content.get("matchFacts", {})
            info_box = match_facts.get("infoBox", {})

            print_header_scores(header)
            print_leg_info(info_box)

            teams = header.get("teams")
            team_form = match_facts.get("teamForm")

            print_team_form(team_form, teams)

            print()
            print("SPECIAL AGGREGATE / WINNER DATA")
            print("-" * 100)

            find_match_related_data(data)

        except Exception as error:
            print()
            print("ERROR:", type(error).__name__)
            print(str(error))


if __name__ == "__main__":
    main()

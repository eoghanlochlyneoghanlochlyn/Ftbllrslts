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


def find_key(obj, target_key, path="root"):
    if isinstance(obj, dict):
        for key, value in obj.items():
            current_path = f"{path}.{key}"

            if key == target_key:
                yield current_path, value

            yield from find_key(value, target_key, current_path)

    elif isinstance(obj, list):
        for index, value in enumerate(obj):
            current_path = f"{path}[{index}]"
            yield from find_key(value, target_key, current_path)


def extract_next_data(html):
    match = re.search(
        r'<script id="__NEXT_DATA__" type="application/json">(.*?)</script>',
        html,
        re.DOTALL,
    )

    if not match:
        raise RuntimeError("__NEXT_DATA__ was not found.")

    return json.loads(match.group(1))


def get_tournament_info(data):
    tournament_results = list(find_key(data, "Tournament"))

    for path, tournament in tournament_results:
        if not isinstance(tournament, dict):
            continue

        if "leagueName" not in tournament:
            continue

        return path, tournament

    return None, None


def get_leg_info(data, tournament):
    info_box_results = list(find_key(data, "infoBox"))

    for _, info_box in info_box_results:
        if not isinstance(info_box, dict):
            continue

        if info_box.get("Tournament") is tournament:
            return info_box.get("legInfo")

    return None


def main():
    print("=" * 80)
    print("FotMob Competition / Round Test")
    print("=" * 80)

    session = requests.Session()

    session.headers.update(
        {
            "User-Agent": "Mozilla/5.0",
        }
    )

    for index, match_url in enumerate(MATCH_URLS, start=1):

        print("\n" + "=" * 80)
        print(f"MATCH {index}/{len(MATCH_URLS)}")
        print("=" * 80)

        print("URL:")
        print(match_url)

        try:
            response = session.get(
                match_url,
                timeout=45,
            )

            print("\nHTTP status:", response.status_code)
            print("Response length:", len(response.text))

            response.raise_for_status()

            data = extract_next_data(response.text)

            tournament_path, tournament = get_tournament_info(data)

            if tournament is None:
                print("\nTournament information was NOT found.")
                continue

            leg_info = get_leg_info(data, tournament)

            print("\n---------- RESULT ----------")

            print("Tournament path:")
            print(tournament_path)

            print("\nCompetition:")
            print(tournament.get("leagueName"))

            print("\nRound:")
            print(tournament.get("round"))

            print("\nRound name:")
            print(tournament.get("roundName"))

            print("\nLeg info:")
            print(
                json.dumps(
                    leg_info,
                    ensure_ascii=False,
                    indent=2,
                )
                if leg_info is not None
                else "None"
            )

            print("\nRAW TOURNAMENT:")
            print(
                json.dumps(
                    tournament,
                    ensure_ascii=False,
                    indent=2,
                )
            )

        except Exception as e:
            print("\nERROR:")
            print(type(e).__name__, str(e))


if __name__ == "__main__":
    main()

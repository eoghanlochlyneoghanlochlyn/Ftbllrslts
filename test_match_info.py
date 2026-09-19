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


def get_next_data(html):
    pattern = r'<script id="__NEXT_DATA__" type="application/json">(.*?)</script>'

    match = re.search(pattern, html, re.DOTALL)

    if not match:
        return None

    return json.loads(match.group(1))


def find_info_box(obj):
    if isinstance(obj, dict):

        if "matchFacts" in obj and isinstance(obj["matchFacts"], dict):
            match_facts = obj["matchFacts"]

            if "infoBox" in match_facts and isinstance(
                match_facts["infoBox"], dict
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


def get_leg_text(info_box):
    leg_info = info_box.get("legInfo")

    if leg_info is None:
        return "-"

    if isinstance(leg_info, str):
        return leg_info

    if isinstance(leg_info, dict):

        for key in (
            "localizedString",
            "text",
            "string",
            "name",
            "label",
            "fallback",
        ):
            value = leg_info.get(key)

            if isinstance(value, str) and value.strip():
                return value.strip()

            if isinstance(value, dict):
                for subkey in (
                    "fallback",
                    "text",
                    "string",
                    "name",
                    "label",
                ):
                    subvalue = value.get(subkey)

                    if isinstance(subvalue, str) and subvalue.strip():
                        return subvalue.strip()

        leg = leg_info.get("leg")

        if leg is not None:
            return str(leg)

        leg_number = leg_info.get("legNumber")

        if leg_number is not None:
            return str(leg_number)

    return "-"


def process_match(session, index, url):
    try:
        response = session.get(
            url,
            timeout=45,
        )

        response.raise_for_status()

        data = get_next_data(response.text)

        if data is None:
            print(
                f"{index:02d} | ERROR | __NEXT_DATA__ not found"
            )
            return

        info_box = find_info_box(data)

        if info_box is None:
            print(
                f"{index:02d} | ERROR | infoBox not found"
            )
            return

        tournament = info_box.get("Tournament")

        if not isinstance(tournament, dict):
            print(
                f"{index:02d} | ERROR | Tournament not found"
            )
            return

        competition = (
            tournament.get("leagueName")
            or tournament.get("name")
            or "-"
        )

        round_name = (
            tournament.get("roundName")
            or tournament.get("round")
            or "-"
        )

        leg = get_leg_text(info_box)

        print(
            f"{index:02d} | "
            f"{competition} | "
            f"Round: {round_name} | "
            f"Leg: {leg}"
        )

    except Exception as e:
        print(
            f"{index:02d} | ERROR | "
            f"{type(e).__name__}: {e}"
        )


def main():
    session = requests.Session()

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

    print()
    print("FotMob Competition / Round / Leg Test")
    print("=" * 90)

    for index, url in enumerate(MATCH_URLS, start=1):
        process_match(
            session,
            index,
            url,
        )

    print("=" * 90)
    print("Test finished.")


if __name__ == "__main__":
    main()

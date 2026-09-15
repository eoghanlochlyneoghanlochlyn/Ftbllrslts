import json
import time
from typing import Any

import requests


SEARCH_URL = "https://www.fotmob.com/api/data/search/suggest"

REQUEST_DELAY = 0.4
TIMEOUT = 15

COUNTRY = "Spain"


TEAMS_TO_FIND = [
    # LaLiga
    "Athletic Club",
    "Atlético de Madrid",
    "CA Osasuna",
    "Celta",
    "Deportivo Alavés",
    "Elche CF",
    "FC Barcelona",
    "Getafe CF",
    "Levante UD",
    "Málaga CF",
    "R. Racing Club",
    "Rayo Vallecano",
    "RC Deportivo",
    "RCD Espanyol de Barcelona",
    "Real Betis",
    "Real Madrid",
    "Real Sociedad",
    "Sevilla FC",
    "Valencia CF",
    "Villarreal CF",

    # Segunda División
    "AD Ceuta FC",
    "Albacete BP",
    "Burgos CF",
    "Cádiz CF",
    "CD Castellón",
    "CD Eldense",
    "CD Leganés",
    "CD Tenerife",
    "CE Sabadell",
    "Celta Fortuna",
    "Córdoba CF",
    "FC Andorra",
    "Girona FC",
    "Granada CF",
    "R. Sociedad B",
    "RCD Mallorca",
    "Real Oviedo",
    "Real Sporting",
    "Real Valladolid CF",
    "SD Eibar",
    "UD Almería",
    "UD Las Palmas",
]


# --------------------------------------------------------
# نام فارسی تیم‌ها
# --------------------------------------------------------

PERSIAN_NAMES = {
    "Athletic Club": "اتلتیک بیلبائو",
    "Atlético de Madrid": "اتلتیکومادرید",
    "CA Osasuna": "اوساسونا",
    "Celta": "سلتاویگو",
    "Deportivo Alavés": "آلاوس",
    "Elche CF": "الچه",
    "FC Barcelona": "بارسلونا",
    "Getafe CF": "ختافه",
    "Levante UD": "لوانته",
    "Málaga CF": "مالاگا",
    "R. Racing Club": "راسينگ سانتاندر",
    "Rayo Vallecano": "رایو وایکانو",
    "RC Deportivo": "دپورتیوو لاکرونیا",
    "RCD Espanyol de Barcelona": "اسپانیول",
    "Real Betis": "رئال بتیس",
    "Real Madrid": "رئال مادرید",
    "Real Sociedad": "رئال سوسیداد",
    "Sevilla FC": "سویا",
    "Valencia CF": "والنسیا",
    "Villarreal CF": "ویارئال",

    "AD Ceuta FC": "سئوتا",
    "Albacete BP": "آلباسته",
    "Burgos CF": "بورگوس",
    "Cádiz CF": "کادیز",
    "CD Castellón": "کاستیون",
    "CD Eldense": "الدنسه",
    "CD Leganés": "لگانس",
    "CD Tenerife": "تنریف",
    "CE Sabadell": "سابادل",
    "Celta Fortuna": "سلتا فورتونا",
    "Córdoba CF": "کوردوبا",
    "FC Andorra": "آندورا",
    "Girona FC": "ژیرونا",
    "Granada CF": "گرانادا",
    "R. Sociedad B": "رئال سوسیداد بی",
    "RCD Mallorca": "مایورکا",
    "Real Oviedo": "رئال اوویدو",
    "Real Sporting": "اسپورتینگ خیخون",
    "Real Valladolid CF": "وایادولید",
    "SD Eibar": "ایبار",
    "UD Almería": "آلمریا",
    "UD Las Palmas": "لاس پالماس",
}


# --------------------------------------------------------
# ابزارها
# --------------------------------------------------------

def clean_text(value: Any) -> str:
    if value is None:
        return ""

    return " ".join(str(value).split()).strip()


def normalize_name(value: Any) -> str:
    value = clean_text(value).lower()

    replacements = {
        "á": "a",
        "é": "e",
        "í": "i",
        "ó": "o",
        "ú": "u",
        "ü": "u",
        "ñ": "n",
        "’": "'",
    }

    for old, new in replacements.items():
        value = value.replace(old, new)

    return value


def get_team_name(team: dict) -> str:
    for key in (
        "longName",
        "name",
        "shortName",
        "title",
    ):
        value = team.get(key)

        if value:
            return clean_text(value)

    return ""


def get_team_id(team: dict):
    return (
        team.get("id")
        or team.get("teamId")
        or team.get("teamID")
    )


def get_country(team: dict) -> str:
    country = team.get("country")

    if isinstance(country, dict):
        return clean_text(
            country.get("name")
            or country.get("longName")
            or country.get("shortName")
        )

    if country:
        return clean_text(country)

    for key in (
        "countryName",
        "country_name",
    ):
        value = team.get(key)

        if value:
            return clean_text(value)

    return ""


def is_team_result(item: Any) -> bool:
    if not isinstance(item, dict):
        return False

    item_type = str(item.get("type", "")).lower()

    return item_type == "team"


def extract_team_objects(obj: Any) -> list[dict]:
    """
    به‌صورت بازگشتی تمام objectهایی که type=team دارند
    پیدا می‌کند.
    """

    found = []

    if isinstance(obj, dict):

        if is_team_result(obj):
            found.append(obj)

        for value in obj.values():
            found.extend(extract_team_objects(value))

    elif isinstance(obj, list):

        for item in obj:
            found.extend(extract_team_objects(item))

    return found


def is_women_or_youth(team: dict) -> bool:
    """
    حذف تیم‌های زنان، جوانان، B / II / U21 / U23 و موارد مشابه.
    """

    text_parts = []

    for key in (
        "name",
        "longName",
        "shortName",
        "title",
    ):
        value = team.get(key)

        if value:
            text_parts.append(str(value))

    text = " ".join(text_parts).lower()

    blocked_words = [
        "women",
        "woman",
        "femenino",
        "femeni",
        "female",
        "ladies",
        "girls",
        "youth",
        "juvenil",
        "juvenile",
        "u19",
        "u20",
        "u21",
        "u23",
        "under-19",
        "under-20",
        "under-21",
        "under-23",
    ]

    for word in blocked_words:
        if word in text:
            return True

    return False


def search_team(query: str) -> list[dict]:
    params = {
        "term": query,
        "hits": 50,
        "lang": "en",
    }

    response = requests.get(
        SEARCH_URL,
        params=params,
        timeout=TIMEOUT,
        headers={
            "User-Agent": (
                "Mozilla/5.0 "
                "(Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 "
                "(KHTML, like Gecko) "
                "Chrome/140.0 Safari/537.36"
            )
        },
    )

    response.raise_for_status()

    data = response.json()

    teams = extract_team_objects(data)

    # حذف موارد تکراری
    unique = {}

    for team in teams:

        team_id = get_team_id(team)

        if team_id is None:
            continue

        unique[str(team_id)] = team

    return list(unique.values())


def score_candidate(
    candidate: dict,
    requested_name: str,
) -> int:

    name = normalize_name(
        get_team_name(candidate)
    )

    requested = normalize_name(
        requested_name
    )

    score = 0

    # نام دقیق
    if name == requested:
        score += 100

    # نام اصلی شامل عبارت جستجو
    elif requested in name:
        score += 70

    # عبارت جستجو شامل نام نتیجه
    elif name in requested:
        score += 50

    # کشور
    country = normalize_name(
        get_country(candidate)
    )

    if country == normalize_name(COUNTRY):
        score += 30

    # حذف زنان / پایه
    if is_women_or_youth(candidate):
        score -= 200

    return score


def choose_best_team(
    candidates: list[dict],
    requested_name: str,
):
    valid = []

    for candidate in candidates:

        if is_women_or_youth(candidate):
            continue

        team_id = get_team_id(candidate)

        if team_id is None:
            continue

        valid.append(candidate)

    if not valid:
        return None, []

    scored = []

    for candidate in valid:

        score = score_candidate(
            candidate,
            requested_name,
        )

        scored.append(
            (
                score,
                candidate,
            )
        )

    scored.sort(
        key=lambda item: item[0],
        reverse=True,
    )

    best_score = scored[0][0]

    best = [
        candidate
        for score, candidate in scored
        if score == best_score
    ]

    # اگر چند نتیجه دقیقاً هم‌امتیاز باشند،
    # نمی‌خواهیم حدس بزنیم.
    if len(best) > 1:
        return None, scored

    # حداقل اطمینان
    if best_score < 100:
        return None, scored

    return best[0], scored


def make_output(
    requested_name: str,
    team: dict,
) -> dict:

    team_name = get_team_name(team)
    team_id = get_team_id(team)

    return {
        "id": str(team_id),
        "name": team_name,
        "country": COUNTRY,
        "persian": PERSIAN_NAMES.get(
            requested_name,
            requested_name,
        ),
    }


# --------------------------------------------------------
# اجرای اصلی
# --------------------------------------------------------

def main():

    print("FotMob Team ID Extractor")
    print(f"Country: {COUNTRY}")
    print(f"Total teams: {len(TEAMS_TO_FIND)}")
    print()

    confirmed = []
    ambiguous = []
    not_found = []

    for index, requested_name in enumerate(
        TEAMS_TO_FIND,
        start=1,
    ):

        print(
            f"[{index}/{len(TEAMS_TO_FIND)}] "
            f"{requested_name}"
        )

        try:

            candidates = search_team(
                requested_name
            )

            team, scored = choose_best_team(
                candidates,
                requested_name,
            )

            if team is not None:

                result = make_output(
                    requested_name,
                    team,
                )

                confirmed.append(result)

                print(
                    f"    ✅ "
                    f"{result['name']} "
                    f"→ {result['id']}"
                )

            elif scored:

                ambiguous.append(
                    (
                        requested_name,
                        scored,
                    )
                )

                print(
                    "    ⚠️ AMBIGUOUS"
                )

                for score, candidate in scored[:10]:

                    print(
                        f"       - "
                        f"{get_team_name(candidate)} "
                        f"→ {get_team_id(candidate)} "
                        f"| country={get_country(candidate)} "
                        f"| score={score}"
                    )

            else:

                not_found.append(
                    requested_name
                )

                print(
                    "    ❌ NOT FOUND"
                )

        except Exception as exc:

            print(
                f"    ❌ ERROR: {exc}"
            )

            not_found.append(
                requested_name
            )

        print()

        time.sleep(
            REQUEST_DELAY
        )

    # ----------------------------------------------------
    # گزارش نهایی
    # ----------------------------------------------------

    print("=" * 60)
    print("FINAL REPORT")
    print("=" * 60)

    print(
        f"Requested : {len(TEAMS_TO_FIND)}"
    )

    print(
        f"Confirmed : {len(confirmed)}"
    )

    print(
        f"Ambiguous : {len(ambiguous)}"
    )

    print(
        f"Not found : {len(not_found)}"
    )

    # ----------------------------------------------------
    # خروجی استاندارد
    # ----------------------------------------------------

    print()
    print("=" * 60)
    print("STANDARD OUTPUT")
    print("=" * 60)
    print()

    print("TEAMS = [")

    for team in confirmed:

        print("    {")

        print(
            f'        "id": "{team["id"]}",'
        )

        print(
            f'        "name": "{team["name"]}",'
        )

        print(
            f'        "country": "{team["country"]}",'
        )

        print(
            f'        "persian": "{team["persian"]}",'
        )

        print("    },")

    print("]")

    # ----------------------------------------------------
    # موارد مبهم
    # ----------------------------------------------------

    if ambiguous:

        print()
        print("=" * 60)
        print("AMBIGUOUS TEAMS")
        print("=" * 60)

        for requested_name, scored in ambiguous:

            print()
            print(
                f"{requested_name}:"
            )

            for score, candidate in scored[:10]:

                print(
                    f"    "
                    f"{get_team_name(candidate)} "
                    f"→ {get_team_id(candidate)} "
                    f"| country={get_country(candidate)} "
                    f"| score={score}"
                )

    # ----------------------------------------------------
    # پیدا نشد
    # ----------------------------------------------------

    if not_found:

        print()
        print("=" * 60)
        print("NOT FOUND")
        print("=" * 60)

        for name in not_found:
            print(
                f"    - {name}"
            )


if __name__ == "__main__":
    main()

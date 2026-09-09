import json
import requests
from urllib.parse import quote


TEAMS = [
    "Liverpool",
    "Arsenal",
    "Manchester City",
    "Manchester United",
    "Chelsea",
    "Tottenham Hotspur",
    "Juventus",
    "AC Milan",
    "Inter Milan",
    "Bayern Munich",
    "Borussia Dortmund",
    "PSG",
    "Real Madrid",
    "Barcelona",
    "Atlético Madrid",
]


HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (X11; Linux x86_64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/140.0.0.0 Safari/537.36"
    ),
    "Accept": (
        "text/html,application/xhtml+xml,"
        "application/xml;q=0.9,image/avif,image/webp,"
        "*/*;q=0.8"
    ),
    "Accept-Language": "en-US,en;q=0.9",
    "Referer": "https://www.fotmob.com/",
}


def search_fotmob(term):
    url = (
        "https://www.fotmob.com/api/data/search/suggest"
        f"?term={quote(term)}&hits=20&lang=en"
    )

    response = requests.get(
        url,
        headers=HEADERS,
        timeout=30,
    )

    print(
        f"HTTP {response.status_code} | "
        f"{term}"
    )

    response.raise_for_status()

    return response.json()


def extract_results(data):
    if isinstance(data, list):
        return data

    if not isinstance(data, dict):
        return []

    for key in [
        "suggestions",
        "results",
        "data",
    ]:
        value = data.get(key)

        if isinstance(value, list):
            return value

    return []


def get_result_type(item):
    if not isinstance(item, dict):
        return ""

    return (
        item.get("type")
        or item.get("entityType")
        or item.get("category")
        or ""
    )


def get_team_id(item):
    if not isinstance(item, dict):
        return None

    for key in [
        "id",
        "teamId",
    ]:
        value = item.get(key)

        if value is not None:
            return value

    team = item.get("team")

    if isinstance(team, dict):
        for key in [
            "id",
            "teamId",
        ]:
            value = team.get(key)

            if value is not None:
                return value

    return None


def get_team_name(item):
    if not isinstance(item, dict):
        return None

    for key in [
        "name",
        "teamName",
        "title",
    ]:
        value = item.get(key)

        if value:
            return value

    team = item.get("team")

    if isinstance(team, dict):
        for key in [
            "name",
            "teamName",
            "title",
        ]:
            value = team.get(key)

            if value:
                return value

    return None


def is_team_result(item):
    result_type = str(
        get_result_type(item)
    ).lower()

    if result_type in [
        "team",
        "club",
    ]:
        return True

    if get_team_id(item) is not None:
        return True

    return False


def find_team_results(data):
    results = extract_results(data)

    teams = []

    for item in results:

        if not is_team_result(item):
            continue

        team_id = get_team_id(item)
        team_name = get_team_name(item)

        if team_id is None:
            continue

        teams.append(
            {
                "id": team_id,
                "name": team_name,
                "type": get_result_type(item),
            }
        )

    return teams


def main():

    print("=" * 70)
    print("جست‌وجوی ۱۵ تیم در فوت‌ماب")
    print("=" * 70)
    print()

    found_teams = {}

    for search_name in TEAMS:

        print("=" * 70)
        print(
            f"جست‌وجو: {search_name}"
        )
        print("=" * 70)

        try:

            data = search_fotmob(
                search_name
            )

            teams = find_team_results(
                data
            )

            if not teams:

                print(
                    "❌ نتیجهٔ تیمی پیدا نشد."
                )
                print()
                continue

            print(
                f"تعداد نتایج تیمی: "
                f"{len(teams)}"
            )
            print()

            for index, team in enumerate(
                teams,
                start=1,
            ):

                print(
                    f"{index}. "
                    f"{team['name']} "
                    f"→ ID: {team['id']}"
                )

            best = teams[0]

            found_teams[search_name] = {
                "name": best["name"],
                "id": best["id"],
            }

            print()
            print(
                "⭐ نتیجهٔ انتخاب‌شده:"
            )
            print(
                f"{best['name']} "
                f"→ {best['id']}"
            )

        except Exception as error:

            print(
                f"❌ خطا: {error}"
            )

        print()

    print("=" * 70)
    print("خلاصهٔ نهایی")
    print("=" * 70)
    print()

    for search_name in TEAMS:

        result = found_teams.get(
            search_name
        )

        if result:

            print(
                f"{search_name:<24} "
                f"→ {result['name']:<24} "
                f"→ {result['id']}"
            )

        else:

            print(
                f"{search_name:<24} "
                f"→ ❌ پیدا نشد"
            )

    print()

    with open(
        "fotmob_teams.json",
        "w",
        encoding="utf-8",
    ) as file:

        json.dump(
            found_teams,
            file,
            ensure_ascii=False,
            indent=2,
        )

    print(
        "✅ نتیجه در "
        "fotmob_teams.json "
        "ذخیره شد."
    )


if __name__ == "__main__":
    main()

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
        f"HTTP {response.status_code} | {term}"
    )

    response.raise_for_status()

    return response.json()


def extract_team_suggestions(data):
    teams = []

    if not isinstance(data, list):
        return teams

    for section in data:

        if not isinstance(section, dict):
            continue

        suggestions = section.get(
            "suggestions",
            [],
        )

        if not isinstance(suggestions, list):
            continue

        for item in suggestions:

            if not isinstance(item, dict):
                continue

            if item.get("type") != "team":
                continue

            team_id = item.get("id")
            team_name = item.get("name")

            if team_id is None:
                continue

            if not team_name:
                continue

            teams.append(
                {
                    "id": str(team_id),
                    "name": team_name,
                    "score": item.get(
                        "score",
                        0,
                    ),
                    "league_id": item.get(
                        "leagueId"
                    ),
                    "league_name": item.get(
                        "leagueName"
                    ),
                }
            )

    return teams


def choose_best_team(
    search_name,
    teams,
):
    if not teams:
        return None

    search_name_lower = (
        search_name.strip().lower()
    )

    exact_matches = [
        team
        for team in teams
        if team["name"].strip().lower()
        == search_name_lower
    ]

    if exact_matches:

        exact_matches.sort(
            key=lambda team: team.get(
                "score",
                0,
            ),
            reverse=True,
        )

        return exact_matches[0]

    teams.sort(
        key=lambda team: team.get(
            "score",
            0,
        ),
        reverse=True,
    )

    return teams[0]


def main():

    print("=" * 70)
    print("پیدا کردن شناسهٔ ۱۵ تیم در فوت‌ماب")
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

            teams = extract_team_suggestions(
                data
            )

            if not teams:

                print(
                    "❌ هیچ تیمی پیدا نشد."
                )
                print()

                continue

            print(
                f"تعداد نتایج تیمی: "
                f"{len(teams)}"
            )
            print()

            print("نتایج:")

            for index, team in enumerate(
                teams,
                start=1,
            ):

                print(
                    f"  {index}. "
                    f"{team['name']} "
                    f"→ ID: {team['id']} "
                    f"| لیگ: "
                    f"{team['league_name']}"
                )

            best_team = choose_best_team(
                search_name,
                teams,
            )

            if best_team is None:

                print(
                    "❌ انتخاب تیم ناموفق بود."
                )

                print()

                continue

            found_teams[search_name] = {
                "id": best_team["id"],
                "name": best_team["name"],
                "league_id": best_team[
                    "league_id"
                ],
                "league_name": best_team[
                    "league_name"
                ],
            }

            print()
            print(
                "⭐ تیم انتخاب‌شده:"
            )

            print(
                f"  {best_team['name']} "
                f"→ ID: {best_team['id']}"
            )

            print(
                f"  لیگ: "
                f"{best_team['league_name']}"
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

        team = found_teams.get(
            search_name
        )

        if team:

            print(
                f"{search_name:<24} "
                f"→ {team['name']:<24} "
                f"→ ID: {team['id']}"
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

    print()
    print("=" * 70)
    print(
        f"تعداد تیم‌های پیدا شده: "
        f"{len(found_teams)} از {len(TEAMS)}"
    )
    print("=" * 70)


if __name__ == "__main__":
    main()

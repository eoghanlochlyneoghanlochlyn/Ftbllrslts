import requests
import time


# ============================================================
# لیست تیم‌ها
# ============================================================

TEAMS = [
    "Nacional",
    "Olimpia",
    "Everton",
    "Al Ahli",
    "Al Hilal",
    "Al Ittihad",
    "Al Wahda",
    "Al Wehda",
    "Al Arabi",
    "Al Qadsiah",
    "Al Qadsia",
    "Al Faisaly",
    "Al Nassr",
    "Al Nasr",
    "América",
    "Alianza",
    "Universidad Católica",
    "Barcelona",
    "Independiente",
    "Racing",
    "Junior",

    # تیم‌های فعلاً قطعی برای تست
    "Real Sociedad",
    "Osasuna",
    "AC Milan",
    "Milan",
    "Inter",
    "Inter Milan",
]


# ============================================================
# تنظیمات
# ============================================================

BASE_URL = "https://www.fotmob.com/api/data/search/suggest"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/140.0.0.0 Safari/537.36"
    ),
    "Accept": "application/json",
}


# بین درخواست‌ها کمی فاصله می‌گذاریم
REQUEST_DELAY = 0.4


# ============================================================
# جست‌وجوی یک تیم
# ============================================================

def search_team(team_name):

    params = {
        "term": team_name,
        "hits": 50,
        "lang": "en",
    }

    try:

        response = requests.get(
            BASE_URL,
            params=params,
            headers=HEADERS,
            timeout=20,
        )

    except requests.RequestException as e:

        print()
        print(f"❌ Request error: {e}")

        return []

    print(
        f"HTTP: {response.status_code}"
    )

    if response.status_code != 200:

        print(
            f"❌ FotMob request failed for: "
            f"{team_name}"
        )

        return []

    try:

        data = response.json()

    except ValueError:

        print(
            "❌ Response is not valid JSON"
        )

        return []

    return extract_team_results(data)


# ============================================================
# استخراج نتایج تیم‌ها
# ============================================================

def extract_team_results(data):

    results = []

    def walk(value):

        if isinstance(value, dict):

            # اگر خود آبجکت یک تیم است
            if value.get("type") == "team":

                team_id = (
                    value.get("id")
                    or value.get("teamId")
                    or value.get("teamID")
                )

                name = (
                    value.get("name")
                    or value.get("title")
                    or ""
                )

                league_name = (
                    value.get("leagueName")
                    or ""
                )

                league_id = (
                    value.get("leagueId")
                    or ""
                )

                if team_id and name:

                    result = {
                        "id": str(team_id),
                        "name": str(name),
                        "league_name": str(
                            league_name
                        ),
                        "league_id": str(
                            league_id
                        ),
                    }

                    results.append(result)

            for child in value.values():

                walk(child)

        elif isinstance(value, list):

            for item in value:

                walk(item)

    walk(data)

    # حذف موارد تکراری
    unique = {}

    for item in results:

        key = (
            item["id"],
            item["name"],
            item["league_id"],
        )

        unique[key] = item

    return list(unique.values())


# ============================================================
# چاپ نتایج
# ============================================================

def print_results(
    search_name,
    results,
):

    print()
    print("=" * 70)
    print(
        f"SEARCH: {search_name}"
    )
    print("=" * 70)

    if not results:

        print(
            "❌ No team results found."
        )

        return

    for index, team in enumerate(
        results,
        start=1,
    ):

        print()
        print(
            f"{index}. {team['name']}"
        )

        print(
            f"   ID:     {team['id']}"
        )

        if team["league_name"]:

            print(
                f"   League: "
                f"{team['league_name']}"
            )

        if team["league_id"]:

            print(
                f"   League ID: "
                f"{team['league_id']}"
            )


# ============================================================
# اجرای تست
# ============================================================

def main():

    print("=" * 70)
    print("FOTMOB TEAM ID SEARCH")
    print("=" * 70)

    print()
    print(
        f"Total teams: {len(TEAMS)}"
    )

    print()
    print(
        "Searching FotMob..."
    )

    all_results = {}

    for index, team_name in enumerate(
        TEAMS,
        start=1,
    ):

        print()
        print(
            f"[{index}/{len(TEAMS)}] "
            f"{team_name}"
        )

        results = search_team(
            team_name
        )

        all_results[team_name] = results

        print_results(
            team_name,
            results,
        )

        if index < len(TEAMS):

            time.sleep(
                REQUEST_DELAY
            )

    # ========================================================
    # خلاصه
    # ========================================================

    print()
    print()
    print("=" * 70)
    print("SUMMARY")
    print("=" * 70)

    found_count = 0
    not_found_count = 0
    ambiguous_count = 0

    for team_name, results in (
        all_results.items()
    ):

        if not results:

            not_found_count += 1

            print()
            print(
                f"❌ {team_name}"
            )

        elif len(results) == 1:

            found_count += 1

            team = results[0]

            print()
            print(
                f"✅ {team_name}"
            )

            print(
                f"   "
                f"{team['name']} "
                f"→ {team['id']}"
            )

        else:

            ambiguous_count += 1

            print()
            print(
                f"⚠️ {team_name}"
            )

            print(
                f"   "
                f"{len(results)} "
                f"team results"
            )

            for team in results:

                league = (
                    team["league_name"]
                    or "Unknown league"
                )

                print(
                    f"   - "
                    f"{team['name']} "
                    f"| ID: {team['id']} "
                    f"| {league}"
                )

    print()
    print("=" * 70)
    print(
        f"Unique:     {found_count}"
    )
    print(
        f"Ambiguous:  {ambiguous_count}"
    )
    print(
        f"Not found:  {not_found_count}"
    )
    print("=" * 70)


if __name__ == "__main__":
    main()

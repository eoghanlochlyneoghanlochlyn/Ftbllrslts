import json
import re
import sys
from pathlib import Path

import requests


BASE_URL = "https://www.fotmob.com/leagues/{league_id}/overview"
OUTPUT_FILE = "teams.json"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/140.0.0.0 Safari/537.36"
    )
}

TIMEOUT = 30


LEAGUES = [
    {
        "name": "Liga Profesional",
        "country": "Argentina",
        "league_id": 112,
    },
    {
        "name": "Serie A",
        "country": "Brazil",
        "league_id": 268,
    },
    {
        "name": "Primera División",
        "country": "Uruguay",
        "league_id": 161,
    },
    {
        "name": "Primera A",
        "country": "Colombia",
        "league_id": 274,
    },
    {
        "name": "Primera División",
        "country": "Chile",
        "league_id": 273,
    },
    {
        "name": "MLS",
        "country": "United States",
        "league_id": 130,
    },
    {
        "name": "Liga MX",
        "country": "Mexico",
        "league_id": 230,
    },
    {
        "name": "Saudi Pro League",
        "country": "Saudi Arabia",
        "league_id": 536,
    },
    {
        "name": "J1 League",
        "country": "Japan",
        "league_id": 223,
    },
    {
        "name": "K League 1",
        "country": "South Korea",
        "league_id": 9080,
    },
    {
        "name": "Qatar Stars League",
        "country": "Qatar",
        "league_id": 535,
    },
    {
        "name": "Pro League",
        "country": "United Arab Emirates",
        "league_id": 538,
    },
    {
        "name": "A-League",
        "country": "Australia",
        "league_id": 113,
    },
    {
        "name": "Persian Gulf Pro League",
        "country": "Iran",
        "league_id": 523,
    },
    {
        "name": "Chinese Super League",
        "country": "China",
        "league_id": 120,
    },
]


def fetch_league_page(league_id):
    url = BASE_URL.format(league_id=league_id)
    print(f"  دریافت: {url}")

    response = requests.get(
        url,
        headers=HEADERS,
        timeout=TIMEOUT,
    )
    response.raise_for_status()
    return response.text


def extract_next_data(html):
    match = re.search(
        r'<script[^>]+id=["\']__NEXT_DATA__["\'][^>]*>(.*?)</script>',
        html,
        re.DOTALL,
    )

    if not match:
        raise ValueError("__NEXT_DATA__ پیدا نشد.")

    raw_json = match.group(1).strip()

    try:
        return json.loads(raw_json)
    except json.JSONDecodeError as exc:
        raise ValueError(
            f"JSON مربوط به __NEXT_DATA__ قابل خواندن نیست: {exc}"
        )


def get_nested(data, path):
    current = data

    for key in path:
        if not isinstance(current, dict):
            return None

        current = current.get(key)

        if current is None:
            return None

    return current


def extract_teams_list(data):
    possible_paths = [
        (
            "props",
            "pageProps",
            "overview",
            "matches",
            "fixtureInfo",
            "teams",
        ),
        (
            "props",
            "pageProps",
            "overview",
            "fixtureInfo",
            "teams",
        ),
        (
            "props",
            "pageProps",
            "overview",
            "teams",
        ),
    ]

    for path in possible_paths:
        teams = get_nested(data, path)

        if isinstance(teams, list) and teams:
            return teams, path

    raise ValueError(
        "لیست teams در هیچ‌کدام از مسیرهای شناخته‌شده پیدا نشد."
    )


def extract_season(data):
    possible_paths = [
        (
            "props",
            "pageProps",
            "overview",
            "season",
        ),
        (
            "props",
            "pageProps",
            "season",
        ),
    ]

    for path in possible_paths:
        season = get_nested(data, path)

        if season:
            return str(season)

    return None


def clean_team_name(name):
    if not isinstance(name, str):
        return ""

    return " ".join(name.split()).strip()


def normalize_team(team):
    if not isinstance(team, dict):
        return None

    team_id = (
        team.get("id")
        or team.get("teamId")
        or team.get("teamID")
    )

    name = (
        team.get("name")
        or team.get("longName")
        or team.get("shortName")
        or team.get("title")
    )

    if team_id is None or not name:
        return None

    name = clean_team_name(name)

    if not name:
        return None

    return {
        "id": str(team_id),
        "name": name,
    }


def deduplicate_teams(teams):
    result = []
    seen_ids = set()

    for team in teams:
        team_id = team["id"]

        if team_id in seen_ids:
            continue

        seen_ids.add(team_id)
        result.append(team)

    return result


def extract_league(league):
    league_name = league["name"]
    country = league["country"]
    league_id = league["league_id"]

    print()
    print("=" * 60)
    print(f"لیگ: {league_name}")
    print(f"کشور: {country}")
    print(f"League ID: {league_id}")
    print("=" * 60)

    html = fetch_league_page(league_id)

    print(f"  حجم صفحه: {len(html):,} کاراکتر")

    data = extract_next_data(html)

    print("  __NEXT_DATA__: OK")

    season = extract_season(data)

    if season:
        print(f"  فصل: {season}")
    else:
        print("  ⚠️ فصل پیدا نشد.")

    teams_raw, path = extract_teams_list(data)

    print(
        "  مسیر تیم‌ها: "
        + ".".join(path)
    )

    teams = []

    for raw_team in teams_raw:
        team = normalize_team(raw_team)

        if team is not None:
            teams.append(team)

    teams = deduplicate_teams(teams)

    print(f"  تعداد تیم استخراج‌شده: {len(teams)}")

    normalized = []

    for team in teams:
        normalized.append(
            {
                "id": team["id"],
                "name": team["name"],
                "country": country,
                "persian": "",
            }
        )

    normalized.sort(
        key=lambda item: item["name"].lower()
    )

    return {
        "league": league_name,
        "country": country,
        "league_id": str(league_id),
        "season": season,
        "teams": normalized,
    }


def print_league_result(result):
    print()
    print(f"--- {result['league']} ({result['country']}) ---")

    for index, team in enumerate(result["teams"], start=1):
        print(
            f"{index:02d}. "
            f"{team['id']:>6} | "
            f"{team['name']}"
        )


def save_results(results):
    output = {
        "leagues": results
    }

    Path(OUTPUT_FILE).write_text(
        json.dumps(
            output,
            ensure_ascii=False,
            indent=4,
        ),
        encoding="utf-8",
    )

    print()
    print("=" * 60)
    print(f"✅ خروجی ذخیره شد: {OUTPUT_FILE}")
    print("=" * 60)


def main():
    results = []

    try:
        for league in LEAGUES:
            result = extract_league(league)

            print_league_result(result)

            results.append(result)

        save_results(results)

        total_teams = sum(
            len(league["teams"])
            for league in results
        )

        print()
        print(
            f"✅ تمام شد. "
            f"تعداد کل تیم‌ها: {total_teams}"
        )

    except Exception as exc:
        print()
        print("=" * 60)
        print("❌ استخراج با خطا متوقف شد.")
        print("=" * 60)
        print(str(exc))

        sys.exit(1)


if __name__ == "__main__":
    main()

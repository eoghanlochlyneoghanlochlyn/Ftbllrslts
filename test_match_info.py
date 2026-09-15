import json
import re
import sys
from pathlib import Path

import requests


BASE_URL = "https://www.fotmob.com/fifaranking/men"
OUTPUT_FILE = "national_teams.json"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/140.0.0.0 Safari/537.36"
    )
}

TIMEOUT = 30


def fetch_ranking_page():
    print(f"  دریافت: {BASE_URL}")

    response = requests.get(
        BASE_URL,
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


def find_national_teams(data):
    found = []

    def walk(value, path=""):
        if isinstance(value, dict):

            team_id = (
                value.get("id")
                or value.get("teamId")
                or value.get("teamID")
            )

            name = (
                value.get("name")
                or value.get("longName")
                or value.get("shortName")
                or value.get("title")
            )

            if team_id is not None and isinstance(name, str):
                name = clean_team_name(name)

                if name:
                    found.append(
                        {
                            "id": str(team_id),
                            "name": name,
                            "path": path,
                        }
                    )

            for key, child in value.items():
                child_path = (
                    f"{path}.{key}"
                    if path
                    else key
                )

                walk(child, child_path)

        elif isinstance(value, list):
            for index, child in enumerate(value):
                child_path = f"{path}[{index}]"
                walk(child, child_path)

    walk(data)

    return found


def extract_ranking_teams(data):
    candidates = find_national_teams(data)

    if not candidates:
        raise ValueError(
            "هیچ تیمی در داده‌های FIFA Ranking پیدا نشد."
        )

    print(
        f"  تعداد رکوردهای تیمی پیدا‌شده: "
        f"{len(candidates)}"
    )

    teams = []

    for candidate in candidates:
        team = normalize_team(candidate)

        if team is not None:
            teams.append(team)

    teams = deduplicate_teams(teams)

    if not teams:
        raise ValueError(
            "بعد از نرمال‌سازی، هیچ تیمی باقی نماند."
        )

    return teams


def build_result(teams):
    normalized = []

    for team in teams:
        normalized.append(
            {
                "id": team["id"],
                "name": team["name"],
                "country": team["name"],
                "persian": "",
            }
        )

    normalized.sort(
        key=lambda item: item["name"].lower()
    )

    return {
        "source": "FotMob FIFA Ranking Men",
        "url": BASE_URL,
        "teams": normalized,
    }


def print_result(result):
    print()
    print("=" * 60)
    print("تیم‌های ملی مردان")
    print("=" * 60)

    for index, team in enumerate(
        result["teams"],
        start=1,
    ):
        print(
            f"{index:03d}. "
            f"{team['id']:>8} | "
            f"{team['name']}"
        )

    print()
    print(
        f"تعداد کل تیم‌های ملی: "
        f"{len(result['teams'])}"
    )


def save_results(result):
    output = {
        "national_teams": result["teams"]
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
    try:
        print("=" * 60)
        print("استخراج تیم‌های ملی از FotMob FIFA Ranking")
        print("=" * 60)

        html = fetch_ranking_page()

        print(
            f"  حجم صفحه: "
            f"{len(html):,} کاراکتر"
        )

        data = extract_next_data(html)

        print("  __NEXT_DATA__: OK")

        teams = extract_ranking_teams(data)

        result = build_result(teams)

        print_result(result)

        save_results(result)

        print()
        print(
            f"✅ تمام شد. "
            f"تعداد کل تیم‌های ملی: "
            f"{len(result['teams'])}"
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

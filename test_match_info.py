import json
import re
from html import unescape
from urllib.parse import urljoin

import requests


MATCH_ID = "5749667"

BASE_URL = "https://www.fotmob.com"
MATCH_URL = f"{BASE_URL}/match/{MATCH_ID}"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/140.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9",
}


TARGET_STATS = [
    "Ball possession",
    "Expected goals (xG)",
    "Total shots",
    "Shots on target",
    "Big chances",
    "Passes",
    "Accurate passes",
    "Yellow cards",
    "Red cards",
]


def clean_text(value):
    if value is None:
        return ""

    value = unescape(str(value))
    value = re.sub(r"\s+", " ", value)
    return value.strip()


def fetch_page(url):
    print(f"Fetching: {url}")

    response = requests.get(
        url,
        headers=HEADERS,
        timeout=30,
        allow_redirects=True,
    )

    print("HTTP status:", response.status_code)
    print("Final URL:", response.url)
    print("Response length:", len(response.text))

    response.raise_for_status()

    return response.text


def extract_next_data(html):
    patterns = [
        r'<script[^>]+id="__NEXT_DATA__"[^>]*>(.*?)</script>',
        r'<script[^>]+id="NEXT_DATA__"[^>]*>(.*?)</script>',
    ]

    for pattern in patterns:
        match = re.search(
            pattern,
            html,
            flags=re.DOTALL | re.IGNORECASE,
        )

        if not match:
            continue

        raw_json = match.group(1).strip()

        try:
            return json.loads(raw_json)
        except json.JSONDecodeError as error:
            print("Could not decode NEXT_DATA:", error)
            return None

    return None


def get_page_props(next_data):
    if not isinstance(next_data, dict):
        return {}

    props = next_data.get("props")

    if not isinstance(props, dict):
        return {}

    page_props = props.get("pageProps")

    if not isinstance(page_props, dict):
        return {}

    return page_props


def get_content(page_props):
    content = page_props.get("content")

    if isinstance(content, dict):
        return content

    return {}


def get_general(page_props):
    general = page_props.get("general")

    if isinstance(general, dict):
        return general

    return {}


def get_team_name(team_data):
    if isinstance(team_data, dict):
        return (
            team_data.get("name")
            or team_data.get("shortName")
            or team_data.get("title")
            or ""
        )

    if isinstance(team_data, str):
        return team_data

    return ""


def extract_team_names(page_props, content):
    general = get_general(page_props)

    home_team = get_team_name(
        general.get("homeTeam")
    )

    away_team = get_team_name(
        general.get("awayTeam")
    )

    if home_team and away_team:
        return home_team, away_team

    # Fallbackهای احتمالی
    general_teams = general.get("teams")

    if isinstance(general_teams, list):
        if len(general_teams) >= 2:
            home_team = get_team_name(
                general_teams[0]
            )

            away_team = get_team_name(
                general_teams[1]
            )

            if home_team and away_team:
                return home_team, away_team

    return "Home", "Away"


def get_all_stats(content):
    stats_root = content.get("stats")

    if not isinstance(stats_root, dict):
        return []

    periods = stats_root.get("Periods")

    if not isinstance(periods, dict):
        return []

    all_period = periods.get("All")

    if not isinstance(all_period, dict):
        return []

    stats = all_period.get("stats")

    if not isinstance(stats, list):
        return []

    return stats


def normalize_title(title):
    title = clean_text(title).lower()

    replacements = {
        "ball possession": "Ball possession",
        "expected goals (xg)": "Expected goals (xG)",
        "total shots": "Total shots",
        "shots": "Total shots",
        "shots on target": "Shots on target",
        "big chances": "Big chances",
        "passes": "Passes",
        "accurate passes": "Accurate passes",
        "yellow cards": "Yellow cards",
        "red cards": "Red cards",
    }

    return replacements.get(
        title,
        clean_text(title),
    )


def extract_value_pair(stat):
    if not isinstance(stat, dict):
        return None

    values = stat.get("stats")

    if not isinstance(values, list):
        return None

    if len(values) < 2:
        return None

    home_value = values[0]
    away_value = values[1]

    if home_value is None or away_value is None:
        return None

    return home_value, away_value


def extract_requested_stats(content):
    groups = get_all_stats(content)

    found = {}

    print()
    print("Number of stat groups:", len(groups))
    print()

    for group in groups:
        if not isinstance(group, dict):
            continue

        group_title = group.get("title") or group.get("key")

        print(f"Stat group: {group_title}")

        stats = group.get("stats")

        if not isinstance(stats, list):
            continue

        for stat in stats:
            if not isinstance(stat, dict):
                continue

            title = stat.get("title") or stat.get("key") or ""
            normalized = normalize_title(title)

            pair = extract_value_pair(stat)

            print(
                f"  - {title!r} "
                f"| key={stat.get('key')!r} "
                f"| values={stat.get('stats')!r}"
            )

            if normalized not in TARGET_STATS:
                continue

            if pair is None:
                continue

            found[normalized] = {
                "home": pair[0],
                "away": pair[1],
                "original_title": title,
                "key": stat.get("key"),
                "format": stat.get("format"),
                "type": stat.get("type"),
            }

    return found


def print_result(
    home_team,
    away_team,
    stats,
):
    print()
    print("=" * 70)
    print("FINAL EXTRACTED RESULT")
    print("=" * 70)
    print()
    print(f"Home: {home_team}")
    print(f"Away: {away_team}")
    print()

    if not stats:
        print("NO REQUESTED STATS WERE FOUND.")
        return

    for stat_name in TARGET_STATS:
        item = stats.get(stat_name)

        if not item:
            print(f"{stat_name}: NOT FOUND")
            continue

        print(
            f"{stat_name}: "
            f"{item['home']} - {item['away']}"
        )

    print()
    print("=" * 70)


def main():
    try:
        html = fetch_page(MATCH_URL)
    except Exception as error:
        print("Could not fetch FotMob page:")
        print(error)
        return

    next_data = extract_next_data(html)

    if not next_data:
        print("NEXT_DATA was not found.")
        return

    page_props = get_page_props(next_data)

    if not page_props:
        print("pageProps was not found.")
        return

    content = get_content(page_props)

    if not content:
        print()
        print("FotMob page has no embedded content.")
        print("The page may require browser hydration.")
        return

    home_team, away_team = extract_team_names(
        page_props,
        content,
    )

    stats = extract_requested_stats(content)

    print_result(
        home_team,
        away_team,
        stats,
    )

    with open(
        "test_team_stats_output.json",
        "w",
        encoding="utf-8",
    ) as file:
        json.dump(
            {
                "match_id": MATCH_ID,
                "home": home_team,
                "away": away_team,
                "stats": stats,
            },
            file,
            ensure_ascii=False,
            indent=2,
        )

    print()
    print(
        "Raw extracted result saved to "
        "test_team_stats_output.json"
    )


if __name__ == "__main__":
    main()

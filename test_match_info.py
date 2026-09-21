import json
import requests
from collections import defaultdict


HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/140.0.0.0 Safari/537.36"
    ),
    "Accept": "application/json,text/plain,*/*",
}

BASE_URL = "https://www.fotmob.com/api/data/leagues"


def fetch_all_leagues():
    response = requests.get(
        "https://www.fotmob.com/api/data/allLeagues",
        headers=HEADERS,
        timeout=30,
    )
    print("allLeagues:", response.status_code)
    response.raise_for_status()
    data = response.json()

    if not isinstance(data, dict):
        raise RuntimeError("allLeagues returned a non-object payload.")

    return data


def collect_leagues(data):
    found = []

    def walk(node):
        if isinstance(node, dict):
            if node.get("id") is not None and node.get("name"):
                found.append({
                    "id": str(node["id"]),
                    "name": node["name"],
                    "pageUrl": node.get("pageUrl"),
                })

            for value in node.values():
                if isinstance(value, (dict, list)):
                    walk(value)

        elif isinstance(node, list):
            for item in node:
                walk(item)

    walk(data)

    unique = {}
    for item in found:
        unique[(item["id"], item["name"], item.get("pageUrl"))] = item

    return list(unique.values())


def fetch_league(league_id, season=None):
    params = {"id": league_id}

    if season:
        params["season"] = season

    response = requests.get(
        BASE_URL,
        params=params,
        headers=HEADERS,
        timeout=45,
    )

    print(
        f"  leagues?id={league_id}"
        f"{'&season=' + str(season) if season else ''}: "
        f"HTTP {response.status_code}"
    )

    if response.status_code != 200:
        return None

    try:
        data = response.json()
    except Exception:
        return None

    return data if isinstance(data, dict) else None


def extract_details(data):
    details = data.get("details")

    if not isinstance(details, dict):
        return {}

    return details


# These competitions are intentionally excluded from previous-season testing.
EXCLUDED_PREVIOUS_SEASON_IDS = {\n    "77", "78", "50", "9806", "44", "290", "289", "297",\n    "10607", "10199",\n}\n\n\nEXCLUDED_PREVIOUS_SEASON_NAMES = {
    "world cup", "fifa club world cup", "euro", "european championship",
    "asian cup", "afc asian cup", "africa cup of nations",
    "african cup of nations", "concacaf gold cup", "copa america",
    "euro qualification", "world cup qualification conmebol",
}


def is_excluded_competition(name):
    if not name:
        return False
    normalized = " ".join(str(name).lower().split())
    if normalized in EXCLUDED_PREVIOUS_SEASON_NAMES:
        return True
    return any(fragment in normalized for fragment in ("qualification", "qualifiers", "qualifying"))


def get_previous_season_candidate(current_season):
    if current_season is None:
        return None
    text = str(current_season).strip()
    if "/" in text:
        parts = text.split("/")
        if len(parts) == 2 and all(part.isdigit() for part in parts):
            start_year = int(parts[0])
            end_year = int(parts[1])
            length = end_year - start_year
            if 0 < length <= 3:
                return f"{start_year - length}/{end_year - length}"
    if text.isdigit() and len(text) == 4:
        return str(int(text) - 1)
    return None


def choose_previous_season(data):
    details = extract_details(data)
    current = details.get("selectedSeason")
    previous = get_previous_season_candidate(current)
    return (str(current).strip() if current is not None else None, previous, [])

def normalize_stage(value):
    if value is None or isinstance(value, (dict, list)):
        return None

    value = str(value).strip()
    return value or None


def stage_key(value):
    text = str(value).strip().lower()

    aliases = {
        "round of 32": "round_of_32",
        "round_of_16": "round_of_16",
        "round of 16": "round_of_16",
        "quarter-final": "quarter_final",
        "quarter final": "quarter_final",
        "quarter_final": "quarter_final",
        "semi-final": "semi_final",
        "semi final": "semi_final",
        "semi_final": "semi_final",
        "final": "final",
        "bronze": "bronze",
    }

    return aliases.get(text, text)


def stage_sort_key(value):
    order = {
        "preliminary round": 1,
        "round_of_32": 10,
        "1/16": 10,
        "round_of_16": 20,
        "1/8": 20,
        "quarter_final": 30,
        "1/4": 30,
        "semi_final": 40,
        "1/2": 40,
        "bronze": 45,
        "final": 50,
    }

    normalized = stage_key(value)
    return (order.get(normalized, 100), normalized)


def collect_stage_values(node, path="root", result=None):
    if result is None:
        result = []

    if isinstance(node, dict):
        for key, value in node.items():
            current_path = f"{path}.{key}"
            key_lower = str(key).lower()

            if key_lower in {
                "stage",
                "round",
                "roundname",
                "stagename",
                "phase",
            }:
                normalized = normalize_stage(value)

                if normalized:
                    result.append({
                        "value": normalized,
                        "path": current_path,
                    })

            if isinstance(value, (dict, list)):
                collect_stage_values(value, current_path, result)

    elif isinstance(node, list):
        for index, value in enumerate(node):
            collect_stage_values(
                value,
                f"{path}[{index}]",
                result,
            )

    return result


def summarize_stages(data):
    mappings = collect_stage_values(data)

    if not mappings:
        return []

    # If a playoff tree exists, prioritize it over ordinary league
    # matchdays/round numbers.
    playoff = [
        item for item in mappings
        if ".playoff." in item["path"].lower()
    ]

    selected = playoff if playoff else mappings

    unique = {}

    for item in selected:
        value = item["value"]
        normalized = stage_key(value)

        if normalized not in unique:
            unique[normalized] = {
                "value": value,
                "path": item["path"],
            }

    return sorted(
        unique.values(),
        key=lambda item: stage_sort_key(item["value"]),
    )


def configured_stage_found(stages, configured_stage):
    if not configured_stage:
        return None

    aliases = {
        "round_of_16": {"round_of_16", "1/8"},
        "quarter_final": {"quarter_final", "1/4"},
        "semi_final": {"semi_final", "1/2"},
        "final": {"final"},
    }

    wanted = aliases.get(
        str(configured_stage).lower(),
        {str(configured_stage).lower()},
    )

    return [
        item["value"]
        for item in stages
        if stage_key(item["value"]) in wanted
    ]


def print_competition_result(
    configured,
    current_data,
    previous_data,
    league_id,
):
    current_details = extract_details(current_data)
    previous_details = extract_details(previous_data)

    current_season, previous_season, seasons = choose_previous_season(
        current_data
    )

    # The second call is explicitly made with the previous season.
    previous_details_season = (
        previous_details.get("selectedSeason")
        or previous_season
    )

    print()
    print("=" * 110)
    print(
        f"COMPETITION {league_id} | "
        f"{current_details.get('name') or previous_details.get('name')!r}"
    )
    print(
        f"  CURRENT SEASON: {current_season!r} | "
        f"PREVIOUS SEASON: {previous_details_season!r}"
    )
    print(
        f"  CONFIG: mode={configured.get('mode')!r} | "
        f"stage={configured.get('stage')!r}"
    )

    if seasons:
        print("  AVAILABLE SEASONS:", ", ".join(seasons))

    stages = summarize_stages(previous_data)

    print("  PREVIOUS-SEASON STAGE STRUCTURE:")

    if not stages:
        print("    NO EXPLICIT STAGE/ROUND STRUCTURE FOUND")
        return False

    for item in stages:
        print(
            f"    {item['value']!r} | {item['path']}"
        )

    found = configured_stage_found(
        stages,
        configured.get("stage"),
    )

    if configured.get("stage"):
        print(
            f"  CONFIGURED START STAGE "
            f"{configured['stage']!r}: "
            f"{found or 'NOT FOUND'}"
        )

    return True


def main():
    with open("auto_matches.json", "r", encoding="utf-8") as file:
        config = json.load(file)

    configured = [
        item
        for item in config.get("competitions", [])
        if item.get("id") is not None
    ]

    print()
    print("=" * 110)
    print("FOTMOB PREVIOUS-SEASON COMPETITION TEST")
    print("=" * 110)
    print(
        "هدف: بررسی ساختار لیگ‌ها و تورنمنت‌ها بر اساس فصل قبلی، "
        "نه فصل جاری."
    )
    print(
        "برای هر competition ابتدا فصل جاری از FotMob خوانده می‌شود، "
        "سپس فصل قبلی از فهرست seasons انتخاب و با پارامتر season "
        "به /api/data/leagues درخواست می‌شود."
    )

    all_leagues = fetch_all_leagues()
    directory = collect_leagues(all_leagues)

    by_id = defaultdict(list)
    for item in directory:
        by_id[item["id"]].append(item)

    print()
    print("Configured competitions:", len(configured))
    print("Global directory entries:", len(directory))

    unresolved = []
    current_failures = []
    previous_failures = []
    no_previous_season = []
    stage_failures = []

    checked = 0

    for configured_item in configured:
        league_id = str(configured_item["id"])

        print()
        print("-" * 110)
        print(
            f"CONFIGURED ID {league_id} | "
            f"mode={configured_item.get('mode')} | "
            f"stage={configured_item.get('stage')}"
        )

        directory_matches = by_id.get(league_id, [])

        if not directory_matches:
            print("  NOT FOUND IN allLeagues")
            unresolved.append(league_id)
            continue

        print(
            "  GLOBAL:",
            " | ".join(
                f"{item['name']} | pageUrl={item.get('pageUrl')}"
                for item in directory_matches
            ),
        )

        competition_name = directory_matches[0].get("name")

        if is_excluded_competition(competition_name, league_id):
            print("  PREVIOUS-SEASON TEST: SKIPPED")
            print("  REASON: excluded national/international competition")
            continue

        current_data = fetch_league(league_id)

        if not current_data:
            current_failures.append(league_id)
            print("  CURRENT SEASON REQUEST FAILED")
            continue

        current_season, previous_season, seasons = choose_previous_season(
            current_data
        )

        print(
            f"  DETECTED CURRENT={current_season!r} | "
            f"PREVIOUS={previous_season!r}"
        )

        if not previous_season:
            no_previous_season.append(league_id)
            print("  NO PREVIOUS SEASON AVAILABLE")
            continue

        previous_data = fetch_league(
            league_id,
            season=previous_season,
        )

        if not previous_data:
            previous_failures.append(league_id)
            print("  PREVIOUS-SEASON REQUEST FAILED")
            continue

        checked += 1

        ok = print_competition_result(
            configured_item,
            current_data,
            previous_data,
            league_id,
        )

        if not ok:
            stage_failures.append(league_id)

    print()
    print("=" * 110)
    print("FINAL RESULT")
    print("=" * 110)
    print("Configured competitions:", len(configured))
    print("Resolved in allLeagues:", len(configured) - len(unresolved))
    print("Previous seasons checked:", checked)
    print("Unresolved:", unresolved or "NONE")
    print("Current-season request failures:", current_failures or "NONE")
    print("Previous-season request failures:", previous_failures or "NONE")
    print("No previous season available:", no_previous_season or "NONE")
    print("No stage structure:", stage_failures or "NONE")

    print()
    print("IMPORTANT:")
    print(
        "این تست فقط برای کشف ساختار واقعی فصل قبلی است. "
        "هیچ تغییری در auto_matches.json یا منطق ربات اعمال نمی‌کند "
        "و هیچ matchDetails برای تک‌تک بازی‌ها صدا زده نمی‌شود."
    )


if __name__ == "__main__":
    main()

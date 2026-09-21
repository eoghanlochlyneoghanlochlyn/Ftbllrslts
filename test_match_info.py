import json
import requests
from collections import defaultdict
from datetime import datetime
from zoneinfo import ZoneInfo


IRAN_TZ = ZoneInfo("Asia/Tehran")

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/140.0.0.0 Safari/537.36"
    ),
    "Accept": "application/json,text/plain,*/*",
}


def fetch_all_leagues():
    url = "https://www.fotmob.com/api/data/allLeagues"

    print("Downloading FotMob global league directory...")
    response = requests.get(url, headers=HEADERS, timeout=30)

    print("Status code:", response.status_code)
    response.raise_for_status()

    data = response.json()

    if not isinstance(data, dict):
        raise RuntimeError("FotMob allLeagues returned a non-object payload.")

    return data


def collect_leagues(data):
    found = []

    def walk(node, country=None, category=None):
        if isinstance(node, dict):
            if (
                node.get("id") is not None
                and node.get("name")
            ):
                found.append({
                    "id": node.get("id"),
                    "name": node.get("name"),
                    "pageUrl": node.get("pageUrl"),
                    "country": country,
                    "category": category,
                    "raw": node,
                })

            for key, value in node.items():
                next_category = category
                if key in ("international", "countries"):
                    next_category = key

                next_country = country
                if key == "name" and category == "countries":
                    next_country = value

                if isinstance(value, (dict, list)):
                    walk(value, next_country, next_category)

        elif isinstance(node, list):
            for item in node:
                walk(item, country, category)

    walk(data)

    unique = {}
    for item in found:
        key = (
            str(item["id"]),
            item["name"],
            item.get("pageUrl"),
        )
        unique[key] = item

    return list(unique.values())


def fetch_league(league_id):
    url = "https://www.fotmob.com/api/data/leagues"

    response = requests.get(
        url,
        params={"id": league_id},
        headers=HEADERS,
        timeout=30,
    )

    print(
        f"  league endpoint id={league_id}: "
        f"HTTP {response.status_code}"
    )

    if response.status_code != 200:
        return None

    try:
        data = response.json()
    except Exception:
        return None

    if not isinstance(data, dict):
        return None

    return data


def extract_details(data):
    details = data.get("details")

    if not isinstance(details, dict):
        return {}

    result = {}
    for key in (
        "id",
        "name",
        "type",
        "selectedSeason",
        "pageUrl",
        "ccode",
        "country",
        "primaryId",
        "parentLeagueId",
    ):
        if key in details:
            result[key] = details[key]

    return result


def _is_stage_key(key):
    key = str(key).lower()
    return any(token in key for token in (
        "stage", "round", "phase", "leg", "matchday", "matchweek"
    ))


def _short_value(value, limit=800):
    if isinstance(value, (dict, list)):
        try:
            text = json.dumps(value, ensure_ascii=False, separators=(",", ":"))
        except Exception:
            text = repr(value)
    else:
        text = repr(value)

    return text if len(text) <= limit else text[:limit] + "...[TRUNCATED]"


def collect_stage_fields(node, path="root", results=None):
    if results is None:
        results = []

    if isinstance(node, dict):
        for key, value in node.items():
            current_path = f"{path}.{key}"

            if _is_stage_key(key):
                results.append((current_path, value))

            if isinstance(value, (dict, list)):
                collect_stage_fields(value, current_path, results)

    elif isinstance(node, list):
        for index, value in enumerate(node):
            collect_stage_fields(value, f"{path}[{index}]", results)

    return results


def print_stage_mapping(data, configured_item, league_id):
    details = extract_details(data)

    print()
    print("-" * 120)
    print(
        f"COMPETITION {league_id} | {details.get('name')!r} | "
        f"configured_stage={configured_item.get('stage')!r} | "
        f"mode={configured_item.get('mode')!r}"
    )

    fields = collect_stage_fields(data)

    if not fields:
        print("  No stage/round/phase/leg/matchday/matchweek fields found.")
        return

    seen = set()

    for path, value in fields:
        rendered = _short_value(value)
        signature = (path, rendered)

        if signature in seen:
            continue

        seen.add(signature)
        print(f"  {path} = {rendered}")


def main():
    with open("auto_matches.json", "r", encoding="utf-8") as file:
        config = json.load(file)

    configured = [
        item for item in config.get("competitions", [])
        if item.get("id") is not None
    ]

    configured_ids = {str(item["id"]) for item in configured}

    print()
    print("=" * 120)
    print("FOTMOB CONFIGURED COMPETITION ID MAPPING TEST")
    print("=" * 120)
    print(
        "Configured IDs:",
        ", ".join(sorted(configured_ids, key=lambda x: (len(x), x))),
    )

    all_leagues = fetch_all_leagues()
    leagues = collect_leagues(all_leagues)

    by_id = defaultdict(list)
    for league in leagues:
        by_id[str(league["id"])].append(league)

    print()
    print("Global league directory entries:", len(leagues))
    print("=" * 120)
    print("CONFIGURED ID -> GLOBAL FOTMOB DIRECTORY")
    print("=" * 120)

    unresolved = []

    for item in configured:
        configured_id = str(item["id"])
        matches = by_id.get(configured_id, [])

        print()
        print(
            f"CONFIGURED {configured_id} | "
            f"mode={item.get('mode')} | "
            f"stage={item.get('stage')} | "
            f"extra_country={item.get('extra_country')} | "
            f"extra_teams={item.get('extra_teams')}"
        )

        if not matches:
            print("  -> NOT FOUND IN allLeagues")
            unresolved.append(configured_id)
            continue

        for match in matches:
            print(
                f"  -> {match['name']} | "
                f"country={match.get('country')} | "
                f"category={match.get('category')} | "
                f"pageUrl={match.get('pageUrl')}"
            )

    print()
    print("=" * 120)
    print("VERIFYING RESOLVED IDs WITH /api/data/leagues")
    print("=" * 120)

    verified = []
    verification_failed = []

    print()
    print("=" * 120)
    print("EXTRACTING STAGE / ROUND STRUCTURE")
    print("=" * 120)

    for item in configured:
        configured_id = str(item["id"])

        if configured_id in unresolved:
            continue

        data = fetch_league(configured_id)

        if not data:
            print(f"  {configured_id} -> FAILED")
            verification_failed.append(configured_id)
            continue

        details = extract_details(data)

        print(
            f"  {configured_id} -> "
            f"name={details.get('name')!r} | "
            f"id={details.get('id')!r} | "
            f"type={details.get('type')!r} | "
            f"season={details.get('selectedSeason')!r}"
        )

        verified.append({
            "configured": item,
            "details": details,
        })

        print_stage_mapping(data, item, configured_id)

    print()
    print("=" * 120)
    print("FINAL RESULT")
    print("=" * 120)
    print("Configured competitions:", len(configured))
    print("Resolved in allLeagues:", len(configured) - len(unresolved))
    print("Verified by league endpoint:", len(verified))
    print("Unresolved:", unresolved or "NONE")
    print("Verification failures:", verification_failed or "NONE")

    print()
    print("NOTE:")
    print(
        "This test does not depend on today's matches. "
        "It uses FotMob's global allLeagues directory, verifies each "
        "configured ID with /api/data/leagues, and recursively prints "
        "stage/round/phase/leg/matchday fields from each competition "
        "payload without calling matchDetails."
    )


if __name__ == "__main__":
    main()

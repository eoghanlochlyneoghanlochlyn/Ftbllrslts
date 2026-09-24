import json
import requests
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed

from match_discovery import (
    build_league_stage_map,
    fetch_match_page_stage,
    load_team_config,
    selection_reasons,
)


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
EXCLUDED_PREVIOUS_SEASON_IDS = {
    "77", "78", "50", "9806", "44", "290", "289", "297",
    "10607", "10199",
}


EXCLUDED_PREVIOUS_SEASON_NAMES = {
    "world cup", "fifa club world cup", "euro", "european championship",
    "asian cup", "afc asian cup", "africa cup of nations",
    "african cup of nations", "concacaf gold cup", "copa america",
    "euro qualification", "world cup qualification conmebol",
}


def is_excluded_competition(name, league_id=None):
    if league_id is not None and str(league_id) in EXCLUDED_PREVIOUS_SEASON_IDS:
        return True

    if not name:
        return False

    normalized = " ".join(str(name).lower().split())

    if normalized in EXCLUDED_PREVIOUS_SEASON_NAMES:
        return True

    return any(
        fragment in normalized
        for fragment in ("qualification", "qualifiers", "qualifying")
    )


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
    return (
        str(current).strip() if current is not None else None,
        previous,
        [],
    )


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

    playoff = [
        item
        for item in mappings
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


# =========================================================
# Exhaustive historical match test helpers
# =========================================================

STAGE_PAGE_WORKERS = 8


def extract_all_matches_for_test(data):
    """Extract every historical fixture from FotMob league payload."""
    if not isinstance(data, dict):
        return []

    candidates = []
    matches = data.get("matches")

    if isinstance(matches, dict):
        for key in ("allMatches", "matches", "fixtures", "all"):
            value = matches.get(key)
            if isinstance(value, list):
                candidates.extend(value)

    for key in ("allMatches", "fixtures"):
        value = data.get(key)
        if isinstance(value, list):
            candidates.extend(value)

    result = []
    seen = set()

    for match in candidates:
        if not isinstance(match, dict):
            continue

        match_id = (
            match.get("id")
            or match.get("matchId")
            or match.get("eventId")
        )
        if match_id is None:
            continue

        match_id = str(match_id)
        if not match_id.isdigit() or match_id in seen:
            continue

        home = match.get("home") or match.get("homeTeam")
        away = match.get("away") or match.get("awayTeam")

        if not isinstance(home, dict) or not isinstance(away, dict):
            continue

        home_id = home.get("id") or home.get("teamId")
        away_id = away.get("id") or away.get("teamId")
        if home_id is None or away_id is None:
            continue

        seen.add(match_id)
        result.append(match)

    return result


def is_finished_for_test(match):
    status = match.get("status")
    if not isinstance(status, dict):
        return False

    if status.get("cancelled") is True:
        return True

    if status.get("finished") is True:
        return True

    reason = status.get("reason")
    if isinstance(reason, dict):
        reason = (
            reason.get("long")
            or reason.get("short")
            or reason.get("key")
        )

    return str(reason or "").strip().lower() in {
        "ft", "aet", "after penalties", "finished", "full-time"
    }


def _season_value(item):
    if isinstance(item, dict):
        for key in (
            "id", "seasonId", "season_id", "value", "season",
            "slug", "name", "title",
        ):
            value = item.get(key)
            if value is not None and str(value).strip():
                return str(value).strip()
        return None

    if item is None:
        return None

    text = str(item).strip()
    return text or None


def _collect_season_candidates(node, result=None):
    """Collect season identifiers from the actual FotMob payload."""
    if result is None:
        result = []

    if isinstance(node, dict):
        for key, value in node.items():
            key_lower = str(key).lower()

            if key_lower in {
                "seasons", "seasonlist", "seasonoptions",
                "availableseasons", "seasonlistitems",
            }:
                if isinstance(value, list):
                    for item in value:
                        season = _season_value(item)
                        if season and season not in result:
                            result.append(season)
                elif isinstance(value, dict):
                    season = _season_value(value)
                    if season and season not in result:
                        result.append(season)
                    for nested in value.values():
                        if isinstance(nested, (dict, list)):
                            _collect_season_candidates(nested, result)

            if isinstance(value, (dict, list)):
                _collect_season_candidates(value, result)

    elif isinstance(node, list):
        for item in node:
            if isinstance(item, (dict, list)):
                _collect_season_candidates(item, result)

    return result


def _season_rank_key(value):
    text = str(value).strip()

    if "/" in text:
        parts = text.split("/")
        if len(parts) == 2 and all(part.isdigit() for part in parts):
            return int(parts[0]), int(parts[1])

    if re.match(r"^(19|20)\\d{2}$", text):
        year = int(text)
        return year, year

    return -1, -1


def _generated_previous_seasons(current_season):
    """Generate plausible prior season labels when FotMob exposes no list."""
    text = str(current_season or "").strip()
    result = []

    if "/" in text:
        parts = text.split("/")
        if len(parts) == 2 and all(part.isdigit() for part in parts):
            start = int(parts[0])
            end = int(parts[1])
            length = end - start
            if 0 < length <= 4:
                for step in range(1, 9):
                    candidate = f"{start - step * length}/{end - step * length}"
                    result.append(candidate)
            return result

    if text.isdigit() and len(text) == 4:
        year = int(text)
        return [str(year - step) for step in range(1, 9)]

    return result


def _is_complete_season_payload(data):
    matches = extract_all_matches_for_test(data)
    if not matches:
        return False, 0, 0

    finished = sum(
        1 for match in matches
        if is_finished_for_test(match)
    )
    return finished == len(matches), len(matches), finished


def find_last_completed_season_test(league_id, current_data):
    details = extract_details(current_data)
    current_season = details.get("selectedSeason")

    discovered = _collect_season_candidates(current_data)
    generated = _generated_previous_seasons(current_season)

    current_text = str(current_season or "").strip()
    candidates = [
        value for value in discovered
        if str(value).strip() and str(value).strip() != current_text
    ]

    candidates.sort(key=_season_rank_key, reverse=True)

    for value in generated:
        if value not in candidates and value != current_text:
            candidates.append(value)

    print(
        f"  SEASON CANDIDATES: {candidates[:20]}"
        + (" ..." if len(candidates) > 20 else "")
    )

    for season in candidates:
        data = fetch_league(league_id, season=season)
        if not data:
            print(f"  SEASON {season}: request failed")
            continue

        complete, total, finished = _is_complete_season_payload(data)

        print(
            f"  SEASON {season}: "
            f"{finished}/{total} finished"
        )

        if complete:
            return season, data

    return None, None


def historical_stage_for_test(match, stage_map):
    match_id = str(
        match.get("id")
        or match.get("matchId")
        or match.get("eventId")
        or ""
    )

    if match_id in stage_map:
        return stage_map[match_id], "league_stage_map"

    home = match.get("home") or match.get("homeTeam") or {}
    away = match.get("away") or match.get("awayTeam") or {}
    home_id = home.get("id") or home.get("teamId")
    away_id = away.get("id") or away.get("teamId")

    if home_id and away_id:
        pair_key = (
            "teams:"
            + "|".join(sorted((str(home_id), str(away_id))))
        )
        if pair_key in stage_map:
            return stage_map[pair_key], "team_pair"

    return None, None


def _fetch_stage_page_test(match_id):
    try:
        return match_id, fetch_match_page_stage(match_id)
    except Exception as error:
        print(f"  STAGE PAGE ERROR {match_id}: {error}")
        return match_id, None


def prefetch_missing_stage_pages(matches, rule, stage_map):
    mode = str(rule.get("mode") or "all").lower()
    if mode not in {"from", "final_only"}:
        return {}

    missing = []
    for match in matches:
        stage, _ = historical_stage_for_test(match, stage_map)
        if stage:
            continue

        match_id = str(match.get("id") or match.get("matchId") or "")
        if match_id:
            missing.append(match_id)

    missing = list(dict.fromkeys(missing))
    if not missing:
        return {}

    print(
        f"  STAGE PAGE FALLBACK: {len(missing)} matches "
        f"(workers={STAGE_PAGE_WORKERS})"
    )

    result = {}
    with ThreadPoolExecutor(max_workers=STAGE_PAGE_WORKERS) as executor:
        futures = {
            executor.submit(_fetch_stage_page_test, match_id): match_id
            for match_id in missing
        }

        for future in as_completed(futures):
            match_id, stage = future.result()
            if stage:
                result[match_id] = normalize_stage(stage)

    print(
        f"  STAGE PAGE RESOLVED: {len(result)}/{len(missing)}"
    )
    return result


def historical_selection_test(
    match,
    rule,
    stage,
    selected_team_ids,
    by_name,
    by_country,
):
    prepared = dict(match)

    # The historical endpoint is already scoped to this competition.
    # Canonicalizing only the temporary test object lets the exact
    # production selection_reasons() logic evaluate this fixture.
    prepared["leagueId"] = str(rule["id"])

    if stage:
        prepared["stage"] = stage

    reasons = selection_reasons(
        prepared,
        {"competitions": [rule]},
        selected_team_ids,
        by_name,
        by_country,
    )

    if reasons:
        return "SELECT", reasons

    mode = str(rule.get("mode") or "all").lower()
    if mode in {"from", "final_only"} and not stage:
        return "INCONCLUSIVE", ["stage_unresolved"]

    return "REJECT", ["no_selection_rule"]


def test_match_label(match):
    home = match.get("home") or {}
    away = match.get("away") or {}
    home_name = home.get("longName") or home.get("name") or "?"
    away_name = away.get("longName") or away.get("name") or "?"
    return (
        f"{home_name} ({home.get('id')}) "
        f"vs {away_name} ({away.get('id')})"
    )

def main():
    with open("auto_matches.json", "r", encoding="utf-8") as file:
        config = json.load(file)

    competitions = config.get("competitions", [])
    selected_team_ids = {
        str(value)
        for value in config.get("team_ids", [])
        if str(value).strip()
    }
    by_name, by_country = load_team_config()

    print()
    print("=" * 120)
    print("FOTMOB EXHAUSTIVE HISTORICAL SELECTION TEST")
    print("=" * 120)
    print(
        "برای هر competition فصل فعلی از FotMob خوانده می‌شود، "
        "آخرین فصل قبلی که تمام مسابقاتش تمام شده پیدا می‌شود، "
        "و تک‌تک بازی‌های آن فصل SELECT/REJECT می‌شوند."
    )
    print(
        "Stage فقط از ساختار واقعی FotMob یا صفحه همان مسابقه "
        "استخراج می‌شود؛ هیچ stageای داخل تست hardcode نشده است."
    )

    summary = {
        "competitions": 0,
        "completed_seasons": 0,
        "matches": 0,
        "selected": 0,
        "rejected": 0,
        "inconclusive": 0,
        "errors": 0,
    }
    failures = []

    for rule in competitions:
        if not isinstance(rule, dict):
            continue

        league_id = str(rule.get("id", "")).strip()
        if not league_id:
            continue

        summary["competitions"] += 1

        print()
        print("#" * 120)
        print(
            f"COMPETITION {league_id} | "
            f"mode={rule.get('mode')} | "
            f"stage={rule.get('stage')}"
        )

        current_data = fetch_league(league_id)
        if not current_data:
            print("  ERROR: current league request failed")
            summary["errors"] += 1
            failures.append((league_id, "current_request_failed"))
            continue

        details = extract_details(current_data)
        print(
            "  CURRENT SEASON:",
            details.get("selectedSeason")
        )

        season, historical_data = (
            find_last_completed_season_test(
                league_id,
                current_data,
            )
        )

        if not historical_data:
            print(
                "  ERROR: no fully completed previous season found"
            )
            summary["errors"] += 1
            failures.append(
                (league_id, "no_completed_previous_season")
            )
            continue

        summary["completed_seasons"] += 1

        matches = extract_all_matches_for_test(
            historical_data
        )
        print(f"  COMPLETED SEASON: {season}")
        print(f"  MATCHES: {len(matches)}")

        if not matches:
            summary["errors"] += 1
            failures.append((league_id, "no_matches"))
            continue

        summary["matches"] += len(matches)

        # Stage is built from the same historical competition payload.
        stage_map = build_league_stage_map(historical_data)
        print(f"  STAGE MAP ENTRIES: {len(stage_map)}")

        page_stage_map = prefetch_missing_stage_pages(
            matches,
            rule,
            stage_map,
        )

        counts = {
            "SELECT": 0,
            "REJECT": 0,
            "INCONCLUSIVE": 0,
        }

        ordered = sorted(
            matches,
            key=lambda match: (
                str(
                    (
                        match.get("status")
                        or {}
                    ).get("utcTime")
                    or match.get("utcTime")
                    or match.get("timeTS")
                    or ""
                ),
                str(
                    match.get("id")
                    or match.get("matchId")
                    or ""
                ),
            ),
        )

        for index, match in enumerate(ordered, 1):
            stage, stage_source = historical_stage_for_test(
                match,
                stage_map,
            )

            if not stage:
                match_id = str(
                    match.get("id")
                    or match.get("matchId")
                    or ""
                )
                if match_id in page_stage_map:
                    stage = page_stage_map[match_id]
                    stage_source = "match_page"

            status, reasons = historical_selection_test(
                match,
                rule,
                stage,
                selected_team_ids,
                by_name,
                by_country,
            )

            counts[status] += 1
            summary[status.lower()] += 1

            print(
                f"  [{index}/{len(ordered)}] "
                f"{match.get('id')} | "
                f"{test_match_label(match)} | "
                f"stage={stage or 'UNKNOWN'} | "
                f"stage_source={stage_source or 'NONE'} | "
                f"{status} | "
                f"reason={','.join(reasons)}"
            )

            if status == "INCONCLUSIVE":
                failures.append(
                    (
                        league_id,
                        str(
                            match.get("id")
                            or match.get("matchId")
                        ),
                        "stage_unresolved",
                    )
                )

        print()
        print(
            f"  SUMMARY {league_id} | "
            f"season={season} | "
            f"matches={len(ordered)} | "
            f"SELECT={counts['SELECT']} | "
            f"REJECT={counts['REJECT']} | "
            f"INCONCLUSIVE={counts['INCONCLUSIVE']}"
        )

    print()
    print("=" * 120)
    print("FINAL SUMMARY")
    print("=" * 120)

    for key, value in summary.items():
        print(f"{key}: {value}")

    if failures:
        print()
        print("FAILURES / INCONCLUSIVE:")
        for failure in failures:
            print("  ", failure)

        raise AssertionError(
            f"Historical exhaustive test failed: "
            f"{len(failures)} unresolved/error case(s)."
        )

    print()
    print(
        "PASS: همه competitionهای تنظیم‌شده و تمام مسابقات "
        "آخرین فصل کامل قبلی بدون stage unresolved بررسی شدند."
    )


if __name__ == "__main__":
    main()

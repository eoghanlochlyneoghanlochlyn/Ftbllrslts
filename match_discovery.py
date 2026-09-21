import json
import os
import re
from datetime import datetime, timedelta, timezone

import requests

from fotmob import extract_next_data, recursive_find


CONFIG_FILE = "auto_matches.json"
MATCHES_FILE = "matches.json"
TEAMS_FILE = "teams.json"

FOTMOB_BASE_URL = "https://www.fotmob.com"
DAILY_MATCHES_URL = "https://www.fotmob.com/api/data/matches"
TIMEOUT = 30

# FotMob playoff labels -> internal normalized labels.
STAGE_ALIASES = {
    "final": "final",
    "finale": "final",
    "third place": "third_place",
    "third-place": "third_place",
    "semi final": "semi_final",
    "semi-final": "semi_final",
    "semifinal": "semi_final",
    "1/2": "semi_final",
    "quarter final": "quarter_final",
    "quarter-final": "quarter_final",
    "quarterfinal": "quarter_final",
    "1/4": "quarter_final",
    "round of 16": "round_of_16",
    "round-of-16": "round_of_16",
    "last 16": "round_of_16",
    "1/8": "round_of_16",
    "round of 32": "round_of_32",
    "round-of-32": "round_of_32",
    "last 32": "round_of_32",
    "1/16": "round_of_32",
    "playoff": "playoff",
    "play-off": "playoff",
    "playoffs": "playoffs",
    "play-offs": "playoffs",
    "knockout stage": "knockout",
    "knockout": "knockout",
    "league phase": "league_phase",
    "group stage": "group_stage",
    "group": "group",
    "regular season": "regular_season",
}

STAGE_RANK = {
    "final": 0,
    "third_place": 1,
    "semi_final": 2,
    "quarter_final": 3,
    "round_of_16": 4,
    "round_of_32": 5,
    "playoff": 6,
    "playoffs": 6,
    "knockout": 7,
    "league_phase": 8,
    "group_stage": 9,
    "group": 9,
    "regular_season": 10,
}


def load_json(path, default):
    if not os.path.exists(path):
        return default

    try:
        with open(path, "r", encoding="utf-8") as file:
            return json.load(file)
    except (OSError, json.JSONDecodeError):
        return default


def save_json(path, data):
    with open(path, "w", encoding="utf-8") as file:
        json.dump(data, file, ensure_ascii=False, indent=2)
        file.write("\n")


def clean_text(value):
    if value is None:
        return ""

    if isinstance(value, (int, float)):
        return str(value)

    return " ".join(str(value).replace("\xa0", " ").split()).strip()


def normalize(value):
    return clean_text(value).lower()


def normalize_stage(value):
    if value is None:
        return None

    text = re.sub(r"\s+", " ", normalize(value))

    if text in STAGE_ALIASES:
        return STAGE_ALIASES[text]

    return text if text in STAGE_RANK else None


def parse_datetime(value):
    if value is None:
        return None

    text = clean_text(value)
    if not text:
        return None

    try:
        return datetime.fromisoformat(
            text.replace("Z", "+00:00")
        ).astimezone(timezone.utc)
    except ValueError:
        pass

    try:
        timestamp = float(text)
        if timestamp > 10_000_000_000:
            timestamp /= 1000
        return datetime.fromtimestamp(timestamp, timezone.utc)
    except (TypeError, ValueError, OSError, OverflowError):
        return None


def fetch_matches_for_date(date_text):
    url = f"{DAILY_MATCHES_URL}?date={date_text}"

    print(f"[DISCOVERY] Fetching daily matches: {date_text}")

    try:
        response = requests.get(
            url,
            headers={
                "User-Agent": (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/140.0.0.0 Safari/537.36"
                ),
                "Accept": "application/json,text/plain,*/*",
                "Accept-Language": "en-US,en;q=0.9",
                "Referer": FOTMOB_BASE_URL + "/",
            },
            timeout=TIMEOUT,
        )
        print(
            f"[DISCOVERY] Daily matches {date_text}: "
            f"HTTP {response.status_code}"
        )
        response.raise_for_status()
        data = response.json()
    except (requests.RequestException, ValueError) as error:
        print(f"[DISCOVERY] Daily matches failed for {date_text}: {error}")
        return []

    if not isinstance(data, dict):
        return []

    result = []

    for league in data.get("leagues", []):
        if not isinstance(league, dict):
            continue

        league_id = (
            league.get("id")
            or league.get("leagueId")
            or league.get("competitionId")
        )
        league_id = str(league_id) if league_id is not None else ""

        league_name = clean_text(
            league.get("name")
            or league.get("title")
            or league.get("shortName")
        )

        matches = league.get("matches", [])
        if not isinstance(matches, list):
            continue

        for match in matches:
            if not isinstance(match, dict):
                continue

            match_id = match.get("id") or match.get("matchId")
            if match_id is None:
                continue

            status = match.get("status")
            if not isinstance(status, dict):
                status = {}

            start_value = (
                status.get("utcTime")
                or match.get("utcTime")
                or match.get("startTime")
                or match.get("matchTimeUTC")
            )
            start_dt = parse_datetime(start_value)

            if start_dt is None:
                continue

            home = match.get("home") or match.get("homeTeam") or {}
            away = match.get("away") or match.get("awayTeam") or {}

            if not isinstance(home, dict):
                home = {}
            if not isinstance(away, dict):
                away = {}

            home_id = home.get("id") or home.get("teamId") or home.get("teamID")
            away_id = away.get("id") or away.get("teamId") or away.get("teamID")

            result.append(
                {
                    "id": str(match_id),
                    "start": start_dt.isoformat(),
                    "home": {
                        "id": str(home_id) if home_id is not None else "",
                        "name": clean_text(
                            home.get("longName")
                            or home.get("name")
                            or home.get("shortName")
                        ),
                    },
                    "away": {
                        "id": str(away_id) if away_id is not None else "",
                        "name": clean_text(
                            away.get("longName")
                            or away.get("name")
                            or away.get("shortName")
                        ),
                    },
                    "leagueId": league_id,
                    "competitionName": league_name,
                    "stage": None,
                    "pageUrl": (
                        match.get("pageUrl")
                        or match.get("url")
                        or f"{FOTMOB_BASE_URL}/match/{match_id}"
                    ),
                    "dailyMatch": match,
                    "dailyLeague": league,
                }
            )

    return result


def extract_page_match(data):
    if not isinstance(data, dict):
        return None

    general = recursive_find(data, {"general"})
    if not isinstance(general, dict):
        return None

    home = general.get("homeTeam") or general.get("home")
    away = general.get("awayTeam") or general.get("away")

    if not isinstance(home, dict) or not isinstance(away, dict):
        return None

    match_id = (
        general.get("matchId")
        or general.get("id")
    )

    if match_id is None:
        return None

    stage = None

    sources = [
        general,
        recursive_find(data, {"tournament"}),
        recursive_find(data, {"league"}),
        recursive_find(data, {"competition"}),
        recursive_find(data, {"uniqueTournament"}),
        recursive_find(data, {"matchFacts"}),
    ]

    for source in sources:
        if not isinstance(source, dict):
            continue

        for key in (
            "stage",
            "stageName",
            "roundName",
            "round",
            "tournamentStage",
            "leagueRoundName",
            "matchRound",
        ):
            value = source.get(key)
            normalized = normalize_stage(value)

            if normalized:
                stage = normalized
                break

        if stage:
            break

    home_id = home.get("id") or home.get("teamId") or home.get("teamID")
    away_id = away.get("id") or away.get("teamId") or away.get("teamID")

    return {
        "id": str(match_id),
        "home": {
            "id": str(home_id) if home_id is not None else "",
            "name": clean_text(
                home.get("longName")
                or home.get("name")
                or home.get("shortName")
            ),
        },
        "away": {
            "id": str(away_id) if away_id is not None else "",
            "name": clean_text(
                away.get("longName")
                or away.get("name")
                or away.get("shortName")
            ),
        },
        "stage": stage,
    }


def fetch_match_page(match):
    match_id = str(match["id"])
    url = match.get("pageUrl") or f"{FOTMOB_BASE_URL}/match/{match_id}"

    try:
        response = requests.get(
            url,
            headers={
                "User-Agent": (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/140.0.0.0 Safari/537.36"
                ),
                "Accept": "text/html,application/xhtml+xml,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.9",
                "Referer": FOTMOB_BASE_URL + "/",
            },
            timeout=TIMEOUT,
            allow_redirects=True,
        )
        response.raise_for_status()
    except requests.RequestException as error:
        print(f"[DISCOVERY] Page failed for {match_id}: {error}")
        return match

    data = extract_next_data(response.text)
    if data is None:
        print(f"[DISCOVERY] No __NEXT_DATA__ for {match_id}")
        return match

    page_match = extract_page_match(data)
    if not page_match:
        print(f"[DISCOVERY] Could not extract page data for {match_id}")
        return match

    # The daily endpoint is authoritative for kickoff time and competition ID.
    # Never replace these with guessed/page-derived values.
    enriched = dict(match)
    enriched["home"] = page_match["home"] or match["home"]
    enriched["away"] = page_match["away"] or match["away"]
    enriched["stage"] = page_match.get("stage")
    return enriched


def load_team_config():
    teams = load_json(TEAMS_FILE, [])

    by_name = {}
    by_country = {}

    if not isinstance(teams, list):
        return by_name, by_country

    for team in teams:
        if not isinstance(team, dict):
            continue

        team_id = team.get("id")
        if team_id is None:
            continue

        team_id = str(team_id)

        for key in ("name", "shortName", "longName"):
            name = normalize(team.get(key))
            if name:
                by_name[name] = team_id

        country = normalize(team.get("country"))
        if country:
            by_country.setdefault(country, set()).add(team_id)

    return by_name, by_country


def configured_extra_team_ids(rule, by_name, by_country):
    result = set()

    extra_teams = rule.get("extra_teams", [])
    if isinstance(extra_teams, list):
        for name in extra_teams:
            team_id = by_name.get(normalize(name))
            if team_id:
                result.add(team_id)

    country = normalize(rule.get("extra_country"))
    if country:
        result.update(by_country.get(country, set()))

    return result


def match_team_ids(match):
    result = set()

    for side_name in ("home", "away"):
        side = match.get(side_name)
        if not isinstance(side, dict):
            continue

        team_id = side.get("id")
        if team_id:
            result.add(str(team_id))

    return result


def selected_by_rule(match, rule, selected_team_ids, by_name, by_country):
    if str(match.get("leagueId")) != str(rule.get("id")):
        return False

    mode = normalize(rule.get("mode") or "all")

    teams = match_team_ids(match)
    rule_teams = (
        set(selected_team_ids)
        | configured_extra_team_ids(rule, by_name, by_country)
    )

    if mode == "all":
        return True

    if mode == "team_only":
        return bool(teams & rule_teams)

    stage = normalize_stage(match.get("stage"))

    if mode == "final_only":
        return stage == "final"

    if mode == "from":
        required = normalize_stage(rule.get("stage"))

        if required is None or stage is None:
            return False

        return (
            STAGE_RANK.get(stage, 999)
            <= STAGE_RANK.get(required, 999)
        )

    return False


def is_selected(match, config, selected_team_ids, by_name, by_country):
    start = parse_datetime(match.get("start"))
    if start is None:
        return False

    iran_tz = timezone(timedelta(hours=3, minutes=30))
    window_start = datetime(
        2026, 9, 20, 0, 0, 0, tzinfo=iran_tz
    ).astimezone(timezone.utc)
    window_end = datetime.now(timezone.utc)

    if start < window_start or start > window_end:
        return False

    if match_team_ids(match) & selected_team_ids:
        return True

    competitions = config.get("competitions", [])
    if not isinstance(competitions, list):
        return False

    for rule in competitions:
        if not isinstance(rule, dict):
            continue

        if selected_by_rule(
            match,
            rule,
            selected_team_ids,
            by_name,
            by_country,
        ):
            return True

    return False


def build_entry(match):
    match_id = str(match["id"])

    return {
        "id": match_id,
        "url": f"{FOTMOB_BASE_URL}/match/{match_id}",
        "enabled": True,
        "auto": True,
        "start": match.get("start"),
    }


def existing_matches():
    value = load_json(MATCHES_FILE, [])

    if isinstance(value, dict):
        value = value.get("matches", [])

    return value if isinstance(value, list) else []


def entry_start(item):
    if not isinstance(item, dict):
        return None

    return parse_datetime(item.get("start"))


def prune_old_auto(matches, hours):
    cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)

    result = []
    removed = 0

    for item in matches:
        if not isinstance(item, dict):
            continue

        if item.get("auto") is not True:
            result.append(item)
            continue

        start = entry_start(item)

        if start is not None and start < cutoff:
            removed += 1
            continue

        result.append(item)

    return result, removed


def merge_matches(existing, discovered):
    by_id = {}

    for item in existing:
        if not isinstance(item, dict):
            continue

        match_id = item.get("id")
        if match_id is not None:
            by_id[str(match_id)] = item

    added = 0
    updated = 0

    for item in discovered:
        match_id = str(item["id"])

        if match_id not in by_id:
            by_id[match_id] = item
            added += 1
            continue

        old = by_id[match_id]

        if old.get("auto") is True:
            changed = False

            for key in ("url", "start"):
                if old.get(key) != item.get(key):
                    old[key] = item.get(key)
                    changed = True

            if changed:
                updated += 1

    return list(by_id.values()), added, updated


def main():
    config = load_json(CONFIG_FILE, {})
    if not isinstance(config, dict):
        raise RuntimeError("auto_matches.json is invalid")

    by_name, by_country = load_team_config()

    selected_team_ids = {
        str(value)
        for value in config.get("team_ids", [])
        if str(value).strip()
    }

    iran_tz = timezone(timedelta(hours=3, minutes=30))
    window_start = datetime(
        2026, 9, 20, 0, 0, 0, tzinfo=iran_tz
    ).astimezone(timezone.utc)
    window_end = datetime.now(timezone.utc)

    print(
        "[DISCOVERY] TEST Window:",
        window_start.isoformat(),
        "->",
        window_end.isoformat(),
    )

    dates = []
    current_date = window_start.date()

    while current_date <= window_end.date():
        dates.append(current_date.strftime("%Y%m%d"))
        current_date += timedelta(days=1)

    all_matches = []

    for date_text in dates:
        all_matches.extend(fetch_matches_for_date(date_text))

    unique_matches = {}

    for match in all_matches:
        match_id = str(match.get("id", ""))
        if match_id and match_id not in unique_matches:
            unique_matches[match_id] = match

    candidates = []

    for match in unique_matches.values():
        start = parse_datetime(match.get("start"))

        if start is None:
            continue

        if window_start <= start <= window_end:
            candidates.append(match)

    candidates.sort(key=lambda item: item.get("start") or "")

    print(
        f"[DISCOVERY] Daily endpoint matches in window: "
        f"{len(candidates)}"
    )

    discovered = []
    seen_ids = set()

    for index, match in enumerate(candidates, 1):
        team_ids = match_team_ids(match)
        direct_team = bool(team_ids & selected_team_ids)

        matching_rules = []

        competitions = config.get("competitions", [])
        if isinstance(competitions, list):
            for rule in competitions:
                if not isinstance(rule, dict):
                    continue

                if str(match.get("leagueId")) == str(rule.get("id")):
                    matching_rules.append(rule)

        if not direct_team and not matching_rules:
            continue

        needs_page = direct_team or any(
            normalize(rule.get("mode") or "all")
            in {"from", "final_only"}
            for rule in matching_rules
        )

        if needs_page:
            home_name = match.get("home", {}).get("name", "")
            away_name = match.get("away", {}).get("name", "")

            print(
                f"[DISCOVERY] Enriching candidate "
                f"{index}/{len(candidates)}: "
                f"{home_name} vs {away_name}"
            )

            match = fetch_match_page(match)

        if not is_selected(
            match,
            config,
            selected_team_ids,
            by_name,
            by_country,
        ):
            continue

        match_id = str(match["id"])

        if match_id in seen_ids:
            continue

        seen_ids.add(match_id)
        discovered.append(build_entry(match))

        print(
            "[DISCOVERED]",
            match_id,
            "|",
            match["home"]["name"],
            "vs",
            match["away"]["name"],
            "|",
            match.get("start"),
            "| competition:",
            match.get("competitionName"),
            "| leagueId:",
            match.get("leagueId"),
            "| stage:",
            match.get("stage"),
        )

    current_matches = existing_matches()

    current_matches, removed = prune_old_auto(
        current_matches,
        float(config.get("prune_auto_after_hours", 6)),
    )

    merged, added, updated = merge_matches(
        current_matches,
        discovered,
    )

    save_json(MATCHES_FILE, merged)

    print("========================================")
    print("[DISCOVERY] Discovered:", len(discovered))
    print("[DISCOVERY] Added:", added)
    print("[DISCOVERY] Updated:", updated)
    print("[DISCOVERY] Removed old auto matches:", removed)
    print("[DISCOVERY] Total matches:", len(merged))
    print("========================================")


if __name__ == "__main__":
    main()

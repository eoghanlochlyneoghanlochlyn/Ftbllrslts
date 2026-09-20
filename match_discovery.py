import json
import os
import re
from datetime import datetime, timedelta, timezone

import requests

BASE_URL = "https://www.fotmob.com/api"
CONFIG_FILE = "auto_matches.json"
MATCHES_FILE = "matches.json"
TEAMS_FILE = "teams.json"
TIMEOUT = 30

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

STAGE_ALIASES = {
    "final": "final",
    "semi final": "semi_final",
    "semi-final": "semi_final",
    "semifinal": "semi_final",
    "quarter final": "quarter_final",
    "quarter-final": "quarter_final",
    "quarterfinal": "quarter_final",
    "round of 16": "round_of_16",
    "round-of-16": "round_of_16",
    "last 16": "round_of_16",
    "1/16": "round_of_16",
    "round of 32": "round_of_32",
    "round-of-32": "round_of_32",
    "last 32": "round_of_32",
    "1/32": "round_of_32",
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


def load_json(path, default):
    if not os.path.exists(path):
        return default

    with open(path, "r", encoding="utf-8") as file:
        try:
            return json.load(file)
        except json.JSONDecodeError:
            return default


def save_json(path, data):
    with open(path, "w", encoding="utf-8") as file:
        json.dump(data, file, ensure_ascii=False, indent=2)
        file.write("\n")


def extract_jsonld(html):
    objects = []

    for block in re.findall(
        r'<script[^>]+type=["']application/ld\\+json["'][^>]*>(.*?)</script>',
        html,
        re.DOTALL | re.IGNORECASE,
    ):
        try:
            data = json.loads(block)
        except json.JSONDecodeError:
            continue

        if isinstance(data, list):
            objects.extend(data)
        else:
            objects.append(data)

    return objects


def extract_match_links(html):
    links = []
    seen = set()

    pattern = re.compile(
        r'href=["']([^"']+/(?:matches|match)/[^"'<#\\s]+)(?:#(\\d+))?["']',
        re.IGNORECASE,
    )

    for match in pattern.finditer(html):
        href = match.group(1)
        fragment_id = match.group(2)

        current_id = fragment_id
        if not current_id:
            id_match = re.search(r'/match(?:es)?/[^/]+/(\\d+)$', href)
            if id_match:
                current_id = id_match.group(1)

        if not current_id or current_id in seen:
            continue

        if href.startswith("/"):
            href = "https://www.fotmob.com" + href

        links.append((current_id, href, match.start()))
        seen.add(current_id)

    return links


def detect_stage(html, position):
    context = re.sub(r"\\s+", " ", html[max(0, position - 5000):position])

    patterns = (
        (r"round\\s+of\\s+16|last\\s+16", "round_of_16"),
        (r"round\\s+of\\s+32|last\\s+32", "round_of_32"),
        (r"quarter[- ]final|quarterfinal", "quarter_final"),
        (r"semi[- ]final|semifinal", "semi_final"),
        (r"third[- ]place", "third_place"),
        (r"final", "final"),
    )

    for pattern, stage in patterns:
        matches = list(re.finditer(pattern, context, re.IGNORECASE))
        if matches:
            return stage

    return None


def fetch_match_page(match_id_value, url, league_id, link_position=None, fixture_html=""):
    try:
        response = requests.get(
            url,
            headers={
                "User-Agent": (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/140.0 Safari/537.36"
                ),
                "Accept": "text/html,application/xhtml+xml",
            },
            timeout=TIMEOUT,
        )
        response.raise_for_status()
    except requests.RequestException as error:
        print(f"[DISCOVERY] Match {match_id_value}: page request failed: {error}")
        return None

    jsonld = extract_jsonld(response.text)

    event = None
    for item in jsonld:
        if isinstance(item, dict):
            item_type = item.get("@type")
            if item_type == "SportsEvent" or (
                isinstance(item_type, list) and "SportsEvent" in item_type
            ):
                event = item
                break

    if event is None:
        return None

    start = event.get("startDate")
    home_data = event.get("homeTeam")
    away_data = event.get("awayTeam")

    if not start or not isinstance(home_data, dict) or not isinstance(away_data, dict):
        return None

    home_name = str(home_data.get("name", "")).strip()
    away_name = str(away_data.get("name", "")).strip()

    team_ids = re.findall(
        r'/teams/(\\d+)(?:/|["?#])',
        response.text,
        re.IGNORECASE,
    )

    home_id = team_ids[0] if len(team_ids) >= 1 else ""
    away_id = team_ids[1] if len(team_ids) >= 2 else ""

    try:
        start_dt = datetime.fromisoformat(
            str(start).replace("Z", "+00:00")
        ).astimezone(timezone.utc)
    except ValueError:
        return None

    stage = detect_stage(
        fixture_html,
        link_position,
    ) if fixture_html and link_position is not None else None

    return {
        "id": str(match_id_value),
        "start": start_dt.isoformat(),
        "home": {
            "id": home_id,
            "name": home_name,
        },
        "away": {
            "id": away_id,
            "name": away_name,
        },
        "leagueId": str(league_id),
        "stage": stage,
        "_league_ids": {str(league_id)},
    }


def fetch_matches(date_value, league_ids):
    result = []
    seen = set()

    for league_id in sorted(league_ids):
        url = f"https://www.fotmob.com/leagues/{league_id}/fixtures"

        try:
            response = requests.get(
                url,
                headers={
                    "User-Agent": (
                        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                        "AppleWebKit/537.36 (KHTML, like Gecko) "
                        "Chrome/140.0 Safari/537.36"
                    ),
                    "Accept": "text/html,application/xhtml+xml",
                },
                timeout=TIMEOUT,
            )
            response.raise_for_status()
        except requests.RequestException as error:
            print(f"[DISCOVERY] League {league_id}: page request failed: {error}")
            continue

        links = extract_match_links(response.text)

        print(
            f"[DISCOVERY] League {league_id}: "
            f"found {len(links)} match links on fixtures page"
        )

        for current_id, match_url, position in links:
            if current_id in seen:
                continue

            item = fetch_match_page(
                current_id,
                match_url,
                league_id,
                position,
                response.text,
            )

            if item is None:
                continue

            start = match_start(item)
            if start is None or start.date() != date_value:
                continue

            seen.add(current_id)
            result.append(item)

        print(
            f"[DISCOVERY] League {league_id} / "
            f"{date_value.isoformat()}: "
            f"{sum(1 for item in result if str(league_id) in item.get('_league_ids', set()))} matches"
        )

    print(
        f"[DISCOVERY] {date_value.isoformat()}: "
        f"found {len(result)} matches from site pages"
    )

    return result


def match_id(match):
    value = match.get("id") if isinstance(match, dict) else None
    return str(value) if value is not None else ""


def team_id(team):
    if not isinstance(team, dict):
        return ""
    value = team.get("id")
    return str(value) if value is not None else ""


def match_team_ids(match):
    return {
        team_id(match.get("home")),
        team_id(match.get("away")),
    } - {""}


def match_start(match):
    stored_start = match.get("start")

    if stored_start:
        try:
            return datetime.fromisoformat(
                str(stored_start).replace("Z", "+00:00")
            ).astimezone(timezone.utc)
        except ValueError:
            pass

    status = match.get("status")
    if isinstance(status, dict) and status.get("utcTime"):
        try:
            return datetime.fromisoformat(
                str(status["utcTime"]).replace("Z", "+00:00")
            ).astimezone(timezone.utc)
        except ValueError:
            pass

    value = match.get("timeTS")
    if value is not None:
        try:
            timestamp = float(value)
            if timestamp > 10_000_000_000:
                timestamp /= 1000
            return datetime.fromtimestamp(timestamp, timezone.utc)
        except (TypeError, ValueError, OSError):
            pass

    return None


def normalize_stage(value):
    if value is None:
        return None

    text = re.sub(r"\s+", " ", str(value).strip().lower())

    if text in STAGE_ALIASES:
        return STAGE_ALIASES[text]

    if text in STAGE_RANK:
        return text

    return None


def get_stage(match):
    values = []

    for key in (
        "tournamentStage",
        "stage",
        "stageName",
        "roundName",
        "round",
        "leagueRoundName",
        "matchRound",
    ):
        value = match.get(key)
        if value is not None:
            values.append(value)

    for value in values:
        stage = normalize_stage(value)
        if stage is not None:
            return stage

    return None


def resolve_team_index():
    teams = load_json(TEAMS_FILE, [])
    by_name = {}
    by_country = {}

    for team in teams:
        if not isinstance(team, dict):
            continue

        team_id_value = team.get("id")
        if team_id_value is None:
            continue

        team_id_value = str(team_id_value)
        name = str(team.get("name", "")).strip().lower()
        country = str(team.get("country", "")).strip().lower()

        if name:
            by_name[name] = team_id_value

        if country:
            by_country.setdefault(country, set()).add(team_id_value)

    return by_name, by_country


def rule_team_ids(rule, by_name, by_country):
    ids = set()

    for name in rule.get("extra_teams", []):
        value = by_name.get(str(name).strip().lower())
        if value:
            ids.add(value)

    country = rule.get("extra_country")
    if country:
        ids.update(
            by_country.get(
                str(country).strip().lower(),
                set(),
            )
        )

    return ids


def rule_matches(match, rule, selected_team_ids, by_name, by_country):
    if str(rule.get("id")) not in match.get("_league_ids", set()):
        return False

    mode = str(rule.get("mode", "all")).lower()
    teams = match_team_ids(match)
    rule_teams = selected_team_ids | rule_team_ids(
        rule,
        by_name,
        by_country,
    )

    if mode == "all":
        return True

    if mode == "team_only":
        return bool(teams & rule_teams)

    stage = get_stage(match)

    if mode == "final_only":
        return stage == "final"

    if mode == "from":
        minimum = normalize_stage(rule.get("stage"))
        if minimum is None or stage is None:
            return False

        return STAGE_RANK.get(stage, 999) <= STAGE_RANK.get(
            minimum,
            999,
        )

    return False


def is_selected(match, config, selected_team_ids, by_name, by_country):
    start = match_start(match)
    if start is None:
        return False

    now = datetime.now(timezone.utc)
    end = now + timedelta(
        hours=float(config.get("window_hours", 24))
    )

    if start < now or start > end:
        return False

    status = match.get("status")
    if isinstance(status, dict):
        if status.get("cancelled") is True:
            return False
        if status.get("finished") is True:
            return False

    if match_team_ids(match) & selected_team_ids:
        return True

    return any(
        rule_matches(
            match,
            rule,
            selected_team_ids,
            by_name,
            by_country,
        )
        for rule in config.get("competitions", [])
        if isinstance(rule, dict)
    )


def build_entry(match):
    current_id = match_id(match)
    start = match_start(match)

    return {
        "id": current_id,
        "url": f"https://www.fotmob.com/match/{current_id}",
        "enabled": True,
        "auto": True,
        "start": (
            start.isoformat()
            if start is not None
            else None
        ),
    }


def merge(existing, discovered):
    by_id = {}

    for item in existing:
        if not isinstance(item, dict):
            continue
        current_id = match_id(item)
        if current_id:
            by_id[current_id] = item

    added = 0

    for item in discovered:
        current_id = match_id(item)
        if not current_id or current_id in by_id:
            continue
        by_id[current_id] = item
        added += 1

    return list(by_id.values()), added


def prune_old_auto(matches, hours):
    cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)
    kept = []
    removed = 0

    for item in matches:
        if not isinstance(item, dict):
            continue

        if item.get("auto") is not True:
            kept.append(item)
            continue

        start = match_start(item)
        if start is not None and start < cutoff:
            removed += 1
        else:
            kept.append(item)

    return kept, removed


def main():
    config = load_json(CONFIG_FILE, {})
    if not isinstance(config, dict):
        raise RuntimeError("Invalid auto_matches.json")

    by_name, by_country = resolve_team_index()

    selected_team_ids = {
        str(value)
        for value in config.get("team_ids", [])
        if str(value).strip()
    }

    now = datetime.now(timezone.utc)
    dates = [now.date(), (now + timedelta(days=1)).date()]

    league_ids = {
        str(rule.get("id"))
        for rule in config.get("competitions", [])
        if isinstance(rule, dict) and rule.get("id") is not None
    }

    all_matches = []
    seen = set()

    for date_value in dates:
        print(f"[DISCOVERY] Fetching {date_value.isoformat()}")
        for item in fetch_matches(date_value, league_ids):
            current_id = match_id(item)
            if current_id and current_id not in seen:
                seen.add(current_id)
                all_matches.append(item)

    discovered = []

    for item in all_matches:
        if not is_selected(
            item,
            config,
            selected_team_ids,
            by_name,
            by_country,
        ):
            continue

        entry = build_entry(item)
        discovered.append(entry)

        home = item.get("home") or {}
        away = item.get("away") or {}

        print(
            "[DISCOVERED]",
            entry["id"],
            "|",
            home.get("name", "?"),
            "vs",
            away.get("name", "?"),
            "|",
            match_start(item),
            "| stage:",
            get_stage(item),
        )

    existing = load_json(MATCHES_FILE, [])
    if isinstance(existing, dict):
        existing = existing.get("matches", [])
    if not isinstance(existing, list):
        existing = []

    existing, removed = prune_old_auto(
        existing,
        float(config.get("prune_auto_after_hours", 6)),
    )

    merged, added = merge(existing, discovered)
    save_json(MATCHES_FILE, merged)

    print("========================================")
    print("[DISCOVERY] Discovered:", len(discovered))
    print("[DISCOVERY] Added:", added)
    print("[DISCOVERY] Removed old auto matches:", removed)
    print("[DISCOVERY] Total matches:", len(merged))
    print("========================================")


if __name__ == "__main__":
    main()

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


def extract_next_data(html):
    if not html:
        return None

    pattern = (
        r"<script[^>]+id=[^>]*__NEXT_DATA__[^>]*>"
        r"(.*?)"
        r"</script\\s*>"
    )

    match = re.search(
        pattern,
        html,
        re.IGNORECASE | re.DOTALL,
    )

    if not match:
        return None

    try:
        return json.loads(match.group(1).strip())
    except Exception:
        return None


def recursive_find(data, keys):
    if not isinstance(keys, (set, list, tuple)):
        keys = {keys}

    if isinstance(data, dict):
        for key, value in data.items():
            if key in keys and value is not None:
                return value

        for value in data.values():
            result = recursive_find(value, keys)
            if result is not None:
                return result

    elif isinstance(data, list):
        for value in data:
            result = recursive_find(value, keys)
            if result is not None:
                return result

    return None


def find_match_ids(html):
    if not html:
        return []

    text = (
        html
        .replace("\\\\/","/")
        .replace("\\\\u002F","/")
        .replace("&quot;", '"')
    )

    patterns = (
        r'"matchId"\\s*[:=]\\s*"?(\\d{5,})',
        r'"matchID"\\s*[:=]\\s*"?(\\d{5,})',
        r'matchId\\s*[:=]\\s*"?(\\d{5,})',
        r'/match/(\\d{5,})',
        r'/matches/[^"\\s<#]+#(\\d{5,})',
    )

    result = []
    seen = set()

    for pattern in patterns:
        for value in re.findall(pattern, text, re.IGNORECASE):
            value = str(value)
            if value not in seen:
                seen.add(value)
                result.append(value)

    return result


def extract_event_jsonld(html):
    if not html:
        return None

    pattern = (
        r'<script[^>]+type=["\\']'
        r'application/ld\\+json'
        r'["\\'][^>]*>'
        r"(.*?)"
        r"</script>"
    )

    for raw in re.findall(
        pattern,
        html,
        re.IGNORECASE | re.DOTALL,
    ):
        try:
            data = json.loads(raw.strip())
        except Exception:
            continue

        objects = data if isinstance(data, list) else [data]

        for item in objects:
            if not isinstance(item, dict):
                continue

            if (
                item.get("@type") == "SportsEvent"
                or (
                    item.get("homeTeam") is not None
                    and item.get("awayTeam") is not None
                )
            ):
                return item

    return None


def build_match_from_page(match_id_value, html):
    data = extract_next_data(html)

    general = None

    if isinstance(data, dict):
        page_props = data.get("props", {}).get("pageProps", {})

        if isinstance(page_props, dict):
            general = page_props.get("general")

        if not isinstance(general, dict):
            general = recursive_find(data, {"general"})

    if isinstance(general, dict):
        home = general.get("homeTeam")
        away = general.get("awayTeam")
        start = (
            general.get("matchTimeUTC")
            or general.get("matchTime")
            or general.get("startTime")
        )

        league_id = (
            general.get("parentLeagueId")
            or general.get("leagueId")
            or general.get("tournamentId")
            or general.get("uniqueTournamentId")
        )

        stage = (
            general.get("tournamentStage")
            or general.get("stage")
            or general.get("round")
        )

        if (
            isinstance(home, dict)
            and isinstance(away, dict)
            and start
        ):
            return {
                "id": str(general.get("matchId") or match_id_value),
                "start": start,
                "home": {
                    "id": home.get("id"),
                    "name": home.get("name") or home.get("longName"),
                },
                "away": {
                    "id": away.get("id"),
                    "name": away.get("name") or away.get("longName"),
                },
                "leagueId": str(league_id) if league_id is not None else "",
                "stage": stage,
                "_league_ids": (
                    {str(league_id)}
                    if league_id is not None
                    else set()
                ),
            }

    event = extract_event_jsonld(html)

    if not isinstance(event, dict):
        return None

    home = event.get("homeTeam")
    away = event.get("awayTeam")
    start = event.get("startDate")

    if not isinstance(home, dict) or not isinstance(away, dict) or not start:
        return None

    return {
        "id": str(match_id_value),
        "start": start,
        "home": {
            "id": None,
            "name": home.get("name", ""),
        },
        "away": {
            "id": None,
            "name": away.get("name", ""),
        },
        "leagueId": "",
        "stage": None,
        "_league_ids": set(),
    }


def fetch_matches(date_value):
    url = "https://www.fotmob.com/matches"

    try:
        response = requests.get(
            url,
            params={"date": date_value.strftime("%Y%m%d")},
            headers={
                "User-Agent": (
                    "Mozilla/5.0 (X11; Linux x86_64) "
                    "AppleWebKit/537.36 "
                    "(KHTML, like Gecko) "
                    "Chrome/140.0.0.0 Safari/537.36"
                ),
                "Accept": (
                    "text/html,application/xhtml+xml,"
                    "application/xml;q=0.9,*/*;q=0.8"
                ),
                "Accept-Language": "en-US,en;q=0.9",
                "Referer": "https://www.fotmob.com/",
            },
            timeout=TIMEOUT,
            allow_redirects=True,
        )
        response.raise_for_status()
    except requests.RequestException as error:
        print(f"[DISCOVERY] Matches page failed: {error}")
        return []

    html = response.text

    print(
        f"[DISCOVERY] Matches page: HTTP {response.status_code}, "
        f"length {len(html)}"
    )

    match_ids = find_match_ids(html)

    print(
        f"[DISCOVERY] {date_value.isoformat()}: "
        f"found {len(match_ids)} match IDs in page"
    )

    result = []
    seen = set()

    for current_id in match_ids:
        if current_id in seen:
            continue

        match_url = f"https://www.fotmob.com/match/{current_id}"

        try:
            match_response = requests.get(
                match_url,
                headers={
                    "User-Agent": (
                        "Mozilla/5.0 (X11; Linux x86_64) "
                        "AppleWebKit/537.36 "
                        "(KHTML, like Gecko) "
                        "Chrome/140.0.0.0 Safari/537.36"
                    ),
                    "Accept": (
                        "text/html,application/xhtml+xml,"
                        "application/xml;q=0.9,*/*;q=0.8"
                    ),
                    "Accept-Language": "en-US,en;q=0.9",
                    "Referer": "https://www.fotmob.com/",
                },
                timeout=TIMEOUT,
                allow_redirects=True,
            )
            match_response.raise_for_status()
        except requests.RequestException as error:
            print(
                f"[DISCOVERY] Match {current_id} page failed: "
                f"{error}"
            )
            continue

        item = build_match_from_page(
            current_id,
            match_response.text,
        )

        if item is None:
            print(
                f"[DISCOVERY] Match {current_id}: "
                "could not extract match data"
            )
            continue

        start = match_start(item)

        if start is None or start.date() != date_value:
            continue

        seen.add(current_id)
        result.append(item)

    print(
        f"[DISCOVERY] {date_value.isoformat()}: "
        f"found {len(result)} matches from site"
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
        for item in fetch_matches(date_value):
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

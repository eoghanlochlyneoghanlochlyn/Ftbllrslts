import json
import os
import re
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta, timezone
from urllib.parse import urlparse

import requests

from fotmob import (
    extract_next_data,
    fetch_match_page,
    get_content,
    recursive_find,
)

CONFIG_FILE = "auto_matches.json"
MATCHES_FILE = "matches.json"
TEAMS_FILE = "teams.json"

SITEMAP_URL = "https://www.fotmob.com/sitemap/en/matches.xml"
FOTMOB_BASE_URL = "https://www.fotmob.com"
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
    "finale": "final",
    "semi final": "semi_final",
    "semi-final": "semi_final",
    "semifinal": "semi_final",
    "quarter final": "quarter_final",
    "quarter-final": "quarter_final",
    "quarterfinal": "quarter_final",
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
    except (TypeError, ValueError, OSError):
        return None


def extract_match_id(data):
    value = recursive_find(
        data,
        {
            "matchId",
            "matchID",
            "match_id",
        },
    )

    if value is None:
        return None

    text = clean_text(value)

    return text if text.isdigit() else None


def fetch_url(url):
    try:
        response = requests.get(
            url,
            headers={
                "User-Agent": (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 "
                    "(KHTML, like Gecko) "
                    "Chrome/131.0.0.0 Safari/537.36"
                ),
                "Accept": (
                    "text/html,application/xhtml+xml,"
                    "application/xml;q=0.9,*/*;q=0.8"
                ),
                "Accept-Language": "en-US,en;q=0.9",
                "Referer": FOTMOB_BASE_URL + "/",
            },
            timeout=TIMEOUT,
            allow_redirects=True,
        )

        response.raise_for_status()
        return response.text

    except requests.RequestException as error:
        print(f"[DISCOVERY] Request failed: {url} -> {error}")
        return None


def xml_root(text):
    if not text:
        return None

    try:
        return ET.fromstring(text)
    except ET.ParseError as error:
        print(f"[DISCOVERY] Invalid sitemap XML: {error}")
        return None


def xml_local_name(tag):
    return tag.rsplit("}", 1)[-1]


def sitemap_locations(text):
    root = xml_root(text)

    if root is None:
        return [], []

    urls = []
    sitemaps = []

    for element in root.iter():
        name = xml_local_name(element.tag)

        if name == "loc" and element.text:
            value = element.text.strip()

            if not value:
                continue

            parent = element.getparent() if hasattr(element, "getparent") else None

            if parent is not None:
                parent_name = xml_local_name(parent.tag)
                if parent_name == "sitemap":
                    sitemaps.append(value)
                elif parent_name == "url":
                    urls.append(value)
                continue

    for container in root:
        container_name = xml_local_name(container.tag)

        if container_name == "sitemap":
            for child in container:
                if xml_local_name(child.tag) == "loc" and child.text:
                    sitemaps.append(child.text.strip())

        elif container_name == "url":
            for child in container:
                if xml_local_name(child.tag) == "loc" and child.text:
                    urls.append(child.text.strip())

    return list(dict.fromkeys(urls)), list(dict.fromkeys(sitemaps))


def fetch_sitemap_urls():
    print(f"[DISCOVERY] Fetching sitemap: {SITEMAP_URL}")

    text = fetch_url(SITEMAP_URL)

    if text is None:
        return []

    urls, child_sitemaps = sitemap_locations(text)

    if urls:
        print(
            f"[DISCOVERY] Match sitemap contains "
            f"{len(urls)} match URLs"
        )
        return urls

    if not child_sitemaps:
        print("[DISCOVERY] Sitemap contains no match URLs.")
        return []

    print(
        f"[DISCOVERY] Sitemap index contains "
        f"{len(child_sitemaps)} child sitemaps"
    )

    all_urls = []

    for index, child_url in enumerate(child_sitemaps, 1):
        print(
            f"[DISCOVERY] Fetching child sitemap "
            f"{index}/{len(child_sitemaps)}"
        )

        child_text = fetch_url(child_url)
        child_urls, _ = sitemap_locations(child_text)

        all_urls.extend(child_urls)

    return list(dict.fromkeys(all_urls))


def sitemap_match_time(url):
    """
    FotMob's match sitemap can append the scheduled UTC time to the
    match code, e.g.:
        .../37gy4p2025-09-04T11:00:00Z
    """
    match = re.search(
        r"(20\d{2}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?Z)",
        url,
    )

    if not match:
        return None

    return parse_datetime(match.group(1))


def extract_page_match(data, fallback_url):
    if not isinstance(data, dict):
        return None

    general = recursive_find(data, {"general"})

    if not isinstance(general, dict):
        return None

    home = (
        general.get("homeTeam")
        or general.get("home")
    )

    away = (
        general.get("awayTeam")
        or general.get("away")
    )

    if not isinstance(home, dict) or not isinstance(away, dict):
        return None

    match_id = (
        general.get("matchId")
        or general.get("id")
        or extract_match_id(data)
    )

    if match_id is None:
        return None

    start = (
        general.get("matchTimeUTC")
        or general.get("matchTime")
        or general.get("startTime")
        or general.get("utcTime")
    )

    start_dt = parse_datetime(start)

    if start_dt is None:
        start_dt = sitemap_match_time(fallback_url)

    competition = recursive_find(
        data,
        {
            "tournament",
            "league",
            "competition",
            "uniqueTournament",
        },
    )

    competition_id = None
    competition_name = ""

    if isinstance(competition, dict):
        for key in (
            "parentLeagueId",
            "parentTournamentId",
            "parentCompetitionId",
            "leagueId",
            "tournamentId",
            "uniqueTournamentId",
            "competitionId",
            "id",
        ):
            if competition.get(key) is not None:
                competition_id = str(competition[key])
                break

        for key in (
            "name",
            "title",
            "shortName",
            "displayName",
            "leagueName",
            "tournamentName",
            "competitionName",
        ):
            if competition.get(key):
                competition_name = clean_text(
                    competition[key]
                )
                break

    if isinstance(competition, dict):
        for key in (
            "parentLeagueId",
            "parentTournamentId",
            "parentCompetitionId",
        ):
            if competition.get(key) is not None:
                competition_id = str(competition[key])
                break

    stage = None

    for source in (
        general,
        competition,
        recursive_find(
            data,
            {
                "matchFacts",
            },
        ),
    ):
        if not isinstance(source, dict):
            continue

        for key in (
            "tournamentStage",
            "stage",
            "stageName",
            "roundName",
            "round",
            "leagueRoundName",
            "matchRound",
        ):
            value = source.get(key)

            if value is None:
                continue

            normalized = normalize_stage(value)

            if normalized:
                stage = normalized
                break

        if stage:
            break

    home_id = (
        home.get("id")
        or home.get("teamId")
        or home.get("teamID")
    )

    away_id = (
        away.get("id")
        or away.get("teamId")
        or away.get("teamID")
    )

    return {
        "id": str(match_id),
        "start": (
            start_dt.isoformat()
            if start_dt is not None
            else None
        ),
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
        "leagueId": (
            competition_id
            if competition_id is not None
            else ""
        ),
        "competitionName": competition_name,
        "stage": stage,
    }


def fetch_match_from_sitemap(url):
    html = fetch_url(url)

    if html is None:
        return None

    data = extract_next_data(html)

    if data is None:
        print(
            f"[DISCOVERY] No __NEXT_DATA__ on match page: {url}"
        )
        return None

    return extract_page_match(data, url)


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

        for key in (
            "name",
            "shortName",
            "longName",
        ):
            name = normalize(team.get(key))

            if name:
                by_name[name] = team_id

        country = normalize(team.get("country"))

        if country:
            by_country.setdefault(
                country,
                set(),
            ).add(team_id)

    return by_name, by_country


def configured_extra_team_ids(
    rule,
    by_name,
    by_country,
):
    result = set()

    for name in rule.get("extra_teams", []):
        team_id = by_name.get(normalize(name))

        if team_id:
            result.add(team_id)

    country = normalize(
        rule.get("extra_country")
    )

    if country:
        result.update(
            by_country.get(
                country,
                set(),
            )
        )

    return result


def match_team_ids(match):
    result = set()

    for side in (
        match.get("home"),
        match.get("away"),
    ):
        if not isinstance(side, dict):
            continue

        value = side.get("id")

        if value:
            result.add(str(value))

    return result


def selected_by_rule(
    match,
    rule,
    selected_team_ids,
    by_name,
    by_country,
):
    configured_competition = str(
        rule.get("id")
    )

    if str(match.get("leagueId")) != configured_competition:
        return False

    mode = normalize(
        rule.get("mode") or "all"
    )

    teams = match_team_ids(match)

    rule_teams = (
        set(selected_team_ids)
        | configured_extra_team_ids(
            rule,
            by_name,
            by_country,
        )
    )

    if mode == "all":
        return True

    if mode == "team_only":
        return bool(teams & rule_teams)

    stage = match.get("stage")

    if mode == "final_only":
        return stage == "final"

    if mode == "from":
        required = normalize_stage(
            rule.get("stage")
        )

        if required is None or stage is None:
            return False

        return (
            STAGE_RANK.get(stage, 999)
            <= STAGE_RANK.get(required, 999)
        )

    return False


def is_selected(
    match,
    config,
    selected_team_ids,
    by_name,
    by_country,
):
    start = parse_datetime(
        match.get("start")
    )

    if start is None:
        return False

    now = datetime.now(timezone.utc)

    window_hours = float(
        config.get("window_hours", 24)
    )

    window_start = datetime(
        2026,
        9,
        20,
        0,
        0,
        0,
        tzinfo=timezone(timedelta(hours=3, minutes=30)),
    ).astimezone(timezone.utc)

    window_end = datetime.now(timezone.utc)

    if start < window_start:
        return False

    if start > window_end:
        return False

    team_ids = match_team_ids(match)

    if team_ids & selected_team_ids:
        return True

    for rule in config.get("competitions", []):
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
    value = load_json(
        MATCHES_FILE,
        [],
    )

    if isinstance(value, dict):
        value = value.get("matches", [])

    return value if isinstance(value, list) else []


def entry_start(item):
    if not isinstance(item, dict):
        return None

    return parse_datetime(
        item.get("start")
    )


def prune_old_auto(
    matches,
    hours,
):
    cutoff = (
        datetime.now(timezone.utc)
        - timedelta(hours=hours)
    )

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


def merge_matches(
    existing,
    discovered,
):
    by_id = {}

    for item in existing:
        if not isinstance(item, dict):
            continue

        match_id = item.get("id")

        if match_id is None:
            continue

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

            for key in (
                "url",
                "start",
            ):
                if old.get(key) != item.get(key):
                    old[key] = item.get(key)
                    changed = True

            if changed:
                updated += 1

    return list(by_id.values()), added, updated


def main():
    config = load_json(
        CONFIG_FILE,
        {},
    )

    if not isinstance(config, dict):
        raise RuntimeError(
            "auto_matches.json is invalid"
        )

    by_name, by_country = load_team_config()

    selected_team_ids = {
        str(value)
        for value in config.get(
            "team_ids",
            [],
        )
        if str(value).strip()
    }

    # Historical test window:
    # 20 September 2026 00:00 Iran time -> current moment.
    # This is intentionally used for testing discovery against a day
    # that already has completed matches.
    test_start = datetime(
        2026,
        9,
        20,
        0,
        0,
        0,
        tzinfo=timezone(timedelta(hours=3, minutes=30)),
    ).astimezone(timezone.utc)

    now = datetime.now(timezone.utc)

    window_start = test_start
    window_end = now

    print(
        "[DISCOVERY] TEST Window:",
        window_start.isoformat(),
        "->",
        window_end.isoformat(),
    )

    sitemap_urls = fetch_sitemap_urls()

    if not sitemap_urls:
        raise RuntimeError(
            "FotMob match sitemap returned no URLs"
        )

    candidates = []

    for url in sitemap_urls:
        scheduled = sitemap_match_time(url)

        if scheduled is None:
            continue

        if scheduled < now:
            continue

        if scheduled > window_end:
            continue

        candidates.append(
            (
                scheduled,
                url,
            )
        )

    candidates.sort(
        key=lambda item: item[0]
    )

    print(
        f"[DISCOVERY] Sitemap candidates in window: "
        f"{len(candidates)}"
    )

    discovered = []
    seen_ids = set()

    for index, (scheduled, url) in enumerate(
        candidates,
        1,
    ):
        print(
            f"[DISCOVERY] Match page "
            f"{index}/{len(candidates)}: "
            f"{scheduled.isoformat()}"
        )

        match = fetch_match_from_sitemap(url)

        if not match:
            continue

        match_id = str(match["id"])

        if match_id in seen_ids:
            continue

        seen_ids.add(match_id)

        if not is_selected(
            match,
            config,
            selected_team_ids,
            by_name,
            by_country,
        ):
            continue

        discovered.append(
            build_entry(match)
        )

        home = match["home"]["name"]
        away = match["away"]["name"]

        print(
            "[DISCOVERED]",
            match_id,
            "|",
            home,
            "vs",
            away,
            "|",
            match.get("start"),
            "| competition:",
            match.get("competitionName"),
            "| leagueId:",
            match.get("leagueId"),
            "| stage:",
            match.get("stage"),
        )

    current = existing_matches()

    current, removed = prune_old_auto(
        current,
        float(
            config.get(
                "prune_auto_after_hours",
                6,
            )
        ),
    )

    merged, added, updated = merge_matches(
        current,
        discovered,
    )

    save_json(
        MATCHES_FILE,
        merged,
    )

    print("========================================")
    print(
        "[DISCOVERY] Discovered:",
        len(discovered),
    )
    print(
        "[DISCOVERY] Added:",
        added,
    )
    print(
        "[DISCOVERY] Updated:",
        updated,
    )
    print(
        "[DISCOVERY] Removed old auto matches:",
        removed,
    )
    print(
        "[DISCOVERY] Total matches:",
        len(merged),
    )
    print("========================================")


if __name__ == "__main__":
    main()

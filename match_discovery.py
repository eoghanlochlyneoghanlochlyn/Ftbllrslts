import json
import os
import re
from datetime import datetime, timedelta, timezone

import requests

from fotmob import extract_next_data, extract_round_info, recursive_find


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

    # Config/tests and some FotMob payloads may already use the
    # canonical internal form (for example round_of_16). Accept
    # those values directly instead of treating them as unknown.
    if text in STAGE_RANK:
        return text

    # Be tolerant of common separator variants while keeping the
    # stage vocabulary closed to STAGE_RANK.
    compact = re.sub(r"[_-]+", " ", text)
    if compact in STAGE_ALIASES:
        return STAGE_ALIASES[compact]

    return None


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

        # FotMob's daily endpoint can expose a temporary/season-specific
        # tournament id in `id`, while the stable competition id used by
        # /api/data/leagues and auto_matches.json is in `primaryId`.
        # Always prefer primaryId so current fixtures match our configured
        # competition rules.
        league_id = (
            league.get("primaryId")
            or league.get("leagueId")
            or league.get("competitionId")
            or league.get("id")
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


def fetch_league_structure(league_id, season=None):
    """
    ساختار کامل رقابت را از endpoint خود لیگ می‌گیرد.
    برای مرحله حذفی، منبع اصلی stage همین ساختار است:
    overview.playoff.rounds[*].stage
    و matchupهای هر round شامل matchId / id هستند.
    """
    league_id = clean_text(league_id)

    if not league_id:
        return None

    url = f"{FOTMOB_BASE_URL}/api/data/leagues?id={league_id}"
    if season:
        url += f"&season={requests.utils.quote(str(season), safe=chr(47))}"

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
            f"[STAGE] League {league_id}: "
            f"HTTP {response.status_code}"
        )
        response.raise_for_status()
        data = response.json()

        return data if isinstance(data, dict) else None

    except (requests.RequestException, ValueError) as error:
        print(
            f"[STAGE] League {league_id}: "
            f"structure fetch failed: {error}"
        )
        return None


def _stage_from_round_value(value):
    if isinstance(value, dict):
        value = (
            value.get("stage")
            or value.get("name")
            or value.get("label")
            or value.get("value")
        )

    return normalize_stage(value)


def _collect_match_ids(node):
    """
    همه شناسه‌های ممکن مسابقه را از یک matchup/round جمع می‌کند.
    """
    result = set()

    if isinstance(node, dict):
        for key in (
            "matchId",
            "matchID",
            "match_id",
            "eventId",
            "eventID",
            "event_id",
            "id",
        ):
            value = node.get(key)

            if value is not None:
                text = clean_text(value)

                if text.isdigit() and len(text) >= 5:
                    result.add(text)

        for key, value in node.items():
            if key in {
                "matchId",
                "matchID",
                "match_id",
                "eventId",
                "eventID",
                "event_id",
                "id",
            }:
                continue

            if isinstance(value, (dict, list)):
                result.update(_collect_match_ids(value))

    elif isinstance(node, list):
        for item in node:
            result.update(_collect_match_ids(item))

    return result


def _team_id_from_node(node):
    if not isinstance(node, dict):
        return None
    for key in ("id", "teamId", "teamID", "team_id"):
        value = node.get(key)
        if value is not None and clean_text(value).isdigit():
            return clean_text(value)
    return None


def _team_pair_key(home_id, away_id):
    if not home_id or not away_id:
        return None
    return "teams:" + "|".join(sorted((str(home_id), str(away_id))))


def _collect_team_pairs(node):
    result = set()
    if isinstance(node, dict):
        home = node.get("home") or node.get("homeTeam") or node.get("home_team")
        away = node.get("away") or node.get("awayTeam") or node.get("away_team")
        key = _team_pair_key(_team_id_from_node(home), _team_id_from_node(away))
        if key:
            result.add(key)
        for value in node.values():
            if isinstance(value, (dict, list)):
                result.update(_collect_team_pairs(value))
    elif isinstance(node, list):
        for item in node:
            result.update(_collect_team_pairs(item))
    return result


def _iter_playoff_rounds(data):
    """
    roundهای واقعی playoff را از ساختار لیگ پیدا می‌کند.
    ساختار مورد انتظار FotMob:
    overview.playoff.rounds[*]
    """
    if not isinstance(data, dict):
        return []

    overview = data.get("overview")
    if not isinstance(overview, dict):
        overview = recursive_find(data, {"overview"})

    if not isinstance(overview, dict):
        return []

    playoff = overview.get("playoff")

    if not isinstance(playoff, dict):
        return []

    rounds = playoff.get("rounds")

    if not isinstance(rounds, list):
        return []

    return [
        item
        for item in rounds
        if isinstance(item, dict)
    ]


def build_league_stage_map(data):
    """
    خروجی:
        {
            "579....": "semi_final",
            "580....": "quarter_final",
            ...
        }

    مرحله فقط از round واقعی رقابت تعیین می‌شود، نه از
    tournamentStage عددی endpoint روزانه و نه از matchRound صفحه مسابقه.
    """
    result = {}

    for round_item in _iter_playoff_rounds(data):
        stage = _stage_from_round_value(
            round_item.get("stage")
        )

        if stage is None:
            continue

        match_ids = set()
        team_pairs = set()

        for key in (
            "matchups",
            "matches",
            "events",
            "fixtures",
            "games",
        ):
            value = round_item.get(key)
            if isinstance(value, (dict, list)):
                match_ids.update(_collect_match_ids(value))
                team_pairs.update(_collect_team_pairs(value))

        if not match_ids:
            match_ids = _collect_match_ids(round_item)
        if not team_pairs:
            team_pairs = _collect_team_pairs(round_item)

        for match_id in match_ids:
            result[str(match_id)] = stage
        for pair_key in team_pairs:
            result[pair_key] = stage

        print(
            f"[STAGE] Round {round_item.get('stage')!r} "
            f"-> {stage} | matches: {len(match_ids)} | "
            f"team_pairs: {len(team_pairs)}"
        )

    return result


def fetch_match_page_stage(match_id):
    """
    آخرین fallback تشخیص مرحله برای مسابقه‌ای که در ساختار
    /api/data/leagues به صورت playoff.rounds موجود نیست.

    خود صفحه مسابقه FotMob برای مسابقات حذفی معمولاً مرحله را
    در داده‌های __NEXT_DATA__ یا متن صفحه دارد؛ بنابراین اینجا
    مرحله را از خود مسابقه می‌خوانیم، نه از tournamentStage عددی
    endpoint روزانه.
    """
    match_id = clean_text(match_id)
    if not match_id:
        return None

    url = f"{FOTMOB_BASE_URL}/match/{match_id}"

    try:
        response = requests.get(
            url,
            headers={
                "User-Agent": (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/140.0.0.0 Safari/537.36"
                ),
                "Accept": "text/html,application/xhtml+xml,*/*",
                "Accept-Language": "en-US,en;q=0.9",
                "Referer": FOTMOB_BASE_URL + "/",
            },
            timeout=TIMEOUT,
        )
        print(
            f"[STAGE-PAGE] Match {match_id}: "
            f"HTTP {response.status_code}"
        )
        response.raise_for_status()
        html = response.text

    except (requests.RequestException, ValueError) as error:
        print(
            f"[STAGE-PAGE] Match {match_id}: "
            f"page fetch failed: {error}"
        )
        return None

    # 1) داده ساختاریافته خود صفحه
    next_data = extract_next_data(html)
    if isinstance(next_data, dict):
        round_info = extract_round_info(next_data)
        if isinstance(round_info, dict):
            for value in (
                round_info.get("raw"),
                round_info.get("name"),
                round_info.get("name_fa"),
            ):
                stage = normalize_stage(value)
                if stage:
                    print(
                        f"[STAGE-PAGE] Match {match_id}: "
                        f"{value!r} -> {stage}"
                    )
                    return stage

    # 2) fallback روی متن/JSON خام صفحه.
    # فقط عبارت‌های صریح مرحله را قبول می‌کنیم؛
    # عددهای عمومی مثل tournamentStage یا round=1 قابل اعتماد نیستند.
    text = clean_text(html)

    # فقط عبارت‌هایی را می‌پذیریم که واقعاً به مرحله مسابقات اشاره
    # می‌کنند. جست‌وجوی \\bFinal\\b به‌تنهایی خطرناک است، چون
    # کلمه final در متن خبری/توضیحات عادی صفحه هم زیاد دیده می‌شود.
    explicit_patterns = (
        (r"\\bRound\\s+of\\s+32\\b", "round_of_32"),
        (r"\\bRound\\s+of\\s+16\\b", "round_of_16"),
        (r"\\bQuarter[- ]?finals?\\b", "quarter_final"),
        (r"\\bSemi[- ]?finals?\\b", "semi_final"),
        (
            r"(?<![A-Za-z])"
            r"(?:Champions League|Europa League|Conference League|"
            r"Asian Champions League|AFC Champions League|"
            r"World Cup|Euro|Copa America|FA Cup|EFL Cup|"
            r"UEFA Nations League)"
            r"\\s+Final\\b",
            "final",
        ),
        (r"\\bFinal Stage\\b", "knockout"),
    )

    for pattern, stage in explicit_patterns:
        if re.search(pattern, text, re.IGNORECASE):
            print(
                f"[STAGE-PAGE] Match {match_id}: "
                f"HTML -> {stage}"
            )
            return stage

    print(
        f"[STAGE-PAGE] Match {match_id}: "
        "no explicit knockout stage found"
    )
    return None


def apply_page_stage_fallback(candidates, config):
    """
    برای رقابت‌های mode=from/final_only که stage map لیگ ندارند
    یا matchId داخل map نیست، مرحله را از صفحه همان مسابقه می‌گیرد.

    این fallback فقط برای competitionهای واقعاً stage-based اجرا
    می‌شود تا برای لیگ‌های عادی درخواست اضافی ایجاد نکند.
    """
    rules_by_competition = configured_competition_rules(config)
    stage_competitions = set()

    for league_id, rules in rules_by_competition.items():
        if any(
            normalize(rule.get("mode") or "all")
            in {"from", "final_only"}
            for rule in rules
        ):
            stage_competitions.add(str(league_id))

    cache = {}

    for match in candidates:
        league_id = clean_text(match.get("leagueId"))

        if league_id not in stage_competitions:
            continue

        if normalize_stage(match.get("stage")) is not None:
            continue

        match_id = clean_text(match.get("id"))
        if not match_id:
            continue

        if match_id not in cache:
            cache[match_id] = fetch_match_page_stage(match_id)

        stage = cache[match_id]
        if stage:
            match["stage"] = stage

    return candidates


def configured_competition_rules(config):
    """
    قوانین رقابت‌ها را مستقیماً از auto_matches.json می‌خواند.

    نکته مهم:
    ساختار یک رقابت نباید از لیست مسابقات روزانه کشف شود؛
    ممکن است آن رقابت در بازه فعلی هیچ مسابقه‌ای نداشته باشد.
    """
    result = {}

    competitions = config.get("competitions", [])
    if not isinstance(competitions, list):
        return result

    for rule in competitions:
        if not isinstance(rule, dict):
            continue

        league_id = clean_text(rule.get("id"))
        if league_id:
            result.setdefault(league_id, []).append(rule)

    return result


def build_stage_cache(config):
    """
    ساختار playoff فقط برای رقابت‌هایی خوانده می‌شود که در
    auto_matches.json تعریف شده‌اند و واقعاً به stage نیاز دارند.

    بنابراین:
    - وجود مسابقه در endpoint روزانه شرط خواندن ساختار نیست.
    - لیگ‌های عادی و mode=all/team_only اصلاً درخواست stage نمی‌گیرند.
    - برای هر competition فقط یک درخواست /api/data/leagues داریم.
    """
    cache = {}
    rules_by_competition = configured_competition_rules(config)

    stage_league_ids = []

    for league_id, rules in rules_by_competition.items():
        needs_stage = any(
            normalize(rule.get("mode") or "all")
            in {"from", "final_only"}
            for rule in rules
        )

        if needs_stage:
            stage_league_ids.append(league_id)

    print(
        f"[STAGE] Building playoff stage cache for "
        f"{len(stage_league_ids)} configured stage competitions"
    )

    for league_id in stage_league_ids:
        rules = rules_by_competition.get(league_id, [])
        data = fetch_league_structure(league_id)

        if not data:
            print(
                f"[STAGE] League {league_id}: "
                "structure unavailable"
            )
            continue

        mapping = build_league_stage_map(data)

        if mapping:
            cache[league_id] = mapping
            print(
                f"[STAGE] League {league_id}: "
                f"{len(mapping)} match-stage mappings"
            )
        else:
            print(
                f"[STAGE] No playoff structure for competition "
                f"{league_id}"
            )

    return cache


def apply_stage_cache(match, stage_cache):
    league_id = clean_text(match.get("leagueId"))
    match_id = clean_text(match.get("id"))

    mapping = stage_cache.get(league_id, {})

    if match_id in mapping:
        match["stage"] = mapping[match_id]
        return match

    home_id = clean_text((match.get("home") or {}).get("id"))
    away_id = clean_text((match.get("away") or {}).get("id"))
    pair_key = _team_pair_key(home_id, away_id)
    if pair_key and pair_key in mapping:
        match["stage"] = mapping[pair_key]

    return match


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


def selection_reasons(match, config, selected_team_ids, by_name, by_country):
    """Independent OR rules: global teams, competition-wide, stage, extras."""
    reasons = []
    teams = match_team_ids(match)

    if teams & set(selected_team_ids):
        reasons.append("selected_team")

    for rule in config.get("competitions", []):
        if not isinstance(rule, dict):
            continue
        if str(match.get("leagueId")) != str(rule.get("id")):
            continue

        mode = normalize(rule.get("mode") or "all")
        extras = configured_extra_team_ids(rule, by_name, by_country)

        # Extra teams are unconditional *within this competition*.
        # This preserves Brazil/Argentina in all Copa America rounds,
        # and Iranian teams in all AFC rounds.
        if teams & extras:
            reasons.append("extra_team:" + str(rule.get("id")))

        if mode == "all":
            reasons.append("competition_all:" + str(rule.get("id")))
        elif mode == "team_only":
            if teams & (set(selected_team_ids) | extras):
                reasons.append("competition_team:" + str(rule.get("id")))
        elif mode in {"from", "final_only"}:
            stage = normalize_stage(match.get("stage"))
            required = (
                "final" if mode == "final_only"
                else normalize_stage(rule.get("stage"))
            )
            # Unknown stage must never be accepted by a stage rule.
            # Do not interpret group/league phases as knockout rounds.
            knockout = {
                "round_of_32", "round_of_16", "quarter_final",
                "semi_final", "final", "third_place",
            }
            if mode == "final_only" and stage == "final":
                reasons.append("competition_final:" + str(rule.get("id")))
            elif (
                mode == "from"
                and stage in knockout
                and required in knockout
                and STAGE_RANK[stage] <= STAGE_RANK[required]
            ):
                reasons.append("competition_stage:" + str(rule.get("id")))

    return list(dict.fromkeys(reasons))


def selected_by_rule(match, rule, selected_team_ids, by_name, by_country):
    if str(match.get("leagueId")) != str(rule.get("id")):
        return False
    return bool(selection_reasons(
        match, {"competitions": [rule]}, set(),
        by_name, by_country,
    ))


def is_selected(match, config, selected_team_ids, by_name, by_country):
    start = parse_datetime(match.get("start"))
    if start is None:
        return False

    now_utc = datetime.now(timezone.utc)
    try:
        hours = float(config.get("window_hours", 24))
    except (TypeError, ValueError):
        hours = 24
    if hours <= 0:
        hours = 24
    if not now_utc <= start <= now_utc + timedelta(hours=hours):
        return False

    return bool(selection_reasons(
        match, config, selected_team_ids, by_name, by_country,
    ))


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
    now_utc = datetime.now(timezone.utc)

    # بازه واقعی discovery باید از «الان» تا window_hours آینده باشد.
    # بازه قبلی که از 2026-09-20 تا زمان اجرا بود صرفاً برای تست
    # تاریخی بود و باعث می‌شد مسابقات آینده اصلاً وارد matches.json نشوند.
    window_hours = config.get("window_hours", 24)

    try:
        window_hours = float(window_hours)
    except (TypeError, ValueError):
        window_hours = 24

    if window_hours <= 0:
        window_hours = 24

    window_start = now_utc
    window_end = now_utc + timedelta(hours=window_hours)

    print(
        "[DISCOVERY] Window:",
        window_start.isoformat(),
        "->",
        window_end.isoformat(),
        f"({window_hours:g}h)",
    )

    dates = []
    current_date = window_start.astimezone(iran_tz).date()
    last_date = window_end.astimezone(iran_tz).date()

    while current_date <= last_date:
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

    # دیباگ کامل payload روزانه قبل از هرگونه انتخاب.
    # این لاگ عمداً همه مسابقات بازه را چاپ می‌کند تا مشخص شود
    # کدام competition/team در payload واقعی FotMob دیده شده و
    # چرا یک مسابقه بعداً انتخاب یا رد می‌شود.
    for index, match in enumerate(candidates, 1):
        teams = match_team_ids(match)
        direct_team = bool(teams & selected_team_ids)
        matching_rules = [
            rule for rule in config.get("competitions", [])
            if isinstance(rule, dict)
            and str(match.get("leagueId")) == str(rule.get("id"))
        ]
        print(
            "[RAW-MATCH]",
            index,
            "| id:", match.get("id"),
            "| competition:", match.get("competitionName"),
            "| leagueId:", match.get("leagueId"),
            "| home:", match.get("home", {}).get("name"),
            "(", match.get("home", {}).get("id"), ")",
            "| away:", match.get("away", {}).get("name"),
            "(", match.get("away", {}).get("id"), ")",
            "| direct_selected_team:", direct_team,
            "| configured_rules:", [
                {
                    "id": rule.get("id"),
                    "mode": rule.get("mode"),
                    "stage": rule.get("stage"),
                    "extra_teams": rule.get("extra_teams"),
                    "extra_country": rule.get("extra_country"),
                }
                for rule in matching_rules
            ],
        )

    # ساختار مرحله را از خود competitionهای تعریف‌شده در
    # auto_matches.json می‌گیریم، نه از competitionهایی که
    # اتفاقاً در endpoint مسابقات روزانه ظاهر شده‌اند.
    #
    # این بخش عمداً مستقل از candidates است؛ بنابراین اگر مثلاً
    # جام حذفی امروز هیچ مسابقه‌ای نداشته باشد، باز هم ساختار
    # آن رقابت برای تشخیص مرحله بازی‌های آینده در دسترس است.
    stage_cache = build_stage_cache(config)

    # مرحله مسابقات را قبل از اعمال mode=from/final_only تزریق می‌کنیم.
    for match in candidates:
        apply_stage_cache(match, stage_cache)

    # بعضی رقابت‌ها (مثل UEFA/FIFA/AFC یا تورنمنت‌های ملی)
    # در endpoint لیگِ فصل جاری هنوز overview.playoff.rounds ندارند،
    # اما صفحه خود مسابقه مرحله را صریحاً اعلام می‌کند.
    candidates = apply_page_stage_fallback(
        candidates,
        config,
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

        # stage را از ساختار خود competition تعیین می‌کنیم.
        # فقط برای مسابقات کاندید انجام می‌شود و برای هر leagueId
        # فقط یک درخواست زده می‌شود.
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
        print("[SELECT-REASONS]", match_id, selection_reasons(
            match, config, selected_team_ids, by_name, by_country,
        ))

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

import json
import re
from datetime import datetime, timezone
from urllib.parse import urlparse
from zoneinfo import ZoneInfo

import requests


# =========================================================
# تنظیمات
# =========================================================

IRAN_TIMEZONE = ZoneInfo("Asia/Tehran")

FOTMOB_BASE_URL = "https://www.fotmob.com"

FOTMOB_API_URL = (
    "https://www.fotmob.com/api/matchDetails"
)

FOTMOB_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 "
        "(KHTML, like Gecko) "
        "Chrome/131.0.0.0 Safari/537.36"
    ),
    "Accept": (
        "application/json,text/plain,*/*"
    ),
    "Accept-Language": (
        "en-US,en;q=0.9"
    ),
    "Referer": (
        "https://www.fotmob.com/"
    ),
    "Cache-Control": "no-cache",
    "Pragma": "no-cache",
}


# =========================================================
# ابزارهای عمومی
# =========================================================

def clean_text(value):
    if value is None:
        return ""

    if isinstance(value, (int, float)):
        return str(value)

    if not isinstance(value, str):
        return str(value)

    value = re.sub(
        r"<[^>]+>",
        "",
        value,
    )

    value = (
        value
        .replace("\xa0", " ")
        .replace("\u200b", "")
        .replace("\r", " ")
        .replace("\n", " ")
    )

    return " ".join(
        value.split()
    ).strip()


def get_nested(data, *keys):
    current = data

    for key in keys:
        if not isinstance(
            current,
            dict,
        ):
            return None

        current = current.get(key)

    return current


def recursive_find(data, target_keys):
    if not isinstance(
        target_keys,
        (list, tuple, set),
    ):
        target_keys = {
            target_keys
        }

    if isinstance(data, dict):

        for key, value in data.items():

            if key in target_keys:
                if value is not None:
                    return value

        for value in data.values():

            result = recursive_find(
                value,
                target_keys,
            )

            if result is not None:
                return result

    elif isinstance(data, list):

        for item in data:

            result = recursive_find(
                item,
                target_keys,
            )

            if result is not None:
                return result

    return None


def find_section(data, section_name):
    if not isinstance(
        data,
        dict,
    ):
        return None

    if section_name in data:
        return data[section_name]

    return recursive_find(
        data,
        {section_name},
    )


# =========================================================
# Match ID
# =========================================================

def extract_match_id(value):

    if value is None:
        return None

    if isinstance(
        value,
        int,
    ):
        return str(value)

    value = str(
        value
    ).strip()

    if value.isdigit():
        return value

    patterns = [
        r"[#/]([0-9]{5,})",
        r"match(?:Id)?[=/]([0-9]{5,})",
        r"([0-9]{5,})",
    ]

    for pattern in patterns:

        match = re.search(
            pattern,
            value,
            re.IGNORECASE,
        )

        if match:
            return match.group(1)

    return None


# =========================================================
# دریافت API
# =========================================================

def fetch_match_api(match_id):

    match_id = extract_match_id(
        match_id
    )

    if not match_id:
        return None

    try:

        response = requests.get(
            FOTMOB_API_URL,
            params={
                "matchId": match_id,
            },
            headers=FOTMOB_HEADERS,
            timeout=30,
        )

        print(
            f"FotMob {match_id}: "
            f"API HTTP {response.status_code}"
        )

        if response.status_code != 200:
            return None

        data = response.json()

        if not isinstance(
            data,
            dict,
        ):
            return None

        return data

    except Exception as error:

        print(
            f"FotMob {match_id}: "
            f"API error: {error}"
        )

        return None


# =========================================================
# دریافت صفحه
# =========================================================

def fetch_match_page(match_id):

    match_id = extract_match_id(
        match_id
    )

    if not match_id:
        return None

    url = (
        f"{FOTMOB_BASE_URL}/match/"
        f"{match_id}"
    )

    try:

        response = requests.get(
            url,
            headers=FOTMOB_HEADERS,
            timeout=30,
        )

        print(
            f"FotMob {match_id}: "
            f"Page HTTP {response.status_code}"
        )

        print(
            f"FotMob {match_id}: "
            f"Final URL = {response.url}"
        )

        print(
            f"FotMob {match_id}: "
            f"Response length = "
            f"{len(response.text)}"
        )

        if response.status_code != 200:
            return None

        return response.text

    except Exception as error:

        print(
            f"FotMob {match_id}: "
            f"Page error: {error}"
        )

        return None


# =========================================================
# __NEXT_DATA__
# =========================================================

def extract_next_data(html):

    if not html:
        return None

    patterns = [
        (
            r'<script[^>]+id=["\']'
            r'__NEXT_DATA__["\'][^>]*>'
            r"(.*?)"
            r"</script>"
        ),
        (
            r'<script[^>]+id=["\']'
            r'__NEXT_DATA__["\'][^>]*>'
            r"(.*?)"
            r"</script\s*>"
        ),
    ]

    for pattern in patterns:

        match = re.search(
            pattern,
            html,
            re.IGNORECASE | re.DOTALL,
        )

        if not match:
            continue

        raw = match.group(1).strip()

        try:
            return json.loads(
                raw
            )

        except Exception:
            continue

    return None


# =========================================================
# JSON-LD
# =========================================================

def extract_event_jsonld(html):

    if not html:
        return None

    pattern = (
        r'<script[^>]+type=["\']'
        r'application/ld\+json'
        r'["\'][^>]*>'
        r"(.*?)"
        r"</script>"
    )

    matches = re.findall(
        pattern,
        html,
        re.IGNORECASE | re.DOTALL,
    )

    for raw in matches:

        try:

            data = json.loads(
                raw.strip()
            )

            if isinstance(
                data,
                dict,
            ):

                if (
                    data.get("@type") == "SportsEvent"
                    or
                    data.get("homeTeam")
                    or
                    data.get("awayTeam")
                ):
                    return data

            if isinstance(
                data,
                list,
            ):

                for item in data:

                    if not isinstance(
                        item,
                        dict,
                    ):
                        continue

                    if (
                        item.get("@type")
                        == "SportsEvent"
                        or item.get("homeTeam")
                        or item.get("awayTeam")
                    ):
                        return item

        except Exception:
            continue

    return None


# =========================================================
# content
# =========================================================

def get_content(data):

    if not isinstance(
        data,
        dict,
    ):
        return None

    if isinstance(
        data.get("content"),
        dict,
    ):
        return data["content"]

    paths = [
        (
            "props",
            "pageProps",
            "content",
        ),
        (
            "props",
            "pageProps",
            "data",
            "content",
        ),
        (
            "props",
            "pageProps",
            "match",
            "content",
        ),
        (
            "props",
            "pageProps",
            "matchData",
        ),
        (
            "props",
            "pageProps",
            "data",
        ),
        (
            "pageProps",
            "content",
        ),
    ]

    for path in paths:

        value = get_nested(
            data,
            *path,
        )

        if isinstance(
            value,
            dict,
        ):
            return value

    return None


# =========================================================
# اطلاعات پایه
# =========================================================

def _get_team_name(team):

    if not isinstance(
        team,
        dict,
    ):
        return ""

    for key in (
        "longName",
        "name",
        "shortName",
        "title",
    ):

        value = team.get(
            key
        )

        if value:
            return clean_text(
                value
            )

    return ""


def _get_team_id(team):

    if not isinstance(
        team,
        dict,
    ):
        return None

    return (
        team.get("id")
        or team.get("teamId")
        or team.get("teamID")
    )


def extract_basic_info(data):

    if not isinstance(
        data,
        dict,
    ):
        return {}

    general = data.get(
        "general"
    )

    if not isinstance(
        general,
        dict,
    ):
        general = {}

    header = data.get(
        "header"
    )

    if not isinstance(
        header,
        dict,
    ):
        header = {}

    page_props = get_nested(
        data,
        "props",
        "pageProps",
    )

    if not isinstance(
        page_props,
        dict,
    ):
        page_props = {}

    page_general = page_props.get(
        "general"
    )

    if not isinstance(
        page_general,
        dict,
    ):
        page_general = {}

    home = (
        general.get("homeTeam")
        or page_general.get("homeTeam")
        or header.get("homeTeam")
    )

    away = (
        general.get("awayTeam")
        or page_general.get("awayTeam")
        or header.get("awayTeam")
    )

    if not isinstance(
        home,
        dict,
    ):
        home = {}

    if not isinstance(
        away,
        dict,
    ):
        away = {}

    home_name = _get_team_name(
        home
    )

    away_name = _get_team_name(
        away
    )

    home_id = _get_team_id(
        home
    )

    away_id = _get_team_id(
        away
    )

    event_jsonld = get_nested(
        page_props,
        "seo",
        "eventJSONLD",
    )

    if isinstance(
        event_jsonld,
        dict,
    ):

        if not home_name:

            jsonld_home = (
                event_jsonld.get(
                    "homeTeam"
                )
            )

            home_name = _get_team_name(
                jsonld_home
            )

        if not away_name:

            jsonld_away = (
                event_jsonld.get(
                    "awayTeam"
                )
            )

            away_name = _get_team_name(
                jsonld_away
            )

        if not home_id:

            jsonld_home = (
                event_jsonld.get(
                    "homeTeam"
                )
            )

            home_id = _get_team_id(
                jsonld_home
            )

        if not away_id:

            jsonld_away = (
                event_jsonld.get(
                    "awayTeam"
                )
            )

            away_id = _get_team_id(
                jsonld_away
            )

    if not home_name:

        home_name = clean_text(
            recursive_find(
                data,
                {
                    "homeTeamName",
                },
            )
            or ""
        )

    if not away_name:

        away_name = clean_text(
            recursive_find(
                data,
                {
                    "awayTeamName",
                },
            )
            or ""
        )

    league = ""

    tournament = (
        general.get("tournament")
        or general.get("league")
        or page_general.get("tournament")
        or page_general.get("league")
    )

    if isinstance(
        tournament,
        dict,
    ):

        league = (
            tournament.get("name")
            or tournament.get("title")
            or ""
        )

    elif isinstance(
        tournament,
        str,
    ):
        league = tournament

    if not league:

        league = (
            recursive_find(
                data,
                {
                    "leagueName",
                    "tournamentName",
                },
            )
            or ""
        )

    start = (
        general.get(
            "matchTimeUTCDate"
        )
        or general.get(
            "matchTimeUTC"
        )
        or general.get(
            "startDate"
        )
        or page_general.get(
            "matchTimeUTCDate"
        )
        or page_general.get(
            "matchTimeUTC"
        )
        or page_general.get(
            "startDate"
        )
    )

    if not start and isinstance(
        event_jsonld,
        dict,
    ):

        start = event_jsonld.get(
            "startDate"
        )

    if not start:

        start = recursive_find(
            data,
            {
                "matchTimeUTCDate",
                "startDate",
                "utcTime",
            },
        )

    return {
        "home_name": clean_text(
            home_name
        ),
        "away_name": clean_text(
            away_name
        ),
        "home_id": home_id,
        "away_id": away_id,
        "league": clean_text(
            league
        ),
        "start": start,
    }


# =========================================================
# زمان
# =========================================================

def parse_datetime(value):

    if value is None:
        return None

    if isinstance(
        value,
        datetime,
    ):

        if value.tzinfo is None:
            return value.replace(
                tzinfo=timezone.utc
            )

        return value

    if isinstance(
        value,
        (int, float),
    ):

        try:

            if value > 100000000000:
                value /= 1000

            return datetime.fromtimestamp(
                value,
                tz=timezone.utc,
            )

        except Exception:
            return None

    value = str(
        value
    ).strip()

    if not value:
        return None

    value = value.replace(
        "Z",
        "+00:00",
    )

    try:

        result = datetime.fromisoformat(
            value
        )

        if result.tzinfo is None:
            result = result.replace(
                tzinfo=timezone.utc
            )

        return result

    except Exception:
        pass

    formats = [
        "%Y-%m-%dT%H:%M:%S.%fZ",
        "%Y-%m-%dT%H:%M:%SZ",
        "%Y-%m-%dT%H:%M:%S",
    ]

    for fmt in formats:

        try:

            return datetime.strptime(
                value,
                fmt,
            ).replace(
                tzinfo=timezone.utc
            )

        except Exception:
            continue

    return None


def format_iran_datetime(value):

    dt = parse_datetime(
        value
    )

    if dt is None:
        return "نامشخص"

    return dt.astimezone(
        IRAN_TIMEZONE
    ).strftime(
        "%Y/%m/%d - %H:%M"
    )


# =========================================================
# وضعیت بازی
# =========================================================

def _find_status_objects(data):

    result = []

    if not isinstance(
        data,
        dict,
    ):
        return result

    header = data.get(
        "header"
    )

    if isinstance(
        header,
        dict,
    ):

        status = header.get(
            "status"
        )

        if isinstance(
            status,
            dict,
        ):
            result.append(
                status
            )

    general = data.get(
        "general"
    )

    if isinstance(
        general,
        dict,
    ):

        status = general.get(
            "status"
        )

        if isinstance(
            status,
            dict,
        ):
            result.append(
                status
            )

    page_props = get_nested(
        data,
        "props",
        "pageProps",
    )

    if isinstance(
        page_props,
        dict,
    ):

        status = page_props.get(
            "status"
        )

        if isinstance(
            status,
            dict,
        ):
            result.append(
                status
            )

    found = recursive_find(
        data,
        {"status"},
    )

    if isinstance(
        found,
        dict,
    ):
        result.append(
            found
        )

    return result


def get_match_status(data):

    statuses = _find_status_objects(
        data
    )

    started = False
    finished = False
    cancelled = False
    half_time = False

    for status in statuses:

        if status.get(
            "started"
        ) is True:
            started = True

        if status.get(
            "finished"
        ) is True:
            finished = True

        if status.get(
            "cancelled"
        ) is True:
            cancelled = True

        reason = status.get(
            "reason"
        )

        reason_text = ""

        if isinstance(
            reason,
            dict,
        ):

            reason_text = " ".join(
                [
                    str(
                        reason.get(
                            "short",
                            "",
                        )
                    ),
                    str(
                        reason.get(
                            "long",
                            "",
                        )
                    ),
                ]
            ).lower()

        else:

            reason_text = str(
                reason or ""
            ).lower()

        name = str(
            status.get(
                "name",
                "",
            )
        ).lower()

        short = str(
            status.get(
                "short",
                "",
            )
        ).lower()

        status_text = (
            reason_text
            + " "
            + name
            + " "
            + short
        )

        if (
            "half" in status_text
            or "halftime" in status_text
            or status_text.strip()
            in {
                "ht",
                "1st half",
            }
        ):
            half_time = True

        if short in {
            "ht",
            "half time",
            "halftime",
        }:
            half_time = True

    if finished:
        started = True

    return {
        "started": started,
        "finished": finished,
        "cancelled": cancelled,
        "half_time": half_time,
    }


def get_match_status_key(data):

    status = get_match_status(
        data
    )

    if status["cancelled"]:
        return "cancelled"

    if status["finished"]:
        return "finished"

    if status["half_time"]:
        return "half_time"

    if status["started"]:
        return "started"

    return "not_started"


def is_match_started(data):

    return bool(
        get_match_status(
            data
        ).get("started")
    )


def is_half_time(data):

    return bool(
        get_match_status(
            data
        ).get("half_time")
    )


# =========================================================
# Lineup
# =========================================================

def get_lineup_section(data):

    if not isinstance(
        data,
        dict,
    ):
        return None

    content = get_content(
        data
    )

    candidates = []

    if isinstance(
        content,
        dict,
    ):

        candidates.append(
            content.get(
                "lineup"
            )
        )

    page_props = get_nested(
        data,
        "props",
        "pageProps",
    )

    if isinstance(
        page_props,
        dict,
    ):

        candidates.append(
            page_props.get(
                "lineup"
            )
        )

    candidates.append(
        data.get(
            "lineup"
        )
    )

    for candidate in candidates:

        if isinstance(
            candidate,
            dict,
        ):
            return candidate

    found = recursive_find(
        data,
        {"lineup"},
    )

    if isinstance(
        found,
        dict,
    ):
        return found

    return None


def get_lineup(data):

    return get_lineup_section(
        data
    )


def get_lineup_teams(data):

    lineup = get_lineup_section(
        data
    )

    if not isinstance(
        lineup,
        dict,
    ):
        return []

    for key in (
        "lineup",
        "lineups",
        "teams",
    ):

        candidate = lineup.get(
            key
        )

        if isinstance(
            candidate,
            list,
        ):

            return candidate

        if isinstance(
            candidate,
            dict,
        ):

            result = []

            for side in (
                "home",
                "away",
                "homeTeam",
                "awayTeam",
            ):

                team = candidate.get(
                    side
                )

                if isinstance(
                    team,
                    dict,
                ):
                    result.append(
                        team
                    )

            if result:
                return result

    result = []

    for key in (
        "home",
        "away",
        "homeTeam",
        "awayTeam",
        "homeTeamData",
        "awayTeamData",
    ):

        team = lineup.get(
            key
        )

        if isinstance(
            team,
            dict,
        ):
            result.append(
                team
            )

    return result


def get_team_id(team):

    if not isinstance(
        team,
        dict,
    ):
        return None

    return (
        team.get("teamId")
        or team.get("id")
        or team.get("teamID")
    )


def get_team_players(team):

    if not isinstance(
        team,
        dict,
    ):
        return []

    for key in (
        "players",
        "lineup",
        "starters",
    ):

        value = team.get(
            key
        )

        if isinstance(
            value,
            list,
        ):
            return value

    return []


def get_starters(team):

    if not isinstance(
        team,
        dict,
    ):
        return []

    starters = team.get(
        "starters"
    )

    if isinstance(
        starters,
        list,
    ):
        return starters

    players = get_team_players(
        team
    )

    result = []

    for player in players:

        if not isinstance(
            player,
            dict,
        ):
            continue

        if player.get(
            "starter"
        ) is True:

            result.append(
                player
            )
            continue

        if player.get(
            "isStarter"
        ) is True:

            result.append(
                player
            )
            continue

        if player.get(
            "bench"
        ) is True:

            continue

        if player.get(
            "isSubstitute"
        ) is True:

            continue

        if (
            player.get(
                "timeSubbedOn"
            ) is None
            and player.get(
                "substitute"
            ) is not True
        ):

            result.append(
                player
            )

    return result


def get_substitutes(team):

    if not isinstance(
        team,
        dict,
    ):
        return []

    for key in (
        "substitutes",
        "bench",
        "subs",
    ):

        value = team.get(
            key
        )

        if isinstance(
            value,
            list,
        ):
            return value

        if isinstance(
            value,
            dict,
        ):

            for nested_key in (
                "players",
                "benchArr",
                "substitutes",
            ):

                nested = value.get(
                    nested_key
                )

                if isinstance(
                    nested,
                    list,
                ):

                    flattened = []

                    for item in nested:

                        if isinstance(
                            item,
                            list,
                        ):

                            flattened.extend(
                                item
                            )

                        elif isinstance(
                            item,
                            dict,
                        ):

                            flattened.append(
                                item
                            )

                    if flattened:
                        return flattened

    players = get_team_players(
        team
    )

    result = []

    for player in players:

        if not isinstance(
            player,
            dict,
        ):
            continue

        if (
            player.get(
                "isSubstitute"
            ) is True
        ):

            result.append(
                player
            )
            continue

        if (
            player.get(
                "substitute"
            ) is True
        ):

            result.append(
                player
            )
            continue

        if (
            player.get(
                "bench"
            ) is True
        ):

            result.append(
                player
            )

    return result


def get_lineup_type(data):

    lineup = get_lineup_section(
        data
    )

    if not isinstance(
        lineup,
        dict,
    ):
        return None

    for key in (
        "lineupType",
        "type",
        "lineupStatus",
    ):

        value = lineup.get(
            key
        )

        if value is None:
            continue

        value = str(
            value
        ).lower()

        if "confirm" in value:
            return "confirmed"

        if "standard" in value:
            return "standard"

        return value

    return None


# =========================================================
# بازیکنان
# =========================================================

def get_player_id(player):

    if not isinstance(
        player,
        dict,
    ):
        return None

    for key in (
        "id",
        "playerId",
        "player_id",
        "playerID",
    ):

        value = player.get(
            key
        )

        if value is not None:
            return value

    nested = player.get(
        "player"
    )

    if isinstance(
        nested,
        dict,
    ):

        for key in (
            "id",
            "playerId",
            "player_id",
            "playerID",
        ):

            value = nested.get(
                key
            )

            if value is not None:
                return value

    return recursive_find(
        player,
        {
            "playerId",
            "player_id",
            "playerID",
        },
    )


def get_player_name(player):

    if not isinstance(
        player,
        dict,
    ):
        return ""

    name = (
        player.get("name")
        or player.get("playerName")
        or player.get("shortName")
    )

    if isinstance(
        name,
        dict,
    ):

        name = (
            name.get("full")
            or name.get("display")
            or name.get("name")
        )

    if name:
        return clean_text(
            name
        )

    nested = player.get(
        "player"
    )

    if isinstance(
        nested,
        dict,
    ):

        name = (
            nested.get("name")
            or nested.get("shortName")
            or nested.get("playerName")
        )

        if name:
            return clean_text(
                name
            )

    return ""


def _rating_from_value(value):

    if value is None:
        return None

    if isinstance(
        value,
        dict,
    ):

        for key in (
            "num",
            "value",
            "rating",
            "score",
        ):

            nested = value.get(
                key
            )

            if nested is not None:

                result = _rating_from_value(
                    nested
                )

                if result is not None:
                    return result

        return None

    if isinstance(
        value,
        str,
    ):

        value = value.strip()

        if not value:
            return None

        value = value.replace(
            ",",
            ".",
        )

    try:

        number = float(
            value
        )

    except (
        TypeError,
        ValueError,
    ):

        return None

    if number < 0 or number > 10:
        return None

    return number


def get_player_rating(player):

    if not isinstance(
        player,
        dict,
    ):
        return None

    # اولویت با فیلدهای مستقیم
    for key in (
        "rating",
        "ratingNum",
        "matchRating",
        "performanceRating",
    ):

        if key in player:

            rating = _rating_from_value(
                player.get(key)
            )

            if rating is not None:
                return rating

    # ساختارهای رایج nested
    for key in (
        "stats",
        "performance",
        "matchStats",
        "playerStats",
        "ratingData",
    ):

        value = player.get(
            key
        )

        if isinstance(
            value,
            dict,
        ):

            for rating_key in (
                "rating",
                "ratingNum",
                "matchRating",
                "performanceRating",
            ):

                rating = _rating_from_value(
                    value.get(
                        rating_key
                    )
                )

                if rating is not None:
                    return rating

    # اگر rating داخل player باشد
    nested_player = player.get(
        "player"
    )

    if isinstance(
        nested_player,
        dict,
    ):

        rating = get_player_rating(
            nested_player
        )

        if rating is not None:
            return rating

    return None


# =========================================================
# مربی / آرایش
# =========================================================

def get_coach(team):

    if not isinstance(
        team,
        dict,
    ):
        return ""

    for key in (
        "coach",
        "manager",
        "headCoach",
    ):

        value = team.get(
            key
        )

        if isinstance(
            value,
            str,
        ):

            return clean_text(
                value
            )

        if isinstance(
            value,
            dict,
        ):

            name = (
                value.get("name")
                or value.get("fullName")
                or value.get("shortName")
            )

            if name:
                return clean_text(
                    name
                )

    return ""


def get_formation(team):

    if not isinstance(
        team,
        dict,
    ):
        return ""

    for key in (
        "formation",
        "formationString",
        "displayFormation",
    ):

        value = team.get(
            key
        )

        if isinstance(
            value,
            str,
        ):

            return clean_text(
                value
            )

    return ""


def get_player_position(player):

    if not isinstance(
        player,
        dict,
    ):
        return ""

    position = (
        player.get("position")
        or player.get("role")
        or player.get("positionStringShort")
    )

    if isinstance(
        position,
        dict,
    ):

        position = (
            position.get("name")
            or position.get("short")
            or position.get("value")
        )

    return str(
        position or ""
    ).lower()


def organize_players(
    players,
    formation=None,
):

    groups = {
        "goalkeeper": [],
        "defender": [],
        "midfielder": [],
        "attacker": [],
        "unknown": [],
    }

    if not isinstance(
        players,
        list,
    ):
        return groups

    for player in players:

        position = get_player_position(
            player
        )

        position = position.lower()

        if (
            "goal" in position
            or position in {
                "gk",
                "keeper",
                "goalkeeper",
            }
        ):

            groups[
                "goalkeeper"
            ].append(player)

        elif any(
            word in position
            for word in (
                "def",
                "back",
                "centre-back",
                "center-back",
                "cb",
                "lb",
                "rb",
                "lwb",
                "rwb",
            )
        ):

            groups[
                "defender"
            ].append(player)

        elif any(
            word in position
            for word in (
                "mid",
                "dm",
                "cm",
                "am",
                "lm",
                "rm",
            )
        ):

            groups[
                "midfielder"
            ].append(player)

        elif any(
            word in position
            for word in (
                "attack",
                "forward",
                "striker",
                "st",
                "cf",
                "lw",
                "rw",
                "wing",
            )
        ):

            groups[
                "attacker"
            ].append(player)

        else:

            groups[
                "unknown"
            ].append(player)

    return groups


# =========================================================
# Event helpers
# =========================================================

def get_event_player_id(event):

    if not isinstance(
        event,
        dict,
    ):
        return None

    for key in (
        "playerId",
        "player_id",
        "playerID",
    ):

        value = event.get(
            key
        )

        if value is not None:
            return value

    player = event.get(
        "player"
    )

    if isinstance(
        player,
        dict,
    ):

        for key in (
            "id",
            "playerId",
            "player_id",
            "playerID",
        ):

            value = player.get(
                key
            )

            if value is not None:
                return value

    return recursive_find(
        event,
        {
            "playerId",
            "player_id",
            "playerID",
        },
    )


def get_event_assist_player_id(event):

    if not isinstance(
        event,
        dict,
    ):
        return None

    for key in (
        "assistPlayerId",
        "assist_player_id",
        "assistantPlayerId",
        "assistant_player_id",
    ):

        value = event.get(
            key
        )

        if value is not None:
            return value

    for key in (
        "assist",
        "assistant",
    ):

        value = event.get(
            key
        )

        if isinstance(
            value,
            dict,
        ):

            for id_key in (
                "id",
                "playerId",
                "player_id",
            ):

                player_id = value.get(
                    id_key
                )

                if player_id is not None:
                    return player_id

    return None


def get_event_unique_id(event):

    if not isinstance(
        event,
        dict,
    ):
        return None

    for key in (
        "id",
        "eventId",
        "eventID",
        "incidentId",
        "incidentID",
    ):

        value = event.get(
            key
        )

        if value is not None:
            return value

    return None


def normalize_event(event):

    if not isinstance(
        event,
        dict,
    ):
        return None

    result = dict(
        event
    )

    event_type = (
        event.get("type")
        or event.get("eventType")
        or event.get("incidentType")
        or event.get("incident")
        or ""
    )

    if isinstance(
        event_type,
        dict,
    ):

        event_type = (
            event_type.get("name")
            or event_type.get("type")
            or ""
        )

    event_type = str(
        event_type
    ).lower()

    if (
        "goal" in event_type
        or event.get(
            "isGoal"
        ) is True
    ):

        result["type"] = "goal"

    elif (
        "card" in event_type
        or event.get(
            "card"
        ) is not None
        or event.get(
            "cardType"
        ) is not None
    ):

        result["type"] = "card"

    elif "var" in event_type:

        result["type"] = "var"

    else:

        result["type"] = event_type

    player_id = get_event_player_id(
        event
    )

    if player_id is not None:

        result[
            "playerId"
        ] = player_id

    assist_id = (
        get_event_assist_player_id(
            event
        )
    )

    if assist_id is not None:

        result[
            "assistPlayerId"
        ] = assist_id

    if "isHome" in event:

        result[
            "isHome"
        ] = event[
            "isHome"
        ]

    elif "home" in event:

        result[
            "isHome"
        ] = event[
            "home"
        ]

    elif "team" in event:

        team = event[
            "team"
        ]

        if isinstance(
            team,
            dict,
        ):

            if "isHome" in team:

                result[
                    "isHome"
                ] = team[
                    "isHome"
                ]

            elif "home" in team:

                result[
                    "isHome"
                ] = team[
                    "home"
                ]

    return result


# =========================================================
# استخراج Eventها
# =========================================================

def _normalize_event_list(
    candidate
):

    if not isinstance(
        candidate,
        list,
    ):
        return []

    result = []

    for event in candidate:

        normalized = normalize_event(
            event
        )

        if normalized is not None:
            result.append(
                normalized
            )

    return result


def extract_events_from_data(data):

    if not isinstance(
        data,
        dict,
    ):
        return []

    content = get_content(
        data
    )

    candidates = []

    if isinstance(
        content,
        dict,
    ):

        match_facts = content.get(
            "matchFacts"
        )

        if isinstance(
            match_facts,
            dict,
        ):

            events = match_facts.get(
                "events"
            )

            incidents = match_facts.get(
                "incidents"
            )

            candidates.extend(
                [
                    events,
                    incidents,
                ]
            )

        liveticker = content.get(
            "liveticker"
        )

        if isinstance(
            liveticker,
            dict,
        ):

            candidates.extend(
                [
                    liveticker.get(
                        "events"
                    ),
                    liveticker.get(
                        "incidents"
                    ),
                ]
            )

    header = data.get(
        "header"
    )

    if isinstance(
        header,
        dict,
    ):

        candidates.append(
            header.get(
                "events"
            )
        )

    candidates.append(
        data.get(
            "events"
        )
    )

    page_props = get_nested(
        data,
        "props",
        "pageProps",
    )

    if isinstance(
        page_props,
        dict,
    ):

        candidates.extend(
            [
                page_props.get(
                    "events"
                ),
                page_props.get(
                    "incidents"
                ),
            ]
        )

    for candidate in candidates:

        if isinstance(
            candidate,
            list,
        ):

            result = _normalize_event_list(
                candidate
            )

            if result:
                return result

        elif isinstance(
            candidate,
            dict,
        ):

            for key in (
                "events",
                "incidents",
                "chronological",
                "all",
            ):

                nested = candidate.get(
                    key
                )

                if isinstance(
                    nested,
                    list,
                ):

                    result = (
                        _normalize_event_list(
                            nested
                        )
                    )

                    if result:
                        return result

    found = recursive_find(
        data,
        {
            "chronological",
        },
    )

    if isinstance(
        found,
        list,
    ):

        result = _normalize_event_list(
            found
        )

        if result:
            return result

    return []


def get_match_events(match_url):

    match_id = extract_match_id(
        match_url
    )

    if not match_id:
        return []

    data = fetch_match_api(
        match_id
    )

    if isinstance(
        data,
        dict,
    ):

        events = extract_events_from_data(
            data
        )

        if events:
            return events

    page = fetch_match_page(
        match_id
    )

    if not page:
        return []

    next_data = extract_next_data(
        page
    )

    if isinstance(
        next_data,
        dict,
    ):

        return extract_events_from_data(
            next_data
        )

    return []


# =========================================================
# Score
# =========================================================

def get_score(data):

    if not isinstance(
        data,
        dict,
    ):

        return {
            "home": 0,
            "away": 0,
        }

    header = data.get(
        "header"
    )

    status = {}

    if isinstance(
        header,
        dict,
    ):

        status = header.get(
            "status"
        )

        if not isinstance(
            status,
            dict,
        ):
            status = {}

    candidates = [
        status.get(
            "score"
        ),
        data.get(
            "score"
        ),
        get_nested(
            data,
            "props",
            "pageProps",
            "header",
            "status",
            "score",
        ),
    ]

    for score in candidates:

        if not isinstance(
            score,
            dict,
        ):
            continue

        home = (
            score.get("home")
            if score.get("home")
            is not None
            else score.get(
                "homeScore"
            )
        )

        away = (
            score.get("away")
            if score.get("away")
            is not None
            else score.get(
                "awayScore"
            )
        )

        try:

            if home is not None and away is not None:

                return {
                    "home": int(home),
                    "away": int(away),
                }

        except (
            TypeError,
            ValueError,
        ):
            pass

    score_strings = [
        status.get(
            "scoreStr"
        ),
        data.get(
            "scoreStr"
        ),
        get_nested(
            data,
            "props",
            "pageProps",
            "header",
            "status",
            "scoreStr",
        ),
    ]

    for score_str in score_strings:

        if score_str is None:
            continue

        match = re.search(
            r"(\d+)\s*[-:]\s*(\d+)",
            str(score_str),
        )

        if match:

            return {
                "home": int(
                    match.group(1)
                ),
                "away": int(
                    match.group(2)
                ),
            }

    return {
        "home": 0,
        "away": 0,
    }


# =========================================================
# آمار بازی
# =========================================================

STAT_ALIASES = {
    "expected goals": "xG",
    "expected goals (xg)": "xG",
    "xg": "xG",
    "shots": "شوت",
    "total shots": "شوت",
    "shots on target": "شوت در چارچوب",
    "shots on target from inside the box": "شوت در چارچوب",
    "possession": "مالکیت",
    "passes": "پاس",
    "total passes": "پاس",
    "pass accuracy": "دقت پاس",
    "accurate passes": "پاس دقیق",
    "corners": "کرنر",
    "corner kicks": "کرنر",
    "fouls": "خطا",
    "offsides": "آفساید",
    "yellow cards": "کارت زرد",
    "red cards": "کارت قرمز",
}


def _normalize_stat_label(value):

    value = clean_text(
        value
    ).lower()

    value = re.sub(
        r"\s+",
        " ",
        value,
    )

    return STAT_ALIASES.get(
        value,
        None,
    )


def _stat_value(value):

    if value is None:
        return None

    if isinstance(
        value,
        bool,
    ):
        return None

    if isinstance(
        value,
        (int, float),
    ):
        return value

    if isinstance(
        value,
        str,
    ):

        text = clean_text(
            value
        )

        if not text:
            return None

        text = text.replace(
            "%",
            "",
        )

        try:
            return float(
                text
            )

        except (
            TypeError,
            ValueError,
        ):
            return text

    return None


def _team_name_matches(
    value,
    home_name,
    away_name,
):

    if value is None:
        return None

    text = clean_text(
        value
    ).lower()

    home = clean_text(
        home_name
    ).lower()

    away = clean_text(
        away_name
    ).lower()

    if text == home and home:
        return "home"

    if text == away and away:
        return "away"

    return None


def _extract_stat_pair(
    item,
    home_name,
    away_name,
):

    if not isinstance(
        item,
        dict,
    ):
        return None

    label = (
        item.get("title")
        or item.get("name")
        or item.get("label")
        or item.get("stat")
    )

    normalized_label = _normalize_stat_label(
        label
    )

    if normalized_label is None:
        return None

    values = item.get(
        "stats"
    )

    if not isinstance(
        values,
        list,
    ):
        values = item.get(
            "values"
        )

    if not isinstance(
        values,
        list,
    ):
        values = item.get(
            "value"
        )

    if isinstance(
        values,
        list,
    ):

        home_value = None
        away_value = None

        for value_item in values:

            if not isinstance(
                value_item,
                dict,
            ):
                continue

            team_side = (
                _team_name_matches(
                    value_item.get(
                        "name"
                    )
                    or value_item.get(
                        "team"
                    )
                    or value_item.get(
                        "teamName"
                    ),
                    home_name,
                    away_name,
                )
            )

            value = (
                value_item.get("value")
            )

            if value is None:
                value = value_item.get(
                    "stat"
                )

            if value is None:
                value = value_item.get(
                    "displayValue"
                )

            value = _stat_value(
                value
            )

            if team_side == "home":
                home_value = value

            elif team_side == "away":
                away_value = value

        if (
            home_value is not None
            and away_value is not None
        ):

            return (
                normalized_label,
                home_value,
                away_value,
            )

    if isinstance(
        values,
        dict,
    ):

        home_value = None
        away_value = None

        for key, value in values.items():

            side = _team_name_matches(
                key,
                home_name,
                away_name,
            )

            value = _stat_value(
                value
            )

            if side == "home":
                home_value = value

            elif side == "away":
                away_value = value

        if (
            home_value is not None
            and away_value is not None
        ):

            return (
                normalized_label,
                home_value,
                away_value,
            )

    return None


def _walk_stat_candidates(
    data,
    home_name,
    away_name,
    found,
):

    if isinstance(
        data,
        dict,
    ):

        result = _extract_stat_pair(
            data,
            home_name,
            away_name,
        )

        if result is not None:

            found[
                result[0]
            ] = {
                "home": result[1],
                "away": result[2],
            }

        for value in data.values():

            _walk_stat_candidates(
                value,
                home_name,
                away_name,
                found,
            )

    elif isinstance(
        data,
        list,
    ):

        for item in data:

            _walk_stat_candidates(
                item,
                home_name,
                away_name,
                found,
            )


def extract_match_stats(
    data,
    home_name,
    away_name,
):

    if not isinstance(
        data,
        dict,
    ):
        return {}

    found = {}

    # ابتدا بخش‌های محتمل آمار را بررسی می‌کنیم.
    preferred_sections = []

    content = get_content(
        data
    )

    if isinstance(
        content,
        dict,
    ):

        for key in (
            "stats",
            "statistics",
            "teamStats",
            "matchStats",
        ):

            value = content.get(
                key
            )

            if value is not None:
                preferred_sections.append(
                    value
                )

    page_props = get_nested(
        data,
        "props",
        "pageProps",
    )

    if isinstance(
        page_props,
        dict,
    ):

        for key in (
            "stats",
            "statistics",
            "teamStats",
            "matchStats",
        ):

            value = page_props.get(
                key
            )

            if value is not None:
                preferred_sections.append(
                    value
                )

    for section in preferred_sections:

        _walk_stat_candidates(
            section,
            home_name,
            away_name,
            found,
        )

    # اگر ساختار بالا نبود، کل داده را جست‌وجو می‌کنیم.
    if not found:

        _walk_stat_candidates(
            data,
            home_name,
            away_name,
            found,
        )

    return found


# =========================================================
# Team object
# =========================================================

def build_team_object(
    team_data,
    lineup_team,
):

    if not isinstance(
        team_data,
        dict,
    ):
        team_data = {}

    if not isinstance(
        lineup_team,
        dict,
    ):
        lineup_team = {}

    result = dict(
        lineup_team
    )

    if not result.get(
        "id"
    ):

        result["id"] = (
            team_data.get("id")
            or team_data.get("teamId")
        )

    if not result.get(
        "name"
    ):

        result["name"] = (
            team_data.get("name")
            or ""
        )

    starters = get_starters(
        result
    )

    substitutes = get_substitutes(
        result
    )

    result[
        "starters"
    ] = starters

    result[
        "substitutes"
    ] = substitutes

    if not result.get(
        "formation"
    ):

        formation = get_formation(
            lineup_team
        )

        if formation:
            result[
                "formation"
            ] = formation

    if not result.get(
        "coach"
    ):

        coach = get_coach(
            lineup_team
        )

        if coach:
            result[
                "coach"
            ] = coach

    return result


# =========================================================
# Snapshot
# =========================================================

def get_match_snapshot(match_url):

    match_id = extract_match_id(
        match_url
    )

    if not match_id:

        print(
            "FotMob: Match ID not found."
        )

        return None

    data = fetch_match_api(
        match_id
    )

    if not isinstance(
        data,
        dict,
    ):

        page = fetch_match_page(
            match_id
        )

        if not page:
            return None

        data = extract_next_data(
            page
        )

        if not isinstance(
            data,
            dict,
        ):

            print(
                f"FotMob {match_id}: "
                "Could not extract NEXT_DATA."
            )

            return None

    info = extract_basic_info(
        data
    )

    status = get_match_status(
        data
    )

    lineup_teams = get_lineup_teams(
        data
    )

    home_id = info.get(
        "home_id"
    )

    away_id = info.get(
        "away_id"
    )

    home_lineup = None
    away_lineup = None

    for team in lineup_teams:

        team_id = get_team_id(
            team
        )

        if (
            home_id is not None
            and team_id is not None
            and str(team_id)
            == str(home_id)
        ):

            home_lineup = team

        elif (
            away_id is not None
            and team_id is not None
            and str(team_id)
            == str(away_id)
        ):

            away_lineup = team

    if home_lineup is None:

        for team in lineup_teams:

            if isinstance(
                team,
                dict,
            ):

                name = _get_team_name(
                    team
                )

                if (
                    name
                    and name.lower()
                    == info.get(
                        "home_name",
                        "",
                    ).lower()
                ):

                    home_lineup = team
                    break

    if away_lineup is None:

        for team in lineup_teams:

            if isinstance(
                team,
                dict,
            ):

                name = _get_team_name(
                    team
                )

                if (
                    name
                    and name.lower()
                    == info.get(
                        "away_name",
                        "",
                    ).lower()
                ):

                    away_lineup = team
                    break

    if home_lineup is None and len(
        lineup_teams
    ) >= 1:

        home_lineup = lineup_teams[0]

    if away_lineup is None and len(
        lineup_teams
    ) >= 2:

        away_lineup = lineup_teams[1]

    home_team_data = {
        "id": home_id,
        "name": info.get(
            "home_name"
        ),
    }

    away_team_data = {
        "id": away_id,
        "name": info.get(
            "away_name"
        ),
    }

    home_team = build_team_object(
        home_team_data,
        home_lineup or {},
    )

    away_team = build_team_object(
        away_team_data,
        away_lineup or {},
    )

    home_starters = get_starters(
        home_team
    )

    away_starters = get_starters(
        away_team
    )

    lineup_type = get_lineup_type(
        data
    )

    if (
        lineup_type is None
        and len(home_starters) == 11
        and len(away_starters) == 11
    ):

        lineup_type = "standard"

    home_name = (
        info.get(
            "home_name"
        )
        or _get_team_name(
            home_lineup
        )
        or "Home"
    )

    away_name = (
        info.get(
            "away_name"
        )
        or _get_team_name(
            away_lineup
        )
        or "Away"
    )

    if home_id is None:
        home_id = get_team_id(
            home_lineup
        )

    if away_id is None:
        away_id = get_team_id(
            away_lineup
        )

    score = get_score(
        data
    )

    stats = extract_match_stats(
        data,
        home_name,
        away_name,
    )

    return {
        "match_id": match_id,

        "home": home_name,

        "away": away_name,

        "home_team": home_team,

        "away_team": away_team,

        "home_team_id": home_id,

        "away_team_id": away_id,

        "league": (
            info.get(
                "league"
            )
            or "نامشخص"
        ),

        "start": info.get(
            "start"
        ),

        "start_formatted": (
            format_iran_datetime(
                info.get(
                    "start"
                )
            )
        ),

        "lineup_type": lineup_type,

        "home_starters": home_starters,

        "away_starters": away_starters,

        "started": status[
            "started"
        ],

        "half_time": status[
            "half_time"
        ],

        "finished": status[
            "finished"
        ],

        "cancelled": status[
            "cancelled"
        ],

        "score": score,

        "stats": stats,

        "status_key": (
            get_match_status_key(
                data
            )
        ),

        "raw": data,
    }


# =========================================================
# تابع سازگاری
# =========================================================

def get_match(match_url):

    return get_match_snapshot(
        match_url
    )

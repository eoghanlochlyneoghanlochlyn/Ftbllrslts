import json
import re
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

import requests


IRAN_TIMEZONE = ZoneInfo("Asia/Tehran")


FOTMOB_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 "
        "(KHTML, like Gecko) "
        "Chrome/131.0.0.0 Safari/537.36"
    ),
    "Accept": (
        "text/html,application/xhtml+xml,application/xml;"
        "q=0.9,image/avif,image/webp,image/apng,*/*;"
        "q=0.8,application/signed-exchange;v=b3;q=0.7"
    ),
    "Accept-Language": "en-US,en;q=0.9",
    "Referer": "https://www.google.com/",
    "Cache-Control": "no-cache",
    "Pragma": "no-cache",
}


# --------------------------------------------------------
# ابزارهای عمومی
# --------------------------------------------------------

def clean_text(value):
    if value is None:
        return ""

    if isinstance(value, str):
        return value.strip()

    return str(value).strip()


def get_nested(data, *keys):
    current = data

    for key in keys:
        if not isinstance(current, dict):
            return None

        current = current.get(key)

    return current


def recursive_find(data, target_key):
    """
    جست‌وجوی بازگشتی یک کلید در تمام ساختار JSON.
    """

    if isinstance(data, dict):

        if target_key in data:
            return data[target_key]

        for value in data.values():

            result = recursive_find(
                value,
                target_key,
            )

            if result is not None:
                return result

    elif isinstance(data, list):

        for item in data:

            result = recursive_find(
                item,
                target_key,
            )

            if result is not None:
                return result

    return None


def find_section(data, possible_keys):
    """
    پیدا کردن اولین دیکشنری‌ای که یکی از کلیدهای موردنظر
    را داشته باشد.
    """

    if isinstance(data, dict):

        for key in possible_keys:

            if key in data:

                value = data[key]

                if isinstance(value, dict):
                    return value

        for value in data.values():

            result = find_section(
                value,
                possible_keys,
            )

            if result is not None:
                return result

    elif isinstance(data, list):

        for item in data:

            result = find_section(
                item,
                possible_keys,
            )

            if result is not None:
                return result

    return None


# --------------------------------------------------------
# اطلاعات بازیکنان event
# --------------------------------------------------------

def get_event_player_id(event):
    """
    استخراج شناسه بازیکن اصلی یک event.
    """

    if not isinstance(event, dict):
        return None

    # حالت مستقیم
    for key in (
        "playerId",
        "player_id",
        "playerID",
    ):

        value = event.get(key)

        if value is not None:
            return str(value)

    # حالت player به صورت دیکشنری
    player = event.get("player")

    if isinstance(player, dict):

        for key in (
            "id",
            "playerId",
            "player_id",
        ):

            value = player.get(key)

            if value is not None:
                return str(value)

    # بعضی ساختارهای FotMob ممکن است
    # player را داخل nested object قرار دهند.

    player_data = recursive_find(
        event,
        "playerId",
    )

    if player_data is not None:
        return str(player_data)

    return None


def get_event_assist_player_id(event):
    """
    استخراج شناسه بازیکنی که پاس گل داده است.
    """

    if not isinstance(event, dict):
        return None

    # حالت‌های مستقیم
    for key in (
        "assistPlayerId",
        "assist_player_id",
        "assistantPlayerId",
        "assistant_player_id",
    ):

        value = event.get(key)

        if value is not None:
            return str(value)

    # assist به صورت دیکشنری
    assist = event.get("assist")

    if isinstance(assist, dict):

        for key in (
            "id",
            "playerId",
            "player_id",
        ):

            value = assist.get(key)

            if value is not None:
                return str(value)

    # assistant به صورت دیکشنری
    assistant = event.get("assistant")

    if isinstance(assistant, dict):

        for key in (
            "id",
            "playerId",
            "player_id",
        ):

            value = assistant.get(key)

            if value is not None:
                return str(value)

    # fallback برای ساختارهای nested
    for key in (
        "assist",
        "assistant",
    ):

        nested = event.get(key)

        if isinstance(nested, dict):

            value = recursive_find(
                nested,
                "playerId",
            )

            if value is not None:
                return str(value)

    return None


def get_event_unique_id(event):
    """
    استخراج شناسه یکتا برای event.
    """

    if not isinstance(event, dict):
        return None

    for key in (
        "id",
        "eventId",
        "eventID",
    ):

        value = event.get(key)

        if value is not None:
            return str(value)

    return None


# --------------------------------------------------------
# دریافت صفحه FotMob
# --------------------------------------------------------

def fetch_match_page(match_id):
    match_id = str(match_id)

    url = f"https://www.fotmob.com/match/{match_id}"

    response = requests.get(
        url,
        headers=FOTMOB_HEADERS,
        timeout=30,
    )

    print(
        f"FotMob {match_id}: HTTP {response.status_code}"
    )

    print(
        f"FotMob {match_id}: Final URL = {response.url}"
    )

    print(
        f"FotMob {match_id}: Response length = "
        f"{len(response.text)}"
    )

    print(
        f"FotMob {match_id}: __NEXT_DATA__ found = "
        f"{'__NEXT_DATA__' in response.text}"
    )

    print(
        f"FotMob {match_id}: eventJSONLD found = "
        f"{'eventJSONLD' in response.text}"
    )

    print(
        f"FotMob {match_id}: First 300 chars = "
        f"{response.text[:300]!r}"
    )

    response.raise_for_status()

    return response.text


# --------------------------------------------------------
# استخراج __NEXT_DATA__
# --------------------------------------------------------

def extract_next_data(html):
    patterns = [
        r'<script[^>]+id=["\']__NEXT_DATA__["\'][^>]*>'
        r'(.*?)</script>',

        r'<script[^>]+id=["\']__NEXT_DATA__["\'][^>]*>'
        r'(.*?)</script\s*>',
    ]

    for pattern in patterns:

        match = re.search(
            pattern,
            html,
            re.DOTALL | re.IGNORECASE,
        )

        if not match:
            continue

        raw_json = match.group(1).strip()

        try:

            return json.loads(
                raw_json
            )

        except json.JSONDecodeError as error:

            raise RuntimeError(
                "__NEXT_DATA__ JSON decode failed: "
                f"{error}"
            )

    raise RuntimeError(
        "__NEXT_DATA__ not found."
    )


def fetch_match_data(match_id):
    html = fetch_match_page(
        match_id
    )

    root = extract_next_data(
        html
    )

    if not isinstance(root, dict):

        raise RuntimeError(
            "FotMob root JSON is not a dictionary."
        )

    print(
        "FotMob root top-level keys:",
        list(root.keys()),
    )

    return root


# --------------------------------------------------------
# پیدا کردن content
# --------------------------------------------------------

def get_content(root):
    """
    تلاش برای پیدا کردن محتوای اصلی مسابقه
    در مسیرهای مختلف ساختار FotMob.
    """

    possible_paths = [

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

        (
            "content",
        ),
    ]

    for path in possible_paths:

        value = get_nested(
            root,
            *path,
        )

        if isinstance(value, dict):

            print(
                "FotMob content found at path:",
                " → ".join(path),
            )

            return value

    print(
        "FotMob content not found in known paths."
    )

    if isinstance(root, dict):

        print(
            "FotMob root top-level keys:",
            list(root.keys()),
        )

        props = root.get(
            "props"
        )

        print(
            "FotMob props keys:",
            list(props.keys())
            if isinstance(
                props,
                dict,
            )
            else type(props),
        )

        if isinstance(
            props,
            dict,
        ):

            page_props = props.get(
                "pageProps"
            )

            print(
                "FotMob pageProps keys:",
                list(page_props.keys())
                if isinstance(
                    page_props,
                    dict,
                )
                else type(page_props),
            )

    # fallback بازگشتی
    recursive_content = recursive_find(
        root,
        "content",
    )

    if isinstance(
        recursive_content,
        dict,
    ):

        print(
            "FotMob content found recursively."
        )

        return recursive_content

    # fallback برای matchData
    recursive_match_data = recursive_find(
        root,
        "matchData",
    )

    if isinstance(
        recursive_match_data,
        dict,
    ):

        print(
            "FotMob matchData found recursively."
        )

        return recursive_match_data

    raise RuntimeError(
        "FotMob content not found."
    )


# --------------------------------------------------------
# Event JSON-LD
# --------------------------------------------------------

def extract_event_jsonld(root):
    possible_paths = [

        (
            "props",
            "pageProps",
            "seo",
            "eventJSONLD",
        ),

        (
            "props",
            "pageProps",
            "eventJSONLD",
        ),

        (
            "pageProps",
            "seo",
            "eventJSONLD",
        ),

        (
            "seo",
            "eventJSONLD",
        ),
    ]

    for path in possible_paths:

        value = get_nested(
            root,
            *path,
        )

        if value is not None:
            return value

    return recursive_find(
        root,
        "eventJSONLD",
    )


# --------------------------------------------------------
# اطلاعات پایه مسابقه
# --------------------------------------------------------

def extract_basic_info(root):
    event_jsonld = extract_event_jsonld(
        root
    )

    content = get_content(
        root
    )

    home_team = ""
    away_team = ""
    start_date = ""
    match_name = ""

    if isinstance(
        event_jsonld,
        dict,
    ):

        home_team_data = event_jsonld.get(
            "homeTeam"
        )

        away_team_data = event_jsonld.get(
            "awayTeam"
        )

        if isinstance(
            home_team_data,
            dict,
        ):

            home_team = clean_text(
                home_team_data.get(
                    "name"
                )
            )

        else:

            home_team = clean_text(
                home_team_data
            )

        if isinstance(
            away_team_data,
            dict,
        ):

            away_team = clean_text(
                away_team_data.get(
                    "name"
                )
            )

        else:

            away_team = clean_text(
                away_team_data
            )

        start_date = clean_text(
            event_jsonld.get(
                "startDate"
            )
        )

        match_name = clean_text(
            event_jsonld.get(
                "name"
            )
        )

    if not home_team:

        home_team = clean_text(
            recursive_find(
                content,
                "homeTeamName",
            )
        )

    if not away_team:

        away_team = clean_text(
            recursive_find(
                content,
                "awayTeamName",
            )
        )

    if not home_team:

        home_team = clean_text(
            recursive_find(
                root,
                "homeTeamName",
            )
        )

    if not away_team:

        away_team = clean_text(
            recursive_find(
                root,
                "awayTeamName",
            )
        )

    if (
        not match_name
        and home_team
        and away_team
    ):

        match_name = (
            f"{home_team} vs {away_team}"
        )

    return {
        "home_team": home_team,
        "away_team": away_team,
        "start_date": start_date,
        "match_name": match_name,
    }


# --------------------------------------------------------
# تاریخ و زمان
# --------------------------------------------------------

def parse_datetime(value):
    if not value:
        return None

    if isinstance(
        value,
        datetime,
    ):
        return value

    value = clean_text(
        value
    )

    if not value:
        return None

    try:

        parsed = datetime.fromisoformat(
            value.replace(
                "Z",
                "+00:00",
            )
        )

        if parsed.tzinfo is None:

            parsed = parsed.replace(
                tzinfo=timezone.utc
            )

        return parsed

    except ValueError:
        pass

    formats = [
        "%Y-%m-%dT%H:%M:%S.%f%z",
        "%Y-%m-%dT%H:%M:%S%z",
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%d",
    ]

    for fmt in formats:

        try:

            parsed = datetime.strptime(
                value,
                fmt,
            )

            if parsed.tzinfo is None:

                parsed = parsed.replace(
                    tzinfo=timezone.utc
                )

            return parsed

        except ValueError:
            continue

    return None


def format_iran_datetime(value):
    parsed = parse_datetime(
        value
    )

    if parsed is None:
        return ""

    return parsed.astimezone(
        IRAN_TIMEZONE
    ).strftime(
        "%Y-%m-%d %H:%M:%S"
    )


# --------------------------------------------------------
# وضعیت مسابقه
# --------------------------------------------------------

def get_match_status(root):
    possible_paths = [

        (
            "props",
            "pageProps",
            "header",
            "status",
        ),

        (
            "props",
            "pageProps",
            "content",
            "header",
            "status",
        ),

        (
            "props",
            "pageProps",
            "status",
        ),

        (
            "pageProps",
            "header",
            "status",
        ),

        (
            "header",
            "status",
        ),
    ]

    status = None

    for path in possible_paths:

        status = get_nested(
            root,
            *path,
        )

        if status is not None:
            break

    if status is None:

        status = recursive_find(
            root,
            "status",
        )

    if not isinstance(
        status,
        dict,
    ):

        status = {}

    finished = status.get(
        "finished"
    )

    started = status.get(
        "started"
    )

    cancelled = status.get(
        "cancelled"
    )

    period = status.get(
        "period"
    )

    reason = status.get(
        "reason"
    )

    utc_time = status.get(
        "utcTime"
    )

    return {
        "finished": bool(
            finished
        ),
        "started": bool(
            started
        ),
        "cancelled": bool(
            cancelled
        ),
        "period": clean_text(
            period
        ),
        "reason": clean_text(
            reason
        ),
        "utc_time": clean_text(
            utc_time
        ),
        "raw": status,
    }


def _find_status_objects(root):
    objects = []

    if not isinstance(
        root,
        dict,
    ):
        return objects

    props = root.get(
        "props"
    )

    if not isinstance(
        props,
        dict,
    ):
        return objects

    page_props = props.get(
        "pageProps"
    )

    if not isinstance(
        page_props,
        dict,
    ):
        return objects

    content = page_props.get(
        "content"
    )

    if isinstance(
        content,
        dict,
    ):

        header = content.get(
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

                objects.append(
                    status
                )

        status = content.get(
            "status"
        )

        if isinstance(
            status,
            dict,
        ):

            objects.append(
                status
            )

    header = page_props.get(
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

            objects.append(
                status
            )

    status = page_props.get(
        "status"
    )

    if isinstance(
        status,
        dict,
    ):

        objects.append(
            status
        )

    return objects


def get_match_status_key(root):
    """
    تبدیل وضعیت مسابقه به یک مقدار ساده.
    """

    for status in _find_status_objects(
        root
    ):

        reason = status.get(
            "reason"
        )

        if isinstance(
            reason,
            dict,
        ):

            short = clean_text(
                reason.get(
                    "short"
                )
            ).upper()

            if short:
                return short

            long_text = clean_text(
                reason.get(
                    "long"
                )
            ).upper()

            if long_text:
                return long_text

        short = clean_text(
            status.get(
                "short"
            )
        ).upper()

        if short:
            return short

        name = clean_text(
            status.get(
                "name"
            )
        ).upper()

        if name:
            return name

    return ""


def is_match_started(
    root,
    snapshot=None,
):
    if isinstance(
        snapshot,
        dict,
    ):

        status = clean_text(
            snapshot.get(
                "status"
            )
        ).lower()

        if status in (
            "live",
            "started",
            "inplay",
            "in_play",
        ):
            return True

        if snapshot.get(
            "finished"
        ) is True:

            return True

    status_key = get_match_status_key(
        root
    )

    if status_key in (
        "LIVE",
        "1H",
        "2H",
        "ET",
        "P",
        "HT",
        "FT",
        "AET",
        "PEN",
        "FINISHED",
    ):

        return True

    status_lower = status_key.lower()

    if any(
        word in status_lower
        for word in (
            "live",
            "started",
            "in progress",
            "halftime",
            "half time",
            "finished",
        )
    ):

        return True

    return False


def is_half_time(
    root,
    snapshot=None,
):
    if isinstance(
        snapshot,
        dict,
    ):

        status = clean_text(
            snapshot.get(
                "status"
            )
        ).lower()

        if status in (
            "ht",
            "halftime",
            "half_time",
        ):

            return True

    status_key = get_match_status_key(
        root
    )

    normalized = status_key.lower()

    return normalized in (
        "ht",
        "halftime",
        "half time",
        "half_time",
    )


# --------------------------------------------------------
# Eventهای مسابقه
# --------------------------------------------------------

def get_match_events(root):
    possible_paths = [

        (
            "props",
            "pageProps",
            "content",
            "matchFacts",
            "events",
            "events",
        ),

        (
            "props",
            "pageProps",
            "matchFacts",
            "events",
            "events",
        ),

        (
            "props",
            "pageProps",
            "content",
            "events",
        ),

        (
            "props",
            "pageProps",
            "events",
        ),

        (
            "props",
            "pageProps",
            "content",
            "matchFacts",
            "events",
        ),
    ]

    events = None

    for path in possible_paths:

        value = get_nested(
            root,
            *path,
        )

        if isinstance(
            value,
            list,
        ):

            events = value
            break

    if events is None:

        events = recursive_find(
            root,
            "events",
        )

    if not isinstance(
        events,
        list,
    ):

        return []

    return events


# --------------------------------------------------------
# Lineup
# --------------------------------------------------------

def get_lineup(
    content,
    root=None,
):
    lineup = None

    if isinstance(
        content,
        dict,
    ):

        lineup = content.get(
            "lineup"
        )

    if isinstance(
        lineup,
        dict,
    ):

        return lineup

    if isinstance(
        root,
        dict,
    ):

        lineup = find_section(
            root,
            ["lineup"],
        )

        if isinstance(
            lineup,
            dict,
        ):

            return lineup

    return {}


def get_lineup_type(root):
    content = get_content(
        root
    )

    lineup = get_lineup(
        content,
        root,
    )

    if not isinstance(
        lineup,
        dict,
    ):

        return ""

    lineup_type = lineup.get(
        "lineupType"
    )

    if lineup_type is None:

        lineup_type = lineup.get(
            "type"
        )

    return clean_text(
        lineup_type
    ).lower()


def extract_players(team_data):
    if not isinstance(
        team_data,
        dict,
    ):

        return []

    possible_keys = [
        "starters",
        "startingPlayers",
        "players",
        "lineup",
    ]

    players = []

    for key in possible_keys:

        value = team_data.get(
            key
        )

        if isinstance(
            value,
            list,
        ):

            players = value
            break

    result = []

    for player in players:

        if not isinstance(
            player,
            dict,
        ):
            continue

        name = (
            player.get("name")
            or player.get("playerName")
            or get_nested(
                player,
                "player",
                "name",
            )
        )

        position = (
            player.get("position")
            or player.get("role")
            or ""
        )

        result.append(
            {
                "name": clean_text(
                    name
                ),
                "position": clean_text(
                    position
                ),
            }
        )

    return result


def get_lineup_teams(root):
    content = get_content(
        root
    )

    lineup = get_lineup(
        content,
        root,
    )

    if not isinstance(
        lineup,
        dict,
    ):

        return {
            "home": [],
            "away": [],
        }

    home_data = (
        lineup.get("home")
        or lineup.get("homeTeam")
        or lineup.get("homeLineup")
        or {}
    )

    away_data = (
        lineup.get("away")
        or lineup.get("awayTeam")
        or lineup.get("awayLineup")
        or {}
    )

    return {
        "home": extract_players(
            home_data
        ),
        "away": extract_players(
            away_data
        ),
    }


# --------------------------------------------------------
# نتیجه مسابقه
# --------------------------------------------------------

def get_score(root):
    content = get_content(
        root
    )

    possible_score_paths = [

        (
            "props",
            "pageProps",
            "content",
            "header",
            "teams",
        ),

        (
            "props",
            "pageProps",
            "header",
            "teams",
        ),

        (
            "props",
            "pageProps",
            "content",
            "teams",
        ),
    ]

    teams = None

    for path in possible_score_paths:

        value = get_nested(
            root,
            *path,
        )

        if isinstance(
            value,
            list,
        ):

            teams = value
            break

    if teams is None:

        teams = recursive_find(
            root,
            "teams",
        )

    home_score = None
    away_score = None

    if (
        isinstance(
            teams,
            list,
        )
        and len(teams) >= 2
    ):

        home_team = teams[0]
        away_team = teams[1]

        if isinstance(
            home_team,
            dict,
        ):

            home_score = (
                home_team.get("score")
                or home_team.get("goals")
                or home_team.get("currentScore")
            )

        if isinstance(
            away_team,
            dict,
        ):

            away_score = (
                away_team.get("score")
                or away_team.get("goals")
                or away_team.get("currentScore")
            )

    if home_score is None:

        home_score = recursive_find(
            content,
            "homeScore",
        )

    if away_score is None:

        away_score = recursive_find(
            content,
            "awayScore",
        )

    return {
        "home": home_score,
        "away": away_score,
    }


# --------------------------------------------------------
# Snapshot کامل مسابقه
# --------------------------------------------------------

def get_match_snapshot(root):
    basic_info = extract_basic_info(
        root
    )

    status = get_match_status(
        root
    )

    events = get_match_events(
        root
    )

    lineup_type = get_lineup_type(
        root
    )

    lineup_teams = get_lineup_teams(
        root
    )

    score = get_score(
        root
    )

    return {
        "basic_info": basic_info,
        "status": status,
        "events": events,
        "lineup_type": lineup_type,
        "lineup_teams": lineup_teams,
        "score": score,
    }


# --------------------------------------------------------
# دریافت مستقیم مسابقه
# --------------------------------------------------------

def get_match(match_id):
    root = fetch_match_data(
        match_id
    )

    return get_match_snapshot(
        root
    )

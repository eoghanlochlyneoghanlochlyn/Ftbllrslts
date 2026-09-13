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
    """
    متن را برای استفاده در پیام تمیز می‌کند.
    """

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
        value.replace(
            "\xa0",
            " ",
        )
        .replace(
            "\u200b",
            "",
        )
        .replace(
            "\r",
            " ",
        )
        .replace(
            "\n",
            " ",
        )
    )

    return " ".join(
        value.split()
    ).strip()


def get_nested(data, *keys):
    """
    دسترسی امن به مسیر تو در تو.
    """

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
    """
    اولین مقدار قابل استفاده برای یکی از کلیدهای موردنظر
    را در ساختار JSON پیدا می‌کند.
    """

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
    """
    پیدا کردن یک بخش مشخص در JSON.
    """

    if not isinstance(data, dict):
        return None

    if section_name in data:
        return data[section_name]

    return recursive_find(
        data,
        {section_name},
    )


# =========================================================
# استخراج Match ID
# =========================================================

def extract_match_id(value):
    """
    Match ID را از عدد، URL یا متن استخراج می‌کند.
    """

    if value is None:
        return None

    if isinstance(
        value,
        int,
    ):
        return str(value)

    value = str(value).strip()

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
# دریافت داده از FotMob
# =========================================================

def fetch_match_api(match_id):
    """
    دریافت مستقیم matchDetails از API فوت‌موب.
    """

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


def fetch_match_page(match_id):
    """
    دریافت صفحه مسابقه به عنوان روش پشتیبان.
    """

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


def extract_next_data(html):
    """
    استخراج __NEXT_DATA__ از صفحه.
    """

    if not html:
        return None

    patterns = [
        r'<script[^>]+id=["\']__NEXT_DATA__["\'][^>]*>'
        r"(.*?)"
        r"</script>",

        r'<script[^>]+id=["\']__NEXT_DATA__["\'][^>]*>'
        r"(.*?)"
        r"</script\s*>",
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
            return json.loads(raw)

        except Exception:
            continue

    return None


def extract_event_jsonld(html):
    """
    استخراج Event JSON-LD در صورت وجود.
    """

    if not html:
        return None

    pattern = (
        r'<script[^>]+type=["\']application/ld\+json'
        r'["\'][^>]*>(.*?)</script>'
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
                return data

            if isinstance(
                data,
                list,
            ):

                for item in data:

                    if isinstance(
                        item,
                        dict,
                    ):
                        return item

        except Exception:
            continue

    return None


def get_content(data):
    """
    پیدا کردن بخش اصلی matchDetails.
    """

    if not isinstance(
        data,
        dict,
    ):
        return None

    # API مستقیم FotMob
    if isinstance(
        data.get("content"),
        dict,
    ):
        return data["content"]

    # ساختارهای احتمالی صفحه
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
        (
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

    found = recursive_find(
        data,
        {
            "content",
            "matchData",
        },
    )

    if isinstance(
        found,
        dict,
    ):
        return found

    return None


def fetch_match_data(match_id):
    """
    دریافت داده مسابقه.

    ابتدا API مستقیم.
    در صورت شکست، صفحه مسابقه.
    """

    match_id = extract_match_id(
        match_id
    )

    if not match_id:
        return None

    data = fetch_match_api(
        match_id
    )

    if isinstance(
        data,
        dict,
    ):
        return data

    html = fetch_match_page(
        match_id
    )

    if not html:
        return None

    next_data = extract_next_data(
        html
    )

    if isinstance(
        next_data,
        dict,
    ):
        return next_data

    jsonld = extract_event_jsonld(
        html
    )

    if isinstance(
        jsonld,
        dict,
    ):
        return {
            "eventJSONLD": jsonld
        }

    return None


# =========================================================
# اطلاعات پایه مسابقه
# =========================================================

def extract_basic_info(data):
    """
    اطلاعات پایه مسابقه را از ساختارهای مختلف استخراج می‌کند.
    """

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

    home = (
        general.get("homeTeam")
        or header.get("homeTeam")
    )

    away = (
        general.get("awayTeam")
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

    home_name = (
        home.get("name")
        or recursive_find(
            data,
            {"homeTeamName"},
        )
        or ""
    )

    away_name = (
        away.get("name")
        or recursive_find(
            data,
            {"awayTeamName"},
        )
        or ""
    )

    league = ""

    tournament = (
        general.get(
            "tournament"
        )
        or general.get(
            "league"
        )
    )

    if isinstance(
        tournament,
        dict,
    ):
        league = (
            tournament.get("name")
            or ""
        )

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
        "home_id": (
            home.get("id")
            or home.get("teamId")
        ),
        "away_id": (
            away.get("id")
            or away.get("teamId")
        ),
        "league": clean_text(
            league
        ),
        "start": start,
    }


# =========================================================
# زمان
# =========================================================

def parse_datetime(value):
    """
    تبدیل تاریخ‌های رایج FotMob به datetime.
    """

    if value is None:
        return None

    if isinstance(
        value,
        datetime,
    ):
        return value

    if isinstance(
        value,
        (int, float),
    ):

        try:

            # milliseconds
            if value > 100000000000:
                return datetime.fromtimestamp(
                    value / 1000,
                    tz=timezone.utc,
                )

            return datetime.fromtimestamp(
                value,
                tz=timezone.utc,
            )

        except Exception:
            return None

    value = str(value).strip()

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
    """
    تبدیل زمان به ساعت ایران.
    """

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
# وضعیت مسابقه
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
            result.append(status)

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
            result.append(status)

    found = recursive_find(
        data,
        {"status"},
    )

    if isinstance(
        found,
        dict,
    ):
        result.append(found)

    return result


def get_match_status(data):
    """
    وضعیت مسابقه را به شکل استاندارد برمی‌گرداند.
    """

    statuses = _find_status_objects(
        data
    )

    started = False
    finished = False
    cancelled = False
    half_time = False

    for status in statuses:

        if status.get("started") is True:
            started = True

        if status.get("finished") is True:
            finished = True

        if status.get("cancelled") is True:
            cancelled = True

        reason = str(
            status.get(
                "reason",
                "",
            )
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
            reason
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

    # اگر finished است، بازی حتماً شروع شده
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
# استخراج lineup
# =========================================================

def get_lineup_section(data):
    """
    بخش lineup را پیدا می‌کند.
    """

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
            content.get("lineup")
        )

    candidates.append(
        data.get("lineup")
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
    """
    دو تیم lineup را پیدا می‌کند.
    """

    lineup = get_lineup_section(
        data
    )

    if not isinstance(
        lineup,
        dict,
    ):
        return []

    candidates = [
        lineup.get(
            "lineup"
        ),
        lineup.get(
            "lineups"
        ),
    ]

    for candidate in candidates:

        if isinstance(
            candidate,
            list,
        ):
            return candidate

    # بعضی ساختارها ممکن است مستقیم team object داشته باشند
    result = []

    for key in (
        "home",
        "away",
        "homeTeam",
        "awayTeam",
    ):

        team = lineup.get(
            key
        )

        if isinstance(
            team,
            dict,
        ):
            result.append(team)

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
    """
    بازیکنان اصلی یک تیم.
    """

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
            "isSubstitute"
        ) is True:
            continue

        # در ساختار FotMob lineup معمولاً
        # role/position برای بازیکن اصلی وجود دارد.
        if (
            player.get("timeSubbedOn")
            is None
            and player.get("bench")
            is not True
        ):
            result.append(
                player
            )

    return result


def get_substitutes(team):
    """
    بازیکنان ذخیره یک تیم.
    """

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
                    # اگر benchArr شامل دو لیست تیمی باشد
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

        if player.get(
            "isSubstitute"
        ) is True:
            result.append(
                player
            )
            continue

        if player.get(
            "substitute"
        ) is True:
            result.append(
                player
            )
            continue

        if player.get(
            "bench"
        ) is True:
            result.append(
                player
            )

    return result


def get_lineup_type(data):
    """
    نوع lineup را پیدا می‌کند.
    """

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

        if value is not None:

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

    direct_keys = (
        "id",
        "playerId",
        "player_id",
        "playerID",
    )

    for key in direct_keys:

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

        for key in direct_keys:

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


def get_player_rating(player):
    if not isinstance(
        player,
        dict,
    ):
        return None

    rating = player.get(
        "rating"
    )

    if isinstance(
        rating,
        dict,
    ):

        rating = (
            rating.get("num")
            or rating.get("value")
            or rating.get("rating")
        )

    if rating is None:

        rating = (
            player.get("ratingNum")
            or player.get("matchRating")
        )

    if rating is None:
        return None

    try:
        return float(
            rating
        )

    except (
        TypeError,
        ValueError,
    ):
        return None


# =========================================================
# مربی و آرایش
# =========================================================

def get_coach(team):
    """
    نام مربی تیم را استخراج می‌کند.
    """

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
    """
    آرایش تیم را استخراج می‌کند.
    """

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
    """
    بازیکنان را برای نمایش به دروازه‌بان،
    مدافع، هافبک و مهاجم تقسیم می‌کند.
    """

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

        # دروازه‌بان
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

        # مدافع
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

        # هافبک
        elif any(
            word in position
            for word in (
                "mid",
                "wing",
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

        # مهاجم
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
# Eventها
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
    """
    یک event خام FotMob را تا حد ممکن
    به ساختار قابل استفاده پروژه تبدیل می‌کند.
    """

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
        or event.get("isGoal") is True
    ):
        result["type"] = "goal"

    elif (
        "card" in event_type
        or event.get("card") is not None
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
        result["playerId"] = player_id

    assist_id = (
        get_event_assist_player_id(
            event
        )
    )

    if assist_id is not None:
        result[
            "assistPlayerId"
        ] = assist_id

    # home / away
    if "isHome" in event:
        result["isHome"] = event[
            "isHome"
        ]

    elif "home" in event:
        result["isHome"] = event[
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
                result["isHome"] = team[
                    "isHome"
                ]

    return result


def extract_events_from_data(data):
    """
    استخراج eventهای مسابقه از چند ساختار شناخته‌شده.
    """

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

            candidates.extend(
                [
                    match_facts.get(
                        "events"
                    ),
                    match_facts.get(
                        "incidents"
                    ),
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
        data.get("events")
    )

    for candidate in candidates:

        if isinstance(
            candidate,
            list,
        ):

            result = []

            for event in candidate:

                normalized = normalize_event(
                    event
                )

                if normalized is not None:
                    result.append(
                        normalized
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

                    result = []

                    for event in nested:

                        normalized = (
                            normalize_event(
                                event
                            )
                        )

                        if normalized is not None:
                            result.append(
                                normalized
                            )

                    if result:
                        return result

    # آخرین fallback
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

        result = []

        for event in found:

            normalized = normalize_event(
                event
            )

            if normalized is not None:
                result.append(
                    normalized
                )

        return result

    return []


def get_match_events(match_url):
    """
    eventهای مسابقه را دریافت می‌کند.

    این تابع برای event_detector استفاده می‌شود.
    """

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

        return extract_events_from_data(
            data
        )

    # fallback صفحه
    page = fetch_match_page(
        match_id
    )

    if page:

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
    """
    نتیجه فعلی مسابقه.
    """

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

    score = (
        status.get("score")
        or data.get("score")
    )

    if isinstance(
        score,
        dict,
    ):

        home = (
            score.get("home")
            or score.get("homeScore")
        )

        away = (
            score.get("away")
            or score.get("awayScore")
        )

        try:

            return {
                "home": int(
                    home or 0
                ),
                "away": int(
                    away or 0
                ),
            }

        except (
            TypeError,
            ValueError,
        ):
            pass

    score_str = (
        status.get(
            "scoreStr"
        )
        or data.get(
            "scoreStr"
        )
        or ""
    )

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
# ساخت Team object
# =========================================================

def build_team_object(
    team_data,
    lineup_team,
):
    """
    ساخت ساختار ساده‌ای که formatter انتظار دارد.
    """

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

    result["starters"] = starters
    result["substitutes"] = substitutes

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
    """
    snapshot استاندارد برای main.py و formatter.py.
    """

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
            return None

    info = extract_basic_info(
        data
    )

    status = get_match_status(
        data
    )

    lineup = get_lineup_section(
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

    # اگر ID پیدا نشد، ترتیب معمول home/away را استفاده کن
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

    # اگر FotMob نوع lineup را صریح نگفته ولی
    # 11 بازیکن اصلی هر تیم داریم، standard در نظر می‌گیریم.
    if (
        lineup_type is None
        and len(home_starters) == 11
        and len(away_starters) == 11
    ):

        lineup_type = "standard"

    score = get_score(
        data
    )

    return {
        "match_id": match_id,

        "home": info.get(
            "home_name"
        )
        or "Home",

        "away": info.get(
            "away_name"
        )
        or "Away",

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
    """
    نام قدیمی/عمومی برای دریافت snapshot.
    """

    return get_match_snapshot(
        match_url
    )

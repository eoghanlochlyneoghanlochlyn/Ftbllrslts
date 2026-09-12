import json
import os
import re
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

import requests


MATCH_ID = "5811755"
MATCH_URL = f"https://www.fotmob.com/match/{MATCH_ID}"

IRAN_TIMEZONE = ZoneInfo("Asia/Tehran")

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAMBOT")
TELEGRAM_CHANNEL = os.getenv("TELEGRAMCHANNEL")


# --------------------------------------------------------
# ابزارهای عمومی
# --------------------------------------------------------

def get_nested(data, *keys):
    current = data

    for key in keys:
        if not isinstance(current, dict):
            return None

        current = current.get(key)

    return current


def clean_text(value):
    if value is None:
        return ""

    return str(value).strip()


def first_non_empty(*values):
    for value in values:
        if value is None:
            continue

        if isinstance(value, str):
            value = value.strip()

            if value:
                return value

        elif value not in ("", None):
            return value

    return ""


# --------------------------------------------------------
# ارسال تلگرام
# --------------------------------------------------------

def send_telegram(text):
    if not TELEGRAM_BOT_TOKEN:
        raise RuntimeError(
            "TELEGRAMBOT environment variable is missing."
        )

    if not TELEGRAM_CHANNEL:
        raise RuntimeError(
            "TELEGRAMCHANNEL environment variable is missing."
        )

    url = (
        f"https://api.telegram.org/"
        f"bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    )

    response = requests.post(
        url,
        data={
            "chat_id": TELEGRAM_CHANNEL,
            "text": text,
        },
        timeout=30,
    )

    print(
        "Telegram status:",
        response.status_code,
    )

    if not response.ok:
        print(response.text)

    response.raise_for_status()

    return response.json()


# --------------------------------------------------------
# دریافت صفحه فوت‌موب
# --------------------------------------------------------

def fetch_match_page():
    print("=" * 70)
    print("FETCHING FOTMOB MATCH")
    print("=" * 70)

    print("Match ID:", MATCH_ID)
    print("URL:", MATCH_URL)

    response = requests.get(
        MATCH_URL,
        headers={
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 "
                "(KHTML, like Gecko) "
                "Chrome/131.0.0.0 Safari/537.36"
            )
        },
        timeout=30,
    )

    print("HTTP:", response.status_code)
    print("HTML:", len(response.text), "bytes")

    response.raise_for_status()

    return response.text


# --------------------------------------------------------
# استخراج __NEXT_DATA__
# --------------------------------------------------------

def extract_next_data(html):
    pattern = (
        r'<script id="__NEXT_DATA__" '
        r'type="application/json">(.*?)</script>'
    )

    match = re.search(
        pattern,
        html,
        re.DOTALL,
    )

    if not match:
        raise RuntimeError(
            "__NEXT_DATA__ not found."
        )

    raw_json = match.group(1)

    data = json.loads(raw_json)

    print(
        "NEXT_DATA extracted successfully."
    )

    return data


# --------------------------------------------------------
# جستجوی بازگشتی
# --------------------------------------------------------

def recursive_find(data, wanted_keys):
    results = []

    def walk(value, path="root"):

        if len(results) >= 500:
            return

        if isinstance(value, dict):

            for key, child in value.items():

                current_path = (
                    f"{path}.{key}"
                )

                if key in wanted_keys:
                    results.append(
                        (
                            current_path,
                            child,
                        )
                    )

                walk(
                    child,
                    current_path,
                )

        elif isinstance(value, list):

            for index, child in enumerate(
                value
            ):

                walk(
                    child,
                    f"{path}[{index}]",
                )

    walk(data)

    return results


# --------------------------------------------------------
# پیدا کردن بخش مهم
# --------------------------------------------------------

def find_section(root, names):
    results = recursive_find(
        root,
        set(names),
    )

    if not results:
        return None

    # اولویت با content واقعی مسابقه
    for path, value in results:

        if (
            "pageProps.content" in path
            and isinstance(value, (dict, list))
        ):
            return value

    return results[0][1]


# --------------------------------------------------------
# استخراج content واقعی
# --------------------------------------------------------

def get_content(root):
    content = get_nested(
        root,
        "props",
        "pageProps",
        "content",
    )

    if not isinstance(content, dict):
        raise RuntimeError(
            "FotMob content not found."
        )

    return content


# --------------------------------------------------------
# پیدا کردن اسم یک تیم
# --------------------------------------------------------

def get_team_name(team):
    if not isinstance(team, dict):
        return ""

    return clean_text(
        first_non_empty(
            team.get("longName"),
            team.get("name"),
            team.get("shortName"),
            team.get("title"),
        )
    )


# --------------------------------------------------------
# اطلاعات پایه بازی
# --------------------------------------------------------

def extract_basic_info(root):
    event_jsonld = get_nested(
        root,
        "props",
        "pageProps",
        "seo",
        "eventJSONLD",
    )

    content = get_content(root)

    info = {
        "home": "",
        "away": "",
        "start": "",
        "league": "",
        "venue": "",
        "status": "",
        "score": "",
    }

    # ----------------------------------------------------
    # اسم تیم‌ها و زمان از eventJSONLD
    # ----------------------------------------------------

    if isinstance(event_jsonld, dict):

        home_team = event_jsonld.get(
            "homeTeam"
        )

        away_team = event_jsonld.get(
            "awayTeam"
        )

        if isinstance(home_team, dict):
            info["home"] = clean_text(
                home_team.get("name")
            )

        if isinstance(away_team, dict):
            info["away"] = clean_text(
                away_team.get("name")
            )

        info["start"] = clean_text(
            event_jsonld.get("startDate")
        )

    # ----------------------------------------------------
    # اطلاعات تیم‌ها از content
    # ----------------------------------------------------

    for side in ("home", "away"):

        if info[side]:
            continue

        possible_keys = (
            f"{side}Team",
            side,
        )

        for key in possible_keys:

            value = content.get(key)

            if isinstance(value, dict):

                name = get_team_name(
                    value
                )

                if name:
                    info[side] = name
                    break

    # ----------------------------------------------------
    # رقابت
    # ----------------------------------------------------

    league_keys = (
        "league",
        "tournament",
        "competition",
        "parentTournament",
        "parentLeague",
        "competitionName",
        "leagueName",
    )

    for key in league_keys:

        value = content.get(key)

        if isinstance(value, dict):

            name = first_non_empty(
                value.get("name"),
                value.get("longName"),
                value.get("shortName"),
            )

            if name:
                info["league"] = clean_text(
                    name
                )
                break

        elif isinstance(value, str):

            if value.strip():
                info["league"] = value.strip()
                break

    # ----------------------------------------------------
    # fallback برای رقابت
    # ----------------------------------------------------

    if not info["league"]:

        league_results = recursive_find(
            content,
            {
                "leagueName",
                "competitionName",
                "tournamentName",
            },
        )

        for _, value in league_results:

            if isinstance(value, str):

                value = value.strip()

                if value:
                    info["league"] = value
                    break

    # ----------------------------------------------------
    # ورزشگاه
    # ----------------------------------------------------

    for key in (
        "venue",
        "stadium",
    ):

        value = content.get(key)

        if isinstance(value, dict):

            name = first_non_empty(
                value.get("name"),
                value.get("longName"),
            )

            if name:
                info["venue"] = clean_text(
                    name
                )
                break

        elif isinstance(value, str):

            if value.strip():
                info["venue"] = value.strip()
                break

    return info


# --------------------------------------------------------
# زمان بازی
# --------------------------------------------------------

def format_match_time(value):
    if not value:
        return "نامشخص"

    try:
        value = str(value)

        if value.endswith("Z"):
            value = value[:-1] + "+00:00"

        dt = datetime.fromisoformat(value)

        if dt.tzinfo is None:
            dt = dt.replace(
                tzinfo=timezone.utc
            )

        iran_time = dt.astimezone(
            IRAN_TIMEZONE
        )

        return iran_time.strftime(
            "%H:%M"
        )

    except Exception:
        return str(value)


# --------------------------------------------------------
# استخراج زمان
# --------------------------------------------------------

def get_match_start(root, content):
    event_jsonld = get_nested(
        root,
        "props",
        "pageProps",
        "seo",
        "eventJSONLD",
    )

    if isinstance(event_jsonld, dict):

        value = event_jsonld.get(
            "startDate"
        )

        if value:
            return value

    if isinstance(content, dict):

        status = content.get(
            "status"
        )

        if isinstance(status, dict):

            for key in (
                "utcTime",
                "startTime",
                "startDate",
            ):

                if status.get(key):
                    return status[key]

        for key in (
            "utcTime",
            "startTime",
            "startDate",
        ):

            if content.get(key):
                return content[key]

    return ""


# --------------------------------------------------------
# تشخیص پایان بازی
# --------------------------------------------------------

def is_match_finished(content):
    status = content.get(
        "status"
    )

    if isinstance(status, dict):

        if status.get("finished") is True:
            return True

        values = []

        for key in (
            "reason",
            "name",
            "short",
            "long",
            "status",
        ):

            value = status.get(key)

            if value is not None:
                values.append(
                    str(value).lower()
                )

        status_text = " ".join(values)

        finished_words = (
            "full time",
            "finished",
            "complete",
            "completed",
            "ft",
        )

        for word in finished_words:

            if word in status_text:
                return True

    return False


# --------------------------------------------------------
# پیدا کردن lineup
# --------------------------------------------------------

def get_lineup(content, root):
    lineup = content.get(
        "lineup"
    )

    if isinstance(lineup, dict):
        return lineup

    lineup = find_section(
        root,
        ["lineup"],
    )

    if isinstance(lineup, dict):
        return lineup

    return None


# --------------------------------------------------------
# پیدا کردن تیم داخل lineup
# --------------------------------------------------------

def get_lineup_team(lineup, side):
    if not isinstance(lineup, dict):
        return None

    aliases = {
        "home": (
            "home",
            "homeTeam",
            "homeTeamData",
        ),
        "away": (
            "away",
            "awayTeam",
            "awayTeamData",
        ),
    }

    for key in aliases.get(
        side,
        (),
    ):

        team = lineup.get(key)

        if isinstance(team, dict):
            return team

    teams = lineup.get("teams")

    if isinstance(teams, dict):

        for key in aliases.get(
            side,
            (),
        ):

            team = teams.get(key)

            if isinstance(team, dict):
                return team

    wanted_name = (
        "home" if side == "home"
        else "away"
    )

    for key, value in lineup.items():

        if not isinstance(value, dict):
            continue

        key_lower = str(key).lower()

        if wanted_name in key_lower:
            return value

    return None


# --------------------------------------------------------
# پیدا کردن لیست بازیکنان
# --------------------------------------------------------

def find_player_list(team):
    if not isinstance(team, dict):
        return []

    for key in (
        "players",
        "lineup",
        "playerList",
        "startingXI",
        "startingLineup",
    ):

        value = team.get(key)

        if isinstance(value, list):
            return value

    results = recursive_find(
        team,
        {
            "players",
            "playerList",
            "startingXI",
            "startingLineup",
        },
    )

    for _, value in results:

        if isinstance(value, list):
            return value

    return []


# --------------------------------------------------------
# تشخیص Starter
# --------------------------------------------------------

def is_player_starter(player):
    if not isinstance(player, dict):
        return False

    for key in (
        "isStarter",
        "starter",
        "starting",
        "isStarting",
        "isStartingXI",
    ):

        value = player.get(key)

        if value is True:
            return True

        if isinstance(value, str):

            if value.lower().strip() in (
                "true",
                "yes",
                "starter",
                "starting",
            ):
                return True

    nested_player = player.get(
        "player"
    )

    if isinstance(nested_player, dict):

        for key in (
            "isStarter",
            "starter",
            "starting",
            "isStarting",
            "isStartingXI",
        ):

            value = nested_player.get(
                key
            )

            if value is True:
                return True

            if isinstance(value, str):

                if value.lower().strip() in (
                    "true",
                    "yes",
                    "starter",
                    "starting",
                ):
                    return True

    return False


# --------------------------------------------------------
# تشخیص Substitute
# --------------------------------------------------------

def is_player_substitute(player):
    if not isinstance(player, dict):
        return False

    for key in (
        "isSubstitute",
        "substitute",
        "isSub",
        "bench",
    ):

        value = player.get(key)

        if value is True:
            return True

        if isinstance(value, str):

            if value.lower().strip() in (
                "true",
                "yes",
                "substitute",
                "bench",
            ):
                return True

    return False


# --------------------------------------------------------
# استخراج Starterها
# --------------------------------------------------------

def get_starters(team):
    if not isinstance(team, dict):
        return []

    for key in (
        "starters",
        "startingXI",
        "startingLineup",
    ):

        value = team.get(key)

        if isinstance(value, list) and value:
            return value

    players = find_player_list(
        team
    )

    if players:

        starters = [
            player
            for player in players
            if is_player_starter(player)
        ]

        if starters:
            return starters

    return []


# --------------------------------------------------------
# استخراج Substituteها
# --------------------------------------------------------

def get_substitutes(team):
    if not isinstance(team, dict):
        return []

    for key in (
        "substitutes",
        "subs",
        "bench",
    ):

        value = team.get(key)

        if isinstance(value, list):
            return value

    players = find_player_list(
        team
    )

    if players:

        substitutes = [
            player
            for player in players
            if (
                is_player_substitute(player)
                and not is_player_starter(player)
            )
        ]

        if substitutes:
            return substitutes

    return []


# --------------------------------------------------------
# نام بازیکن
# --------------------------------------------------------

def get_player_name(player):
    if not isinstance(player, dict):
        return ""

    for key in (
        "name",
        "playerName",
        "longName",
        "shortName",
    ):

        value = player.get(key)

        if isinstance(value, str):

            value = value.strip()

            if value:
                return value

    nested_player = player.get(
        "player"
    )

    if isinstance(nested_player, dict):

        for key in (
            "name",
            "playerName",
            "longName",
            "shortName",
        ):

            value = nested_player.get(
                key
            )

            if value:
                return str(
                    value
                ).strip()

    return ""


# --------------------------------------------------------
# Rating
# --------------------------------------------------------

def get_player_rating(player):
    if not isinstance(player, dict):
        return None

    candidates = [
        player.get("rating"),
        player.get("ratingScore"),
        player.get("matchRating"),
    ]

    nested_player = player.get(
        "player"
    )

    if isinstance(nested_player, dict):

        candidates.extend(
            [
                nested_player.get(
                    "rating"
                ),
                nested_player.get(
                    "ratingScore"
                ),
                nested_player.get(
                    "matchRating"
                ),
            ]
        )

    for value in candidates:

        if value is None:
            continue

        try:
            return float(value)
        except (
            TypeError,
            ValueError,
        ):
            pass

    return None


# --------------------------------------------------------
# استخراج positionId
# --------------------------------------------------------

def get_player_position_id(player):
    if not isinstance(player, dict):
        return None

    for key in (
        "positionId",
        "positionID",
        "position_id",
    ):

        value = player.get(key)

        if value is not None:

            try:
                return int(value)
            except (
                TypeError,
                ValueError,
            ):
                pass

    nested_player = player.get(
        "player"
    )

    if isinstance(nested_player, dict):

        for key in (
            "positionId",
            "positionID",
            "position_id",
        ):

            value = nested_player.get(key)

            if value is not None:

                try:
                    return int(value)
                except (
                    TypeError,
                    ValueError,
                ):
                    pass

    return None


# --------------------------------------------------------
# تبدیل positionId به گروه پایه
#
# نکته بسیار مهم:
#
# این تابع دیگر مستقیماً تعیین نمی‌کند که بازیکن
# در پیام نهایی در خط هافبک یا حمله قرار بگیرد.
#
# بعضی positionIdها مثل 78 و 82 و 84 و ... در
# ترکیب‌های مختلف می‌توانند نقش متفاوتی داشته باشند.
# --------------------------------------------------------

def position_group(player):
    position_id = get_player_position_id(
        player
    )

    if position_id is None:
        return "unknown"

    # دروازه‌بان
    if position_id == 11:
        return "goalkeeper"

    # مدافع‌های قطعی
    if position_id in {
        32,
        33,
        34,
        35,
        36,
        37,
        38,
    }:
        return "defender"

    # هافبک‌های قطعی
    if position_id in {
        51,
        59,
        62,
        64,
        65,
        66,
        68,
        71,
        72,
        73,
        74,
        75,
        76,
        77,
        79,
    }:
        return "midfielder"

    # بازیکنان مرزی بین هافبک و حمله
    if position_id in {
        78,
        82,
        83,
        84,
        85,
        86,
        87,
        88,
        103,
        107,
    }:
        return "wide_attacker"

    # مهاجم‌های مرکزی قطعی
    if position_id in {
        104,
        105,
        106,
        115,
    }:
        return "attacker"

    return "unknown"


# --------------------------------------------------------
# layout بازیکن
# --------------------------------------------------------

def get_player_layout(player):
    if not isinstance(player, dict):
        return None, None

    sources = [
        player,
        player.get("player"),
    ]

    for source in sources:

        if not isinstance(source, dict):
            continue

        horizontal = None
        vertical = None

        for key in (
            "horizontalLayout",
            "horizontal",
            "x",
        ):

            if source.get(key) is not None:
                horizontal = source.get(key)
                break

        for key in (
            "verticalLayout",
            "vertical",
            "y",
        ):

            if source.get(key) is not None:
                vertical = source.get(key)
                break

        if (
            horizontal is not None
            or vertical is not None
        ):

            try:
                if horizontal is not None:
                    horizontal = float(horizontal)
            except (
                TypeError,
                ValueError,
            ):
                horizontal = None

            try:
                if vertical is not None:
                    vertical = float(vertical)
            except (
                TypeError,
                ValueError,
            ):
                vertical = None

            return (
                horizontal,
                vertical,
            )

    return None, None


# --------------------------------------------------------
# تبدیل layout به عدد
# --------------------------------------------------------

def numeric_layout_value(value):
    if value is None:
        return None

    try:
        return float(value)
    except (
        TypeError,
        ValueError,
    ):
        return None


# --------------------------------------------------------
# تشخیص Formation
# --------------------------------------------------------

def get_formation(team):
    if not isinstance(team, dict):
        return ""

    direct_keys = (
        "formation",
        "formationName",
        "system",
        "shape",
    )

    for key in direct_keys:

        value = team.get(key)

        if isinstance(value, str):

            value = value.strip()

            if re.fullmatch(
                r"\d+(?:-\d+)+",
                value,
            ):
                return value

        elif isinstance(value, dict):

            name = first_non_empty(
                value.get("name"),
                value.get("formation"),
                value.get("value"),
            )

            if name:

                name = clean_text(
                    name
                )

                if re.fullmatch(
                    r"\d+(?:-\d+)+",
                    name,
                ):
                    return name

    results = recursive_find(
        team,
        {
            "formation",
            "formationName",
            "system",
            "shape",
        },
    )

    for _, value in results:

        if isinstance(value, str):

            value = value.strip()

            if re.fullmatch(
                r"\d+(?:-\d+)+",
                value,
            ):
                return value

        elif isinstance(value, dict):

            name = first_non_empty(
                value.get("name"),
                value.get("formation"),
                value.get("value"),
            )

            if name:

                name = clean_text(
                    name
                )

                if re.fullmatch(
                    r"\d+(?:-\d+)+",
                    name,
                ):
                    return name

    return ""


# --------------------------------------------------------
# تبدیل Formation به خطوط
#
# 3-4-3 -> دفاع 3، هافبک 4، حمله 3
# 4-4-2 -> دفاع 4، هافبک 4، حمله 2
# 4-2-3-1 -> دفاع 4، هافبک 5، حمله 1
# 3-5-2 -> دفاع 3، هافبک 5، حمله 2
# --------------------------------------------------------

def parse_formation(formation):
    if not formation:
        return None

    parts = formation.split("-")

    numbers = []

    for part in parts:

        try:
            number = int(part)
        except (
            TypeError,
            ValueError,
        ):
            return None

        if number <= 0:
            return None

        numbers.append(number)

    # در Formation استاندارد، مجموع خطوط خارج از GK باید 10 باشد
    if len(numbers) < 2:
        return None

    if sum(numbers) != 10:
        return None

    defenders = numbers[0]
    attackers = numbers[-1]

    midfielders = sum(
        numbers[1:-1]
    )

    return {
        "defenders": defenders,
        "midfielders": midfielders,
        "attackers": attackers,
        "lines": numbers,
    }


# --------------------------------------------------------
# مربی
# --------------------------------------------------------

def get_coach(team):
    if not isinstance(team, dict):
        return ""

    for key in (
        "coach",
        "manager",
        "headCoach",
        "headcoach",
        "managerInfo",
    ):

        value = team.get(key)

        if isinstance(value, dict):

            name = first_non_empty(
                value.get("name"),
                value.get("longName"),
                value.get("shortName"),
            )

            if name:
                return clean_text(name)

        elif isinstance(value, str):

            if value.strip():
                return value.strip()

    results = recursive_find(
        team,
        {
            "coach",
            "manager",
            "headCoach",
            "headcoach",
        },
    )

    for _, value in results:

        if isinstance(value, dict):

            name = first_non_empty(
                value.get("name"),
                value.get("longName"),
                value.get("shortName"),
            )

            if name:
                return clean_text(name)

        elif isinstance(value, str):

            if value.strip():
                return value.strip()

    return ""


# --------------------------------------------------------
# بازیکن را بر اساس اطلاعات پایه به یکی از گروه‌ها
# اختصاص می‌دهد.
#
# خروجی:
# goalkeeper
# defender
# midfielder
# wide_attacker
# attacker
# unknown
# --------------------------------------------------------

def get_base_player_role(player):
    return position_group(
        player
    )


# --------------------------------------------------------
# امتیاز اطمینان برای اینکه بازیکن ذاتاً متعلق به
# کدام خط است.
#
# عدد بزرگ‌تر = اطمینان بیشتر
# --------------------------------------------------------

def role_priority(player, target_role):
    role = get_base_player_role(
        player
    )

    if target_role == "defender":

        if role == "defender":
            return 100

        if role == "unknown":
            return 20

        return 0

    if target_role == "midfielder":

        if role == "midfielder":
            return 100

        # بازیکنان wide_attacker را عمداً
        # می‌توانیم برای تکمیل خط هافبک استفاده کنیم.
        if role == "wide_attacker":
            return 60

        if role == "unknown":
            return 20

        return 0

    if target_role == "attacker":

        if role == "attacker":
            return 100

        if role == "wide_attacker":
            return 60

        if role == "unknown":
            return 20

        return 0

    return 0


# --------------------------------------------------------
# فاصله عمقی بازیکن
#
# اگر layout عمودی وجود داشته باشد، از آن برای
# تشخیص اینکه بازیکن جلوتر یا عقب‌تر قرار گرفته
# استفاده می‌کنیم.
# --------------------------------------------------------

def get_depth(player):
    _, vertical = get_player_layout(
        player
    )

    return numeric_layout_value(
        vertical
    )


# --------------------------------------------------------
# مرتب کردن بازیکنان یک خط از چپ به راست
#
# horizontalLayout در FotMob برای تعیین جای افقی
# بازیکن استفاده می‌شود.
# --------------------------------------------------------

def sort_line_players(players):
    if not players:
        return []

    decorated = []

    has_horizontal = False

    for index, player in enumerate(
        players
    ):

        horizontal, _ = get_player_layout(
            player
        )

        horizontal = numeric_layout_value(
            horizontal
        )

        if horizontal is not None:
            has_horizontal = True

        decorated.append(
            (
                index,
                player,
                horizontal,
            )
        )

    if not has_horizontal:
        return players

    decorated.sort(
        key=lambda item: (
            item[2]
            if item[2] is not None
            else 999999
        )
    )

    return [
        item[1]
        for item in decorated
    ]


# --------------------------------------------------------
# انتخاب بازیکنان بر اساس Formation
#
# این مهم‌ترین بخش جدید است.
#
# positionId دیگر به تنهایی تعیین‌کننده خط نیست.
# Formation تعیین می‌کند چند نفر باید در هر خط باشند.
# --------------------------------------------------------

def organize_players(
    starters,
    formation,
):
    groups = {
        "goalkeeper": [],
        "defender": [],
        "midfielder": [],
        "attacker": [],
        "unknown": [],
    }

    if not starters:
        return groups

    formation_info = parse_formation(
        formation
    )

    # ----------------------------------------------------
    # اگر Formation معتبر نبود،
    # fallback به positionId
    # ----------------------------------------------------

    if not formation_info:

        for player in starters:

            role = get_base_player_role(
                player
            )

            if role == "goalkeeper":
                groups["goalkeeper"].append(
                    player
                )

            elif role == "defender":
                groups["defender"].append(
                    player
                )

            elif role == "midfielder":
                groups["midfielder"].append(
                    player
                )

            elif role in (
                "wide_attacker",
                "attacker",
            ):
                groups["attacker"].append(
                    player
                )

            else:
                groups["unknown"].append(
                    player
                )

        return groups

    # ----------------------------------------------------
    # اول دروازه‌بان
    # ----------------------------------------------------

    goalkeeper = None

    for player in starters:

        if get_base_player_role(
            player
        ) == "goalkeeper":

            goalkeeper = player
            break

    if goalkeeper is not None:

        groups["goalkeeper"].append(
            goalkeeper
        )

    remaining = [
        player
        for player in starters
        if player is not goalkeeper
    ]

    # ----------------------------------------------------
    # تعداد موردنیاز
    # ----------------------------------------------------

    defender_count = (
        formation_info["defenders"]
    )

    midfielder_count = (
        formation_info["midfielders"]
    )

    attacker_count = (
        formation_info["attackers"]
    )

    # ----------------------------------------------------
    # دفاع
    #
    # اول مدافع‌های قطعی را انتخاب می‌کنیم.
    # ----------------------------------------------------

    defenders = [
        player
        for player in remaining
        if get_base_player_role(
            player
        ) == "defender"
    ]

    # اگر تعداد مدافع قطعی بیشتر از Formation بود،
    # با layout عمقی نزدیک‌ترین‌ها به خط دفاعی را
    # نگه می‌داریم.
    if len(defenders) > defender_count:

        defenders_with_depth = []

        for player in defenders:

            depth = get_depth(
                player
            )

            defenders_with_depth.append(
                (
                    player,
                    depth,
                )
            )

        usable_depth = [
            item
            for item in defenders_with_depth
            if item[1] is not None
        ]

        if usable_depth:

            usable_depth.sort(
                key=lambda item: item[1]
            )

            defenders = [
                item[0]
                for item in usable_depth[
                    :defender_count
                ]
            ]

        else:

            defenders = defenders[
                :defender_count
            ]

    # اگر مدافع کافی نداریم، unknown را اضافه می‌کنیم.
    if len(defenders) < defender_count:

        candidates = [
            player
            for player in remaining
            if (
                player not in defenders
                and get_base_player_role(
                    player
                ) == "unknown"
            )
        ]

        needed = (
            defender_count
            - len(defenders)
        )

        defenders.extend(
            candidates[:needed]
        )

    for player in defenders:
        if player in remaining:
            remaining.remove(
                player
            )

    groups["defender"] = defenders

    # ----------------------------------------------------
    # مهاجم‌های قطعی
    #
    # فقط مهاجمان مرکزی قطعی را اینجا می‌گیریم.
    # wide_attacker فعلاً آزاد می‌ماند تا Formation
    # تعیین کند هافبک است یا مهاجم.
    # ----------------------------------------------------

    pure_attackers = [
        player
        for player in remaining
        if get_base_player_role(
            player
        ) == "attacker"
    ]

    # تعداد مهاجم قطعی موردنیاز
    pure_attackers_to_take = min(
        len(pure_attackers),
        attacker_count,
    )

    attackers = pure_attackers[
        :pure_attackers_to_take
    ]

    for player in attackers:
        if player in remaining:
            remaining.remove(
                player
            )

    # ----------------------------------------------------
    # حالا بازیکنان باقی‌مانده را داریم.
    #
    # معمولاً اینها ترکیبی از:
    # - هافبک‌های قطعی
    # - وینگرها
    # - بازیکنان ناشناخته
    # هستند.
    # ----------------------------------------------------

    fixed_midfielders = [
        player
        for player in remaining
        if get_base_player_role(
            player
        ) == "midfielder"
    ]

    wide_players = [
        player
        for player in remaining
        if get_base_player_role(
            player
        ) == "wide_attacker"
    ]

    unknown_players = [
        player
        for player in remaining
        if get_base_player_role(
            player
        ) == "unknown"
    ]

    # ----------------------------------------------------
    # اول هافبک‌های قطعی را وارد خط هافبک می‌کنیم.
    # ----------------------------------------------------

    midfielders = fixed_midfielders[
        :midfielder_count
    ]

    for player in midfielders:
        if player in remaining:
            remaining.remove(
                player
            )

    # ----------------------------------------------------
    # ظرفیت باقی‌مانده خط هافبک
    # ----------------------------------------------------

    midfield_need = (
        midfielder_count
        - len(midfielders)
    )

    # ----------------------------------------------------
    # وینگرها را با توجه به Formation تقسیم می‌کنیم.
    #
    # این قسمت دقیقاً مشکل بازی KV Mechelen و
    # Anderlecht را حل می‌کند.
    # ----------------------------------------------------

    if midfield_need > 0:

        wide_sorted = list(
            wide_players
        )

        # اگر verticalLayout داریم، بازیکنان
        # عقب‌تر را برای تکمیل خط هافبک ترجیح می‌دهیم.
        wide_with_depth = []

        for player in wide_sorted:

            depth = get_depth(
                player
            )

            wide_with_depth.append(
                (
                    player,
                    depth,
                )
            )

        if any(
            depth is not None
            for _, depth
            in wide_with_depth
        ):

            wide_with_depth.sort(
                key=lambda item: (
                    item[1]
                    if item[1] is not None
                    else 999999
                )
            )

            wide_sorted = [
                item[0]
                for item in wide_with_depth
            ]

        selected = wide_sorted[
            :midfield_need
        ]

        midfielders.extend(
            selected
        )

        for player in selected:

            if player in remaining:
                remaining.remove(
                    player
                )

            if player in wide_players:
                wide_players.remove(
                    player
                )

    # ----------------------------------------------------
    # حالا ظرفیت باقی‌مانده مهاجمان
    # ----------------------------------------------------

    attacker_need = (
        attacker_count
        - len(attackers)
    )

    if attacker_need > 0:

        # وینگرهای باقی‌مانده اولویت دارند.
        selected = wide_players[
            :attacker_need
        ]

        attackers.extend(
            selected
        )

        for player in selected:

            if player in remaining:
                remaining.remove(
                    player
                )

            if player in wide_players:
                wide_players.remove(
                    player
                )

    # ----------------------------------------------------
    # اگر هنوز خط هافبک کامل نشده،
    # از unknown استفاده می‌کنیم.
    # ----------------------------------------------------

    if len(midfielders) < midfielder_count:

        midfield_need = (
            midfielder_count
            - len(midfielders)
        )

        candidates = [
            player
            for player in unknown_players
            if player in remaining
        ]

        selected = candidates[
            :midfield_need
        ]

        midfielders.extend(
            selected
        )

        for player in selected:

            if player in remaining:
                remaining.remove(
                    player
                )

    # ----------------------------------------------------
    # اگر هنوز خط حمله کامل نشده،
    # از unknown باقی‌مانده استفاده می‌کنیم.
    # ----------------------------------------------------

    if len(attackers) < attacker_count:

        attacker_need = (
            attacker_count
            - len(attackers)
        )

        candidates = [
            player
            for player in unknown_players
            if player in remaining
        ]

        selected = candidates[
            :attacker_need
        ]

        attackers.extend(
            selected
        )

        for player in selected:

            if player in remaining:
                remaining.remove(
                    player
                )

    # ----------------------------------------------------
    # اگر هنوز بازیکنی باقی مانده،
    # گم نمی‌شود.
    # ----------------------------------------------------

    groups["midfielder"] = midfielders
    groups["attacker"] = attackers

    groups["unknown"] = [
        player
        for player in remaining
    ]

    # ----------------------------------------------------
    # مرتب‌سازی داخل خطوط
    # ----------------------------------------------------

    groups["goalkeeper"] = sort_line_players(
        groups["goalkeeper"]
    )

    groups["defender"] = sort_line_players(
        groups["defender"]
    )

    groups["midfielder"] = sort_line_players(
        groups["midfielder"]
    )

    groups["attacker"] = sort_line_players(
        groups["attacker"]
    )

    groups["unknown"] = sort_line_players(
        groups["unknown"]
    )

    return groups


# --------------------------------------------------------
# فرمت نام بازیکن
# --------------------------------------------------------

def format_player(
    player,
    show_rating,
):
    name = get_player_name(
        player
    )

    if not name:
        return ""

    if not show_rating:
        return name

    rating = get_player_rating(
        player
    )

    if rating is None:
        return name

    return f"{name} {rating:.1f}"


# --------------------------------------------------------
# فرمت یک خط بازیکنان
# --------------------------------------------------------

def format_player_line(
    icon,
    players,
    show_rating,
):
    names = []

    for player in players:

        name = format_player(
            player,
            show_rating,
        )

        if name:
            names.append(
                name
            )

    if not names:
        return ""

    return (
        f"{icon} "
        + " | ".join(names)
    )


# --------------------------------------------------------
# فرمت ترکیب یک تیم
# --------------------------------------------------------

def format_team_lineup(
    team_name,
    team,
    show_rating,
    team_icon,
):
    if not isinstance(team, dict):
        return (
            f"{team_icon} "
            f"{team_name}\n"
            "اطلاعات ترکیب پیدا نشد."
        )

    starters = get_starters(
        team
    )

    substitutes = get_substitutes(
        team
    )

    coach = get_coach(
        team
    )

    formation = get_formation(
        team
    )

    groups = organize_players(
        starters,
        formation,
    )

    lines = []

    lines.append(
        f"{team_icon} {team_name}"
    )

    if coach:
        lines.append(
            f"👔 {coach}"
        )

    if formation:
        lines.append(
            f"📐 {formation}"
        )

    lines.append("")

    line = format_player_line(
        "🧤",
        groups["goalkeeper"],
        show_rating,
    )

    if line:
        lines.append(line)

    line = format_player_line(
        "🛡",
        groups["defender"],
        show_rating,
    )

    if line:
        lines.append(line)

    line = format_player_line(
        "⚙️",
        groups["midfielder"],
        show_rating,
    )

    if line:
        lines.append(line)

    line = format_player_line(
        "⚡",
        groups["attacker"],
        show_rating,
    )

    if line:
        lines.append(line)

    # اگر به هر دلیل بازیکنی در هیچ خطی قرار نگرفت،
    # آن را گم نمی‌کنیم.
    if groups["unknown"]:

        unknown_line = format_player_line(
            "⚽",
            groups["unknown"],
            show_rating,
        )

        if unknown_line:
            lines.append(
                unknown_line
            )

    lines.append("")

    substitute_names = []

    for player in substitutes:

        name = format_player(
            player,
            show_rating,
        )

        if name:
            substitute_names.append(
                name
            )

    if substitute_names:

        lines.append(
            "🔄 "
            + " | ".join(
                substitute_names
            )
        )

    return "\n".join(lines)


# --------------------------------------------------------
# ساخت پیام نهایی
# --------------------------------------------------------

def build_message(root):
    content = get_content(
        root
    )

    info = extract_basic_info(
        root
    )

    home_name = (
        info["home"]
        or "Home"
    )

    away_name = (
        info["away"]
        or "Away"
    )

    league = (
        info["league"]
        or "نامشخص"
    )

    start_time = get_match_start(
        root,
        content,
    )

    kickoff = format_match_time(
        start_time
    )

    finished = is_match_finished(
        content
    )

    print()
    print(
        "MATCH FINISHED:",
        finished,
    )

    show_rating = finished

    lineup = get_lineup(
        content,
        root,
    )

    if not isinstance(
        lineup,
        dict,
    ):
        raise RuntimeError(
            "LINEUP OBJECT NOT FOUND."
        )

    lineup_type = lineup.get(
        "lineupType"
    )

    print(
        "LINEUP TYPE:",
        lineup_type,
    )

    home_team = get_lineup_team(
        lineup,
        "home",
    )

    away_team = get_lineup_team(
        lineup,
        "away",
    )

    if not home_team:
        raise RuntimeError(
            "HOME LINEUP NOT FOUND."
        )

    if not away_team:
        raise RuntimeError(
            "AWAY LINEUP NOT FOUND."
        )

    home_starters = get_starters(
        home_team
    )

    away_starters = get_starters(
        away_team
    )

    home_subs = get_substitutes(
        home_team
    )

    away_subs = get_substitutes(
        away_team
    )

    home_coach = get_coach(
        home_team
    )

    away_coach = get_coach(
        away_team
    )

    home_formation = get_formation(
        home_team
    )

    away_formation = get_formation(
        away_team
    )

    print(
        f"{home_name}: "
        f"{len(home_starters)} starters, "
        f"{len(home_subs)} substitutes"
    )

    print(
        f"{away_name}: "
        f"{len(away_starters)} starters, "
        f"{len(away_subs)} substitutes"
    )

    print(
        f"{home_name} coach:",
        home_coach or "NOT FOUND",
    )

    print(
        f"{away_name} coach:",
        away_coach or "NOT FOUND",
    )

    print(
        f"{home_name} formation:",
        home_formation or "NOT FOUND",
    )

    print(
        f"{away_name} formation:",
        away_formation or "NOT FOUND",
    )

    print(
        "LEAGUE:",
        league,
    )

    # ----------------------------------------------------
    # بررسی positionIdها
    # ----------------------------------------------------

    print("")
    print("-" * 70)
    print("POSITION IDS / BASE ROLES")
    print("-" * 70)

    for player in (
        home_starters
        + away_starters
    ):

        name = get_player_name(
            player
        )

        position_id = (
            get_player_position_id(
                player
            )
        )

        role = position_group(
            player
        )

        horizontal, vertical = (
            get_player_layout(
                player
            )
        )

        print(
            f"{name}: "
            f"positionId={position_id} "
            f"→ {role} "
            f"| x={horizontal} "
            f"| y={vertical}"
        )

    print("-" * 70)

    # ----------------------------------------------------
    # نمایش نتیجه نهایی تقسیم خطوط برای دیباگ
    # ----------------------------------------------------

    print("")
    print("-" * 70)
    print("FINAL FORMATION GROUPS")
    print("-" * 70)

    for label, team, starters, formation in (
        (
            home_name,
            home_team,
            home_starters,
            home_formation,
        ),
        (
            away_name,
            away_team,
            away_starters,
            away_formation,
        ),
    ):

        groups = organize_players(
            starters,
            formation,
        )

        print("")
        print(
            label,
            "| Formation:",
            formation,
        )

        print(
            "GK:",
            [
                get_player_name(player)
                for player
                in groups["goalkeeper"]
            ],
        )

        print(
            "DEF:",
            [
                get_player_name(player)
                for player
                in groups["defender"]
            ],
        )

        print(
            "MID:",
            [
                get_player_name(player)
                for player
                in groups["midfielder"]
            ],
        )

        print(
            "ATT:",
            [
                get_player_name(player)
                for player
                in groups["attacker"]
            ],
        )

        print(
            "UNKNOWN:",
            [
                get_player_name(player)
                for player
                in groups["unknown"]
            ],
        )

    print("-" * 70)

    # ----------------------------------------------------
    # ساخت پیام
    # ----------------------------------------------------

    message = []

    message.append(
        f"🏆 {league}"
    )

    message.append("")

    message.append(
        f"⚽️ {home_name} 🆚 {away_name}"
    )

    message.append(
        f"🕐 {kickoff} به وقت ایران"
    )

    message.append("")

    message.append(
        format_team_lineup(
            home_name,
            home_team,
            show_rating,
            "🔴",
        )
    )

    message.append("")

    message.append(
        format_team_lineup(
            away_name,
            away_team,
            show_rating,
            "🔵",
        )
    )

    return "\n".join(message)


# --------------------------------------------------------
# اجرای تست
# --------------------------------------------------------

def main():

    print("")
    print("#" * 70)
    print(
        "FOTMOB → TELEGRAM MATCH "
        "STRUCTURE TEST"
    )
    print("#" * 70)

    html = fetch_match_page()

    root = extract_next_data(
        html
    )

    # ----------------------------------------------------
    # ذخیره JSON خام
    # ----------------------------------------------------

    with open(
        "match_5811755_raw.json",
        "w",
        encoding="utf-8",
    ) as file:

        json.dump(
            root,
            file,
            ensure_ascii=False,
            indent=2,
        )

    print(
        "Raw JSON saved: "
        "match_5811755_raw.json"
    )

    # ----------------------------------------------------
    # ساخت پیام
    # ----------------------------------------------------

    message = build_message(
        root
    )

    print("")
    print("=" * 70)
    print("MESSAGE TO TELEGRAM")
    print("=" * 70)
    print(message)
    print("=" * 70)

    # ----------------------------------------------------
    # تقسیم پیام
    # ----------------------------------------------------

    max_length = 4000

    chunks = []

    remaining = message

    while len(remaining) > max_length:

        cut = remaining.rfind(
            "\n",
            0,
            max_length,
        )

        if cut == -1:
            cut = max_length

        chunks.append(
            remaining[:cut]
        )

        remaining = remaining[
            cut:
        ].lstrip()

    if remaining:
        chunks.append(
            remaining
        )

    print(
        f"Telegram messages to send: "
        f"{len(chunks)}"
    )

    # ----------------------------------------------------
    # ارسال
    # ----------------------------------------------------

    for index, chunk in enumerate(
        chunks,
        1,
    ):

        print(
            f"Sending message "
            f"{index}/{len(chunks)}..."
        )

        send_telegram(
            chunk
        )

    print("")
    print("=" * 70)
    print("TEST SUCCESSFUL")
    print("=" * 70)


if __name__ == "__main__":
    main()

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
    # fallback برای رقابت:
    # جستجوی بازگشتی فقط در محدوده content
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

    # حالت‌های رایج
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

    # بعضی نسخه‌ها تیم‌ها را داخل teams می‌گذارند
    teams = lineup.get("teams")

    if isinstance(teams, dict):

        for key in aliases.get(
            side,
            (),
        ):

            team = teams.get(key)

            if isinstance(team, dict):
                return team

    # ----------------------------------------------------
    # fallback:
    # اگر ساختار شامل homeTeam/awayTeam باشد
    # ولی نام کلید متفاوت باشد
    # ----------------------------------------------------

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

    # اولویت با کلیدهای شناخته‌شده
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

    # fallback: جستجوی بازگشتی
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
# تشخیص اینکه بازیکن starter است یا نه
# --------------------------------------------------------

def is_player_starter(player):
    if not isinstance(player, dict):
        return False

    # ----------------------------------------------------
    # flagهای مستقیم
    # ----------------------------------------------------

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

    # ----------------------------------------------------
    # nested player
    # ----------------------------------------------------

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
# تشخیص substitute
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
# استخراج starter ها
# --------------------------------------------------------

def get_starters(team):
    if not isinstance(team, dict):
        return []

    # ----------------------------------------------------
    # اگر FotMob مستقیماً starterها را داده باشد
    # ----------------------------------------------------

    for key in (
        "starters",
        "startingXI",
        "startingLineup",
    ):

        value = team.get(key)

        if isinstance(value, list) and value:
            return value

    # ----------------------------------------------------
    # اگر همه بازیکنان داخل players باشند
    # ----------------------------------------------------

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
# استخراج substitute ها
# --------------------------------------------------------

def get_substitutes(team):
    if not isinstance(team, dict):
        return []

    # ----------------------------------------------------
    # کلیدهای مستقیم
    # ----------------------------------------------------

    for key in (
        "substitutes",
        "subs",
        "bench",
    ):

        value = team.get(key)

        if isinstance(value, list):
            return value

    # ----------------------------------------------------
    # اگر همه بازیکنان داخل players باشند
    # ----------------------------------------------------

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
# پیدا کردن نام بازیکن
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
# پیدا کردن rating
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
# پیدا کردن پست بازیکن
# --------------------------------------------------------

def get_player_position(player):
    if not isinstance(player, dict):
        return ""

    candidates = []

    for key in (
        "position",
        "positionName",
        "role",
        "playerPosition",
    ):

        candidates.append(
            player.get(key)
        )

    position = player.get(
        "position"
    )

    if isinstance(position, dict):

        candidates.extend(
            [
                position.get("name"),
                position.get("shortName"),
                position.get("abbreviation"),
                position.get("code"),
            ]
        )

    role = player.get(
        "role"
    )

    if isinstance(role, dict):

        candidates.extend(
            [
                role.get("name"),
                role.get("shortName"),
                role.get("abbreviation"),
                role.get("code"),
            ]
        )

    nested_player = player.get(
        "player"
    )

    if isinstance(nested_player, dict):

        for key in (
            "position",
            "positionName",
            "role",
            "playerPosition",
        ):

            value = nested_player.get(
                key
            )

            candidates.append(
                value
            )

            if isinstance(
                value,
                dict,
            ):

                candidates.extend(
                    [
                        value.get("name"),
                        value.get("shortName"),
                        value.get("abbreviation"),
                        value.get("code"),
                    ]
                )

    for value in candidates:

        if isinstance(value, str):

            value = value.strip()

            if value:
                return value.lower()

    return ""


# --------------------------------------------------------
# تبدیل پست به چهار گروه
# --------------------------------------------------------

def position_group(player):
    position = get_player_position(
        player
    )

    position = position.lower().strip()

    # ----------------------------------------------------
    # دروازه‌بان
    # ----------------------------------------------------

    goalkeeper_terms = (
        "goalkeeper",
        "goal keeper",
        "keeper",
        "goalie",
        "gk",
    )

    if any(
        term in position
        for term in goalkeeper_terms
    ):
        return "goalkeeper"

    # ----------------------------------------------------
    # مدافع
    # ----------------------------------------------------

    defender_terms = (
        "defender",
        "defence",
        "defense",
        "centre-back",
        "center-back",
        "central defender",
        "left-back",
        "right-back",
        "wing-back",
        "full-back",
        "fullback",
        "cb",
        "lb",
        "rb",
        "lwb",
        "rwb",
    )

    if any(
        term in position
        for term in defender_terms
    ):
        return "defender"

    # ----------------------------------------------------
    # هافبک
    # ----------------------------------------------------

    midfielder_terms = (
        "midfielder",
        "midfield",
        "central midfield",
        "defensive midfield",
        "attacking midfield",
        "central midfielder",
        "cm",
        "cdm",
        "dm",
        "am",
        "lm",
        "rm",
    )

    if any(
        term in position
        for term in midfielder_terms
    ):
        return "midfielder"

    # ----------------------------------------------------
    # مهاجم
    # ----------------------------------------------------

    attacker_terms = (
        "forward",
        "attacker",
        "striker",
        "centre-forward",
        "center-forward",
        "central forward",
        "winger",
        "left wing",
        "right wing",
        "left winger",
        "right winger",
        "lw",
        "rw",
        "st",
        "cf",
    )

    if any(
        term in position
        for term in attacker_terms
    ):
        return "attacker"

    return "unknown"


# --------------------------------------------------------
# پیدا کردن مربی
# --------------------------------------------------------

def get_coach(team):
    if not isinstance(team, dict):
        return ""

    # مسیرهای مستقیم
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

    # fallback بازگشتی
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
# پیدا کردن سیستم
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

            if value:
                return value

        if isinstance(value, dict):

            name = first_non_empty(
                value.get("name"),
                value.get("formation"),
                value.get("value"),
            )

            if name:
                return clean_text(name)

    # fallback بازگشتی
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

            # سیستم فوتبال معمولاً حداقل یک خط تیره دارد
            # یا شکل عددی مثل 343 / 442 است.
            if (
                re.fullmatch(
                    r"\d{3,4}",
                    value,
                )
                or re.fullmatch(
                    r"\d-\d-\d(?:-\d)?",
                    value,
                )
            ):
                return value

        elif isinstance(value, dict):

            name = first_non_empty(
                value.get("name"),
                value.get("formation"),
                value.get("value"),
            )

            if name:
                return clean_text(name)

    return ""


# --------------------------------------------------------
# مرتب کردن بازیکنان
# --------------------------------------------------------

def organize_players(starters):
    groups = {
        "goalkeeper": [],
        "defender": [],
        "midfielder": [],
        "attacker": [],
        "unknown": [],
    }

    for player in starters:

        group = position_group(
            player
        )

        groups[group].append(
            player
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
        starters
    )

    lines = []

    # ----------------------------------------------------
    # نام تیم
    # ----------------------------------------------------

    lines.append(
        f"{team_icon} {team_name}"
    )

    # ----------------------------------------------------
    # مربی
    # ----------------------------------------------------

    if coach:
        lines.append(
            f"👔 {coach}"
        )

    # ----------------------------------------------------
    # سیستم
    # ----------------------------------------------------

    if formation:
        lines.append(
            f"📐 {formation}"
        )

    lines.append("")

    # ----------------------------------------------------
    # دروازه‌بان
    # ----------------------------------------------------

    line = format_player_line(
        "🧤",
        groups["goalkeeper"],
        show_rating,
    )

    if line:
        lines.append(line)

    # ----------------------------------------------------
    # مدافعان
    # ----------------------------------------------------

    line = format_player_line(
        "🛡",
        groups["defender"],
        show_rating,
    )

    if line:
        lines.append(line)

    # ----------------------------------------------------
    # هافبک‌ها
    # ----------------------------------------------------

    line = format_player_line(
        "⚙️",
        groups["midfielder"],
        show_rating,
    )

    if line:
        lines.append(line)

    # ----------------------------------------------------
    # مهاجمان
    # ----------------------------------------------------

    line = format_player_line(
        "⚡",
        groups["attacker"],
        show_rating,
    )

    if line:
        lines.append(line)

    # ----------------------------------------------------
    # بازیکنان ناشناخته
    # ----------------------------------------------------

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

    # ----------------------------------------------------
    # دقیقاً یک خط خالی قبل از تعویضی‌ها
    # ----------------------------------------------------

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

    # ----------------------------------------------------
    # زمان
    # ----------------------------------------------------

    start_time = get_match_start(
        root,
        content,
    )

    kickoff = format_match_time(
        start_time
    )

    # ----------------------------------------------------
    # وضعیت
    # ----------------------------------------------------

    finished = is_match_finished(
        content
    )

    print()
    print(
        "MATCH FINISHED:",
        finished,
    )

    show_rating = finished

    # ----------------------------------------------------
    # lineup
    # ----------------------------------------------------

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

    # ----------------------------------------------------
    # تیم‌ها
    # ----------------------------------------------------

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

    # ----------------------------------------------------
    # اطلاعات تشخیصی
    # ----------------------------------------------------

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
    # پیام
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

    # ----------------------------------------------------
    # میزبان
    # ----------------------------------------------------

    message.append(
        format_team_lineup(
            home_name,
            home_team,
            show_rating,
            "🔴",
        )
    )

    message.append("")

    # ----------------------------------------------------
    # مهمان
    # ----------------------------------------------------

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

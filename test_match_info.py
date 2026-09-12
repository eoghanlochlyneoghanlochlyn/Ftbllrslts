import json
import os
import re
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

import requests


# ============================================================
# تنظیمات
# ============================================================

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAMBOT")
TELEGRAM_CHANNEL = os.getenv("TELEGRAMCHANNEL")

MATCH_ID = "5811755"

FOTMOB_URL = f"https://www.fotmob.com/match/{MATCH_ID}"

IRAN_TIMEZONE = ZoneInfo("Asia/Tehran")


# ============================================================
# ابزارهای عمومی
# ============================================================

def clean_text(value):
    if value is None:
        return ""

    if isinstance(value, str):
        return re.sub(r"\s+", " ", value).strip()

    return str(value).strip()


def get_nested(data, *keys):
    current = data

    for key in keys:
        if not isinstance(current, dict):
            return None

        current = current.get(key)

    return current


# ============================================================
# تلگرام
# ============================================================

def send_telegram(message):
    if not TELEGRAM_BOT_TOKEN:
        print("TELEGRAMBOT پیدا نشد.")
        return False

    if not TELEGRAM_CHANNEL:
        print("TELEGRAMCHANNEL پیدا نشد.")
        return False

    url = (
        f"https://api.telegram.org/"
        f"bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    )

    payload = {
        "chat_id": TELEGRAM_CHANNEL,
        "text": message,
    }

    try:
        response = requests.post(
            url,
            json=payload,
            timeout=30,
        )

        print(
            f"Telegram status: "
            f"{response.status_code}"
        )

        if response.status_code != 200:
            print(response.text)

        return response.status_code == 200

    except Exception as e:
        print(f"Telegram error: {e}")
        return False


# ============================================================
# دریافت صفحه فوت‌موب
# ============================================================

def fetch_match_page():
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 "
            "(KHTML, like Gecko) "
            "Chrome/140.0 Safari/537.36"
        ),
        "Accept-Language": "en-US,en;q=0.9",
    }

    response = requests.get(
        FOTMOB_URL,
        headers=headers,
        timeout=30,
    )

    response.raise_for_status()

    print(
        f"HTML دریافت شد: "
        f"{len(response.text):,} bytes"
    )

    return response.text


# ============================================================
# استخراج NEXT_DATA
# ============================================================

def extract_next_data(html):
    match = re.search(
        r'<script id="__NEXT_DATA__"[^>]*>(.*?)</script>',
        html,
        re.DOTALL,
    )

    if not match:
        raise RuntimeError(
            "__NEXT_DATA__ پیدا نشد."
        )

    raw = match.group(1)

    data = json.loads(raw)

    print("NEXT_DATA با موفقیت استخراج شد.")

    return data


# ============================================================
# جستجوی بازگشتی
# ============================================================

def recursive_find(data, target_key):
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


def find_all_recursive(data, target_key):
    results = []

    if isinstance(data, dict):

        if target_key in data:
            results.append(data[target_key])

        for value in data.values():
            results.extend(
                find_all_recursive(
                    value,
                    target_key,
                )
            )

    elif isinstance(data, list):

        for item in data:
            results.extend(
                find_all_recursive(
                    item,
                    target_key,
                )
            )

    return results


# ============================================================
# اطلاعات اصلی مسابقه
# ============================================================

def extract_basic_info(root):
    seo = get_nested(
        root,
        "props",
        "pageProps",
        "seo",
    )

    event_json = None

    if isinstance(seo, dict):
        event_json = seo.get(
            "eventJSONLD"
        )

    if isinstance(event_json, str):
        try:
            event_json = json.loads(
                event_json
            )
        except Exception:
            event_json = None

    home = ""
    away = ""
    start_date = ""

    if isinstance(event_json, dict):

        home_team = event_json.get(
            "homeTeam"
        )

        away_team = event_json.get(
            "awayTeam"
        )

        if isinstance(home_team, dict):
            home = clean_text(
                home_team.get("name")
            )

        if isinstance(away_team, dict):
            away = clean_text(
                away_team.get("name")
            )

        start_date = clean_text(
            event_json.get("startDate")
        )

    return {
        "home": home,
        "away": away,
        "start_date": start_date,
    }


# ============================================================
# پیدا کردن content
# ============================================================

def get_content(root):
    content = get_nested(
        root,
        "props",
        "pageProps",
        "content",
    )

    if isinstance(content, dict):
        return content

    content = recursive_find(
        root,
        "content",
    )

    if isinstance(content, dict):
        return content

    return {}


# ============================================================
# زمان مسابقه
# ============================================================

def parse_datetime(value):
    if not value:
        return None

    value = clean_text(value)

    try:
        if value.endswith("Z"):
            value = value[:-1] + "+00:00"

        dt = datetime.fromisoformat(value)

        if dt.tzinfo is None:
            dt = dt.replace(
                tzinfo=timezone.utc
            )

        return dt

    except Exception:
        return None


def format_match_time(value):
    dt = parse_datetime(value)

    if not dt:
        return "نامشخص"

    iran_time = dt.astimezone(
        IRAN_TIMEZONE
    )

    return iran_time.strftime("%H:%M")


def get_match_start(root, basic_info):
    start_date = basic_info.get(
        "start_date"
    )

    if start_date:
        return start_date

    seo = get_nested(
        root,
        "props",
        "pageProps",
        "seo",
    )

    if isinstance(seo, dict):
        event_json = seo.get(
            "eventJSONLD"
        )

        if isinstance(event_json, str):
            try:
                event_json = json.loads(
                    event_json
                )
            except Exception:
                event_json = None

        if isinstance(event_json, dict):
            return event_json.get(
                "startDate",
                "",
            )

    return ""


# ============================================================
# تشخیص پایان بازی
# ============================================================

def is_match_finished(content):
    """
    فقط برای تعیین اینکه rating نمایش داده شود یا نه.

    rating فقط وقتی نمایش داده می‌شود که بازی
    واقعاً تمام شده باشد.
    """

    possible_statuses = []

    def collect_statuses(data):
        if isinstance(data, dict):

            for key in (
                "status",
                "matchStatus",
                "state",
                "shortStatus",
            ):
                value = data.get(key)

                if isinstance(value, str):
                    possible_statuses.append(
                        value.lower().strip()
                    )

            for value in data.values():
                collect_statuses(value)

        elif isinstance(data, list):

            for item in data:
                collect_statuses(item)

    collect_statuses(content)

    finished_words = {
        "finished",
        "complete",
        "completed",
        "ft",
        "full time",
    }

    for status in possible_statuses:
        if status in finished_words:
            return True

        if (
            "finished" in status
            or "full time" in status
        ):
            return True

    return False


# ============================================================
# پیدا کردن lineup
# ============================================================

def get_lineup(content, root):
    lineup = None

    if isinstance(content, dict):
        lineup = content.get("lineup")

    if isinstance(lineup, dict):
        return lineup

    lineup = recursive_find(
        content,
        "lineup",
    )

    if isinstance(lineup, dict):
        return lineup

    lineup = recursive_find(
        root,
        "lineup",
    )

    if isinstance(lineup, dict):
        return lineup

    return {}


# ============================================================
# پیدا کردن تیم‌های lineup
# ============================================================

def get_lineup_team(lineup, team_index):
    """
    ساختار فوت‌موب ممکن است در نسخه‌های مختلف
    کمی متفاوت باشد.

    ابتدا ساختارهای معمول را بررسی می‌کنیم.
    """

    teams = lineup.get("teams")

    if isinstance(teams, list):
        if len(teams) > team_index:
            return teams[team_index]

    if team_index == 0:
        for key in (
            "homeTeam",
            "home",
        ):
            value = lineup.get(key)

            if isinstance(value, dict):
                return value

    if team_index == 1:
        for key in (
            "awayTeam",
            "away",
        ):
            value = lineup.get(key)

            if isinstance(value, dict):
                return value

    return {}


# ============================================================
# پیدا کردن لیست بازیکنان
# ============================================================

def find_player_list(team_data):
    if not isinstance(team_data, dict):
        return []

    possible_keys = (
        "starters",
        "players",
        "lineup",
        "playerList",
    )

    for key in possible_keys:
        value = team_data.get(key)

        if isinstance(value, list):
            return value

    for value in team_data.values():

        if isinstance(value, dict):

            result = find_player_list(
                value
            )

            if result:
                return result

        elif isinstance(value, list):

            player_like = []

            for item in value:

                if isinstance(item, dict):
                    if (
                        "name" in item
                        or "player" in item
                        or "id" in item
                    ):
                        player_like.append(
                            item
                        )

            if player_like:
                return player_like

    return []


# ============================================================
# تشخیص Starter / Substitute
# ============================================================

def is_player_starter(player):
    if not isinstance(player, dict):
        return False

    for key in (
        "isStarter",
        "starter",
        "isStarting",
    ):
        value = player.get(key)

        if value is True:
            return True

    status = player.get("status")

    if isinstance(status, str):
        if status.lower() in {
            "starter",
            "starting",
            "starting11",
        }:
            return True

    return False


def is_player_substitute(player):
    if not isinstance(player, dict):
        return False

    for key in (
        "isSubstitute",
        "substitute",
        "isOnBench",
        "bench",
    ):
        value = player.get(key)

        if value is True:
            return True

    status = player.get("status")

    if isinstance(status, str):
        if status.lower() in {
            "substitute",
            "bench",
            "sub",
        }:
            return True

    return False


# ============================================================
# استخراج Starterها
# ============================================================

def get_starters(team_data):
    players = find_player_list(
        team_data
    )

    starters = [
        player
        for player in players
        if is_player_starter(player)
    ]

    return starters


# ============================================================
# استخراج Substituteها
# ============================================================

def get_substitutes(team_data):
    players = find_player_list(
        team_data
    )

    substitutes = [
        player
        for player in players
        if is_player_substitute(player)
        and not is_player_starter(player)
    ]

    return substitutes


# ============================================================
# نام بازیکن
# ============================================================

def get_player_name(player):
    if not isinstance(player, dict):
        return "Unknown"

    name = player.get("name")

    if isinstance(name, str):
        return clean_text(name)

    player_data = player.get(
        "player"
    )

    if isinstance(player_data, dict):
        name = player_data.get("name")

        if isinstance(name, str):
            return clean_text(name)

    return "Unknown"


# ============================================================
# Rating
# ============================================================

def get_player_rating(player):
    if not isinstance(player, dict):
        return None

    possible_keys = (
        "rating",
        "playerRating",
        "score",
    )

    for key in possible_keys:
        value = player.get(key)

        if value is not None:
            try:
                return float(value)
            except Exception:
                pass

    player_data = player.get(
        "player"
    )

    if isinstance(player_data, dict):

        for key in possible_keys:
            value = player_data.get(key)

            if value is not None:
                try:
                    return float(value)
                except Exception:
                    pass

    return None


# ============================================================
# استخراج positionId
# ============================================================

def find_position_id(data):
    """
    positionId را به صورت بازگشتی پیدا می‌کند.

    اینجا عمداً به فیلد متنی position وابسته نیستیم.
    منبع اصلی تشخیص پست = positionId
    """

    if isinstance(data, dict):

        # مهم‌ترین حالت
        for key in (
            "positionId",
            "positionID",
            "position_id",
        ):
            value = data.get(key)

            if value is not None:
                try:
                    return int(value)
                except Exception:
                    pass

        # بعضی ساختارها position را به شکل object دارند
        position = data.get("position")

        if isinstance(position, dict):

            for key in (
                "positionId",
                "positionID",
                "position_id",
                "id",
            ):
                value = position.get(key)

                if value is not None:
                    try:
                        return int(value)
                    except Exception:
                        pass

        # بررسی بازگشتی
        for value in data.values():

            result = find_position_id(
                value
            )

            if result is not None:
                return result

    elif isinstance(data, list):

        for item in data:

            result = find_position_id(
                item
            )

            if result is not None:
                return result

    return None


def get_player_position_id(player):
    return find_position_id(player)


# ============================================================
# تبدیل positionId به گروه کلی
# ============================================================

def position_group(position_id):
    """
    نگاشت استخراج‌شده و تست‌شده قبلی FotMob.

    هدف:
        GK
        DEF
        MID
        ATT

    چپ/راست عمداً از positionId استخراج نمی‌شود.
    """

    if position_id is None:
        return "UNKNOWN"

    try:
        position_id = int(position_id)
    except Exception:
        return "UNKNOWN"

    # --------------------------------------------------------
    # دروازه‌بان
    # --------------------------------------------------------

    if position_id == 11:
        return "GK"

    # --------------------------------------------------------
    # مدافع
    # --------------------------------------------------------

    if position_id in {
        32,
        33,
        34,
        35,
        36,
        37,
        38,
    }:
        return "DEF"

    # --------------------------------------------------------
    # هافبک / وینگ‌بک / بازیکن میانی
    # --------------------------------------------------------

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
        return "MID"

    # --------------------------------------------------------
    # وینگر / بازیکن هجومی
    # --------------------------------------------------------

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
        return "ATT"

    # --------------------------------------------------------
    # مهاجم
    # --------------------------------------------------------

    if position_id in {
        104,
        105,
        106,
        115,
    }:
        return "ATT"

    return "UNKNOWN"


# ============================================================
# مختصات بازیکن
# ============================================================

def get_layout_value(player, key):
    if not isinstance(player, dict):
        return None

    value = player.get(key)

    if value is not None:
        try:
            return float(value)
        except Exception:
            pass

    # بعضی ساختارها اطلاعات جایگاه را داخل
    # position / layout نگه می‌دارند.

    for container_key in (
        "position",
        "layout",
        "coordinates",
    ):
        container = player.get(
            container_key
        )

        if isinstance(container, dict):

            value = container.get(key)

            if value is not None:
                try:
                    return float(value)
                except Exception:
                    pass

    return None


def get_horizontal_layout(player):
    return get_layout_value(
        player,
        "horizontalLayout",
    )


def get_vertical_layout(player):
    return get_layout_value(
        player,
        "verticalLayout",
    )


# ============================================================
# مرتب‌سازی بازیکنان
# ============================================================

def organize_players(players):
    groups = {
        "GK": [],
        "DEF": [],
        "MID": [],
        "ATT": [],
        "UNKNOWN": [],
    }

    for player in players:

        position_id = get_player_position_id(
            player
        )

        group = position_group(
            position_id
        )

        groups[group].append(
            player
        )

    # --------------------------------------------------------
    # مرتب‌سازی هر خط
    #
    # horizontalLayout برای ترتیب چپ به راست
    # و verticalLayout برای ترتیب عمودی استفاده می‌شود.
    # --------------------------------------------------------

    for group_players in groups.values():

        group_players.sort(
            key=lambda player: (
                get_horizontal_layout(
                    player
                )
                if get_horizontal_layout(
                    player
                ) is not None
                else 9999,

                get_vertical_layout(
                    player
                )
                if get_vertical_layout(
                    player
                ) is not None
                else 9999,
            )
        )

    return groups


# ============================================================
# فرمت بازیکن
# ============================================================

def format_player(
    player,
    show_rating=False,
):
    name = get_player_name(
        player
    )

    if not show_rating:
        return name

    rating = get_player_rating(
        player
    )

    if rating is None:
        return name

    # مثل 8.4 / 7.1 / 6.0
    rating_text = (
        f"{rating:.1f}"
    )

    return (
        f"{name} "
        f"({rating_text})"
    )


# ============================================================
# فرمت هر خط
# ============================================================

def format_player_line(
    icon,
    players,
    show_rating=False,
):
    if not players:
        return ""

    names = [
        format_player(
            player,
            show_rating,
        )
        for player in players
    ]

    return (
        f"{icon} "
        f"{' | '.join(names)}"
    )


# ============================================================
# نام مربی
# ============================================================

def get_coach(team_data):
    if not isinstance(team_data, dict):
        return ""

    possible_keys = (
        "coach",
        "manager",
        "headCoach",
    )

    for key in possible_keys:

        value = team_data.get(key)

        if isinstance(value, dict):

            for name_key in (
                "name",
                "fullName",
                "displayName",
            ):
                name = value.get(
                    name_key
                )

                if isinstance(name, str):
                    return clean_text(
                        name
                    )

        elif isinstance(value, str):
            return clean_text(value)

    # جستجوی بازگشتی
    for value in team_data.values():

        if isinstance(value, dict):

            result = get_coach(
                value
            )

            if result:
                return result

    return ""


# ============================================================
# سیستم بازی
# ============================================================

def get_formation(team_data):
    if not isinstance(team_data, dict):
        return ""

    possible_keys = (
        "formation",
        "formationName",
    )

    for key in possible_keys:

        value = team_data.get(key)

        if isinstance(value, str):
            return clean_text(value)

        if isinstance(value, dict):

            for nested_key in (
                "name",
                "formation",
                "value",
            ):
                nested = value.get(
                    nested_key
                )

                if isinstance(
                    nested,
                    str,
                ):
                    return clean_text(
                        nested
                    )

    return ""


# ============================================================
# نام رقابت
# ============================================================

def get_competition_name(
    content,
    root,
):
    possible_keys = (
        "league",
        "competition",
        "tournament",
    )

    for key in possible_keys:

        value = content.get(key)

        if isinstance(value, dict):

            for name_key in (
                "name",
                "title",
            ):
                name = value.get(
                    name_key
                )

                if isinstance(name, str):
                    return clean_text(
                        name
                    )

        elif isinstance(value, str):
            return clean_text(value)

    # جستجوی بازگشتی
    for key in (
        "league",
        "competition",
        "tournament",
    ):

        values = find_all_recursive(
            content,
            key,
        )

        for value in values:

            if isinstance(value, dict):

                for name_key in (
                    "name",
                    "title",
                ):
                    name = value.get(
                        name_key
                    )

                    if isinstance(name, str):
                        return clean_text(
                            name
                        )

            elif isinstance(value, str):
                return clean_text(value)

    return "Football"


# ============================================================
# نام تیم برای هدر
# ============================================================

def get_team_name(team_data):
    if not isinstance(team_data, dict):
        return ""

    for key in (
        "name",
        "teamName",
    ):
        value = team_data.get(key)

        if isinstance(value, str):
            return clean_text(value)

    team = team_data.get(
        "team"
    )

    if isinstance(team, dict):

        for key in (
            "name",
            "teamName",
        ):
            value = team.get(key)

            if isinstance(value, str):
                return clean_text(value)

    return ""


# ============================================================
# فرمت ترکیب یک تیم
# ============================================================

def format_team_lineup(
    team_data,
    team_name,
    show_rating=False,
):
    starters = get_starters(
        team_data
    )

    substitutes = get_substitutes(
        team_data
    )

    groups = organize_players(
        starters
    )

    coach = get_coach(
        team_data
    )

    formation = get_formation(
        team_data
    )

    lines = []

    lines.append(
        team_name
    )

    if coach:
        lines.append(
            f"👔 {coach}"
        )

    if formation:
        lines.append(
            f"📐 {formation}"
        )

    # --------------------------------------------------------
    # دروازه‌بان
    # --------------------------------------------------------

    line = format_player_line(
        "🧤",
        groups["GK"],
        show_rating,
    )

    if line:
        lines.append(line)

    # --------------------------------------------------------
    # مدافعان
    # --------------------------------------------------------

    line = format_player_line(
        "🛡",
        groups["DEF"],
        show_rating,
    )

    if line:
        lines.append(line)

    # --------------------------------------------------------
    # هافبک‌ها
    # --------------------------------------------------------

    line = format_player_line(
        "⚙️",
        groups["MID"],
        show_rating,
    )

    if line:
        lines.append(line)

    # --------------------------------------------------------
    # مهاجمان / وینگرهای هجومی
    # --------------------------------------------------------

    line = format_player_line(
        "⚡",
        groups["ATT"],
        show_rating,
    )

    if line:
        lines.append(line)

    # --------------------------------------------------------
    # اگر بازیکنی positionId ناشناخته داشت
    # فعلاً آن را به صورت خط جداگانه نشان می‌دهیم
    # تا داده گم نشود.
    # --------------------------------------------------------

    line = format_player_line(
        "⚽️",
        groups["UNKNOWN"],
        show_rating,
    )

    if line:
        lines.append(line)

    # --------------------------------------------------------
    # یک خط خالی قبل از ذخیره‌ها
    # --------------------------------------------------------

    if substitutes:
        lines.append("")

        substitute_names = [
            format_player(
                player,
                show_rating,
            )
            for player in substitutes
        ]

        lines.append(
            "🔄 "
            + " | ".join(
                substitute_names
            )
        )

    return "\n".join(lines)


# ============================================================
# ساخت پیام نهایی
# ============================================================

def build_message(
    root,
    content,
    basic_info,
    home_team_data,
    away_team_data,
):
    home = basic_info.get(
        "home"
    )

    away = basic_info.get(
        "away"
    )

    if not home:
        home = get_team_name(
            home_team_data
        )

    if not away:
        away = get_team_name(
            away_team_data
        )

    competition = (
        get_competition_name(
            content,
            root,
        )
    )

    start_date = get_match_start(
        root,
        basic_info,
    )

    match_time = format_match_time(
        start_date
    )

    finished = is_match_finished(
        content
    )

    home_lineup = format_team_lineup(
        home_team_data,
        f"🔴 {home}",
        show_rating=finished,
    )

    away_lineup = format_team_lineup(
        away_team_data,
        f"🔵 {away}",
        show_rating=finished,
    )

    message = (
        f"🏆 {competition}\n\n"
        f"⚽️ {home} 🆚 {away}\n"
        f"🕐 {match_time} به وقت ایران\n\n"
        f"{home_lineup}\n\n"
        f"{away_lineup}"
    )

    return message


# ============================================================
# MAIN
# ============================================================

def main():
    print(
        f"شروع تست بازی {MATCH_ID}"
    )

    html = fetch_match_page()

    root = extract_next_data(
        html
    )

    basic_info = extract_basic_info(
        root
    )

    print(
        f"Home: "
        f"{basic_info.get('home')}"
    )

    print(
        f"Away: "
        f"{basic_info.get('away')}"
    )

    content = get_content(
        root
    )

    lineup = get_lineup(
        content,
        root,
    )

    if not lineup:
        raise RuntimeError(
            "lineup پیدا نشد."
        )

    home_team_data = get_lineup_team(
        lineup,
        0,
    )

    away_team_data = get_lineup_team(
        lineup,
        1,
    )

    home_starters = get_starters(
        home_team_data
    )

    away_starters = get_starters(
        away_team_data
    )

    print(
        f"Home starters: "
        f"{len(home_starters)}"
    )

    print(
        f"Away starters: "
        f"{len(away_starters)}"
    )

    # --------------------------------------------------------
    # Debug positionId
    # --------------------------------------------------------

    print("\n--- POSITION IDS ---")

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

        group = position_group(
            position_id
        )

        horizontal = (
            get_horizontal_layout(
                player
            )
        )

        vertical = (
            get_vertical_layout(
                player
            )
        )

        print(
            f"{name}: "
            f"positionId={position_id}, "
            f"group={group}, "
            f"H={horizontal}, "
            f"V={vertical}"
        )

    # --------------------------------------------------------
    # ساخت پیام
    # --------------------------------------------------------

    message = build_message(
        root,
        content,
        basic_info,
        home_team_data,
        away_team_data,
    )

    print("\n")
    print("=" * 70)
    print(message)
    print("=" * 70)
    print("\n")

    # --------------------------------------------------------
    # ارسال
    # --------------------------------------------------------

    success = send_telegram(
        message
    )

    if success:
        print(
            "پیام با موفقیت به تلگرام ارسال شد."
        )
    else:
        print(
            "ارسال پیام ناموفق بود."
        )


if __name__ == "__main__":
    main()

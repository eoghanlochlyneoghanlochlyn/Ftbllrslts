import json
import re
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

import requests


# ============================================================
# تنظیمات
# ============================================================

MATCH_ID = "5811755"

FOTMOB_URL = f"https://www.fotmob.com/match/{MATCH_ID}"

IRAN_TIMEZONE = ZoneInfo("Asia/Tehran")

BOT_TOKEN = None
CHANNEL_ID = None


# ============================================================
# دریافت اطلاعات از FotMob
# ============================================================

def fetch_match_data():
    print("Fetching FotMob page...")

    response = requests.get(
        FOTMOB_URL,
        headers={
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/140.0 Safari/537.36"
            )
        },
        timeout=30,
    )

    response.raise_for_status()

    print(f"HTTP status: {response.status_code}")
    print(f"HTML size: {len(response.text):,} bytes")

    match = re.search(
        r'<script[^>]+id="__NEXT_DATA__"[^>]*>(.*?)</script>',
        response.text,
        re.DOTALL,
    )

    if not match:
        raise RuntimeError("__NEXT_DATA__ not found")

    root = json.loads(match.group(1))

    print("NEXT_DATA extracted successfully.")

    return root


# ============================================================
# پیدا کردن داده اصلی مسابقه
# ============================================================

def get_content(root):
    try:
        return root["props"]["pageProps"]["content"]
    except (KeyError, TypeError):
        raise RuntimeError("FotMob content structure not found")


# ============================================================
# ابزارهای عمومی
# ============================================================

def get_value(obj, *keys, default=None):
    if not isinstance(obj, dict):
        return default

    for key in keys:
        if key in obj and obj[key] is not None:
            return obj[key]

    return default


def player_name(player):
    if not isinstance(player, dict):
        return "Unknown"

    name = get_value(
        player,
        "name",
        "longName",
        "shortName",
        default="Unknown",
    )

    if isinstance(name, dict):
        name = (
            name.get("fullName")
            or name.get("displayName")
            or name.get("firstName")
            or "Unknown"
        )

    return str(name)


def player_rating(player):
    if not isinstance(player, dict):
        return None

    rating = get_value(
        player,
        "rating",
        "playerRating",
        "matchRating",
    )

    if rating is None:
        return None

    try:
        return float(rating)
    except (TypeError, ValueError):
        return None


# ============================================================
# وضعیت مسابقه
# ============================================================

def get_match_status(content):
    status = content.get("status", {})

    if isinstance(status, str):
        return status

    if not isinstance(status, dict):
        return ""

    return str(
        status.get("reason")
        or status.get("name")
        or status.get("short")
        or status.get("long")
        or ""
    )


def is_finished(content):
    status = content.get("status", {})

    if isinstance(status, dict):
        finished = status.get("finished")

        if finished is True:
            return True

        started = status.get("started")

        # FotMob در بعضی پاسخ‌ها reason/name را می‌دهد
        text = " ".join(
            str(status.get(key, ""))
            for key in (
                "reason",
                "name",
                "short",
                "long",
            )
        ).lower()

        if "full time" in text or text.strip() in {
            "ft",
            "finished",
            "complete",
            "completed",
        }:
            return True

        if started is False:
            return False

    return False


# ============================================================
# نام رقابت
# ============================================================

def get_league_name(content):
    competition = content.get("competition")

    if isinstance(competition, dict):
        name = (
            competition.get("name")
            or competition.get("leagueName")
            or competition.get("displayName")
        )

        if name:
            return str(name)

    league = content.get("league")

    if isinstance(league, dict):
        name = (
            league.get("name")
            or league.get("longName")
            or league.get("shortName")
        )

        if name:
            return str(name)

    # بعضی نسخه‌های FotMob اطلاعات لیگ را اینجا دارند
    for key in ("leagueName", "competitionName"):
        value = content.get(key)

        if value:
            return str(value)

    return "نامشخص"


# ============================================================
# تیم‌ها
# ============================================================

def get_team_info(content):
    home = content.get("homeTeam", {})
    away = content.get("awayTeam", {})

    home_name = (
        home.get("longName")
        or home.get("name")
        or home.get("shortName")
        or "Home"
    )

    away_name = (
        away.get("longName")
        or away.get("name")
        or away.get("shortName")
        or "Away"
    )

    return home, away, home_name, away_name


# ============================================================
# ساعت بازی
# ============================================================

def get_kickoff_time(content):
    status = content.get("status", {})

    utc_time = None

    if isinstance(status, dict):
        utc_time = (
            status.get("utcTime")
            or status.get("startTime")
        )

    if not utc_time:
        utc_time = (
            content.get("utcTime")
            or content.get("startTime")
        )

    if not utc_time:
        return "نامشخص"

    try:
        value = str(utc_time)

        if value.endswith("Z"):
            value = value[:-1] + "+00:00"

        dt = datetime.fromisoformat(value)

        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)

        iran_time = dt.astimezone(IRAN_TIMEZONE)

        return iran_time.strftime("%H:%M")

    except Exception:
        return "نامشخص"


# ============================================================
# پیدا کردن lineup
# ============================================================

def get_lineup(content):
    lineup = content.get("lineup")

    if not isinstance(lineup, dict):
        raise RuntimeError("LINEUP OBJECT NOT FOUND")

    return lineup


# ============================================================
# استخراج بازیکنان هر تیم
# ============================================================

def get_team_lineup(lineup, side):
    team_data = lineup.get(side)

    if not isinstance(team_data, dict):
        return {
            "starters": [],
            "substitutes": [],
            "formation": None,
            "coach": None,
        }

    starters = team_data.get("starters") or []
    substitutes = team_data.get("substitutes") or []

    formation = (
        team_data.get("formation")
        or team_data.get("formationName")
    )

    coach = team_data.get("coach")

    if isinstance(coach, dict):
        coach = (
            coach.get("name")
            or coach.get("longName")
            or coach.get("shortName")
        )

    return {
        "starters": starters,
        "substitutes": substitutes,
        "formation": formation,
        "coach": coach,
    }


# ============================================================
# تشخیص پست بازیکن
# ============================================================

def get_position(player):
    if not isinstance(player, dict):
        return ""

    position = (
        player.get("position")
        or player.get("positionName")
        or player.get("role")
        or ""
    )

    if isinstance(position, dict):
        position = (
            position.get("name")
            or position.get("shortName")
            or position.get("abbreviation")
            or ""
        )

    return str(position).lower().strip()


def get_position_group(player):
    """
    بازیکن را به یکی از این چهار گروه می‌فرستد:
    goalkeeper
    defender
    midfielder
    attacker
    """

    position = get_position(player)

    # -------------------------
    # دروازه‌بان
    # -------------------------

    if (
        "goalkeeper" in position
        or position in {"gk", "keeper", "goalie"}
    ):
        return "goalkeeper"

    # -------------------------
    # مدافع
    # -------------------------

    if any(
        word in position
        for word in (
            "defender",
            "defence",
            "defense",
            "centre-back",
            "center-back",
            "left-back",
            "right-back",
            "wing-back",
            "full-back",
            "cb",
            "lb",
            "rb",
            "lwb",
            "rwb",
        )
    ):
        return "defender"

    # -------------------------
    # هافبک
    # -------------------------

    if any(
        word in position
        for word in (
            "midfielder",
            "midfield",
            "central midfield",
            "defensive midfield",
            "attacking midfield",
            "cm",
            "dm",
            "am",
            "lm",
            "rm",
        )
    ):
        return "midfielder"

    # -------------------------
    # مهاجم
    # -------------------------

    if any(
        word in position
        for word in (
            "forward",
            "attacker",
            "striker",
            "centre-forward",
            "center-forward",
            "winger",
            "left wing",
            "right wing",
            "lw",
            "rw",
            "st",
            "cf",
        )
    ):
        return "attacker"

    return "unknown"


# ============================================================
# fallback برای تشخیص پست از شماره/اطلاعات دیگر
# ============================================================

def find_position_from_nested_data(player):
    """
    FotMob ممکن است اطلاعات پست را در ساختارهای متفاوت
    قرار دهد. این تابع چند مسیر رایج را بررسی می‌کند.
    """

    if not isinstance(player, dict):
        return ""

    candidates = []

    for key in (
        "position",
        "positionName",
        "role",
        "playerPosition",
    ):
        candidates.append(player.get(key))

    role = player.get("role")

    if isinstance(role, dict):
        candidates.extend(
            [
                role.get("name"),
                role.get("shortName"),
                role.get("abbreviation"),
            ]
        )

    position = player.get("position")

    if isinstance(position, dict):
        candidates.extend(
            [
                position.get("name"),
                position.get("shortName"),
                position.get("abbreviation"),
            ]
        )

    for value in candidates:
        if value:
            return str(value)

    return ""


# ============================================================
# مرتب‌سازی ترکیب
# ============================================================

def organize_starters(starters):
    groups = {
        "goalkeeper": [],
        "defender": [],
        "midfielder": [],
        "attacker": [],
        "unknown": [],
    }

    for player in starters:
        position = find_position_from_nested_data(player)

        if position:
            # موقتاً position را داخل کپی نگه می‌داریم
            player = dict(player)
            player["position"] = position

        group = get_position_group(player)

        groups[group].append(player)

    # اگر FotMob پست بعضی بازیکنان را نداده بود،
    # فعلاً آنها را حذف نمی‌کنیم.
    # در خروجی پایین‌تر به انتهای مناسب منتقل می‌شوند.

    if groups["unknown"]:
        print("WARNING: Some players have unknown positions:")

        for player in groups["unknown"]:
            print(
                " -",
                player_name(player),
                "| position:",
                get_position(player),
            )

    return groups


# ============================================================
# فرمت نمره
# ============================================================

def format_player(player, show_rating):
    name = player_name(player)

    if not show_rating:
        return name

    rating = player_rating(player)

    if rating is None:
        return name

    # مثلاً 8.0 → 8.0
    # 8.42 → 8.4
    return f"{name} {rating:.1f}"


# ============================================================
# فرمت هر خط
# ============================================================

def format_player_line(icon, players, show_rating):
    if not players:
        return None

    names = [
        format_player(player, show_rating)
        for player in players
    ]

    return f"{icon} " + " | ".join(names)


# ============================================================
# فرمت ترکیب یک تیم
# ============================================================

def format_team_lineup(team_name, team_lineup, show_rating):
    starters = team_lineup["starters"]
    substitutes = team_lineup["substitutes"]

    groups = organize_starters(starters)

    lines = []

    # نام تیم
    lines.append(team_name)
    lines.append("")

    # دروازه‌بان
    line = format_player_line(
        "🧤",
        groups["goalkeeper"],
        show_rating,
    )

    if line:
        lines.append(line)

    # مدافعان
    line = format_player_line(
        "🛡",
        groups["defender"],
        show_rating,
    )

    if line:
        lines.append(line)

    # هافبک‌ها
    line = format_player_line(
        "⚙️",
        groups["midfielder"],
        show_rating,
    )

    if line:
        lines.append(line)

    # مهاجمان
    line = format_player_line(
        "⚡",
        groups["attacker"],
        show_rating,
    )

    if line:
        lines.append(line)

    # فاصله بین مهاجمان و تعویضی‌ها
    lines.append("")

    # تعویضی‌ها
    if substitutes:
        substitute_names = [
            format_player(player, show_rating)
            for player in substitutes
        ]

        lines.append(
            "🔄 " + " | ".join(substitute_names)
        )

    return "\n".join(lines)


# ============================================================
# ساخت پیام کامل
# ============================================================

def build_message(content):
    home, away, home_name, away_name = get_team_info(content)

    league_name = get_league_name(content)
    kickoff = get_kickoff_time(content)

    finished = is_finished(content)

    lineup = get_lineup(content)

    home_lineup = get_team_lineup(lineup, "home")
    away_lineup = get_team_lineup(lineup, "away")

    # نمره فقط بعد از پایان بازی
    show_rating = finished

    message = []

    message.append(f"🏆 {league_name}")
    message.append("")
    message.append(f"⚽ {home_name} 🆚 {away_name}")
    message.append(f"🕐 {kickoff} به وقت ایران")
    message.append("")

    message.append(
        format_team_lineup(
            f"🔴 {home_name}",
            home_lineup,
            show_rating,
        )
    )

    message.append("")
    message.append(
        format_team_lineup(
            f"🔵 {away_name}",
            away_lineup,
            show_rating,
        )
    )

    return "\n".join(message)


# ============================================================
# ارسال به تلگرام
# ============================================================

def send_to_telegram(message):
    if not BOT_TOKEN or not CHANNEL_ID:
        print()
        print("BOT_TOKEN / CHANNEL_ID are not configured.")
        print("Telegram sending skipped.")
        return

    url = (
        f"https://api.telegram.org/bot"
        f"{BOT_TOKEN}/sendMessage"
    )

    response = requests.post(
        url,
        data={
            "chat_id": CHANNEL_ID,
            "text": message,
        },
        timeout=30,
    )

    print()
    print("Telegram status:", response.status_code)

    if response.status_code != 200:
        print(response.text)
        response.raise_for_status()

    print("Telegram message sent successfully.")


# ============================================================
# اجرای تست
# ============================================================

def main():
    print("=" * 60)
    print("FotMob Match Telegram Test")
    print("=" * 60)
    print(f"Match ID: {MATCH_ID}")
    print(f"URL: {FOTMOB_URL}")
    print()

    root = fetch_match_data()

    content = get_content(root)

    home, away, home_name, away_name = get_team_info(content)

    print()
    print("MATCH")
    print("-" * 60)
    print("Home:", home_name)
    print("Away:", away_name)
    print("League:", get_league_name(content))
    print("Kickoff:", get_kickoff_time(content))
    print("Status:", get_match_status(content))
    print("Finished:", is_finished(content))

    lineup = get_lineup(content)

    print()
    print("LINEUP")
    print("-" * 60)

    home_lineup = get_team_lineup(lineup, "home")
    away_lineup = get_team_lineup(lineup, "away")

    print(
        home_name,
        "| starters:",
        len(home_lineup["starters"]),
        "| substitutes:",
        len(home_lineup["substitutes"]),
    )

    print(
        away_name,
        "| starters:",
        len(away_lineup["starters"]),
        "| substitutes:",
        len(away_lineup["substitutes"]),
    )

    # ========================================================
    # ساخت پیام
    # ========================================================

    message = build_message(content)

    print()
    print("=" * 60)
    print("FINAL TELEGRAM MESSAGE")
    print("=" * 60)
    print()
    print(message)
    print()
    print("=" * 60)

    # ========================================================
    # ارسال تلگرام
    # ========================================================

    send_to_telegram(message)


if __name__ == "__main__":
    main()

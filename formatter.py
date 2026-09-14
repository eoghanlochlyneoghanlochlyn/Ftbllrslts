import html
from datetime import datetime

from zoneinfo import ZoneInfo

from event_detector import (
    get_event_assist_player_name,
    get_event_player_name,
    get_event_team,
    get_goal_minute,
    is_own_goal,
    is_penalty_goal,
)


IRAN_TIMEZONE = ZoneInfo("Asia/Tehran")


# --------------------------------------------------------
# ابزارهای عمومی
# --------------------------------------------------------

def safe_text(value, default=""):
    if value is None:
        return default

    text = str(value).strip()

    if not text:
        return default

    return text


def escape_html(value):
    return html.escape(
        safe_text(value),
        quote=False,
    )


def format_minute(minute):
    if minute is None:
        return ""

    try:
        minute = int(minute)
    except (TypeError, ValueError):
        return safe_text(minute)

    return f"{minute}'"


def format_score(score, home_name="", away_name=""):
    home_name = safe_text(home_name, "تیم میزبان")
    away_name = safe_text(away_name, "تیم مهمان")

    if not isinstance(score, dict):
        return f"{home_name} 🆚 {away_name}"

    home_score = score.get("home", 0)
    away_score = score.get("away", 0)

    try:
        home_score = int(home_score)
    except (TypeError, ValueError):
        home_score = 0

    try:
        away_score = int(away_score)
    except (TypeError, ValueError):
        away_score = 0

    return (
        f"{home_name} {home_score} 🆚 "
        f"{away_score} {away_name}"
    )


# --------------------------------------------------------
# استخراج نام تیم‌ها
# --------------------------------------------------------

def get_team_names(snapshot):
    if not isinstance(snapshot, dict):
        return "", ""

    home_name = ""
    away_name = ""

    home_team = snapshot.get("home_team")

    if isinstance(home_team, dict):
        home_name = (
            home_team.get("name")
            or home_team.get("shortName")
            or home_team.get("short_name")
            or ""
        )

    away_team = snapshot.get("away_team")

    if isinstance(away_team, dict):
        away_name = (
            away_team.get("name")
            or away_team.get("shortName")
            or away_team.get("short_name")
            or ""
        )

    if not home_name:
        home_name = (
            snapshot.get("home_name")
            or snapshot.get("homeName")
            or ""
        )

    if not away_name:
        away_name = (
            snapshot.get("away_name")
            or snapshot.get("awayName")
            or ""
        )

    return (
        safe_text(home_name),
        safe_text(away_name),
    )


# --------------------------------------------------------
# استخراج نام بازیکن
# --------------------------------------------------------

def get_player_name(event):
    name = get_event_player_name(event)

    if name:
        return safe_text(name)

    player = event.get("player") if isinstance(event, dict) else None

    if isinstance(player, dict):
        return safe_text(
            player.get("name")
            or player.get("fullName")
            or player.get("full_name")
        )

    return ""


def get_assist_name(event):
    name = get_event_assist_player_name(event)

    if name:
        return safe_text(name)

    if not isinstance(event, dict):
        return ""

    assist = (
        event.get("assist")
        or event.get("assistPlayer")
        or event.get("assist_player")
    )

    if isinstance(assist, dict):
        return safe_text(
            assist.get("name")
            or assist.get("fullName")
            or assist.get("full_name")
        )

    return ""


# --------------------------------------------------------
# مشخص کردن تیم گلزن
# --------------------------------------------------------

def get_goal_team_name(snapshot, event):
    home_name, away_name = get_team_names(snapshot)

    is_home = get_event_team(event)

    if is_home is True:
        return home_name

    if is_home is False:
        return away_name

    return ""


# --------------------------------------------------------
# پیام گل
# --------------------------------------------------------

def build_goal_message(snapshot, event, score=None):
    home_name, away_name = get_team_names(snapshot)

    player_name = get_player_name(event)
    assist_name = get_assist_name(event)

    minute = get_goal_minute(event)

    is_home = get_event_team(event)
    own_goal = is_own_goal(event)
    penalty = is_penalty_goal(event)

    # ----------------------------------------------------
    # گل به خودی
    # ----------------------------------------------------

    if own_goal:
        if is_home is True:
            team_name = away_name
        elif is_home is False:
            team_name = home_name
        else:
            team_name = ""

        lines = [
            "⚽️ <b>گل به خودی</b>",
        ]

        if team_name:
            lines.append(
                f"به سود <b>{escape_html(team_name)}</b>!"
            )

        if minute is not None:
            lines.append(
                f"⏱️ دقیقه {escape_html(format_minute(minute))}"
            )

        if player_name:
            lines.append(
                escape_html(player_name)
            )

        lines.append("")

        # score از main.py به‌صورت نتیجه «بعد از گل» ارسال می‌شود.
        # بنابراین برای گل به خودی نباید دوباره +1 شود.
        score_text = format_score(
            score,
            home_name,
            away_name,
        )

        lines.append(
            escape_html(score_text)
        )

        return "\n".join(lines)

    # ----------------------------------------------------
    # گل عادی / پنالتی
    # ----------------------------------------------------

    if penalty:
        title = "⚽️ <b>گل از روی نقطه پنالتی</b>"
    else:
        title = "⚽️ <b>گل</b>"

    lines = [
        title,
    ]

    if minute is not None:
        lines.append(
            f"⏱️ دقیقه {escape_html(format_minute(minute))}"
        )

    if player_name:
        lines.append(
            escape_html(player_name)
        )

    if assist_name:
        lines.append(
            f"پاس گل: {escape_html(assist_name)}"
        )

    lines.append("")

    score_text = format_score(
        score,
        home_name,
        away_name,
    )

    lines.append(
        escape_html(score_text)
    )

    return "\n".join(lines)


# --------------------------------------------------------
# پیام ترکیب رسمی
# --------------------------------------------------------

def get_player_display_name(player):
    if not isinstance(player, dict):
        return ""

    return safe_text(
        player.get("name")
        or player.get("fullName")
        or player.get("full_name")
        or player.get("shortName")
    )


def get_player_number(player):
    if not isinstance(player, dict):
        return ""

    number = (
        player.get("shirtNumber")
        or player.get("shirt_number")
        or player.get("number")
    )

    if number is None:
        return ""

    return safe_text(number)


def get_team_players(team):
    if not isinstance(team, dict):
        return []

    players = (
        team.get("starters")
        or team.get("players")
        or team.get("lineup")
        or []
    )

    if not isinstance(players, list):
        return []

    return players


def format_lineup_team(team, team_name):
    players = get_team_players(team)

    lines = [
        f"<b>{escape_html(team_name)}</b>"
    ]

    for player in players:
        name = get_player_display_name(player)

        if not name:
            continue

        number = get_player_number(player)

        if number:
            lines.append(
                f"{escape_html(number)}. "
                f"{escape_html(name)}"
            )
        else:
            lines.append(
                escape_html(name)
            )

    return lines


def build_lineup_message(snapshot):
    home_name, away_name = get_team_names(snapshot)

    home_team = snapshot.get("home_team", {})
    away_team = snapshot.get("away_team", {})

    lines = [
        "📋 <b>ترکیب رسمی</b>",
        "",
    ]

    lines.extend(
        format_lineup_team(
            home_team,
            home_name,
        )
    )

    lines.extend(
        [
            "",
            "🆚",
            "",
        ]
    )

    lines.extend(
        format_lineup_team(
            away_team,
            away_name,
        )
    )

    return "\n".join(lines)


# --------------------------------------------------------
# پیام شروع بازی
# --------------------------------------------------------

def build_start_message(snapshot):
    home_name, away_name = get_team_names(snapshot)

    return (
        "🟢 <b>بازی شروع شد</b>\n\n"
        f"{escape_html(home_name)} 🆚 "
        f"{escape_html(away_name)}"
    )


# --------------------------------------------------------
# زمان بازی
# --------------------------------------------------------

def format_kickoff_time(start_timestamp):
    if start_timestamp is None:
        return ""

    try:
        timestamp = float(start_timestamp)

        # اگر timestamp برحسب میلی‌ثانیه باشد
        if timestamp > 10_000_000_000:
            timestamp /= 1000

        dt = datetime.fromtimestamp(
            timestamp,
            tz=IRAN_TIMEZONE,
        )

        return dt.strftime("%H:%M")

    except (TypeError, ValueError, OSError, OverflowError):
        return ""


# --------------------------------------------------------
# پیام اطلاعات بازی
# --------------------------------------------------------

def build_match_info_message(snapshot):
    home_name, away_name = get_team_names(snapshot)

    competition = safe_text(
        snapshot.get("competition")
        or snapshot.get("league")
        or snapshot.get("tournament")
    )

    venue = safe_text(
        snapshot.get("venue")
        or snapshot.get("stadium")
    )

    start_timestamp = (
        snapshot.get("start_timestamp")
        or snapshot.get("startTimestamp")
        or snapshot.get("kickoff")
    )

    kickoff = format_kickoff_time(
        start_timestamp
    )

    lines = [
        "🏟️ <b>اطلاعات بازی</b>",
        "",
        f"<b>{escape_html(home_name)}</b>",
        "🆚",
        f"<b>{escape_html(away_name)}</b>",
    ]

    if competition:
        lines.extend(
            [
                "",
                f"🏆 {escape_html(competition)}",
            ]
        )

    if kickoff:
        lines.append(
            f"🕐 ساعت شروع: {escape_html(kickoff)}"
        )

    if venue:
        lines.append(
            f"🏟️ ورزشگاه: {escape_html(venue)}"
        )

    return "\n".join(lines)


# --------------------------------------------------------
# پیام پایان بازی
# --------------------------------------------------------

def build_final_message(
    snapshot,
    score=None,
    scorers=None,
):
    home_name, away_name = get_team_names(snapshot)

    lines = [
        "🔴 <b>پایان بازی</b>",
        "",
        f"<b>{escape_html(format_score(score, home_name, away_name))}</b>",
    ]

    if scorers:
        lines.extend(
            [
                "",
                "⚽️ <b>گلزنان:</b>",
            ]
        )

        for scorer in scorers:
            if not isinstance(scorer, dict):
                continue

            name = safe_text(
                scorer.get("name")
                or scorer.get("player_name")
            )

            count = scorer.get("count", 1)

            if not name:
                continue

            try:
                count = int(count)
            except (TypeError, ValueError):
                count = 1

            if count > 1:
                lines.append(
                    f"• {escape_html(name)} ×{count}"
                )
            else:
                lines.append(
                    f"• {escape_html(name)}"
                )

    return "\n".join(lines)

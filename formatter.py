import re
from datetime import datetime, timezone, timedelta

from fotmob import (
    get_coach,
    get_formation,
    get_player_id,
    get_player_name,
    get_player_rating,
    get_starters,
    get_substitutes,
    organize_players,
)

from event_detector import (
    get_goal_minute,
    get_event_assist_player_id,
    get_event_player_id,
    get_event_team,
    get_event_type,
    is_own_goal,
    is_penalty_goal,
)

from team_translations import (
    get_persian_team_name,
)


# --------------------------------------------------------
# نام نمایشی تیم
# --------------------------------------------------------

def get_display_team_name(
    snapshot,
    side,
):
    if not isinstance(
        snapshot,
        dict,
    ):
        return "Home" if side == "home" else "Away"

    if side == "home":
        translated_name = (
            snapshot.get("home_fa")
            or ""
        )

        raw_name = (
            snapshot.get("home")
            or "Home"
        )

    else:
        translated_name = (
            snapshot.get("away_fa")
            or ""
        )

        raw_name = (
            snapshot.get("away")
            or "Away"
        )

    if translated_name:
        return translated_name

    return raw_name


# --------------------------------------------------------
# تبدیل میلادی به شمسی
# --------------------------------------------------------

def gregorian_to_jalali(
    gy,
    gm,
    gd,
):
    g_days_in_month = [
        31,
        28,
        31,
        30,
        31,
        30,
        31,
        31,
        30,
        31,
        30,
        31,
    ]

    j_days_in_month = [
        31,
        31,
        31,
        31,
        31,
        31,
        30,
        30,
        30,
        30,
        30,
        29,
    ]

    gy2 = gy - 1600
    gm2 = gm - 1
    gd2 = gd - 1

    g_day_no = (
        365 * gy2
        + (gy2 + 3) // 4
        - (gy2 + 99) // 100
        + (gy2 + 399) // 400
    )

    for i in range(gm2):
        g_day_no += g_days_in_month[i]

    if (
        gm2 > 1
        and (
            gy % 4 == 0
            and (
                gy % 100 != 0
                or gy % 400 == 0
            )
        )
    ):
        g_day_no += 1

    g_day_no += gd2

    j_day_no = g_day_no - 79

    j_np = j_day_no // 12053
    j_day_no %= 12053

    jy = 979 + 33 * j_np + 4 * (
        j_day_no // 1461
    )

    j_day_no %= 1461

    if j_day_no >= 366:
        jy += (
            (j_day_no - 1) // 365
        )
        j_day_no = (
            j_day_no - 1
        ) % 365

    i = 0

    while (
        i < 11
        and j_day_no >= j_days_in_month[i]
    ):
        j_day_no -= j_days_in_month[i]
        i += 1

    jm = i + 1
    jd = j_day_no + 1

    return jy, jm, jd


# --------------------------------------------------------
# قالب تاریخ و ساعت ایران
# --------------------------------------------------------

def format_iran_datetime_jalali(
    value,
):
    if value is None:
        return ""

    try:
        if isinstance(
            value,
            (int, float),
        ):
            dt = datetime.fromtimestamp(
                value,
                tz=timezone.utc,
            )
        else:
            text = str(value).strip()

            if not text:
                return ""

            if text.endswith("Z"):
                text = text[:-1] + "+00:00"

            dt = datetime.fromisoformat(
                text
            )

            if dt.tzinfo is None:
                dt = dt.replace(
                    tzinfo=timezone.utc
                )

    except (
        TypeError,
        ValueError,
        OverflowError,
        OSError,
    ):
        return ""

    iran_tz = timezone(
        timedelta(hours=3, minutes=30)
    )

    dt = dt.astimezone(
        iran_tz
    )

    jy, jm, jd = gregorian_to_jalali(
        dt.year,
        dt.month,
        dt.day,
    )

    return (
        f"{jy:04d}/{jm:02d}/{jd:02d}"
        f" - "
        f"{dt.hour:02d}:{dt.minute:02d}"
    )


# --------------------------------------------------------
# نمایش نتیجه
# --------------------------------------------------------

def format_score(
    score,
    home_name="Home",
    away_name="Away",
    penalty_score=None,
):
    if not isinstance(
        score,
        dict,
    ):
        return ""

    home_score = score.get(
        "home"
    )

    away_score = score.get(
        "away"
    )

    if home_score is None:
        return ""

    if away_score is None:
        return ""

    try:
        home_score = int(
            home_score
        )
        away_score = int(
            away_score
        )
    except (
        TypeError,
        ValueError,
    ):
        return ""

    penalty_home = None
    penalty_away = None

    if isinstance(
        penalty_score,
        dict,
    ):
        penalty_home = (
            penalty_score.get(
                "home"
            )
        )

        penalty_away = (
            penalty_score.get(
                "away"
            )
        )

        try:
            if (
                penalty_home is not None
                and penalty_away is not None
            ):
                penalty_home = int(
                    penalty_home
                )

                penalty_away = int(
                    penalty_away
                )
        except (
            TypeError,
            ValueError,
        ):
            penalty_home = None
            penalty_away = None

    if (
        penalty_home is not None
        and penalty_away is not None
    ):
        return (
            f"{home_name} "
            f"{home_score} ({penalty_home}) "
            f"🆚 "
            f"({penalty_away}) {away_score} "
            f"{away_name}"
        )

    return (
        f"{home_name} "
        f"{home_score} "
        f"🆚 "
        f"{away_score} "
        f"{away_name}"
    )


def has_valid_score(
    score,
):
    if not isinstance(
        score,
        dict,
    ):
        return False

    if score.get(
        "home"
    ) is None:
        return False

    if score.get(
        "away"
    ) is None:
        return False

    try:
        int(
            score.get("home")
        )

        int(
            score.get("away")
        )
    except (
        TypeError,
        ValueError,
    ):
        return False

    return True


# --------------------------------------------------------
# داده رویدادهای بازیکن
# --------------------------------------------------------

def _empty_player_event_data():
    return {
        "goals": 0,
        "assists": 0,
        "own_goals": 0,
        "penalty_goals": 0,
        "red_cards": 0,
    }


def build_final_player_events(
    events,
):
    result = {}

    if not isinstance(
        events,
        list,
    ):
        return result

    for event in events:

        if not isinstance(
            event,
            dict,
        ):
            continue

        event_type = get_event_type(
            event
        )

        if event_type != "goal":
            continue

        if event.get(
            "shootout",
            False,
        ):
            continue

        player_id = get_event_player_id(
            event
        )

        if player_id is None:
            continue

        if player_id not in result:
            result[player_id] = (
                _empty_player_event_data()
            )

        data = result[player_id]

        if is_own_goal(
            event
        ):
            data[
                "own_goals"
            ] += 1

        else:
            data[
                "goals"
            ] += 1

            if is_penalty_goal(
                event
            ):
                data[
                    "penalty_goals"
                ] += 1

        assist_id = (
            get_event_assist_player_id(
                event
            )
        )

        if assist_id is not None:

            if assist_id not in result:
                result[assist_id] = (
                    _empty_player_event_data()
                )

            result[
                assist_id
            ][
                "assists"
            ] += 1

    for event in events:

        if not isinstance(
            event,
            dict,
        ):
            continue

        event_type = get_event_type(
            event
        )

        if event_type != "card":
            continue

        card = str(
            event.get(
                "card",
                "",
            )
        ).lower()

        if not (
            card in (
                "red",
                "redcard",
                "red_card",
            )
            or "red" in card
        ):
            continue

        player_id = get_event_player_id(
            event
        )

        if player_id is None:
            continue

        if player_id not in result:
            result[player_id] = (
                _empty_player_event_data()
            )

        result[player_id][
            "red_cards"
        ] += 1

    return result


def get_player_event_markers(
    player,
    player_events,
):
    player_id = get_player_id(
        player
    )

    if player_id is None:
        return []

    data = player_events.get(
        player_id
    )

    if data is None:
        data = player_events.get(
            str(player_id)
        )

    if not isinstance(
        data,
        dict,
    ):
        return []

    markers = []

    goals = int(
        data.get(
            "goals",
            0,
        )
        or 0
    )

    assists = int(
        data.get(
            "assists",
            0,
        )
        or 0
    )

    own_goals = int(
        data.get(
            "own_goals",
            0,
        )
        or 0
    )

    red_cards = int(
        data.get(
            "red_cards",
            0,
        )
        or 0
    )

    if goals == 1:
        markers.append(
            "⚽️"
        )

    elif goals > 1:
        markers.append(
            f"⚽️×{goals}"
        )

    if assists == 1:
        markers.append(
            "🅰️"
        )

    elif assists > 1:
        markers.append(
            f"🅰️×{assists}"
        )

    if own_goals == 1:
        markers.append(
            "⚽️ OG"
        )

    elif own_goals > 1:
        markers.append(
            f"⚽️ OG×{own_goals}"
        )

    if red_cards == 1:
        markers.append(
            "🟥"
        )

    elif red_cards > 1:
        markers.append(
            f"🟥×{red_cards}"
        )

    return markers


# --------------------------------------------------------
# بازیکن
# --------------------------------------------------------

def format_player(
    player,
    show_rating,
    player_events=None,
):
    name = get_player_name(
        player
    )

    if not name:
        return ""

    shirt_number = ""

    if isinstance(
        player,
        dict,
    ):
        shirt_number = (
            player.get(
                "shirtNumber"
            )
            or ""
        )

    if shirt_number:
        result = (
            f"{shirt_number}. {name}"
        )
    else:
        result = name

    if show_rating:

        rating = get_player_rating(
            player
        )

        if rating is not None:
            result += (
                f" — {rating:.1f}"
            )

    if player_events is not None:

        markers = (
            get_player_event_markers(
                player,
                player_events,
            )
        )

        if markers:
            result += (
                " ("
                + " ".join(
                    markers
                )
                + ")"
            )

    return result


# --------------------------------------------------------
# خط بازیکنان
# --------------------------------------------------------

def format_player_line(
    icon,
    players,
    show_rating,
    player_events=None,
):
    names = []

    for player in players:

        name = format_player(
            player,
            show_rating,
            player_events,
        )

        if name:
            names.append(
                name
            )

    if not names:
        return ""

    return (
        f"{icon} "
        + " | ".join(
            names
        )
    )


# --------------------------------------------------------
# ترکیب تیم
# --------------------------------------------------------

def format_team_lineup(
    team_name,
    team,
    show_rating,
    team_icon,
    player_events=None,
):
    if not isinstance(
        team,
        dict,
    ):
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

    lines = [
        f"{team_icon} {team_name}"
    ]

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
        player_events,
    )

    if line:
        lines.append(line)

    line = format_player_line(
        "🛡",
        groups["defender"],
        show_rating,
        player_events,
    )

    if line:
        lines.append(line)

    line = format_player_line(
        "⚙️",
        groups["midfielder"],
        show_rating,
        player_events,
    )

    if line:
        lines.append(line)

    line = format_player_line(
        "⚡",
        groups["attacker"],
        show_rating,
        player_events,
    )

    if line:
        lines.append(line)

    if groups["unknown"]:

        line = format_player_line(
            "⚽",
            groups["unknown"],
            show_rating,
            player_events,
        )

        if line:
            lines.append(line)

    lines.append("")

    substitute_names = []

    for player in substitutes:

        name = format_player(
            player,
            show_rating,
            player_events,
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

    return "\n".join(
        lines
    )


# --------------------------------------------------------
# نام بازیکن رویداد
# --------------------------------------------------------

def get_event_player_name(
    event,
):
    if not isinstance(
        event,
        dict,
    ):
        return ""

    player = event.get(
        "player"
    )

    if isinstance(
        player,
        dict,
    ):
        name = (
            player.get("name")
            or player.get("shortName")
            or ""
        )

        if name:
            return name

    return (
        event.get(
            "playerName"
        )
        or ""
    )


# --------------------------------------------------------
# متن گلزن
# --------------------------------------------------------

def _get_scorer_text(
    event,
):
    player_name = (
        get_event_player_name(
            event
        )
    )

    if not player_name:
        player_name = (
            "بازیکن نامشخص"
        )

    minute = get_goal_minute(
        event
    )

    if minute is None:
        return player_name

    return (
        f"{player_name} "
        f"({minute}')"
    )


# --------------------------------------------------------
# گل‌های یک تیم
# --------------------------------------------------------

def _get_goal_events(
    events,
    home_or_away,
):
    result = []

    if not isinstance(
        events,
        list,
    ):
        return result

    for index, event in enumerate(
        events
    ):

        if not isinstance(
            event,
            dict,
        ):
            continue

        event_type = get_event_type(
            event
        )

        if event_type != "goal":
            continue

        if event.get(
            "shootout",
            False,
        ):
            continue

        event_team = get_event_team(
            event
        )

        if event_team != home_or_away:
            continue

        scorer_text = _get_scorer_text(
            event
        )

        if is_own_goal(
            event
        ):
            scorer_text += " OG"

        minute = get_goal_minute(
            event
        )

        try:
            minute_text = str(
                minute
            )

            match = re.match(
                r"^(\d+)(?:\+(\d+))?$",
                minute_text,
            )

            if match:
                base_minute = int(
                    match.group(1)
                )

                added_minute = int(
                    match.group(2)
                    or 0
                )

                sort_minute = (
                    base_minute
                    + added_minute / 100
                )

            else:
                sort_minute = float(
                    minute_text
                    .replace(
                        "'",
                        "",
                    )
                )

        except (
            TypeError,
            ValueError,
        ):
            sort_minute = 9999

        result.append(
            {
                "event": event,
                "text": scorer_text,
                "minute": sort_minute,
                "index": index,
            }
        )

    result.sort(
        key=lambda item: (
            item["minute"],
            item["index"],
        )
    )

    return result


# --------------------------------------------------------
# گلزنان برای پیام قدیمی
# --------------------------------------------------------

def _build_scorer_lines(
    home_scorers,
    away_scorers,
):
    lines = []

    if home_scorers:
        lines.append(
            "⚽️ "
            + " | ".join(
                home_scorers
            )
        )

    if away_scorers:
        lines.append(
            "⚽️ "
            + " | ".join(
                away_scorers
            )
        )

    return lines


def format_scorers(
    home_scorers,
    away_scorers,
):
    lines = []

    if home_scorers:
        lines.append(
            "⚽ "
            + " | ".join(
                home_scorers
            )
        )

    if away_scorers:
        lines.append(
            "⚽ "
            + " | ".join(
                away_scorers
            )
        )

    return lines


# --------------------------------------------------------
# پیام ترکیب
# --------------------------------------------------------

def build_lineup_message(
    snapshot,
    player_events=None,
    home_scorers=None,
    away_scorers=None,
    show_rating=False,
    show_final_score=False,
):
    home_name = get_display_team_name(
        snapshot,
        "home",
    )

    away_name = get_display_team_name(
        snapshot,
        "away",
    )

    league = (
        snapshot.get("league_fa")
        or snapshot.get("league")
        or "نامشخص"
    )

    kickoff = (
        snapshot.get(
            "start_formatted"
        )
        or "نامشخص"
    )

    home_team = snapshot.get(
        "home_team"
    )

    away_team = snapshot.get(
        "away_team"
    )

    message = [
        f"🏆 {league}",
        "",
    ]

    if show_final_score:

        score = snapshot.get(
            "score"
        )

        penalty_score = snapshot.get(
            "penalty_score"
        )

        score_text = format_score(
            score,
            home_name,
            away_name,
            penalty_score,
        )

        if score_text:
            message.append(
                score_text
            )

            message.append("")

        message.append(
            (
                f"🕐 {kickoff} "
                f"به وقت ایران"
            )
        )

    else:

        message.append(
            (
                f"⚽️ {home_name} "
                f"🆚 {away_name}"
            )
        )

        message.append(
            (
                f"🕐 {kickoff} "
                f"به وقت ایران"
            )
        )

    if show_rating:

        scorer_lines = (
            format_scorers(
                home_scorers
                or [],
                away_scorers
                or [],
            )
        )

        if scorer_lines:
            message.append("")
            message.extend(
                scorer_lines
            )

    message.append("")

    message.append(
        format_team_lineup(
            home_name,
            home_team,
            show_rating,
            "🔴",
            player_events,
        )
    )

    message.append("")

    message.append(
        format_team_lineup(
            away_name,
            away_team,
            show_rating,
            "🔵",
            player_events,
        )
    )

    return "\n".join(
        message
    )


# --------------------------------------------------------
# پیام شروع بازی
# --------------------------------------------------------

def build_start_message(
    snapshot,
):
    home_name = get_display_team_name(
        snapshot,
        "home",
    )

    away_name = get_display_team_name(
        snapshot,
        "away",
    )

    return (
        "🔴 بازی شروع شد\n"
        "\n"
        f"{home_name} 🆚 {away_name}"
    )


# --------------------------------------------------------
# پیام گل
# --------------------------------------------------------

def build_goal_message(
    snapshot,
    event,
    score=None,
):
    home_name = get_display_team_name(
        snapshot,
        "home",
    )

    away_name = get_display_team_name(
        snapshot,
        "away",
    )

    player_name = (
        get_event_player_name(
            event
        )
    )

    if not player_name:
        player_name = (
            "بازیکن نامشخص"
        )

    event_team = get_event_team(
        event
    )

    if event_team is True:
        team_name = home_name

    elif event_team is False:
        team_name = away_name

    else:
        team_name = ""

    own_goal = is_own_goal(
        event
    )

    minute = get_goal_minute(
        event
    )

    if minute is not None:
        minute_text = (
            f"⏱ دقیقه {minute}"
        )
    else:
        minute_text = ""

    if own_goal:
        title = (
            "⚽️ گل به خودی"
        )
    else:
        title = (
            "⚽️ گل"
        )

    lines = [
        title,
    ]

    if team_name:

        if own_goal:
            lines.append(
                f"به سود {team_name}!"
            )
        else:
            lines.append(
                f"برای {team_name}!"
            )

    if minute_text:
        lines.append(
            minute_text
        )

    lines.append(
        player_name
    )

    if is_penalty_goal(
        event
    ):
        lines.append(
            "🎯 پنالتی"
        )

    score_for_display = score

    if own_goal and isinstance(
        score,
        dict,
    ):

        score_for_display = dict(
            score
        )

        if event_team is True:

            try:
                score_for_display[
                    "home"
                ] = (
                    int(
                        score_for_display.get(
                            "home",
                            0,
                        )
                    )
                    + 1
                )

            except (
                TypeError,
                ValueError,
            ):
                score_for_display = score

        elif event_team is False:

            try:
                score_for_display[
                    "away"
                ] = (
                    int(
                        score_for_display.get(
                            "away",
                            0,
                        )
                    )
                    + 1
                )

            except (
                TypeError,
                ValueError,
            ):
                score_for_display = score

    score_text = format_score(
        score_for_display,
        home_name,
        away_name,
    )

    if score_text:
        lines.append("")
        lines.append(
            score_text
        )

    return "\n".join(
        lines
    )


# --------------------------------------------------------
# پیام گل مردود
# --------------------------------------------------------

def build_cancelled_goal_message(
    snapshot,
    cancelled_goal,
    score=None,
):
    home_name = get_display_team_name(
        snapshot,
        "home",
    )

    away_name = get_display_team_name(
        snapshot,
        "away",
    )

    if not isinstance(
        cancelled_goal,
        dict,
    ):
        return ""

    goal_event = (
        cancelled_goal.get(
            "goal_event"
        )
    )

    if not isinstance(
        goal_event,
        dict,
    ):
        return ""

    player_name = (
        get_event_player_name(
            goal_event
        )
    )

    if not player_name:
        player_name = (
            "بازیکن نامشخص"
        )

    event_team = (
        cancelled_goal.get(
            "event_team"
        )
    )

    if event_team is None:
        event_team = (
            get_event_team(
                goal_event
            )
        )

    if event_team is True:
        team_name = home_name

    elif event_team is False:
        team_name = away_name

    else:
        team_name = ""

    minute = (
        cancelled_goal.get(
            "minute"
        )
    )

    if minute is None:
        minute = get_goal_minute(
            goal_event
        )

    lines = [
        "❌ گل مردود شد!",
    ]

    if team_name:
        lines.append(
            f"گل {team_name}"
        )

    if minute is not None:
        lines.append(
            f"⏱ دقیقه {minute}"
        )

    lines.append(
        player_name
    )

    lines.append(
        "🖥 VAR گل را مردود اعلام کرد."
    )

    score_text = format_score(
        score,
        home_name,
        away_name,
    )

    if score_text:
        lines.append("")
        lines.append(
            score_text
        )

    return "\n".join(
        lines
    )


# --------------------------------------------------------
# پایان نیمه اول
# --------------------------------------------------------

def build_half_time_message(
    snapshot,
    score=None,
):
    home_name = get_display_team_name(
        snapshot,
        "home",
    )

    away_name = get_display_team_name(
        snapshot,
        "away",
    )

    lines = [
        "⏸️ پایان نیمه اول",
        "",
        f"{home_name} 🆚 {away_name}",
    ]

    score_text = format_score(
        score,
        home_name,
        away_name,
    )

    if score_text:
        lines.append("")
        lines.append(
            score_text
        )

    return "\n".join(
        lines
    )


# --------------------------------------------------------
# کارت قرمز
# --------------------------------------------------------

def build_red_card_message(
    snapshot,
    event,
):
    home_name = get_display_team_name(
        snapshot,
        "home",
    )

    away_name = get_display_team_name(
        snapshot,
        "away",
    )

    player_name = (
        get_event_player_name(
            event
        )
    )

    if not player_name:
        player_name = (
            "بازیکن نامشخص"
        )

    minute = get_goal_minute(
        event
    )

    event_team = get_event_team(
        event
    )

    if event_team is True:
        team_name = home_name

    elif event_team is False:
        team_name = away_name

    else:
        team_name = ""

    lines = [
        "🟥 کارت قرمز",
        player_name,
    ]

    if team_name:
        lines.append(
            team_name
        )

    if minute is not None:
        lines.append(
            f"⏱ دقیقه {minute}"
        )

    lines.append(
        f"{home_name} 🆚 {away_name}"
    )

    return "\n".join(
        lines
    )


# --------------------------------------------------------
# پیام عمومی event
# --------------------------------------------------------

def build_event_message(
    snapshot,
    event,
    score=None,
):
    if not isinstance(
        event,
        dict,
    ):
        return ""

    event_type = get_event_type(
        event
    )

    if event_type == "goal":
        return build_goal_message(
            snapshot,
            event,
            score,
        )

    if event_type == "card":

        card = str(
            event.get(
                "card",
                "",
            )
        ).lower()

        if (
            card in (
                "red",
                "redcard",
                "red_card",
            )
            or "red" in card
        ):
            return build_red_card_message(
                snapshot,
                event,
            )

    return ""


# --------------------------------------------------------
# نمایش مقدار آمار
# --------------------------------------------------------

def format_stat_value(
    label,
    value,
):
    if value is None:
        return ""

    if label == "xG":
        try:
            return f"{float(value):.2f}"
        except (
            TypeError,
            ValueError,
        ):
            return str(value)

    if label == "مالکیت":
        try:
            number = float(
                value
            )

            return (
                f"{number:g}%"
            )

        except (
            TypeError,
            ValueError,
        ):
            return str(value)

    if isinstance(
        value,
        float,
    ):

        if value.is_integer():
            return str(
                int(value)
            )

        return (
            f"{value:.2f}"
            .rstrip("0")
            .rstrip(".")
        )

    return str(
        value
    )


# --------------------------------------------------------
# ترتیب آمار نهایی
# --------------------------------------------------------

FINAL_STAT_ORDER = [
    "xG",
    "شوت",
    "شوت در چارچوب",
    "مالکیت",
    "پاس",
    "دقت پاس",
    "پاس دقیق",
    "کرنر",
    "خطا",
    "آفساید",
    "کارت زرد",
    "کارت قرمز",
]


FINAL_STAT_ICONS = {
    "xG": "🎯",
    "شوت": "💥",
    "شوت در چارچوب": "🥅",
    "مالکیت": "⚽️",
    "پاس": "🔄",
    "دقت پاس": "✅",
    "پاس دقیق": "✅",
    "کرنر": "🚩",
    "خطا": "⚠️",
    "آفساید": "🚫",
    "کارت زرد": "🟨",
    "کارت قرمز": "🟥",
}


# --------------------------------------------------------
# استخراج داده آمار
# --------------------------------------------------------

def _get_stat_data(
    stats,
    possible_keys,
):
    if not isinstance(
        stats,
        dict,
    ):
        return None

    for key in possible_keys:

        data = stats.get(
            key
        )

        if isinstance(
            data,
            dict,
        ):
            return data

    return None


def _get_stat_rows(
    stats,
):
    rows = []

    if not isinstance(
        stats,
        dict,
    ):
        return rows

    aliases = {
        "xG": (
            "xG",
            "xg",
            "expected_goals",
        ),
        "شوت": (
            "شوت",
            "shots",
            "Shots",
        ),
        "شوت در چارچوب": (
            "شوت در چارچوب",
            "shots_on_target",
            "Shots on target",
        ),
        "مالکیت": (
            "مالکیت",
            "possession",
            "Possession",
        ),
        "پاس": (
            "پاس",
            "passes",
            "Passes",
        ),
        "دقت پاس": (
            "دقت پاس",
            "pass_accuracy",
        ),
        "پاس دقیق": (
            "پاس دقیق",
            "accurate_passes",
            "Accurate passes",
        ),
        "کرنر": (
            "کرنر",
            "corners",
            "Corners",
        ),
        "خطا": (
            "خطا",
            "fouls",
            "Fouls",
        ),
        "آفساید": (
            "آفساید",
            "offsides",
            "Offsides",
        ),
        "کارت زرد": (
            "کارت زرد",
            "yellow_cards",
            "Yellow cards",
        ),
        "کارت قرمز": (
            "کارت قرمز",
            "red_cards",
            "Red cards",
        ),
    }

    for label in FINAL_STAT_ORDER:

        data = _get_stat_data(
            stats,
            aliases.get(
                label,
                (label,),
            ),
        )

        if not isinstance(
            data,
            dict,
        ):
            continue

        home_value = data.get(
            "home"
        )

        away_value = data.get(
            "away"
        )

        if (
            home_value is None
            or away_value is None
        ):
            continue

        rows.append(
            (
                label,
                home_value,
                away_value,
            )
        )

    return rows


# --------------------------------------------------------
# بازیکن برای Rich Message
# --------------------------------------------------------

def _format_rich_player(
    player,
    show_rating=False,
    player_events=None,
):
    name = get_player_name(
        player
    )

    if not name:
        return ""

    shirt_number = ""

    if isinstance(
        player,
        dict,
    ):
        shirt_number = (
            player.get(
                "shirtNumber"
            )
            or ""
        )

    if shirt_number:
        text = (
            f"{shirt_number}. {name}"
        )
    else:
        text = name

    if show_rating:

        rating = get_player_rating(
            player
        )

        if rating is not None:
            text += (
                f" — {rating:.1f}"
            )

    if player_events is not None:

        markers = (
            get_player_event_markers(
                player,
                player_events,
            )
        )

        if markers:
            text += (
                " "
                + " ".join(
                    markers
                )
            )

    return text


# --------------------------------------------------------
# سربرگ تیم در جدول
# --------------------------------------------------------

def _get_team_header_text(
    team_name,
    team,
):
    if not isinstance(
        team,
        dict,
    ):
        return team_name

    coach = get_coach(
        team
    )

    formation = get_formation(
        team
    )

    lines = [
        team_name
    ]

    if coach:
        lines.append(
            f"👔 {coach}"
        )

    if formation:
        lines.append(
            f"📐 {formation}"
        )

    return "\n".join(
        lines
    )


# --------------------------------------------------------
# ساخت جدول ترکیب Rich
# --------------------------------------------------------

def _build_rich_lineup_rows(
    home_name,
    away_name,
    home_team,
    away_team,
    show_rating=False,
    player_events=None,
):
    home_starters = []

    away_starters = []

    home_substitutes = []

    away_substitutes = []

    if isinstance(
        home_team,
        dict,
    ):
        home_starters = get_starters(
            home_team
        )

        home_substitutes = get_substitutes(
            home_team
        )

    if isinstance(
        away_team,
        dict,
    ):
        away_starters = get_starters(
            away_team
        )

        away_substitutes = get_substitutes(
            away_team
        )

    rows = []

    rows.append(
        [
            {
                "text": _get_team_header_text(
                    home_name,
                    home_team,
                ),
                "is_header": True,
                "align": "center",
                "valign": "middle",
            },
            {
                "text": _get_team_header_text(
                    away_name,
                    away_team,
                ),
                "is_header": True,
                "align": "center",
                "valign": "middle",
            },
        ]
    )

    for index in range(11):

        home_text = ""

        away_text = ""

        if index < len(
            home_starters
        ):
            home_text = (
                _format_rich_player(
                    home_starters[index],
                    show_rating,
                    player_events,
                )
            )

        if index < len(
            away_starters
        ):
            away_text = (
                _format_rich_player(
                    away_starters[index],
                    show_rating,
                    player_events,
                )
            )

        rows.append(
            [
                {
                    "text": home_text,
                    "align": "center",
                    "valign": "middle",
                },
                {
                    "text": away_text,
                    "align": "center",
                    "valign": "middle",
                },
            ]
        )

    home_sub_texts = []

    for player in home_substitutes:

        text = _format_rich_player(
            player,
            show_rating,
            player_events,
        )

        if text:
            home_sub_texts.append(
                text
            )

    away_sub_texts = []

    for player in away_substitutes:

        text = _format_rich_player(
            player,
            show_rating,
            player_events,
        )

        if text:
            away_sub_texts.append(
                text
            )

    home_sub_text = (
        "🔄 تعویضی‌ها\n"
        + "\n".join(
            home_sub_texts
        )
        if home_sub_texts
        else "🔄 تعویضی‌ها"
    )

    away_sub_text = (
        "🔄 تعویضی‌ها\n"
        + "\n".join(
            away_sub_texts
        )
        if away_sub_texts
        else "🔄 تعویضی‌ها"
    )

    rows.append(
        [
            {
                "text": home_sub_text,
                "align": "center",
                "valign": "top",
            },
            {
                "text": away_sub_text,
                "align": "center",
                "valign": "top",
            },
        ]
    )

    return rows


# --------------------------------------------------------
# گل‌های Rich
# --------------------------------------------------------

def _get_rich_goal_events(
    events,
):
    goals = []

    if not isinstance(
        events,
        list,
    ):
        return goals

    for index, event in enumerate(
        events
    ):

        if not isinstance(
            event,
            dict,
        ):
            continue

        event_type = get_event_type(
            event
        )

        if event_type != "goal":
            continue

        # پنالتی‌های ضربات پنالتی
        # جزو گل‌های جریان بازی نیستند.
        if event.get(
            "shootout",
            False,
        ):
            continue

        event_team = get_event_team(
            event
        )

        # get_event_team در event_detector:
        # True  = میزبان
        # False = مهمان
        if event_team not in (
            True,
            False,
        ):
            continue

        scorer_text = _get_scorer_text(
            event
        )

        if not scorer_text:
            continue

        # در گل به خودی، event_team همچنان
        # تیمی است که گل به سود آن ثبت شده.
        if is_own_goal(
            event
        ):
            scorer_text += " OG"

        minute = get_goal_minute(
            event
        )

        try:
            minute_text = str(
                minute
            )

            match = re.match(
                r"^(\d+)(?:\+(\d+))?$",
                minute_text,
            )

            if match:
                base_minute = int(
                    match.group(1)
                )

                added_minute = int(
                    match.group(2)
                    or 0
                )

                sort_minute = (
                    base_minute
                    + added_minute / 100
                )

            else:
                sort_minute = float(
                    minute_text
                    .replace(
                        "'",
                        "",
                    )
                )

        except (
            TypeError,
            ValueError,
        ):
            sort_minute = 9999

        goals.append(
            {
                "event": event,
                "team": (
                    "home"
                    if event_team is True
                    else "away"
                ),
                "text": scorer_text,
                "minute": sort_minute,
                "index": index,
            }
        )

    goals.sort(
        key=lambda item: (
            item["minute"],
            item["index"],
        )
    )

    return goals


# --------------------------------------------------------
# جدول گلزنان با ترتیب زمانی واقعی
# --------------------------------------------------------

# --------------------------------------------------------
# جدول گلزنان
# --------------------------------------------------------

def _build_rich_scorer_table(
    events,
    home_name,
    away_name,
):
    goals = _get_rich_goal_events(
        events
    )

    if not goals:
        return None

    home_goals = []

    away_goals = []

    for goal in goals:

        if goal["team"] == "home":
            home_goals.append(
                goal["text"]
            )

        elif goal["team"] == "away":
            away_goals.append(
                goal["text"]
            )

    rows = [
        [
            {
                "text": home_name,
                "is_header": True,
                "align": "center",
                "valign": "middle",
            },
            {
                "text": away_name,
                "is_header": True,
                "align": "center",
                "valign": "middle",
            },
        ]
    ]

    row_count = max(
        len(home_goals),
        len(away_goals),
    )

    for index in range(
        row_count
    ):

        home_text = ""

        away_text = ""

        if index < len(
            home_goals
        ):
            home_text = (
                home_goals[index]
            )

        if index < len(
            away_goals
        ):
            away_text = (
                away_goals[index]
            )

        rows.append(
            [
                {
                    "text": home_text,
                    "align": "center",
                    "valign": "middle",
                },
                {
                    "text": away_text,
                    "align": "center",
                    "valign": "middle",
                },
            ]
        )

    return {
        "type": "table",
        "is_bordered": True,
        "is_compact": False,
        "cells": rows,
    }

# --------------------------------------------------------
# سربرگ مسابقه Rich
# --------------------------------------------------------

def _build_rich_match_header(
    snapshot,
    show_final_score=False,
    events=None,
):
    home_name = get_display_team_name(
        snapshot,
        "home",
    )

    away_name = get_display_team_name(
        snapshot,
        "away",
    )

    league = (
        snapshot.get("league_fa")
        or snapshot.get("league")
        or "نامشخص"
    )

    blocks = [
        {
            "type": "paragraph",
            "text": f"🏆 {league}",
        }
    ]

    if show_final_score:

        score = snapshot.get(
            "score"
        )

        penalty_score = snapshot.get(
            "penalty_score"
        )

        score_text = format_score(
            score,
            home_name,
            away_name,
            penalty_score,
        )

        if score_text:
            blocks.append(
                {
                    "type": "paragraph",
                    "text": score_text,
                }
            )

        if events:

            scorer_table = (
                _build_rich_scorer_table(
                    events,
                    home_name,
                    away_name,
                )
            )

            if scorer_table:
                blocks.append(
                    scorer_table
                )

    else:

        blocks.append(
            {
                "type": "paragraph",
                "text": (
                    f"⚽️ {home_name} "
                    f"🆚 {away_name}"
                ),
            }
        )

    kickoff = (
        snapshot.get(
            "start_formatted"
        )
        or "نامشخص"
    )

    blocks.append(
        {
            "type": "paragraph",
            "text": (
                f"🕐 {kickoff} "
                f"به وقت ایران"
            ),
        }
    )

    return blocks


# --------------------------------------------------------
# پیام Rich ترکیب
# --------------------------------------------------------

def build_lineup_rich_message(
    snapshot,
    show_rating=False,
):
    home_name = get_display_team_name(
        snapshot,
        "home",
    )

    away_name = get_display_team_name(
        snapshot,
        "away",
    )

    home_team = snapshot.get(
        "home_team"
    )

    away_team = snapshot.get(
        "away_team"
    )

    blocks = (
        _build_rich_match_header(
            snapshot,
            show_final_score=False,
            events=None,
        )
    )

    blocks.append(
        _build_rich_lineup_table(
            home_name,
            away_name,
            home_team,
            away_team,
            show_rating=show_rating,
            player_events=None,
        )
    )

    return {
        "is_rtl": True,
        "blocks": blocks,
    }


# --------------------------------------------------------
# جدول ترکیب Rich
# --------------------------------------------------------

def _build_rich_lineup_table(
    home_name,
    away_name,
    home_team,
    away_team,
    show_rating=False,
    player_events=None,
):
    rows = _build_rich_lineup_rows(
        home_name,
        away_name,
        home_team,
        away_team,
        show_rating,
        player_events,
    )

    return {
        "type": "table",
        "is_bordered": True,
        "is_compact": False,
        "cells": rows,
    }


# --------------------------------------------------------
# پیام نهایی ترکیب + امتیاز Rich
# --------------------------------------------------------

def build_final_lineup_rich_message(
    snapshot,
    events=None,
):
    player_events = (
        build_final_player_events(
            events
        )
    )

    home_name = get_display_team_name(
        snapshot,
        "home",
    )

    away_name = get_display_team_name(
        snapshot,
        "away",
    )

    home_team = snapshot.get(
        "home_team"
    )

    away_team = snapshot.get(
        "away_team"
    )

    blocks = (
        _build_rich_match_header(
            snapshot,
            show_final_score=True,
            events=events,
        )
    )

    blocks.append(
        _build_rich_lineup_table(
            home_name,
            away_name,
            home_team,
            away_team,
            show_rating=True,
            player_events=player_events,
        )
    )

    return {
        "is_rtl": True,
        "blocks": blocks,
    }


# --------------------------------------------------------
# پیام نهایی آمار Rich
# --------------------------------------------------------

def build_final_stats_rich_message(
    snapshot,
    score=None,
):
    home_name = get_display_team_name(
        snapshot,
        "home",
    )

    away_name = get_display_team_name(
        snapshot,
        "away",
    )

    stats = snapshot.get(
        "stats"
    )

    if not isinstance(
        stats,
        dict,
    ):
        stats = {}

    blocks = [
        {
            "type": "paragraph",
            "text": "📊 آمار بازی",
        }
    ]

    if score is None:
        score = snapshot.get(
            "score"
        )

    penalty_score = snapshot.get(
        "penalty_score"
    )

    score_text = format_score(
        score,
        home_name,
        away_name,
        penalty_score,
    )

    if score_text:
        blocks.append(
            {
                "type": "paragraph",
                "text": score_text,
            }
        )

    stat_rows = _get_stat_rows(
        stats
    )

    if not stat_rows:
        blocks.append(
            {
                "type": "paragraph",
                "text": (
                    "آمار بازی در داده‌های "
                    "FotMob پیدا نشد."
                ),
            }
        )

        return {
            "is_rtl": True,
            "blocks": blocks,
        }

    cells = [
        [
            {
                "text": "آمار",
                "is_header": True,
                "align": "center",
                "valign": "middle",
            },
            {
                "text": home_name,
                "is_header": True,
                "align": "center",
                "valign": "middle",
            },
            {
                "text": away_name,
                "is_header": True,
                "align": "center",
                "valign": "middle",
            },
        ]
    ]

    for (
        label,
        home_value,
        away_value,
    ) in stat_rows:

        icon = FINAL_STAT_ICONS.get(
            label,
            "•",
        )

        display_label = (
            f"{icon} {label}"
        )

        cells.append(
            [
                {
                    "text": display_label,
                    "align": "center",
                    "valign": "middle",
                },
                {
                    "text": format_stat_value(
                        label,
                        home_value,
                    ),
                    "align": "center",
                    "valign": "middle",
                },
                {
                    "text": format_stat_value(
                        label,
                        away_value,
                    ),
                    "align": "center",
                    "valign": "middle",
                },
            ]
        )

    blocks.append(
        {
            "type": "table",
            "is_bordered": True,
            "is_striped": True,
            "is_compact": False,
            "cells": cells,
        }
    )

    return {
        "is_rtl": True,
        "blocks": blocks,
    }


# --------------------------------------------------------
# سازگاری با کدهای قبلی
# --------------------------------------------------------

def build_final_lineup_message(
    snapshot,
    events=None,
):
    player_events = (
        build_final_player_events(
            events
        )
    )

    message = build_lineup_message(
        snapshot,
        player_events=player_events,
        show_rating=True,
        show_final_score=True,
    )

    return message


def build_final_stats_message(
    snapshot,
    score=None,
):
    home_name = get_display_team_name(
        snapshot,
        "home",
    )

    away_name = get_display_team_name(
        snapshot,
        "away",
    )

    stats = snapshot.get(
        "stats"
    )

    if not isinstance(
        stats,
        dict,
    ):
        stats = {}

    lines = [
        "📊 آمار بازی",
        "",
    ]

    if score is None:
        score = snapshot.get(
            "score"
        )

    penalty_score = snapshot.get(
        "penalty_score"
    )

    score_text = format_score(
        score,
        home_name,
        away_name,
        penalty_score,
    )

    if score_text:
        lines.append(
            score_text
        )

        lines.append("")

    available_stats = _get_stat_rows(
        stats
    )

    if not available_stats:
        lines.append(
            "آمار بازی در داده‌های FotMob پیدا نشد."
        )

        return "\n".join(
            lines
        )

    home_width = max(
        8,
        len(home_name),
    )

    away_width = max(
        8,
        len(away_name),
    )

    label_width = max(
        14,
        max(
            len(
                label
            )
            for label, _, _
            in available_stats
        )
        + 2,
    )

    lines.append(
        " "
        * label_width
        + f"{home_name:>{home_width}}"
        + "    "
        + f"{away_name:>{away_width}}"
    )

    for (
        label,
        home_value,
        away_value,
    ) in available_stats:

        icon = FINAL_STAT_ICONS.get(
            label,
            "•",
        )

        display_label = (
            f"{icon} {label}"
        )

        home_text = (
            format_stat_value(
                label,
                home_value,
            )
        )

        away_text = (
            format_stat_value(
                label,
                away_value,
            )
        )

        lines.append(
            f"{display_label:<{label_width}}"
            f"{home_text:>{home_width}}"
            "    "
            f"{away_text:>{away_width}}"
        )

    return "\n".join(
        lines
    )


def build_final_message(
    snapshot,
    score=None,
):
    return build_final_stats_message(
        snapshot,
        score,
    )

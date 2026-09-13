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
    get_event_player_id,
    get_event_team,
    is_own_goal,
    is_penalty_goal,
)


# --------------------------------------------------------
# ابزارهای نتیجه
# --------------------------------------------------------

def format_score(
    score,
    home_name="Home",
    away_name="Away",
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

    return (
        f"{home_name} "
        f"{home_score} - {away_score} "
        f"{away_name}"
    )


def has_valid_score(score):

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
# نشان‌های رویداد بازیکن
# --------------------------------------------------------

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

    penalty_goals = int(
        data.get(
            "penalty_goals",
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

    red_cards = int(
        data.get(
            "red_cards",
            0,
        )
        or 0
    )

    normal_goals = (
        goals
        - penalty_goals
    )

    if penalty_goals == 1:

        markers.append(
            "P ⚽"
        )

    elif penalty_goals > 1:

        markers.append(
            f"P ⚽×{penalty_goals}"
        )

    if normal_goals == 1:

        markers.append(
            "⚽"
        )

    elif normal_goals > 1:

        markers.append(
            f"×{normal_goals} ⚽"
        )

    if assists == 1:

        markers.append(
            "👟"
        )

    elif assists > 1:

        markers.append(
            f"×{assists} 👟"
        )

    if red_cards == 1:

        markers.append(
            "❌"
        )

    elif red_cards > 1:

        markers.append(
            f"×{red_cards} ❌"
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

    result = name

    if show_rating:

        rating = get_player_rating(
            player
        )

        if rating is not None:

            result += (
                f" {rating:.1f}"
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
# گل‌زنان
# --------------------------------------------------------

def format_scorers(
    home_name,
    away_name,
    home_scorers,
    away_scorers,
):

    lines = []

    if home_scorers:

        lines.append(
            f"⚽ {home_name}: "
            + " | ".join(
                home_scorers
            )
        )

    if away_scorers:

        lines.append(
            f"⚽ {away_name}: "
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
):

    home_name = (
        snapshot.get("home")
        or "Home"
    )

    away_name = (
        snapshot.get("away")
        or "Away"
    )

    league = (
        snapshot.get("league")
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
        (
            f"⚽️ {home_name} "
            f"🆚 {away_name}"
        ),
        (
            f"🕐 {kickoff} "
            f"به وقت ایران"
        ),
    ]

    if show_rating:

        scorer_lines = (
            format_scorers(
                home_name,
                away_name,
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

    home_name = (
        snapshot.get("home")
        or "Home"
    )

    away_name = (
        snapshot.get("away")
        or "Away"
    )

    return (
        "🔴 بازی شروع شد\n"
        "\n"
        f"{home_name} 🆚 {away_name}"
    )


# --------------------------------------------------------
# نام بازیکن event
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
# پیام گل
# --------------------------------------------------------

def build_goal_message(
    snapshot,
    event,
    score=None,
):

    home_name = (
        snapshot.get("home")
        or "Home"
    )

    away_name = (
        snapshot.get("away")
        or "Away"
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

    is_home = get_event_team(
        event
    )

    if is_home is True:
        team_name = home_name

    elif is_home is False:
        team_name = away_name

    else:
        team_name = ""

    minute = get_goal_minute(
        event
    )

    if minute is not None:

        minute_text = (
            f"⏱ دقیقه {minute}"
        )

    else:

        minute_text = ""

    if is_own_goal(
        event
    ):

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
# پیام گل مردود
# --------------------------------------------------------

def build_cancelled_goal_message(
    snapshot,
    cancelled_goal,
    score=None,
):

    home_name = (
        snapshot.get("home")
        or "Home"
    )

    away_name = (
        snapshot.get("away")
        or "Away"
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

    is_home = (
        cancelled_goal.get(
            "is_home"
        )
    )

    if is_home is None:

        is_home = get_event_team(
            goal_event
        )

    if is_home is True:
        team_name = home_name

    elif is_home is False:
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

    home_name = (
        snapshot.get("home")
        or "Home"
    )

    away_name = (
        snapshot.get("away")
        or "Away"
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

    home_name = (
        snapshot.get("home")
        or "Home"
    )

    away_name = (
        snapshot.get("away")
        or "Away"
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

    is_home = get_event_team(
        event
    )

    if is_home is True:

        team_name = home_name

    elif is_home is False:

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

    event_type = str(
        event.get(
            "type",
            "",
        )
    ).lower()

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
# پیام پایان بازی
# --------------------------------------------------------

def build_final_message(
    snapshot,
    score=None,
):

    home_name = (
        snapshot.get("home")
        or "Home"
    )

    away_name = (
        snapshot.get("away")
        or "Away"
    )

    lines = [
        "🏁 پایان بازی",
        "",
    ]

    score_text = format_score(
        score,
        home_name,
        away_name,
    )

    if score_text:

        lines.append(
            score_text
        )

    else:

        lines.append(
            f"{home_name} 🆚 {away_name}"
        )

    return "\n".join(
        lines
    )

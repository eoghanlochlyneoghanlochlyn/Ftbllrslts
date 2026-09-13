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


def get_player_event_markers(
    player,
    player_events,
):
    player_id = get_player_id(player)

    if player_id is None:
        return []

    data = player_events.get(player_id)

    if not isinstance(data, dict):
        return []

    markers = []

    goals = int(
        data.get("goals", 0) or 0
    )

    penalty_goals = int(
        data.get("penalty_goals", 0) or 0
    )

    assists = int(
        data.get("assists", 0) or 0
    )

    red_cards = int(
        data.get("red_cards", 0) or 0
    )

    normal_goals = goals - penalty_goals

    if penalty_goals == 1:
        markers.append("P ⚽")

    elif penalty_goals > 1:
        markers.append(
            f"P ⚽×{penalty_goals}"
        )

    if normal_goals == 1:
        markers.append("⚽")

    elif normal_goals > 1:
        markers.append(
            f"×{normal_goals} ⚽"
        )

    if assists == 1:
        markers.append("👟")

    elif assists > 1:
        markers.append(
            f"×{assists} 👟"
        )

    if red_cards == 1:
        markers.append("❌")

    elif red_cards > 1:
        markers.append(
            f"×{red_cards} ❌"
        )

    return markers


def format_player(
    player,
    show_rating,
    player_events=None,
):
    name = get_player_name(player)

    if not name:
        return ""

    result = name

    if show_rating:

        rating = get_player_rating(player)

        if rating is not None:
            result += f" {rating:.1f}"

    if player_events is not None:

        markers = get_player_event_markers(
            player,
            player_events,
        )

        if markers:

            result += (
                " ("
                + " ".join(markers)
                + ")"
            )

    return result


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
            names.append(name)

    if not names:
        return ""

    return (
        f"{icon} "
        + " | ".join(names)
    )


def format_team_lineup(
    team_name,
    team,
    show_rating,
    team_icon,
    player_events=None,
):
    if not isinstance(team, dict):

        return (
            f"{team_icon} {team_name}\n"
            "اطلاعات ترکیب پیدا نشد."
        )

    starters = get_starters(team)
    substitutes = get_substitutes(team)
    coach = get_coach(team)
    formation = get_formation(team)

    groups = organize_players(
        starters,
        formation,
    )

    lines = [
        f"{team_icon} {team_name}"
    ]

    if coach:
        lines.append(f"👔 {coach}")

    if formation:
        lines.append(f"📐 {formation}")

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
            substitute_names.append(name)

    if substitute_names:

        lines.append(
            "🔄 "
            + " | ".join(substitute_names)
        )

    return "\n".join(lines)


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
            + " | ".join(home_scorers)
        )

    if away_scorers:
        lines.append(
            f"⚽ {away_name}: "
            + " | ".join(away_scorers)
        )

    return lines


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
        snapshot.get("start_formatted")
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
        f"⚽️ {home_name} 🆚 {away_name}",
        f"🕐 {kickoff} به وقت ایران",
    ]

    if show_rating:

        scorer_lines = format_scorers(
            home_name,
            away_name,
            home_scorers or [],
            away_scorers or [],
        )

        if scorer_lines:
            message.append("")
            message.extend(scorer_lines)

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

    return "\n".join(message)


def build_event_message(
    snapshot,
    event,
):
    home_name = snapshot.get(
        "home",
        "Home",
    )

    away_name = snapshot.get(
        "away",
        "Away",
    )

    event_type = str(
        event.get("type", "")
    ).lower()

    player = event.get("player")

    player_name = ""

    if isinstance(player, dict):
        player_name = (
            player.get("name")
            or ""
        )

    if not player_name:
        player_name = (
            event.get("playerName")
            or ""
        )

    if event_type == "goal":

        if event.get("ownGoal") is True:
            title = "گل به خودی"
        else:
            title = "گل"

        return (
            f"⚽ {title}\n"
            f"{player_name}\n"
            f"{home_name} 🆚 {away_name}"
        )

    if event_type == "card":

        card = str(
            event.get("card", "")
        ).lower()

        if card in (
            "red",
            "redcard",
            "red_card",
        ):

            return (
                f"🟥 کارت قرمز\n"
                f"{player_name}\n"
                f"{home_name} 🆚 {away_name}"
            )

    return ""

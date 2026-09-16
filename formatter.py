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
is_own_goal,
is_penalty_goal,
)

from team_translations import (
get_persian_team_name,
)

# --------------------------------------------------------

# نام فارسی تیم

# --------------------------------------------------------

def get_display_team_name(
snapshot,
side,
):
if not isinstance(
snapshot,
dict,
):
return ""

```
if side == "home":

    team_id = snapshot.get(
        "home_team_id"
    )

    translated_name = (
        snapshot.get("home_fa")
        or ""
    )

    team_name = (
        snapshot.get("home")
        or ""
    )

    team_data = snapshot.get(
        "home_team"
    )

elif side == "away":

    team_id = snapshot.get(
        "away_team_id"
    )

    translated_name = (
        snapshot.get("away_fa")
        or ""
    )

    team_name = (
        snapshot.get("away")
        or ""
    )

    team_data = snapshot.get(
        "away_team"
    )

else:

    return ""

# ----------------------------------------------------
# استخراج اطلاعات از home_team / away_team
# ----------------------------------------------------

if isinstance(
    team_data,
    dict,
):

    if team_id is None:

        team_id = (
            team_data.get("id")
            or team_data.get("teamId")
            or team_data.get("team_id")
        )

    if not translated_name:

        translated_name = (
            team_data.get("persian")
            or team_data.get("persian_name")
            or team_data.get("name_fa")
            or team_data.get("persianName")
            or ""
        )

    if not team_name:

        team_name = (
            team_data.get("name")
            or team_data.get("shortName")
            or team_data.get("displayName")
            or ""
        )

# ----------------------------------------------------
# DEBUG
# ----------------------------------------------------

print(
    "\n========== FORMATTER TEAM DEBUG =========="
)

print(
    f"side: {side}"
)

print(
    f"team_id: {team_id}"
)

print(
    f"translated_name: {translated_name}"
)

print(
    f"team_name: {team_name}"
)

print(
    f"team_data_type: {type(team_data).__name__}"
)

print(
    "==========================================\n"
)

# ----------------------------------------------------
# اولویت اول:
# ترجمه‌ای که خود snapshot دارد
# ----------------------------------------------------

if translated_name:

    return translated_name

# ----------------------------------------------------
# اولویت دوم:
# ترجمه بر اساس ID از teams.json
# ----------------------------------------------------

if team_id is not None:

    translated_name = (
        get_persian_team_name(
            team_id,
            "",
        )
    )

    if translated_name:

        return translated_name

# ----------------------------------------------------
# آخرین fallback:
# نام خام تیم
# ----------------------------------------------------

return team_name
```

# --------------------------------------------------------

# ابزارهای نتیجه

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

```
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
```

def has_valid_score(score):
if not isinstance(
score,
dict,
):
return False

```
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
```

# --------------------------------------------------------

# نشان‌های رویداد بازیکن

# --------------------------------------------------------

def _empty_player_event_data():
return {
"goals": 0,
"assists": 0,
"own_goals": 0,
"penalty_goals": 0,
}

def build_final_player_events(
events
):
result = {}

```
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

    event_type = str(
        event.get(
            "type",
            "",
        )
    ).lower()

    if event_type != "goal":
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

return result
```

def get_player_event_markers(
player,
player_events,
):
player_id = get_player_id(
player
)

```
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

return markers
```

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

```
if not name:
    return ""

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
```

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

```
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
```

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

```
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
```

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

```
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
```

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

```
if not home_name:

    home_name = "Home"

away_name = get_display_team_name(
    snapshot,
    "away",
)

if not away_name:

    away_name = "Away"

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
```

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

```
if not home_name:

    home_name = "Home"

away_name = get_display_team_name(
    snapshot,
    "away",
)

if not away_name:

    away_name = "Away"

return (
    "🔴 بازی شروع شد\n"
    "\n"
    f"{home_name} 🆚 {away_name}"
)
```

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

```
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
```

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

```
if not home_name:

    home_name = "Home"

away_name = get_display_team_name(
    snapshot,
    "away",
)

if not away_name:

    away_name = "Away"

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
```

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

```
if not home_name:

    home_name = "Home"

away_name = get_display_team_name(
    snapshot,
    "away",
)

if not away_name:

    away_name = "Away"

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
```

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

```
if not home_name:

    home_name = "Home"

away_name = get_display_team_name(
    snapshot,
    "away",
)

if not away_name:

    away_name = "Away"

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
```

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

```
if not home_name:

    home_name = "Home"

away_name = get_display_team_name(
    snapshot,
    "away",
)

if not away_name:

    away_name = "Away"

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
```

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

```
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
```

# --------------------------------------------------------

# نمایش مقدار آمار

# --------------------------------------------------------

def format_stat_value(
label,
value,
):
if value is None:
return ""

```
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

    return f"{value:.2f}".rstrip(
        "0"
    ).rstrip(
        "."
    )

return str(
    value
)
```

# --------------------------------------------------------

# پیام نهایی ترکیب + امتیاز

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

```
message = build_lineup_message(
    snapshot,
    player_events=player_events,
    show_rating=True,
    show_final_score=True,
)

return message
```

# --------------------------------------------------------

# پیام نهایی آمار

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
"شوت در چارچوب": "🎯",
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

def build_final_stats_message(
snapshot,
score=None,
):
home_name = get_display_team_name(
snapshot,
"home",
)

```
if not home_name:

    home_name = "Home"

away_name = get_display_team_name(
    snapshot,
    "away",
)

if not away_name:

    away_name = "Away"

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

available_stats = []

for label in FINAL_STAT_ORDER:

    data = stats.get(
        label
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

    available_stats.append(
        (
            label,
            home_value,
            away_value,
        )
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
        for label, _, _ in available_stats
    )
    \+ 2,
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
```

# --------------------------------------------------------

# سازگاری با کدهای قبلی

# --------------------------------------------------------

def build_final_message(
snapshot,
score=None,
):
return build_final_stats_message(
snapshot,
score,
)

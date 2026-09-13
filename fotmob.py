import json
import re
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

import requests


IRAN_TIMEZONE = ZoneInfo("Asia/Tehran")

FOTMOB_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 "
        "(KHTML, like Gecko) "
        "Chrome/131.0.0.0 Safari/537.36"
    )
}


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
# دریافت صفحه فوت‌موب
# --------------------------------------------------------

def fetch_match_page(match_id):
    match_id = str(match_id)

    url = f"https://www.fotmob.com/match/{match_id}"

    response = requests.get(
        url,
        headers=FOTMOB_HEADERS,
        timeout=30,
    )

    print(
        f"FotMob {match_id}: HTTP {response.status_code}"
    )

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

    return json.loads(match.group(1))


# --------------------------------------------------------
# دریافت JSON بازی
# --------------------------------------------------------

def fetch_match_data(match_id):
    html = fetch_match_page(match_id)

    root = extract_next_data(html)

    return root


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

            for index, child in enumerate(value):

                walk(
                    child,
                    f"{path}[{index}]",
                )

    walk(data)

    return results


def find_section(root, names):
    results = recursive_find(
        root,
        set(names),
    )

    if not results:
        return None

    for path, value in results:

        if (
            "pageProps.content" in path
            and isinstance(value, (dict, list))
        ):
            return value

    return results[0][1]


# --------------------------------------------------------
# content اصلی
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
# نام تیم
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

    for side in ("home", "away"):

        if info[side]:
            continue

        for key in (
            f"{side}Team",
            side,
        ):

            value = content.get(key)

            if isinstance(value, dict):

                name = get_team_name(value)

                if name:
                    info[side] = name
                    break

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
                info["league"] = clean_text(name)
                break

        elif isinstance(value, str):

            if value.strip():
                info["league"] = value.strip()
                break

    if not info["league"]:

        results = recursive_find(
            content,
            {
                "leagueName",
                "competitionName",
                "tournamentName",
            },
        )

        for _, value in results:

            if isinstance(value, str):

                value = value.strip()

                if value:
                    info["league"] = value
                    break

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
                info["venue"] = clean_text(name)
                break

        elif isinstance(value, str):

            if value.strip():
                info["venue"] = value.strip()
                break

    return info


# --------------------------------------------------------
# زمان شروع بازی
# --------------------------------------------------------

def get_match_start(root, content=None):
    event_jsonld = get_nested(
        root,
        "props",
        "pageProps",
        "seo",
        "eventJSONLD",
    )

    if isinstance(event_jsonld, dict):

        value = event_jsonld.get("startDate")

        if value:
            return value

    if content is None:
        content = get_content(root)

    if isinstance(content, dict):

        status = content.get("status")

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
# تبدیل زمان به وقت ایران
# --------------------------------------------------------

def parse_datetime(value):
    if not value:
        return None

    try:
        value = str(value)

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

    if dt is None:
        return "نامشخص"

    return dt.astimezone(
        IRAN_TIMEZONE
    ).strftime("%H:%M")


# --------------------------------------------------------
# وضعیت بازی
# --------------------------------------------------------

def get_match_status(root):
    status = get_nested(
        root,
        "props",
        "pageProps",
        "header",
        "status",
    )

    if isinstance(status, dict):
        return status

    return {}


def _status_value(status, keys):
    if not isinstance(status, dict):
        return None

    for key in keys:

        value = status.get(key)

        if value is not None:
            return value

    return None


def is_match_started(root):
    """
    تشخیص شروع بازی.

    اولویت با فیلدهای صریح FotMob است.
    در صورت نبودن آنها، از reason/status نیز استفاده می‌شود.
    """

    general = get_nested(
        root,
        "props",
        "pageProps",
        "general",
    )

    if isinstance(general, dict):

        for key in (
            "started",
            "isStarted",
        ):

            if general.get(key) is True:
                return True

    status = get_match_status(root)

    for key in (
        "started",
        "isStarted",
        "inProgress",
        "live",
    ):

        if status.get(key) is True:
            return True

    reason = status.get("reason")

    if isinstance(reason, dict):

        short = clean_text(
            reason.get("short")
        ).lower()

        long = clean_text(
            reason.get("long")
        ).lower()

        key = clean_text(
            reason.get("key")
        ).lower()

        if short in {
            "1h",
            "2h",
            "ht",
            "et",
            "aet",
            "live",
            "in progress",
            "ft",
            "pen",
        }:
            return True

        if key in {
            "live",
            "in_progress",
            "match_started",
            "halftime",
            "full_time",
        }:
            return True

        if (
            "half" in long
            or "live" in long
            or "in progress" in long
            or "full-time" in long
        ):
            return True

    return False


def is_half_time(root):
    status = get_match_status(root)

    for key in (
        "halfTime",
        "half_time",
        "isHalfTime",
    ):

        if status.get(key) is True:
            return True

    reason = status.get("reason")

    if isinstance(reason, dict):

        values = [
            reason.get("short"),
            reason.get("long"),
            reason.get("key"),
        ]

        for value in values:

            value = clean_text(
                value
            ).lower()

            if value in {
                "ht",
                "half time",
                "halftime",
            }:
                return True

            if (
                "half time" in value
                or "halftime" in value
            ):
                return True

    return False


# --------------------------------------------------------
# وضعیت پایان بازی
# --------------------------------------------------------

def is_match_finished(root):
    general = get_nested(
        root,
        "props",
        "pageProps",
        "general",
    )

    if isinstance(general, dict):

        if general.get("finished") is True:
            return True

        if general.get("isFinished") is True:
            return True

    status = get_match_status(root)

    if isinstance(status, dict):

        if status.get("finished") is True:
            return True

        if status.get("isFinished") is True:
            return True

        reason = status.get("reason")

        if isinstance(reason, dict):

            short = str(
                reason.get("short", "")
            ).strip().lower()

            long = str(
                reason.get("long", "")
            ).strip().lower()

            key = str(
                reason.get("key", "")
            ).strip().lower()

            if short in (
                "ft",
                "aet",
                "pen",
            ):
                return True

            if key in (
                "full_time",
                "finished",
                "match_finished",
            ):
                return True

            if "full-time" in long:
                return True

    return False


# --------------------------------------------------------
# Lineup
# --------------------------------------------------------

def get_lineup(content, root):
    lineup = content.get("lineup")

    if isinstance(lineup, dict):
        return lineup

    lineup = find_section(
        root,
        ["lineup"],
    )

    if isinstance(lineup, dict):
        return lineup

    return None


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

    for key in aliases.get(side, ()):

        team = lineup.get(key)

        if isinstance(team, dict):
            return team

    teams = lineup.get("teams")

    if isinstance(teams, dict):

        for key in aliases.get(side, ()):

            team = teams.get(key)

            if isinstance(team, dict):
                return team

    wanted_name = (
        "home"
        if side == "home"
        else "away"
    )

    for key, value in lineup.items():

        if not isinstance(value, dict):
            continue

        if wanted_name in str(key).lower():
            return value

    return None


# --------------------------------------------------------
# بازیکنان
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

    nested_player = player.get("player")

    if isinstance(nested_player, dict):

        for key in (
            "isStarter",
            "starter",
            "starting",
            "isStarting",
            "isStartingXI",
        ):

            value = nested_player.get(key)

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

    players = find_player_list(team)

    if players:

        starters = [
            player
            for player in players
            if is_player_starter(player)
        ]

        if starters:
            return starters

    return []


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

    players = find_player_list(team)

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
# اطلاعات بازیکن
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

    nested_player = player.get("player")

    if isinstance(nested_player, dict):

        for key in (
            "name",
            "playerName",
            "longName",
            "shortName",
        ):

            value = nested_player.get(key)

            if value:
                return str(value).strip()

    return ""


def get_player_id(player):
    if not isinstance(player, dict):
        return None

    for key in (
        "id",
        "playerId",
        "playerID",
    ):

        value = player.get(key)

        if value is not None:

            try:
                return int(value)

            except (TypeError, ValueError):
                return str(value)

    nested_player = player.get("player")

    if isinstance(nested_player, dict):

        for key in (
            "id",
            "playerId",
            "playerID",
        ):

            value = nested_player.get(key)

            if value is not None:

                try:
                    return int(value)

                except (TypeError, ValueError):
                    return str(value)

    return None


def get_player_rating(player):
    if not isinstance(player, dict):
        return None

    performance = player.get("performance")

    if isinstance(performance, dict):

        rating = performance.get("rating")

        if rating is not None:

            try:
                return float(rating)

            except (TypeError, ValueError):
                pass

    candidates = [
        player.get("rating"),
        player.get("ratingScore"),
        player.get("matchRating"),
    ]

    nested_player = player.get("player")

    if isinstance(nested_player, dict):

        performance = nested_player.get("performance")

        if isinstance(performance, dict):

            rating = performance.get("rating")

            if rating is not None:

                try:
                    return float(rating)

                except (TypeError, ValueError):
                    pass

        candidates.extend(
            [
                nested_player.get("rating"),
                nested_player.get("ratingScore"),
                nested_player.get("matchRating"),
            ]
        )

    for value in candidates:

        if value is None:
            continue

        try:
            return float(value)

        except (TypeError, ValueError):
            pass

    return None


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

            except (TypeError, ValueError):
                pass

    nested_player = player.get("player")

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

                except (TypeError, ValueError):
                    pass

    return None


# --------------------------------------------------------
# Formation
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

                name = clean_text(name)

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

                name = clean_text(name)

                if re.fullmatch(
                    r"\d+(?:-\d+)+",
                    name,
                ):
                    return name

    return ""


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
# Layout و گروه‌بندی بازیکنان
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

            except (TypeError, ValueError):
                horizontal = None

            try:
                if vertical is not None:
                    vertical = float(vertical)

            except (TypeError, ValueError):
                vertical = None

            return horizontal, vertical

    return None, None


def numeric_layout_value(value):
    if value is None:
        return None

    try:
        return float(value)

    except (TypeError, ValueError):
        return None


def position_group(player):
    position_id = get_player_position_id(player)

    if position_id is None:
        return "unknown"

    if position_id == 11:
        return "goalkeeper"

    if position_id in {
        32, 33, 34, 35, 36, 37, 38,
    }:
        return "defender"

    if position_id in {
        51, 59, 62, 64, 65, 66, 68,
        71, 72, 73, 74, 75, 76, 77, 79,
    }:
        return "midfielder"

    if position_id in {
        78, 82, 83, 84, 85, 86, 87, 88,
        103, 107,
    }:
        return "wide_attacker"

    if position_id in {
        104, 105, 106, 115,
    }:
        return "attacker"

    return "unknown"


def parse_formation(formation):
    if not formation:
        return None

    parts = formation.split("-")
    numbers = []

    for part in parts:

        try:
            number = int(part)

        except (TypeError, ValueError):
            return None

        if number <= 0:
            return None

        numbers.append(number)

    if len(numbers) < 2:
        return None

    if sum(numbers) != 10:
        return None

    return {
        "defenders": numbers[0],
        "midfielders": sum(numbers[1:-1]),
        "attackers": numbers[-1],
        "lines": numbers,
    }


def get_depth(player):
    _, vertical = get_player_layout(player)

    return numeric_layout_value(vertical)


def sort_line_players(players):
    if not players:
        return []

    decorated = []
    has_horizontal = False

    for index, player in enumerate(players):

        horizontal, _ = get_player_layout(player)

        horizontal = numeric_layout_value(horizontal)

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


def get_base_player_role(player):
    return position_group(player)


def organize_players(starters, formation):
    groups = {
        "goalkeeper": [],
        "defender": [],
        "midfielder": [],
        "attacker": [],
        "unknown": [],
    }

    if not starters:
        return groups

    formation_info = parse_formation(formation)

    if not formation_info:

        for player in starters:

            role = get_base_player_role(player)

            if role == "goalkeeper":
                groups["goalkeeper"].append(player)

            elif role == "defender":
                groups["defender"].append(player)

            elif role == "midfielder":
                groups["midfielder"].append(player)

            elif role in (
                "wide_attacker",
                "attacker",
            ):
                groups["attacker"].append(player)

            else:
                groups["unknown"].append(player)

        return groups

    goalkeeper = None

    for player in starters:

        if get_base_player_role(player) == "goalkeeper":
            goalkeeper = player
            break

    if goalkeeper is not None:
        groups["goalkeeper"].append(goalkeeper)

    remaining = [
        player
        for player in starters
        if player is not goalkeeper
    ]

    defender_count = formation_info["defenders"]
    midfielder_count = formation_info["midfielders"]
    attacker_count = formation_info["attackers"]

    defenders = [
        player
        for player in remaining
        if get_base_player_role(player) == "defender"
    ]

    if len(defenders) > defender_count:

        with_depth = [
            (player, get_depth(player))
            for player in defenders
        ]

        usable = [
            item
            for item in with_depth
            if item[1] is not None
        ]

        if usable:

            usable.sort(key=lambda item: item[1])

            defenders = [
                item[0]
                for item in usable[:defender_count]
            ]

        else:
            defenders = defenders[:defender_count]

    if len(defenders) < defender_count:

        candidates = [
            player
            for player in remaining
            if (
                player not in defenders
                and get_base_player_role(player)
                == "unknown"
            )
        ]

        needed = defender_count - len(defenders)

        defenders.extend(candidates[:needed])

    for player in defenders:

        if player in remaining:
            remaining.remove(player)

    groups["defender"] = defenders

    pure_attackers = [
        player
        for player in remaining
        if get_base_player_role(player) == "attacker"
    ]

    attackers = pure_attackers[:attacker_count]

    for player in attackers:

        if player in remaining:
            remaining.remove(player)

    fixed_midfielders = [
        player
        for player in remaining
        if get_base_player_role(player) == "midfielder"
    ]

    wide_players = [
        player
        for player in remaining
        if get_base_player_role(player) == "wide_attacker"
    ]

    unknown_players = [
        player
        for player in remaining
        if get_base_player_role(player) == "unknown"
    ]

    midfielders = fixed_midfielders[:midfielder_count]

    for player in midfielders:

        if player in remaining:
            remaining.remove(player)

    midfield_need = midfielder_count - len(midfielders)

    if midfield_need > 0:

        wide_with_depth = [
            (player, get_depth(player))
            for player in wide_players
        ]

        if any(
            depth is not None
            for _, depth in wide_with_depth
        ):

            wide_with_depth.sort(
                key=lambda item: (
                    item[1]
                    if item[1] is not None
                    else 999999
                )
            )

            wide_players = [
                item[0]
                for item in wide_with_depth
            ]

        selected = wide_players[:midfield_need]

        midfielders.extend(selected)

        for player in selected:

            if player in remaining:
                remaining.remove(player)

            if player in wide_players:
                wide_players.remove(player)

    attacker_need = attacker_count - len(attackers)

    if attacker_need > 0:

        selected = wide_players[:attacker_need]

        attackers.extend(selected)

        for player in selected:

            if player in remaining:
                remaining.remove(player)

            if player in wide_players:
                wide_players.remove(player)

    if len(midfielders) < midfielder_count:

        needed = midfielder_count - len(midfielders)

        selected = [
            player
            for player in unknown_players
            if player in remaining
        ][:needed]

        midfielders.extend(selected)

        for player in selected:

            if player in remaining:
                remaining.remove(player)

    if len(attackers) < attacker_count:

        needed = attacker_count - len(attackers)

        selected = [
            player
            for player in unknown_players
            if player in remaining
        ][:needed]

        attackers.extend(selected)

        for player in selected:

            if player in remaining:
                remaining.remove(player)

    groups["midfielder"] = midfielders
    groups["attacker"] = attackers

    groups["unknown"] = list(remaining)

    for key in groups:
        groups[key] = sort_line_players(groups[key])

    return groups


# --------------------------------------------------------
# رویدادهای بازی
# --------------------------------------------------------

def get_match_events(root):
    events = get_nested(
        root,
        "props",
        "pageProps",
        "content",
        "matchFacts",
        "events",
        "events",
    )

    if isinstance(events, list):
        return events

    return []


def get_event_type(event):
    if not isinstance(event, dict):
        return ""

    for key in (
        "type",
        "eventType",
        "event_type",
        "incidentType",
    ):

        value = event.get(key)

        if value is not None:

            if isinstance(value, dict):

                value = first_non_empty(
                    value.get("key"),
                    value.get("name"),
                    value.get("type"),
                )

            value = clean_text(value)

            if value:
                return value.lower()

    return ""


def get_event_time(event):
    if not isinstance(event, dict):
        return None

    for key in (
        "time",
        "minute",
        "matchMinute",
        "timeElapsed",
        "elapsed",
        "minuteValue",
    ):

        value = event.get(key)

        if value is None:
            continue

        if isinstance(value, dict):

            value = first_non_empty(
                value.get("value"),
                value.get("minute"),
                value.get("time"),
            )

        try:
            return int(float(value))

        except (TypeError, ValueError):
            pass

    return None


def get_event_minute_text(event):
    """
    متن مناسب برای نمایش دقیقه رویداد.

    برای مثال:
    34
    45+2
    90+5
    """

    if not isinstance(event, dict):
        return ""

    for key in (
        "time",
        "minute",
        "matchMinute",
        "timeElapsed",
        "elapsed",
    ):

        value = event.get(key)

        if value is None:
            continue

        if isinstance(value, dict):

            value = first_non_empty(
                value.get("display"),
                value.get("text"),
                value.get("value"),
                value.get("minute"),
                value.get("time"),
            )

        value = clean_text(value)

        if not value:
            continue

        if re.fullmatch(
            r"\d+(?:\+\d+)?",
            value,
        ):
            return value

        match = re.search(
            r"(\d+(?:\+\d+)?)",
            value,
        )

        if match:
            return match.group(1)

    return ""


def get_event_unique_id(event):
    if not isinstance(event, dict):
        return None

    for key in (
        "id",
        "eventId",
        "eventID",
        "incidentId",
        "incidentID",
    ):

        value = event.get(key)

        if value is not None:

            value = clean_text(value)

            if value:
                return value

    return None


def _normalise_team_id(value):
    if value is None:
        return None

    if isinstance(value, dict):

        value = first_non_empty(
            value.get("id"),
            value.get("teamId"),
            value.get("teamID"),
        )

    try:
        return int(value)

    except (TypeError, ValueError):
        value = clean_text(value)

        return value if value else None


def get_event_team(event):
    """
    مشخص می‌کند رویداد مربوط به کدام تیم است.

    خروجی:
        {
            "id": ...,
            "name": ...,
            "is_home": True/False/None
        }

    در صورتی که اطلاعات کامل موجود نباشد،
    تا حد ممکن از فیلدهای مختلف FotMob استفاده می‌شود.
    """

    if not isinstance(event, dict):
        return {
            "id": None,
            "name": "",
            "is_home": None,
        }

    team_id = None
    team_name = ""

    for key in (
        "teamId",
        "teamID",
        "team_id",
    ):

        if event.get(key) is not None:
            team_id = _normalise_team_id(
                event.get(key)
            )
            break

    for key in (
        "team",
        "teamData",
        "teamInfo",
    ):

        value = event.get(key)

        if isinstance(value, dict):

            if team_id is None:
                team_id = _normalise_team_id(
                    value
                )

            team_name = first_non_empty(
                value.get("name"),
                value.get("longName"),
                value.get("shortName"),
            )

            if team_name:
                break

        elif isinstance(value, str):

            if value.strip():
                team_name = value.strip()
                break

    if not team_name:

        team_name = clean_text(
            first_non_empty(
                event.get("teamName"),
                event.get("teamLongName"),
                event.get("teamShortName"),
            )
        )

    is_home = None

    for key in (
        "isHome",
        "home",
        "isHomeTeam",
    ):

        value = event.get(key)

        if isinstance(value, bool):
            is_home = value
            break

    if is_home is None:

        side = clean_text(
            first_non_empty(
                event.get("side"),
                event.get("teamSide"),
            )
        ).lower()

        if side in (
            "home",
            "h",
        ):
            is_home = True

        elif side in (
            "away",
            "a",
        ):
            is_home = False

    return {
        "id": team_id,
        "name": team_name,
        "is_home": is_home,
    }


# --------------------------------------------------------
# بازیکن رویداد
# --------------------------------------------------------

def get_event_player_id(event):
    if not isinstance(event, dict):
        return None

    for key in (
        "playerId",
        "playerID",
        "player_id",
    ):

        value = event.get(key)

        if value is not None:

            try:
                return int(value)

            except (TypeError, ValueError):
                return str(value)

    player = event.get("player")

    if isinstance(player, dict):

        for key in (
            "id",
            "playerId",
            "playerID",
        ):

            value = player.get(key)

            if value is not None:

                try:
                    return int(value)

                except (TypeError, ValueError):
                    return str(value)

    return None


def get_event_assist_player_id(event):
    if not isinstance(event, dict):
        return None

    for key in (
        "assistPlayerId",
        "assistPlayerID",
        "assist_player_id",
    ):

        value = event.get(key)

        if value is not None:

            try:
                return int(value)

            except (TypeError, ValueError):
                return str(value)

    assist_player = event.get(
        "assistPlayer"
    )

    if isinstance(assist_player, dict):

        for key in (
            "id",
            "playerId",
            "playerID",
        ):

            value = assist_player.get(key)

            if value is not None:

                try:
                    return int(value)

                except (TypeError, ValueError):
                    return str(value)

    return None


# --------------------------------------------------------
# نوع گل
# --------------------------------------------------------

def is_cancelled_goal_event(event):
    if not isinstance(event, dict):
        return False

    event_type = get_event_type(event)

    decision = event.get("decision")

    decision_values = []

    if isinstance(decision, dict):

        for key in (
            "key",
            "name",
            "type",
            "decision",
            "value",
        ):

            value = decision.get(key)

            if value is not None:
                decision_values.append(
                    clean_text(value).lower()
                )

    elif decision is not None:

        decision_values.append(
            clean_text(decision).lower()
        )

    for key in (
        "decisionKey",
        "decisionType",
        "decisionName",
        "varDecision",
    ):

        value = event.get(key)

        if value is not None:
            decision_values.append(
                clean_text(value).lower()
            )

    for value in decision_values:

        if any(
            token in value
            for token in (
                "var_goal_cancelled",
                "goal_cancelled",
                "goal_canceled",
                "goal disallowed",
                "goal disallowed",
                "cancelled goal",
                "canceled goal",
            )
        ):
            return True

    if event_type in (
        "var",
        "video_assistant_referee",
    ):

        combined = " ".join(
            decision_values
        )

        if any(
            token in combined
            for token in (
                "cancel",
                "disallow",
                "no goal",
                "no_goal",
                "overturn",
            )
        ):
            return True

    return False


def is_penalty_goal(event):
    if not isinstance(event, dict):
        return False

    goal_description_key = clean_text(
        event.get("goalDescriptionKey")
    ).lower()

    goal_description = clean_text(
        event.get("goalDescription")
    ).lower()

    if "penalty" in goal_description_key:
        return True

    if "penalty" in goal_description:
        return True

    shotmap = event.get(
        "shotmapEvent"
    )

    if isinstance(shotmap, dict):

        situation = clean_text(
            shotmap.get("situation")
        ).lower()

        if situation == "penalty":
            return True

        if shotmap.get("isPenalty") is True:
            return True

    return False


def is_own_goal(event):
    if not isinstance(event, dict):
        return False

    if event.get("ownGoal") is True:
        return True

    if event.get("isOwnGoal") is True:
        return True

    shotmap = event.get(
        "shotmapEvent"
    )

    if isinstance(shotmap, dict):

        if shotmap.get("isOwnGoal") is True:
            return True

        if shotmap.get("ownGoal") is True:
            return True

    description = clean_text(
        first_non_empty(
            event.get("goalDescription"),
            event.get("description"),
        )
    ).lower()

    if (
        "own goal" in description
        or "own_goal" in description
    ):
        return True

    return False


def is_red_card_event(event):
    if not isinstance(event, dict):
        return False

    event_type = get_event_type(event)

    if event_type in (
        "red_card",
        "redcard",
        "red card",
    ):
        return True

    card = clean_text(
        first_non_empty(
            event.get("card"),
            event.get("cardType"),
            event.get("cardName"),
        )
    ).lower()

    if card in (
        "red",
        "red card",
        "redcard",
    ):
        return True

    if "red" in card:
        return True

    return False


# --------------------------------------------------------
# اطلاعات کامل گل
# --------------------------------------------------------

def get_goal_info(event):
    if not isinstance(event, dict):
        return None

    event_type = get_event_type(event)

    if event_type not in (
        "goal",
        "goals",
        "score",
        "scored",
    ):
        return None

    if is_cancelled_goal_event(event):
        return None

    player_id = get_event_player_id(event)

    assist_player_id = (
        get_event_assist_player_id(event)
    )

    team = get_event_team(event)

    return {
        "event": event,
        "event_id": get_event_unique_id(event),
        "player_id": player_id,
        "assist_player_id": assist_player_id,
        "minute": get_event_minute_text(event),
        "minute_value": get_event_time(event),
        "team_id": team.get("id"),
        "team_name": team.get("name", ""),
        "is_home": team.get("is_home"),
        "penalty": is_penalty_goal(event),
        "own_goal": is_own_goal(event),
    }


# --------------------------------------------------------
# وضعیت کلی بازی
# --------------------------------------------------------

def get_lineup_type(root):
    content = get_content(root)
    lineup = get_lineup(content, root)

    if not isinstance(lineup, dict):
        return ""

    return clean_text(
        lineup.get("lineupType")
    )


def get_match_snapshot(root):
    content = get_content(root)

    info = extract_basic_info(root)

    start = get_match_start(
        root,
        content,
    )

    lineup = get_lineup(
        content,
        root,
    )

    home_team = None
    away_team = None

    if isinstance(lineup, dict):

        home_team = get_lineup_team(
            lineup,
            "home",
        )

        away_team = get_lineup_team(
            lineup,
            "away",
        )

    home_starters = (
        get_starters(home_team)
        if home_team
        else []
    )

    away_starters = (
        get_starters(away_team)
        if away_team
        else []
    )

    events = get_match_events(root)

    return {
        "home": info["home"],
        "away": info["away"],
        "league": info["league"],
        "venue": info["venue"],
        "start": start,
        "start_formatted": format_match_time(start),

        "finished": is_match_finished(root),
        "started": is_match_started(root),
        "half_time": is_half_time(root),

        "lineup_type": get_lineup_type(root),

        "home_team": home_team,
        "away_team": away_team,

        "home_starters": home_starters,
        "away_starters": away_starters,

        "events": events,

        "status": get_match_status(root),
    }

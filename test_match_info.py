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
# نام فارسی رقابت‌ها
# --------------------------------------------------------

COMPETITION_NAMES_FA = {
    "Premier League": "لیگ برتر انگلیس",
    "English Premier League": "لیگ برتر انگلیس",
    "LaLiga": "لالیگا",
    "La Liga": "لالیگا",
    "Serie A": "سری آ ایتالیا",
    "Bundesliga": "بوندس‌لیگا",
    "Ligue 1": "لیگ یک فرانسه",
    "UEFA Champions League": "لیگ قهرمانان اروپا",
    "Champions League": "لیگ قهرمانان اروپا",
    "UEFA Europa League": "لیگ اروپا",
    "Europa League": "لیگ اروپا",
    "UEFA Conference League": "لیگ کنفرانس اروپا",
    "Conference League": "لیگ کنفرانس اروپا",
    "Belgian Pro League": "لیگ برتر بلژیک",
    "Jupiler Pro League": "لیگ برتر بلژیک",
    "Eredivisie": "اردیویسه هلند",
    "Primeira Liga": "لیگ برتر پرتغال",
    "Saudi Pro League": "لیگ حرفه‌ای عربستان",
    "MLS": "لیگ آمریکا",
    "Major League Soccer": "لیگ آمریکا",
    "FA Cup": "جام حذفی انگلیس",
    "EFL Cup": "جام اتحادیه انگلیس",
    "Carabao Cup": "جام اتحادیه انگلیس",
    "Copa del Rey": "جام حذفی اسپانیا",
    "Copa Italia": "جام حذفی ایتالیا",
    "Coppa Italia": "جام حذفی ایتالیا",
    "DFB Pokal": "جام حذفی آلمان",
    "Coupe de France": "جام حذفی فرانسه",
    "FIFA World Cup": "جام جهانی",
    "World Cup": "جام جهانی",
    "UEFA Nations League": "لیگ ملت‌های اروپا",
}


# --------------------------------------------------------
# نام فارسی باشگاه‌ها
# --------------------------------------------------------

TEAM_NAMES_FA = {
    "KV Mechelen": "مِخلن",
    "Mechelen": "مِخلن",
    "Anderlecht": "اندرلخت",

    "Liverpool": "لیورپول",
    "Liverpool FC": "لیورپول",
    "Arsenal": "آرسنال",
    "Arsenal FC": "آرسنال",
    "Manchester City": "منچسترسیتی",
    "Manchester City FC": "منچسترسیتی",
    "Manchester United": "منچستریونایتد",
    "Manchester United FC": "منچستریونایتد",
    "Chelsea": "چلسی",
    "Chelsea FC": "چلسی",
    "Tottenham Hotspur": "تاتنهام",
    "Tottenham Hotspur FC": "تاتنهام",

    "Juventus": "یوونتوس",
    "Juventus Turin": "یوونتوس",
    "AC Milan": "آث میلان",
    "AC Milan FC": "آث میلان",
    "Inter Milan": "اینتر",
    "Inter Milano": "اینتر",
    "Inter": "اینتر",

    "Bayern Munich": "بایرن مونیخ",
    "FC Bayern München": "بایرن مونیخ",
    "Borussia Dortmund": "بوروسیا دورتموند",
    "PSG": "پاری‌سن‌ژرمن",
    "Paris Saint-Germain": "پاری‌سن‌ژرمن",
    "Paris Saint-Germain FC": "پاری‌سن‌ژرمن",

    "Real Madrid": "رئال مادرید",
    "Real Madrid CF": "رئال مادرید",
    "Barcelona": "بارسلونا",
    "FC Barcelona": "بارسلونا",
    "Atletico Madrid": "اتلتیکومادرید",
    "Atlético Madrid": "اتلتیکومادرید",
    "Club Atletico de Madrid": "اتلتیکومادرید",

    "Everton": "اورتون",
    "Everton FC": "اورتون",
    "Fulham": "فولام",
    "Fulham FC": "فولام",
    "Crystal Palace": "کریستال پالاس",
    "Crystal Palace FC": "کریستال پالاس",
    "Newcastle United": "نیوکاسل",
    "Newcastle United FC": "نیوکاسل",
    "Aston Villa": "استون ویلا",
    "Aston Villa FC": "استون ویلا",
    "Nottingham Forest": "ناتینگهام فارست",
    "Nottingham Forest FC": "ناتینگهام فارست",
    "Sunderland": "ساندرلند",
    "Sunderland AFC": "ساندرلند",
    "Ipswich Town": "ایپسویچ",
    "Ipswich Town FC": "ایپسویچ",
    "Leeds United": "لیدز",
    "Leeds United FC": "لیدز",
    "Brentford": "برنتفورد",
    "Brentford FC": "برنتفورد",
    "Brighton": "برایتون",
    "Brighton & Hove Albion": "برایتون",
    "Brighton & Hove Albion FC": "برایتون",
    "Bournemouth": "بورنموث",
    "AFC Bournemouth": "بورنموث",
    "Coventry City": "کاونتری",
    "Coventry City FC": "کاونتری",
    "Hull City": "هال سیتی",
    "Hull City FC": "هال سیتی",

    "Valencia": "والنسیا",
    "Valencia CF": "والنسیا",
    "Sevilla": "سویا",
    "Sevilla FC": "سویا",
    "Real Betis": "رئال بتیس",
    "Real Betis Seville": "رئال بتیس",
    "Athletic Bilbao": "اتلتیک بیلبائو",
    "Athletic Club": "اتلتیک بیلبائو",
    "Atletico Madrid": "اتلتیکومادرید",
    "Rayo Vallecano": "رایو وایکانو",
    "Villarreal": "ویارئال",
    "Villarreal CF": "ویارئال",
    "Osasuna": "اوساسونا",
    "CA Osasuna": "اوساسونا",
    "Espanyol": "اسپانیول",
    "Espanyol Barcelona": "اسپانیول",
    "Getafe": "ختافه",
    "Getafe CF": "ختافه",
    "Real Sociedad": "رئال سوسیداد",
    "Real Sociedad San Sebastian": "رئال سوسیداد",
    "Celta Vigo": "سلتاویگو",
    "RC Celta de Vigo": "سلتاویگو",
    "Levante": "لوانته",
    "Levante UD": "لوانته",
    "Elche": "الچه",
    "Elche CF": "الچه",
    "Malaga": "مالاگا",
    "Malaga CF": "مالاگا",
    "Deportivo Alaves": "آلاوس",
    "Racing Santander": "راسينگ سانتاندر",
    "RC Deportivo de La Coruna": "دپورتیوو لاکرونیا",

    "Fiorentina": "فیورنتینا",
    "ACF Fiorentina": "فیورنتینا",
    "Torino": "تورینو",
    "Torino FC": "تورینو",
    "Napoli": "ناپولی",
    "SSC Napoli": "ناپولی",
    "Roma": "رم",
    "AS Roma": "رم",
    "Atalanta": "آتالانتا",
    "Atalanta BC": "آتالانتا",
    "Genoa": "جنوا",
    "Genoa CFC": "جنوا",
    "Como": "کومو",
    "Como 1907": "کومو",
    "Frosinone": "فروزینونه",
    "Frosinone Calcio": "فروزینونه",
    "Venezia": "ونتزیا",
    "Venezia FC": "ونتزیا",
    "Parma": "پارما",
    "Parma Calcio": "پارما",
    "Monza": "مونتزا",
    "AC Monza": "مونتزا",
    "Bologna": "بولونیا",
    "Bologna FC": "بولونیا",
    "Sassuolo": "ساسولو",
    "Sassuolo Calcio": "ساسولو",
    "Lazio": "لاتزیو",
    "Lazio Rome": "لاتزیو",
    "Udinese": "اودینزه",
    "Udinese Calcio": "اودینزه",
    "Cagliari": "کالیاری",
    "Cagliari Calcio": "کالیاری",
    "Lecce": "لچه",
    "US Lecce": "لچه",

    "Union Berlin": "اونیون برلین",
    "1. FC Union Berlin": "اونیون برلین",
    "Schalke 04": "شالکه",
    "FC Schalke 04": "شالکه",
    "Mainz 05": "ماینتس",
    "1. FSV Mainz 05": "ماینتس",
    "Hamburger SV": "هامبورگ",
    "Hamburg": "هامبورگ",

    "Rennes": "رن",
    "Stade Rennais": "رن",
    "Marseille": "مارسی",
    "Olympique Marseille": "مارسی",
}


# --------------------------------------------------------
# تبدیل نام رقابت به فارسی
# --------------------------------------------------------

def translate_competition_name(name):
    name = clean_text(name)

    if not name:
        return "نامشخص"

    if name in COMPETITION_NAMES_FA:
        return COMPETITION_NAMES_FA[name]

    normalized = name.lower().strip()

    for original, translated in COMPETITION_NAMES_FA.items():

        if normalized == original.lower():
            return translated

    return name


# --------------------------------------------------------
# تبدیل نام باشگاه به فارسی
# --------------------------------------------------------

def translate_team_name(name):
    name = clean_text(name)

    if not name:
        return ""

    if name in TEAM_NAMES_FA:
        return TEAM_NAMES_FA[name]

    normalized = name.lower().strip()

    for original, translated in TEAM_NAMES_FA.items():

        if normalized == original.lower():
            return translated

    return name


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

            value = (
                value[:-1]
                + "+00:00"
            )

        dt = datetime.fromisoformat(
            value
        )

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

    status = get_nested(
        root,
        "props",
        "pageProps",
        "header",
        "status",
    )

    if isinstance(status, dict):

        if status.get("finished") is True:
            return True

        reason = status.get(
            "reason"
        )

        if isinstance(reason, dict):

            short = str(
                reason.get(
                    "short",
                    "",
                )
            ).strip().lower()

            long = str(
                reason.get(
                    "long",
                    "",
                )
            ).strip().lower()

            if short in (
                "ft",
                "aet",
                "pen",
            ):

                return True

            if "full-time" in long:
                return True

    return False


# --------------------------------------------------------
# استخراج نتیجه بازی
# --------------------------------------------------------

def get_match_score(root, content):

    candidates = []

    status = get_nested(
        root,
        "props",
        "pageProps",
        "header",
        "status",
    )

    if isinstance(status, dict):

        candidates.extend(
            [
                status.get("scoreStr"),
                status.get("score"),
            ]
        )

    general = get_nested(
        root,
        "props",
        "pageProps",
        "general",
    )

    if isinstance(general, dict):

        candidates.extend(
            [
                general.get("scoreStr"),
                general.get("score"),
            ]
        )

    content_status = (
        content.get("status")
        if isinstance(content, dict)
        else None
    )

    if isinstance(content_status, dict):

        candidates.extend(
            [
                content_status.get("scoreStr"),
                content_status.get("score"),
            ]
        )

    if isinstance(content, dict):

        candidates.extend(
            [
                content.get("scoreStr"),
                content.get("score"),
            ]
        )

    for candidate in candidates:

        if candidate is None:
            continue

        if isinstance(candidate, str):

            match = re.search(
                r"(\d+)\s*[-:]\s*(\d+)",
                candidate,
            )

            if match:

                try:

                    return {
                        "home": int(
                            match.group(1)
                        ),
                        "away": int(
                            match.group(2)
                        ),
                    }

                except (
                    TypeError,
                    ValueError,
                ):
                    pass

        if isinstance(candidate, dict):

            home_value = first_non_empty(
                candidate.get("home"),
                candidate.get("homeScore"),
                candidate.get("homeGoals"),
            )

            away_value = first_non_empty(
                candidate.get("away"),
                candidate.get("awayScore"),
                candidate.get("awayGoals"),
            )

            if (
                home_value != ""
                and away_value != ""
            ):

                try:

                    return {
                        "home": int(
                            home_value
                        ),
                        "away": int(
                            away_value
                        ),
                    }

                except (
                    TypeError,
                    ValueError,
                ):
                    pass

    events = get_match_events(
        root
    )

    home_goals = 0
    away_goals = 0

    for event in events:

        if not isinstance(event, dict):
            continue

        event_type = clean_text(
            event.get("type")
        ).lower()

        if event_type != "goal":
            continue

        if event.get(
            "isPenaltyShootoutEvent"
        ) is True:
            continue

        if is_cancelled_goal_event(
            event
        ):
            continue

        is_home = event.get(
            "isHome"
        )

        own_goal = is_own_goal(
            event
        )

        if own_goal:

            if is_home is True:
                away_goals += 1

            elif is_home is False:
                home_goals += 1

        else:

            if is_home is True:
                home_goals += 1

            elif is_home is False:
                away_goals += 1

    if home_goals or away_goals:

        return {
            "home": home_goals,
            "away": away_goals,
        }

    return None


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
        "home"
        if side == "home"
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

    if isinstance(
        nested_player,
        dict,
    ):

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

    if isinstance(
        nested_player,
        dict,
    ):

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
# شناسه بازیکن
# --------------------------------------------------------

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

            except (
                TypeError,
                ValueError,
            ):

                return str(value)

    nested_player = player.get(
        "player"
    )

    if isinstance(
        nested_player,
        dict,
    ):

        for key in (
            "id",
            "playerId",
            "playerID",
        ):

            value = nested_player.get(
                key
            )

            if value is not None:

                try:

                    return int(value)

                except (
                    TypeError,
                    ValueError,
                ):

                    return str(value)

    return None


# --------------------------------------------------------
# Rating
# --------------------------------------------------------

def get_player_rating(player):

    if not isinstance(player, dict):
        return None

    performance = player.get(
        "performance"
    )

    if isinstance(performance, dict):

        rating = performance.get(
            "rating"
        )

        if rating is not None:

            try:
                return float(rating)

            except (
                TypeError,
                ValueError,
            ):
                pass

    candidates = [
        player.get("rating"),
        player.get("ratingScore"),
        player.get("matchRating"),
    ]

    nested_player = player.get(
        "player"
    )

    if isinstance(
        nested_player,
        dict,
    ):

        performance = nested_player.get(
            "performance"
        )

        if isinstance(
            performance,
            dict,
        ):

            rating = performance.get(
                "rating"
            )

            if rating is not None:

                try:

                    return float(
                        rating
                    )

                except (
                    TypeError,
                    ValueError,
                ):
                    pass

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

    if isinstance(
        nested_player,
        dict,
    ):

        for key in (
            "positionId",
            "positionID",
            "position_id",
        ):

            value = nested_player.get(
                key
            )

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
# --------------------------------------------------------

def position_group(player):

    position_id = get_player_position_id(
        player
    )

    if position_id is None:
        return "unknown"

    if position_id == 11:
        return "goalkeeper"

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

                horizontal = source.get(
                    key
                )

                break

        for key in (
            "verticalLayout",
            "vertical",
            "y",
        ):

            if source.get(key) is not None:

                vertical = source.get(
                    key
                )

                break

        if (
            horizontal is not None
            or vertical is not None
        ):

            try:

                if horizontal is not None:

                    horizontal = float(
                        horizontal
                    )

            except (
                TypeError,
                ValueError,
            ):

                horizontal = None

            try:

                if vertical is not None:

                    vertical = float(
                        vertical
                    )

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
# نقش پایه بازیکن
# --------------------------------------------------------

def get_base_player_role(player):

    return position_group(
        player
    )


# --------------------------------------------------------
# اولویت نقش
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
# --------------------------------------------------------

def get_depth(player):

    _, vertical = get_player_layout(
        player
    )

    return numeric_layout_value(
        vertical
    )


# --------------------------------------------------------
# مرتب کردن بازیکنان یک خط
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

    defender_count = (
        formation_info["defenders"]
    )

    midfielder_count = (
        formation_info["midfielders"]
    )

    attacker_count = (
        formation_info["attackers"]
    )

    defenders = [
        player
        for player in remaining
        if get_base_player_role(
            player
        ) == "defender"
    ]

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

    pure_attackers = [
        player
        for player in remaining
        if get_base_player_role(
            player
        ) == "attacker"
    ]

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

    midfielders = fixed_midfielders[
        :midfielder_count
    ]

    for player in midfielders:

        if player in remaining:

            remaining.remove(
                player
            )

    midfield_need = (
        midfielder_count
        - len(midfielders)
    )

    if midfield_need > 0:

        wide_sorted = list(
            wide_players
        )

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

    attacker_need = (
        attacker_count
        - len(attackers)
    )

    if attacker_need > 0:

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

    groups["midfielder"] = midfielders
    groups["attacker"] = attackers

    groups["unknown"] = [
        player
        for player in remaining
    ]

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


# --------------------------------------------------------
# تشخیص گل مردودشده توسط VAR
# --------------------------------------------------------

def is_cancelled_goal_event(event):

    if not isinstance(event, dict):
        return False

    event_type = clean_text(
        event.get("type")
    ).lower()

    if event_type != "var":
        return False

    decision = event.get(
        "decision"
    )

    if not isinstance(decision, dict):
        return False

    keys = decision.get(
        "key"
    )

    if isinstance(keys, list):

        for key in keys:

            key = clean_text(
                key
            ).lower()

            if key == "var_goal_cancelled":
                return True

    elif isinstance(keys, str):

        if (
            "var_goal_cancelled"
            in keys.lower()
        ):

            return True

    return False


# --------------------------------------------------------
# تشخیص گل پنالتی موفق
# --------------------------------------------------------

def is_penalty_goal(event):

    if not isinstance(event, dict):
        return False

    goal_description_key = clean_text(
        event.get(
            "goalDescriptionKey"
        )
    ).lower()

    if goal_description_key == "penalty":
        return True

    goal_description = clean_text(
        event.get(
            "goalDescription"
        )
    ).lower()

    if goal_description == "penalty":
        return True

    shotmap_event = event.get(
        "shotmapEvent"
    )

    if isinstance(
        shotmap_event,
        dict,
    ):

        situation = clean_text(
            shotmap_event.get(
                "situation"
            )
        ).lower()

        if situation == "penalty":
            return True

    return False


# --------------------------------------------------------
# تشخیص گل به خودی
# --------------------------------------------------------

def is_own_goal(event):

    if not isinstance(event, dict):
        return False

    if event.get(
        "ownGoal"
    ) is True:

        return True

    shotmap_event = event.get(
        "shotmapEvent"
    )

    if isinstance(
        shotmap_event,
        dict,
    ):

        if shotmap_event.get(
            "isOwnGoal"
        ) is True:

            return True

    return False


# --------------------------------------------------------
# تشخیص کارت قرمز بازیکن
# --------------------------------------------------------

def is_red_card_event(event):

    if not isinstance(event, dict):
        return False

    event_type = clean_text(
        event.get("type")
    ).lower()

    if event_type != "card":
        return False

    card = clean_text(
        event.get("card")
    ).lower()

    if card not in (
        "red",
        "redcard",
        "red_card",
    ):

        return False

    card_description = event.get(
        "cardDescription"
    )

    if isinstance(
        card_description,
        dict,
    ):

        localized_key = clean_text(
            card_description.get(
                "localizedKey"
            )
        ).lower()

        default_text = clean_text(
            card_description.get(
                "defaultText"
            )
        ).lower()

        if localized_key == "coach":
            return False

        if default_text == "coach":
            return False

    return True


# --------------------------------------------------------
# پیدا کردن شناسه بازیکن از رویداد
# --------------------------------------------------------

def get_event_player_id(event):

    if not isinstance(event, dict):
        return None

    value = event.get(
        "playerId"
    )

    if value is not None:

        try:

            return int(value)

        except (
            TypeError,
            ValueError,
        ):

            return str(value)

    player = event.get(
        "player"
    )

    if isinstance(
        player,
        dict,
    ):

        value = player.get(
            "id"
        )

        if value is not None:

            try:

                return int(value)

            except (
                TypeError,
                ValueError,
            ):

                return str(value)

    return None


# --------------------------------------------------------
# پیدا کردن شناسه پاس‌دهنده
# --------------------------------------------------------

def get_event_assist_player_id(event):

    if not isinstance(event, dict):
        return None

    value = event.get(
        "assistPlayerId"
    )

    if value is not None:

        try:

            return int(value)

        except (
            TypeError,
            ValueError,
        ):

            return str(value)

    return None


# --------------------------------------------------------
# اطلاعات رویدادهای بازیکنان
# --------------------------------------------------------

def extract_player_events(root):

    events = get_match_events(
        root
    )

    player_events = {}

    def ensure_player(player_id):

        if player_id is None:
            return None

        if player_id not in player_events:

            player_events[player_id] = {
                "goals": 0,
                "penalty_goals": 0,
                "assists": 0,
                "red_cards": 0,
                "own_goals": 0,
            }

        return player_events[player_id]

    cancelled_goal_player_ids = set()

    for event in events:

        if not isinstance(event, dict):
            continue

        if not is_cancelled_goal_event(
            event
        ):
            continue

        player_id = get_event_player_id(
            event
        )

        if player_id is not None:

            cancelled_goal_player_ids.add(
                player_id
            )

    for event in events:

        if not isinstance(event, dict):
            continue

        event_type = clean_text(
            event.get("type")
        ).lower()

        if event_type == "goal":

            player_id = get_event_player_id(
                event
            )

            if player_id is None:
                continue

            if event.get(
                "isPenaltyShootoutEvent"
            ) is True:

                continue

            if player_id in cancelled_goal_player_ids:

                continue

            data = ensure_player(
                player_id
            )

            if is_own_goal(event):

                data["own_goals"] += 1

            else:

                data["goals"] += 1

                if is_penalty_goal(event):

                    data["penalty_goals"] += 1

            assist_player_id = (
                get_event_assist_player_id(
                    event
                )
            )

            if assist_player_id is not None:

                assist_data = ensure_player(
                    assist_player_id
                )

                assist_data["assists"] += 1

        elif event_type == "card":

            if not is_red_card_event(
                event
            ):
                continue

            player_id = get_event_player_id(
                event
            )

            if player_id is None:
                continue

            data = ensure_player(
                player_id
            )

            data["red_cards"] += 1

    return player_events


# --------------------------------------------------------
# استخراج گلزنان هر تیم
# --------------------------------------------------------

def extract_scorers(
    root,
    home_players,
    away_players,
):

    events = get_match_events(
        root
    )

    home_ids = {
        get_player_id(player)
        for player in home_players
        if get_player_id(player) is not None
    }

    away_ids = {
        get_player_id(player)
        for player in away_players
        if get_player_id(player) is not None
    }

    home_scorers = []
    away_scorers = []

    cancelled_player_ids = set()

    for event in events:

        if not isinstance(event, dict):
            continue

        if is_cancelled_goal_event(
            event
        ):

            player_id = get_event_player_id(
                event
            )

            if player_id is not None:

                cancelled_player_ids.add(
                    player_id
                )

    for event in events:

        if not isinstance(event, dict):
            continue

        event_type = clean_text(
            event.get("type")
        ).lower()

        if event_type != "goal":
            continue

        if event.get(
            "isPenaltyShootoutEvent"
        ) is True:

            continue

        player_id = get_event_player_id(
            event
        )

        if player_id is None:
            continue

        if player_id in cancelled_player_ids:

            continue

        player = event.get(
            "player"
        )

        player_name = ""

        if isinstance(
            player,
            dict,
        ):

            player_name = clean_text(
                player.get("name")
            )

        if not player_name:

            player_name = clean_text(
                event.get(
                    "playerName"
                )
            )

        if not player_name:
            continue

        own_goal = is_own_goal(
            event
        )

        is_home = event.get(
            "isHome"
        )

        if own_goal:

            if is_home is True:

                away_scorers.append(
                    player_name
                )

            elif is_home is False:

                home_scorers.append(
                    player_name
                )

            continue

        if player_id in home_ids:

            home_scorers.append(
                player_name
            )

        elif player_id in away_ids:

            away_scorers.append(
                player_name
            )

        else:

            if is_home is True:

                home_scorers.append(
                    player_name
                )

            elif is_home is False:

                away_scorers.append(
                    player_name
                )

    return (
        home_scorers,
        away_scorers,
    )


# --------------------------------------------------------
# ساخت علامت‌های رویداد برای بازیکن
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

    if not isinstance(data, dict):
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

    own_goals = int(
        data.get(
            "own_goals",
            0,
        )
        or 0
    )

    normal_goals = (
        goals
        - penalty_goals
    )

    if own_goals == 1:

        markers.append(
            "🔴"
        )

    elif own_goals > 1:

        markers.append(
            f"×{own_goals} 🔴"
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
# فرمت نام بازیکن با رویدادها
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


# --------------------------------------------------------
# فرمت یک خط بازیکنان
#
# ایموجی فقط در ابتدای خط اول می‌آید.
#
# اگر بازیکنان یک گروه در چند خط قرار بگیرند،
# خطوط بعدی با ۶ فاصله شروع می‌شوند تا اسم
# بازیکن زیر اسم بازیکن اول خط قرار بگیرد،
# نه زیر ایموجی پست.
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

    max_players_per_row = 3

    rows = []

    for index in range(
        0,
        len(names),
        max_players_per_row,
    ):

        rows.append(
            names[
                index:index
                + max_players_per_row
            ]
        )

    formatted_rows = []

    for row_index, row in enumerate(
        rows
    ):

        content = " | ".join(row)

        if row_index == 0:

            formatted_rows.append(
                f"{icon} {content}"
            )

        else:

            formatted_rows.append(
                f"      {content}"
            )

    return "\n".join(
        formatted_rows
    )


# --------------------------------------------------------
# فرمت گلزنان
#
# تیم سمت چپ → گلزن سمت چپ
# تیم سمت راست → گلزن سمت راست
#
# اسم تیم‌ها اینجا تکرار نمی‌شوند.
#
# اگر یک تیم گل نزده باشد،
# هیچ چیزی در سمت آن تیم نمایش داده نمی‌شود.
# --------------------------------------------------------

def format_scorers_side_by_side(
    home_scorers,
    away_scorers,
):

    if (
        not home_scorers
        and not away_scorers
    ):

        return ""

    left = (
        " | ".join(home_scorers)
        if home_scorers
        else ""
    )

    right = (
        " | ".join(away_scorers)
        if away_scorers
        else ""
    )

    # هر دو تیم گل زده‌اند.
    if left and right:

        return (
            f"⚽️ {left}"
            f"                 "
            f"{right} ⚽️"
        )

    # فقط تیم سمت چپ گل زده است.
    if left:

        return f"⚽️ {left}"

    # فقط تیم سمت راست گل زده است.
    return (
        "                 "
        f"{right} ⚽️"
    )


# --------------------------------------------------------
# فرمت ترکیب یک تیم
# --------------------------------------------------------

def format_team_lineup(
    team_name,
    team,
    show_rating,
    team_icon,
    player_events=None,
    team_score=None,
):

    if not isinstance(team, dict):

        if team_score is not None:

            return (
                f"{team_name} "
                f"{team_score}\n"
                "اطلاعات ترکیب پیدا نشد."
            )

        return (
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

    # ----------------------------------------------------
    # نام تیم + نتیجه
    # ----------------------------------------------------

    if team_score is not None:

        lines.append(
            f"{team_name} {team_score}"
        )

    else:

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

    lines.append("")

    # ----------------------------------------------------
    # دروازه‌بان
    # ----------------------------------------------------

    line = format_player_line(
        "🧤",
        groups["goalkeeper"],
        show_rating,
        player_events,
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
        player_events,
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
        player_events,
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
        player_events,
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
            player_events,
        )

        if unknown_line:

            lines.append(
                unknown_line
            )

    lines.append("")

    # ----------------------------------------------------
    # ذخیره‌ها
    # ----------------------------------------------------

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

    return "\n".join(lines)


# --------------------------------------------------------
# فرمت گلزنان قدیمی
# --------------------------------------------------------

def format_scorers(
    scorers,
):

    if not scorers:
        return ""

    return "⚽ " + " | ".join(
        scorers
    )


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

    raw_home_name = (
        info["home"]
        or "Home"
    )

    raw_away_name = (
        info["away"]
        or "Away"
    )

    home_name = translate_team_name(
        raw_home_name
    )

    away_name = translate_team_name(
        raw_away_name
    )

    raw_league = (
        info["league"]
        or "نامشخص"
    )

    league = translate_competition_name(
        raw_league
    )

    start_time = get_match_start(
        root,
        content,
    )

    kickoff = format_match_time(
        start_time
    )

    finished = is_match_finished(
        root
    )

    print()
    print(
        "MATCH FINISHED:",
        finished,
    )

    show_rating = finished

    # ----------------------------------------------------
    # نتیجه فقط بعد از پایان بازی
    # ----------------------------------------------------

    match_score = None

    if finished:

        match_score = get_match_score(
            root,
            content,
        )

    if match_score:

        print(
            "FINAL SCORE:",
            f"{match_score['home']} - "
            f"{match_score['away']}",
        )

    else:

        print(
            "FINAL SCORE:",
            "NOT FOUND",
        )

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
    # استخراج رویدادهای بازیکنان
    # ----------------------------------------------------

    player_events = {}

    home_scorers = []
    away_scorers = []

    if finished:

        player_events = extract_player_events(
            root
        )

        (
            home_scorers,
            away_scorers,
        ) = extract_scorers(
            root,
            home_starters + home_subs,
            away_starters + away_subs,
        )

    # ----------------------------------------------------
    # دیباگ رویدادها
    # ----------------------------------------------------

    print("")
    print("-" * 70)
    print("PLAYER EVENTS")
    print("-" * 70)

    if player_events:

        all_players = (
            home_starters
            + home_subs
            + away_starters
            + away_subs
        )

        printed_ids = set()

        for player in all_players:

            player_id = get_player_id(
                player
            )

            if player_id in printed_ids:
                continue

            data = player_events.get(
                player_id
            )

            if not data:
                continue

            printed_ids.add(
                player_id
            )

            print(
                f"{get_player_name(player)} "
                f"(id={player_id}): "
                f"goals={data['goals']} "
                f"| penalty_goals={data['penalty_goals']} "
                f"| own_goals={data.get('own_goals', 0)} "
                f"| assists={data['assists']} "
                f"| red_cards={data['red_cards']}"
            )

    else:

        print(
            "No player events."
        )

    print("-" * 70)

    print(
        "HOME SCORERS:",
        home_scorers,
    )

    print(
        "AWAY SCORERS:",
        away_scorers,
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
    # نمایش نتیجه نهایی تقسیم خطوط
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

    # ----------------------------------------------------
    # نام تیم‌ها + نتیجه
    #
    # هیچ ایموجی قبل از اسم تیم‌ها نیست.
    # فقط 🆚 بین دو تیم قرار می‌گیرد.
    # ----------------------------------------------------

    if finished and match_score:

        message.append(
            f"{home_name} "
            f"{match_score['home']} "
            f"🆚 "
            f"{away_name} "
            f"{match_score['away']}"
        )

    else:

        message.append(
            f"{home_name} "
            f"🆚 "
            f"{away_name}"
        )

    message.append(
        f"🕐 {kickoff} به وقت ایران"
    )

    # ----------------------------------------------------
    # گلزنان
    #
    # اسم تیم‌ها تکرار نمی‌شوند.
    #
    # اگر فقط تیم سمت چپ گل زده باشد:
    # ⚽️ Player
    #
    # اگر فقط تیم سمت راست گل زده باشد:
    # Player ⚽️
    #
    # اگر هیچ تیمی گل نزده باشد:
    # هیچ خطی نمایش داده نمی‌شود.
    # ----------------------------------------------------

    if finished:

        scorer_line = (
            format_scorers_side_by_side(
                home_scorers,
                away_scorers,
            )
        )

        if scorer_line:

            message.append("")

            message.append(
                scorer_line
            )

    message.append("")

    # ----------------------------------------------------
    # ترکیب تیم اول
    # ----------------------------------------------------

    home_score = None

    if finished and match_score:

        home_score = match_score[
            "home"
        ]

    message.append(
        format_team_lineup(
            home_name,
            home_team,
            show_rating,
            "",
            player_events,
            home_score,
        )
    )

    message.append("")

    # ----------------------------------------------------
    # ترکیب تیم دوم
    # ----------------------------------------------------

    away_score = None

    if finished and match_score:

        away_score = match_score[
            "away"
        ]

    message.append(
        format_team_lineup(
            away_name,
            away_team,
            show_rating,
            "",
            player_events,
            away_score,
        )
    )

    return "\n".join(message)


# --------------------------------------------------------
# تقسیم پیام تلگرام
# --------------------------------------------------------

def split_message(
    message,
    max_length=4000,
):

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

    return chunks


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
        f"match_{MATCH_ID}_raw.json",
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
        f"match_{MATCH_ID}_raw.json"
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

    chunks = split_message(
        message
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

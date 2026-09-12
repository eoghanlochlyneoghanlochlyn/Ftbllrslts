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
# پیدا کردن اطلاعات پایه بازی
# --------------------------------------------------------

def extract_basic_info(root):
    event_jsonld = get_nested(
        root,
        "props",
        "pageProps",
        "seo",
        "eventJSONLD",
    )

    content = get_nested(
        root,
        "props",
        "pageProps",
        "content",
    )

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
    # اطلاعات تکمیلی از content
    # ----------------------------------------------------

    if isinstance(content, dict):

        # اگر اسم تیم از eventJSONLD پیدا نشد،
        # چند مسیر احتمالی داخل content را بررسی می‌کنیم.

        if not info["home"]:
            for key in (
                "homeTeam",
                "home",
            ):
                value = content.get(key)

                if isinstance(value, dict):
                    name = (
                        value.get("longName")
                        or value.get("name")
                        or value.get("shortName")
                    )

                    if name:
                        info["home"] = clean_text(
                            name
                        )
                        break

        if not info["away"]:
            for key in (
                "awayTeam",
                "away",
            ):
                value = content.get(key)

                if isinstance(value, dict):
                    name = (
                        value.get("longName")
                        or value.get("name")
                        or value.get("shortName")
                    )

                    if name:
                        info["away"] = clean_text(
                            name
                        )
                        break

        # ------------------------------------------------
        # رقابت
        # ------------------------------------------------

        for key in (
            "league",
            "tournament",
            "competition",
        ):

            value = content.get(key)

            if isinstance(value, dict):

                for name_key in (
                    "name",
                    "longName",
                    "shortName",
                ):

                    if value.get(name_key):

                        info["league"] = clean_text(
                            value[name_key]
                        )

                        break

            elif isinstance(value, str):

                info["league"] = clean_text(
                    value
                )

            if info["league"]:
                break

        # ------------------------------------------------
        # ورزشگاه
        # ------------------------------------------------

        for key in (
            "venue",
            "stadium",
        ):

            value = content.get(key)

            if isinstance(value, dict):

                for name_key in (
                    "name",
                    "longName",
                ):

                    if value.get(name_key):

                        info["venue"] = clean_text(
                            value[name_key]
                        )

                        break

            elif isinstance(value, str):

                info["venue"] = clean_text(
                    value
                )

            if info["venue"]:
                break

    return info


# --------------------------------------------------------
# جستجوی بازگشتی
# --------------------------------------------------------

def recursive_find(data, wanted_keys):
    results = []

    def walk(value, path="root"):

        if len(results) >= 100:
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
# استخراج زمان از ساختارهای مختلف
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
            ):

                if status.get(key):
                    return status[key]

        for key in (
            "utcTime",
            "startTime",
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

        # اگر FotMob مستقیماً finished بدهد
        if status.get("finished") is True:
            return True

        # بعضی نسخه‌ها reason/name دارند
        values = []

        for key in (
            "reason",
            "name",
            "short",
            "long",
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

    # fallback فقط برای اطمینان
    lineup = find_section(
        root,
        ["lineup"],
    )

    if isinstance(lineup, dict):
        return lineup

    return None


# --------------------------------------------------------
# پیدا کردن نام بازیکن
# --------------------------------------------------------

def get_player_name(player):
    if not isinstance(player, dict):
        return ""

    # مسیرهای مختلفی که قبلاً در FotMob دیده شده
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

    # مسیرهای مستقیم
    for key in (
        "position",
        "positionName",
        "role",
        "playerPosition",
    ):

        candidates.append(
            player.get(key)
        )

    # بعضی داده‌ها position را به صورت object دارند
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

    # role به صورت object
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

    # player nested
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
                        value.get(
                            "abbreviation"
                        ),
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

    # -------------------------
    # دروازه‌بان
    # -------------------------

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

    # -------------------------
    # مدافع
    # -------------------------

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

    # -------------------------
    # هافبک
    # -------------------------

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

    # -------------------------
    # مهاجم
    # -------------------------

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
# پیدا کردن تیم داخل lineup
# --------------------------------------------------------

def get_lineup_team(lineup, side):
    if not isinstance(lineup, dict):
        return None

    # ساختار قبلی واقعی FotMob
    team = lineup.get(side)

    if isinstance(team, dict):
        return team

    # fallback
    aliases = {
        "home": (
            "homeTeam",
            "home",
        ),
        "away": (
            "awayTeam",
            "away",
        ),
    }

    for key in aliases.get(
        side,
        (),
    ):

        team = lineup.get(key)

        if isinstance(team, dict):
            return team

    return None


# --------------------------------------------------------
# استخراج starter ها
# --------------------------------------------------------

def get_starters(team):
    if not isinstance(team, dict):
        return []

    for key in (
        "starters",
        "startingXI",
        "startingLineup",
        "players",
    ):

        value = team.get(key)

        if isinstance(value, list):
            return value

    return []


# --------------------------------------------------------
# استخراج substitute ها
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

    return []


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
# فرمت یک خط از بازیکنان
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

    groups = organize_players(
        starters
    )

    lines = []

    # نام تیم
    lines.append(
        f"{team_icon} {team_name}"
    )

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

    # دقیقاً یک خط خالی قبل از تعویضی‌ها
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

    # ----------------------------------------------------
    # اگر نام تیم‌ها از eventJSONLD پیدا شده
    # همان‌ها را نگه می‌داریم.
    # ----------------------------------------------------

    home_name = (
        info["home"]
        or "Home"
    )

    away_name = (
        info["away"]
        or "Away"
    )

    # ----------------------------------------------------
    # رقابت
    # ----------------------------------------------------

    league = (
        info["league"]
        or "نامشخص"
    )

    # ----------------------------------------------------
    # زمان ایران
    # ----------------------------------------------------

    start_time = get_match_start(
        root,
        content,
    )

    kickoff = format_match_time(
        start_time
    )

    # ----------------------------------------------------
    # وضعیت بازی
    # ----------------------------------------------------

    finished = is_match_finished(
        content
    )

    print()
    print(
        "MATCH FINISHED:",
        finished,
    )

    # فقط بعد از پایان بازی rating نمایش داده شود
    show_rating = finished

    # ----------------------------------------------------
    # ترکیب
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

    # ----------------------------------------------------
    # پیام
    # ----------------------------------------------------

    message = []

    message.append(
        f"🏆 {league}"
    )

    message.append("")

    message.append(
        f"⚽ {home_name} 🆚 {away_name}"
    )

    message.append(
        f"🕐 {kickoff} به وقت ایران"
    )

    message.append("")

    # ----------------------------------------------------
    # تیم میزبان
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
    # تیم مهمان
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
    # ذخیره JSON خام برای بررسی
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
    # تقسیم پیام در صورت طول زیاد
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

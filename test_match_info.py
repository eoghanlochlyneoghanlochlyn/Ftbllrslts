import json
import os
import re
from datetime import datetime, timezone

import requests


MATCH_ID = "5811755"
MATCH_URL = f"https://www.fotmob.com/match/{MATCH_ID}"

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


def send_telegram(text):
    if not TELEGRAM_BOT_TOKEN:
        raise RuntimeError("TELEGRAMBOT environment variable is missing.")

    if not TELEGRAM_CHANNEL:
        raise RuntimeError("TELEGRAMCHANNEL environment variable is missing.")

    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"

    response = requests.post(
        url,
        data={
            "chat_id": TELEGRAM_CHANNEL,
            "text": text,
        },
        timeout=30,
    )

    print("Telegram status:", response.status_code)

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

    match = re.search(pattern, html, re.DOTALL)

    if not match:
        raise RuntimeError("__NEXT_DATA__ not found.")

    raw_json = match.group(1)

    data = json.loads(raw_json)

    print("NEXT_DATA extracted successfully.")

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

    if isinstance(event_jsonld, dict):
        home_team = event_jsonld.get("homeTeam")
        away_team = event_jsonld.get("awayTeam")

        if isinstance(home_team, dict):
            info["home"] = clean_text(home_team.get("name"))

        if isinstance(away_team, dict):
            info["away"] = clean_text(away_team.get("name"))

        info["start"] = clean_text(
            event_jsonld.get("startDate")
        )

    if isinstance(content, dict):

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
                info["league"] = value

            if info["league"]:
                break

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
                info["venue"] = value

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

                current_path = f"{path}.{key}"

                if key in wanted_keys:
                    results.append(
                        (
                            current_path,
                            child,
                        )
                    )

                walk(child, current_path)

        elif isinstance(value, list):
            for index, child in enumerate(value):
                walk(
                    child,
                    f"{path}[{index}]",
                )

    walk(data)

    return results


# --------------------------------------------------------
# پیدا کردن بخش‌های مهم
# --------------------------------------------------------

def find_section(root, names):
    results = recursive_find(
        root,
        set(names),
    )

    if not results:
        return None

    # اولویت با مواردی که داخل content هستند
    for path, value in results:
        if "pageProps.content" in path:
            return value

    return results[0][1]


# --------------------------------------------------------
# تبدیل زمان
# --------------------------------------------------------

def format_match_time(value):
    if not value:
        return "نامشخص"

    try:
        dt = datetime.fromisoformat(
            value.replace("Z", "+00:00")
        )

        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)

        iran_time = dt.astimezone(
            timezone.utc
        )

        return dt.strftime(
            "%Y-%m-%d %H:%M UTC"
        )

    except Exception:
        return str(value)


# --------------------------------------------------------
# تبدیل داده‌های مختلف به متن قابل خواندن
# --------------------------------------------------------

def format_value(value, indent=0):
    prefix = " " * indent

    if value is None:
        return ""

    if isinstance(value, (str, int, float, bool)):
        return str(value)

    if isinstance(value, list):

        lines = []

        for index, item in enumerate(value, 1):
            if isinstance(item, (dict, list)):
                lines.append(
                    f"{prefix}{index}."
                )
                lines.append(
                    format_value(
                        item,
                        indent + 2,
                    )
                )
            else:
                lines.append(
                    f"{prefix}- {item}"
                )

        return "\n".join(lines)

    if isinstance(value, dict):

        lines = []

        for key, child in value.items():

            if isinstance(
                child,
                (dict, list),
            ):
                lines.append(
                    f"{prefix}{key}:"
                )

                formatted = format_value(
                    child,
                    indent + 2,
                )

                if formatted:
                    lines.append(formatted)

            else:
                lines.append(
                    f"{prefix}{key}: {child}"
                )

        return "\n".join(lines)

    return str(value)


# --------------------------------------------------------
# ساخت بخش ترکیب
# --------------------------------------------------------

def format_lineups(lineup):
    if not lineup:
        return "اطلاعات ترکیب پیدا نشد."

    text = []

    text.append("👥 ترکیب‌ها")

    if isinstance(lineup, dict):

        lineup_type = lineup.get(
            "lineupType"
        )

        if lineup_type:
            text.append(
                f"نوع ترکیب: {lineup_type}"
            )

        home = (
            lineup.get("home")
            or lineup.get("homeTeam")
        )

        away = (
            lineup.get("away")
            or lineup.get("awayTeam")
        )

        for title, team in (
            ("🏠 تیم میزبان", home),
            ("✈️ تیم مهمان", away),
        ):

            if not isinstance(team, dict):
                continue

            text.append("")
            text.append(title)

            coach = (
                team.get("coach")
                or team.get("manager")
            )

            if isinstance(coach, dict):
                coach = (
                    coach.get("name")
                    or coach.get("longName")
                )

            if coach:
                text.append(
                    f"مربی: {coach}"
                )

            formation = team.get(
                "formation"
            )

            if formation:
                text.append(
                    f"آرایش: {formation}"
                )

            starters = (
                team.get("starters")
                or team.get("startingXI")
                or team.get("players")
            )

            if isinstance(starters, list):

                text.append(
                    "بازیکنان:"
                )

                for player in starters:

                    if not isinstance(
                        player,
                        dict,
                    ):
                        continue

                    name = (
                        player.get("name")
                        or player.get(
                            "playerName"
                        )
                        or player.get(
                            "longName"
                        )
                    )

                    number = (
                        player.get("number")
                        or player.get(
                            "shirtNumber"
                        )
                    )

                    rating = (
                        player.get("rating")
                        or player.get(
                            "ratingScore"
                        )
                    )

                    line = "-"

                    if number:
                        line += f" {number}"

                    if name:
                        line += f" {name}"

                    if rating:
                        line += (
                            f" ⭐ {rating}"
                        )

                    text.append(line)

    return "\n".join(text)


# --------------------------------------------------------
# ساخت پیام اصلی
# --------------------------------------------------------

def build_message(root):

    info = extract_basic_info(root)

    content = get_nested(
        root,
        "props",
        "pageProps",
        "content",
    )

    lineup = find_section(
        root,
        [
            "lineup",
        ],
    )

    events = find_section(
        root,
        [
            "events",
            "incidents",
            "matchEvents",
        ],
    )

    stats = find_section(
        root,
        [
            "stats",
            "statistics",
            "matchStats",
        ],
    )

    shotmap = find_section(
        root,
        [
            "shotmap",
        ],
    )

    momentum = find_section(
        root,
        [
            "momentum",
        ],
    )

    message = []

    message.append("⚽ KV Mechelen 🆚 Anderlecht")
    message.append("")

    message.append(
        f"🏆 {info['league'] or 'نامشخص'}"
    )

    message.append(
        f"🕐 {format_match_time(info['start'])}"
    )

    if info["venue"]:
        message.append(
            f"🏟 {info['venue']}"
        )

    message.append("")

    message.append("━━━━━━━━━━━━━━")
    message.append("📊 اطلاعات مسابقه")
    message.append("━━━━━━━━━━━━━━")

    if isinstance(content, dict):

        for key in (
            "status",
            "score",
            "round",
            "matchStatus",
        ):
            value = content.get(key)

            if value is not None:
                message.append(
                    f"{key}: "
                    f"{format_value(value)}"
                )

    message.append("")
    message.append(
        format_lineups(lineup)
    )

    if events:
        message.append("")
        message.append(
            "━━━━━━━━━━━━━━"
        )
        message.append(
            "🔥 رویدادهای بازی"
        )
        message.append(
            "━━━━━━━━━━━━━━"
        )
        message.append(
            format_value(events)
        )

    if stats:
        message.append("")
        message.append(
            "━━━━━━━━━━━━━━"
        )
        message.append(
            "📈 آمار مسابقه"
        )
        message.append(
            "━━━━━━━━━━━━━━"
        )
        message.append(
            format_value(stats)
        )

    if shotmap:
        message.append("")
        message.append(
            "━━━━━━━━━━━━━━"
        )
        message.append(
            "🎯 Shotmap"
        )
        message.append(
            "━━━━━━━━━━━━━━"
        )
        message.append(
            format_value(shotmap)
        )

    if momentum:
        message.append("")
        message.append(
            "━━━━━━━━━━━━━━"
        )
        message.append(
            "📉 Momentum"
        )
        message.append(
            "━━━━━━━━━━━━━━"
        )
        message.append(
            format_value(momentum)
        )

    return "\n".join(message)


# --------------------------------------------------------
# اجرای تست
# --------------------------------------------------------

def main():

    print("")
    print("#" * 70)
    print("FOTMOB → TELEGRAM MATCH STRUCTURE TEST")
    print("#" * 70)

    html = fetch_match_page()

    root = extract_next_data(html)

    # ذخیره JSON خام فقط برای بررسی
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

    message = build_message(root)

    print("")
    print("=" * 70)
    print("MESSAGE TO TELEGRAM")
    print("=" * 70)
    print(message)
    print("=" * 70)

    # Telegram محدودیت طول پیام دارد.
    # اگر پیام خیلی بزرگ باشد آن را به چند پیام تقسیم می‌کنیم.

    max_length = 4000

    chunks = []

    while len(message) > max_length:

        cut = message.rfind(
            "\n",
            0,
            max_length,
        )

        if cut == -1:
            cut = max_length

        chunks.append(
            message[:cut]
        )

        message = message[
            cut:
        ].lstrip()

    if message:
        chunks.append(message)

    print(
        f"Telegram messages to send: "
        f"{len(chunks)}"
    )

    for index, chunk in enumerate(
        chunks,
        1,
    ):

        print(
            f"Sending message "
            f"{index}/{len(chunks)}..."
        )

        send_telegram(chunk)

    print("")
    print("=" * 70)
    print("TEST SUCCESSFUL")
    print("=" * 70)


if __name__ == "__main__":
    main()

import html
import json
import re
from datetime import datetime, timezone

import requests

from match_cache import load_matches_cache, save_matches_cache
from telegram_sender import send_telegram_message


# ============================================================
# تنظیمات
# ============================================================

FOTMOB_MATCH_URL = "https://www.fotmob.com/match/{}"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/140.0.0.0 Safari/537.36"
    ),
    "Accept": (
        "text/html,application/xhtml+xml,application/xml;"
        "q=0.9,image/avif,image/webp,*/*;q=0.8"
    ),
    "Accept-Language": "en-US,en;q=0.9",
}

REQUEST_TIMEOUT = 20

# اگر تا این زمان ترکیب رسمی پیدا نشد،
# پیام "ترکیب رسمی هنوز اعلام نشده" ارسال می‌شود.
FALLBACK_MINUTES = 30


# ============================================================
# ترجمه لیگ‌ها
# ============================================================

LEAGUE_TRANSLATIONS = {
    "Premier League": "لیگ برتر انگلیس",
    "LaLiga": "لالیگا",
    "La Liga": "لالیگا",
    "Serie A": "سری آ",
    "Bundesliga": "بوندس‌لیگا",
    "Ligue 1": "لیگ ۱ فرانسه",
    "UEFA Champions League": "لیگ قهرمانان اروپا",
    "Champions League": "لیگ قهرمانان اروپا",
    "UEFA Europa League": "لیگ اروپا",
    "Europa League": "لیگ اروپا",
    "UEFA Conference League": "لیگ کنفرانس اروپا",
    "Conference League": "لیگ کنفرانس اروپا",
    "FA Cup": "جام حذفی انگلیس",
    "EFL Cup": "جام اتحادیه انگلیس",
    "Carabao Cup": "جام اتحادیه انگلیس",
    "DFB Pokal": "جام حذفی آلمان",
    "Coppa Italia": "جام حذفی ایتالیا",
    "Copa del Rey": "جام حذفی اسپانیا",
    "Coupe de France": "جام حذفی فرانسه",
    "Super Cup": "سوپرجام",
}


# ============================================================
# ترجمه نام تیم‌ها
# ============================================================

TEAM_TRANSLATIONS = {
    "Liverpool": "لیورپول",
    "Arsenal": "آرسنال",
    "Manchester City": "منچسترسیتی",
    "Manchester United": "منچستریونایتد",
    "Chelsea": "چلسی",
    "Tottenham Hotspur": "تاتنهام",
    "Tottenham": "تاتنهام",
    "Juventus": "یوونتوس",
    "AC Milan": "آث میلان",
    "Milan": "میلان",
    "Inter": "اینتر",
    "Inter Milan": "اینتر",
    "Inter Milano": "اینتر",
    "Bayern Munich": "بایرن مونیخ",
    "Bayern München": "بایرن مونیخ",
    "Borussia Dortmund": "بوروسیا دورتموند",
    "PSG": "پاری‌سن‌ژرمن",
    "Paris Saint-Germain": "پاری‌سن‌ژرمن",
    "Real Madrid": "رئال مادرید",
    "Barcelona": "بارسلونا",
    "Atlético Madrid": "اتلتیکومادرید",
    "Atletico Madrid": "اتلتیکومادرید",
    "Atletico de Madrid": "اتلتیکومادرید",
    "Sevilla": "سویا",
    "Valencia": "والنسیا",
    "Fiorentina": "فیورنتینا",
    "Venezia": "ونیزیا",
    "Union Berlin": "یونیون برلین",
    "Schalke 04": "شالکه",
    "Marseille": "مارسی",
    "Rennes": "رن",
}


# ============================================================
# ابزارهای عمومی
# ============================================================

def log(message):
    print(message, flush=True)


def translate_league(name):
    if not name:
        return "نامشخص"

    name = str(name).strip()

    return LEAGUE_TRANSLATIONS.get(name, name)


def translate_team(name):
    if not name:
        return "نامشخص"

    name = str(name).strip()

    return TEAM_TRANSLATIONS.get(name, name)


def get_nested(data, *keys):
    current = data

    for key in keys:
        if not isinstance(current, dict):
            return None

        current = current.get(key)

    return current


# ============================================================
# دریافت صفحه مسابقه فوت‌موب
# ============================================================

def fetch_match_page(match_id):
    url = FOTMOB_MATCH_URL.format(match_id)

    log(f"Fetching FotMob page: {url}")

    try:
        response = requests.get(
            url,
            headers=HEADERS,
            timeout=REQUEST_TIMEOUT,
        )

        log(f"HTTP status: {response.status_code}")

        response.raise_for_status()

        return response.text

    except requests.RequestException as exc:
        log(f"ERROR fetching FotMob page: {exc}")
        return None


# ============================================================
# استخراج __NEXT_DATA__
# ============================================================

def extract_next_data(page_html):
    if not page_html:
        return None

    match = re.search(
        r'<script[^>]+id=["\']__NEXT_DATA__["\'][^>]*>(.*?)</script>',
        page_html,
        re.DOTALL | re.IGNORECASE,
    )

    if not match:
        log("ERROR: __NEXT_DATA__ not found.")
        return None

    raw_json = html.unescape(match.group(1))

    try:
        return json.loads(raw_json)

    except json.JSONDecodeError as exc:
        log(f"ERROR parsing __NEXT_DATA__: {exc}")
        return None


# ============================================================
# استخراج اطلاعات lineup
# ============================================================

def get_lineup_data(root):
    if not isinstance(root, dict):
        return None

    lineup = get_nested(
        root,
        "props",
        "pageProps",
        "content",
        "lineup",
    )

    if not isinstance(lineup, dict):
        log("LINEUP OBJECT NOT FOUND")
        return None

    log("LINEUP OBJECT FOUND")

    return lineup


# ============================================================
# وضعیت رسمی بودن ترکیب
# ============================================================

def has_official_lineups(lineup):
    """
    در تست‌های واقعی FotMob:

    standard  -> ترکیب منتشرشده
    confirmed -> ترکیب منتشرشده
    predicted -> ترکیب پیش‌بینی‌شده

    برای جلوگیری از ارسال اشتباه، فقط standard و confirmed
    را رسمی در نظر می‌گیریم.
    """

    if not isinstance(lineup, dict):
        return False

    lineup_type = str(
        lineup.get("lineupType") or ""
    ).strip().lower()

    log(f"FotMob lineupType: {lineup_type}")

    if lineup_type not in {
        "standard",
        "confirmed",
    }:
        return False

    home_team = lineup.get("homeTeam") or {}
    away_team = lineup.get("awayTeam") or {}

    home_starters = get_starters(home_team)
    away_starters = get_starters(away_team)

    log(f"Home starters: {len(home_starters)}")
    log(f"Away starters: {len(away_starters)}")

    return (
        len(home_starters) >= 11
        and len(away_starters) >= 11
    )


# ============================================================
# نام مربی
# ============================================================

def get_coach_name(team_data):
    if not isinstance(team_data, dict):
        return "Unknown"

    coach = team_data.get("coach")

    if isinstance(coach, dict):
        return (
            coach.get("name")
            or coach.get("shortName")
            or "Unknown"
        )

    if isinstance(coach, str):
        return coach

    return "Unknown"


# ============================================================
# آرایش
# ============================================================

def get_formation(team_data):
    if not isinstance(team_data, dict):
        return "Unknown"

    formation = team_data.get("formation")

    if formation:
        return str(formation)

    return "Unknown"


# ============================================================
# بازیکنان اصلی
# ============================================================

def get_starters(team_data):
    if not isinstance(team_data, dict):
        return []

    starters = team_data.get("starters")

    if not isinstance(starters, list):
        return []

    return starters


# ============================================================
# نام بازیکن
# ============================================================

def get_player_name(player):
    if not isinstance(player, dict):
        return "Unknown"

    player_data = player.get("player")

    if isinstance(player_data, dict):
        name = (
            player_data.get("name")
            or player_data.get("shortName")
            or player_data.get("fullName")
        )

        if name:
            return str(name)

    name = (
        player.get("name")
        or player.get("shortName")
        or player.get("fullName")
    )

    if name:
        return str(name)

    return "Unknown"


# ============================================================
# شماره پیراهن
# ============================================================

def get_player_number(player):
    if not isinstance(player, dict):
        return None

    number = player.get("shirtNumber")

    if number is None:
        number = player.get("number")

    if number is None:
        player_data = player.get("player")

        if isinstance(player_data, dict):
            number = player_data.get("shirtNumber")

            if number is None:
                number = player_data.get("number")

    if number is None:
        return None

    return str(number)


# ============================================================
# فرمت بازیکن
# ============================================================

def format_player(player):
    name = get_player_name(player)
    number = get_player_number(player)

    if number:
        return f"{number}. {name}"

    return name


# ============================================================
# استخراج اطلاعات مسابقه
# ============================================================

def extract_match_info(root, match):
    """
    اطلاعات پایه را اول از کش می‌گیریم.
    اگر چیزی موجود نبود، از __NEXT_DATA__ استفاده می‌کنیم.
    """

    content = get_nested(
        root,
        "props",
        "pageProps",
        "content",
    )

    if not isinstance(content, dict):
        content = {}

    match_info = content.get("match")

    if not isinstance(match_info, dict):
        match_info = {}

    home_team = match_info.get("homeTeam")

    if not isinstance(home_team, dict):
        home_team = {}

    away_team = match_info.get("awayTeam")

    if not isinstance(away_team, dict):
        away_team = {}

    home_name = (
        match.get("home")
        or home_team.get("name")
        or "Unknown"
    )

    away_name = (
        match.get("away")
        or away_team.get("name")
        or "Unknown"
    )

    league = (
        match.get("league")
        or match_info.get("leagueName")
        or content.get("leagueName")
        or "Unknown"
    )

    return {
        "home": home_name,
        "away": away_name,
        "league": league,
    }


# ============================================================
# تبدیل ساعت به ساعت ایران
# ============================================================

def get_iran_time(match):
    iran_time = match.get("iran_time")

    if not iran_time:
        return "نامشخص"

    try:
        parsed = datetime.fromisoformat(
            str(iran_time).replace("Z", "+00:00")
        )

        return parsed.strftime("%H:%M")

    except Exception:
        pass

    text = str(iran_time)

    match_time = re.search(
        r"(\d{1,2}):(\d{2})",
        text,
    )

    if match_time:
        return (
            f"{int(match_time.group(1)):02d}:"
            f"{match_time.group(2)}"
        )

    return text


# ============================================================
# ساخت بخش ترکیب یک تیم
# ============================================================

def format_team_lineup(team_data):
    if not isinstance(team_data, dict):
        return "Unknown"

    team_name = translate_team(
        team_data.get("name")
    )

    coach = get_coach_name(team_data)
    formation = get_formation(team_data)
    starters = get_starters(team_data)

    lines = []

    lines.append(f"🔹 {team_name}")
    lines.append(f"Coach: {coach}")
    lines.append(f"Formation: {formation}")
    lines.append("Starting XI:")

    for player in starters:
        lines.append(
            f"• {format_player(player)}"
        )

    return "\n".join(lines)


# ============================================================
# ساخت پست پیش‌مسابقه
# ============================================================

def build_pre_match_post(
    match,
    lineup=None,
    official_lineups=False,
):
    home = translate_team(
        match.get("home")
    )

    away = translate_team(
        match.get("away")
    )

    league = translate_league(
        match.get("league")
    )

    iran_time = get_iran_time(match)

    lines = []

    lines.append(f"🏆 {league}")
    lines.append("")
    lines.append(
        f"{home} 🆚 {away}"
    )
    lines.append("")
    lines.append(
        f"⏰ {iran_time} به وقت ایران"
    )

    lines.append("")
    lines.append("━━━━━━━━━━━━━━━━━━━━━━")
    lines.append("")

    if official_lineups and isinstance(lineup, dict):
        home_team = lineup.get("homeTeam") or {}
        away_team = lineup.get("awayTeam") or {}

        lines.append(
            format_team_lineup(home_team)
        )

        lines.append("")

        lines.append(
            format_team_lineup(away_team)
        )

    else:
        lines.append(
            "ترکیب رسمی هنوز اعلام نشده است."
        )

    return "\n".join(lines)


# ============================================================
# محاسبه زمان باقی‌مانده تا شروع
# ============================================================

def get_minutes_until_kickoff(match):
    utc_time = match.get("utc_time")

    if not utc_time:
        return None

    try:
        kickoff = datetime.fromisoformat(
            str(utc_time).replace("Z", "+00:00")
        )

        if kickoff.tzinfo is None:
            kickoff = kickoff.replace(
                tzinfo=timezone.utc
            )

        now = datetime.now(timezone.utc)

        difference = (
            kickoff - now
        ).total_seconds() / 60

        return difference

    except Exception as exc:
        log(
            f"ERROR parsing kickoff time: {exc}"
        )

        return None


# ============================================================
# تصمیم‌گیری برای ارسال
# ============================================================

def should_send_pre_match(
    match,
    official_lineups,
):
    if match.get("pre_match_sent") is True:
        return (
            False,
            "Pre-match post already sent.",
        )

    status = str(
        match.get("status") or ""
    ).strip().lower()

    if status != "upcoming":
        return (
            False,
            f"Match status is {match.get('status')}.",
        )

    minutes_until_kickoff = (
        get_minutes_until_kickoff(match)
    )

    if minutes_until_kickoff is None:
        return (
            False,
            "Kickoff time is unavailable.",
        )

    log(
        f"Minutes until kickoff: "
        f"{minutes_until_kickoff:.1f}"
    )

    # --------------------------------------------------------
    # حالت اول:
    # ترکیب رسمی پیدا شده
    # --------------------------------------------------------

    if official_lineups:
        return (
            True,
            "Official lineups detected.",
        )

    # --------------------------------------------------------
    # حالت دوم:
    # هنوز ترکیب رسمی نیست،
    # ولی 30 دقیقه یا کمتر مانده
    # --------------------------------------------------------

    if (
        0 <= minutes_until_kickoff
        <= FALLBACK_MINUTES
    ):
        return (
            True,
            "Fallback: 30 minutes or less remain.",
        )

    # --------------------------------------------------------
    # اگر بازی شروع شده باشد، هیچ پست پیش‌مسابقه‌ای
    # نباید ارسال شود.
    # --------------------------------------------------------

    if minutes_until_kickoff < 0:
        return (
            False,
            "Kickoff time has already passed.",
        )

    return (
        False,
        "More than 30 minutes remain and official lineups are not available.",
    )


# ============================================================
# پردازش یک مسابقه
# ============================================================

async def process_match(match):
    match_id = match.get("id")

    log("")
    log("=" * 70)
    log(
        f"Processing match: "
        f"{match.get('home')} vs {match.get('away')}"
    )
    log(f"Match ID: {match_id}")
    log(f"Status: {match.get('status')}")
    log(
        f"Pre-match sent: "
        f"{match.get('pre_match_sent')}"
    )
    log(
        f"UTC time: "
        f"{match.get('utc_time')}"
    )
    log("=" * 70)

    if not match_id:
        log("ERROR: Match ID is missing.")
        return False

    if match.get("pre_match_sent") is True:
        log("Decision: ALREADY SENT")
        return False

    page_html = fetch_match_page(match_id)

    if not page_html:
        log("Decision: WAIT")
        return False

    root = extract_next_data(page_html)

    if not root:
        log("Decision: WAIT")
        return False

    lineup = get_lineup_data(root)

    if lineup is None:
        log("Decision: WAIT")
        return False

    lineup_type = str(
        lineup.get("lineupType") or ""
    ).strip().lower()

    log(
        f"FotMob lineupType: "
        f"{lineup_type}"
    )

    home_team = lineup.get("homeTeam") or {}
    away_team = lineup.get("awayTeam") or {}

    home_starters = get_starters(home_team)
    away_starters = get_starters(away_team)

    log(
        f"Home starters: "
        f"{len(home_starters)}"
    )

    log(
        f"Away starters: "
        f"{len(away_starters)}"
    )

    official_lineups = has_official_lineups(
        lineup
    )

    log(
        f"Official lineups: "
        f"{official_lineups}"
    )

    should_send, reason = (
        should_send_pre_match(
            match,
            official_lineups,
        )
    )

    log(
        f"Decision reason: "
        f"{reason}"
    )

    if not should_send:
        log("Decision: WAIT")
        return False

    log("Decision: SEND")

    post_text = build_pre_match_post(
        match=match,
        lineup=lineup,
        official_lineups=official_lineups,
    )

    log("")
    log("Generated Telegram post:")
    log("-" * 70)
    log(post_text)
    log("-" * 70)

    success = await send_telegram_message(
        post_text
    )

    if not success:
        log(
            "Telegram send failed. "
            "Cache will NOT be marked as sent."
        )

        return False

    match["pre_match_sent"] = True

    match["last_pre_match_sent_at"] = (
        datetime.now(
            timezone.utc
        ).isoformat()
    )

    log(
        "pre_match_sent = True"
    )

    return True


# ============================================================
# تابع اصلی
# ============================================================

async def main():
    log("")
    log("=" * 70)
    log("PRE-MATCH POST PROCESSOR")
    log("=" * 70)
    log(
        f"Fallback window: "
        f"{FALLBACK_MINUTES} minutes"
    )
    log(
        "Official lineup types: "
        "standard / confirmed"
    )
    log("=" * 70)

    cache = load_matches_cache()

    if not isinstance(cache, dict):
        log(
            "ERROR: matches_cache.json "
            "could not be loaded."
        )

        return

    if not cache:
        log(
            "No matches found in cache."
        )

        return

    log(
        f"Matches in cache: "
        f"{len(cache)}"
    )

    changed = False

    for match_id, match in cache.items():
        if not isinstance(match, dict):
            continue

        try:
            sent = await process_match(
                match
            )

            if sent:
                changed = True

        except Exception as exc:
            log("")
            log(
                f"ERROR processing match "
                f"{match_id}: {exc}"
            )

            import traceback

            traceback.print_exc()

    # --------------------------------------------------------
    # ذخیره کش فقط در پایان
    # --------------------------------------------------------

    if changed:
        log("")
        log(
            "Saving updated matches_cache.json..."
        )

        save_matches_cache(cache)

        log(
            "Cache saved successfully."
        )

    else:
        log("")
        log(
            "No cache changes."
        )

    log("")
    log("=" * 70)
    log("PRE-MATCH PROCESSING FINISHED")
    log("=" * 70)


# ============================================================
# اجرای برنامه
# ============================================================

if __name__ == "__main__":
    import asyncio

    asyncio.run(main())

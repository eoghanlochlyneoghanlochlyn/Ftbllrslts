import json
import requests


# ============================================================
# تنظیمات
# ============================================================

MATCH_ID = "6106264"

URL = f"https://www.fotmob.com/match/{MATCH_ID}"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/140.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,"
              "image/avif,image/webp,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Referer": "https://www.fotmob.com/",
}


# ============================================================
# دریافت صفحه مسابقه
# ============================================================

def get_match_page():

    print("🌐 درخواست به فوت‌ماب:")
    print(URL)
    print()

    response = requests.get(
        URL,
        headers=HEADERS,
        timeout=30
    )

    print(f"📡 HTTP Status: {response.status_code}")
    print(f"📏 HTML Length: {len(response.text)}")
    print()

    response.raise_for_status()

    return response.text


# ============================================================
# استخراج __NEXT_DATA__
# ============================================================

def extract_next_data(html):

    marker_start = '<script id="__NEXT_DATA__" type="application/json">'
    marker_end = "</script>"

    start = html.find(marker_start)

    if start == -1:
        raise Exception("❌ __NEXT_DATA__ پیدا نشد.")

    start += len(marker_start)

    end = html.find(marker_end, start)

    if end == -1:
        raise Exception("❌ پایان __NEXT_DATA__ پیدا نشد.")

    json_text = html[start:end]

    data = json.loads(json_text)

    print("✅ __NEXT_DATA__ با موفقیت استخراج شد.")
    print()

    return data


# ============================================================
# استخراج اطلاعات اصلی
# ============================================================

def extract_match_data(root):

    page_props = (
        root
        .get("props", {})
        .get("pageProps", {})
    )

    general = page_props.get("general", {})
    header = page_props.get("header", {})
    content = page_props.get("content", {})

    return {
        "general": general,
        "header": header,
        "content": content,
    }


# ============================================================
# نمایش کلیدهای موجود
# ============================================================

def show_structure(data):

    print("=" * 70)
    print("🧩 ساختار اطلاعات مسابقه")
    print("=" * 70)
    print()

    general = data["general"]
    header = data["header"]
    content = data["content"]

    print("📌 کلیدهای general:")
    print(list(general.keys()))
    print()

    print("📌 کلیدهای header:")
    print(list(header.keys()))
    print()

    print("📌 کلیدهای content:")
    print(list(content.keys()))
    print()


# ============================================================
# نمایش اطلاعات اصلی بازی
# ============================================================

def show_basic_info(data):

    general = data["general"]
    header = data["header"]

    print("=" * 70)
    print("⚽ اطلاعات اصلی بازی")
    print("=" * 70)
    print()

    print("🆔 Match ID:")
    print(general.get("matchId"))
    print()

    print("🏆 نام مسابقه:")
    print(general.get("matchName"))
    print()

    print("🏟️ لیگ:")
    print(general.get("leagueName"))
    print()

    print("🕐 زمان بازی:")
    print(general.get("matchTimeUTC"))
    print()

    print("▶️ شروع شده:")
    print(general.get("started"))
    print()

    print("🏁 تمام شده:")
    print(general.get("finished"))
    print()

    print("📊 سطح پوشش:")
    print(general.get("coverageLevel"))
    print()

    print("🏠 اطلاعات تیم میزبان:")

    home_team = (
        header.get("teams", {})
        .get("home", {})
    )

    print(home_team)
    print()

    print("✈️ اطلاعات تیم مهمان:")

    away_team = (
        header.get("teams", {})
        .get("away", {})
    )

    print(away_team)
    print()


# ============================================================
# بررسی ترکیب
# ============================================================

def show_lineups(data):

    content = data["content"]

    lineup = content.get("lineup")

    print("=" * 70)
    print("👥 بررسی ترکیب")
    print("=" * 70)
    print()

    if not lineup:
        print("❌ بخش lineup وجود ندارد یا خالی است.")
        print()
        return

    print("✅ بخش lineup وجود دارد.")
    print()

    print("کلیدهای lineup:")
    print(list(lineup.keys()))
    print()

    home = lineup.get("homeTeam")
    away = lineup.get("awayTeam")

    print("🏠 ترکیب میزبان:")
    print(home)
    print()

    print("✈️ ترکیب مهمان:")
    print(away)
    print()


# ============================================================
# بررسی رویدادها
# ============================================================

def show_events(data):

    content = data["content"]

    match_facts = content.get("matchFacts", {})

    print("=" * 70)
    print("📋 بررسی رویدادهای بازی")
    print("=" * 70)
    print()

    print("کلیدهای matchFacts:")

    if match_facts:
        print(list(match_facts.keys()))
    else:
        print("❌ matchFacts وجود ندارد.")

    print()

    events_section = match_facts.get("events", {})

    events = events_section.get("events", [])

    print(f"📌 تعداد رویدادها: {len(events)}")
    print()

    if events:

        for event in events[:20]:

            print(event)

    else:

        print("❌ هنوز رویدادی وجود ندارد.")

    print()


# ============================================================
# بررسی آمار
# ============================================================

def show_stats(data):

    content = data["content"]

    stats = content.get("stats")

    print("=" * 70)
    print("📊 بررسی آمار")
    print("=" * 70)
    print()

    if not stats:
        print("❌ بخش stats وجود ندارد.")
        print()
        return

    print("کلیدهای stats:")
    print(list(stats.keys()))
    print()

    periods = stats.get("Periods", {})

    print("دوره‌های آماری:")

    for period_name in periods.keys():
        print(f"  - {period_name}")

    print()


# ============================================================
# بررسی همه اطلاعات موجود در pageProps
# ============================================================

def show_page_props_keys(root):

    page_props = (
        root
        .get("props", {})
        .get("pageProps", {})
    )

   

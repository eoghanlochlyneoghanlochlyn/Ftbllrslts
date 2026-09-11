import html
import json
import re
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

import requests

from match_cache import (
    add_or_update_match,
    save_matches_cache,
)


# ============================================================
# مسابقات تستی
# ============================================================

TEST_MATCH_IDS = {
    "5868059": "Sevilla vs Valencia",
    "5749679": "Venezia vs Fiorentina",
    "5881169": "Union Berlin vs Schalke 04",
    "5802935": "Rennes vs Marseille",
}


# ============================================================
# اطلاعات ثابت همین چهار مسابقه تستی
#
# این بخش فقط برای تست ساخت کش است.
# در سیستم اصلی، مسابقات از FotMob دریافت می‌شوند.
# ============================================================

TEST_LEAGUES = {
    "5868059": "LaLiga",
    "5749679": "Serie A",
    "5881169": "Bundesliga",
    "5802935": "Ligue 1",
}


# ============================================================
# تنظیمات
# ============================================================

IRAN_TIMEZONE = ZoneInfo("Asia/Tehran")

FOTMOB_MATCH_URL = (
    "https://www.fotmob.com/match/{}"
)

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/140.0.0.0 Safari/537.36"
    ),
    "Accept": (
        "text/html,application/xhtml+xml,"
        "application/xml;q=0.9,image/avif,"
        "image/webp,*/*;q=0.8"
    ),
    "Accept-Language": (
        "en-US,en;q=0.9"
    ),
}

REQUEST_TIMEOUT = 30


# ============================================================
# تبدیل UTC به ساعت ایران
# ============================================================

def utc_to_iran(utc_time):
    if not utc_time:
        return None

    try:
        value = str(
            utc_time
        ).strip()

        dt = datetime.fromisoformat(
            value.replace(
                "Z",
                "+00:00",
            )
        )

        if dt.tzinfo is None:
            dt = dt.replace(
                tzinfo=timezone.utc
            )

        iran_dt = dt.astimezone(
            IRAN_TIMEZONE
        )

        return iran_dt.strftime(
            "%Y-%m-%d %H:%M"
        )

    except Exception as exc:
        print(
            "ERROR converting UTC time "
            f"to Iran time: {exc}"
        )

        return None


# ============================================================
# وضعیت مسابقه
# ============================================================

def get_match_status(match_data):
    if not isinstance(
        match_data,
        dict,
    ):
        return "Upcoming"

    status = match_data.get(
        "status"
    )

    if not isinstance(
        status,
        dict,
    ):
        return "Upcoming"

    if status.get("cancelled"):
        return "Cancelled"

    if status.get("finished"):
        return "Finished"

    if status.get("started"):
        return "Live"

    return "Upcoming"


# ============================================================
# دریافت صفحه مسابقه
# ============================================================

def fetch_match_page(match_id):
    url = FOTMOB_MATCH_URL.format(
        match_id
    )

    print("")
    print(
        f"Fetching: {url}"
    )

    try:
        response = requests.get(
            url,
            headers=HEADERS,
            timeout=REQUEST_TIMEOUT,
        )

        print(
            f"HTTP status: "
            f"{response.status_code}"
        )

        response.raise_for_status()

        return response.text

    except requests.RequestException as exc:
        print(
            f"ERROR fetching match "
            f"{match_id}: {exc}"
        )

        return None


# ============================================================
# استخراج __NEXT_DATA__
# ============================================================

def extract_next_data(page_html):
    if not page_html:
        return None

    match = re.search(
        r'<script[^>]+id=["\']__NEXT_DATA__["\'][^>]*>'
        r'(.*?)'
        r'</script>',
        page_html,
        re.DOTALL | re.IGNORECASE,
    )

    if not match:
        print(
            "ERROR: __NEXT_DATA__ not found."
        )

        return None

    raw_json = html.unescape(
        match.group(1)
    )

    try:
        return json.loads(
            raw_json
        )

    except json.JSONDecodeError as exc:
        print(
            "ERROR parsing __NEXT_DATA__: "
            f"{exc}"
        )

        return None


# ============================================================
# دسترسی امن به مسیر تو در تو
# ============================================================

def get_nested(
    data,
    *keys,
):
    current = data

    for key in keys:
        if not isinstance(
            current,
            dict,
        ):
            return None

        current = current.get(
            key
        )

    return current


# ============================================================
# استخراج eventJSONLD
#
# FotMob اطلاعات پایه مسابقه را در این بخش قرار می‌دهد.
# ============================================================

def get_event_jsonld(root):
    event_jsonld = get_nested(
        root,
        "props",
        "pageProps",
        "seo",
        "eventJSONLD",
    )

    if isinstance(
        event_jsonld,
        dict,
    ):
        return event_jsonld

    # بعضی نسخه‌ها ممکن است JSON-LD را
    # به صورت لیست برگردانند.
    if isinstance(
        event_jsonld,
        list,
    ):
        for item in event_jsonld:
            if not isinstance(
                item,
                dict,
            ):
                continue

            if (
                item.get("@type")
                == "SportsEvent"
            ):
                return item

            if (
                "homeTeam" in item
                and "awayTeam" in item
            ):
                return item

    return None


# ============================================================
# استخراج نام تیم از JSON-LD
# ============================================================

def get_event_team_name(
    team_data
):
    if isinstance(
        team_data,
        dict,
    ):
        return (
            team_data.get("name")
            or team_data.get("alternateName")
        )

    if isinstance(
        team_data,
        str,
    ):
        return team_data

    return None


# ============================================================
# استخراج اطلاعات مسابقه
# ============================================================

def extract_match_info(
    root,
    match_id,
):
    event = get_event_jsonld(
        root
    )

    if not event:
        print(
            "ERROR: eventJSONLD "
            "not found."
        )

        return None

    print(
        "eventJSONLD found."
    )

    # --------------------------------------------------------
    # تیم میزبان
    # --------------------------------------------------------

    home_name = get_event_team_name(
        event.get("homeTeam")
    )

    # --------------------------------------------------------
    # تیم مهمان
    # --------------------------------------------------------

    away_name = get_event_team_name(
        event.get("awayTeam")
    )

    # --------------------------------------------------------
    # زمان شروع
    # --------------------------------------------------------

    utc_time = (
        event.get("startDate")
    )

    # --------------------------------------------------------
    # لیگ
    #
    # برای این تست چهار مسابقه، نام رقابت مشخص است.
    # --------------------------------------------------------

    league = TEST_LEAGUES.get(
        str(match_id)
    )

    # --------------------------------------------------------
    # بررسی اطلاعات ضروری
    # --------------------------------------------------------

    if not home_name:
        print(
            "ERROR: Home team could "
            "not be identified from "
            "eventJSONLD."
        )

        return None

    if not away_name:
        print(
            "ERROR: Away team could "
            "not be identified from "
            "eventJSONLD."
        )

        return None

    if not utc_time:
        print(
            "ERROR: Kickoff time could "
            "not be identified from "
            "eventJSONLD."
        )

        return None

    # --------------------------------------------------------
    # ساعت ایران
    # --------------------------------------------------------

    iran_time = utc_to_iran(
        utc_time
    )

    if not iran_time:
        print(
            "ERROR: Iran time could "
            "not be calculated."
        )

        return None

    # --------------------------------------------------------
    # تاریخ ایران
    # --------------------------------------------------------

    try:
        date_value = datetime.strptime(
            iran_time,
            "%Y-%m-%d %H:%M",
        ).strftime(
            "%Y-%m-%d"
        )

    except Exception:
        date_value = None

    # --------------------------------------------------------
    # رکورد اولیه
    # --------------------------------------------------------

    return {
        "id": str(match_id),
        "date": date_value,
        "league": league,
        "home": home_name,
        "away": away_name,
        "home_id": None,
        "away_id": None,
        "utc_time": utc_time,
        "iran_time": iran_time,
        "status": "Upcoming",
        "score": "-",
        "url": FOTMOB_MATCH_URL.format(
            match_id
        ),
    }


# ============================================================
# نمایش اطلاعات
# ============================================================

def print_match(
    match_id,
    match,
):
    print("")
    print(
        "-" * 70
    )

    print(
        f"Match ID: {match_id}"
    )

    print(
        f"Test name: "
        f"{TEST_MATCH_IDS[match_id]}"
    )

    print(
        f"Actual home: "
        f"{match.get('home')}"
    )

    print(
        f"Actual away: "
        f"{match.get('away')}"
    )

    print(
        f"League: "
        f"{match.get('league')}"
    )

    print(
        f"Date: "
        f"{match.get('date')}"
    )

    print(
        f"UTC time: "
        f"{match.get('utc_time')}"
    )

    print(
        f"Iran time: "
        f"{match.get('iran_time')}"
    )

    print(
        f"Status: "
        f"{match.get('status')}"
    )

    print(
        f"URL: "
        f"{match.get('url')}"
    )

    print(
        "-" * 70
    )


# ============================================================
# پیدا کردن مستقیم مسابقات
# ============================================================

def find_test_matches():
    found_matches = {}

    for match_id in TEST_MATCH_IDS:
        print("")
        print(
            "=" * 70
        )

        print(
            f"Testing match "
            f"{match_id}: "
            f"{TEST_MATCH_IDS[match_id]}"
        )

        print(
            "=" * 70
        )

        # ----------------------------------------------------
        # دریافت صفحه
        # ----------------------------------------------------

        page_html = fetch_match_page(
            match_id
        )

        if not page_html:
            print(
                "Could not download "
                "the match page."
            )

            continue

        # ----------------------------------------------------
        # استخراج NEXT_DATA
        # ----------------------------------------------------

        root = extract_next_data(
            page_html
        )

        if not root:
            print(
                "Could not extract "
                "__NEXT_DATA__."
            )

            continue

        # ----------------------------------------------------
        # استخراج اطلاعات
        # ----------------------------------------------------

        match = extract_match_info(
            root,
            match_id,
        )

        if not match:
            print(
                "Could not extract "
                "match information."
            )

            continue

        # ----------------------------------------------------
        # ذخیره
        # ----------------------------------------------------

        found_matches[
            str(match_id)
        ] = match

        print(
            "MATCH FOUND SUCCESSFULLY"
        )

        print_match(
            match_id,
            match,
        )

    return found_matches


# ============================================================
# ساخت کش تستی
# ============================================================

def main():
    print("")
    print(
        "=" * 70
    )
    print(
        "TEST PRE-MATCH CACHE"
    )
    print(
        "=" * 70
    )

    print("")
    print(
        "Directly checking the four "
        "FotMob match pages..."
    )

    found_matches = (
        find_test_matches()
    )

    # --------------------------------------------------------
    # خلاصه
    # --------------------------------------------------------

    print("")
    print(
        "=" * 70
    )

    print(
        f"Found test matches: "
        f"{len(found_matches)}/"
        f"{len(TEST_MATCH_IDS)}"
    )

    print(
        "=" * 70
    )

    # --------------------------------------------------------
    # بررسی مسابقات گم‌شده
    # --------------------------------------------------------

    missing_matches = []

    for match_id in TEST_MATCH_IDS:
        if match_id not in found_matches:
            missing_matches.append(
                match_id
            )

    if missing_matches:
        print("")
        print(
            "=" * 70
        )

        print(
            "WARNING: Some test matches "
            "were not found."
        )

        print(
            "=" * 70
        )

        for match_id in missing_matches:
            print(
                f"{match_id}: "
                f"{TEST_MATCH_IDS[match_id]}"
            )

        print("")
        print(
            "The cache was NOT changed."
        )

        return

    # --------------------------------------------------------
    # ساخت کش جدید
    #
    # عمداً کش قبلی را نمی‌خوانیم.
    # این تست باید فقط چهار مسابقه را داشته باشد.
    # --------------------------------------------------------

    final_cache = {}

    for match_id in TEST_MATCH_IDS:
        match = found_matches[
            match_id
        ]

        add_or_update_match(
            final_cache,
            match,
        )

    # --------------------------------------------------------
    # ذخیره
    # --------------------------------------------------------

    save_matches_cache(
        final_cache
    )

    # --------------------------------------------------------
    # نتیجه
    # --------------------------------------------------------

    print("")
    print(
        "=" * 70
    )

    print(
        "TEST CACHE CREATED SUCCESSFULLY"
    )

    print(
        "=" * 70
    )

    print("")
    print(
        f"Total cached test matches: "
        f"{len(final_cache)}"
    )

    print("")

    for match_id in TEST_MATCH_IDS:
        match = final_cache[
            match_id
        ]

        print(
            f"{match_id}: "
            f"{match.get('home')} 🆚 "
            f"{match.get('away')} | "
            f"{match.get('status')} | "
            f"{match.get('iran_time')}"
        )

    print("")
    print(
        "=" * 70
    )

    print(
        "matches_cache.json now contains "
        "ONLY the four test matches."
    )

    print(
        "=" * 70
    )


# ============================================================
# اجرا
# ============================================================

if __name__ == "__main__":
    main()

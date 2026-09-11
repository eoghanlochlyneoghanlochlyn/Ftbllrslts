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
        value = str(utc_time).strip()

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
            f"ERROR converting UTC time "
            f"to Iran time: {exc}"
        )

        return None


# ============================================================
# وضعیت مسابقه
# ============================================================

def get_match_status(match_info):
    if not isinstance(
        match_info,
        dict,
    ):
        return "Upcoming"

    status = match_info.get(
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
            f"ERROR parsing __NEXT_DATA__: "
            f"{exc}"
        )

        return None


# ============================================================
# دسترسی امن به مسیر تو در تو
# ============================================================

def get_nested(data, *keys):
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
# استخراج محتوای اصلی FotMob
# ============================================================

def get_content(root):
    content = get_nested(
        root,
        "props",
        "pageProps",
        "content",
    )

    if isinstance(
        content,
        dict,
    ):
        return content

    return {}


# ============================================================
# پیدا کردن مقدار یک کلید در JSON
#
# برای اینکه اگر ساختار FotMob کمی تغییر کرد
# تست کاملاً خراب نشود.
# ============================================================

def find_key_recursive(
    data,
    wanted_key,
):
    if isinstance(
        data,
        dict,
    ):
        if wanted_key in data:
            value = data.get(
                wanted_key
            )

            if value is not None:
                return value

        for value in data.values():
            result = find_key_recursive(
                value,
                wanted_key,
            )

            if result is not None:
                return result

    elif isinstance(
        data,
        list,
    ):
        for item in data:
            result = find_key_recursive(
                item,
                wanted_key,
            )

            if result is not None:
                return result

    return None


# ============================================================
# استخراج اطلاعات مسابقه
# ============================================================

def extract_match_info(
    root,
    match_id,
):
    content = get_content(
        root
    )

    match_info = content.get(
        "match"
    )

    if not isinstance(
        match_info,
        dict,
    ):
        match_info = {}

    # --------------------------------------------------------
    # تیم میزبان
    # --------------------------------------------------------

    home_team = match_info.get(
        "homeTeam"
    )

    if not isinstance(
        home_team,
        dict,
    ):
        home_team = {}

    home_name = (
        home_team.get("name")
        or home_team.get("longName")
        or home_team.get("shortName")
    )

    home_id = home_team.get(
        "id"
    )

    # --------------------------------------------------------
    # تیم مهمان
    # --------------------------------------------------------

    away_team = match_info.get(
        "awayTeam"
    )

    if not isinstance(
        away_team,
        dict,
    ):
        away_team = {}

    away_name = (
        away_team.get("name")
        or away_team.get("longName")
        or away_team.get("shortName")
    )

    away_id = away_team.get(
        "id"
    )

    # --------------------------------------------------------
    # لیگ
    # --------------------------------------------------------

    league = (
        match_info.get(
            "leagueName"
        )
        or content.get(
            "leagueName"
        )
    )

    if not league:
        league_object = (
            match_info.get(
                "league"
            )
        )

        if isinstance(
            league_object,
            dict,
        ):
            league = (
                league_object.get(
                    "name"
                )
                or league_object.get(
                    "leagueName"
                )
            )

    if not league:
        league = "Unknown League"

    # --------------------------------------------------------
    # زمان UTC
    #
    # اول مسیرهای محتمل و شناخته‌شده را بررسی می‌کنیم.
    # --------------------------------------------------------

    utc_time = None

    status_object = match_info.get(
        "status"
    )

    if isinstance(
        status_object,
        dict,
    ):
        utc_time = (
            status_object.get(
                "utcTime"
            )
            or status_object.get(
                "utcDate"
            )
        )

    if not utc_time:
        utc_time = (
            content.get(
                "status",
                {},
            ).get(
                "utcTime"
            )
            if isinstance(
                content.get(
                    "status"
                ),
                dict,
            )
            else None
        )

    if not utc_time:
        utc_time = find_key_recursive(
            match_info,
            "utcTime",
        )

    if not utc_time:
        utc_time = find_key_recursive(
            content,
            "utcTime",
        )

    # --------------------------------------------------------
    # اگر UTC پیدا نشد، eventJSONLD را هم بررسی می‌کنیم.
    # --------------------------------------------------------

    if not utc_time:
        event_json_ld = get_nested(
            root,
            "props",
            "pageProps",
            "seo",
            "eventJSONLD",
        )

        if isinstance(
            event_json_ld,
            dict,
        ):
            utc_time = (
                event_json_ld.get(
                    "startDate"
                )
            )

    # --------------------------------------------------------
    # تاریخ و ساعت ایران
    # --------------------------------------------------------

    iran_time = utc_to_iran(
        utc_time
    )

    # --------------------------------------------------------
    # وضعیت
    # --------------------------------------------------------

    status = get_match_status(
        match_info
    )

    # --------------------------------------------------------
    # امتیاز
    # --------------------------------------------------------

    score = "-"

    home_score = home_team.get(
        "score"
    )

    away_score = away_team.get(
        "score"
    )

    if (
        status in {
            "Finished",
            "Live",
        }
        and home_score is not None
        and away_score is not None
    ):
        score = (
            f"{home_score} - "
            f"{away_score}"
        )

    # --------------------------------------------------------
    # تاریخ
    # --------------------------------------------------------

    date_value = None

    if iran_time:
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
    # رکورد نهایی
    # --------------------------------------------------------

    return {
        "id": str(match_id),
        "date": date_value,
        "league": league,
        "home": home_name or "Unknown",
        "away": away_name or "Unknown",
        "home_id": home_id,
        "away_id": away_id,
        "utc_time": utc_time,
        "iran_time": iran_time,
        "status": status,
        "score": score,
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
        f"Score: "
        f"{match.get('score')}"
    )

    print(
        f"Home ID: "
        f"{match.get('home_id')}"
    )

    print(
        f"Away ID: "
        f"{match.get('away_id')}"
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
        # دریافت مستقیم صفحه مسابقه
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
        # استخراج اطلاعات مسابقه
        # ----------------------------------------------------

        try:
            match = extract_match_info(
                root,
                match_id,
            )

        except Exception as exc:
            print(
                f"ERROR extracting "
                f"match information: {exc}"
            )

            continue

        # ----------------------------------------------------
        # بررسی حداقل اطلاعات ضروری
        # ----------------------------------------------------

        if (
            not match.get("home")
            or match.get("home") == "Unknown"
        ):
            print(
                "WARNING: Home team "
                "could not be identified."
            )

            continue

        if (
            not match.get("away")
            or match.get("away") == "Unknown"
        ):
            print(
                "WARNING: Away team "
                "could not be identified."
            )

            continue

        if not match.get(
            "utc_time"
        ):
            print(
                "WARNING: UTC kickoff "
                "time could not be identified."
            )

            continue

        # ----------------------------------------------------
        # مسابقه معتبر است
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
    # نمایش مسابقات پیدا شده
    # --------------------------------------------------------

    for match_id in TEST_MATCH_IDS:
        if match_id in found_matches:
            print_match(
                match_id,
                found_matches[
                    match_id
                ],
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
    # این تست باید فقط همین چهار مسابقه را داشته باشد.
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

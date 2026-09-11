from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from test_daily_matches import fetch_matches_for_date

from match_cache import (
    load_matches_cache,
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


# ============================================================
# پیدا کردن مسابقات تستی
# ============================================================

def find_test_matches():
    today = datetime.now(
        IRAN_TIMEZONE
    ).date()

    dates = [
        today - timedelta(days=1),
        today,
        today + timedelta(days=1),
    ]

    found_matches = {}

    for current_date in dates:
        date_string = current_date.strftime(
            "%Y%m%d"
        )

        print("")
        print(
            f"Downloading matches for "
            f"{date_string}..."
        )

        try:
            matches = fetch_matches_for_date(
                date_string
            )

        except Exception as exc:
            print(
                f"ERROR downloading "
                f"{date_string}: {exc}"
            )
            continue

        print(
            f"Matches returned: "
            f"{len(matches)}"
        )

        for match in matches:
            match_id = str(
                match.get("id")
            )

            if match_id in TEST_MATCH_IDS:
                found_matches[match_id] = match

    return found_matches


# ============================================================
# نمایش اطلاعات یک مسابقه
# ============================================================

def print_match(match_id, match):
    print("")
    print("-" * 70)

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

    print("-" * 70)


# ============================================================
# ساخت کش تستی
# ============================================================

def main():
    print("")
    print("=" * 70)
    print("TEST PRE-MATCH CACHE")
    print("=" * 70)

    print("")
    print("Searching FotMob for the four test matches...")

    found_matches = find_test_matches()

    print("")
    print("=" * 70)
    print(
        f"Found test matches: "
        f"{len(found_matches)}/"
        f"{len(TEST_MATCH_IDS)}"
    )
    print("=" * 70)

    # --------------------------------------------------------
    # نمایش مسابقات پیدا شده
    # --------------------------------------------------------

    for match_id in TEST_MATCH_IDS:
        if match_id in found_matches:
            print_match(
                match_id,
                found_matches[match_id],
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
        print("=" * 70)
        print("WARNING: Some test matches were not found.")
        print("=" * 70)

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
    # کش فعلی را می‌خوانیم
    # --------------------------------------------------------

    cache = load_matches_cache()

    # --------------------------------------------------------
    # فقط چهار مسابقه تستی را نگه می‌داریم
    # --------------------------------------------------------

    test_cache = {}

    for match_id, match in found_matches.items():
        test_cache[match_id] = match

    # --------------------------------------------------------
    # رکوردها را با ساختار واقعی match_cache.py می‌سازیم
    # --------------------------------------------------------

    final_cache = {}

    for match_id, match in test_cache.items():
        add_or_update_match(
            final_cache,
            match,
        )

    # --------------------------------------------------------
    # ذخیره کش
    # --------------------------------------------------------

    save_matches_cache(
        final_cache
    )

    print("")
    print("=" * 70)
    print("TEST CACHE CREATED SUCCESSFULLY")
    print("=" * 70)

    print("")
    print(
        f"Total cached test matches: "
        f"{len(final_cache)}"
    )

    print("")

    for match_id, match in final_cache.items():
        print(
            f"{match_id}: "
            f"{match.get('home')} 🆚 "
            f"{match.get('away')} | "
            f"{match.get('status')} | "
            f"{match.get('iran_time')}"
        )

    print("")
    print("=" * 70)
    print(
        "matches_cache.json now contains "
        "ONLY the four test matches."
    )
    print("=" * 70)


if __name__ == "__main__":
    main()

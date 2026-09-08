import json
import os
import requests
from datetime import datetime, timezone


# ============================================================
# تنظیمات
# ============================================================

API_KEY = os.getenv("BIGBALLS_API_KEY")

BASE_URL = "https://api.bigballsdata.com/v1"

HEADERS = {
    "Authorization": f"Bearer {API_KEY}"
}

CACHE_FILE = "cache.json"


# ============================================================
# ۱۵ تیم موردنظر
# ============================================================

TRACKED_TEAMS = {
    "Liverpool",
    "Arsenal",
    "Manchester City",
    "Manchester United",
    "Chelsea",
    "Tottenham Hotspur",
    "Juventus",
    "AC Milan",
    "Inter Milan",
    "Bayern Munich",
    "Borussia Dortmund",
    "Paris Saint-Germain",
    "Real Madrid",
    "Barcelona",
    "Atlético Madrid",
}


# ============================================================
# ارتباط با API
# ============================================================

def get_json(url, params=None):

    response = requests.get(
        url,
        headers=HEADERS,
        params=params,
        timeout=30
    )

    response.raise_for_status()

    return response.json()


# ============================================================
# دریافت مسابقات آینده فوتبال
# ============================================================

def get_upcoming_matches():

    response = get_json(
        f"{BASE_URL}/matches",
        params={
            "sport": "football",
            "status": "scheduled",
            "limit": 200
        }
    )

    return response.get("data", [])


# ============================================================
# بارگذاری کش
# ============================================================

def load_cache():

    if not os.path.exists(CACHE_FILE):
        return {}

    try:

        with open(
            CACHE_FILE,
            "r",
            encoding="utf-8"
        ) as file:

            data = json.load(file)

            if isinstance(data, dict):
                return data

    except (json.JSONDecodeError, OSError):

        print("⚠️ فایل cache.json قابل خواندن نیست.")
        print("🔄 کش جدید ساخته می‌شود.")

    return {}


# ============================================================
# ذخیره کش
# ============================================================

def save_cache(cache):

    with open(
        CACHE_FILE,
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            cache,
            file,
            ensure_ascii=False,
            indent=2
        )


# ============================================================
# بررسی اینکه مسابقه مربوط به یکی از ۱۵ تیم هست یا نه
# ============================================================

def get_tracked_team(match):

    home = match.get("home") or {}
    away = match.get("away") or {}

    home_name = home.get("name")
    away_name = away.get("name")

    if home_name in TRACKED_TEAMS:
        return home_name

    if away_name in TRACKED_TEAMS:
        return away_name

    return None


# ============================================================
# حذف مسابقات تکراری بر اساس شناسه مسابقه
# ============================================================

def remove_duplicates(matches):

    unique_matches = {}

    for match in matches:

        match_id = match.get("id")

        if not match_id:
            continue

        unique_matches[match_id] = match

    return list(unique_matches.values())


# ============================================================
# مرتب‌سازی بر اساس زمان شروع
# ============================================================

def sort_by_kickoff(matches):

    def get_time(match):

        kickoff = match.get("kickoff_utc")

        if not kickoff:
            return datetime.max.replace(tzinfo=timezone.utc)

        try:
            return datetime.fromisoformat(
                kickoff.replace("Z", "+00:00")
            )

        except ValueError:
            return datetime.max.replace(
                tzinfo=timezone.utc
            )

    return sorted(
        matches,
        key=get_time
    )


# ============================================================
# اضافه کردن مسابقه جدید به کش
# ============================================================

def add_new_matches(matches, cache):

    new_matches = []

    for match in matches:

        match_id = match.get("id")

        if not match_id:
            continue

        if match_id in cache:
            continue

        home = match.get("home") or {}
        away = match.get("away") or {}

        tracked_team = get_tracked_team(match)

        cache[match_id] = {
            "home": home.get("name"),
            "away": away.get("name"),
            "league": match.get("league"),
            "kickoff_utc": match.get("kickoff_utc"),
            "status": match.get("status"),
            "tracked_team": tracked_team,

            "lineup_sent": False,

            "goals": [],

            "finished": False
        }

        new_matches.append(match)

    return new_matches


# ============================================================
# نمایش مسابقات جدید
# ============================================================

def print_new_matches(matches):

    if not matches:

        print()
        print("ℹ️ مسابقه جدیدی پیدا نشد.")
        return

    print()
    print("=" * 70)
    print("🆕 مسابقات جدید")
    print("=" * 70)

    for match in matches:

        home = match.get("home") or {}
        away = match.get("away") or {}

        print()

        print(
            f"⚽ {home.get('name', '-')} "
            f"vs "
            f"{away.get('name', '-')}"
        )

        print(
            f"🏆 لیگ: "
            f"{match.get('league', '-')}"
        )

        print(
            f"🕐 زمان UTC: "
            f"{match.get('kickoff_utc', '-')}"
        )

        print(
            f"🎯 تیم موردنظر: "
            f"{get_tracked_team(match) or '-'}"
        )

        print(
            f"🆔 شناسه: "
            f"{match.get('id', '-')}"
        )

    print()
    print("=" * 70)


# ============================================================
# اجرای اصلی
# ============================================================

def main():

    if not API_KEY:

        print("❌ BIGBALLS_API_KEY پیدا نشد.")

        raise SystemExit(1)

    print("🔄 دریافت مسابقات آینده فوتبال...")

    try:

        all_matches = get_upcoming_matches()

    except requests.HTTPError as error:

        print()
        print("❌ خطای HTTP:")
        print(error)

        raise SystemExit(1)

    except requests.RequestException as error:

        print()
        print("❌ خطای ارتباط با API:")
        print(error)

        raise SystemExit(1)

    except Exception as error:

        print()
        print("❌ خطای غیرمنتظره:")
        print(error)

        raise SystemExit(1)

    print(
        f"📥 تعداد مسابقات دریافتی از API: "
        f"{len(all_matches)}"
    )

    # --------------------------------------------------------
    # حذف مسابقات تکراری
    # --------------------------------------------------------

    all_matches = remove_duplicates(
        all_matches
    )

    print(
        f"🧹 تعداد مسابقات یکتا: "
        f"{len(all_matches)}"
    )

    # --------------------------------------------------------
    # مرتب‌سازی
    # --------------------------------------------------------

    all_matches = sort_by_kickoff(
        all_matches
    )

    # --------------------------------------------------------
    # فقط مسابقات مربوط به ۱۵ تیم
    # --------------------------------------------------------

    tracked_matches = []

    for match in all_matches:

        if get_tracked_team(match):

            tracked_matches.append(match)

    print(
        f"🎯 مسابقات مربوط به ۱۵ تیم: "
        f"{len(tracked_matches)}"
    )

    # --------------------------------------------------------
    # بارگذاری کش
    # --------------------------------------------------------

    cache = load_cache()

    print(
        f"💾 مسابقات موجود در کش: "
        f"{len(cache)}"
    )

    # --------------------------------------------------------
    # پیدا کردن مسابقات جدید
    # --------------------------------------------------------

    new_matches = add_new_matches(
        tracked_matches,
        cache
    )

    # --------------------------------------------------------
    # ذخیره کش
    # --------------------------------------------------------

    save_cache(cache)

    # --------------------------------------------------------
    # نمایش نتیجه
    # --------------------------------------------------------

    print_new_matches(
        new_matches
    )

    print()
    print(
        f"💾 تعداد مسابقات ذخیره‌شده در کش: "
        f"{len(cache)}"
    )

    print()
    print("=" * 70)
    print("✅ بررسی مسابقات با موفقیت انجام شد.")
    print("=" * 70)


# ============================================================
# اجرا
# ============================================================

if __name__ == "__main__":
    main()

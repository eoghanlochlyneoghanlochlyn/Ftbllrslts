import json
import time
import requests


# ============================================================
# تنظیمات
# ============================================================

BASE_URL = "https://www.fotmob.com"

LEAGUES = {
    "Premier League": 47,
    "Championship": 48,
    "League One": 108,
}

SEASON = "2026/2027"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/140.0.0.0 Safari/537.36"
    ),
    "Accept": "application/json,text/plain,*/*",
    "Referer": "https://www.fotmob.com/",
}


# ============================================================
# درخواست به FotMob
# ============================================================

def fetch_league(league_id):
    """
    اطلاعات لیگ را از endpoint رسمی FotMob می‌گیرد.
    """

    url = f"{BASE_URL}/api/leagues?id={league_id}"

    print()
    print("=" * 70)
    print(f"در حال دریافت لیگ: {league_id}")
    print(f"URL: {url}")

    try:
        response = requests.get(
            url,
            headers=HEADERS,
            timeout=30,
        )

        print(f"HTTP Status: {response.status_code}")

        response.raise_for_status()

        return response.json()

    except Exception as e:
        print(f"❌ خطا در دریافت لیگ {league_id}: {e}")
        return None


# ============================================================
# پیدا کردن لیست تیم‌ها
# ============================================================

def find_team_list(obj):
    """
    به صورت بازگشتی در JSON دنبال ساختارهای محتمل مربوط به
    لیست تیم‌های لیگ می‌گردد.

    چون ساختار داخلی FotMob ممکن است تغییر کند،
    به جای وابستگی به یک مسیر ثابت، چند الگوی رایج را بررسی می‌کنیم.
    """

    if isinstance(obj, dict):

        # کلیدهای محتمل
        for key in (
            "teams",
            "teamList",
            "team_list",
            "standings",
            "table",
        ):
            value = obj.get(key)

            if isinstance(value, list):
                if looks_like_team_list(value):
                    return value

            elif isinstance(value, dict):
                result = find_team_list(value)

                if result:
                    return result

        # جست‌وجوی بازگشتی
        for value in obj.values():
            result = find_team_list(value)

            if result:
                return result

    elif isinstance(obj, list):

        if looks_like_team_list(obj):
            return obj

        for item in obj:
            result = find_team_list(item)

            if result:
                return result

    return None


def looks_like_team_list(items):
    """
    بررسی می‌کند آیا یک لیست واقعاً شامل تیم‌هاست یا نه.
    """

    if not items:
        return False

    team_count = 0

    for item in items:

        if not isinstance(item, dict):
            continue

        # بعضی پاسخ‌های FotMob
        # id / teamId / teamID دارند.
        team_id = (
            item.get("id")
            or item.get("teamId")
            or item.get("teamID")
        )

        name = (
            item.get("name")
            or item.get("teamName")
            or item.get("shortName")
            or item.get("longName")
        )

        if team_id is not None and name:
            team_count += 1

    return team_count >= 2


# ============================================================
# استخراج اطلاعات تیم
# ============================================================

def extract_team(item):
    """
    یک تیم را به ساختار استاندارد خام تبدیل می‌کند.
    """

    if not isinstance(item, dict):
        return None

    team_id = (
        item.get("id")
        or item.get("teamId")
        or item.get("teamID")
    )

    name = (
        item.get("name")
        or item.get("teamName")
        or item.get("shortName")
        or item.get("longName")
    )

    if team_id is None or not name:
        return None

    return {
        "id": str(team_id),
        "name": str(name),
    }


# ============================================================
# حذف تیم‌های تکراری
# ============================================================

def unique_teams(teams):
    """
    تیم‌ها را بر اساس ID یکتا می‌کند.
    """

    result = []
    seen = set()

    for team in teams:

        if not team:
            continue

        team_id = team["id"]

        if team_id in seen:
            continue

        seen.add(team_id)
        result.append(team)

    return result


# ============================================================
# استخراج یک لیگ
# ============================================================

def extract_league_teams(league_name, league_id):
    """
    تمام تیم‌های یک لیگ را استخراج می‌کند.
    """

    data = fetch_league(league_id)

    if data is None:
        return []

    teams_raw = find_team_list(data)

    if not teams_raw:
        print("❌ نتوانستم لیست تیم‌ها را در پاسخ FotMob پیدا کنم.")

        # برای دیباگ، ساختار اصلی را ذخیره می‌کنیم.
        filename = (
            "debug_"
            + league_name.lower()
            .replace(" ", "_")
            .replace("-", "_")
            + ".json"
        )

        with open(
            filename,
            "w",
            encoding="utf-8",
        ) as f:
            json.dump(
                data,
                f,
                ensure_ascii=False,
                indent=2,
            )

        print(f"📁 پاسخ خام در {filename} ذخیره شد.")

        return []

    teams = []

    for item in teams_raw:

        team = extract_team(item)

        if team:
            teams.append(team)

    teams = unique_teams(teams)

    return teams


# ============================================================
# چاپ نتایج
# ============================================================

def print_league(league_name, teams):
    """

    """

    print()
    print("#" * 70)
    print(f"{league_name}")
    print("#" * 70)

    if not teams:
        print("❌ هیچ تیمی پیدا نشد.")
        return

    for index, team in enumerate(teams, start=1):

        print(
            f"{index:2}. "
            f"{team['name']} "
            f"→ {team['id']}"
        )

    print()
    print(f"تعداد تیم‌ها: {len(teams)}")


# ============================================================
# ساخت خروجی نهایی خام
# ============================================================

def build_output(all_leagues):
    """
    خروجی استاندارد برای بررسی دستی.
    """

    output = []

    for league_name, teams in all_leagues.items():

        for team in teams:

            output.append(
                {
                    "id": team["id"],
                    "name": team["name"],
                }
            )

    return output


# ============================================================
# MAIN
# ============================================================

def main():

    print("=" * 70)
    print("FotMob England League Team Extractor")
    print("=" * 70)
    print(f"Season: {SEASON}")
    print()
    print("Leagues:")
    print("1. Premier League")
    print("2. Championship")
    print("3. League One")
    print()

    all_leagues = {}

    for league_name, league_id in LEAGUES.items():

        teams = extract_league_teams(
            league_name,
            league_id,
        )

        all_leagues[league_name] = teams

        print_league(
            league_name,
            teams,
        )

        # کمی فاصله بین درخواست‌ها
        time.sleep(1)

    # ========================================================
    # خلاصه
    # ========================================================

    print()
    print("=" * 70)
    print("SUMMARY")
    print("=" * 70)

    total = 0

    for league_name, teams in all_leagues.items():

        count = len(teams)
        total += count

        print(
            f"{league_name}: {count}"
        )

    print("-" * 70)
    print(f"TOTAL: {total}")

    # ========================================================
    # ذخیره JSON خام
    # ========================================================

    output = build_output(all_leagues)

    with open(
        "england_league_teams_raw.json",
        "w",
        encoding="utf-8",
    ) as f:

        json.dump(
            output,
            f,
            ensure_ascii=False,
            indent=2,
        )

    print()
    print(
        "📁 فایل england_league_teams_raw.json ساخته شد."
    )

    # ========================================================
    # ذخیره ساختار تفکیک‌شده
    # ========================================================

    with open(
        "england_league_teams_by_league.json",
        "w",
        encoding="utf-8",
    ) as f:

        json.dump(
            all_leagues,
            f,
            ensure_ascii=False,
            indent=2,
        )

    print(
        "📁 فایل england_league_teams_by_league.json ساخته شد."
    )

    print()
    print("=" * 70)
    print("پایان")
    print("=" * 70)


if __name__ == "__main__":
    main()

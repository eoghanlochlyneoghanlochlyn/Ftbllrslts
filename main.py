import os
import requests

from football_teams import FOOTBALL_TEAMS
from match_data import get_match_data


# ============================================================
# تنظیمات
# ============================================================

API_KEY = os.getenv("BIGBALLS_API_KEY")

BASE_URL = "https://api.bigballsdata.com/v1"

HEADERS = {
    "Authorization": f"Bearer {API_KEY}"
}


# ============================================================
# درخواست به API
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
# دریافت مسابقات یک تیم
# ============================================================

def get_team_matches(team_id):

    response = get_json(
        f"{BASE_URL}/teams/{team_id}/matches",
        params={
            "sport": "football",
            "limit": 100
        }
    )

    return response.get("data", [])


# ============================================================
# پیدا کردن آخرین مسابقه تمام‌شده یک تیم
# ============================================================

def get_latest_finished_match(team_id):

    matches = get_team_matches(team_id)

    finished_matches = []

    for match in matches:

        if match.get("status") != "finished":
            continue

        home = match.get("home") or {}
        away = match.get("away") or {}

        home_id = home.get("id")
        away_id = away.get("id")

        if team_id not in (home_id, away_id):
            continue

        kickoff = match.get("kickoff_utc")

        if not kickoff:
            continue

        finished_matches.append(match)

    if not finished_matches:
        return None

    finished_matches.sort(
        key=lambda match: match.get("kickoff_utc", ""),
        reverse=True
    )

    return finished_matches[0]


# ============================================================
# پیدا کردن آخرین مسابقه هر 15 تیم
# ============================================================

def find_latest_matches():

    latest_matches = {}

    print()
    print("=" * 70)
    print("🔎 پیدا کردن آخرین مسابقه تمام‌شده هر تیم")
    print("=" * 70)

    for team_name, team_id in FOOTBALL_TEAMS.items():

        try:

            match = get_latest_finished_match(team_id)

            if not match:

                print(
                    f"❌ {team_name} → مسابقه‌ای پیدا نشد."
                )

                continue

            match_id = match.get("id")

            home = match.get("home") or {}
            away = match.get("away") or {}

            score = match.get("score") or {}

            print(
                f"✅ {team_name} → "
                f'{home.get("name", "-")} '
                f'{score.get("home", "-")}-'
                f'{score.get("away", "-")} '
                f'{away.get("name", "-")}'
            )

            latest_matches[team_name] = match

        except requests.RequestException as error:

            print(
                f"❌ {team_name} → خطای ارتباط با API: {error}"
            )

        except Exception as error:

            print(
                f"❌ {team_name} → خطای غیرمنتظره: {error}"
            )

    return latest_matches


# ============================================================
# حذف مسابقات تکراری
# ============================================================

def get_unique_matches(latest_matches):

    unique_matches = {}

    for team_name, match in latest_matches.items():

        match_id = match.get("id")

        if not match_id:
            continue

        if match_id not in unique_matches:

            unique_matches[match_id] = match

    return unique_matches


# ============================================================
# نمایش مسابقات یکتا
# ============================================================

def print_unique_matches(unique_matches):

    print()
    print("=" * 70)
    print(
        f"📋 مسابقات یکتا ({len(unique_matches)})"
    )
    print("=" * 70)

    for match_id, match in unique_matches.items():

        home = match.get("home") or {}
        away = match.get("away") or {}

        score = match.get("score") or {}

        print(
            f'{home.get("name", "-")} '
            f'{score.get("home", "-")}-'
            f'{score.get("away", "-")} '
            f'{away.get("name", "-")}'
        )

        print(
            f'   لیگ: {match.get("league", "-")}'
        )

        print(
            f'   زمان: {match.get("kickoff_utc", "-")}'
        )

        print(
            f'   شناسه: {match_id}'
        )


# ============================================================
# دریافت اطلاعات کامل مسابقات
# ============================================================

def get_all_match_data(unique_matches):

    all_match_data = {}

    print()
    print("=" * 70)
    print("🔄 دریافت اطلاعات کامل مسابقات")
    print("=" * 70)

    for match_id, match in unique_matches.items():

        home = match.get("home") or {}
        away = match.get("away") or {}

        print()
        print(
            f'🔄 {home.get("name", "-")} - '
            f'{away.get("name", "-")}'
        )

        try:

            data = get_match_data(match_id)

            all_match_data[match_id] = data

            print("✅ اطلاعات کامل دریافت شد.")

        except requests.RequestException as error:

            print(
                f"❌ خطای ارتباط با API: {error}"
            )

        except Exception as error:

            print(
                f"❌ خطای غیرمنتظره: {error}"
            )

    return all_match_data


# ============================================================
# اجرای برنامه
# ============================================================

def main():

    if not API_KEY:

        print("❌ BIGBALLS_API_KEY پیدا نشد.")

        raise SystemExit(1)

    print()
    print("=" * 70)
    print("⚽ Football Results Bot")
    print("=" * 70)

    print(
        f"تعداد تیم‌های موردنظر: {len(FOOTBALL_TEAMS)}"
    )

    # --------------------------------------------------------
    # مرحله 1: پیدا کردن آخرین بازی هر تیم
    # --------------------------------------------------------

    latest_matches = find_latest_matches()

    # --------------------------------------------------------
    # مرحله 2: حذف مسابقات تکراری
    # --------------------------------------------------------

    unique_matches = get_unique_matches(
        latest_matches
    )

    print()
    print("=" * 70)
    print("📊 نتیجه انتخاب مسابقات")
    print("=" * 70)

    print(
        f"تیم‌های بررسی‌شده: {len(FOOTBALL_TEAMS)}"
    )

    print(
        f"تیم‌هایی که مسابقه پیدا شد: "
        f"{len(latest_matches)}"
    )

    print(
        f"مسابقات یکتا: {len(unique_matches)}"
    )

    # --------------------------------------------------------
    # نمایش مسابقات
    # --------------------------------------------------------

    print_unique_matches(unique_matches)

    # --------------------------------------------------------
    # مرحله 3: دریافت اطلاعات کامل
    # --------------------------------------------------------

    all_match_data = get_all_match_data(
        unique_matches
    )

    # --------------------------------------------------------
    # نتیجه نهایی
    # --------------------------------------------------------

    print()
    print("=" * 70)
    print("🏁 نتیجه نهایی")
    print("=" * 70)

    print(
        f"تعداد مسابقات یکتا: {len(unique_matches)}"
    )

    print(
        f"تعداد مسابقات دریافت‌شده: "
        f"{len(all_match_data)}"
    )

    if len(all_match_data) == len(unique_matches):

        print()
        print(
            "✅ اطلاعات تمام مسابقات با موفقیت دریافت شد."
        )

    else:

        print()
        print(
            "⚠️ بعضی از مسابقات با موفقیت دریافت نشدند."
        )


# ============================================================
# اجرای مستقیم
# ============================================================

if __name__ == "__main__":
    main()

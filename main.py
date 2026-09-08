import os
import requests

from football_teams import FOOTBALL_TEAMS


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
# پیدا کردن نزدیک‌ترین مسابقه آینده یک تیم
# ============================================================

def get_next_match(team_id):

    matches = get_team_matches(team_id)

    upcoming_matches = []

    for match in matches:

        if match.get("status") != "scheduled":
            continue

        kickoff = match.get("kickoff_utc")

        if not kickoff:
            continue

        home = match.get("home") or {}
        away = match.get("away") or {}

        home_id = home.get("id")
        away_id = away.get("id")

        if team_id not in (home_id, away_id):
            continue

        upcoming_matches.append(match)

    if not upcoming_matches:
        return None

    upcoming_matches.sort(
        key=lambda match: match.get(
            "kickoff_utc",
            ""
        )
    )

    return upcoming_matches[0]


# ============================================================
# پیدا کردن نزدیک‌ترین مسابقه آینده برای تمام تیم‌ها
# ============================================================

def find_next_matches():

    next_matches = {}

    print()
    print("=" * 70)
    print("🔎 پیدا کردن نزدیک‌ترین مسابقه آینده")
    print("=" * 70)

    for team_name, team_id in FOOTBALL_TEAMS.items():

        try:

            match = get_next_match(team_id)

            if not match:

                print(
                    f"❌ {team_name} → "
                    "مسابقه آینده‌ای پیدا نشد."
                )

                continue

            match_id = match.get("id")

            home = match.get("home") or {}
            away = match.get("away") or {}

            print()
            print(
                f"✅ {team_name}"
            )

            print(
                f'   {home.get("name", "-")} '
                f'vs '
                f'{away.get("name", "-")}'
            )

            print(
                f'   لیگ: {match.get("league", "-")}'
            )

            print(
                f'   زمان UTC: '
                f'{match.get("kickoff_utc", "-")}'
            )

            print(
                f'   وضعیت: '
                f'{match.get("status", "-")}'
            )

            print(
                f'   شناسه: {match_id}'
            )

            next_matches[team_name] = match

        except requests.RequestException as error:

            print()
            print(
                f"❌ {team_name} → "
                f"خطای ارتباط با API: {error}"
            )

        except Exception as error:

            print()
            print(
                f"❌ {team_name} → "
                f"خطای غیرمنتظره: {error}"
            )

    return next_matches


# ============================================================
# حذف مسابقات تکراری
# ============================================================

def get_unique_matches(next_matches):

    unique_matches = {}

    for team_name, match in next_matches.items():

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
        f"📋 مسابقات آینده یکتا "
        f"({len(unique_matches)})"
    )
    print("=" * 70)

    for match_id, match in unique_matches.items():

        home = match.get("home") or {}
        away = match.get("away") or {}

        print()
        print(
            f'⚽ {home.get("name", "-")} '
            f'vs '
            f'{away.get("name", "-")}'
        )

        print(
            f'   لیگ: {match.get("league", "-")}'
        )

        print(
            f'   زمان UTC: '
            f'{match.get("kickoff_utc", "-")}'
        )

        print(
            f'   وضعیت: '
            f'{match.get("status", "-")}'
        )

        print(
            f'   شناسه: {match_id}'
        )


# ============================================================
# اجرای برنامه
# ============================================================

def main():

    if not API_KEY:

        print(
            "❌ BIGBALLS_API_KEY پیدا نشد."
        )

        raise SystemExit(1)

    print()
    print("=" * 70)
    print("⚽ Football Results Bot - Stage 3")
    print("=" * 70)

    print(
        f"تعداد تیم‌های موردنظر: "
        f"{len(FOOTBALL_TEAMS)}"
    )

    # --------------------------------------------------------
    # پیدا کردن مسابقه آینده هر تیم
    # --------------------------------------------------------

    next_matches = find_next_matches()

    # --------------------------------------------------------
    # حذف مسابقات تکراری
    # --------------------------------------------------------

    unique_matches = get_unique_matches(
        next_matches
    )

    # --------------------------------------------------------
    # نتیجه
    # --------------------------------------------------------

    print()
    print("=" * 70)
    print("📊 نتیجه")
    print("=" * 70)

    print(
        f"تیم‌های بررسی‌شده: "
        f"{len(FOOTBALL_TEAMS)}"
    )

    print(
        f"تیم‌هایی که مسابقه آینده دارند: "
        f"{len(next_matches)}"
    )

    print(
        f"مسابقات آینده یکتا: "
        f"{len(unique_matches)}"
    )

    # --------------------------------------------------------
    # نمایش مسابقات یکتا
    # --------------------------------------------------------

    print_unique_matches(
        unique_matches
    )

    print()
    print("=" * 70)
    print("✅ مرحله ۳ با موفقیت تمام شد.")
    print("=" * 70)


# ============================================================
# اجرای مستقیم
# ============================================================

if __name__ == "__main__":
    main()

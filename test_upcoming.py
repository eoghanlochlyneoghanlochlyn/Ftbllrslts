import os
import requests


# ============================================================
# تنظیمات
# ============================================================

API_KEY = os.getenv("BIGBALLS_API_KEY")

BASE_URL = "https://api.bigballsdata.com/v1"

TEAM_ID = "74a9c474-32e5-4b48-b9c0-b67122a1617a"

TEAM_NAME = "Liverpool"

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
# دریافت مسابقات تیم
# ============================================================

def get_team_matches(team_id):

    response = get_json(
        f"{BASE_URL}/teams/{team_id}/matches",
        params={
            "sport": "football",
            "limit": 100
        }
    )

    return response


# ============================================================
# نمایش مسابقات آینده
# ============================================================

def print_upcoming_matches(response):

    data = response.get("data", [])

    print()
    print("=" * 70)
    print(f"⚽ مسابقات تیم {TEAM_NAME}")
    print("=" * 70)

    print(
        f"تعداد کل مسابقات دریافت‌شده: {len(data)}"
    )

    upcoming = []

    for match in data:

        status = match.get("status")

        if status == "finished":
            continue

        kickoff = match.get("kickoff_utc")

        if not kickoff:
            continue

        upcoming.append(match)

    upcoming.sort(
        key=lambda match: match.get(
            "kickoff_utc",
            ""
        )
    )

    print()
    print("=" * 70)
    print(
        f"🔮 مسابقات غیرتمام‌شده: {len(upcoming)}"
    )
    print("=" * 70)

    for match in upcoming:

        home = match.get("home") or {}
        away = match.get("away") or {}

        print()
        print(
            f'{home.get("name", "-")} '
            f'vs '
            f'{away.get("name", "-")}'
        )

        print(
            f'لیگ: {match.get("league", "-")}'
        )

        print(
            f'زمان UTC: '
            f'{match.get("kickoff_utc", "-")}'
        )

        print(
            f'وضعیت: '
            f'{match.get("status", "-")}'
        )

        print(
            f'شناسه مسابقه: '
            f'{match.get("id", "-")}'
        )

        print(
            f'اطلاعات میزبان: {home}'
        )

        print(
            f'اطلاعات مهمان: {away}'
        )


# ============================================================
# اجرای تست
# ============================================================

def main():

    if not API_KEY:

        print(
            "❌ BIGBALLS_API_KEY پیدا نشد."
        )

        raise SystemExit(1)

    print(
        "🔄 دریافت مسابقات Liverpool..."
    )

    try:

        response = get_team_matches(
            TEAM_ID
        )

        print()
        print(
            "✅ پاسخ API با موفقیت دریافت شد."
        )

        print_upcoming_matches(
            response
        )

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


# ============================================================
# اجرای مستقیم
# ============================================================

if __name__ == "__main__":
    main()

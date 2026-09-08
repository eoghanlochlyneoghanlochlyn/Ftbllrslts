import os
import requests


# ============================================================
# تنظیمات
# ============================================================

API_KEY = os.getenv("BIGBALLS_API_KEY")

BASE_URL = "https://api.bigballsdata.com/v1"

HEADERS = {
    "Authorization": f"Bearer {API_KEY}"
}


# ============================================================
# دریافت مسابقات فوتبال
# ============================================================

def get_matches():

    response = requests.get(
        f"{BASE_URL}/matches",
        headers=HEADERS,
        params={
            "sport": "football",
            "status": "scheduled",
            "limit": 20
        },
        timeout=30
    )

    response.raise_for_status()

    return response.json()


# ============================================================
# نمایش نتیجه
# ============================================================

def main():

    if not API_KEY:

        print("❌ BIGBALLS_API_KEY پیدا نشد.")

        raise SystemExit(1)

    print("🔄 دریافت مسابقات آینده فوتبال...")

    try:

        response = get_matches()

        data = response.get("data", [])

        print()
        print("=" * 70)
        print("⚽ مسابقات آینده فوتبال")
        print("=" * 70)

        print(
            f"تعداد مسابقات دریافت‌شده: {len(data)}"
        )

        for match in data:

            home = match.get("home") or {}
            away = match.get("away") or {}

            print()
            print(
                f'⚽ {home.get("name", "-")} '
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
                f'شناسه: '
                f'{match.get("id", "-")}'
            )

        print()
        print("=" * 70)
        print("✅ تست با موفقیت انجام شد.")
        print("=" * 70)

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
# اجرا
# ============================================================

if __name__ == "__main__":
    main()

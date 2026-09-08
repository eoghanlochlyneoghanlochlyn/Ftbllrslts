import json
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
# شناسه مسابقه Real Madrid vs Inter Milan
# ============================================================

MATCH_ID = "6df94920-30e2-49f2-b61f-db072cdcfb25"


# ============================================================
# دریافت اطلاعات زنده مسابقه
# ============================================================

def get_live_match():

    response = requests.get(
        f"{BASE_URL}/matches/{MATCH_ID}",
        headers=HEADERS,
        params={
            "sport": "football",
            "fields": "scores,odds,lineups,stats,events"
        },
        timeout=30
    )

    print()
    print("=" * 70)
    print("HTTP STATUS:", response.status_code)
    print("=" * 70)

    response.raise_for_status()

    return response.json()


# ============================================================
# نمایش نتیجه
# ============================================================

def main():

    if not API_KEY:

        print(
            "❌ BIGBALLS_API_KEY پیدا نشد."
        )

        raise SystemExit(1)

    print(
        "🔄 دریافت اطلاعات زنده "
        "Real Madrid vs Inter Milan..."
    )

    try:

        result = get_live_match()

    except requests.HTTPError as error:

        print()
        print("❌ خطای HTTP:")
        print(error)

        return

    except requests.RequestException as error:

        print()
        print("❌ خطای ارتباط با API:")
        print(error)

        return

    print()
    print("=" * 70)
    print("📦 پاسخ کامل API")
    print("=" * 70)

    print(
        json.dumps(
            result,
            ensure_ascii=False,
            indent=2
        )
    )

    # --------------------------------------------------------
    # بررسی lineups
    # --------------------------------------------------------

    data = result.get("data") or {}

    lineups = data.get("lineups")

    print()
    print("=" * 70)
    print("👥 بررسی ترکیب")
    print("=" * 70)

    if lineups is None:

        print(
            "❌ فیلد lineups در پاسخ وجود ندارد."
        )

    else:

        print(
            "✅ فیلد lineups در پاسخ وجود دارد."
        )

        print()
        print(
            json.dumps(
                lineups,
                ensure_ascii=False,
                indent=2
            )
        )

    print()
    print("=" * 70)
    print("✅ تست تمام شد.")
    print("=" * 70)


# ============================================================
# اجرا
# ============================================================

if __name__ == "__main__":
    main()

import json
import requests
from datetime import datetime, timezone


# ============================================================
# تنظیمات
# ============================================================

TEAMS = {
    "Liverpool": 8650,
    "Arsenal": 9825,
    "Manchester City": 8456,
    "Manchester United": 10260,
    "Chelsea": 8455,
    "Tottenham Hotspur": 8586,
    "Juventus": 9885,
    "AC Milan": 8564,
    "Inter Milan": 8636,
    "Bayern Munich": 9823,
    "Borussia Dortmund": 9789,
    "PSG": 9847,
    "Real Madrid": 8633,
    "Barcelona": 8634,
    "Atlético Madrid": 9906,
}


# ============================================================
# دریافت مسابقات فوت‌ماب
# ============================================================

def get_matches(date_string):
    url = (
        "https://www.fotmob.com/api/data/matches"
        f"?date={date_string}"
    )

    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/140.0.0.0 Safari/537.36"
        ),
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "en-US,en;q=0.9",
        "Referer": "https://www.fotmob.com/",
    }

    print(f"🌐 درخواست به فوت‌ماب:")
    print(url)
    print()

    response = requests.get(
        url,
        headers=headers,
        timeout=30
    )

    print(f"📡 HTTP Status: {response.status_code}")
    print()

    response.raise_for_status()

    return response.json()


# ============================================================
# پیدا کردن بازی‌های تیم‌های موردنظر
# ============================================================

def find_target_matches(data):
    found_matches = []

    leagues = data.get("leagues", [])

    print(f"🏆 تعداد لیگ‌ها: {len(leagues)}")
    print()

    for league in leagues:

        league_name = league.get("name", "Unknown League")

        matches = league.get("matches", [])

        for match in matches:

            home = match.get("home", {})
            away = match.get("away", {})

            home_id = home.get("id")
            away_id = away.get("id")

            if home_id in TEAMS.values() or away_id in TEAMS.values():

                found_matches.append({
                    "league": league_name,
                    "match_id": match.get("id"),
                    "home": home.get("name"),
                    "home_id": home_id,
                    "away": away.get("name"),
                    "away_id": away_id,
                    "status": match.get("status"),
                    "finished": match.get("status", {}).get("finished"),
                    "started": match.get("status", {}).get("started"),
                    "utc_time": match.get("status", {}).get("utcTime"),
                })

    return found_matches


# ============================================================
# نمایش نتیجه
# ============================================================

def print_matches(matches):

    print("=" * 70)
    print("⚽ بازی‌های تیم‌های موردنظر")
    print("=" * 70)
    print()

    if not matches:
        print("❌ هیچ بازی‌ای برای تیم‌های موردنظر پیدا نشد.")
        return

    print(f"✅ تعداد بازی‌های پیدا شده: {len(matches)}")
    print()

    for index, match in enumerate(matches, 1):

        print(f"--- بازی {index} ---")

        print(f"🏆 لیگ: {match['league']}")

        print(
            f"⚽ بازی: "
            f"{match['home']} vs {match['away']}"
        )

        print(f"🆔 Match ID: {match['match_id']}")

        print(f"🕐 زمان UTC: {match['utc_time']}")

        print(f"▶️ شروع شده: {match['started']}")

        print(f"🏁 تمام شده: {match['finished']}")

        print()


# ============================================================
# ذخیره نتیجه در فایل JSON
# ============================================================

def save_results(matches):

    with open(
        "fotmob_matches.json",
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            matches,
            file,
            ensure_ascii=False,
            indent=2
        )

    print("💾 نتیجه در فایل fotmob_matches.json ذخیره شد.")


# ============================================================
# اجرای اصلی
# ============================================================

def main():

    # تاریخ امروز به وقت UTC
    today = datetime.now(timezone.utc).strftime("%Y%m%d")

    print("=" * 70)
    print("🔎 تست پیدا کردن مسابقات فوت‌ماب")
    print("=" * 70)
    print()

    print(f"📅 تاریخ مورد بررسی: {today}")
    print()

    try:

        data = get_matches(today)

        print("✅ اطلاعات مسابقات دریافت شد.")
        print()

        matches = find_target_matches(data)

        print_matches(matches)

        save_results(matches)

        print()
        print("=" * 70)
        print("✅ تست با موفقیت تمام شد.")
        print("=" * 70)

    except requests.exceptions.RequestException as error:

        print()
        print("❌ خطا در درخواست به فوت‌ماب:")
        print(error)

    except Exception as error:

        print()
        print("❌ خطای غیرمنتظره:")
        print(error)


if __name__ == "__main__":
    main()

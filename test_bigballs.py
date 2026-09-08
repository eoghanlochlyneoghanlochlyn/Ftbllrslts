import os
import requests
from datetime import datetime


# ============================================================
# تنظیمات
# ============================================================

API_KEY = os.getenv("BIGBALLS_API_KEY")

BASE_URL = "https://api.bigballsdata.com"

HEADERS = {
    "Authorization": f"Bearer {API_KEY}"
}


# ============================================================
# تیم‌ها
# ============================================================

TEAMS = {
    # انگلیس
    "Liverpool": "74a9c474-32e5-4b48-b9c0-b67122a1617a",
    "Arsenal": "d1b0b567-a653-43f6-8d47-d230c447650f",
    "Manchester City": "c12cf38c-1e19-4095-b367-c4ef2a184bb4",
    "Manchester United": "7aa8f8ce-df72-41bd-ac07-d8699514f9e0",
    "Chelsea": "544de6be-906a-40c9-8d32-17ed7239348f",
    "Tottenham Hotspur": "e03f803f-cd23-4db0-a79a-318f58734c7c",

    # ایتالیا
    "Juventus": "1afc40a5-a6a6-41fc-85ff-95ac9c140733",
    "AC Milan": "f6d37fa6-81ad-4c70-bea5-ddde2e839331",
    "Inter Milan": "325dc8ae-18ee-437a-868e-a106b44d5383",

    # آلمان
    "Bayern Munich": "26bff15e-9d29-490a-99bb-d925266acff0",
    "Borussia Dortmund": "aff07d0d-86d0-47e4-858a-94dd2dc96535",

    # فرانسه
    "Paris Saint-Germain": "50bd2f6b-e64f-469b-a4e2-867bfdab0476",

    # اسپانیا
    "Real Madrid": "e0dcfb37-2786-4270-894a-af7c411627f9",
    "Barcelona": "b7fe0fa7-e9ec-4c48-8b15-941b258aeb5d",
    "Atlético Madrid": "9fe82092-5ef1-4101-b8e3-2ab08f41b82e",
}


# ============================================================
# گرفتن مسابقات یک تیم
# ============================================================

def get_team_matches(team_id):

    url = f"{BASE_URL}/v1/teams/{team_id}/matches"

    params = {
        "sport": "football",
        "limit": 200,
    }

    response = requests.get(
        url,
        headers=HEADERS,
        params=params,
        timeout=30,
    )

    if response.status_code != 200:
        print(f"❌ HTTP {response.status_code}")
        print(response.text)
        return None

    try:
        payload = response.json()
    except Exception:
        print("❌ پاسخ API JSON معتبر نیست.")
        return None

    return payload


# ============================================================
# تبدیل تاریخ
# ============================================================

def parse_datetime(value):

    if not value:
        return None

    try:
        return datetime.fromisoformat(
            value.replace("Z", "+00:00")
        )
    except Exception:
        return None


# ============================================================
# پیدا کردن آخرین مسابقه تمام‌شده
# ============================================================

def find_last_finished_match(payload, team_id):

    if not isinstance(payload, dict):
        return None

    matches = payload.get("data")

    if not isinstance(matches, list):
        return None

    finished = []

    for match in matches:

        if not isinstance(match, dict):
            continue

        # ----------------------------------------------------
        # بررسی اینکه تیم واقعاً در مسابقه حضور دارد
        # ----------------------------------------------------

        home = match.get("home") or {}
        away = match.get("away") or {}

        home_id = home.get("id")
        away_id = away.get("id")

        if team_id not in (home_id, away_id):
            continue

        # ----------------------------------------------------
        # فقط مسابقات تمام‌شده
        # ----------------------------------------------------

        if match.get("status") != "finished":
            continue

        # ----------------------------------------------------
        # تاریخ مسابقه
        # ----------------------------------------------------

        kickoff = parse_datetime(
            match.get("kickoff_utc")
        )

        if kickoff is None:
            continue

        finished.append(
            (kickoff, match)
        )

    if not finished:
        return None

    # جدیدترین مسابقه تمام‌شده
    finished.sort(
        key=lambda x: x[0],
        reverse=True
    )

    return finished[0][1]


# ============================================================
# چاپ مسابقه
# ============================================================

def print_match(team_name, match):

    home = match.get("home") or {}
    away = match.get("away") or {}

    home_name = home.get("name", "نامشخص")
    away_name = away.get("name", "نامشخص")

    score = match.get("score") or {}

    home_score = score.get("home")
    away_score = score.get("away")

    print(f"تیم: {team_name}")
    print(f"مسابقه: {home_name} - {away_name}")

    if home_score is not None and away_score is not None:
        print(f"نتیجه: {home_score} - {away_score}")
    else:
        print("نتیجه: نامشخص")

    print(f"لیگ: {match.get('league', 'نامشخص')}")
    print(f"زمان: {match.get('kickoff_utc', 'نامشخص')}")
    print(f"شناسه مسابقه: {match.get('id', 'نامشخص')}")


# ============================================================
# اجرای اصلی
# ============================================================

def main():

    if not API_KEY:
        print("❌ BIGBALLS_API_KEY پیدا نشد.")
        return

    print("=" * 70)
    print("🔎 آخرین مسابقه تمام‌شده ۱۵ تیم")
    print("=" * 70)

    success = 0

    for team_name, team_id in TEAMS.items():

        print()
        print("=" * 70)

        payload = get_team_matches(team_id)

        if payload is None:
            print(f"🏟 تیم: {team_name}")
            print("❌ دریافت اطلاعات ناموفق بود.")
            continue

        match = find_last_finished_match(
            payload,
            team_id
        )

        if match is None:
            print(f"🏟 تیم: {team_name}")
            print("⚠️ هیچ مسابقه تمام‌شده‌ای پیدا نشد.")
            continue

        print_match(
            team_name,
            match
        )

        success += 1

    print()
    print("=" * 70)
    print("✅ پایان تست")
    print("=" * 70)
    print(
        f"موفق: {success} از {len(TEAMS)} تیم"
    )


if __name__ == "__main__":
    main()

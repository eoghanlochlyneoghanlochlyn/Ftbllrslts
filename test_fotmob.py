import json
import os
import time
from datetime import datetime

import requests


# ============================================================
# تنظیمات
# ============================================================

CHECK_INTERVAL = 120  # هر ۲ دقیقه

HALFTIME_WAIT = 15 * 60  # بعد از پایان نیمه اول، ۱۵ دقیقه صبر

REQUEST_TIMEOUT = 20

STATE_FILE = "fotmob_test_state.json"


# ============================================================
# مسابقه‌های آزمایشی
# ============================================================

MATCHES = {
    "5881155": "هامبورگ - ماینتس",
    "5749667": "یوونتوس - میلان",
    "5795435": "آرسنال - چلسی",
    "5868049": "والنسیا - بارسلونا",
}


# ============================================================
# آدرس‌های فوت‌موب
# ============================================================

MATCH_SCORE_URL = (
    "https://www.fotmob.com/api/data/match-score"
)

MATCH_DETAILS_URL = (
    "https://www.fotmob.com/api/data/matchDetails"
)


# ============================================================
# هدر درخواست
# ============================================================

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/139.0.0.0 Safari/537.36"
    ),
    "Accept": "application/json,text/plain,*/*",
    "Referer": "https://www.fotmob.com/",
}


# ============================================================
# ابزارهای عمومی
# ============================================================

def now():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def print_line():
    print("=" * 70)


def safe_get(data, *keys, default=None):
    """
    گرفتن مقدار تو در تو بدون ایجاد خطا.
    """
    current = data

    for key in keys:
        if not isinstance(current, dict):
            return default

        current = current.get(key)

        if current is None:
            return default

    return current


# ============================================================
# ذخیره و بارگذاری وضعیت قبلی
# ============================================================

def load_state():
    if not os.path.exists(STATE_FILE):
        return {}

    try:
        with open(
            STATE_FILE,
            "r",
            encoding="utf-8",
        ) as f:
            return json.load(f)

    except Exception as e:
        print(f"⚠️ خطا در خواندن فایل وضعیت: {e}")
        return {}


def save_state(state):
    try:
        with open(
            STATE_FILE,
            "w",
            encoding="utf-8",
        ) as f:
            json.dump(
                state,
                f,
                ensure_ascii=False,
                indent=2,
            )

    except Exception as e:
        print(f"⚠️ خطا در ذخیره وضعیت: {e}")


# ============================================================
# دریافت وضعیت سبک مسابقه
# ============================================================

def get_match_score(match_id):
    try:
        response = requests.get(
            MATCH_SCORE_URL,
            params={
                "matchId": match_id,
            },
            headers=HEADERS,
            timeout=REQUEST_TIMEOUT,
        )

        print(
            f"   ↳ match-score | "
            f"HTTP {response.status_code}"
        )

        if response.status_code != 200:
            print(
                f"   ❌ خطا در دریافت match-score "
                f"برای {match_id}"
            )
            return None

        return response.json()

    except requests.RequestException as e:
        print(
            f"   ❌ خطای شبکه در match-score: {e}"
        )
        return None

    except ValueError as e:
        print(
            f"   ❌ پاسخ JSON نامعتبر: {e}"
        )
        return None


# ============================================================
# دریافت جزئیات کامل مسابقه
# ============================================================

def get_match_details(match_id):
    try:
        response = requests.get(
            MATCH_DETAILS_URL,
            params={
                "matchId": match_id,
            },
            headers=HEADERS,
            timeout=REQUEST_TIMEOUT,
        )

        print(
            f"   ↳ matchDetails | "
            f"HTTP {response.status_code}"
        )

        if response.status_code != 200:
            print(
                f"   ❌ خطا در دریافت matchDetails "
                f"برای {match_id}"
            )
            return None

        return response.json()

    except requests.RequestException as e:
        print(
            f"   ❌ خطای شبکه در matchDetails: {e}"
        )
        return None

    except ValueError as e:
        print(
            f"   ❌ پاسخ JSON نامعتبر: {e}"
        )
        return None


# ============================================================
# استخراج وضعیت مسابقه
# ============================================================

def extract_status(score_data):
    match = score_data.get("match", {})

    status = match.get("status")

    if isinstance(status, dict):
        return (
            status.get("reason")
            or status.get("name")
            or status.get("short")
            or status.get("long")
            or ""
        )

    if isinstance(status, str):
        return status

    return ""


# ============================================================
# استخراج نتیجه
# ============================================================

def extract_score(score_data):
    match = score_data.get("match", {})

    home_score = (
        match.get("home", {})
        .get("score")
    )

    away_score = (
        match.get("away", {})
        .get("score")
    )

    if home_score is None:
        home_score = match.get("homeScore")

    if away_score is None:
        away_score = match.get("awayScore")

    return home_score, away_score


# ============================================================
# تشخیص نیمه اول
# ============================================================

def is_halftime(status):
    if not status:
        return False

    text = str(status).lower()

    halftime_words = [
        "halftime",
        "half time",
        "half-time",
        "ht",
        "1st half ended",
        "first half ended",
    ]

    for word in halftime_words:
        if word in text:
            return True

    return False


# ============================================================
# تشخیص پایان مسابقه
# ============================================================

def is_finished(status):
    if not status:
        return False

    text = str(status).lower()

    finished_words = [
        "finished",
        "full time",
        "full-time",
        "ft",
        "ended",
        "match ended",
    ]

    for word in finished_words:
        if word in text:
            return True

    return False


# ============================================================
# استخراج رویدادها
# ============================================================

def extract_events(details_data):
    if not details_data:
        return []

    events = details_data.get("content", {}).get(
        "events",
        []
    )

    if not events:
        events = details_data.get("events", [])

    if not isinstance(events, list):
        return []

    return events


# ============================================================
# ساخت شناسه برای رویداد
# ============================================================

def event_identifier(event, index):
    """
    سعی می‌کنیم از شناسه واقعی رویداد استفاده کنیم.
    اگر وجود نداشت، اطلاعات اصلی رویداد را ترکیب می‌کنیم.
    """

    for key in [
        "id",
        "eventId",
        "eventID",
    ]:
        if event.get(key) is not None:
            return str(event[key])

    minute = (
        event.get("time")
        or event.get("minute")
        or event.get("min")
        or ""
    )

    event_type = (
        event.get("type")
        or event.get("eventType")
        or ""
    )

    player = (
        event.get("player", {})
        if isinstance(event.get("player"), dict)
        else {}
    )

    player_id = (
        player.get("id")
        or player.get("name")
        or ""
    )

    return (
        f"{minute}|"
        f"{event_type}|"
        f"{player_id}|"
        f"{index}"
    )


# ============================================================
# نمایش رویدادهای جدید
# ============================================================

def print_new_events(
    match_name,
    match_id,
    events,
    previous_event_ids,
):
    new_events = []

    for index, event in enumerate(events):
        if not isinstance(event, dict):
            continue

        event_id = event_identifier(
            event,
            index,
        )

        if event_id not in previous_event_ids:
            new_events.append(
                (
                    event_id,
                    event,
                )
            )

    if not new_events:
        return previous_event_ids

    print()
    print("   🆕 رویداد جدید:")

    for event_id, event in new_events:
        print()
        print(
            f"   ┌─ {match_name}"
        )

        print(
            f"   │ شناسه مسابقه: {match_id}"
        )

        print(
            f"   │ رویداد: "
            f"{json.dumps(event, ensure_ascii=False)}"
        )

        print("   └────────────────────────")

        previous_event_ids.append(event_id)

    return previous_event_ids


# ============================================================
# بررسی یک مسابقه
# ============================================================

def check_match(
    match_id,
    match_name,
    state,
):
    print()
    print_line()

    print(
        f"⚽ {match_name}"
    )

    print(
        f"🆔 شناسه: {match_id}"
    )

    print(
        f"🕐 زمان بررسی: {now()}"
    )

    print_line()

    # --------------------------------------------------------
    # دریافت وضعیت سبک
    # --------------------------------------------------------

    score_data = get_match_score(match_id)

    if score_data is None:
        print(
            "❌ اطلاعات مسابقه دریافت نشد."
        )

        return state, False

    status = extract_status(score_data)

    home_score, away_score = extract_score(
        score_data
    )

    print(
        f"📊 وضعیت: {status or 'نامشخص'}"
    )

    print(
        f"⚽ نتیجه: "
        f"{home_score if home_score is not None else '?'}"
        f" - "
        f"{away_score if away_score is not None else '?'}"
    )

    # --------------------------------------------------------
    # وضعیت قبلی
    # --------------------------------------------------------

    previous_status = state.get(
        "status",
        "",
    )

    previous_home_score = state.get(
        "home_score"
    )

    previous_away_score = state.get(
        "away_score"
    )

    # --------------------------------------------------------
    # تشخیص تغییر نتیجه
    # --------------------------------------------------------

    if (
        previous_home_score is not None
        and previous_away_score is not None
        and (
            home_score != previous_home_score
            or away_score != previous_away_score
        )
    ):
        print()
        print(
            "🚨 نتیجه تغییر کرده است!"
        )

        print(
            f"   قبلی: "
            f"{previous_home_score} - "
            f"{previous_away_score}"
        )

        print(
            f"   جدید: "
            f"{home_score} - "
            f"{away_score}"
        )

    # --------------------------------------------------------
    # تشخیص تغییر وضعیت
    # --------------------------------------------------------

    if (
        previous_status
        and status
        and status != previous_status
    ):
        print()
        print(
            "🔄 وضعیت مسابقه تغییر کرده:"
        )

        print(
            f"   قبلی: {previous_status}"
        )

        print(
            f"   جدید: {status}"
        )

    # --------------------------------------------------------
    # دریافت جزئیات کامل
    # --------------------------------------------------------

    details_data = get_match_details(
        match_id
    )

    events = extract_events(
        details_data
    )

    print(
        f"📋 تعداد رویدادهای دریافت‌شده: "
        f"{len(events)}"
    )

    # --------------------------------------------------------
    # رویدادهای قبلی
    # --------------------------------------------------------

    previous_event_ids = state.get(
        "event_ids",
        [],
    )

    if not isinstance(previous_event_ids, list):
        previous_event_ids = []

    previous_event_ids = print_new_events(
        match_name,
        match_id,
        events,
        previous_event_ids,
    )

    # --------------------------------------------------------
    # ذخیره وضعیت
    # --------------------------------------------------------

    state["status"] = status

    state["home_score"] = home_score
    state["away_score"] = away_score

    state["event_ids"] = previous_event_ids

    state["last_check"] = now()

    # --------------------------------------------------------
    # تشخیص نیمه اول
    # --------------------------------------------------------

    halftime_detected = is_halftime(
        status
    )

    if halftime_detected:
        print()
        print(
            "⏸️ پایان نیمه اول تشخیص داده شد."
        )

        print(
            "⏳ این مسابقه تا ۱۵ دقیقه "
            "دیگر بررسی نمی‌شود."
        )

    # --------------------------------------------------------
    # تشخیص پایان مسابقه
    # --------------------------------------------------------

    if is_finished(status):
        print()
        print(
            "🏁 مسابقه به پایان رسیده است."
        )

    return state, halftime_detected


# ============================================================
# برنامه اصلی
# ============================================================

def main():
    print()
    print_line()

    print(
        "⚽ آزمایش دریافت اطلاعات مسابقات فوت‌موب"
    )

    print(
        f"🕐 فاصله بررسی: "
        f"{CHECK_INTERVAL // 60} دقیقه"
    )

    print(
        "⏸️ توقف بین دو نیمه: ۱۵ دقیقه"
    )

    print_line()

    print()
    print("مسابقه‌های تحت نظر:")

    for match_id, match_name in MATCHES.items():
        print(
            f"  • {match_name} "
            f"({match_id})"
        )

    print()

    # --------------------------------------------------------
    # بارگذاری وضعیت قبلی
    # --------------------------------------------------------

    state = load_state()

    if not state:
        print(
            "ℹ️ فایل وضعیت قبلی وجود ندارد."
        )

    else:
        print(
            "✅ وضعیت قبلی بارگذاری شد."
        )

    # --------------------------------------------------------
    # نگهداری زمان آزاد شدن مسابقه‌های نیمه‌تمام
    # --------------------------------------------------------

    halftime_until = {}

    # --------------------------------------------------------
    # حلقه اصلی
    # --------------------------------------------------------

    while True:
        cycle_start = time.time()

        print()
        print()
        print("█" * 70)

        print(
            f"🔎 شروع دور جدید بررسی: {now()}"
        )

        print("█" * 70)

        for match_id, match_name in MATCHES.items():

            # ------------------------------------------------
            # بررسی اینکه مسابقه در زمان استراحت است یا نه
            # ------------------------------------------------

            if match_id in halftime_until:
                release_time = halftime_until[
                    match_id
                ]

                if time.time() < release_time:
                    remaining = int(
                        release_time
                        - time.time()
                    )

                    minutes = remaining // 60
                    seconds = remaining % 60

                    print()
                    print_line()

                    print(
                        f"⏸️ {match_name}"
                    )

                    print(
                        "   هنوز در استراحت بین دو نیمه است."
                    )

                    print(
                        f"   ⏳ زمان باقی‌مانده: "
                        f"{minutes:02d}:{seconds:02d}"
                    )

                    print_line()

                    continue

                else:
                    print()
                    print(
                        f"▶️ استراحت ۱۵ دقیقه‌ای "
                        f"{match_name} تمام شد."
                    )

                    del halftime_until[
                        match_id
                    ]

            # ------------------------------------------------
            # اطمینان از وجود وضعیت مسابقه
            # ------------------------------------------------

            if match_id not in state:
                state[match_id] = {}

            # ------------------------------------------------
            # بررسی مسابقه
            # ------------------------------------------------

            new_state, halftime_detected = (
                check_match(
                    match_id,
                    match_name,
                    state[match_id],
                )
            )

            state[match_id] = new_state

            # ------------------------------------------------
            # اگر نیمه اول تمام شده
            # ------------------------------------------------

            if halftime_detected:
                halftime_until[match_id] = (
                    time.time()
                    + HALFTIME_WAIT
                )

        # ----------------------------------------------------
        # ذخیره وضعیت تمام مسابقه‌ها
        # ----------------------------------------------------

        save_state(state)

        # ----------------------------------------------------
        # محاسبه زمان لازم تا بررسی بعدی
        # ----------------------------------------------------

        elapsed = time.time() - cycle_start

        sleep_time = max(
            1,
            CHECK_INTERVAL - elapsed,
        )

        print()
        print_line()

        print(
            f"✅ این دور بررسی تمام شد."
        )

        print(
            f"🕐 زمان پایان: {now()}"
        )

        print(
            f"⏳ بررسی بعدی حدود "
            f"{int(sleep_time)} ثانیه دیگر."
        )

        print_line()

        try:
            time.sleep(
                sleep_time
            )

        except KeyboardInterrupt:
            print()
            print()
            print(
                "🛑 برنامه توسط کاربر متوقف شد."
            )

            save_state(state)

            break


# ============================================================
# اجرای برنامه
# ============================================================

if __name__ == "__main__":
    main()

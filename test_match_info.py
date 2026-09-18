import os
import time

from event_detector import get_goal_info

from state_manager import (
    default_match_state,
    add_goal,
    set_goal_message_id,
)

from main import process_updated_goal


TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAMBOT")
TELEGRAM_CHANNEL = os.getenv("TELEGRAMCHANNEL")


def assert_equal(actual, expected, message):
    if actual != expected:
        raise AssertionError(
            f"{message}\n"
            f"Expected: {expected!r}\n"
            f"Actual:   {actual!r}"
        )


def assert_true(value, message):
    if not value:
        raise AssertionError(message)


def main():

    print("=" * 60)
    print("TBD GOAL -> REAL TELEGRAM EDIT TEST")
    print("=" * 60)

    # ========================================================
    # بررسی تنظیمات Telegram
    # ========================================================

    if not TELEGRAM_BOT_TOKEN:
        raise RuntimeError(
            "TELEGRAMBOT environment variable is not set."
        )

    if not TELEGRAM_CHANNEL:
        raise RuntimeError(
            "TELEGRAMCHANNEL environment variable is not set."
        )

    print()
    print("Telegram configuration found.")
    print("Channel:", TELEGRAM_CHANNEL)

    # ========================================================
    # Import مستقیم توابع Telegram
    # ========================================================

    from telegram_sender import (
        send_rich_message,
        edit_rich_message,
    )

    # ========================================================
    # مرحله 1
    # گل اولیه با <TBD>
    # ========================================================

    first_event = {
        "id": 123456,
        "type": "Goal",
        "minute": 37,
        "isHome": True,
        "playerName": "<TBD>",
    }

    match_state = default_match_state()

    first_goal_info = get_goal_info(
        first_event
    )

    assert_true(
        first_goal_info is not None,
        "مرحله 1: گل اولیه شناسایی نشد."
    )

    goal = add_goal(
        match_state,
        first_goal_info,
    )

    assert_true(
        goal is not None,
        "مرحله 1: گل در state ثبت نشد."
    )

    print()
    print("PASS 1: گل اولیه با <TBD> ساخته شد.")

    # ========================================================
    # مرحله 2
    # ارسال واقعی پیام به Telegram
    # ========================================================

    first_rich_message = {
        "markdown": (
            "⚽️ گل\n"
            "برای **Test Home**!\n"
            "⏱ دقیقه 37\n"
            "<TBD>\n"
            "\n"
            "Test Home 1 🆚 0 Test Away"
        )
    }

    print()
    print("Sending REAL Telegram message...")
    print("مهم: این مرحله واقعاً یک پیام در کانال می‌فرستد.")

    response = send_rich_message(
        first_rich_message
    )

    print()
    print("Telegram send response:")
    print(response)

    assert_true(
        isinstance(response, dict),
        "مرحله 2: پاسخ Telegram معتبر نیست."
    )

    assert_true(
        response.get("ok") is True,
        "مرحله 2: Telegram ارسال پیام را قبول نکرد."
    )

    result = response.get("result")

    assert_true(
        isinstance(result, dict),
        "مرحله 2: result در پاسخ Telegram وجود ندارد."
    )

    message_id = result.get(
        "message_id"
    )

    assert_true(
        message_id is not None,
        "مرحله 2: Telegram message_id برنگرداند."
    )

    message_id = int(
        message_id
    )

    set_goal_message_id(
        match_state,
        "id:123456",
        message_id,
    )

    print()
    print("PASS 2: پیام واقعی Telegram ارسال شد.")
    print("       message_id =", message_id)

    # ========================================================
    # مرحله 3
    # FotMob اطلاعات گل را کامل می‌کند
    # ========================================================

    second_event = {
        "id": 123456,
        "type": "Goal",
        "minute": 37,
        "isHome": True,
        "playerId": 9876,
        "playerName": "Test Player",
    }

    updated_goal_info = get_goal_info(
        second_event
    )

    assert_true(
        updated_goal_info is not None,
        "مرحله 3: گل به‌روزشده شناسایی نشد."
    )

    assert_equal(
        updated_goal_info["event_key"],
        "id:123456",
        "مرحله 3: event_key تغییر کرده است."
    )

    assert_equal(
        updated_goal_info["player_name"],
        "Test Player",
        "مرحله 3: نام واقعی بازیکن شناسایی نشد."
    )

    print()
    print("PASS 3: همان گل با نام واقعی دریافت شد.")
    print("       player_name = Test Player")

    # ========================================================
    # مرحله 4
    # ویرایش واقعی همان پیام Telegram
    # ========================================================

    snapshot = {
        "home": "Test Home",
        "away": "Test Away",
        "score": {
            "home": 1,
            "away": 0,
        },
    }

    print()
    print("Waiting 2 seconds before editing...")
    time.sleep(2)

    print()
    print("Editing REAL Telegram message...")
    print("message_id =", message_id)

    result = process_updated_goal(
        snapshot,
        match_state,
        updated_goal_info,
    )

    print()
    print("process_updated_goal returned:")
    print(result)

    assert_true(
        result is True,
        "مرحله 4: process_updated_goal موفق نبود."
    )

    # ========================================================
    # مرحله 5
    # بررسی state
    # ========================================================

    final_goal = match_state["goals"][0]

    assert_equal(
        final_goal["player_name"],
        "Test Player",
        "مرحله 5: نام واقعی در state ذخیره نشده."
    )

    assert_equal(
        final_goal["player_id"],
        9876,
        "مرحله 5: player_id ذخیره نشده."
    )

    assert_equal(
        final_goal["telegram_message_id"],
        message_id,
        "مرحله 5: message_id تغییر کرده."
    )

    assert_equal(
        final_goal["needs_update"],
        False,
        "مرحله 5: needs_update بعد از edit موفق باید False باشد."
    )

    assert_equal(
        len(match_state["goals"]),
        1,
        "مرحله 5: گل تکراری ایجاد شده."
    )

    print()
    print("PASS 5: state بعد از ویرایش Telegram صحیح است.")

    print()
    print("       player_name =",
          final_goal["player_name"])

    print(
        "       player_id =",
        final_goal["player_id"],
    )

    print(
        "       message_id =",
        final_goal["telegram_message_id"],
    )

    print(
        "       needs_update =",
        final_goal["needs_update"],
    )

    # ========================================================
    # نتیجه
    # ========================================================

    print()
    print("=" * 60)
    print("REAL TELEGRAM TEST PASSED")
    print("=" * 60)

    print()
    print("نتیجه:")
    print("1. پیام واقعی با <TBD> به Telegram ارسال شد.")
    print("2. Telegram یک message_id واقعی برگرداند.")
    print("3. همان message_id داخل state ذخیره شد.")
    print("4. اطلاعات همان گل با نام Test Player کامل شد.")
    print("5. همان پیام واقعی Telegram ویرایش شد.")
    print("6. message_id تغییر نکرد.")
    print("7. needs_update = False شد.")
    print("8. گل تکراری ایجاد نشد.")

    print()
    print(
        "پیام آزمایشی را در کانال بررسی کن؛ "
        "باید نام <TBD> به Test Player تغییر کرده باشد."
    )


if __name__ == "__main__":
    main()

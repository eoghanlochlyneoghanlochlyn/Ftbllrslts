from unittest.mock import patch

from event_detector import get_goal_info

from state_manager import (
    default_match_state,
    add_goal,
    set_goal_message_id,
)

from main import process_updated_goal


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
    print("TBD GOAL -> TELEGRAM EDIT TEST")
    print("=" * 60)

    # ========================================================
    # مرحله 1
    # گل ابتدا با نام ناقص از FotMob می‌آید.
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

    # فرض می‌کنیم پیام واقعی تلگرام قبلاً ارسال شده
    # و Telegram message_id = 500 بوده است.

    set_goal_message_id(
        match_state,
        "id:123456",
        500,
    )

    assert_equal(
        goal["player_name"],
        "<TBD>",
        "مرحله 1: نام اولیه گل اشتباه است."
    )

    assert_equal(
        goal["telegram_message_id"],
        500,
        "مرحله 1: message_id ذخیره نشده است."
    )

    assert_true(
        goal["needs_update"] is True,
        "مرحله 1: needs_update باید True باشد."
    )

    print("PASS 1: گل اولیه با <TBD> ثبت شد.")
    print("       message_id = 500")
    print("       needs_update = True")

    # ========================================================
    # مرحله 2
    # FotMob همان event را با نام واقعی برمی‌گرداند.
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
        "مرحله 2: گل به‌روزشده شناسایی نشد."
    )

    assert_equal(
        updated_goal_info["event_key"],
        "id:123456",
        "مرحله 2: event_key تغییر کرده است."
    )

    assert_equal(
        updated_goal_info["player_name"],
        "Test Player",
        "مرحله 2: نام واقعی بازیکن تشخیص داده نشد."
    )

    print("PASS 2: همان event با نام واقعی دریافت شد.")

    # ========================================================
    # مرحله 3
    # خود main.py را تست می‌کنیم.
    #
    # edit_rich_message را Mock می‌کنیم تا هیچ درخواست واقعی
    # به Telegram ارسال نشود.
    # ========================================================

    snapshot = {
        "home": "Test Home",
        "away": "Test Away",
        "score": {
            "home": 1,
            "away": 0,
        },
    }

    fake_telegram_response = {
        "ok": True,
        "result": {
            "message_id": 500,
        },
    }

    with patch(
        "main.edit_rich_message"
    ) as mock_edit:

        mock_edit.return_value = (
            fake_telegram_response
        )

        result = process_updated_goal(
            snapshot,
            match_state,
            updated_goal_info,
        )

        assert_true(
            result is True,
            "مرحله 3: process_updated_goal موفق نبود."
        )

        assert_equal(
            mock_edit.call_count,
            1,
            "مرحله 3: edit_rich_message باید دقیقاً یک بار فراخوانی شود."
        )

        call_args = (
            mock_edit.call_args
        )

        assert_true(
            call_args is not None,
            "مرحله 3: هیچ فراخوانی برای edit_rich_message ثبت نشد."
        )

        actual_message_id = (
            call_args.args[0]
        )

        actual_payload = (
            call_args.args[1]
        )

        assert_equal(
            actual_message_id,
            500,
            "مرحله 3: edit باید روی همان message_id قبلی انجام شود."
        )

        assert_true(
            isinstance(
                actual_payload,
                dict,
            ),
            "مرحله 3: payload ویرایش باید dict باشد."
        )

        assert_true(
            "markdown" in actual_payload,
            "مرحله 3: payload باید شامل markdown باشد."
        )

        print(
            "PASS 3: edit_rich_message فراخوانی شد."
        )

        print(
            "       message_id =",
            actual_message_id,
        )

        print(
            "       payload =",
            actual_payload,
        )

    # ========================================================
    # مرحله 4
    # بررسی کنیم state بعد از edit درست شده باشد.
    # ========================================================

    final_goal = match_state["goals"][0]

    assert_equal(
        final_goal["player_name"],
        "Test Player",
        "مرحله 4: نام واقعی در state ذخیره نشده است."
    )

    assert_equal(
        final_goal["player_id"],
        9876,
        "مرحله 4: player_id واقعی ذخیره نشده است."
    )

    assert_equal(
        final_goal["telegram_message_id"],
        500,
        "مرحله 4: message_id قبلی تغییر کرده است."
    )

    assert_equal(
        final_goal["needs_update"],
        False,
        "مرحله 4: بعد از edit موفق needs_update باید False شود."
    )

    assert_equal(
        len(match_state["goals"]),
        1,
        "مرحله 4: نباید گل دوم ایجاد شده باشد."
    )

    print(
        "PASS 4: state بعد از ویرایش صحیح است."
    )

    print(
        "       player_name =",
        final_goal["player_name"],
    )

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
    print("ALL TESTS PASSED")
    print("=" * 60)
    print()
    print("زنجیره کامل با موفقیت تست شد:")
    print("1. گل با <TBD> ثبت شد.")
    print("2. message_id قبلی ذخیره شد.")
    print("3. همان event با نام واقعی دریافت شد.")
    print("4. main.py آن را به‌عنوان گل جدید نفرستاد.")
    print("5. edit_rich_message با همان message_id فراخوانی شد.")
    print("6. نام بازیکن به‌روزرسانی شد.")
    print("7. needs_update بعد از edit موفق False شد.")
    print("8. هیچ گل تکراری ایجاد نشد.")


if __name__ == "__main__":
    main()

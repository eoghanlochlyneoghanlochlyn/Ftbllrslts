from event_detector import (
    detect_updated_goals,
    get_goal_info,
)

from state_manager import (
    default_match_state,
    add_goal,
    set_goal_message_id,
)


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
    print("TBD GOAL UPDATE TEST")
    print("=" * 60)

    # --------------------------------------------------------
    # مرحله 1:
    # FotMob ابتدا همان گل را بدون نام بازیکن برمی‌گرداند.
    # --------------------------------------------------------

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
        "مرحله اول: گل توسط get_goal_info تشخیص داده نشد."
    )

    assert_equal(
        first_goal_info["event_key"],
        "id:123456",
        "مرحله اول: event_key اشتباه است."
    )

    assert_equal(
        first_goal_info["player_name"],
        "<TBD>",
        "مرحله اول: نام اولیه گل اشتباه است."
    )

    # ثبت گل در state
    goal = add_goal(
        match_state,
        first_goal_info,
    )

    assert_true(
        goal is not None,
        "مرحله اول: گل در state ثبت نشد."
    )

    assert_equal(
        len(match_state["goals"]),
        1,
        "مرحله اول: تعداد گل‌های ثبت‌شده اشتباه است."
    )

    assert_equal(
        goal["player_name"],
        "<TBD>",
        "مرحله اول: نام بازیکن باید TBD باشد."
    )

    assert_true(
        goal["needs_update"] is True,
        "مرحله اول: needs_update باید True باشد."
    )

    # فرض می‌کنیم پیام گل در تلگرام با موفقیت ارسال شده
    # و شناسه پیام 500 است.
    set_goal_message_id(
        match_state,
        "id:123456",
        500,
    )

    assert_equal(
        goal["telegram_message_id"],
        500,
        "مرحله اول: telegram_message_id ذخیره نشد."
    )

    print("PASS 1: گل اولیه با <TBD> ثبت شد.")
    print("       needs_update = True")
    print("       telegram_message_id = 500")

    # --------------------------------------------------------
    # مرحله 2:
    # FotMob همان event را دوباره می‌فرستد،
    # اما این بار نام واقعی بازیکن آمده است.
    # --------------------------------------------------------

    second_event = {
        "id": 123456,
        "type": "Goal",
        "minute": 37,
        "isHome": True,
        "playerId": 9876,
        "playerName": "Test Player",
    }

    updated_goals = detect_updated_goals(
        match_state,
        [second_event],
    )

    assert_equal(
        len(updated_goals),
        1,
        "مرحله دوم: گل به‌روزشده شناسایی نشد."
    )

    updated_goal_info = updated_goals[0]

    assert_equal(
        updated_goal_info["event_key"],
        "id:123456",
        "مرحله دوم: event_key گل تغییر کرده است."
    )

    assert_equal(
        updated_goal_info["player_id"],
        9876,
        "مرحله دوم: player_id جدید تشخیص داده نشد."
    )

    assert_equal(
        updated_goal_info["player_name"],
        "Test Player",
        "مرحله دوم: نام واقعی بازیکن تشخیص داده نشد."
    )

    print("PASS 2: کامل‌شدن اطلاعات همان گل تشخیص داده شد.")

    # --------------------------------------------------------
    # مرحله 3:
    # اطلاعات کامل‌شده را دوباره به state بده.
    #
    # add_goal باید همان گل قبلی را پیدا کند و به‌روزرسانی کند،
    # نه اینکه گل دوم بسازد.
    # --------------------------------------------------------

    updated_goal = add_goal(
        match_state,
        updated_goal_info,
    )

    assert_true(
        updated_goal is goal,
        "مرحله سوم: add_goal یک object جدید برای گل ساخت."
    )

    assert_equal(
        len(match_state["goals"]),
        1,
        "مرحله سوم: یک گل تکراری ایجاد شده است."
    )

    assert_equal(
        updated_goal["player_id"],
        9876,
        "مرحله سوم: player_id در state به‌روزرسانی نشد."
    )

    assert_equal(
        updated_goal["player_name"],
        "Test Player",
        "مرحله سوم: نام واقعی بازیکن در state ذخیره نشد."
    )

    assert_equal(
        updated_goal["telegram_message_id"],
        500,
        "مرحله سوم: telegram_message_id قبلی از بین رفته است."
    )

    assert_true(
        updated_goal["needs_update"] is True,
        "مرحله سوم: needs_update باید برای ویرایش پیام True باشد."
    )

    print("PASS 3: همان گل به‌روزرسانی شد و گل تکراری ساخته نشد.")
    print("       player_name = Test Player")
    print("       player_id = 9876")
    print("       telegram_message_id = 500")
    print("       needs_update = True")

    # --------------------------------------------------------
    # مرحله 4:
    # بررسی نهایی اینکه کل زنجیره دقیقاً چیزی است که می‌خواهیم.
    # --------------------------------------------------------

    final_goal = match_state["goals"][0]

    assert_equal(
        final_goal["event_key"],
        "id:123456",
        "مرحله نهایی: event_key اشتباه است."
    )

    assert_equal(
        final_goal["player_name"],
        "Test Player",
        "مرحله نهایی: نام بازیکن صحیح نیست."
    )

    assert_equal(
        final_goal["player_id"],
        9876,
        "مرحله نهایی: player_id صحیح نیست."
    )

    assert_equal(
        final_goal["telegram_message_id"],
        500,
        "مرحله نهایی: شناسه پیام تلگرام حفظ نشده است."
    )

    assert_equal(
        len(match_state["goals"]),
        1,
        "مرحله نهایی: تعداد گل‌ها باید دقیقاً 1 باشد."
    )

    print()
    print("=" * 60)
    print("ALL TESTS PASSED")
    print("=" * 60)
    print()
    print("نتیجه:")
    print("1. گل با <TBD> ثبت شد.")
    print("2. همان event با نام واقعی دوباره دریافت شد.")
    print("3. event_detector آن را به‌عنوان گل جدید تشخیص نداد.")
    print("4. اطلاعات همان گل به‌روزرسانی شد.")
    print("5. telegram_message_id قبلی حفظ شد.")
    print("6. گل تکراری ایجاد نشد.")


if __name__ == "__main__":
    main()

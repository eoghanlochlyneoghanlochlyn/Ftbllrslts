import json
import re
import requests


URL = "https://www.fotmob.com"


def extract_data(html):
    """
    پیدا کردن script حاوی اطلاعات رقابت‌ها
    """

    scripts = re.findall(
        r"<script[^>]*>(.*?)</script>",
        html,
        re.DOTALL
    )

    for script in scripts:

        if (
            "TournamentPrefixes" not in script
            and "TournamentTemplates" not in script
        ):
            continue

        try:
            return json.loads(script)

        except json.JSONDecodeError:
            continue

    return None


def find_competition_data(obj):
    """
    پیدا کردن آبجکتی که اطلاعات رقابت‌ها را دارد.
    """

    if isinstance(obj, dict):

        if (
            "TournamentPrefixes" in obj
            or "TournamentTemplates" in obj
        ):
            return obj

        for value in obj.values():

            result = find_competition_data(value)

            if result is not None:
                return result

    elif isinstance(obj, list):

        for item in obj:

            result = find_competition_data(item)

            if result is not None:
                return result

    return None


def print_value(title, value, max_items=30):
    """
    چاپ ساختار داده بدون ایجاد لاگ خیلی بزرگ.
    """

    print("\n")
    print("=" * 70)
    print(title)
    print("=" * 70)

    if isinstance(value, dict):

        print(
            "نوع: dict"
        )

        print(
            "تعداد:",
            len(value)
        )

        print(
            "\nنمونه داده:"
        )

        for index, (key, item) in enumerate(
            value.items()
        ):

            if index >= max_items:

                print(
                    f"... و {len(value) - max_items} مورد دیگر"
                )

                break

            if isinstance(item, dict):

                print(
                    f"{key} | dict | "
                    f"keys={list(item.keys())[:20]}"
                )

            elif isinstance(item, list):

                print(
                    f"{key} | list | "
                    f"count={len(item)}"
                )

            else:

                print(
                    f"{key} | {item}"
                )

    elif isinstance(value, list):

        print(
            "نوع: list"
        )

        print(
            "تعداد:",
            len(value)
        )

        print(
            "\nنمونه داده:"
        )

        for index, item in enumerate(
            value[:max_items]
        ):

            if isinstance(item, dict):

                print(
                    f"[{index}] dict | "
                    f"keys={list(item.keys())[:20]}"
                )

            elif isinstance(item, list):

                print(
                    f"[{index}] list | "
                    f"count={len(item)}"
                )

            else:

                print(
                    f"[{index}] {item}"
                )

        if len(value) > max_items:

            print(
                f"... و {len(value) - max_items} مورد دیگر"
            )

    else:

        print(
            "نوع:",
            type(value).__name__
        )

        print(
            value
        )


def inspect_dict_structure(obj, path="root", depth=0, max_depth=4):
    """
    پیدا کردن مسیرهای مربوط به CountryCodes و Participants
    و نمایش ساختار داخلی آنها.
    """

    if depth > max_depth:
        return

    if isinstance(obj, dict):

        for key, value in obj.items():

            current_path = f"{path}.{key}"

            if key in {
                "CountryCodes",
                "Participants"
            }:

                print(
                    "\n"
                    + "-" * 70
                )

                print(
                    "FOUND:",
                    current_path
                )

                print(
                    "-" * 70
                )

                print_value(
                    current_path,
                    value,
                    max_items=20
                )

            inspect_dict_structure(
                value,
                current_path,
                depth + 1,
                max_depth
            )

    elif isinstance(obj, list):

        for index, item in enumerate(obj[:20]):

            inspect_dict_structure(
                item,
                f"{path}[{index}]",
                depth + 1,
                max_depth
            )


def main():

    print(
        "در حال دریافت اطلاعات از FotMob..."
    )

    try:

        response = requests.get(
            URL,
            headers={
                "User-Agent": (
                    "Mozilla/5.0 "
                    "(Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 "
                    "(KHTML, like Gecko) "
                    "Chrome/140.0 Safari/537.36"
                )
            },
            timeout=30
        )

        print(
            "Status:",
            response.status_code
        )

        print(
            "Length:",
            len(response.text)
        )

        if response.status_code != 200:

            print(
                "\n❌ دریافت صفحه FotMob ناموفق بود."
            )

            return

        print(
            "\nدر حال استخراج JSON..."
        )

        data = extract_data(
            response.text
        )

        if data is None:

            print(
                "\n❌ داده اصلی پیدا نشد."
            )

            return

        print(
            "✅ داده اصلی پیدا شد."
        )

        competition_data = find_competition_data(
            data
        )

        if competition_data is None:

            print(
                "\n❌ بخش اطلاعات رقابت‌ها پیدا نشد."
            )

            return

        print(
            "✅ بخش اطلاعات رقابت‌ها پیدا شد."
        )

        # --------------------------------------------------
        # اطلاعات مستقیم
        # --------------------------------------------------

        country_codes = competition_data.get(
            "CountryCodes"
        )

        participants = competition_data.get(
            "Participants"
        )

        tournament_prefixes = competition_data.get(
            "TournamentPrefixes"
        )

        # --------------------------------------------------
        # CountryCodes
        # --------------------------------------------------

        print_value(
            "COUNTRY CODES",
            country_codes,
            max_items=40
        )

        # --------------------------------------------------
        # Participants
        # --------------------------------------------------

        print_value(
            "PARTICIPANTS",
            participants,
            max_items=40
        )

        # --------------------------------------------------
        # بررسی ساختار داخلی
        # --------------------------------------------------

        print(
            "\n"
            + "=" * 70
        )

        print(
            "بررسی مسیرهای CountryCodes و Participants"
        )

        print(
            "=" * 70
        )

        inspect_dict_structure(
            data
        )

        # --------------------------------------------------
        # نمونه TournamentPrefixes
        # --------------------------------------------------

        print(
            "\n"
            + "=" * 70
        )

        print(
            "نمونه TournamentPrefixes"
        )

        print(
            "=" * 70
        )

        if isinstance(
            tournament_prefixes,
            dict
        ):

            for index, (
                tournament_id,
                tournament_name
            ) in enumerate(
                tournament_prefixes.items()
            ):

                if index >= 20:
                    break

                print(
                    tournament_id,
                    "|",
                    tournament_name
                )

        print(
            "\n"
            + "=" * 70
        )

        print(
            "پایان تست"
        )

        print(
            "=" * 70
        )

    except requests.RequestException as e:

        print(
            "\n❌ خطا در ارتباط با FotMob:"
        )

        print(
            repr(e)
        )

    except Exception as e:

        print(
            "\n❌ خطای غیرمنتظره:"
        )

        print(
            repr(e)
        )


if __name__ == "__main__":
    main()

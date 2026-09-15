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


def find_paths(obj, target_keys, path="root"):
    """
    تمام مسیرهایی را که کلیدهای موردنظر در JSON دارند پیدا می‌کند.
    """

    results = []

    if isinstance(obj, dict):

        for key, value in obj.items():

            current_path = f"{path}.{key}"

            if key in target_keys:

                results.append(
                    (current_path, value)
                )

            results.extend(
                find_paths(
                    value,
                    target_keys,
                    current_path
                )
            )

    elif isinstance(obj, list):

        for index, item in enumerate(obj):

            current_path = f"{path}[{index}]"

            results.extend(
                find_paths(
                    item,
                    target_keys,
                    current_path
                )
            )

    return results


def print_value_sample(value, max_items=10):
    """
    چاپ نمونه‌ای کوچک از داده،
    تا لاگ GitHub بیش از حد بزرگ نشود.
    """

    if isinstance(value, dict):

        print(
            f"نوع: dict | تعداد: {len(value)}"
        )

        for i, (key, item) in enumerate(value.items()):

            if i >= max_items:
                print(
                    f"... و {len(value) - max_items} مورد دیگر"
                )
                break

            if isinstance(item, (dict, list)):

                print(
                    f"{key} | "
                    f"{type(item).__name__} | "
                    f"{len(item)} مورد"
                )

            else:

                print(
                    f"{key} | {item}"
                )

    elif isinstance(value, list):

        print(
            f"نوع: list | تعداد: {len(value)}"
        )

        for i, item in enumerate(value[:max_items]):

            if isinstance(item, dict):

                print(
                    f"[{i}] dict | "
                    f"کلیدها: {list(item.keys())[:20]}"
                )

            else:

                print(
                    f"[{i}] {item}"
                )

        if len(value) > max_items:

            print(
                f"... و {len(value) - max_items} مورد دیگر"
            )

    else:

        print(
            f"نوع: {type(value).__name__}"
        )

        print(value)


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

            print(
                response.text[:2000]
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

        print(
            "\n"
            + "=" * 70
        )

        print(
            "جستجوی اطلاعات کشور / منطقه / رقابت"
        )

        print(
            "=" * 70
        )

        target_keys = {
            "Country",
            "Countries",
            "CountryName",
            "CountryId",
            "Region",
            "Regions",
            "RegionName",
            "RegionId",
            "League",
            "Leagues",
            "LeagueName",
            "LeagueId",
            "Tournament",
            "Tournaments",
            "Tournament",
            "TournamentId",
            "TournamentName",
            "Competition",
            "Competitions",
            "CompetitionId",
            "CompetitionName",
        }

        results = find_paths(
            data,
            target_keys
        )

        print(
            "\nتعداد مسیرهای پیدا شده:",
            len(results)
        )

        if not results:

            print(
                "\n⚠️ هیچ‌کدام از کلیدهای موردنظر پیدا نشد."
            )

            print(
                "\nدر حال بررسی کلیدهای سطح داده رقابت‌ها..."
            )

            print(
                "\nکلیدهای موجود:"
            )

            for key in competition_data.keys():

                print(
                    "-",
                    key
                )

            return

        shown = set()

        for path, value in results:

            """
            بعضی کلیدها ممکن است چند بار
            در ساختار تودرتو ظاهر شوند.
            """

            if path in shown:
                continue

            shown.add(path)

            print(
                "\n"
                + "-" * 70
            )

            print(
                "PATH:",
                path
            )

            print(
                "-" * 70
            )

            print_value_sample(
                value,
                max_items=15
            )

        print(
            "\n"
            + "=" * 70
        )

        print(
            "بررسی ساختار مستقیم بخش رقابت‌ها"
        )

        print(
            "=" * 70
        )

        for key, value in competition_data.items():

            key_lower = key.lower()

            if any(
                word in key_lower
                for word in [
                    "country",
                    "region",
                    "league",
                    "tournament",
                    "competition",
                    "sport"
                ]
            ):

                print(
                    "\n"
                    + "-" * 70
                )

                print(
                    "KEY:",
                    key
                )

                print(
                    "-" * 70
                )

                print_value_sample(
                    value,
                    max_items=15
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

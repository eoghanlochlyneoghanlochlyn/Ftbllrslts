import json
import re
import requests


URL = "https://www.fotmob.com"

TARGET_IDS = {
    "38",
    "40",
    "42",
    "45",
    "246",
}


def extract_data(html):
    """
    پیدا کردن script اصلی حاوی JSON
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


def value_preview(value, max_length=500):
    """
    تبدیل مقدار به متن کوتاه برای لاگ
    """

    try:

        text = json.dumps(
            value,
            ensure_ascii=False
        )

    except Exception:

        text = str(value)

    if len(text) > max_length:

        return text[:max_length] + " ..."

    return text


def search_target_ids(obj, path="root", depth=0, max_depth=8):
    """
    تمام جاهایی که یکی از شناسه‌های هدف دیده می‌شود را پیدا می‌کند.

    فقط ساختار JSON را بررسی می‌کنیم.
    """

    if depth > max_depth:

        return

    if isinstance(obj, dict):

        for key, value in obj.items():

            current_path = f"{path}.{key}"

            # --------------------------------------------------
            # اگر خود کلید یکی از IDهای هدف باشد
            # --------------------------------------------------

            if str(key) in TARGET_IDS:

                print()
                print("=" * 80)
                print("🎯 شناسه پیدا شد")
                print("=" * 80)

                print(
                    "ID:",
                    key
                )

                print(
                    "مسیر:",
                    current_path
                )

                print(
                    "نوع مقدار:",
                    type(value).__name__
                )

                print(
                    "مقدار:"
                )

                print(
                    value_preview(
                        value,
                        1200
                    )
                )

            # --------------------------------------------------
            # اگر مقدار دقیقاً یکی از IDهای هدف باشد
            # --------------------------------------------------

            if isinstance(
                value,
                (str, int)
            ):

                if str(value) in TARGET_IDS:

                    print()
                    print("-" * 80)

                    print(
                        "🔎 مقدار شناسه پیدا شد"
                    )

                    print(
                        "ID:",
                        value
                    )

                    print(
                        "مسیر:",
                        current_path
                    )

                    print(
                        "کلید:",
                        key
                    )

                    print(
                        "والد:"
                    )

                    print(
                        value_preview(
                            obj,
                            1500
                        )
                    )

            # --------------------------------------------------
            # ادامه جستجو
            # --------------------------------------------------

            search_target_ids(
                value,
                current_path,
                depth + 1,
                max_depth
            )

    elif isinstance(obj, list):

        for index, item in enumerate(obj):

            current_path = f"{path}[{index}]"

            # --------------------------------------------------
            # اگر خود آیتم یکی از IDها باشد
            # --------------------------------------------------

            if isinstance(
                item,
                (str, int)
            ):

                if str(item) in TARGET_IDS:

                    print()
                    print("-" * 80)

                    print(
                        "🔎 شناسه داخل لیست پیدا شد"
                    )

                    print(
                        "ID:",
                        item
                    )

                    print(
                        "مسیر:",
                        current_path
                    )

            # --------------------------------------------------
            # ادامه جستجو
            # --------------------------------------------------

            search_target_ids(
                item,
                current_path,
                depth + 1,
                max_depth
            )


def inspect_relevant_objects(
    obj,
    path="root",
    depth=0,
    max_depth=8
):
    """
    دنبال آبجکت‌هایی می‌گردد که کلیدهای مرتبط
    با رقابت، لیگ، کشور یا تورنمنت دارند.
    """

    if depth > max_depth:

        return

    relevant_keys = {
        "league",
        "leagueId",
        "leagueName",
        "tournament",
        "tournamentId",
        "tournamentName",
        "country",
        "countryCode",
        "countryName",
        "region",
        "regionName",
        "competition",
        "competitionId",
        "competitionName",
    }

    if isinstance(obj, dict):

        found_keys = [
            key
            for key in obj.keys()
            if key in relevant_keys
        ]

        if found_keys:

            print()
            print("=" * 80)
            print("📌 آبجکت مرتبط پیدا شد")
            print("=" * 80)

            print(
                "مسیر:",
                path
            )

            print(
                "کلیدهای مرتبط:",
                found_keys
            )

            print(
                "داده:"
            )

            print(
                value_preview(
                    obj,
                    2000
                )
            )

        for key, value in obj.items():

            inspect_relevant_objects(
                value,
                f"{path}.{key}",
                depth + 1,
                max_depth
            )

    elif isinstance(obj, list):

        for index, item in enumerate(obj[:100]):

            inspect_relevant_objects(
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

            print()
            print(
                "❌ دریافت صفحه FotMob ناموفق بود."
            )

            return

        print()
        print(
            "در حال استخراج JSON..."
        )

        data = extract_data(
            response.text
        )

        if data is None:

            print()
            print(
                "❌ JSON اصلی پیدا نشد."
            )

            return

        print(
            "✅ داده اصلی پیدا شد."
        )

        # ------------------------------------------------------
        # تست اول:
        # پیدا کردن خود IDها
        # ------------------------------------------------------

        print()
        print("=" * 80)
        print(
            "جستجوی شناسه‌های رقابت"
        )
        print("=" * 80)

        print(
            "شناسه‌های مورد جستجو:",
            ", ".join(
                sorted(
                    TARGET_IDS,
                    key=int
                )
            )
        )

        search_target_ids(
            data
        )

        # ------------------------------------------------------
        # تست دوم:
        # پیدا کردن آبجکت‌های مرتبط
        # ------------------------------------------------------

        print()
        print("=" * 80)
        print(
            "جستجوی آبجکت‌های دارای اطلاعات رقابت / کشور"
        )
        print("=" * 80)

        inspect_relevant_objects(
            data
        )

        # ------------------------------------------------------
        # پایان
        # ------------------------------------------------------

        print()
        print("=" * 80)
        print(
            "پایان تست"
        )
        print("=" * 80)

    except requests.RequestException as e:

        print()
        print(
            "❌ خطا در ارتباط با FotMob:"
        )

        print(
            repr(e)
        )

    except Exception as e:

        print()
        print(
            "❌ خطای غیرمنتظره:"
        )

        print(
            repr(e)
        )


if __name__ == "__main__":

    main()

import json
import re
import requests


TEST_PAGES = {
    "Bundesliga": "https://www.fotmob.com/leagues/54/overview/bundesliga",
    "Serie A": "https://www.fotmob.com/leagues/55/overview/serie-a",
    "Belgian First Division A": "https://www.fotmob.com/leagues/40/overview/belgian-first-division-a",
    "Champions League": "https://www.fotmob.com/leagues/42/overview/champions-league",
}


HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 "
        "(Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 "
        "(KHTML, like Gecko) "
        "Chrome/140.0 Safari/537.36"
    )
}


def extract_json_scripts(html):
    """
    تمام scriptهای JSON موجود در صفحه را استخراج می‌کند.
    """

    scripts = re.findall(
        r"<script[^>]*>(.*?)</script>",
        html,
        re.DOTALL
    )

    results = []

    for script in scripts:

        script = script.strip()

        if not script:
            continue

        try:

            data = json.loads(
                script
            )

            results.append(
                data
            )

        except json.JSONDecodeError:

            continue

    return results


def find_objects_with_keys(
    obj,
    wanted_keys,
    path="root",
    depth=0,
    max_depth=10
):
    """
    آبجکت‌هایی را پیدا می‌کند که حداقل یکی از کلیدهای موردنظر را دارند.
    """

    if depth > max_depth:
        return

    if isinstance(obj, dict):

        matched_keys = [
            key
            for key in obj.keys()
            if key in wanted_keys
        ]

        if matched_keys:

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
                matched_keys
            )

            print(
                "\nداده:"
            )

            try:

                print(
                    json.dumps(
                        obj,
                        ensure_ascii=False,
                        indent=2
                    )[:5000]
                )

            except Exception:

                print(
                    str(obj)[:5000]
                )

        for key, value in obj.items():

            find_objects_with_keys(
                value,
                wanted_keys,
                f"{path}.{key}",
                depth + 1,
                max_depth
            )

    elif isinstance(obj, list):

        for index, item in enumerate(obj[:100]):

            find_objects_with_keys(
                item,
                wanted_keys,
                f"{path}[{index}]",
                depth + 1,
                max_depth
            )


def find_values(
    obj,
    wanted_keys,
    path="root",
    depth=0,
    max_depth=10
):
    """
    تمام مقادیر مربوط به کلیدهای مهم را پیدا می‌کند.
    """

    if depth > max_depth:
        return

    if isinstance(obj, dict):

        for key, value in obj.items():

            current_path = (
                f"{path}.{key}"
            )

            if key in wanted_keys:

                print()
                print("-" * 80)

                print(
                    "🔎 فیلد پیدا شد:",
                    key
                )

                print(
                    "مسیر:",
                    current_path
                )

                print(
                    "مقدار:"
                )

                try:

                    print(
                        json.dumps(
                            value,
                            ensure_ascii=False,
                            indent=2
                        )[:3000]
                    )

                except Exception:

                    print(
                        str(value)[:3000]
                    )

            find_values(
                value,
                wanted_keys,
                current_path,
                depth + 1,
                max_depth
            )

    elif isinstance(obj, list):

        for index, item in enumerate(obj[:100]):

            find_values(
                item,
                wanted_keys,
                f"{path}[{index}]",
                depth + 1,
                max_depth
            )


def test_page(
    page_name,
    url
):
    """
    یک صفحه لیگ را بررسی می‌کند.
    """

    print()
    print()
    print("#" * 80)
    print(
        f"🏆 بررسی: {page_name}"
    )
    print("#" * 80)

    print(
        "URL:",
        url
    )

    try:

        response = requests.get(
            url,
            headers=HEADERS,
            timeout=30
        )

    except requests.RequestException as e:

        print()
        print(
            "❌ خطا در دریافت صفحه:"
        )

        print(
            repr(e)
        )

        return

    print()
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
            "❌ صفحه با موفقیت دریافت نشد."
        )

        return

    print()
    print(
        "در حال استخراج JSONها..."
    )

    json_objects = extract_json_scripts(
        response.text
    )

    print(
        "تعداد JSONهای معتبر:",
        len(json_objects)
    )

    if not json_objects:

        print()
        print(
            "❌ هیچ JSON معتبری پیدا نشد."
        )

        return

    # ----------------------------------------------------------
    # کلیدهای مهم
    # ----------------------------------------------------------

    wanted_keys = {
        "leagueId",
        "leagueName",
        "league",
        "tournamentId",
        "tournamentName",
        "tournament",
        "competitionId",
        "competitionName",
        "competition",
        "countryCode",
        "country",
        "countryName",
        "region",
        "regionName",
        "name",
        "id",
    }

    # ----------------------------------------------------------
    # جستجوی فیلدهای مهم
    # ----------------------------------------------------------

    print()
    print("=" * 80)
    print(
        "جستجوی فیلدهای مربوط به لیگ / تورنمنت / کشور"
    )
    print("=" * 80)

    for index, data in enumerate(
        json_objects
    ):

        print()
        print(
            f"--- JSON شماره {index + 1} ---"
        )

        find_values(
            data,
            {
                "leagueId",
                "leagueName",
                "tournamentId",
                "tournamentName",
                "competitionId",
                "competitionName",
                "countryCode",
                "countryName",
                "region",
                "regionName",
            }
        )

    # ----------------------------------------------------------
    # آبجکت‌های مرتبط
    # ----------------------------------------------------------

    print()
    print("=" * 80)
    print(
        "جستجوی آبجکت‌های مرتبط"
    )
    print("=" * 80)

    for index, data in enumerate(
        json_objects
    ):

        print()
        print(
            f"--- JSON شماره {index + 1} ---"
        )

        find_objects_with_keys(
            data,
            wanted_keys
        )


def main():

    print(
        "شروع تست صفحات واقعی رقابت‌های FotMob"
    )

    print(
        "تعداد صفحات:",
        len(TEST_PAGES)
    )

    for page_name, url in TEST_PAGES.items():

        test_page(
            page_name,
            url
        )

    print()
    print()
    print("#" * 80)
    print(
        "پایان تست"
    )
    print("#" * 80)


if __name__ == "__main__":

    main()

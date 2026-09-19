import json
import requests


LEAGUE_ID = 42
SEASON = "2026/2027"

URL = (
    "https://www.fotmob.com/api/data/leagues"
    f"?id={LEAGUE_ID}"
    f"&season={SEASON}"
)


SEARCH_WORDS = (
    "stage",
    "round",
    "knockout",
    "playoff",
    "play-off",
    "leg",
    "aggregate",
    "bracket",
    "phase",
)


def get_nested_value(node, path="root", results=None):
    if results is None:
        results = []

    if isinstance(node, dict):

        for key, value in node.items():

            key_lower = str(key).lower()

            if any(word in key_lower for word in SEARCH_WORDS):

                results.append(
                    {
                        "path": f"{path}.{key}",
                        "value": value,
                    }
                )

            if isinstance(value, (dict, list)):

                get_nested_value(
                    value,
                    f"{path}.{key}",
                    results,
                )

    elif isinstance(node, list):

        for index, item in enumerate(node):

            if isinstance(item, (dict, list)):

                get_nested_value(
                    item,
                    f"{path}[{index}]",
                    results,
                )

    return results


def print_structure(node, path="root", depth=0, max_depth=5):
    if depth > max_depth:
        return

    indent = "  " * depth

    if isinstance(node, dict):

        for key, value in node.items():

            print(
                f"{indent}{key}: "
                f"{type(value).__name__}"
            )

            if isinstance(value, (dict, list)):

                print_structure(
                    value,
                    f"{path}.{key}",
                    depth + 1,
                    max_depth,
                )

    elif isinstance(node, list):

        print(
            f"{indent}[list] length={len(node)}"
        )

        for index, item in enumerate(node[:10]):

            print(
                f"{indent}  [{index}]: "
                f"{type(item).__name__}"
            )

            if isinstance(item, (dict, list)):

                print_structure(
                    item,
                    f"{path}[{index}]",
                    depth + 1,
                    max_depth,
                )


def main():

    print("=" * 100)
    print("FotMob Competition Structure Test")
    print("=" * 100)

    print()
    print(f"League ID: {LEAGUE_ID}")
    print(f"Season: {SEASON}")
    print(f"URL: {URL}")
    print()

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
            timeout=30,
        )

    except Exception as exc:

        print(
            f"Request error: {exc}"
        )

        return

    print(
        f"HTTP status: {response.status_code}"
    )

    print(
        f"Response length: {len(response.text)}"
    )

    print()

    if response.status_code != 200:

        print(
            "صفحه معتبر دریافت نشد."
        )

        print(
            response.text[:1000]
        )

        return

    try:

        data = response.json()

    except Exception as exc:

        print(
            f"JSON decode error: {exc}"
        )

        print(
            response.text[:1000]
        )

        return

    if not isinstance(data, dict):

        print(
            "پاسخ JSON یک dictionary نیست."
        )

        return

    # ------------------------------------------------------------------
    # اطلاعات اصلی رقابت
    # ------------------------------------------------------------------

    print("=" * 100)
    print("1. ROOT KEYS")
    print("=" * 100)

    print(
        json.dumps(
            list(data.keys()),
            ensure_ascii=False,
            indent=2,
        )
    )

    print()

    # ------------------------------------------------------------------
    # details
    # ------------------------------------------------------------------

    print("=" * 100)
    print("2. DETAILS")
    print("=" * 100)

    details = data.get("details")

    if isinstance(details, dict):

        print(
            json.dumps(
                details,
                ensure_ascii=False,
                indent=2,
            )
        )

    else:

        print(
            "details پیدا نشد."
        )

    print()

    # ------------------------------------------------------------------
    # seasons
    # ------------------------------------------------------------------

    print("=" * 100)
    print("3. SEASONS")
    print("=" * 100)

    seasons = data.get("seasons")

    if isinstance(seasons, list):

        print(
            json.dumps(
                seasons,
                ensure_ascii=False,
                indent=2,
            )
        )

    else:

        print(
            "seasons پیدا نشد."
        )

    print()

    # ------------------------------------------------------------------
    # ساختار کلیدهای مهم
    # ------------------------------------------------------------------

    print("=" * 100)
    print("4. STRUCTURAL KEYS")
    print("=" * 100)

    results = get_nested_value(data)

    print(
        f"تعداد موارد پیدا شده: {len(results)}"
    )

    print()

    for index, item in enumerate(results, start=1):

        print(
            f"[{index}] PATH:"
        )

        print(
            item["path"]
        )

        print(
            "VALUE:"
        )

        try:

            print(
                json.dumps(
                    item["value"],
                    ensure_ascii=False,
                    indent=2,
                )
            )

        except Exception:

            print(
                repr(item["value"])
            )

        print("-" * 100)

    # ------------------------------------------------------------------
    # فقط ساختار سطح اول برای فهم راحت‌تر
    # ------------------------------------------------------------------

    print()
    print("=" * 100)
    print("5. TOP-LEVEL STRUCTURE")
    print("=" * 100)

    print_structure(
        data,
        max_depth=4,
    )

    print()

    # ------------------------------------------------------------------
    # ذخیره JSON کامل برای بررسی بعدی
    # ------------------------------------------------------------------

    output_file = "fotmob_competition_structure.json"

    try:

        with open(
            output_file,
            "w",
            encoding="utf-8",
        ) as file:

            json.dump(
                data,
                file,
                ensure_ascii=False,
                indent=2,
            )

        print(
            f"JSON کامل در {output_file} ذخیره شد."
        )

    except Exception as exc:

        print(
            f"خطا در ذخیره JSON: {exc}"
        )


if __name__ == "__main__":
    main()

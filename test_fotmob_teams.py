import json
import requests
from urllib.parse import quote


SEARCH_TERM = "Real Madrid"


HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (X11; Linux x86_64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/140.0.0.0 Safari/537.36"
    ),
    "Accept": (
        "text/html,application/xhtml+xml,"
        "application/xml;q=0.9,image/avif,image/webp,"
        "*/*;q=0.8"
    ),
    "Accept-Language": "en-US,en;q=0.9",
    "Referer": "https://www.fotmob.com/",
}


def main():

    url = (
        "https://www.fotmob.com/api/data/search/suggest"
        f"?term={quote(SEARCH_TERM)}&hits=20&lang=en"
    )

    print("=" * 70)
    print("تست جست‌وجوی فوت‌ماب")
    print("=" * 70)

    print()
    print(f"جست‌وجو: {SEARCH_TERM}")
    print(f"URL: {url}")
    print()

    response = requests.get(
        url,
        headers=HEADERS,
        timeout=30,
    )

    print(
        f"HTTP Status: {response.status_code}"
    )

    print(
        f"Response Length: {len(response.text)}"
    )

    print()

    response.raise_for_status()

    try:

        data = response.json()

    except Exception:

        print(
            "❌ پاسخ JSON نیست."
        )

        print()
        print(
            response.text[:5000]
        )

        raise

    print("✅ پاسخ JSON است.")
    print()

    print("=" * 70)
    print("ساختار اصلی پاسخ")
    print("=" * 70)

    if isinstance(data, dict):

        print(
            "نوع: dict"
        )

        print(
            "کلیدها:"
        )

        for key in data.keys():
            print(
                f"  - {key}"
            )

    elif isinstance(data, list):

        print(
            "نوع: list"
        )

        print(
            f"تعداد عناصر: {len(data)}"
        )

    else:

        print(
            f"نوع پاسخ: {type(data).__name__}"
        )

    print()

    print("=" * 70)
    print("پاسخ کامل JSON")
    print("=" * 70)

    print(
        json.dumps(
            data,
            ensure_ascii=False,
            indent=2,
        )
    )

    with open(
        "fotmob_search_raw.json",
        "w",
        encoding="utf-8",
    ) as file:

        json.dump(
            data,
            file,
            ensure_ascii=False,
            indent=2,
        )

    print()
    print("=" * 70)
    print(
        "✅ پاسخ خام در "
        "fotmob_search_raw.json "
        "ذخیره شد."
    )
    print("=" * 70)


if __name__ == "__main__":
    main()

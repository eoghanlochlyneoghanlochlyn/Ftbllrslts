import requests


URL = "https://www.fotmob.com"


def main():
    print("در حال بررسی صفحه اصلی FotMob...")

    response = requests.get(
        URL,
        headers={
            "User-Agent": "Mozilla/5.0"
        },
        timeout=20
    )

    print("Status:", response.status_code)
    print("Length:", len(response.text))

    if response.status_code != 200:
        print(response.text[:1000])
        return

    text = response.text

    keywords = [
        "Premier League",
        "Champions League",
        "Serie A",
        "LaLiga",
        "leagues",
        "competitions",
    ]

    print("\n--- جستجوی کلمات کلیدی ---")

    for keyword in keywords:
        print(
            keyword,
            "=>",
            keyword.lower() in text.lower()
        )

    print("\n--- اسکریپت‌های صفحه ---")

    import re

    scripts = re.findall(
        r'<script[^>]*>(.*?)</script>',
        text,
        re.DOTALL
    )

    print("تعداد script:", len(scripts))

    for i, script in enumerate(scripts):
        if any(
            keyword.lower() in script.lower()
            for keyword in keywords
        ):
            print(
                f"\n### Script {i} contains competition data ###"
            )
            print(script[:5000])


if __name__ == "__main__":
    main()

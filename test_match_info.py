import requests
import re


URL = "https://www.fotmob.com"


def main():
    print("در حال بررسی صفحه اصلی FotMob...")

    try:
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
            print("خطا در دریافت صفحه:")
            print(response.text[:2000])
            return

        text = response.text

        keywords = [
            "Premier League",
            "Champions League",
            "Serie A",
            "LaLiga",
            "TournamentPrefixes",
            "TournamentTemplates",
        ]

        print("\n--- جستجوی کلمات کلیدی ---")

        for keyword in keywords:
            found = keyword.lower() in text.lower()

            print(
                f"{keyword} => {found}"
            )

        print("\n--- بررسی اسکریپت‌های صفحه ---")

        scripts = re.findall(
            r"<script[^>]*>(.*?)</script>",
            text,
            re.DOTALL
        )

        print(
            "تعداد script:",
            len(scripts)
        )

        found_competition_data = False

        for i, script in enumerate(scripts):

            if (
                "TournamentPrefixes" in script
                or "TournamentTemplates" in script
            ):
                found_competition_data = True

                print(
                    f"\n### Script {i} contains competition data ###"
                )

                print("\n--- FULL SCRIPT ---\n")

                print(script)

                print(
                    "\n--- END FULL SCRIPT ---"
                )

        if not found_competition_data:
            print(
                "\nهیچ داده‌ای با TournamentPrefixes "
                "یا TournamentTemplates پیدا نشد."
            )

    except requests.RequestException as e:
        print(
            "\nخطا در ارتباط با FotMob:"
        )
        print(repr(e))

    except Exception as e:
        print(
            "\nخطای غیرمنتظره:"
        )
        print(repr(e))


if __name__ == "__main__":
    main()

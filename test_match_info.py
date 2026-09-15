import json
import re
import requests


URL = "https://www.fotmob.com"


def extract_next_data(html):
    """
    پیدا کردن داده JSON مربوط به صفحه از داخل scriptها
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
    جستجوی بازگشتی برای پیدا کردن آبجکتی که
    TournamentPrefixes / TournamentTemplates / LeagueMapping دارد.
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


def print_section(title, data):
    print("\n")
    print("=" * 70)
    print(title)
    print("=" * 70)

    if not data:
        print("هیچ داده‌ای پیدا نشد.")
        return

    for key, value in data.items():

        if isinstance(value, str):
            print(f"{key} | {value}")

        else:
            print(f"{key} | {json.dumps(value, ensure_ascii=False)}")


def main():

    print("در حال دریافت اطلاعات رقابت‌ها از FotMob...")

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

        print("Status:", response.status_code)
        print("Length:", len(response.text))

        if response.status_code != 200:

            print("\nخطا در دریافت صفحه FotMob:")
            print(response.text[:2000])

            return

        print("\nدر حال پیدا کردن داده‌های رقابت‌ها...")

        data = extract_next_data(response.text)

        if data is None:

            print(
                "\n❌ هیچ script حاوی "
                "TournamentPrefixes یا TournamentTemplates پیدا نشد."
            )

            return

        print("✅ داده اصلی پیدا شد.")

        competition_data = find_competition_data(data)

        if competition_data is None:

            print(
                "\n❌ بخش اطلاعات رقابت‌ها پیدا نشد."
            )

            return

        print("✅ بخش اطلاعات رقابت‌ها پیدا شد.")

        tournament_prefixes = (
            competition_data.get(
                "TournamentPrefixes",
                {}
            )
        )

        tournament_templates = (
            competition_data.get(
                "TournamentTemplates",
                {}
            )
        )

        league_mapping = (
            competition_data.get(
                "LeagueMapping",
                {}
            )
        )

        print_section(
            "TOURNAMENT PREFIXES",
            tournament_prefixes
        )

        print_section(
            "TOURNAMENT TEMPLATES",
            tournament_templates
        )

        print_section(
            "LEAGUE MAPPING",
            league_mapping
        )

        print("\n")
        print("=" * 70)
        print("پایان استخراج")
        print("=" * 70)

        print(
            "\nتعداد TournamentPrefixes:",
            len(tournament_prefixes)
        )

        print(
            "تعداد TournamentTemplates:",
            len(tournament_templates)
        )

        print(
            "تعداد LeagueMapping:",
            len(league_mapping)
        )

    except requests.RequestException as e:

        print("\n❌ خطا در ارتباط با FotMob:")
        print(repr(e))

    except Exception as e:

        print("\n❌ خطای غیرمنتظره:")
        print(repr(e))


if __name__ == "__main__":
    main()

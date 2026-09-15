import json
import re
import requests


URL = "https://www.fotmob.com/leagues/47/overview"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/140.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,"
              "image/avif,image/webp,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
}


def main():
    print("=" * 70)
    print("FotMob League Page Structure Test")
    print("=" * 70)

    print()
    print(f"URL: {URL}")
    print()

    try:
        response = requests.get(
            URL,
            headers=HEADERS,
            timeout=30,
        )

        print(f"HTTP Status: {response.status_code}")
        print(f"Content-Type: {response.headers.get('content-type')}")
        print(f"HTML Length: {len(response.text)}")

        response.raise_for_status()

    except Exception as e:
        print(f"❌ Request failed: {e}")
        return

    html = response.text

    # --------------------------------------------------------
    # بررسی وجود __NEXT_DATA__
    # --------------------------------------------------------

    print()
    print("=" * 70)
    print("Checking __NEXT_DATA__")
    print("=" * 70)

    match = re.search(
        r'<script[^>]+id="__NEXT_DATA__"[^>]*>(.*?)</script>',
        html,
        re.DOTALL,
    )

    if not match:
        print("❌ __NEXT_DATA__ پیدا نشد.")
    else:
        print("✅ __NEXT_DATA__ پیدا شد.")

        raw_json = match.group(1)

        print(f"NEXT_DATA length: {len(raw_json)}")

        try:
            data = json.loads(raw_json)

            print("✅ JSON با موفقیت parse شد.")

        except Exception as e:
            print(f"❌ JSON parse failed: {e}")
            data = None

    # --------------------------------------------------------
    # جست‌وجوی teamId
    # --------------------------------------------------------

    print()
    print("=" * 70)
    print("Searching for teamId / team IDs")
    print("=" * 70)

    team_ids = sorted(
        set(
            re.findall(
                r'"(?:teamId|teamID|team_id)"\s*:\s*(\d+)',
                html,
            )
        )
    )

    if team_ids:
        print(f"✅ تعداد IDهای پیدا شده: {len(team_ids)}")
        print()

        for team_id in team_ids[:100]:
            print(team_id)

    else:
        print("❌ هیچ teamIdای در HTML پیدا نشد.")

    # --------------------------------------------------------
    # جست‌وجوی ساختارهای teams
    # --------------------------------------------------------

    print()
    print("=" * 70)
    print("Searching for 'teams' structures")
    print("=" * 70)

    teams_positions = []

    for match in re.finditer(r'"teams"\s*:', html):
        teams_positions.append(match.start())

    print(f"تعداد occurrences برای \"teams\": {len(teams_positions)}")

    for index, position in enumerate(teams_positions[:20], start=1):

        start = max(0, position - 300)
        end = min(len(html), position + 1200)

        print()
        print("-" * 70)
        print(f"Occurrence #{index}")
        print("-" * 70)

        snippet = html[start:end]

        print(snippet)

    # --------------------------------------------------------
    # اگر __NEXT_DATA__ وجود داشت، مسیرهای محتمل را بررسی کنیم
    # --------------------------------------------------------

    if data is not None:

        print()
        print("=" * 70)
        print("Recursive search inside __NEXT_DATA__")
        print("=" * 70)

        found = []

        def recursive_search(obj, path="root"):

            if isinstance(obj, dict):

                for key, value in obj.items():

                    current_path = f"{path}.{key}"

                    # کلیدهای جالب
                    if key.lower() in {
                        "teams",
                        "teamid",
                        "team_id",
                        "teamid",
                        "standings",
                        "table",
                        "league",
                        "season",
                    }:

                        if isinstance(value, (list, dict)):

                            found.append(
                                (
                                    current_path,
                                    type(value).__name__,
                                    len(value),
                                )
                            )

                        else:

                            found.append(
                                (
                                    current_path,
                                    type(value).__name__,
                                    value,
                                )
                            )

                    recursive_search(
                        value,
                        current_path,
                    )

            elif isinstance(obj, list):

                for index, value in enumerate(obj):

                    recursive_search(
                        value,
                        f"{path}[{index}]",
                    )

        recursive_search(data)

        if not found:

            print("❌ ساختار مرتبطی پیدا نشد.")

        else:

            print(
                f"✅ تعداد ساختارهای مرتبط پیدا شده: {len(found)}"
            )

            for item in found[:100]:

                print(item)

    # --------------------------------------------------------
    # ذخیره HTML برای بررسی در صورت نیاز
    # --------------------------------------------------------

    with open(
        "fotmob_premier_league.html",
        "w",
        encoding="utf-8",
    ) as f:

        f.write(html)

    print()
    print("=" * 70)
    print("پایان تست")
    print("=" * 70)
    print()
    print(
        "📁 HTML خام در fotmob_premier_league.html ذخیره شد."
    )


if __name__ == "__main__":
    main()

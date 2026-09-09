import json
import re
import requests


MATCH_ID = "6106242"

URL = f"https://www.fotmob.com/match/{MATCH_ID}"

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


def get_fotmob_data(match_id):
    url = f"https://www.fotmob.com/match/{match_id}"

    print("=" * 70)
    print("دریافت اطلاعات مسابقه")
    print("=" * 70)
    print(f"URL: {url}")
    print()

    session = requests.Session()

    response = session.get(
        url,
        headers=HEADERS,
        timeout=30,
        allow_redirects=True,
    )

    print(f"HTTP Status: {response.status_code}")
    print(f"Final URL: {response.url}")
    print(f"HTML Length: {len(response.text)}")
    print()

    response.raise_for_status()

    html = response.text

    match = re.search(
        r'<script[^>]+id=["\']__NEXT_DATA__["\'][^>]*>'
        r'(.*?)'
        r'</script>',
        html,
        re.DOTALL,
    )

    if not match:
        raise RuntimeError(
            "__NEXT_DATA__ در صفحه فوت‌ماب پیدا نشد."
        )

    print("✅ __NEXT_DATA__ پیدا شد.")

    data = json.loads(match.group(1))

    print("✅ JSON با موفقیت استخراج شد.")
    print()

    return data


def get_page_props(data):
    return data["props"]["pageProps"]


def print_match_info(page_props):
    general = page_props.get("general", {})

    home_team = general.get("homeTeam", {})
    away_team = general.get("awayTeam", {})

    home_name = home_team.get("name", "نامشخص")
    away_name = away_team.get("name", "نامشخص")

    match_time = general.get(
        "matchTimeUTC",
        "نامشخص",
    )

    started = general.get("started")
    finished = general.get("finished")

    print("=" * 70)
    print("اطلاعات مسابقه")
    print("=" * 70)

    print(f"مسابقه: {home_name} - {away_name}")
    print(f"زمان: {match_time}")
    print(f"شروع شده: {started}")
    print(f"تمام شده: {finished}")
    print()


def find_score(obj):
    if isinstance(obj, dict):

        for key in [
            "scoreStr",
            "score",
            "scoreString",
        ]:
            value = obj.get(key)

            if isinstance(value, str):
                if re.search(r"\d+\s*[-:]\s*\d+", value):
                    return value

        for value in obj.values():
            result = find_score(value)

            if result:
                return result

    elif isinstance(obj, list):

        for value in obj:
            result = find_score(value)

            if result:
                return result

    return None


def print_score(page_props):
    print("=" * 70)
    print("نتیجه")
    print("=" * 70)

    score = find_score(page_props)

    if score:
        print(f"نتیجه: {score}")
    else:
        print("❌ نتیجه پیدا نشد.")

    print()


def get_player_name(value):
    if not isinstance(value, dict):
        return None

    name = value.get("name")

    if name:
        return name

    player = value.get("player")

    if isinstance(player, dict):
        name = player.get("name")

        if name:
            return name

    return None


def print_events(page_props):
    content = page_props.get("content", {})
    match_facts = content.get("matchFacts", {})

    events_data = match_facts.get("events", {})
    events = events_data.get("events", [])

    print("=" * 70)
    print("رویدادهای مسابقه")
    print("=" * 70)

    print(f"تعداد رویدادها: {len(events)}")
    print()

    if not events:
        print("❌ هیچ رویدادی پیدا نشد.")
        print()
        return

    for index, event in enumerate(events, start=1):

        print(f"رویداد {index}:")

        if not isinstance(event, dict):
            print()
            continue

        event_type = event.get(
            "type",
            event.get(
                "eventType",
                "نامشخص",
            ),
        )

        time = event.get(
            "timeStr",
            event.get(
                "time",
                "نامشخص",
            ),
        )

        print(f"  نوع: {event_type}")
        print(f"  دقیقه: {time}")

        player = event.get("player")

        player_name = get_player_name(player)

        if player_name:
            print(f"  بازیکن: {player_name}")

        if "homeScore" in event:
            print(
                f"  نتیجه لحظه‌ای: "
                f"{event.get('homeScore')} - "
                f"{event.get('awayScore')}"
            )

        print()


def print_lineup_debug(page_props):
    content = page_props.get("content", {})
    lineup = content.get("lineup", {})

    print("=" * 70)
    print("بررسی ساختار ترکیب")
    print("=" * 70)

    if not lineup:
        print("❌ lineup پیدا نشد.")
        print()
        return

    print("کلیدهای اصلی lineup:")
    print(list(lineup.keys()))
    print()

    for side in [
        "homeTeam",
        "awayTeam",
    ]:

        team_data = lineup.get(side)

        print("-" * 70)
        print(side)
        print("-" * 70)

        if not isinstance(team_data, dict):
            print("❌ اطلاعات تیم پیدا نشد.")
            print()
            continue

        print("کلیدهای این تیم:")
        print(list(team_data.keys()))
        print()

        for key, value in team_data.items():

            if isinstance(value, list):

                print(
                    f"کلید '{key}': "
                    f"لیست با {len(value)} مورد"
                )

                if value:

                    first = value[0]

                    if isinstance(first, dict):

                        print(
                            "کلیدهای اولین مورد:"
                        )

                        print(
                            list(first.keys())
                        )

                        print()

            elif isinstance(value, dict):

                print(
                    f"کلید '{key}': "
                    f"دیکشنری"
                )

            else:

                print(
                    f"کلید '{key}': "
                    f"{value}"
                )

        print()


def print_lineups(page_props):
    content = page_props.get("content", {})
    lineup = content.get("lineup", {})

    print("=" * 70)
    print("ترکیب")
    print("=" * 70)

    if not lineup:
        print("❌ اطلاعات ترکیب پیدا نشد.")
        print()
        return

    for side, title in [
        ("homeTeam", "ترکیب تیم میزبان"),
        ("awayTeam", "ترکیب تیم مهمان"),
    ]:

        team_data = lineup.get(side, {})

        print(title)
        print("-" * 50)

        if not isinstance(team_data, dict):
            print("❌ اطلاعات تیم پیدا نشد.")
            print()
            continue

        team_name = team_data.get(
            "name",
            "نامشخص",
        )

        print(f"تیم: {team_name}")
        print()

        starters = team_data.get(
            "starters",
            [],
        )

        substitutes = team_data.get(
            "substitutes",
            [],
        )

        print("بازیکنان اصلی:")

        if starters:

            for player in starters:

                if not isinstance(player, dict):
                    continue

                name = get_player_name(player)

                number = player.get(
                    "shirtNumber",
                    "",
                )

                position = player.get(
                    "position",
                    "",
                )

                print(
                    f"  {number} | "
                    f"{name or 'نامشخص'}"
                    f"{' | ' + str(position) if position else ''}"
                )

        else:

            print("  ❌ بازیکنی پیدا نشد.")

        print()
        print("بازیکنان نیمکت:")

        if substitutes:

            for player in substitutes:

                if not isinstance(player, dict):
                    continue

                name = get_player_name(player)

                number = player.get(
                    "shirtNumber",
                    "",
                )

                print(
                    f"  {number} | "
                    f"{name or 'نامشخص'}"
                )

        else:

            print("  ❌ بازیکنی پیدا نشد.")

        print()
        print()


def find_substitution_objects(obj, path="root"):
    results = []

    if isinstance(obj, dict):

        for key, value in obj.items():

            key_lower = str(key).lower()

            if (
                "substitution" in key_lower
                or key_lower in [
                    "subs",
                    "substitutes",
                ]
            ):

                if isinstance(value, list):

                    for index, item in enumerate(value):

                        if isinstance(item, dict):

                            results.append(
                                (
                                    f"{path}.{key}[{index}]",
                                    item,
                                )
                            )

                elif isinstance(value, dict):

                    results.append(
                        (
                            f"{path}.{key}",
                            value,
                        )
                    )

            results.extend(
                find_substitution_objects(
                    value,
                    f"{path}.{key}",
                )
            )

    elif isinstance(obj, list):

        for index, value in enumerate(obj):

            results.extend(
                find_substitution_objects(
                    value,
                    f"{path}[{index}]",
                )
            )

    return results


def print_substitution_debug(page_props):
    content = page_props.get("content", {})

    print("=" * 70)
    print("بررسی ساختار تعویض‌ها")
    print("=" * 70)

    results = find_substitution_objects(
        content
    )

    if not results:
        print(
            "❌ هیچ ساختار احتمالی برای "
            "تعویض پیدا نشد."
        )
        print()
        return

    printed = set()

    for path, obj in results:

        signature = json.dumps(
            obj,
            ensure_ascii=False,
            sort_keys=True,
        )

        if signature in printed:
            continue

        printed.add(signature)

        print(f"مسیر: {path}")
        print("ساختار:")

        print(
            json.dumps(
                obj,
                ensure_ascii=False,
                indent=2,
            )
        )

        print()
        print("-" * 70)
        print()

        if len(printed) >= 20:
            print(
                "⚠️ برای جلوگیری از طولانی شدن "
                "خروجی، بررسی متوقف شد."
            )
            break


def print_stats(page_props):
    content = page_props.get("content", {})
    stats_data = content.get("stats", {})

    print("=" * 70)
    print("آمار مسابقه")
    print("=" * 70)

    if not stats_data:
        print("❌ آمار پیدا نشد.")
        print()
        return

    periods = stats_data.get(
        "Periods",
        {},
    )

    all_stats = periods.get(
        "All",
        {},
    )

    groups = all_stats.get(
        "stats",
        [],
    )

    if not groups:
        print("❌ ساختار آمار پیدا نشد.")
        print()
        return

    for group in groups:

        if not isinstance(group, dict):
            continue

        title = group.get(
            "title",
            group.get(
                "name",
                "آمار",
            ),
        )

        print(f"{title}:")
        print("-" * 40)

        stats = group.get(
            "stats",
            [],
        )

        if isinstance(stats, list):

            for stat in stats:

                if not isinstance(stat, dict):
                    continue

                name = (
                    stat.get("title")
                    or stat.get("name")
                    or stat.get("label")
                    or "نامشخص"
                )

                values = stat.get(
                    "stats",
                    [],
                )

                print(
                    f"  {name}: {values}"
                )

        print()


def save_raw_data(data):
    filename = "fotmob_match_data.json"

    with open(
        filename,
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
        f"✅ داده خام در {filename} ذخیره شد."
    )
    print()


def main():

    try:

        data = get_fotmob_data(MATCH_ID)

        page_props = get_page_props(data)

        print()

        print_match_info(page_props)

        print_score(page_props)

        print_events(page_props)

        print_lineup_debug(page_props)

        print_lineups(page_props)

        print_substitution_debug(
            page_props
        )

        print_stats(page_props)

        save_raw_data(data)

        print("=" * 70)
        print("✅ تست با موفقیت تمام شد.")
        print("=" * 70)

    except Exception as error:

        print("=" * 70)
        print("❌ خطا")
        print("=" * 70)

        print(type(error).__name__)
        print(error)

        raise


if __name__ == "__main__":
    main()

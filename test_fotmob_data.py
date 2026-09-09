import json
import re
import requests


MATCH_ID = "6106242"

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

    match = re.search(
        r'<script[^>]+id=["\']__NEXT_DATA__["\'][^>]*>'
        r'(.*?)'
        r'</script>',
        response.text,
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


def get_general(page_props):
    return page_props.get("general", {})


def get_content(page_props):
    return page_props.get("content", {})


def get_team_name(team_data):
    if not isinstance(team_data, dict):
        return "نامشخص"

    return team_data.get("name", "نامشخص")


def get_player_name(player):
    if not isinstance(player, dict):
        return None

    name = player.get("name")

    if name:
        return name

    nested_player = player.get("player")

    if isinstance(nested_player, dict):
        return nested_player.get("name")

    return None


def get_player_number(player):
    if not isinstance(player, dict):
        return ""

    return str(
        player.get(
            "shirtNumber",
            "",
        )
    )


def find_final_score(page_props):
    header = page_props.get("header", {})

    if isinstance(header, dict):

        status = header.get("status", {})

        if isinstance(status, dict):

            score_str = status.get("scoreStr")

            if isinstance(score_str, str):
                if re.search(
                    r"\d+\s*[-:]\s*\d+",
                    score_str,
                ):
                    return score_str

        teams = header.get("teams", [])

        if isinstance(teams, list) and len(teams) >= 2:

            scores = []

            for team in teams[:2]:

                if not isinstance(team, dict):
                    continue

                score = team.get("score")

                if score is not None:
                    scores.append(str(score))

            if len(scores) == 2:
                return f"{scores[0]} - {scores[1]}"

    general = get_general(page_props)

    for key in [
        "scoreStr",
        "score",
        "scoreString",
    ]:

        value = general.get(key)

        if isinstance(value, str):

            if re.search(
                r"\d+\s*[-:]\s*\d+",
                value,
            ):
                return value

    return None


def get_events(page_props):
    content = get_content(page_props)

    match_facts = content.get(
        "matchFacts",
        {},
    )

    events_data = match_facts.get(
        "events",
        {},
    )

    events = events_data.get(
        "events",
        [],
    )

    if not isinstance(events, list):
        return []

    return events


def get_event_time(event):
    if not isinstance(event, dict):
        return ""

    time_str = event.get("timeStr")

    if time_str is not None:
        return str(time_str)

    time = event.get("time")

    if time is not None:
        return str(time)

    return ""


def get_event_type(event):
    if not isinstance(event, dict):
        return ""

    return (
        event.get("type")
        or event.get("eventType")
        or ""
    )


def get_event_player(event):
    if not isinstance(event, dict):
        return None

    return get_player_name(
        event.get("player")
    )


def print_match_info(page_props):
    general = get_general(page_props)

    home_team = general.get(
        "homeTeam",
        {},
    )

    away_team = general.get(
        "awayTeam",
        {},
    )

    home_name = get_team_name(home_team)
    away_name = get_team_name(away_team)

    match_time = general.get(
        "matchTimeUTC",
        "نامشخص",
    )

    started = general.get(
        "started",
        False,
    )

    finished = general.get(
        "finished",
        False,
    )

    print("=" * 70)
    print("اطلاعات مسابقه")
    print("=" * 70)

    print(
        f"مسابقه: "
        f"{home_name} - {away_name}"
    )

    print(
        f"زمان: {match_time}"
    )

    print(
        f"شروع شده: {started}"
    )

    print(
        f"تمام شده: {finished}"
    )

    print()


def print_score(page_props):
    score = find_final_score(
        page_props
    )

    print("=" * 70)
    print("نتیجه")
    print("=" * 70)

    if score:
        print(
            f"نتیجه: {score}"
        )
    else:
        print(
            "❌ نتیجه پیدا نشد."
        )

    print()


def print_goals(page_props):
    events = get_events(page_props)

    goals = [
        event
        for event in events
        if get_event_type(event) == "Goal"
    ]

    print("=" * 70)
    print("گل‌ها")
    print("=" * 70)

    if not goals:
        print(
            "هیچ گلی ثبت نشده."
        )
        print()
        return

    for event in goals:

        minute = get_event_time(event)
        player = get_event_player(event)

        print(
            f"{minute}' "
            f"{player or 'نامشخص'}"
        )

    print()


def print_cards(page_props):
    events = get_events(page_props)

    cards = [
        event
        for event in events
        if get_event_type(event) == "Card"
    ]

    print("=" * 70)
    print("کارت‌ها")
    print("=" * 70)

    if not cards:
        print(
            "هیچ کارتی ثبت نشده."
        )
        print()
        return

    for event in cards:

        minute = get_event_time(event)
        player = get_event_player(event)

        print(
            f"{minute}' "
            f"{player or 'نامشخص'}"
        )

    print()


def get_lineup(page_props):
    content = get_content(page_props)

    return content.get(
        "lineup",
        {},
    )


def get_team_lineup(
    lineup,
    side,
):
    team_data = lineup.get(
        side,
        {},
    )

    if not isinstance(team_data, dict):
        return {}, [], [], []

    starters = team_data.get(
        "starters",
        [],
    )

    subs = team_data.get(
        "subs",
        [],
    )

    unavailable = team_data.get(
        "unavailable",
        [],
    )

    if not isinstance(starters, list):
        starters = []

    if not isinstance(subs, list):
        subs = []

    if not isinstance(unavailable, list):
        unavailable = []

    return (
        team_data,
        starters,
        subs,
        unavailable,
    )


def print_one_team_lineup(
    title,
    team_data,
    starters,
    subs,
):
    team_name = team_data.get(
        "name",
        "نامشخص",
    )

    formation = team_data.get(
        "formation",
        "نامشخص",
    )

    rating = team_data.get(
        "rating",
        "نامشخص",
    )

    print(title)
    print("-" * 50)

    print(
        f"تیم: {team_name}"
    )

    print(
        f"آرایش: {formation}"
    )

    print(
        f"امتیاز تیم: {rating}"
    )

    print()

    print("بازیکنان اصلی:")

    if starters:

        for player in starters:

            name = get_player_name(
                player
            )

            number = get_player_number(
                player
            )

            if name:
                print(
                    f"  {number} | {name}"
                )

    else:

        print(
            "  ❌ بازیکنی پیدا نشد."
        )

    print()

    print("نیمکت:")

    if subs:

        for player in subs:

            name = get_player_name(
                player
            )

            number = get_player_number(
                player
            )

            if name:
                print(
                    f"  {number} | {name}"
                )

    else:

        print(
            "  ❌ بازیکنی پیدا نشد."
        )

    print()


def print_lineups(page_props):
    lineup = get_lineup(
        page_props
    )

    print("=" * 70)
    print("ترکیب و نیمکت")
    print("=" * 70)

    if not lineup:
        print(
            "❌ اطلاعات ترکیب پیدا نشد."
        )
        print()
        return

    (
        home_team,
        home_starters,
        home_subs,
        _,
    ) = get_team_lineup(
        lineup,
        "homeTeam",
    )

    (
        away_team,
        away_starters,
        away_subs,
        _,
    ) = get_team_lineup(
        lineup,
        "awayTeam",
    )

    print_one_team_lineup(
        "تیم میزبان",
        home_team,
        home_starters,
        home_subs,
    )

    print_one_team_lineup(
        "تیم مهمان",
        away_team,
        away_starters,
        away_subs,
    )


def get_substitution_events(
    player,
):
    if not isinstance(player, dict):
        return []

    performance = player.get(
        "performance",
        {},
    )

    if not isinstance(
        performance,
        dict,
    ):
        return []

    events = performance.get(
        "substitutionEvents",
        [],
    )

    if not isinstance(events, list):
        return []

    return events


def collect_substitutions_for_team(
    team_data,
):
    if not isinstance(team_data, dict):
        return []

    substitutions = []

    starters = team_data.get(
        "starters",
        [],
    )

    subs = team_data.get(
        "subs",
        [],
    )

    if not isinstance(starters, list):
        starters = []

    if not isinstance(subs, list):
        subs = []

    for player in starters:

        name = get_player_name(
            player
        )

        number = get_player_number(
            player
        )

        for event in get_substitution_events(
            player
        ):

            if not isinstance(event, dict):
                continue

            if event.get("type") != "subOut":
                continue

            substitutions.append(
                {
                    "time": event.get(
                        "time"
                    ),
                    "out": name,
                    "out_number": number,
                    "in": None,
                    "in_number": "",
                }
            )

    for player in subs:

        name = get_player_name(
            player
        )

        number = get_player_number(
            player
        )

        for event in get_substitution_events(
            player
        ):

            if not isinstance(event, dict):
                continue

            if event.get("type") != "subIn":
                continue

            time = event.get(
                "time"
            )

            matching = None

            for item in substitutions:

                if (
                    item.get("time") == time
                    and item.get("in") is None
                ):
                    matching = item
                    break

            if matching:

                matching["in"] = name
                matching["in_number"] = number

            else:

                substitutions.append(
                    {
                        "time": time,
                        "out": None,
                        "out_number": "",
                        "in": name,
                        "in_number": number,
                    }
                )

    substitutions.sort(
        key=lambda item: (
            item.get("time")
            if isinstance(
                item.get("time"),
                int,
            )
            else 999
        )
    )

    return substitutions


def format_minute(value):
    if value is None:
        return "نامشخص"

    return str(value)


def print_substitutions(page_props):
    lineup = get_lineup(
        page_props
    )

    print("=" * 70)
    print("تعویض‌ها")
    print("=" * 70)

    if not lineup:
        print(
            "❌ اطلاعات ترکیب پیدا نشد."
        )
        print()
        return

    for side in [
        "homeTeam",
        "awayTeam",
    ]:

        team_data = lineup.get(
            side,
            {},
        )

        if not isinstance(
            team_data,
            dict,
        ):
            continue

        team_name = team_data.get(
            "name",
            "نامشخص",
        )

        substitutions = (
            collect_substitutions_for_team(
                team_data
            )
        )

        if not substitutions:
            continue

        print(
            f"{team_name}:"
        )

        for item in substitutions:

            minute = format_minute(
                item.get("time")
            )

            player_out = (
                item.get("out")
                or "نامشخص"
            )

            player_in = (
                item.get("in")
                or "نامشخص"
            )

            print(
                f"  {minute}' "
                f"خروج: {player_out} "
                f"← ورود: {player_in}"
            )

        print()


def extract_stat_value(stat):
    if not isinstance(stat, dict):
        return None

    return stat.get(
        "stats"
    )


def print_stats(page_props):
    content = get_content(
        page_props
    )

    stats_data = content.get(
        "stats",
        {},
    )

    print("=" * 70)
    print("آمار مهم مسابقه")
    print("=" * 70)

    if not stats_data:
        print(
            "❌ آمار پیدا نشد."
        )
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

    if not isinstance(
        groups,
        list,
    ):
        print(
            "❌ ساختار آمار پیدا نشد."
        )
        print()
        return

    preferred_stats = [
        "Ball possession",
        "Expected goals (xG)",
        "Total shots",
        "Shots on target",
        "Touches in opposition box",
        "Big chances",
        "Big chances missed",
        "Accurate passes",
        "Yellow cards",
        "Corners",
    ]

    found = {}

    for group in groups:

        if not isinstance(
            group,
            dict,
        ):
            continue

        stats = group.get(
            "stats",
            [],
        )

        if not isinstance(
            stats,
            list,
        ):
            continue

        for stat in stats:

            if not isinstance(
                stat,
                dict,
            ):
                continue

            name = (
                stat.get("title")
                or stat.get("name")
                or stat.get("label")
            )

            if not name:
                continue

            if name in preferred_stats:

                if name not in found:
                    found[name] = (
                        extract_stat_value(
                            stat
                        )
                    )

    for name in preferred_stats:

        if name in found:

            print(
                f"  {name}: "
                f"{found[name]}"
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

        data = get_fotmob_data(
            MATCH_ID
        )

        page_props = get_page_props(
            data
        )

        print_match_info(
            page_props
        )

        print_score(
            page_props
        )

        print_goals(
            page_props
        )

        print_cards(
            page_props
        )

        print_lineups(
            page_props
        )

        print_substitutions(
            page_props
        )

        print_stats(
            page_props
        )

        save_raw_data(
            data
        )

        print("=" * 70)
        print(
            "✅ تست با موفقیت تمام شد."
        )
        print("=" * 70)

    except Exception as error:

        print("=" * 70)
        print("❌ خطا")
        print("=" * 70)

        print(
            type(error).__name__
        )

        print(error)

        raise


if __name__ == "__main__":
    main()

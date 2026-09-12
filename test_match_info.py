```python
import json
import requests
from bs4 import BeautifulSoup


MATCH_ID = "14u9ym"
MATCH_URL = f"https://www.fotmob.com/matches/canada-vs-qatar/{MATCH_ID}"


def get_nested(data, *keys):
    current = data

    for key in keys:
        if not isinstance(current, dict):
            return None

        current = current.get(key)

    return current


def find_next_data(html):
    soup = BeautifulSoup(
        html,
        "html.parser",
    )

    script = soup.find(
        "script",
        id="__NEXT_DATA__",
    )

    if not script:
        raise RuntimeError(
            "__NEXT_DATA__ پیدا نشد."
        )

    return json.loads(
        script.string
    )


def print_separator(title):
    print()
    print("=" * 80)
    print(title)
    print("=" * 80)


def print_json(title, data):
    print_separator(title)

    print(
        json.dumps(
            data,
            ensure_ascii=False,
            indent=2,
        )
    )


def main():
    print("=" * 80)
    print("FOTMOB EVENT STRUCTURE TEST")
    print("=" * 80)

    print()
    print("Match ID:", MATCH_ID)
    print("URL:", MATCH_URL)

    print()
    print("در حال دریافت صفحه FotMob...")

    response = requests.get(
        MATCH_URL,
        headers={
            "User-Agent": (
                "Mozilla/5.0 "
                "(Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 "
                "(KHTML, like Gecko) "
                "Chrome/140.0.0.0 "
                "Safari/537.36"
            )
        },
        timeout=30,
    )

    print(
        "HTTP:",
        response.status_code,
    )

    print(
        "HTML:",
        len(response.text),
        "bytes",
    )

    response.raise_for_status()

    root = find_next_data(
        response.text
    )

    print()
    print("__NEXT_DATA__ extracted successfully.")

    # --------------------------------------------------------
    # مسیرهای اصلی
    # --------------------------------------------------------

    page_props = get_nested(
        root,
        "props",
        "pageProps",
    )

    content = (
        page_props.get("content")
        if isinstance(page_props, dict)
        else None
    )

    # --------------------------------------------------------
    # اطلاعات کلی مسابقه
    # --------------------------------------------------------

    print_separator(
        "BASIC MATCH INFO"
    )

    general = get_nested(
        root,
        "props",
        "pageProps",
        "general",
    )

    header = get_nested(
        root,
        "props",
        "pageProps",
        "header",
    )

    if isinstance(general, dict):
        print(
            "GENERAL:"
        )

        for key in [
            "finished",
            "started",
            "cancelled",
            "awarded",
            "utcTime",
            "scoreStr",
        ]:
            if key in general:
                print(
                    f"{key}:",
                    general.get(key),
                )

    if isinstance(header, dict):
        print()
        print("HEADER:")

        for key in [
            "homeTeam",
            "awayTeam",
            "status",
        ]:
            if key in header:
                value = header.get(key)

                print(
                    f"{key}:"
                )

                print(
                    json.dumps(
                        value,
                        ensure_ascii=False,
                        indent=2,
                    )
                )

    # --------------------------------------------------------
    # header.events
    # --------------------------------------------------------

    header_events = None

    if isinstance(header, dict):
        header_events = header.get(
            "events"
        )

    print_json(
        "HEADER EVENTS",
        header_events,
    )

    # --------------------------------------------------------
    # matchFacts.events
    # --------------------------------------------------------

    match_facts_events = None

    if isinstance(content, dict):
        match_facts = content.get(
            "matchFacts"
        )

        if isinstance(
            match_facts,
            dict,
        ):
            match_facts_events = (
                match_facts.get(
                    "events"
                )
            )

    print_json(
        "MATCH FACTS EVENTS",
        match_facts_events,
    )

    # --------------------------------------------------------
    # فقط events.events
    # --------------------------------------------------------

    events = None

    if isinstance(
        match_facts_events,
        dict,
    ):
        events = (
            match_facts_events.get(
                "events"
            )
        )

    print_json(
        "EVENTS.EVENTS - FULL LIST",
        events,
    )

    # --------------------------------------------------------
    # تحلیل ساده رویدادها
    # --------------------------------------------------------

    print_separator(
        "EVENT SUMMARY"
    )

    if not isinstance(
        events,
        list,
    ):
        print(
            "events.events پیدا نشد یا لیست نیست."
        )

        return

    print(
        "Total events:",
        len(events),
    )

    for index, event in enumerate(
        events,
        start=1,
    ):
        if not isinstance(
            event,
            dict,
        ):
            continue

        event_type = event.get(
            "type"
        )

        player = event.get(
            "player"
        )

        player_name = None

        if isinstance(
            player,
            dict,
        ):
            player_name = (
                player.get("name")
            )

        if not player_name:
            player_name = event.get(
                "nameStr"
            )

        print()
        print(
            f"EVENT #{index}"
        )
        print(
            "-" * 60
        )

        print(
            "type:",
            event_type,
        )

        print(
            "time:",
            event.get("time"),
        )

        print(
            "isHome:",
            event.get("isHome"),
        )

        print(
            "playerId:",
            event.get("playerId"),
        )

        print(
            "player:",
            player_name,
        )

        # ----------------------------------------------------
        # Goal
        # ----------------------------------------------------

        if event_type == "Goal":

            print()
            print(
                "[GOAL]"
            )

            print(
                "ownGoal:",
                event.get(
                    "ownGoal"
                ),
            )

            print(
                "assistPlayerId:",
                event.get(
                    "assistPlayerId"
                ),
            )

            print(
                "assistInput:",
                event.get(
                    "assistInput"
                ),
            )

            shotmap = event.get(
                "shotmapEvent"
            )

            if isinstance(
                shotmap,
                dict,
            ):
                print(
                    "shotmapEvent.isOwnGoal:",
                    shotmap.get(
                        "isOwnGoal"
                    ),
                )

                print(
                    "shotmapEvent.eventType:",
                    shotmap.get(
                        "eventType"
                    ),
                )

                print(
                    "shotmapEvent.min:",
                    shotmap.get(
                        "min"
                    ),
                )

            # هر فیلدی که ممکن است
            # مربوط به پنالتی باشد
            # را هم نمایش بده
            print()
            print(
                "[PENALTY CANDIDATE FIELDS]"
            )

            for key, value in event.items():
                key_lower = str(
                    key
                ).lower()

                if (
                    "pen" in key_lower
                    or "shoot" in key_lower
                    or "penalty" in key_lower
                ):
                    print(
                        f"{key}:",
                        value,
                    )

            if isinstance(
                shotmap,
                dict,
            ):
                for key, value in shotmap.items():
                    key_lower = str(
                        key
                    ).lower()

                    if (
                        "pen" in key_lower
                        or "shoot" in key_lower
                        or "penalty" in key_lower
                    ):
                        print(
                            f"shotmapEvent.{key}:",
                            value,
                        )

        # ----------------------------------------------------
        # Card
        # ----------------------------------------------------

        elif event_type == "Card":

            print()
            print(
                "[CARD]"
            )

            print(
                "card:",
                event.get(
                    "card"
                ),
            )

            print(
                "cardType:",
                event.get(
                    "cardType"
                ),
            )

            # تمام فیلدهای احتمالی مرتبط
            for key, value in event.items():
                key_lower = str(
                    key
                ).lower()

                if (
                    "card" in key_lower
                    or "red" in key_lower
                    or "yellow" in key_lower
                ):
                    print(
                        f"{key}:",
                        value,
                    )

        # ----------------------------------------------------
        # Substitution
        # ----------------------------------------------------

        elif event_type == "Substitution":

            print()
            print(
                "[SUBSTITUTION]"
            )

            for key in [
                "player",
                "playerId",
                "swap",
                "swapPlayer",
                "substitution",
                "replacement",
                "newPlayer",
                "oldPlayer",
            ]:
                if key in event:
                    print(
                        f"{key}:",
                        json.dumps(
                            event.get(key),
                            ensure_ascii=False,
                            indent=2,
                        ),
                    )

    # --------------------------------------------------------
    # performance.events بازیکنان
    # --------------------------------------------------------

    print_separator(
        "PLAYER PERFORMANCE EVENTS"
    )

    lineup = None

    if isinstance(content, dict):
        lineup = content.get(
            "lineup"
        )

    if not isinstance(
        lineup,
        dict,
    ):
        print(
            "lineup پیدا نشد."
        )

        return

    for team_key in [
        "homeTeam",
        "awayTeam",
    ]:

        team = lineup.get(
            team_key
        )

        if not isinstance(
            team,
            dict,
        ):
            continue

        print()
        print(
            team_key.upper()
        )

        print(
            "-" * 60
        )

        for player_group in [
            "starters",
            "substitutes",
        ]:

            players = team.get(
                player_group
            )

            if not isinstance(
                players,
                list,
            ):
                continue

            for item in players:

                if not isinstance(
                    item,
                    dict,
                ):
                    continue

                player = item.get(
                    "player"
                )

                performance = item.get(
                    "performance"
                )

                if not isinstance(
                    performance,
                    dict,
                ):
                    continue

                player_name = None
                player_id = None

                if isinstance(
                    player,
                    dict,
                ):
                    player_name = (
                        player.get(
                            "name"
                        )
                    )

                    player_id = (
                        player.get(
                            "id"
                        )
                    )

                events_value = (
                    performance.get(
                        "events"
                    )
                )

                if events_value:
                    print()
                    print(
                        "Player:",
                        player_name,
                    )

                    print(
                        "Player ID:",
                        player_id,
                    )

                    print(
                        "Group:",
                        player_group,
                    )

                    print(
                        "Performance events:"
                    )

                    print(
                        json.dumps(
                            events_value,
                            ensure_ascii=False,
                            indent=2,
                        )
                    )

    # --------------------------------------------------------
    # ذخیره کل JSON
    # --------------------------------------------------------

    with open(
        "canada_qatar_raw.json",
        "w",
        encoding="utf-8",
    ) as file:

        json.dump(
            root,
            file,
            ensure_ascii=False,
            indent=2,
        )

    print_separator(
        "DONE"
    )

    print(
        "فایل کامل JSON ذخیره شد:"
    )

    print(
        "canada_qatar_raw.json"
    )


if __name__ == "__main__":
    main()
```

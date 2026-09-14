import json
import re
from html import unescape

import requests


MATCH_URL = (
    "https://www.fotmob.com/matches/"
    "argentina-vs-france/1hox8a#3370572"
)


HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/140.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9",
}


def clean_text(value):
    if value is None:
        return ""

    value = unescape(str(value))
    value = re.sub(r"\s+", " ", value)

    return value.strip()


def fetch_page(url):
    print(f"Fetching: {url}")

    response = requests.get(
        url,
        headers=HEADERS,
        timeout=30,
        allow_redirects=True,
    )

    print("HTTP status:", response.status_code)
    print("Final URL:", response.url)
    print("Response length:", len(response.text))

    response.raise_for_status()

    return response.text


def extract_next_data(html):
    patterns = [
        r'<script[^>]+id="__NEXT_DATA__"[^>]*>(.*?)</script>',
        r'<script[^>]+id="NEXT_DATA__"[^>]*>(.*?)</script>',
    ]

    for pattern in patterns:
        match = re.search(
            pattern,
            html,
            flags=re.DOTALL | re.IGNORECASE,
        )

        if not match:
            continue

        raw_json = match.group(1).strip()

        try:
            return json.loads(raw_json)
        except json.JSONDecodeError as error:
            print("JSON decode error:", error)
            return None

    return None


def get_page_props(next_data):
    if not isinstance(next_data, dict):
        return {}

    props = next_data.get("props")

    if not isinstance(props, dict):
        return {}

    page_props = props.get("pageProps")

    if not isinstance(page_props, dict):
        return {}

    return page_props


def get_content(page_props):
    content = page_props.get("content")

    if isinstance(content, dict):
        return content

    return {}


def recursive_find_all(value, target_key):
    results = []

    if isinstance(value, dict):
        for key, item in value.items():

            if key == target_key:
                results.append(item)

            results.extend(
                recursive_find_all(
                    item,
                    target_key,
                )
            )

    elif isinstance(value, list):
        for item in value:
            results.extend(
                recursive_find_all(
                    item,
                    target_key,
                )
            )

    return results


def print_section(title):
    print()
    print("=" * 80)
    print(title)
    print("=" * 80)


def print_basic_structure(page_props, content):
    print_section("TOP-LEVEL PAGE PROPS KEYS")

    print(
        json.dumps(
            list(page_props.keys()),
            ensure_ascii=False,
            indent=2,
        )
    )

    print_section("CONTENT TOP-LEVEL KEYS")

    print(
        json.dumps(
            list(content.keys()),
            ensure_ascii=False,
            indent=2,
        )
    )


def inspect_status_objects(page_props, content):
    print_section("STATUS-RELATED OBJECTS")

    possible_keys = [
        "status",
        "matchStatus",
        "match_status",
        "state",
        "statusId",
        "statusKey",
        "finished",
        "period",
        "periodName",
        "isFinished",
        "isLive",
        "matchTime",
    ]

    found_any = False

    for key in possible_keys:
        values = recursive_find_all(
            content,
            key,
        )

        if not values:
            values = recursive_find_all(
                page_props,
                key,
            )

        if values:
            found_any = True

            print()
            print(f"KEY: {key}")

            print(
                json.dumps(
                    values[:20],
                    ensure_ascii=False,
                    indent=2,
                )
            )

    if not found_any:
        print("No obvious status keys found.")


def inspect_score_objects(page_props, content):
    print_section("SCORE-RELATED OBJECTS")

    possible_keys = [
        "score",
        "scores",
        "homeScore",
        "awayScore",
        "home_score",
        "away_score",
        "penalty",
        "penalties",
        "shootout",
        "shootoutScore",
        "penaltyShootout",
    ]

    found_any = False

    for key in possible_keys:
        values = recursive_find_all(
            content,
            key,
        )

        if not values:
            values = recursive_find_all(
                page_props,
                key,
            )

        if values:
            found_any = True

            print()
            print(f"KEY: {key}")

            print(
                json.dumps(
                    values[:30],
                    ensure_ascii=False,
                    indent=2,
                )
            )

    if not found_any:
        print("No obvious score keys found.")


def inspect_event_containers(page_props, content):
    print_section("EVENT-RELATED CONTAINERS")

    possible_keys = [
        "events",
        "incidents",
        "event",
        "matchEvents",
        "match_events",
        "commentary",
        "penaltyShootout",
        "penalty-shootout",
        "shootout",
        "penalties",
    ]

    found_any = False

    for key in possible_keys:
        values = recursive_find_all(
            content,
            key,
        )

        if not values:
            values = recursive_find_all(
                page_props,
                key,
            )

        if values:
            found_any = True

            print()
            print(f"KEY: {key}")
            print(f"Number of occurrences: {len(values)}")

            for index, value in enumerate(values[:10]):
                print()
                print(f"Occurrence #{index + 1}")

                try:
                    print(
                        json.dumps(
                            value,
                            ensure_ascii=False,
                            indent=2,
                        )[:12000]
                    )
                except TypeError:
                    print(repr(value))

    if not found_any:
        print("No obvious event containers found.")


def inspect_all_period_stats(content):
    print_section("ALL PERIOD STATS")

    stats_root = content.get("stats")

    if not isinstance(stats_root, dict):
        print("content.stats not found.")
        return

    periods = stats_root.get("Periods")

    if not isinstance(periods, dict):
        print("content.stats.Periods not found.")
        return

    print("Available periods:")

    for period_name in periods.keys():
        print(f"- {period_name}")

    for period_name, period_data in periods.items():

        if not isinstance(period_data, dict):
            continue

        stats = period_data.get("stats")

        if not isinstance(stats, list):
            continue

        print()
        print(f"Period: {period_name}")
        print(f"Number of groups: {len(stats)}")

        for group in stats:

            if not isinstance(group, dict):
                continue

            group_title = (
                group.get("title")
                or group.get("key")
                or ""
            )

            print(f"  Group: {group_title}")

            group_stats = group.get("stats")

            if not isinstance(group_stats, list):
                continue

            for stat in group_stats:

                if not isinstance(stat, dict):
                    continue

                print(
                    "    "
                    f"title={stat.get('title')!r}, "
                    f"key={stat.get('key')!r}, "
                    f"values={stat.get('stats')!r}"
                )


def inspect_events_from_content(content):
    print_section("POSSIBLE EVENT DATA INSIDE CONTENT")

    for key, value in content.items():

        key_lower = str(key).lower()

        if (
            "event" not in key_lower
            and "incident" not in key_lower
            and "comment" not in key_lower
            and "penalty" not in key_lower
            and "shoot" not in key_lower
        ):
            continue

        print()
        print(f"CONTENT KEY: {key}")

        try:
            print(
                json.dumps(
                    value,
                    ensure_ascii=False,
                    indent=2,
                )[:20000]
            )
        except TypeError:
            print(repr(value))


# ============================================================
# MATCH STATE ANALYSIS
# ============================================================

def collect_periods(content):
    """
    Collect every 'period' value found inside the current match content.
    """

    periods = recursive_find_all(
        content,
        "period",
    )

    result = []

    for period in periods:
        if isinstance(period, str):
            result.append(period)

    return result


def collect_penalties(content):
    """
    Collect values stored under 'penalties'.
    """

    penalties = recursive_find_all(
        content,
        "penalties",
    )

    return penalties


def collect_penalty_shootout_events(content):
    """
    Search the match event data for events explicitly marked as
    penalty-shootout events.
    """

    results = []

    def walk(value):

        if isinstance(value, dict):

            if value.get("isPenaltyShootoutEvent") is True:
                results.append(value)

            for item in value.values():
                walk(item)

        elif isinstance(value, list):

            for item in value:
                walk(item)

    walk(content)

    return results


def extract_penalty_score(content):
    """
    Try to extract the final penalty-shootout score.

    FotMob was observed returning:

        penalties: [[4, 2], "Penalties"]

    So we search for a two-number list first.
    """

    penalties = collect_penalties(content)

    for value in penalties:

        if isinstance(value, list):

            for item in value:

                if (
                    isinstance(item, list)
                    and len(item) == 2
                    and all(
                        isinstance(number, int)
                        for number in item
                    )
                ):
                    return item[0], item[1]

    return None


def analyze_match_state(content):
    """
    Analyze the current match state without relying on a simple
    minute >= 90 rule.

    Important:
    90 minutes does NOT automatically mean the match is finished.

    Extra time and penalty shootout are separate states.
    """

    periods = collect_periods(content)

    penalty_events = collect_penalty_shootout_events(
        content
    )

    penalty_score = extract_penalty_score(
        content
    )

    has_regular_first_half = (
        "FirstHalf" in periods
    )

    has_regular_second_half = (
        "SecondHalf" in periods
    )

    has_extra_first_half = (
        "FirstExtraHalf" in periods
    )

    has_extra_second_half = (
        "SecondExtraHalf" in periods
    )

    has_penalty_shootout_period = (
        "PenaltyShootout" in periods
    )

    has_penalty_shootout_events = (
        len(penalty_events) > 0
    )

    has_extra_time = (
        has_extra_first_half
        or has_extra_second_half
    )

    has_penalty_shootout = (
        has_penalty_shootout_period
        or has_penalty_shootout_events
        or penalty_score is not None
    )

    if has_penalty_shootout:

        current_stage = "PenaltyShootout"

    elif has_extra_second_half:

        current_stage = "SecondExtraHalf"

    elif has_extra_first_half:

        current_stage = "FirstExtraHalf"

    elif has_regular_second_half:

        current_stage = "SecondHalf"

    elif has_regular_first_half:

        current_stage = "FirstHalf"

    else:

        current_stage = "Unknown"

    # --------------------------------------------------------
    # IMPORTANT:
    #
    # We deliberately DO NOT say:
    #
    #     second half exists -> finished
    #
    # because a match can continue into extra time.
    #
    # We also do not say:
    #
    #     extra time exists -> finished
    #
    # because the match can continue into a penalty shootout.
    #
    # For this test, the presence of a final penalty score is
    # the strongest indication that the shootout itself has
    # finished.
    # --------------------------------------------------------

    if penalty_score is not None:

        match_finished = True
        finish_reason = (
            "Penalty shootout result detected"
        )

    else:

        match_finished = False
        finish_reason = (
            "No final match-ending signal detected"
        )

    return {
        "periods": periods,
        "current_stage": current_stage,
        "regular_time_detected": (
            has_regular_first_half
            or has_regular_second_half
        ),
        "extra_time_detected": has_extra_time,
        "penalty_shootout_detected": (
            has_penalty_shootout
        ),
        "penalty_shootout_events": len(
            penalty_events
        ),
        "penalty_score": penalty_score,
        "match_finished": match_finished,
        "finish_reason": finish_reason,
    }


def print_match_state_analysis(content):
    print_section("MATCH STATE ANALYSIS")

    result = analyze_match_state(
        content
    )

    print(
        "Detected periods:"
    )

    for period in result["periods"]:
        print(f"- {period}")

    print()

    print(
        "Current stage:",
        result["current_stage"],
    )

    print(
        "Regular time detected:",
        "YES"
        if result["regular_time_detected"]
        else "NO",
    )

    print(
        "Extra time detected:",
        "YES"
        if result["extra_time_detected"]
        else "NO",
    )

    print(
        "Penalty shootout detected:",
        "YES"
        if result["penalty_shootout_detected"]
        else "NO",
    )

    print(
        "Penalty shootout events:",
        result["penalty_shootout_events"],
    )

    if result["penalty_score"] is not None:

        home_penalties, away_penalties = (
            result["penalty_score"]
        )

        print(
            "Penalty score:",
            f"{home_penalties} - {away_penalties}",
        )

    else:

        print(
            "Penalty score:",
            "NOT FOUND",
        )

    print()

    print(
        "MATCH FINISHED:",
        "YES"
        if result["match_finished"]
        else "NO",
    )

    print(
        "Finish reason:",
        result["finish_reason"],
    )


def run_specific_safety_tests(content):
    """
    Tests designed specifically to prevent the common
    mistake of treating 90 minutes as the end of the match.
    """

    print_section("SAFETY TESTS")

    result = analyze_match_state(
        content
    )

    tests_passed = 0
    tests_failed = 0

    # --------------------------------------------------------
    # Test 1:
    # Extra time must be detected.
    # --------------------------------------------------------

    if result["extra_time_detected"]:

        print(
            "PASS: Extra time detected."
        )

        tests_passed += 1

    else:

        print(
            "FAIL: Extra time was not detected."
        )

        tests_failed += 1

    # --------------------------------------------------------
    # Test 2:
    # Penalty shootout must be detected.
    # --------------------------------------------------------

    if result["penalty_shootout_detected"]:

        print(
            "PASS: Penalty shootout detected."
        )

        tests_passed += 1

    else:

        print(
            "FAIL: Penalty shootout was not detected."
        )

        tests_failed += 1

    # --------------------------------------------------------
    # Test 3:
    # Penalty score must be detected.
    # --------------------------------------------------------

    if result["penalty_score"] == (4, 2):

        print(
            "PASS: Penalty score detected as 4 - 2."
        )

        tests_passed += 1

    else:

        print(
            "FAIL: Expected penalty score 4 - 2, "
            f"got {result['penalty_score']!r}."
        )

        tests_failed += 1

    # --------------------------------------------------------
    # Test 4:
    # Final match state must be finished.
    # --------------------------------------------------------

    if result["match_finished"]:

        print(
            "PASS: Match is correctly detected as finished."
        )

        tests_passed += 1

    else:

        print(
            "FAIL: Match should be detected as finished."
        )

        tests_failed += 1

    # --------------------------------------------------------
    # Test 5:
    # Current stage should be PenaltyShootout.
    # --------------------------------------------------------

    if result["current_stage"] == "PenaltyShootout":

        print(
            "PASS: Current stage is PenaltyShootout."
        )

        tests_passed += 1

    else:

        print(
            "FAIL: Expected current stage "
            "PenaltyShootout, "
            f"got {result['current_stage']!r}."
        )

        tests_failed += 1

    print()

    print(
        "Tests passed:",
        tests_passed,
    )

    print(
        "Tests failed:",
        tests_failed,
    )


def save_relevant_json(page_props, content):
    output = {
        "page_props_keys": list(
            page_props.keys()
        ),
        "content_keys": list(
            content.keys()
        ),
        "content": content,
    }

    with open(
        "extra_time_penalty_raw.json",
        "w",
        encoding="utf-8",
    ) as file:

        json.dump(
            output,
            file,
            ensure_ascii=False,
            indent=2,
        )

    print()

    print(
        "Full content saved to "
        "extra_time_penalty_raw.json"
    )


def main():

    try:

        html = fetch_page(
            MATCH_URL
        )

    except Exception as error:

        print(
            "Could not fetch page:"
        )

        print(error)

        return

    next_data = extract_next_data(
        html
    )

    if not next_data:

        print(
            "NEXT_DATA was not found."
        )

        return

    page_props = get_page_props(
        next_data
    )

    if not page_props:

        print(
            "pageProps was not found."
        )

        return

    content = get_content(
        page_props
    )

    if not content:

        print(
            "content was not found."
        )

        return

    print_basic_structure(
        page_props,
        content,
    )

    inspect_status_objects(
        page_props,
        content,
    )

    inspect_score_objects(
        page_props,
        content,
    )

    inspect_event_containers(
        page_props,
        content,
    )

    inspect_events_from_content(
        content,
    )

    inspect_all_period_stats(
        content,
    )

    print_match_state_analysis(
        content,
    )

    run_specific_safety_tests(
        content,
    )

    save_relevant_json(
        page_props,
        content,
    )

    print_section("TEST FINISHED")


if __name__ == "__main__":
    main()

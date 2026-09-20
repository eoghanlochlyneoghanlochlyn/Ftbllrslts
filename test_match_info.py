import json
import re
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse


MATCHES = [
    {
        "name": "Roma - FC Porto",
        "leg": "second",
        "url": "https://www.fotmob.com/matches/roma-vs-fc-porto/2tfyxz#4723944",
    },
    {
        "name": "Roma - FC Porto",
        "leg": "first",
        "url": "https://www.fotmob.com/matches/fc-porto-vs-roma/2tfyxz#4723943",
    },

    {
        "name": "Bodo/Glimt - FC Twente",
        "leg": "second",
        "url": "https://www.fotmob.com/matches/bodoglimt-vs-fc-twente/2e68pm#4723937",
    },
    {
        "name": "FC Twente - Bodo/Glimt",
        "leg": "first",
        "url": "https://www.fotmob.com/matches/fc-twente-vs-bodoglimt/2e68pm#4723936",
    },

    {
        "name": "Lyon - Manchester United",
        "leg": "second",
        "url": "https://www.fotmob.com/matches/lyon-vs-manchester-united/3b6jpk#4737719",
    },
    {
        "name": "Manchester United - Lyon",
        "leg": "first",
        "url": "https://www.fotmob.com/matches/manchester-united-vs-lyon/3b6jpk#4737718",
    },

    {
        "name": "Real Madrid - Benfica",
        "leg": "second",
        "url": "https://www.fotmob.com/matches/real-madrid-vs-benfica/2sumx7#5161859",
    },
    {
        "name": "Benfica - Real Madrid",
        "leg": "first",
        "url": "https://www.fotmob.com/matches/benfica-vs-real-madrid/2sumx7#5161858",
    },

    {
        "name": "Manchester City - Real Madrid",
        "leg": "second",
        "url": "https://www.fotmob.com/matches/manchester-city-vs-real-madrid/2ey0nu#5205731",
    },
    {
        "name": "Real Madrid - Manchester City",
        "leg": "first",
        "url": "https://www.fotmob.com/matches/real-madrid-vs-manchester-city/2ey0nu#5205730",
    },

    {
        "name": "Real Madrid - Bayern",
        "leg": "second",
        "url": "https://www.fotmob.com/matches/real-madrid-vs-bayern-munchen/2tes97#5205791",
    },
    {
        "name": "Bayern - Real Madrid",
        "leg": "first",
        "url": "https://www.fotmob.com/matches/bayern-munchen-vs-real-madrid/2tes97#5205790",
    },
]


HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/140.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9",
}


def extract_match_id(url):
    fragment = urlparse(url).fragment

    if fragment and fragment.isdigit():
        return fragment

    match = re.search(r"#(\d+)", url)

    if match:
        return match.group(1)

    return None


def fetch_match_page(url):
    response = requests.get(
        url,
        headers=HEADERS,
        timeout=30,
    )

    response.raise_for_status()

    return response.text


def extract_next_data(html):
    soup = BeautifulSoup(html, "html.parser")

    script = soup.find(
        "script",
        id="__NEXT_DATA__",
    )

    if not script:
        return None

    try:
        return json.loads(script.string or script.get_text())
    except json.JSONDecodeError:
        return None


def safe_get(data, *keys):
    current = data

    for key in keys:
        if not isinstance(current, dict):
            return None

        current = current.get(key)

    return current


def print_json(label, value):
    print(
        f"{label}: "
        f"{json.dumps(value, ensure_ascii=False, indent=2)}"
    )


def get_leg_info(data):
    possible_paths = [
        (
            "props",
            "pageProps",
            "content",
            "infoBox",
            "legInfo",
        ),
        (
            "props",
            "pageProps",
            "infoBox",
            "legInfo",
        ),
        (
            "props",
            "pageProps",
            "header",
            "infoBox",
            "legInfo",
        ),
    ]

    for path in possible_paths:
        value = safe_get(data, *path)

        if isinstance(value, dict):
            return value

    return None


def get_header(data):
    possible_paths = [
        (
            "props",
            "pageProps",
            "header",
        ),
        (
            "props",
            "pageProps",
            "content",
            "header",
        ),
    ]

    for path in possible_paths:
        value = safe_get(data, *path)

        if isinstance(value, dict):
            return value

    return None


def get_events(data):
    possible_paths = [
        (
            "props",
            "pageProps",
            "content",
            "matchFacts",
            "events",
            "events",
        ),
        (
            "props",
            "pageProps",
            "content",
            "events",
        ),
        (
            "props",
            "pageProps",
            "events",
        ),
    ]

    for path in possible_paths:
        value = safe_get(data, *path)

        if isinstance(value, list):
            return value

    return []


def detect_leg(leg_info):
    if not isinstance(leg_info, dict):
        return None

    localized = leg_info.get("localizedString")

    if isinstance(localized, dict):
        key = localized.get("key")
        fallback = localized.get("fallback")

        if key == "first_leg":
            return "first"

        if key == "second_leg":
            return "second"

        if fallback == "1st leg":
            return "first"

        if fallback == "2nd leg":
            return "second"

    return None


def inspect_match(match):
    print("\n" + "=" * 100)
    print(
        f"{match['name']} | "
        f"EXPECTED: {match['leg'].upper()}"
    )
    print("=" * 100)

    match_id = extract_match_id(match["url"])

    print(f"URL: {match['url']}")
    print(f"URL MATCH ID: {match_id}")

    if not match_id:
        print("ERROR: Could not extract match ID from URL")
        return

    try:
        html = fetch_match_page(match["url"])
    except Exception as e:
        print(f"PAGE ERROR: {e}")
        return

    print(f"PAGE SIZE: {len(html)} bytes")

    data = extract_next_data(html)

    if not data:
        print("ERROR: __NEXT_DATA__ not found")
        return

    print("__NEXT_DATA__: FOUND")

    # ---------------------------------------------------------
    # GENERAL
    # ---------------------------------------------------------

    general = safe_get(
        data,
        "props",
        "pageProps",
        "general",
    )

    print("\n--- GENERAL ---")

    if isinstance(general, dict):

        print_json(
            "matchId",
            general.get("matchId"),
        )

        print_json(
            "matchName",
            general.get("matchName"),
        )

        print_json(
            "leagueName",
            general.get("leagueName"),
        )

        print_json(
            "homeTeam",
            general.get("homeTeam"),
        )

        print_json(
            "awayTeam",
            general.get("awayTeam"),
        )

    else:
        print("GENERAL: NOT FOUND")

    # ---------------------------------------------------------
    # HEADER
    # ---------------------------------------------------------

    header = get_header(data)

    print("\n--- HEADER STATUS ---")

    if isinstance(header, dict):

        status = header.get("status")

        print_json(
            "status",
            status,
        )

        if isinstance(status, dict):

            print_json(
                "aggregatedStr",
                status.get("aggregatedStr"),
            )

            print_json(
                "whoLostOnAggregated",
                status.get("whoLostOnAggregated"),
            )

    else:
        print("HEADER: NOT FOUND")

    # ---------------------------------------------------------
    # LEG INFO
    # ---------------------------------------------------------

    leg_info = get_leg_info(data)

    print("\n--- LEG INFO ---")

    print_json(
        "legInfo",
        leg_info,
    )

    detected_leg = detect_leg(leg_info)

    print(f"Expected leg: {match['leg']}")
    print(f"Detected leg: {detected_leg}")

    if detected_leg == match["leg"]:
        print("LEG DETECTION: PASS")
    elif detected_leg is None:
        print("LEG DETECTION: NOT FOUND")
    else:
        print("LEG DETECTION: FAIL")

    if isinstance(leg_info, dict):

        print_json(
            "bestOf",
            leg_info.get("bestOf"),
        )

        print_json(
            "bestOfNum",
            leg_info.get("bestOfNum"),
        )

        print_json(
            "localizedString",
            leg_info.get("localizedString"),
        )

        print_json(
            "linkToOtherLeg",
            leg_info.get("linkToOtherLeg"),
        )

    # ---------------------------------------------------------
    # EVENTS
    # ---------------------------------------------------------

    events = get_events(data)

    print("\n--- AGGREGATE EVENT DATA ---")

    aggregate_count = 0
    penalty_count = 0

    for index, event in enumerate(events):

        if not isinstance(event, dict):
            continue

        home_aggregate = event.get(
            "homeScoreAggregated"
        )

        away_aggregate = event.get(
            "awayScoreAggregated"
        )

        penalty_shootout = event.get(
            "isPenaltyShootoutEvent"
        )

        if (
            home_aggregate is not None
            or away_aggregate is not None
            or penalty_shootout
        ):

            aggregate_count += 1

            if penalty_shootout:
                penalty_count += 1

            player = event.get("player")

            if isinstance(player, dict):
                player_name = player.get("name")
            else:
                player_name = player

            print(
                f"EVENT {index}: "
                f"type={event.get('type')} | "
                f"player={player_name} | "
                f"aggregate="
                f"{home_aggregate}-{away_aggregate} | "
                f"penaltyShootout="
                f"{penalty_shootout}"
            )

    print(
        f"\nEvents with aggregate information: "
        f"{aggregate_count}"
    )

    print(
        f"Penalty shootout events: "
        f"{penalty_count}"
    )

    # ---------------------------------------------------------
    # SUMMARY
    # ---------------------------------------------------------

    print("\n--- SUMMARY ---")

    aggregate_str = None
    loser = None

    if isinstance(header, dict):

        status = header.get("status")

        if isinstance(status, dict):
            aggregate_str = status.get(
                "aggregatedStr"
            )

            loser = status.get(
                "whoLostOnAggregated"
            )

    print(f"Match ID: {match_id}")
    print(f"Expected leg: {match['leg']}")
    print(f"Detected leg: {detected_leg}")
    print(f"Aggregate: {aggregate_str}")
    print(f"Eliminated team: {loser}")

    if isinstance(leg_info, dict):
        other_leg = leg_info.get(
            "linkToOtherLeg"
        )
    else:
        other_leg = None

    print(
        "Other leg link: "
        f"{'YES' if other_leg else 'NO'}"
    )


def main():

    print("=" * 100)
    print("FOTMOB FIRST LEG / SECOND LEG STRUCTURE TEST")
    print("PAGE + __NEXT_DATA__ VERSION")
    print("=" * 100)

    for match in MATCHES:
        inspect_match(match)

    print("\n" + "=" * 100)
    print("TEST FINISHED")
    print("=" * 100)


if __name__ == "__main__":
    main()

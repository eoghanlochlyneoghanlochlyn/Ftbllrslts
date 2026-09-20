import json
import requests
from typing import Any


MATCHES = [
    # هر دو بازی یک تقابل: رفت + برگشت
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


def extract_match_id(url: str) -> str:
    return url.split("#")[-1]


def get_match_data(match_id: str) -> dict[str, Any]:
    url = f"https://www.fotmob.com/api/matchDetails?matchId={match_id}"

    response = requests.get(
        url,
        headers={
            "User-Agent": "Mozilla/5.0",
            "Accept": "application/json",
        },
        timeout=30,
    )

    response.raise_for_status()
    return response.json()


def safe_get(data: dict, *keys):
    current = data

    for key in keys:
        if not isinstance(current, dict):
            return None

        current = current.get(key)

    return current


def print_value(label: str, value: Any):
    print(f"{label}: {json.dumps(value, ensure_ascii=False)}")


def inspect_match(match: dict):
    match_id = extract_match_id(match["url"])

    print("\n" + "=" * 90)
    print(f"{match['name']} | EXPECTED: {match['leg'].upper()}")
    print(f"MATCH ID: {match_id}")
    print("=" * 90)

    try:
        data = get_match_data(match_id)
    except Exception as e:
        print(f"ERROR: {e}")
        return None

    # ---------------------------------------------------------
    # 1. Header
    # ---------------------------------------------------------

    root = data.get("root", {})

    page_props = safe_get(
        root,
        "props",
        "pageProps",
    )

    header = safe_get(
        root,
        "props",
        "pageProps",
        "header",
    )

    if not isinstance(header, dict):
        print("HEADER: NOT FOUND")
        return None

    status = header.get("status", {})

    print("\n--- BASIC MATCH INFO ---")

    print_value(
        "Home team",
        header.get("teams", [{}])[0] if isinstance(header.get("teams"), list) else None,
    )

    print_value(
        "Status",
        status,
    )

    # ---------------------------------------------------------
    # 2. Leg information
    # ---------------------------------------------------------

    print("\n--- LEG INFO ---")

    info_box = safe_get(
        root,
        "props",
        "pageProps",
        "infoBox",
    )

    leg_info = None

    if isinstance(info_box, dict):
        leg_info = info_box.get("legInfo")

    print_value("legInfo", leg_info)

    if isinstance(leg_info, dict):

        print_value(
            "bestOf",
            leg_info.get("bestOf"),
        )

        print_value(
            "bestOfNum",
            leg_info.get("bestOfNum"),
        )

        print_value(
            "localizedString",
            leg_info.get("localizedString"),
        )

        print_value(
            "linkToOtherLeg",
            leg_info.get("linkToOtherLeg"),
        )

    # ---------------------------------------------------------
    # 3. Aggregate information
    # ---------------------------------------------------------

    print("\n--- AGGREGATE INFO ---")

    aggregated = status.get("aggregatedStr")
    loser = status.get("whoLostOnAggregated")

    print_value(
        "aggregatedStr",
        aggregated,
    )

    print_value(
        "whoLostOnAggregated",
        loser,
    )

    # ---------------------------------------------------------
    # 4. Find events
    # ---------------------------------------------------------

    print("\n--- EVENTS / AGGREGATE SCORES ---")

    events = (
        safe_get(
            root,
            "props",
            "pageProps",
            "content",
            "events",
        )
        or safe_get(
            root,
            "props",
            "pageProps",
            "events",
        )
        or data.get("events")
        or []
    )

    if not isinstance(events, list):
        events = []

    aggregate_events = 0
    penalty_shootout_events = 0

    for index, event in enumerate(events):

        if not isinstance(event, dict):
            continue

        home_agg = event.get("homeScoreAggregated")
        away_agg = event.get("awayScoreAggregated")

        is_penalty = event.get("isPenaltyShootoutEvent")

        if home_agg is not None or away_agg is not None:

            aggregate_events += 1

            print(
                f"EVENT {index}: "
                f"{event.get('type')} | "
                f"{event.get('player', {}).get('name') if isinstance(event.get('player'), dict) else event.get('player')} | "
                f"aggregate={home_agg}-{away_agg} | "
                f"penaltyShootout={is_penalty}"
            )

        if is_penalty:
            penalty_shootout_events += 1

    print_value(
        "Events with aggregate score",
        aggregate_events,
    )

    print_value(
        "Penalty shootout events",
        penalty_shootout_events,
    )

    # ---------------------------------------------------------
    # 5. Compact result for automated comparison
    # ---------------------------------------------------------

    detected_leg = None

    if isinstance(leg_info, dict):

        localized = leg_info.get("localizedString")

        if isinstance(localized, dict):
            key = localized.get("key")
            fallback = localized.get("fallback")

            if key == "second_leg" or fallback == "2nd leg":
                detected_leg = "second"

            elif key == "first_leg" or fallback == "1st leg":
                detected_leg = "first"

    print("\n--- DETECTION RESULT ---")

    print(f"Expected leg : {match['leg']}")
    print(f"Detected leg : {detected_leg}")

    if detected_leg == match["leg"]:
        print("LEG DETECTION: PASS")
    else:
        print("LEG DETECTION: FAIL")

    print(
        f"Aggregate available: "
        f"{'YES' if aggregated is not None else 'NO'}"
    )

    print(
        f"Other leg link available: "
        f"{'YES' if isinstance(leg_info, dict) and leg_info.get('linkToOtherLeg') else 'NO'}"
    )

    return {
        "match_id": match_id,
        "expected_leg": match["leg"],
        "detected_leg": detected_leg,
        "leg_info": leg_info,
        "aggregated_str": aggregated,
        "who_lost_on_aggregated": loser,
        "events_with_aggregate": aggregate_events,
        "penalty_shootout_events": penalty_shootout_events,
    }


def main():

    print("=" * 90)
    print("FOTMOB FIRST LEG / SECOND LEG STRUCTURE TEST")
    print("=" * 90)

    results = []

    for match in MATCHES:
        result = inspect_match(match)

        if result:
            results.append(result)

    print("\n\n" + "=" * 90)
    print("FINAL SUMMARY")
    print("=" * 90)

    for result in results:

        print(
            f"{result['match_id']} | "
            f"expected={result['expected_leg']} | "
            f"detected={result['detected_leg']} | "
            f"aggregate={result['aggregated_str']} | "
            f"other_leg="
            f"{'YES' if result['leg_info'] and result['leg_info'].get('linkToOtherLeg') else 'NO'}"
        )

    print("\nTEST FINISHED.")


if __name__ == "__main__":
    main()

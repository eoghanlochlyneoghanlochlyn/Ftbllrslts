import json

import requests

BASE = "https://www.fotmob.com"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/140.0.0.0 Safari/537.36",
    "Accept": "application/json,text/plain,*/*",
    "Accept-Language": "en-US,en;q=0.9",
    "Referer": BASE + "/",
}

# IMPORTANT:
# The historical test must use a manually fixed reference edition for every
# configured competition. We do NOT let FotMob's "selected/current season"
# decide which edition is used, because that can point to a future/current
# season (for example EURO 2028 or UCL 2026/27).
#
# These are the exact reference editions we want as of 2026-09-24.
#
# The generator deliberately does NOT validate the number of fixtures.
# Whatever fixture IDs FotMob returns for the specified season are frozen into
# historical_test_matches.json and tested one by one later.
REFERENCE_SEASONS = {
    # International tournaments
    "77": "2026",          # FIFA World Cup — explicit user requirement
    "50": "2024",          # UEFA European Championship
    "44": "2024",          # Copa América
    "290": "2023",         # AFC Asian Cup (played Jan-Feb 2024)
    "289": "2023",         # Africa Cup of Nations (played Jan-Feb 2024)
    "9806": "2024/2025",   # UEFA Nations League A

    # Continental / intercontinental club competitions
    "525": "2024/2025",    # AFC Champions League Elite
    "9469": "2024/2025",   # AFC Champions League Two
    "297": "2025",         # CONCACAF Champions Cup
    "526": "2024/2025",    # CAF Champions League
    "45": "2025",          # Copa Libertadores
    "42": "2025/2026",     # UEFA Champions League
    "73": "2025/2026",     # UEFA Europa League
    "10216": "2025/2026",  # UEFA Conference League

    # FIFA club competitions
    "78": "2025",          # FIFA Club World Cup
    "10703": "2025",       # FIFA Intercontinental Cup

    # Domestic cups / super cups — latest fully completed 2025/26 season
    "132": "2025/2026",    # FA Cup
    "133": "2025/2026",    # EFL Cup
    "247": "2025",         # Community Shield
    "138": "2025/2026",    # Copa del Rey
    "139": "2025",         # Supercopa de España
    "141": "2025/2026",    # Coppa Italia
    "11015": "2025",       # Supercoppa Italiana
    "209": "2025/2026",    # DFB-Pokal
    "8924": "2025",        # DFL-Supercup
    "134": "2025/2026",    # Coupe de France
    "207": "2025",         # Trophée des Champions

    # UEFA super cup
    "74": "2025",          # UEFA Super Cup
}


def fetch_league_season(league_id, season):
    params = {"id": league_id, "season": season}
    try:
        r = requests.get(
            f"{BASE}/api/data/leagues",
            params=params,
            headers=HEADERS,
            timeout=45,
        )
        if r.status_code != 200:
            print(f"  {league_id} {season}: HTTP {r.status_code}")
            return {}
        data = r.json()
        return data if isinstance(data, dict) else {}
    except Exception as exc:
        print(f"  {league_id} {season}: request failed: {exc}")
        return {}


def collect_match_ids(payload):
    """
    Extract every fixture ID returned by the specified FotMob league-season
    payload.

    There is intentionally no expected-count check, no finished-match check,
    and no matchDetails validation here. The requested season is authoritative.
    """
    if not payload:
        return []

    candidates = set()

    def add_id(value):
        if value is not None and str(value).isdigit():
            candidates.add(str(value))

    def walk(node):
        if isinstance(node, dict):
            # Common FotMob fixture containers.
            for key in ("matches", "allMatches", "fixtures", "events"):
                value = node.get(key)
                if isinstance(value, list):
                    for item in value:
                        if not isinstance(item, dict):
                            continue
                        add_id(
                            item.get("id")
                            or item.get("matchId")
                            or item.get("matchID")
                            or item.get("eventId")
                            or item.get("eventID")
                        )

            # Also accept a node that is itself a fixture.
            home = node.get("home") or node.get("homeTeam")
            away = node.get("away") or node.get("awayTeam")
            if isinstance(home, dict) and isinstance(away, dict):
                add_id(
                    node.get("id")
                    or node.get("matchId")
                    or node.get("matchID")
                    or node.get("match_id")
                    or node.get("eventId")
                    or node.get("eventID")
                    or node.get("event_id")
                )

            for value in node.values():
                if isinstance(value, (dict, list)):
                    walk(value)

        elif isinstance(node, list):
            for item in node:
                walk(item)

    walk(payload)

    result = sorted(candidates, key=int)
    return result


def main():
    with open("auto_matches.json", "r", encoding="utf-8") as f:
        config = json.load(f)

    configured_ids = {
        str(rule.get("id", "")).strip()
        for rule in config.get("competitions", [])
        if str(rule.get("id", "")).strip()
    }

    missing = sorted(configured_ids - set(REFERENCE_SEASONS))
    if missing:
        raise RuntimeError(
            "Reference season is missing for configured competition IDs: "
            + ", ".join(missing)
        )

    output = {
        "generated_from": "FotMob league structures using manually fixed reference seasons",
        "reference_policy": "Manually fixed per competition; no automatic season selection; no fixture-count validation.",
        "generated_at": None,
        "competitions": [],
    }

    from datetime import datetime, timezone
    output["generated_at"] = datetime.now(timezone.utc).isoformat()

    for rule in config.get("competitions", []):
        league_id = str(rule.get("id", "")).strip()
        if not league_id:
            continue

        season = REFERENCE_SEASONS[league_id]

        print()
        print("=" * 100)
        print(f"COMPETITION {league_id} | FIXED REFERENCE SEASON {season}")

        payload = fetch_league_season(league_id, season)
        match_ids = collect_match_ids(payload)

        if not match_ids:
            raise RuntimeError(
                f"FotMob returned no fixture IDs for configured competition "
                f"{league_id} and fixed season {season}"
            )

        output["competitions"].append({
            "competition_id": league_id,
            "season": season,
            "match_ids": match_ids,
        })

        print(f"  FIXED REFERENCE ACCEPTED: {season}")
        print(f"  fixture ids found: {len(match_ids)}")

    with open("historical_test_matches.json", "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
        f.write("\n")

    total = sum(len(item["match_ids"]) for item in output["competitions"])
    print()
    print(
        f"GENERATED: {len(output['competitions'])} competitions / "
        f"{total} matches"
    )


if __name__ == "__main__":
    main()

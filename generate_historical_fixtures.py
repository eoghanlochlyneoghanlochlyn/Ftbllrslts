import json

import requests

BASE = "https://www.fotmob.com"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/140.0.0.0 Safari/537.36",
    "Accept": "application/json,text/plain,*/*",
    "Accept-Language": "en-US,en;q=0.9",
    "Referer": BASE + "/",
}

# Exact historical reference editions for EVERY competition configured in
# auto_matches.json. These values are deliberately manual: FotMob's current
# selected season must never choose a future edition for this test.
#
# The generator does not validate fixture counts. For the fixed season below,
# every fixture ID returned by FotMob is frozen into historical_test_matches.json.
REFERENCE_SEASONS = {
    # International tournaments
    "77": "2026",          # FIFA World Cup — explicit user requirement
    "50": "2024",          # UEFA European Championship
    "9806": "2024/2025",   # UEFA Nations League A
    "44": "2024",          # Copa América
    "290": "2023",         # AFC Asian Cup (played Jan-Feb 2024)
    "289": "2023",         # Africa Cup of Nations (played Jan-Feb 2024)

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

    # Domestic cups / super cups
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
    "74": "2025",          # UEFA Super Cup

    # World Cup qualifying competitions represented by the current config
    "10607": "2026",       # UEFA World Cup qualifying
    "10199": "2026",       # CONMEBOL World Cup qualifying
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
    and no matchDetails validation here. The manually specified season is
    authoritative.
    """
    if not payload:
        return []

    candidates = set()

    def add_id(value):
        if value is not None and str(value).isdigit():
            candidates.add(str(value))

    def walk(node):
        if isinstance(node, dict):
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
    return sorted(candidates, key=int)


# Super-cup competitions whose historical fixture list must be complete.
# The expected counts are based on the actual tournament formats for the
# fixed reference editions. A mismatch is a hard failure: the generator must
# never silently freeze an incomplete super-cup into the historical manifest.
EXPECTED_SUPERCUP_FIXTURE_COUNTS = {
    "247": 1,
    "139": 3,
    "11015": 3,
    "8924": 1,
    "207": 1,
    "74": 1,
}

PREFERRED_COMPLETE_SOURCES = {
    "11015": ["222", "11015"],
}


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
        "reference_policy": (
            "Manually fixed per configured competition; no automatic season "
            "selection; no fixture-count validation."
        ),
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

        # Some FotMob competition IDs are aliases/season-specific IDs.
        # Example: men's Supercoppa Italiana fixtures have historically
        # appeared under a different ID (222) while the configured stable
        # competition is 11015. For historical completeness we MUST merge
        # the primary ID and every configured alias instead of trusting one
        # endpoint blindly.
        source_ids = [league_id]
        aliases = rule.get("aliases", [])
        if isinstance(aliases, list):
            for alias in aliases:
                alias_text = str(alias).strip()
                if alias_text and alias_text not in source_ids:
                    source_ids.append(alias_text)

        expected_supercup_count = EXPECTED_SUPERCUP_FIXTURE_COUNTS.get(league_id)

        # For super-cups, prefer a source that independently contains the
        # exact expected number of fixtures. This avoids unioning duplicate
        # records exposed by alternate FotMob competition IDs.
        source_order = PREFERRED_COMPLETE_SOURCES.get(league_id, source_ids)
        source_results = {}

        for source_id in source_order:
            if source_id in source_results:
                continue
            source_payload = fetch_league_season(source_id, season)
            source_match_ids = collect_match_ids(source_payload)
            source_results[source_id] = source_match_ids
            print(
                f"  source competition {source_id}: "
                f"{len(source_match_ids)} fixture ids"
            )

        match_ids = []
        selected_source_ids = list(source_results)

        if expected_supercup_count is not None:
            complete = next(
                (
                    ids for ids in source_results.values()
                    if len(ids) == expected_supercup_count
                ),
                None,
            )
            if complete is not None:
                match_ids = sorted(set(complete), key=int)
                selected_source_ids = [
                    source_id
                    for source_id, ids in source_results.items()
                    if len(ids) == expected_supercup_count
                ][:1]
            else:
                # Inspect any remaining aliases before failing.
                for source_id in source_ids:
                    if source_id in source_results:
                        continue
                    source_payload = fetch_league_season(source_id, season)
                    source_match_ids = collect_match_ids(source_payload)
                    source_results[source_id] = source_match_ids
                    print(
                        f"  source competition {source_id}: "
                        f"{len(source_match_ids)} fixture ids"
                    )
                    if len(source_match_ids) == expected_supercup_count:
                        match_ids = sorted(set(source_match_ids), key=int)
                        selected_source_ids = [source_id]
                        break

                if not match_ids:
                    union = set().union(*source_results.values()) if source_results else set()
                    match_ids = sorted(union, key=int)

        else:
            match_id_set = set().union(*source_results.values()) if source_results else set()
            match_ids = sorted(match_id_set, key=int)

        if not match_ids:
            raise RuntimeError(
                f"FotMob returned no fixture IDs for configured competition "
                f"{league_id} (sources: {', '.join(source_ids)}) and "
                f"fixed season {season}"
            )

        if expected_supercup_count is not None:
            if len(match_ids) != expected_supercup_count:
                raise RuntimeError(
                    f"SUPER-CUP COMPLETENESS CHECK FAILED for competition "
                    f"{league_id} / season {season}: expected exactly "
                    f"{expected_supercup_count} fixtures, found {len(match_ids)} "
                    f"from sources {', '.join(source_ids)}"
                )
            print(
                f"  SUPER-CUP COMPLETENESS CHECK: PASS "
                f"({len(match_ids)}/{expected_supercup_count})"
            )


        output["competitions"].append({
            "competition_id": league_id,
            "season": season,
            "match_ids": match_ids,
            "source_competition_ids": source_ids,
        })

        print(f"  FIXED REFERENCE ACCEPTED: {season}")
        print(f"  fixture ids found: {len(match_ids)}")

    with open("historical_test_matches.json", "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
        f.write("\n")

    total = sum(len(item["match_ids"]) for item in output["competitions"])
    print(
        f"\nGENERATED: {len(output['competitions'])} competitions / "
        f"{total} matches"
    )


if __name__ == "__main__":
    main()

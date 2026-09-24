"""One-time generator for the frozen historical competition fixture manifest.

This script is intentionally a data-preparation tool, not part of the test
runtime. It discovers the latest completed season once, extracts every real
fixture, and writes the result to historical_fixtures.py. The generated
manifest is then committed and the network-discovery step is removed from the
regression tests.
"""

import json
import re
from pathlib import Path

import requests

from match_discovery import (
    build_league_stage_map,
    clean_text,
    extract_next_data,
    fetch_match_page_stage,
    load_json,
    normalize_stage,
)

CONFIG_FILE = Path("auto_matches.json")
BENCHMARK_SEASONS = {
    "77": "2026",
    "50": "2024",
    "9806": "2024",
    "44": "2024",
    "290": "2024",
    "289": "2023",
    "297": "2023",
    "525": "2025",
    "9469": "2025",
    "526": "2025",
    "45": "2026",
    "42": "2026",
    "73": "2026",
    "10216": "2025",
    "78": "2025",
    "10703": "2026",
    "247": "2026",
    "139": "2026",
    "11015": "2026",
    "8924": "2026",
    "207": "2026",
    "74": "2026",
    "132": "2025",
    "133": "2025",
    "209": "2026",
    "141": "2026",
    "134": "2026",
    "138": "2026",
    "10607": "2024",
    "10199": "2026",
}

OUTPUT_FILE = Path("historical_fixtures.py")
BASE = "https://www.fotmob.com"
TIMEOUT = 30


def page(url):
    response = requests.get(
        url,
        headers={
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/140.0.0.0 Safari/537.36"
            ),
            "Accept": "text/html,application/xhtml+xml,*/*",
            "Accept-Language": "en-US,en;q=0.9",
        },
        timeout=TIMEOUT,
    )
    response.raise_for_status()
    return response.text


def league(competition_id, season=None):
    url = f"{BASE}/api/data/leagues?id={competition_id}"
    if season:
        url += "&season=" + requests.utils.quote(str(season), safe="/")
    response = requests.get(
        url,
        headers={
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/140.0.0.0 Safari/537.36"
            ),
            "Accept": "application/json,text/plain,*/*",
            "Accept-Language": "en-US,en;q=0.9",
            "Referer": BASE + "/",
        },
        timeout=TIMEOUT,
    )
    response.raise_for_status()
    return response.json()


def season_candidates(competition_id):
    html = page(f"{BASE}/leagues/{competition_id}/fixtures")
    candidates = set()

    # Season links are present in the rendered HTML/Next data on FotMob.
    for match in re.findall(r"(?:season=|season%3D)([0-9]{4}(?:-[0-9]{4})?)", html):
        candidates.add(match)

    data = extract_next_data(html)
    if isinstance(data, dict):
        blob = json.dumps(data, ensure_ascii=False)
        for match in re.findall(r"(?:season|seasonId)[^0-9]{0,20}([0-9]{4}(?:-[0-9]{4})?)", blob):
            candidates.add(match)

    if not candidates:
        raise RuntimeError(
            f"Could not discover season links for competition {competition_id}"
        )

    def sort_key(value):
        years = [int(x) for x in re.findall(r"20[0-9]{2}", value)]
        return years[0] if years else 0

    return sorted(candidates, key=sort_key, reverse=True)


def recursive_find(node, key):
    if isinstance(node, dict):
        if key in node:
            return node[key]
        for value in node.values():
            found = recursive_find(value, key)
            if found is not None:
                return found
    elif isinstance(node, list):
        for value in node:
            found = recursive_find(value, key)
            if found is not None:
                return found
    return None


def extract_matches(node, output):
    if isinstance(node, dict):
        match_id = node.get("id") or node.get("matchId")
        home = node.get("home")
        away = node.get("away")

        if (
            match_id is not None
            and isinstance(home, dict)
            and isinstance(away, dict)
            and (
                home.get("id") or home.get("teamId") or home.get("teamID")
            ) is not None
            and (
                away.get("id") or away.get("teamId") or away.get("teamID")
            ) is not None
        ):
            output.append(node)
            return

        for value in node.values():
            extract_matches(value, output)

    elif isinstance(node, list):
        for value in node:
            extract_matches(value, output)


def finished(match):
    status = match.get("status") or {}
    if status.get("finished") is True or status.get("cancelled") is True:
        return True
    reason = status.get("reason") or {}
    text = " ".join(
        clean_text(reason.get(key))
        for key in ("short", "long", "key")
    ).lower()
    return any(
        marker in text
        for marker in (
            "full-time",
            "full time",
            "after extra time",
            "penalties",
            "ft",
            "aet",
            "cancelled",
        )
    )


def extract_fixture_payload(data, competition_id):
    stage_map = build_league_stage_map(data)
    container = recursive_find(data, "matchesCombinedByRound")

    raw = []
    # The league payload can expose knockout matches under
    # matchesCombinedByRound, while group/league-phase matches live elsewhere.
    # Walk the entire payload so the historical benchmark contains EVERY
    # fixture, not just the knockout tree.
    extract_matches(data, raw)

    result = {}
    for match in raw:
        match_id = str(match.get("id") or match.get("matchId"))
        home = match.get("home") or {}
        away = match.get("away") or {}

        stage = stage_map.get(match_id)
        if stage is None:
            for value in (
                match.get("roundName"),
                match.get("round"),
                match.get("stage"),
            ):
                stage = normalize_stage(value)
                if stage:
                    break

        result[match_id] = {
            "id": match_id,
            "leagueId": str(
                match.get("leagueId")
                or match.get("primaryLeagueId")
                or match.get("tournamentId")
                or competition_id
            ),
            "stage": stage,
            "home": {
                "id": str(
                    home.get("id")
                    or home.get("teamId")
                    or home.get("teamID")
                    or ""
                ),
                "name": clean_text(
                    home.get("longName")
                    or home.get("name")
                    or home.get("shortName")
                ),
            },
            "away": {
                "id": str(
                    away.get("id")
                    or away.get("teamId")
                    or away.get("teamID")
                    or ""
                ),
                "name": clean_text(
                    away.get("longName")
                    or away.get("name")
                    or away.get("shortName")
                ),
            },
        }

    return list(result.values())


def main():
    config = load_json(CONFIG_FILE, {})
    rules = {
        str(rule["id"]): rule
        for rule in config.get("competitions", [])
        if isinstance(rule, dict) and rule.get("id") is not None
    }

    manifest = {}

    for competition_id, rule in rules.items():
        print(f"\n[GENERATE] Competition {competition_id}")

        season = BENCHMARK_SEASONS.get(competition_id)
        if season is None:
            raise RuntimeError(f"No explicit benchmark season configured for {competition_id}")

        print(f"[GENERATE] Using fixed benchmark season {season}")
        data = league(competition_id, season)
        matches = extract_fixture_payload(data, competition_id)

        if not matches:
            raise RuntimeError(
                f"Benchmark season {season} returned no fixtures for competition {competition_id}"
            )

        print(
            f"[GENERATE] Extracted {len(matches)} fixtures from benchmark "
            f"season {season}"
        )

        season, matches = selected
        print(
            f"[GENERATE] {competition_id}: {season} -> {len(matches)} fixtures"
        )

        mode = str(rule.get("mode") or "all").lower()
        if mode in {"from", "final_only"}:
            missing = [m["id"] for m in matches if not m["stage"]]
            for index, match_id in enumerate(missing, 1):
                print(
                    f"[GENERATE] stage fallback {competition_id}: "
                    f"{index}/{len(missing)} match {match_id}"
                )
                stage = fetch_match_page_stage(match_id)
                if stage:
                    next(item for item in matches if item["id"] == match_id)["stage"] = stage

            still_missing = [m["id"] for m in matches if not m["stage"]]
            if still_missing:
                raise RuntimeError(
                    f"Missing stage for {competition_id}: {still_missing[:20]}"
                )

        manifest[competition_id] = {
            "season": season,
            "mode": rule.get("mode"),
            "stage": rule.get("stage"),
            "matches": sorted(matches, key=lambda item: int(item["id"])),
        }

    text = (
        '"""Frozen historical fixtures used by deterministic competition tests.\n\n'
        'Generated once from FotMob historical data. Do not discover seasons or\n'
        'fixtures at test runtime; update this manifest deliberately when the\n'
        'benchmark edition is changed.\n"""\n\n'
        "HISTORICAL_FIXTURES = "
        + repr(manifest)
        + "\n"
    )
    OUTPUT_FILE.write_text(text, encoding="utf-8")
    print(f"[GENERATE] Wrote {OUTPUT_FILE}")


if __name__ == "__main__":
    main()

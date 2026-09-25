import json
from concurrent.futures import ThreadPoolExecutor, as_completed

import requests

from match_discovery import (
    load_team_config,
    selection_reasons,
    fetch_match_page_stage,
    extract_next_data,
)


BASE = "https://www.fotmob.com"
API = f"{BASE}/api/matchDetails"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/140.0.0.0 Safari/537.36",
    "Accept": "application/json,text/plain,*/*",
    "Accept-Language": "en-US,en;q=0.9",
    "Referer": BASE + "/",
}
WORKERS = 12


def recursive_dicts(node):
    if isinstance(node, dict):
        yield node
        for value in node.values():
            yield from recursive_dicts(value)
    elif isinstance(node, list):
        for value in node:
            yield from recursive_dicts(value)


def fetch_match_page_html(match_id):
    """Fetch the real FotMob match page, not the deprecated matchDetails API."""
    url = f"{BASE}/match/{match_id}"
    try:
        r = requests.get(url, headers={**HEADERS, "Accept": "text/html,application/xhtml+xml,*/*"}, timeout=30)
        print(f"FotMob page {match_id}: HTTP {r.status_code}")
        if r.status_code != 200:
            return None
        return r.text
    except requests.RequestException as error:
        print(f"FotMob page {match_id}: ERROR {error}")
        return None


def fetch_match(match_id):
    html = fetch_match_page_html(match_id)
    if html is None:
        return None
    data = extract_next_data(html)
    return data if isinstance(data, dict) else None



def extract_match_object(data):
    for node in recursive_dicts(data):
        home = node.get("homeTeam")
        away = node.get("awayTeam")
        if not isinstance(home, dict) or not isinstance(away, dict):
            continue

        league = node.get("league")
        league_id = None
        if isinstance(league, dict):
            league_id = league.get("id")
        if league_id is None:
            league_id = node.get("leagueId")

        if league_id is None:
            continue

        home_id = home.get("id") or home.get("teamId")
        away_id = away.get("id") or away.get("teamId")
        if home_id is None or away_id is None:
            continue

        return {
            "id": str(
                node.get("matchId")
                or node.get("id")
                or node.get("eventId")
            ),
            "leagueId": str(league_id),
            "home": {
                "id": str(home_id),
                "name": home.get("name") or home.get("longName") or "?",
                "longName": home.get("longName") or home.get("name") or "?",
            },
            "away": {
                "id": str(away_id),
                "name": away.get("name") or away.get("longName") or "?",
                "longName": away.get("longName") or away.get("name") or "?",
            },
        }
    return None


def fetch_stage(match_id):
    try:
        stage = fetch_match_page_stage(match_id)
        return stage
    except Exception as error:
        print(f"Stage {match_id}: ERROR {error}")
        return None


GROUP_TEST_MATCHES = [
    ("5181825", "Netherlands vs Germany"),
    ("5181861", "Denmark vs Norway"),
    ("5181813", "Ireland vs Kosovo"),
    ("5181874", "Malta vs Andorra"),
    ("5181880", "Liechtenstein vs Lithuania"),
    ("4667757", "Canada vs Bosnia and Herzegovina"),
    ("4653852", "England vs Norway"),
]


def inspect_group_structure(data):
    """Return every group-related node with its full JSON path."""
    findings = []

    def walk(node, path):
        if isinstance(node, dict):
            keys = {str(k).lower() for k in node}
            interesting = {
                key: value
                for key, value in node.items()
                if (
                    "group" in str(key).lower()
                    or str(key).lower() in {
                        "leaguename", "league", "stage", "round", "phase", "playoff"
                    }
                )
            }
            if interesting:
                findings.append((path, interesting))
            for key, value in node.items():
                if isinstance(value, (dict, list)):
                    walk(value, f"{path}.{key}")
        elif isinstance(node, list):
            for index, value in enumerate(node):
                if isinstance(value, (dict, list)):
                    walk(value, f"{path}[{index}]")

    walk(data, "$")
    return findings


def run_group_structure_test():
    print("=" * 120)
    print("FOTMOB GROUP STRUCTURE DISCOVERY TEST")
    print("=" * 120)
    print("Goal: discover the REAL group representation in FotMob matchDetails.")
    print("No competition-specific group names are assumed or generated.")
    print()

    all_findings = {}
    for match_id, label in GROUP_TEST_MATCHES:
        data = fetch_match(match_id)
        if data is None:
            print(f"[ERROR] {match_id} | could not fetch/parse FotMob match page")
            all_findings[match_id] = []
            continue

        findings = inspect_group_structure(data)
        all_findings[match_id] = findings

        print("-" * 120)
        print(f"{match_id} | {label}")
        print(f"candidate_nodes={len(findings)}")
        for index, item in enumerate(findings, 1):
            path, item = item
            print(f"  [{index}] PATH={path}")
            print(f"       {json.dumps(item, ensure_ascii=False, default=str)}")

    print()
    print("=" * 120)
    print("GROUP STRUCTURE DISCOVERY SUMMARY")
    print("=" * 120)
    for match_id, label in GROUP_TEST_MATCHES:
        findings = all_findings[match_id]
        print(f"{match_id} | {label} | candidate_nodes={len(findings)}")

    print()
    if not any(all_findings.values()):
        raise AssertionError("No group/stage/league structures were found in any FotMob page payload.")
    print("PASS: real FotMob match-page payloads were fetched and inspected without assuming a group schema.")


def main():
    run_group_structure_test()
    return

    with open("auto_matches.json", "r", encoding="utf-8") as f:
        config = json.load(f)
    with open("historical_test_matches.json", "r", encoding="utf-8") as f:
        manifest = json.load(f)

    selected_team_ids = {
        str(x) for x in config.get("team_ids", []) if str(x).strip()
    }
    by_name, by_country = load_team_config()

    rules = {
        str(rule.get("id")): rule
        for rule in config.get("competitions", [])
        if isinstance(rule, dict)
    }

    total = selected = rejected = inconclusive = errors = 0

    print("=" * 120)
    print("FROZEN HISTORICAL MATCH SELECTION TEST")
    print("=" * 120)
    print("Reference match IDs are fixed in historical_test_matches.json.")
    print("Competition/stage are NOT supplied to selection_reasons().")
    print()

    for block in manifest.get("competitions", []):
        competition_id = str(block["competition_id"])
        season = block["season"]
        match_ids = [str(x) for x in block.get("match_ids", [])]
        rule = rules.get(competition_id)

        if not rule:
            raise AssertionError(f"Manifest competition {competition_id} is missing from auto_matches.json")

        print("=" * 120)
        print(f"COMPETITION {competition_id} | reference season={season} | matches={len(match_ids)}")

        # Fetch every match first; the manifest contributes IDs only.
        fetched = {}
        with ThreadPoolExecutor(max_workers=WORKERS) as pool:
            futures = {pool.submit(fetch_match, mid): mid for mid in match_ids}
            for future in as_completed(futures):
                mid = futures[future]
                data = future.result()
                if data is None:
                    errors += 1
                    print(f"[ERROR] {mid} | matchDetails unavailable")
                    continue
                match = extract_match_object(data)
                if match is None:
                    errors += 1
                    print(f"[ERROR] {mid} | could not normalize real FotMob match object")
                    continue
                fetched[mid] = match

        # Stage is obtained independently from the actual FotMob match page.
        stages = {}
        with ThreadPoolExecutor(max_workers=WORKERS) as pool:
            futures = {pool.submit(fetch_stage, mid): mid for mid in fetched}
            for future in as_completed(futures):
                mid = futures[future]
                stages[mid] = future.result()

        for index, mid in enumerate(match_ids, 1):
            total += 1
            match = fetched.get(mid)
            if match is None:
                print(f"[{index}/{len(match_ids)}] {mid} | ERROR")
                continue

            stage = stages.get(mid)
            if stage:
                match["stage"] = stage

            # IMPORTANT:
            # No competition ID, stage, or expected status is injected here.
            # selection_reasons() sees the real leagueId/team IDs from FotMob
            # and the stage extracted by the production stage resolver.
            reasons = selection_reasons(
                match,
                config,
                selected_team_ids,
                by_name,
                by_country,
            )

            status = "SELECT" if reasons else "REJECT"

            if status == "SELECT":
                selected += 1
            else:
                rejected += 1

            home = match["home"]["longName"]
            away = match["away"]["longName"]

            print(
                f"[{index}/{len(match_ids)}] "
                f"{mid} | {home} vs {away} | "
                f"leagueId={match['leagueId']} | "
                f"stage={stage or 'UNKNOWN'} | "
                f"{status} | "
                f"reason={','.join(reasons) if reasons else 'no_selection_rule'}"
            )

            if rule.get("mode") in {"from", "final_only"} and not stage and not reasons:
                inconclusive += 1

    print()
    print("=" * 120)
    print("FINAL SUMMARY")
    print("=" * 120)
    print(f"competitions: {len(manifest.get('competitions', []))}")
    print(f"matches: {total}")
    print(f"selected: {selected}")
    print(f"rejected: {rejected}")
    print(f"inconclusive: {inconclusive}")
    print(f"errors: {errors}")

    if errors or inconclusive:
        raise AssertionError(
            f"Historical test failed: errors={errors}, inconclusive={inconclusive}"
        )

    print("PASS")
    

if __name__ == "__main__":
    main()

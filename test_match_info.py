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


API_NEW = f"{BASE}/api/data/matchDetails"
LTC_API = f"{BASE}/api/data/ltc"
TEST_MATCH_ID = "5868463"


def _get_path(node, path):
    current = node
    for part in path:
        if not isinstance(current, dict) or part not in current:
            return None
        current = current[part]
    return current


def _walk(node, path="$"):
    """Yield every dict/list node with its JSON path."""
    yield path, node
    if isinstance(node, dict):
        for key, value in node.items():
            yield from _walk(value, f"{path}.{key}")
    elif isinstance(node, list):
        for index, value in enumerate(node):
            yield from _walk(value, f"{path}[{index}]")


def _find_nodes(data, predicate):
    findings = []
    for path, node in _walk(data):
        if isinstance(node, (dict, list)) and predicate(node):
            findings.append((path, node))
    return findings


def _first_matching_dict(data, required_keys):
    required = {str(x).lower() for x in required_keys}
    for path, node in _walk(data):
        if isinstance(node, dict):
            keys = {str(k).lower() for k in node.keys()}
            if required.issubset(keys):
                return path, node
    return None, None


def _compact(value, limit=500):
    try:
        text = json.dumps(value, ensure_ascii=False, default=str)
    except Exception:
        text = repr(value)
    return text if len(text) <= limit else text[:limit] + "...<truncated>"


def _print_section(name, status, detail=""):
    print(f"{name}: {'PASS' if status else 'FAIL'}" + (f" | {detail}" if detail else ""))


def fetch_current_match_api(match_id):
    url = f"{API_NEW}?matchId={match_id}"
    response = requests.get(url, headers=HEADERS, timeout=30)
    print(f"API URL: {url}")
    print(f"HTTP status: {response.status_code}")
    print(f"Elapsed/request completed")
    print(f"Content-Type: {response.headers.get('content-type', '')}")
    print(f"Cache-Control: {response.headers.get('cache-control', '')}")
    print(f"Response length: {len(response.content)} bytes")
    response.raise_for_status()
    payload = response.json()
    if not isinstance(payload, dict):
        raise AssertionError(f"API response is not a JSON object: {type(payload).__name__}")
    return payload


def inspect_lineups(data):
    candidates = []
    for path, node in _walk(data):
        if not isinstance(node, dict):
            continue
        lowered = {str(k).lower(): k for k in node.keys()}
        if "lineups" in lowered and isinstance(node[lowered["lineups"]], list):
            candidates.append((path, node[lowered["lineups"]], node))

    best = None
    for path, lineups, parent in candidates:
        teams = []
        for item in lineups:
            if not isinstance(item, dict):
                continue
            players = item.get("players") or item.get("lineup") or []
            if isinstance(players, list):
                starters = [
                    p for p in players
                    if isinstance(p, dict)
                    and (
                        p.get("isStarter") is True
                        or p.get("starter") is True
                        or p.get("positionId") is not None
                        or p.get("position") is not None
                    )
                ]
                teams.append((item, players, starters))
        if teams:
            best = (path, teams)
            break

    if not best:
        _print_section("LINEUPS", False, "No lineup array found")
        return False

    path, teams = best
    print(f"Lineup path: {path}")
    total_players = 0
    team_ok = 0
    for index, (team, players, starters) in enumerate(teams, 1):
        team_name = team.get("teamName") or team.get("name") or team.get("teamId") or f"team#{index}"
        total_players += len(players)
        print(f"  {team_name}: players={len(players)}, candidate_starters={len(starters)}")
        if len(starters) >= 11:
            team_ok += 1

    # Some FotMob schemas expose starters separately; recursively inspect the
    # lineup node as a fallback instead of assuming one exact player schema.
    lineup_blob = _compact(_get_path(data, tuple(path.strip("$").strip(".").split(".")))) if path != "$" else _compact(data)
    print(f"  Sample: {lineup_blob[:700]}")
    ok = len(teams) >= 2 and team_ok >= 2
    _print_section("LINEUPS", ok, f"teams={len(teams)}, total_players={total_players}")
    return ok


def inspect_events(data):
    event_candidates = []
    for path, node in _walk(data):
        if isinstance(node, dict):
            for key, value in node.items():
                if str(key).lower() in {"events", "event", "incidents", "incident"} and isinstance(value, list):
                    event_candidates.append((f"{path}.{key}", value))

    best_path, events = None, None
    if event_candidates:
        # Prefer the largest event list; match details often contain the most
        # complete chronological list in content.matchFacts.
        best_path, events = max(event_candidates, key=lambda x: len(x[1]))

    if not events:
        _print_section("EVENTS", False, "No event/incident array found")
        return False

    counts = {}
    for event in events:
        if not isinstance(event, dict):
            continue
        raw_type = (
            event.get("type")
            or event.get("eventType")
            or event.get("incidentType")
            or event.get("incidentClass")
            or "unknown"
        )
        key = str(raw_type).lower()
        counts[key] = counts.get(key, 0) + 1

    print(f"Event path: {best_path}")
    print(f"Total event objects: {len(events)}")
    print(f"Event type counts: {json.dumps(counts, ensure_ascii=False)}")
    print("First events:")
    for event in events[:8]:
        print(f"  {_compact(event, 900)}")

    required_categories = {
        "goal": any("goal" in key for key in counts),
        "card": any("card" in key or "yellow" in key or "red" in key for key in counts),
        "substitution": any("sub" in key for key in counts),
    }
    print(f"Required event categories: {json.dumps(required_categories, ensure_ascii=False)}")
    ok = len(events) > 0 and required_categories["goal"]
    _print_section("EVENTS", ok, f"path={best_path}")
    return ok


def inspect_status_and_score(data):
    status_nodes = []
    for path, node in _walk(data):
        if isinstance(node, dict):
            keys = {str(k).lower() for k in node}
            if "finished" in keys and ("started" in keys or "scorestr" in keys or "reason" in keys):
                status_nodes.append((path, node))

    if not status_nodes:
        _print_section("MATCH STATUS", False, "No status object with started/finished/score fields found")
        return False

    path, status = status_nodes[0]
    started = status.get("started")
    finished = status.get("finished")
    score = status.get("scoreStr") or status.get("score")
    reason = status.get("reason")
    print(f"Status path: {path}")
    print(f"  started={started} finished={finished} score={score} reason={reason}")
    ok = started is True and finished is True and score not in (None, "", "-")
    _print_section("MATCH STATUS", ok)
    return ok


def inspect_stats(data):
    stat_arrays = []
    for path, node in _walk(data):
        if isinstance(node, dict):
            for key, value in node.items():
                if str(key).lower() in {"stats", "statistics"} and isinstance(value, list):
                    stat_arrays.append((f"{path}.{key}", value))

    if not stat_arrays:
        _print_section("TEAM STATS", False, "No stats array found")
        return False

    path, stats = max(stat_arrays, key=lambda x: len(x[1]))
    titles = []
    for item in stats:
        if isinstance(item, dict):
            title = item.get("title") or item.get("name") or item.get("stat")
            if title is not None:
                titles.append(str(title))

    print(f"Stats path: {path}")
    print(f"Stats count: {len(stats)}")
    print(f"Stats titles: {json.dumps(titles[:80], ensure_ascii=False)}")
    wanted = ["xg", "expected goals", "possession", "shots", "passes", "accurate passes"]
    found = [title for title in titles if any(w in title.lower() for w in wanted)]
    print(f"Relevant stats found: {json.dumps(found, ensure_ascii=False)}")
    ok = len(stats) > 0
    _print_section("TEAM STATS", ok)
    return ok


def inspect_player_ratings(data):
    rating_hits = []
    player_hits = 0
    for path, node in _walk(data):
        if not isinstance(node, dict):
            continue
        keys = {str(k).lower() for k in node}
        if any(k in keys for k in {"rating", "ratingnum", "matchrating"}):
            rating = node.get("rating", node.get("ratingNum", node.get("matchRating")))
            if rating is not None:
                rating_hits.append((path, rating, node))
        if any(k in keys for k in {"playername", "player", "name"}) and (
            "rating" in keys or "ratingnum" in keys or "matchrating" in keys
        ):
            player_hits += 1

    print(f"Rating fields found: {len(rating_hits)}")
    for path, rating, node in rating_hits[:10]:
        print(f"  {path}: rating={rating} | {_compact(node, 500)}")
    ok = len(rating_hits) > 0
    _print_section("PLAYER RATINGS", ok)
    return ok


def inspect_player_stats(data):
    player_stat_nodes = []
    for path, node in _walk(data):
        if isinstance(node, dict):
            lowered = {str(k).lower() for k in node}
            if any(k in lowered for k in {"playerstats", "players", "player"}) and any(
                k in lowered for k in {"stats", "statistics"}
            ):
                player_stat_nodes.append((path, node))

    print(f"Player-stat candidate nodes: {len(player_stat_nodes)}")
    for path, node in player_stat_nodes[:10]:
        print(f"  {path}: keys={list(node.keys())[:30]}")
    ok = len(player_stat_nodes) > 0
    _print_section("PLAYER STATS", ok)
    return ok


def inspect_raw_structure(data):
    print()
    print("TOP-LEVEL KEYS:", list(data.keys()))
    for key in data:
        value = data[key]
        if isinstance(value, dict):
            print(f"  {key}: dict keys={list(value.keys())[:40]}")
        elif isinstance(value, list):
            print(f"  {key}: list length={len(value)}")
        else:
            print(f"  {key}: {type(value).__name__}")


def test_direct_fotmob_api():
    """Comprehensive read-only diagnostic of FotMob's current matchDetails API."""
    import time

    print("=" * 120)
    print("FOTMOB CURRENT API COMPREHENSIVE TEST")
    print("=" * 120)
    print(f"Match ID: {TEST_MATCH_ID}")
    print("This test only reads the current FotMob API and does NOT modify production files.")
    print()

    started_at = time.perf_counter()
    data = fetch_current_match_api(TEST_MATCH_ID)
    print(f"Total API test fetch time: {time.perf_counter() - started_at:.3f}s")
    print()

    inspect_raw_structure(data)

    results = []
    results.append(("MATCH STATUS", inspect_status_and_score(data)))
    results.append(("LINEUPS", inspect_lineups(data)))
    results.append(("EVENTS", inspect_events(data)))
    results.append(("TEAM STATS", inspect_stats(data)))
    results.append(("PLAYER RATINGS", inspect_player_ratings(data)))
    results.append(("PLAYER STATS", inspect_player_stats(data)))

    print()
    print("=" * 120)
    print("API COMPREHENSIVE TEST SUMMARY")
    print("=" * 120)
    for name, passed in results:
        print(f"{name}: {'PASS' if passed else 'FAIL'}")

    print()
    print("IMPORTANT:")
    print("- A PASS means the current API payload contains usable data for that category.")
    print("- A FAIL means the payload shape needs inspection before production code is changed.")
    print("- This test intentionally does not change fotmob.py or any other production file.")
    print()
    print("LTC/LIVE-TICKER DISCOVERY")
    liveticker = _get_path(data, ("content", "liveticker"))
    if isinstance(liveticker, dict):
        print(f"liveticker keys: {list(liveticker.keys())}")
        ltc_url = liveticker.get("ltcUrl") or liveticker.get("ltcURL") or liveticker.get("url")
        if ltc_url:
            print(f"ltcUrl found: {ltc_url}")
            try:
                from urllib.parse import quote
                ltc_endpoint = f"{LTC_API}?ltcUrl={quote(str(ltc_url), safe='')}"
                ltc_response = requests.get(ltc_endpoint, headers=HEADERS, timeout=30)
                print(f"LTC HTTP status: {ltc_response.status_code}")
                print(f"LTC response length: {len(ltc_response.content)} bytes")
                if ltc_response.status_code == 200:
                    ltc_data = ltc_response.json()
                    print(f"LTC top-level type: {type(ltc_data).__name__}")
                    if isinstance(ltc_data, dict):
                        print(f"LTC keys: {list(ltc_data.keys())[:40]}")
                    print(f"LTC sample: {_compact(ltc_data, 1800)}")
                else:
                    print(f"LTC first 300 chars: {ltc_response.text[:300]!r}")
            except Exception as error:
                print(f"LTC ERROR: {error}")
        else:
            print("No ltcUrl found in content.liveticker.")
    else:
        print("No content.liveticker object found.")

    print()
    print("FINAL API TEST RESULT")
    failed = [name for name, passed in results if not passed]
    if failed:
        print(f"INCOMPLETE: {', '.join(failed)}")
    else:
        print("PASS: all requested match-data categories were detected.")


def main():
    test_direct_fotmob_api()
    return


def test_extract_group_info_uses_current_match_league_only():
    from fotmob import extract_group_info

    data = {
        "props": {
            "pageProps": {
                "general": {"leagueName": "UEFA Nations League A Grp. 2"},
                "content": {
                    "h2h": {"matches": [{"league": {"name": "EURO Grp. B"}}]},
                    "matchFacts": {
                        "infoBox": {
                            "Tournament": {"leagueName": "UEFA Nations League A Grp. 2"}
                        }
                    },
                },
            }
        }
    }
    result = extract_group_info(data)
    assert result["raw"] == "2"
    assert result["name_fa"] == "گروه 2"
    assert result["source"] == "props.pageProps.general.leagueName"


def test_extract_group_info_returns_none_for_knockout_match():
    from fotmob import extract_group_info

    data = {
        "props": {
            "pageProps": {
                "general": {"leagueName": "World Cup"},
                "content": {
                    "matchFacts": {
                        "infoBox": {
                            "Tournament": {"leagueName": "World Cup"}
                        }
                    },
                    "h2h": {
                        "matches": [
                            {"league": {"name": "World Cup Grp. B"}}
                        ]
                    },
                },
            }
        }
    }
    result = extract_group_info(data)
    assert result["raw"] is None
    assert result["name_fa"] is None


def test_extract_group_info_supports_explicit_is_group_schema():
    from fotmob import extract_group_info

    data = {"props": {"pageProps": {"general": {"isGroup": True, "groupName": "A"}}}}
    result = extract_group_info(data)
    assert result["raw"] == "A"
    assert result["name_fa"] == "گروه A"

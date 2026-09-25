import json
import time

import requests

BASE = "https://www.fotmob.com"
API_NEW = f"{BASE}/api/data/matchDetails"
LTC_API = f"{BASE}/api/data/ltc"
TEST_MATCH_ID = "5868463"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/140.0.0.0 Safari/537.36",
    "Accept": "application/json,text/plain,*/*",
    "Accept-Language": "en-US,en;q=0.9",
    "Referer": BASE + "/",
}


def walk(node, path="$"):
    yield path, node
    if isinstance(node, dict):
        for key, value in node.items():
            yield from walk(value, f"{path}.{key}")
    elif isinstance(node, list):
        for i, value in enumerate(node):
            yield from walk(value, f"{path}[{i}]")


def compact(value, limit=900):
    try:
        raw = json.dumps(value, ensure_ascii=False, default=str)
    except Exception:
        raw = repr(value)
    return raw if len(raw) <= limit else raw[:limit] + "...<truncated>"


def section(name, ok, detail=""):
    print(f"{name}: {'PASS' if ok else 'FAIL'}" + (f" | {detail}" if detail else ""))


def fetch_api():
    url = f"{API_NEW}?matchId={TEST_MATCH_ID}"
    print("=" * 100)
    print("FOTMOB CURRENT API COMPREHENSIVE TEST")
    print("=" * 100)
    print(f"Match ID: {TEST_MATCH_ID}")
    print(f"API URL: {url}")
    started = time.perf_counter()
    response = requests.get(url, headers=HEADERS, timeout=30)
    elapsed = time.perf_counter() - started
    print(f"HTTP status: {response.status_code}")
    print(f"Elapsed: {elapsed:.3f}s")
    print(f"Content-Type: {response.headers.get('content-type', '')}")
    print(f"Cache-Control: {response.headers.get('cache-control', '')}")
    print(f"Response length: {len(response.content)} bytes")
    response.raise_for_status()
    data = response.json()
    if not isinstance(data, dict):
        raise AssertionError(f"Expected JSON object, got {type(data).__name__}")
    print(f"Top-level keys: {list(data.keys())}")
    return data


def find_key_nodes(data, wanted):
    wanted = {x.lower() for x in wanted}
    hits = []
    for path, node in walk(data):
        if isinstance(node, dict):
            for key, value in node.items():
                if str(key).lower() in wanted:
                    hits.append((f"{path}.{key}", value))
    return hits


def inspect_status(data):
    candidates = []
    for path, node in walk(data):
        if not isinstance(node, dict):
            continue
        keys = {str(k).lower() for k in node}
        if ("started" in keys or "finished" in keys or "statusid" in keys) and (
            "scorestr" in keys or "score" in keys or "reason" in keys
        ):
            candidates.append((path, node))
    print("\nMATCH STATUS / RESULT")
    for path, node in candidates[:5]:
        print(f"  {path}: {compact(node, 1200)}")
    ok = bool(candidates)
    section("MATCH STATUS / RESULT", ok, f"candidate_objects={len(candidates)}")
    return ok


def inspect_lineups(data):
    hits = find_key_nodes(data, {"lineups", "lineup"})
    print("\nLINEUPS")
    useful = []
    for path, value in hits:
        if isinstance(value, (dict, list)):
            useful.append((path, value))
            print(f"  {path}: type={type(value).__name__}, size={len(value) if hasattr(value, '__len__') else '?'}")
            print(f"    {compact(value, 1400)}")
    ok = bool(useful)
    section("LINEUPS", ok, f"candidate_nodes={len(useful)}")
    return ok


def inspect_events(data):
    hits = find_key_nodes(data, {"events", "incidents"})
    print("\nEVENTS / INCIDENTS")
    useful = [(p, v) for p, v in hits if isinstance(v, list) and v]
    for path, events in useful[:8]:
        print(f"  {path}: {len(events)} objects")
        for event in events[:8]:
            print(f"    {compact(event, 1000)}")
    all_events = [v for _, v in useful]
    ok = bool(all_events)
    categories = set()
    for events in all_events:
        for event in events:
            if isinstance(event, dict):
                raw = " ".join(str(event.get(k, "")) for k in ("type", "eventType", "incidentType", "incidentClass")).lower()
                if "goal" in raw:
                    categories.add("goal")
                if "card" in raw or "yellow" in raw or "red" in raw:
                    categories.add("card")
                if "sub" in raw:
                    categories.add("substitution")
    print(f"  Detected categories: {sorted(categories)}")
    section("EVENTS / INCIDENTS", ok, f"non_empty_arrays={len(useful)}")
    return ok


def inspect_team_stats(data):
    hits = find_key_nodes(data, {"stats", "statistics"})
    useful = [(p, v) for p, v in hits if isinstance(v, list) and v]
    print("\nTEAM STATS")
    for path, stats in useful[:6]:
        print(f"  {path}: {len(stats)} objects")
        for item in stats[:12]:
            print(f"    {compact(item, 700)}")
    ok = bool(useful)
    section("TEAM STATS", ok, f"non_empty_arrays={len(useful)}")
    return ok


def inspect_player_ratings(data):
    hits = []
    for path, node in walk(data):
        if not isinstance(node, dict):
            continue
        keys = {str(k).lower() for k in node}
        rating_keys = {"rating", "ratingnum", "matchrating"} & keys
        if rating_keys:
            rating_key = next(iter(rating_keys))
            if node.get(rating_key) is not None:
                hits.append((path, rating_key, node.get(rating_key), node))
    print("\nPLAYER RATINGS")
    for path, key, rating, node in hits[:15]:
        print(f"  {path}: {key}={rating} | {compact(node, 800)}")
    ok = bool(hits)
    section("PLAYER RATINGS", ok, f"rating_fields={len(hits)}")
    return ok


def inspect_player_stats(data):
    hits = []
    for path, node in walk(data):
        if not isinstance(node, dict):
            continue
        keys = {str(k).lower() for k in node}
        has_player = bool({"player", "playername", "playerid", "playerid"} & keys)
        has_stats = bool({"stats", "statistics"} & keys)
        if has_player and has_stats:
            hits.append((path, node))
    print("\nPLAYER STATS")
    for path, node in hits[:10]:
        print(f"  {path}: {compact(node, 1000)}")
    ok = bool(hits)
    section("PLAYER STATS", ok, f"candidate_objects={len(hits)}")
    return ok


def inspect_liveticker(data):
    print("\nLIVE TICKER")
    candidates = find_key_nodes(data, {"liveticker"})
    for path, value in candidates[:5]:
        print(f"  {path}: {compact(value, 1400)}")
    liveticker = None
    for _, value in candidates:
        if isinstance(value, dict):
            liveticker = value
            break
    if not liveticker:
        section("LIVE TICKER", False, "content.liveticker not found")
        return False
    ltc_url = liveticker.get("ltcUrl") or liveticker.get("ltcURL") or liveticker.get("url")
    if not ltc_url:
        section("LIVE TICKER", True, "liveticker object exists; no ltcUrl exposed")
        return True

    url = f"{LTC_API}?ltcUrl={requests.utils.quote(str(ltc_url), safe='')}"
    try:
        started = time.perf_counter()
        response = requests.get(url, headers=HEADERS, timeout=30)
        elapsed = time.perf_counter() - started
        print(f"  LTC URL: {url}")
        print(f"  LTC status={response.status_code}, elapsed={elapsed:.3f}s, bytes={len(response.content)}")
        if response.status_code == 200:
            payload = response.json()
            print(f"  LTC type={type(payload).__name__}")
            print(f"  LTC sample={compact(payload, 1800)}")
            section("LTC ENDPOINT", True)
            return True
        print(f"  LTC body={response.text[:500]!r}")
    except Exception as error:
        print(f"  LTC ERROR: {error}")
    section("LTC ENDPOINT", False)
    return False


def main():
    data = fetch_api()
    results = [
        ("MATCH STATUS / RESULT", inspect_status(data)),
        ("LINEUPS", inspect_lineups(data)),
        ("EVENTS / INCIDENTS", inspect_events(data)),
        ("TEAM STATS", inspect_team_stats(data)),
        ("PLAYER RATINGS", inspect_player_ratings(data)),
        ("PLAYER STATS", inspect_player_stats(data)),
        ("LIVE TICKER", inspect_liveticker(data)),
    ]

    print("\n" + "=" * 100)
    print("FINAL SUMMARY")
    print("=" * 100)
    for name, ok in results:
        print(f"{name}: {'PASS' if ok else 'FAIL'}")
    print()
    failed = [name for name, ok in results if not ok]
    if failed:
        print("INCOMPLETE:", ", ".join(failed))
        print("The API was reachable, but one or more required categories were not detected.")
    else:
        print("PASS: all requested categories were detected.")
    print("No production files were imported or modified by this test.")


if __name__ == "__main__":
    main()

import json
from concurrent.futures import ThreadPoolExecutor, as_completed

import requests

from match_discovery import fetch_league_structure

BASE = "https://www.fotmob.com"
API = f"{BASE}/api/matchDetails"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/140.0.0.0 Safari/537.36",
    "Accept": "application/json,text/plain,*/*",
    "Accept-Language": "en-US,en;q=0.9",
    "Referer": BASE + "/",
}
WORKERS = 12

# Competition seasons that are not safely represented by "previous season"
# because the 2026 edition is the completed reference edition.
FIXED_REFERENCE_SEASONS = {
    "77": "2026",  # FIFA World Cup 2026
}


def fetch_match(match_id):
    try:
        r = requests.get(
            API,
            params={"matchId": match_id},
            headers=HEADERS,
            timeout=30,
        )
        if r.status_code != 200:
            return None
        data = r.json()
        return data if isinstance(data, dict) else None
    except Exception:
        return None


def recursive_dicts(node):
    if isinstance(node, dict):
        yield node
        for value in node.values():
            yield from recursive_dicts(value)
    elif isinstance(node, list):
        for value in node:
            yield from recursive_dicts(value)


def extract_general(data):
    for node in recursive_dicts(data):
        home = node.get("homeTeam")
        away = node.get("awayTeam")
        league = node.get("league")
        if isinstance(home, dict) and isinstance(away, dict):
            if isinstance(league, dict) or node.get("leagueId") is not None:
                return node
    return None


def actual_league_id(data):
    node = extract_general(data)
    if not node:
        return None
    league = node.get("league")
    if isinstance(league, dict):
        value = league.get("id")
        if value is not None:
            return str(value)
    value = node.get("leagueId")
    return str(value) if value is not None else None


def match_is_finished(data):
    for node in recursive_dicts(data):
        status = node.get("status")
        if isinstance(status, dict):
            if status.get("finished") is True:
                return True
            reason = status.get("reason")
            if isinstance(reason, dict):
                reason = reason.get("long") or reason.get("short") or reason.get("key")
            if str(reason or "").strip().lower() in {
                "ft", "aet", "after penalties", "finished", "full-time"
            }:
                return True
    return False


def season_candidates(league_id):
    current = fetch_league_season(league_id, None)
    details = current.get("details", {}) if isinstance(current, dict) else {}
    selected = str(details.get("selectedSeason") or "").strip()

    if league_id in FIXED_REFERENCE_SEASONS:
        return [FIXED_REFERENCE_SEASONS[league_id]]

    result = []
    if selected:
        result.append(selected)

        if "/" in selected:
            a, b = selected.split("/", 1)
            if a.isdigit() and b.isdigit():
                length = int(b) - int(a)
                if 0 < length <= 4:
                    for step in range(1, 4):
                        result.append(f"{int(a)-step*length}/{int(b)-step*length}")
        elif selected.isdigit() and len(selected) == 4:
            for step in range(1, 4):
                result.append(str(int(selected)-step))

    return list(dict.fromkeys(result))


def fetch_league_season(league_id, season):
    params = {"id": league_id}
    if season:
        params["season"] = season
    try:
        r = requests.get(
            f"{BASE}/api/data/leagues",
            params=params,
            headers=HEADERS,
            timeout=45,
        )
        if r.status_code != 200:
            return {}
        data = r.json()
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def collect_valid_match_ids(league_id, season):
    payload = fetch_league_season(league_id, season)
    if not payload:
        return []

    candidates = sorted(_collect_match_ids(payload), key=lambda x: int(x))
    print(f"  {league_id} {season}: raw candidate ids={len(candidates)}")

    valid = []
    with ThreadPoolExecutor(max_workers=WORKERS) as pool:
        futures = {pool.submit(fetch_match, mid): mid for mid in candidates}
        for future in as_completed(futures):
            mid = futures[future]
            data = future.result()
            if not data:
                continue
            lid = actual_league_id(data)
            aliases = {str(league_id)}
            if lid in aliases:
                valid.append(mid)

    valid = sorted(set(valid), key=lambda x: int(x))
    print(f"  {league_id} {season}: verified matches={len(valid)}")
    return candidates


def season_is_complete(league_id, season, match_ids):
    if not match_ids:
        return False
    finished = 0
    with ThreadPoolExecutor(max_workers=WORKERS) as pool:
        futures = {pool.submit(fetch_match, mid): mid for mid in match_ids}
        for future in as_completed(futures):
            data = future.result()
            if data and match_is_finished(data):
                finished += 1
    print(f"  {league_id} {season}: finished={finished}/{len(match_ids)}")
    return finished == len(match_ids)


def main():
    with open("auto_matches.json", "r", encoding="utf-8") as f:
        config = json.load(f)

    output = {
        "generated_from": "FotMob league structures + matchDetails",
        "generated_at": None,
        "competitions": [],
    }

    from datetime import datetime, timezone
    output["generated_at"] = datetime.now(timezone.utc).isoformat()

    for rule in config.get("competitions", []):
        league_id = str(rule.get("id", "")).strip()
        if not league_id:
            continue

        print()
        print("=" * 100)
        print(f"COMPETITION {league_id}")

        candidates = season_candidates(league_id)
        chosen = None
        chosen_ids = []

        for season in candidates:
            ids = collect_valid_match_ids(league_id, season)
            if league_id in FIXED_REFERENCE_SEASONS and season == FIXED_REFERENCE_SEASONS[league_id]:
                if ids:
                    chosen = season
                    chosen_ids = ids
                    print('  fixed World Cup 2026 reference accepted')
                    break
            elif ids and season_is_complete(league_id, season, ids):
                chosen = season
                chosen_ids = ids
                break

        if not chosen:
            raise RuntimeError(
                f"No complete reference season could be generated for competition {league_id}"
            )

        output["competitions"].append({
            "competition_id": league_id,
            "season": chosen,
            "match_ids": chosen_ids,
        })
        print(f"  SELECTED REFERENCE: {chosen} ({len(chosen_ids)} matches)")

    with open("historical_test_matches.json", "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
        f.write("\n")

    total = sum(len(x["match_ids"]) for x in output["competitions"])
    print()
    print(f"GENERATED: {len(output['competitions'])} competitions / {total} matches")


if __name__ == "__main__":
    main()

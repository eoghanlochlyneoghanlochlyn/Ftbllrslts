"""Live integration test: resolve competition, teams and stage from each FotMob link.

No preset league IDs, team IDs or stages. No changes to matches.json.
Unavailable metadata is INCONCLUSIVE, never silently marked REJECTED.
"""
import json
import re
import unittest
import requests
from datetime import datetime
from pathlib import Path
from urllib.parse import urlsplit
from fotmob import extract_match_id, fetch_match_api, fetch_match_page, extract_next_data, extract_basic_info
from match_discovery import (
    fetch_league_structure, build_league_stage_map, fetch_match_page_stage,
    load_team_config, normalize_stage, selection_reasons, recursive_find,
)

CASES = [{"url":"https://www.fotmob.com/matches/esteghlal-vs-al-sadd/9ih3qny#6050065","expected":True},{"url":"https://www.fotmob.com/matches/al-ahli-vs-pakhtakor-tashkent/2ilhx82#6050068","expected":False},{"url":"https://www.fotmob.com/matches/shabab-al-ahli-dubai-fc-vs-tractor/ht8nrj0#6050066","expected":True},{"url":"https://www.fotmob.com/matches/al-hussein-sc-vs-al-seeb/9i9lc8z#6054511","expected":False},{"url":"https://www.fotmob.com/matches/al-jazira-vs-gol-gohar/1jli52pf#6054591","expected":True},{"url":"https://www.fotmob.com/matches/angers-vs-brest/2agfd8#5802946","expected":False},{"url":"https://www.fotmob.com/matches/rayo-vallecano-vs-crystal-palace/2qknn8#5206271","expected":True},{"url":"https://www.fotmob.com/matches/rayo-vallecano-vs-strasbourg/2qt8qn#5206268","expected":True},{"url":"https://www.fotmob.com/matches/rayo-vallecano-vs-aek-athens/2dd4xe#5206261","expected":False},{"url":"https://www.fotmob.com/matches/freiburg-vs-aston-villa/2v3xep#5206177","expected":True},{"url":"https://www.fotmob.com/matches/freiburg-vs-braga/2v8ps7#5206175","expected":True},{"url":"https://www.fotmob.com/matches/freiburg-vs-celta-vigo/2rcsmk#5206166","expected":True},{"url":"https://www.fotmob.com/matches/brann-vs-bologna/2rz5bc#5161883","expected":False},{"url":"https://www.fotmob.com/matches/rangers-vs-ludogorets-razgrad/azl33ed#4947790","expected":False},{"url":"https://www.fotmob.com/matches/milan-vs-lecce/2td7ci#4932342","expected":True},{"url":"https://www.fotmob.com/matches/pisa-vs-torino/26xs06#4932346","expected":False},{"url":"https://www.fotmob.com/matches/atalanta-vs-lazio/2epyoh#4935322","expected":True},{"url":"https://www.fotmob.com/matches/milan-vs-napoli/2t82b3#4934509","expected":True},{"url":"https://www.fotmob.com/matches/inter-vs-bologna/2ttfqc#4934510","expected":True},{"url":"https://www.fotmob.com/matches/bologna-vs-napoli/37x04l#4934511","expected":True}]

def canonical_competition_from_daily(match_id, start_value):
    """Use FotMob's stable daily primaryId when matchDetails exposes a
    season/edition-specific tournament ID."""
    if not start_value:
        return None
    try:
        date_text = datetime.fromisoformat(
            str(start_value).replace("Z", "+00:00")
        ).strftime("%Y%m%d")
    except ValueError:
        return None

    try:
        response = requests.get(
            "https://www.fotmob.com/api/data/matches",
            params={"date": date_text},
            headers={"User-Agent": "Mozilla/5.0", "Accept": "application/json"},
            timeout=30,
        )
        if response.status_code != 200:
            return None
        payload = response.json()
    except Exception:
        return None

    for league in payload.get("leagues", []) if isinstance(payload, dict) else []:
        if not isinstance(league, dict):
            continue
        for item in league.get("matches", []) or []:
            if not isinstance(item, dict):
                continue
            item_id = item.get("id") or item.get("matchId")
            if str(item_id) != str(match_id):
                continue
            stable_id = (
                league.get("primaryId")
                or league.get("leagueId")
                or league.get("competitionId")
                or league.get("id")
            )
            return str(stable_id) if stable_id is not None else None
    return None


def resolve(url):
    match_id = extract_match_id(urlsplit(url).fragment)
    if not match_id:
        raise ValueError("Missing match ID in URL")
    data = fetch_match_api(match_id)
    source = "matchDetails"
    if not isinstance(data, dict):
        html = fetch_match_page(match_id)
        data = extract_next_data(html) if html else None
        source = "match page"
    if not isinstance(data, dict):
        raise RuntimeError("Could not fetch structured match data")
    info = extract_basic_info(data)
    league_id = info.get("competition_id")
    start_value = info.get("start")

    # Match pages can expose an edition-specific tournament ID
    # (e.g. a Super Cup edition) while the daily endpoint exposes
    # the stable primaryId used by auto_matches.json.
    stable_league_id = canonical_competition_from_daily(match_id, start_value)
    if stable_league_id:
        league_id = stable_league_id

    if not league_id:
        raise RuntimeError("Competition ID unavailable")
    home_id, away_id = info.get("home_id"), info.get("away_id")
    if not home_id or not away_id:
        raise RuntimeError("Team IDs unavailable")
    match = {
        "id": str(match_id), "leagueId": str(league_id),
        "home": {"id": str(home_id), "name": info.get("home_name")},
        "away": {"id": str(away_id), "name": info.get("away_name")},
        "stage": None,
    }
    return match, info, data, source

class LiveUserMatchTest(unittest.TestCase):
    def test_all_links(self):
        config = json.loads(Path("auto_matches.json").read_text(encoding="utf-8"))
        selected = {str(x) for x in config.get("team_ids", [])}
        by_name, by_country = load_team_config()
        mismatches, unresolved = [], []
        league_cache = {}
        for i, case in enumerate(CASES, 1):
            url = case["url"]
            mid = extract_match_id(urlsplit(url).fragment)
            try:
                match, info, data, source = resolve(url)
                lid = match["leagueId"]
                rules = [r for r in config["competitions"] if str(r.get("id")) == lid]
                needs_stage = any(r.get("mode") in ("from", "final_only") for r in rules)
                stage_source = "not required"
                if needs_stage:
                    general = {}
                    if isinstance(data.get("general"), dict):
                        general = data["general"]
                    elif isinstance(data.get("props"), dict):
                        page_props = data["props"].get("pageProps", {})
                        if isinstance(page_props, dict) and isinstance(page_props.get("general"), dict):
                            general = page_props["general"]
                    season = (
                        general.get("season")
                        or general.get("parentLeagueSeason")
                        or recursive_find(data, {"parentLeagueSeason"})
                        or recursive_find(data, {"season"})
                    )
                    key = (lid, str(season or ""))
                    if key not in league_cache:
                        structure = fetch_league_structure(lid, season)
                        league_cache[key] = build_league_stage_map(structure) if structure else {}
                    stage = league_cache[key].get(mid)
                    if stage:
                        match["stage"], stage_source = stage, "league playoff.rounds"
                    else:
                        stage = fetch_match_page_stage(mid)
                        if stage:
                            match["stage"], stage_source = stage, "match page"
                        else:
                            raw_round = info.get("round_info") or {}
                            if isinstance(raw_round, dict):
                                stage = normalize_stage(raw_round.get("raw") or raw_round.get("name"))
                                if stage:
                                    match["stage"], stage_source = stage, "match round info"
                reasons = selection_reasons(match, config, selected, by_name, by_country)
                actual = bool(reasons)
                # Missing stage means a stage-based rejection cannot be confirmed.
                stage_unknown = needs_stage and match["stage"] is None and not actual
                if stage_unknown:
                    status = "INCONCLUSIVE"
                    unresolved.append(mid)
                else:
                    status = "PASS" if actual == case["expected"] else "MISMATCH"
                    if status == "MISMATCH":
                        mismatches.append(mid)
                print(
                    f"[{i:02d}/20] {status} | id={mid} | {match['home']['name']} vs {match['away']['name']}"
                    f" | league={info.get('league')} ({lid}) | stage={match['stage'] or 'UNKNOWN'}"
                    f" | stage_source={stage_source} | data_source={source}"
                    f" | actual={'SELECTED' if actual else 'REJECTED' if not stage_unknown else 'UNKNOWN'}"
                    f" | expected={'SELECTED' if case['expected'] else 'REJECTED'}"
                    f" | reason={','.join(reasons) if reasons else 'no matching rule or unresolved stage'}",
                    flush=True,
                )
            except Exception as exc:
                unresolved.append(mid)
                print(f"[{i:02d}/20] INCONCLUSIVE | id={mid} | fetch/parse error: {exc}", flush=True)
        print(f"SUMMARY total=20 mismatches={mismatches} inconclusive={unresolved}", flush=True)
        self.assertFalse(mismatches, f"Selection mismatches: {mismatches}")
        self.assertFalse(unresolved, f"Could not conclusively resolve: {unresolved}")

if __name__ == "__main__":
    unittest.main(verbosity=2)

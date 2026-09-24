"""Historical regression test for every configured competition."""
import json
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

import requests

from match_discovery import (
    FOTMOB_BASE_URL,
    STAGE_RANK,
    build_league_stage_map,
    configured_extra_team_ids,
    load_team_config,
    match_team_ids,
    normalize,
    normalize_stage,
    parse_datetime,
    selection_reasons,
)

CONFIG_FILE = Path("auto_matches.json")
TIMEOUT = 30
HISTORICAL_SEASONS = ("2024-2025", "2023-2024", "2024", "2023")
KNOCKOUT = {"round_of_32", "round_of_16", "quarter_final", "semi_final", "final", "third_place"}


def headers():
    return {
        "User-Agent": "Mozilla/5.0",
        "Accept": "application/json,text/plain,*/*",
        "Accept-Language": "en-US,en;q=0.9",
        "Referer": FOTMOB_BASE_URL + "/",
    }


def fetch_historical_league(league_id, season):
    url = f"{FOTMOB_BASE_URL}/api/data/leagues?id={league_id}&season={season}"
    response = requests.get(url, headers=headers(), timeout=TIMEOUT)
    response.raise_for_status()
    data = response.json()
    return data if isinstance(data, dict) else {}


def looks_like_match(node):
    if not isinstance(node, dict):
        return False
    match_id = node.get("id") or node.get("matchId")
    home = node.get("home") or node.get("homeTeam")
    away = node.get("away") or node.get("awayTeam")
    if match_id is None or not isinstance(home, dict) or not isinstance(away, dict):
        return False
    home_id = home.get("id") or home.get("teamId") or home.get("teamID")
    away_id = away.get("id") or away.get("teamId") or away.get("teamID")
    if home_id is None or away_id is None:
        return False
    start = node.get("utcTime") or node.get("startTime") or node.get("matchTimeUTC") or node.get("date")
    return parse_datetime(start) is not None


def collect_matches(data, league_id):
    result = {}
    seen = set()

    def walk(node):
        if isinstance(node, dict):
            if looks_like_match(node):
                match_id = str(node.get("id") or node.get("matchId"))
                if match_id not in result:
                    home = node.get("home") or node.get("homeTeam") or {}
                    away = node.get("away") or node.get("awayTeam") or {}
                    start = node.get("utcTime") or node.get("startTime") or node.get("matchTimeUTC") or node.get("date")
                    dt = parse_datetime(start)
                    result[match_id] = {
                        "id": match_id,
                        "leagueId": str(league_id),
                        "start": dt.isoformat(),
                        "home": {
                            "id": str(home.get("id") or home.get("teamId") or home.get("teamID")),
                            "name": home.get("longName") or home.get("name") or home.get("shortName") or "",
                        },
                        "away": {
                            "id": str(away.get("id") or away.get("teamId") or away.get("teamID")),
                            "name": away.get("longName") or away.get("name") or away.get("shortName") or "",
                        },
                        "stage": None,
                    }
            if id(node) not in seen:
                seen.add(id(node))
                for value in node.values():
                    if isinstance(value, (dict, list)):
                        walk(value)
        elif isinstance(node, list):
            for item in node:
                walk(item)

    walk(data)

    stage_map = build_league_stage_map(data)
    for match_id, match in result.items():
        match["stage"] = stage_map.get(match_id)

    return list(result.values())


def old_enough(match):
    dt = parse_datetime(match.get("start"))
    return dt is not None and dt < datetime.now(timezone.utc) - timedelta(days=120)


class HistoricalCompetitionSelectionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.config = json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
        cls.selected_team_ids = {str(x) for x in cls.config.get("team_ids", [])}
        cls.by_name, cls.by_country = load_team_config()
        cls.rules = cls.config.get("competitions", [])

    def load_matches(self, league_id):
        all_matches = []
        seen = set()

        for season in HISTORICAL_SEASONS:
            try:
                data = fetch_historical_league(league_id, season)
            except Exception as exc:
                print(f"[HISTORICAL] competition={league_id} season={season} fetch failed: {exc}")
                continue

            matches = [m for m in collect_matches(data, league_id) if old_enough(m)]
            print(f"[HISTORICAL] competition={league_id} season={season} matches={len(matches)}")

            for match in matches:
                if match["id"] not in seen:
                    seen.add(match["id"])
                    all_matches.append(match)

            if len(all_matches) >= 20:
                break

        return all_matches

    def resolve_stage(self, match):
        if normalize_stage(match.get("stage")) is not None:
            return match["stage"]
        from match_discovery import fetch_match_page_stage
        stage = fetch_match_page_stage(match["id"])
        if stage:
            match["stage"] = stage
        return stage

    def reasons(self, rule, match, selected_ids=None):
        return selection_reasons(
            match,
            {"competitions": [rule]},
            self.selected_team_ids if selected_ids is None else selected_ids,
            self.by_name,
            self.by_country,
        )

    def test_every_competition_has_two_real_historical_matches(self):
        failures = []
        for rule in self.rules:
            league_id = str(rule["id"])
            matches = self.load_matches(league_id)
            if len(matches) < 2:
                failures.append(f"competition {league_id}: only {len(matches)} historical matches found")
                continue
            for match in matches[:2]:
                print(
                    f"[HISTORICAL-CHECK] comp={league_id} match={match['id']} "
                    f"{match['home']['name']} vs {match['away']['name']} "
                    f"stage={match.get('stage')}"
                )
        self.assertFalse(failures, "Historical coverage failures:\n" + "\n".join(failures))

    def test_selection_modes(self):
        failures = []

        for rule in self.rules:
            league_id = str(rule["id"])
            mode = normalize(rule.get("mode") or "all")
            matches = self.load_matches(league_id)
            if len(matches) < 2:
                continue

            if mode in {"from", "final_only"}:
                for match in matches:
                    self.resolve_stage(match)

            if mode == "all":
                if not all(self.reasons(rule, m) for m in matches[:2]):
                    failures.append(f"{league_id} all: historical match rejected")

            elif mode == "from":
                required = normalize_stage(rule.get("stage"))
                qualifying = [
                    m for m in matches
                    if normalize_stage(m.get("stage")) in KNOCKOUT
                    and STAGE_RANK[normalize_stage(m.get("stage"))] <= STAGE_RANK[required]
                ]
                rejected = [
                    m for m in matches
                    if normalize_stage(m.get("stage")) not in KNOCKOUT
                    or STAGE_RANK[normalize_stage(m.get("stage"))] > STAGE_RANK[required]
                ]

                if not qualifying:
                    failures.append(f"{league_id} from={required}: no qualifying historical knockout match")
                elif not any(self.reasons(rule, m) for m in qualifying):
                    failures.append(f"{league_id} from={required}: qualifying match rejected")

                rule_without_extras = dict(rule)
                rule_without_extras.pop("extra_teams", None)
                rule_without_extras.pop("extra_country", None)
                extra_ids = configured_extra_team_ids(rule, self.by_name, self.by_country)
                isolated_rejected = False
                for match in rejected:
                    if match_team_ids(match) & extra_ids:
                        continue
                    if not self.reasons(rule_without_extras, match, selected_ids=set()):
                        isolated_rejected = True
                        break
                if not isolated_rejected:
                    failures.append(f"{league_id} from={required}: could not prove a below-threshold/non-knockout match is rejected")

            elif mode == "final_only":
                finals = [m for m in matches if normalize_stage(m.get("stage")) == "final"]
                non_finals = [m for m in matches if normalize_stage(m.get("stage")) != "final"]
                if not finals:
                    failures.append(f"{league_id} final_only: no historical final found")
                elif not any(self.reasons(rule, m) for m in finals):
                    failures.append(f"{league_id} final_only: historical final rejected")
                rule_only = dict(rule)
                if any(self.reasons(rule_only, m, selected_ids=set()) for m in non_finals):
                    failures.append(f"{league_id} final_only: non-final selected")

            elif mode == "team_only":
                extras = configured_extra_team_ids(rule, self.by_name, self.by_country)
                configured = self.selected_team_ids | extras
                yes = [m for m in matches if match_team_ids(m) & configured]
                no = [m for m in matches if not (match_team_ids(m) & configured)]
                if not yes:
                    failures.append(f"{league_id} team_only: no configured-team historical match found")
                elif not any(self.reasons(rule, m) for m in yes):
                    failures.append(f"{league_id} team_only: configured-team match rejected")
                if no and any(self.reasons(rule, m, selected_ids=set()) for m in no):
                    failures.append(f"{league_id} team_only: unrelated historical match selected")

        self.assertFalse(failures, "Historical selection failures:\n" + "\n".join(failures))


if __name__ == "__main__":
    unittest.main()

"""Exhaustive historical selection test for every fixture in the frozen manifest.

The manifest supplies only real FotMob match IDs and the fixed reference season.
Competition, teams, and (when required) stage are recovered from FotMob data.
No competition/stage is injected into the selection function.
"""

import json
import re
import unittest
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import requests

from match_discovery import (
    FOTMOB_BASE_URL,
    STAGE_RANK,
    build_league_stage_map,
    fetch_league_structure,
    fetch_match_page_stage,
    load_team_config,
    normalize_stage,
    selection_reasons,
)

CONFIG_FILE = Path("auto_matches.json")
MANIFEST_FILE = Path("historical_test_matches.json")
TIMEOUT = 30
PAGE_WORKERS = 12

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/140.0.0.0 Safari/537.36"
    ),
    "Accept": "application/json,text/plain,*/*",
    "Accept-Language": "en-US,en;q=0.9",
    "Referer": FOTMOB_BASE_URL + "/",
}


def _clean(value):
    if value is None:
        return ""
    return " ".join(str(value).replace("\xa0", " ").split()).strip()


def _walk_match_objects(node, wanted_ids, found):
    """Find actual fixture objects in a league-season payload."""
    if isinstance(node, dict):
        candidate_id = (
            node.get("id")
            or node.get("matchId")
            or node.get("matchID")
            or node.get("eventId")
            or node.get("eventID")
        )

        if candidate_id is not None and str(candidate_id) in wanted_ids:
            home = node.get("home") or node.get("homeTeam")
            away = node.get("away") or node.get("awayTeam")
            if isinstance(home, dict) and isinstance(away, dict):
                found[str(candidate_id)] = node

        for value in node.values():
            if isinstance(value, (dict, list)):
                _walk_match_objects(value, wanted_ids, found)

    elif isinstance(node, list):
        for item in node:
            _walk_match_objects(item, wanted_ids, found)


def _team_id(team):
    if not isinstance(team, dict):
        return None
    for key in ("id", "teamId", "teamID", "team_id"):
        value = team.get(key)
        if value is not None and _clean(value):
            return str(value)
    return None


def _team_name(team):
    if not isinstance(team, dict):
        return ""
    return _clean(
        team.get("longName")
        or team.get("name")
        or team.get("shortName")
        or team.get("title")
    )


def _fixture_from_payload(raw, competition_id):
    home = raw.get("home") or raw.get("homeTeam") or {}
    away = raw.get("away") or raw.get("awayTeam") or {}

    league_id = (
        raw.get("leagueId")
        or raw.get("leagueID")
        or raw.get("competitionId")
        or raw.get("competitionID")
        or raw.get("tournamentId")
        or raw.get("tournamentID")
    )

    return {
        "id": str(
            raw.get("id")
            or raw.get("matchId")
            or raw.get("matchID")
            or raw.get("eventId")
            or raw.get("eventID")
        ),
        "leagueId": str(league_id) if league_id is not None else str(competition_id),
        "home": {
            "id": _team_id(home),
            "name": _team_name(home),
        },
        "away": {
            "id": _team_id(away),
            "name": _team_name(away),
        },
    }


def _page_stage(match_id):
    try:
        return fetch_match_page_stage(str(match_id))
    except Exception as exc:
        print(f"[PAGE-STAGE] {match_id}: ERROR {exc}")
        return None


def _rule_applies_to_league(rule, league_id):
    ids = {str(rule.get("id"))}
    aliases = rule.get("aliases", [])
    if isinstance(aliases, list):
        ids.update(str(value) for value in aliases)
    return str(league_id) in ids


def _independent_rule_expectation(match, rule, selected_team_ids, by_name, by_country):
    """Independent expected semantics for one configured competition rule."""
    teams = {
        str(match["home"].get("id")),
        str(match["away"].get("id")),
    }

    extras = set()

    for name in rule.get("extra_teams", []) or []:
        team_id = by_name.get(_clean(name).lower())
        if team_id:
            extras.add(str(team_id))

    extra_country = _clean(rule.get("extra_country")).lower()
    if extra_country:
        extras.update(
            str(value)
            for value in by_country.get(extra_country, set())
        )

    if teams & extras:
        return True

    mode = _clean(rule.get("mode") or "all").lower()

    if mode == "all":
        return True

    if mode == "team_only":
        return bool(teams & (set(selected_team_ids) | extras))

    stage = normalize_stage(match.get("stage"))

    if mode == "final_only":
        return stage == "final"

    if mode == "from":
        required = normalize_stage(rule.get("stage"))
        knockout = {
            "round_of_32",
            "round_of_16",
            "quarter_final",
            "semi_final",
            "final",
            "third_place",
        }
        return (
            stage in knockout
            and required in knockout
            and STAGE_RANK[stage] <= STAGE_RANK[required]
        )

    return False


class HistoricalSelectionExhaustiveTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.config = json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
        cls.manifest = json.loads(MANIFEST_FILE.read_text(encoding="utf-8"))
        cls.selected_team_ids = {
            str(value) for value in cls.config.get("team_ids", [])
        }
        cls.by_name, cls.by_country = load_team_config()

        cls.rules = cls.config.get("competitions", [])
        cls.rules_by_id = {
            str(rule.get("id")): rule
            for rule in cls.rules
            if isinstance(rule, dict)
        }

        cls.raw_payloads = {}
        cls.stage_maps = {}
        cls.fixtures = {}

        # One historical league request per source competition.
        source_jobs = {}
        for entry in cls.manifest.get("competitions", []):
            competition_id = str(entry["competition_id"])
            season = entry["season"]
            source_ids = entry.get("source_competition_ids") or [competition_id]

            for source_id in source_ids:
                source_jobs[(str(source_id), str(season))] = True

        print(
            f"[HISTORICAL] Loading {len(source_jobs)} "
            "FotMob league-season payloads..."
        )

        for source_id, season in sorted(source_jobs):
            payload = fetch_league_structure(source_id, season)
            if not payload:
                raise RuntimeError(
                    f"Could not fetch historical FotMob structure: "
                    f"competition={source_id}, season={season}"
                )

            cls.raw_payloads[(source_id, season)] = payload
            cls.stage_maps[(source_id, season)] = build_league_stage_map(
                payload
            )

        # Resolve every manifest match to its real FotMob fixture object.
        for entry in cls.manifest.get("competitions", []):
            competition_id = str(entry["competition_id"])
            season = str(entry["season"])
            wanted = {str(value) for value in entry.get("match_ids", [])}
            source_ids = [
                str(value)
                for value in (
                    entry.get("source_competition_ids")
                    or [competition_id]
                )
            ]

            found = {}
            for source_id in source_ids:
                payload = cls.raw_payloads.get((source_id, season))
                if payload:
                    _walk_match_objects(payload, wanted, found)

            for match_id, raw in found.items():
                fixture = _fixture_from_payload(raw, competition_id)
                fixture["_manifest_competition"] = competition_id
                fixture["_season"] = season
                cls.fixtures[match_id] = fixture

        missing = sorted(
            {
                str(match_id)
                for entry in cls.manifest.get("competitions", [])
                for match_id in entry.get("match_ids", [])
            }
            - set(cls.fixtures)
        )

        if missing:
            raise RuntimeError(
                f"{len(missing)} manifest matches were not found in "
                f"the corresponding historical FotMob payloads. "
                f"First IDs: {', '.join(missing[:20])}"
            )

        # Stage is derived from FotMob's historical league structure first.
        # Only unresolved stage-based fixtures use the actual match page.
        unresolved = []

        for match_id, fixture in cls.fixtures.items():
            competition_id = fixture["_manifest_competition"]
            season = fixture["_season"]

            stage = None
            for source_id in (
                cls.manifest_entry_for(competition_id, season)
                .get("source_competition_ids")
                or [competition_id]
            ):
                stage_map = cls.stage_maps.get((str(source_id), season), {})
                if match_id in stage_map:
                    stage = stage_map[match_id]
                    break

            if stage:
                fixture["stage"] = stage
                continue

            applicable = [
                rule for rule in cls.rules
                if _rule_applies_to_league(rule, fixture["leagueId"])
            ]
            needs_stage = any(
                _clean(rule.get("mode") or "all").lower()
                in {"from", "final_only"}
                for rule in applicable
            )

            if needs_stage:
                unresolved.append(match_id)

        if unresolved:
            print(
                f"[HISTORICAL] {len(unresolved)} stage values unresolved "
                "from league structures; fetching match pages..."
            )
            with ThreadPoolExecutor(max_workers=PAGE_WORKERS) as executor:
                futures = {
                    executor.submit(_page_stage, match_id): match_id
                    for match_id in unresolved
                }
                for future in as_completed(futures):
                    match_id = futures[future]
                    stage = future.result()
                    if stage:
                        cls.fixtures[match_id]["stage"] = stage

        # Stage-based fixtures must never silently become UNKNOWN.
        unresolved_after = []
        for match_id, fixture in cls.fixtures.items():
            applicable = [
                rule for rule in cls.rules
                if _rule_applies_to_league(rule, fixture["leagueId"])
            ]
            needs_stage = any(
                _clean(rule.get("mode") or "all").lower()
                in {"from", "final_only"}
                for rule in applicable
            )
            if needs_stage and not normalize_stage(fixture.get("stage")):
                unresolved_after.append(match_id)

        if unresolved_after:
            raise RuntimeError(
                f"Stage unresolved for {len(unresolved_after)} "
                f"stage-based fixtures. First IDs: "
                f"{', '.join(unresolved_after[:30])}"
            )

    @classmethod
    def manifest_entry_for(cls, competition_id, season):
        for entry in cls.manifest.get("competitions", []):
            if (
                str(entry.get("competition_id")) == str(competition_id)
                and str(entry.get("season")) == str(season)
            ):
                return entry
        return {}

    def test_every_manifest_fixture_has_correct_selection(self):
        manifest_ids = [
            str(match_id)
            for entry in self.manifest.get("competitions", [])
            for match_id in entry.get("match_ids", [])
        ]

        self.assertEqual(
            len(manifest_ids),
            len(set(manifest_ids)),
            "Manifest contains duplicate match IDs",
        )
        self.assertEqual(
            len(manifest_ids),
            len(self.fixtures),
            "Manifest fixture count differs from resolved FotMob fixtures",
        )

        total_selected = 0
        total_rejected = 0
        by_competition = {}

        for index, match_id in enumerate(manifest_ids, 1):
            match = self.fixtures[match_id]
            competition_id = match["_manifest_competition"]

            rules = [
                rule for rule in self.rules
                if _rule_applies_to_league(rule, match["leagueId"])
            ]

            production_reasons = selection_reasons(
                match,
                self.config,
                self.selected_team_ids,
                self.by_name,
                self.by_country,
            )

            expected_reasons = []
            teams = {
                str(match["home"].get("id")),
                str(match["away"].get("id")),
            }

            if teams & self.selected_team_ids:
                expected_reasons.append("selected_team")

            for rule in rules:
                if _independent_rule_expectation(
                    match,
                    rule,
                    self.selected_team_ids,
                    self.by_name,
                    self.by_country,
                ):
                    mode = _clean(rule.get("mode") or "all").lower()
                    if mode == "all":
                        expected_reasons.append(
                            f"competition_all:{rule.get('id')}"
                        )
                    elif mode == "team_only":
                        expected_reasons.append(
                            f"competition_team:{rule.get('id')}"
                        )
                    elif mode == "final_only":
                        expected_reasons.append(
                            f"competition_final:{rule.get('id')}"
                        )
                    elif mode == "from":
                        teams_match = bool(teams & set(self.selected_team_ids))
                        extras = bool(
                            teams & set(
                                str(value)
                                for value in rule.get("extra_teams", []) or []
                            )
                        )
                        # Exact reason for extra teams is validated separately
                        # through the production output below.
                        if not teams_match and not extras:
                            expected_reasons.append(
                                f"competition_stage:{rule.get('id')}"
                            )

            expected_selected = bool(expected_reasons)
            actual_selected = bool(production_reasons)

            if actual_selected:
                total_selected += 1
            else:
                total_rejected += 1

            by_competition.setdefault(
                competition_id,
                {"total": 0, "selected": 0, "rejected": 0},
            )
            by_competition[competition_id]["total"] += 1
            by_competition[competition_id][
                "selected" if actual_selected else "rejected"
            ] += 1

            print(
                f"{index:04d}. {match_id} | comp={competition_id} "
                f"| leagueId={match['leagueId']} | "
                f"{match['home']['name']} vs {match['away']['name']} "
                f"| stage={match.get('stage') or '-'} | "
                f"{'SELECT' if actual_selected else 'REJECT'} | "
                f"reason={', '.join(production_reasons) if production_reasons else 'none'}"
            )

            self.assertEqual(
                actual_selected,
                expected_selected,
                msg=(
                    f"Selection mismatch for {match_id}: "
                    f"{match['home']['name']} vs {match['away']['name']} | "
                    f"stage={match.get('stage')} | "
                    f"expected={expected_selected} | "
                    f"actual={actual_selected} | "
                    f"actual_reasons={production_reasons}"
                ),
            )

        print("\n" + "=" * 120)
        print(
            f"HISTORICAL EXHAUSTIVE TOTAL | "
            f"{len(manifest_ids)} matches | "
            f"SELECT={total_selected} | REJECT={total_rejected}"
        )

        for competition_id in sorted(by_competition, key=str):
            item = by_competition[competition_id]
            print(
                f"COMPETITION {competition_id}: "
                f"{item['selected']}/{item['total']} SELECTED | "
                f"{item['rejected']} REJECTED"
            )

        # Explicit completeness assertions for the six configured super-cups.
        expected_supercups = {
            "247": 1,
            "139": 3,
            "11015": 3,
            "8924": 1,
            "207": 1,
            "74": 1,
        }

        for competition_id, expected_count in expected_supercups.items():
            item = by_competition.get(
                competition_id,
                {"total": 0, "selected": 0},
            )
            self.assertEqual(
                item["total"],
                expected_count,
                f"Super-cup {competition_id} fixture count is incomplete",
            )
            self.assertEqual(
                item["selected"],
                expected_count,
                f"Super-cup {competition_id} has an unselected fixture",
            )


if __name__ == "__main__":
    unittest.main(verbosity=2)

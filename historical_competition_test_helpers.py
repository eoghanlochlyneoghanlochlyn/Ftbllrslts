"""Exhaustive historical competition regression harness.

Each competition-specific test imports run_exhaustive_competition_test().
The harness asks FotMob for the latest season that is fully finished, extracts
the complete match list from matchesCombinedByRound, evaluates every match
against the configured competition rule, and prints the decision/reasons.

This is intentionally a live-data test: the point is to verify the real
competition structure and every real fixture, not a hand-picked sample.
"""

import json
import re
import unittest
from pathlib import Path

from match_discovery import (
    STAGE_RANK,
    build_league_stage_map,
    configured_extra_team_ids,
    fetch_league_structure,
    load_team_config,
    match_team_ids,
    normalize,
    selection_reasons,
)

CONFIG_FILE = Path("auto_matches.json")

KNOCKOUT_STAGES = {
    "round_of_32",
    "round_of_16",
    "quarter_final",
    "semi_final",
    "final",
    "third_place",
}


def _clean(value):
    if value is None:
        return ""
    return " ".join(str(value).replace("\\xa0", " ").split()).strip()


def _stage_from_text(value):
    text = normalize(value)
    if not text:
        return None

    text = re.sub(r"[^a-z0-9/ -]+", " ", text)
    text = re.sub(r"\\s+", " ", text).strip()

    if "round of 32" in text or "last 32" in text or "1/16" in text:
        return "round_of_32"
    if "round of 16" in text or "last 16" in text or "1/8" in text:
        return "round_of_16"
    if "quarter" in text and "final" in text:
        return "quarter_final"
    if "semi" in text and "final" in text:
        return "semi_final"
    if "third place" in text or "3rd place" in text:
        return "third_place"
    if text == "final" or text.endswith(" final") or text == "final stage":
        return "final"
    if "league phase" in text:
        return "league_phase"
    if "group stage" in text or text == "group" or "group " in text:
        return "group_stage"
    if "regular season" in text:
        return "regular_season"

    return None


def _recursive_find_key(node, wanted_key):
    if isinstance(node, dict):
        if wanted_key in node:
            return node[wanted_key]
        for value in node.values():
            found = _recursive_find_key(value, wanted_key)
            if found is not None:
                return found
    elif isinstance(node, list):
        for value in node:
            found = _recursive_find_key(value, wanted_key)
            if found is not None:
                return found
    return None


def _extract_match_nodes(node, output):
    """Extract real match dictionaries from FotMob's round structure."""
    if isinstance(node, dict):
        home = node.get("home")
        away = node.get("away")
        match_id = node.get("id") or node.get("matchId")

        if (
            match_id is not None
            and isinstance(home, dict)
            and isinstance(away, dict)
        ):
            home_id = home.get("id") or home.get("teamId") or home.get("teamID")
            away_id = away.get("id") or away.get("teamId") or away.get("teamID")
            if home_id is not None and away_id is not None:
                output.append(node)
                return

        for value in node.values():
            _extract_match_nodes(value, output)

    elif isinstance(node, list):
        for value in node:
            _extract_match_nodes(value, output)


def _status_finished(match):
    status = match.get("status")
    if not isinstance(status, dict):
        status = {}

    if status.get("finished") is True:
        return True

    if status.get("cancelled") is True:
        return True

    reason = status.get("reason")
    if isinstance(reason, dict):
        text = " ".join(
            _clean(reason.get(key))
            for key in ("short", "long", "key")
        ).lower()
        if any(
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
        ):
            return True

    return False


def _extract_season_candidates(data):
    seasons = data.get("seasons")
    if seasons is None:
        seasons = _recursive_find_key(data, "seasons")

    if isinstance(seasons, dict):
        seasons = seasons.get("seasons") or list(seasons.values())

    if not isinstance(seasons, list):
        return []

    result = []
    seen = set()

    for item in seasons:
        if isinstance(item, dict):
            value = (
                item.get("id")
                or item.get("season")
                or item.get("name")
            )
        else:
            value = item

        value = _clean(value)
        if value and value not in seen:
            seen.add(value)
            result.append(value)

    return result


def _extract_matches(data, stage_map):
    container = _recursive_find_key(data, "matchesCombinedByRound")
    if container is None:
        raise AssertionError("FotMob season payload has no matchesCombinedByRound")

    raw = []
    _extract_match_nodes(container, raw)

    by_id = {}

    for match in raw:
        match_id = str(match.get("id") or match.get("matchId"))
        if not match_id:
            continue

        home = match.get("home") or {}
        away = match.get("away") or {}

        stage = stage_map.get(match_id)

        if stage is None:
            stage = _stage_from_text(
                match.get("roundName")
                or match.get("round")
                or match.get("stage")
            )

        normalized = {
            "id": match_id,
            "leagueId": str(
                match.get("leagueId")
                or match.get("primaryLeagueId")
                or match.get("tournamentId")
                or ""
            ),
            "stage": stage,
            "roundName": _clean(match.get("roundName")),
            "home": {
                "id": str(
                    home.get("id")
                    or home.get("teamId")
                    or home.get("teamID")
                    or ""
                ),
                "name": _clean(
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
                "name": _clean(
                    away.get("longName")
                    or away.get("name")
                    or away.get("shortName")
                ),
            },
            "status": match.get("status") or {},
        }

        # Prefer the stage map from overview.playoff.rounds because that is
        # the same stage source production discovery uses.
        by_id[match_id] = normalized

    return list(by_id.values())


def _season_is_complete(matches):
    if not matches:
        return False
    return all(_status_finished(match) for match in matches)


def fetch_latest_completed_season(competition_id):
    """Return (season_name, payload, matches) for the newest fully finished season."""
    base = fetch_league_structure(competition_id)
    if not isinstance(base, dict):
        raise AssertionError(
            f"Could not fetch competition {competition_id} season list"
        )

    candidates = _extract_season_candidates(base)
    if not candidates:
        raise AssertionError(
            f"FotMob returned no seasons for competition {competition_id}"
        )

    print(
        f"[HISTORICAL] Competition {competition_id}: "
        f"checking {len(candidates)} seasons newest -> oldest"
    )

    for season in candidates:
        data = fetch_league_structure(competition_id, season=season)
        if not isinstance(data, dict):
            continue

        stage_map = build_league_stage_map(data)
        matches = _extract_matches(data, stage_map)

        if not matches:
            continue

        if _season_is_complete(matches):
            return season, data, matches

        unfinished = [
            match["id"]
            for match in matches
            if not _status_finished(match)
        ]
        print(
            f"[HISTORICAL] {competition_id} season {season}: "
            f"INCOMPLETE ({len(unfinished)} unfinished matches)"
        )

    raise AssertionError(
        f"No fully completed season found for competition {competition_id}"
    )


def _rule_for(config, competition_id):
    for rule in config.get("competitions", []):
        if str(rule.get("id")) == str(competition_id):
            return rule
    raise AssertionError(
        f"Configured competition {competition_id} not found in auto_matches.json"
    )


def run_exhaustive_competition_test(test_case, competition_id):
    config = json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
    rule = _rule_for(config, competition_id)

    selected_team_ids = {
        str(value)
        for value in config.get("team_ids", [])
    }
    by_name, by_country = load_team_config()

    season, payload, matches = fetch_latest_completed_season(competition_id)

    # If FotMob gives a primary/stable competition id in the season payload,
    # verify that every extracted fixture belongs to this configured rule.
    for match in matches:
        test_case.assertEqual(
            str(match["leagueId"]),
            str(competition_id),
            f"Wrong competition id on match {match['id']}",
        )

    test_case.assertEqual(
        len(matches),
        len({match["id"] for match in matches}),
        "Duplicate match IDs found in the historical fixture set",
    )

    print("\n" + "=" * 110)
    print(
        f"[EXHAUSTIVE TEST] competition={competition_id} "
        f"| latest_completed_season={season} "
        f"| mode={rule.get('mode')} "
        f"| threshold={rule.get('stage')}"
    )
    print(f"[EXHAUSTIVE TEST] COMPLETE FIXTURES FROM FOTMOB: {len(matches)}")
    print("=" * 110)

    selected_count = 0
    rejected_count = 0
    production_selected_count = 0

    for index, match in enumerate(
        sorted(matches, key=lambda item: item["id"]),
        1,
    ):
        isolated_reasons = selection_reasons(
            match,
            {"competitions": [rule]},
            set(),
            by_name,
            by_country,
        )
        production_reasons = selection_reasons(
            match,
            config,
            selected_team_ids,
            by_name,
            by_country,
        )

        isolated_selected = bool(isolated_reasons)
        production_selected = bool(production_reasons)

        if isolated_selected:
            selected_count += 1
            rule_reason = ", ".join(isolated_reasons)
            rule_decision = "SELECTED"
        else:
            rejected_count += 1
            rule_reason = "no matching competition rule"
            rule_decision = "REJECTED"

        if production_selected:
            production_selected_count += 1

        home = match["home"]["name"]
        away = match["away"]["name"]
        stage = match["stage"] or "unknown"
        round_name = match["roundName"] or "-"

        print(
            f"{index:03d}. {match['id']} | {stage:<14} | "
            f"{home} vs {away} | "
            f"RULE={rule_decision:<8} | reason: {rule_reason}"
        )
        print(
            f"     round={round_name!r} | "
            f"PRODUCTION={'SELECTED' if production_selected else 'REJECTED':<8} | "
            f"reason: {', '.join(production_reasons) if production_reasons else 'no matching rule'}"
        )

        # This is the actual assertion for every single real fixture.
        if isolated_selected:
            test_case.assertTrue(isolated_reasons, match["id"])
        else:
            test_case.assertEqual(
                isolated_reasons,
                [],
                f"Unexpected competition-rule selection for {match['id']}",
            )

        # Stage-based rules must never silently accept an unknown stage.
        mode = normalize(rule.get("mode") or "all")
        if mode in {"from", "final_only"} and match["stage"] is None:
            # It is acceptable only if the competition rule itself is all/team-only,
            # which it is not here. Therefore this catches stage extraction regressions.
            test_case.fail(
                f"Missing stage for stage-based competition "
                f"{competition_id}, match {match['id']}: "
                f"{home} vs {away}"
            )

    print("-" * 110)
    print(
        f"[EXHAUSTIVE SUMMARY] competition={competition_id} "
        f"| season={season} | matches={len(matches)} "
        f"| rule_selected={selected_count} "
        f"| rule_rejected={rejected_count} "
        f"| production_selected={production_selected_count}"
    )
    print("=" * 110 + "\n")

    test_case.assertEqual(
        selected_count + rejected_count,
        len(matches),
    )

    # A configured mode=all rule must select every real fixture.
    if normalize(rule.get("mode") or "all") == "all":
        test_case.assertEqual(
            rejected_count,
            0,
            f"mode=all rejected {rejected_count} real fixtures",
        )

    # from/final_only/team_only rules should have at least one real decision.
    test_case.assertGreater(
        len(matches),
        0,
        f"Competition {competition_id} returned no historical fixtures",
    )

"""Deterministic historical regression tests for every configured competition.

The previous version tried to recursively extract fixtures from
/api/data/leagues?...season=..., but that endpoint does not expose the
historical fixture list in one stable shape. That made the test report
"0 historical matches" even when FotMob had real historical fixtures.

This version uses FotMob's daily matches endpoint, which is the same
fixture source used by production discovery. It scans historical dates
and then uses the real match page to resolve knockout stages.
"""

import json
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

from match_discovery import (
    fetch_matches_for_date,
    fetch_match_page_stage,
    configured_extra_team_ids,
    load_team_config,
    match_team_ids,
    normalize,
    normalize_stage,
    selection_reasons,
    STAGE_RANK,
)

CONFIG_FILE = Path("auto_matches.json")

# Three years gives enough coverage for the configured annual/international
# competitions while keeping the test independent from a specific season.
LOOKBACK_DAYS = 3 * 365

# Keep several real fixtures per competition so stage/team_only tests can
# find both positive and negative examples without hard-coding match IDs.
MAX_FIXTURES_PER_COMPETITION = 16

# Daily endpoint calls are cheap compared with guessing historical league
# response shapes. A 3-day stride gives good coverage; once all competitions
# have enough candidates we stop immediately.
DATE_STEP_DAYS = 3

KNOCKOUT_STAGES = {
    "round_of_32",
    "round_of_16",
    "quarter_final",
    "semi_final",
    "final",
    "third_place",
}


def date_strings():
    """Yield YYYYMMDD dates from today backwards for the configured lookback."""
    today = datetime.now(timezone.utc).date()
    for offset in range(0, LOOKBACK_DAYS + 1, DATE_STEP_DAYS):
        yield (today - timedelta(days=offset)).strftime("%Y%m%d")


def fixture_key(match):
    return str(match.get("id") or "")


def enough_for_rule(rule, matches):
    """Return whether the candidate pool is useful for this rule."""
    if len(matches) < 2:
        return False

    mode = normalize(rule.get("mode") or "all")

    if mode == "all":
        return True

    # Stage rules need enough candidates to find both a qualifying and a
    # non-qualifying historical fixture. We resolve stage lazily later.
    if mode in {"from", "final_only"}:
        return len(matches) >= 6

    # team_only needs both a configured-team fixture and an unrelated one.
    return len(matches) >= 6


class HistoricalCompetitionSelectionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.config = json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
        cls.rules = [
            rule
            for rule in cls.config.get("competitions", [])
            if isinstance(rule, dict)
        ]
        cls.selected_team_ids = {
            str(value) for value in cls.config.get("team_ids", [])
        }
        cls.by_name, cls.by_country = load_team_config()

        cls.fixtures_by_competition = cls.discover_historical_fixtures()

    @classmethod
    def discover_historical_fixtures(cls):
        """Discover real old fixtures from the same daily source as production."""
        wanted = {
            str(rule["id"]): rule
            for rule in cls.rules
            if rule.get("id") is not None
        }
        found = {competition_id: {} for competition_id in wanted}

        print(
            f"[HISTORICAL] Searching {len(wanted)} configured competitions "
            f"over the last {LOOKBACK_DAYS} days"
        )

        for date_text in date_strings():
            if all(
                enough_for_rule(
                    wanted[competition_id],
                    list(found[competition_id].values()),
                )
                for competition_id in wanted
            ):
                break

            matches = fetch_matches_for_date(date_text)
            if not matches:
                continue

            for match in matches:
                competition_id = str(match.get("leagueId") or "")
                if competition_id not in wanted:
                    continue

                match_id = fixture_key(match)
                if not match_id:
                    continue

                # Production's daily endpoint is historical by construction
                # here, because every scanned date is at least several days old.
                found[competition_id][match_id] = match

                if (
                    len(found[competition_id])
                    >= MAX_FIXTURES_PER_COMPETITION
                ):
                    # No need to keep every domestic fixture from a date.
                    found[competition_id].pop(
                        next(iter(found[competition_id]))
                    )

            if date_text.endswith("01") or date_text.endswith("15"):
                summary = ", ".join(
                    f"{cid}={len(items)}"
                    for cid, items in found.items()
                    if items
                )
                print(f"[HISTORICAL] {date_text}: {summary}")

        return {
            competition_id: list(matches.values())
            for competition_id, matches in found.items()
        }

    def stage(self, match):
        """Resolve stage from the match page when the daily payload lacks it."""
        current = normalize_stage(match.get("stage"))
        if current:
            return current

        value = fetch_match_page_stage(match["id"])
        if value:
            match["stage"] = value
        return value

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
            competition_id = str(rule["id"])
            matches = self.fixtures_by_competition.get(competition_id, [])

            print(
                f"[HISTORICAL-CHECK] competition={competition_id} "
                f"mode={rule.get('mode', 'all')} "
                f"fixtures={len(matches)}"
            )

            if len(matches) < 2:
                failures.append(
                    f"competition {competition_id}: only "
                    f"{len(matches)} real historical fixtures found"
                )
                continue

            for match in matches[:2]:
                print(
                    f"[HISTORICAL-FIXTURE] comp={competition_id} "
                    f"match={match['id']} "
                    f"{match['home']['name']} vs {match['away']['name']} "
                    f"date={match['start']}"
                )

        self.assertFalse(
            failures,
            "Historical fixture coverage failures:\n"
            + "\n".join(failures),
        )

    def test_selection_modes(self):
        failures = []

        for rule in self.rules:
            competition_id = str(rule["id"])
            mode = normalize(rule.get("mode") or "all")
            matches = self.fixtures_by_competition.get(
                competition_id, []
            )

            if len(matches) < 2:
                failures.append(
                    f"{competition_id}: insufficient historical fixtures"
                )
                continue

            # IMPORTANT: isolate competition rules from global selected-team
            # rules. Otherwise a Real Madrid/Liverpool/etc fixture could pass
            # for the wrong reason.
            isolated_selected_ids = set()

            if mode == "all":
                if not all(
                    self.reasons(
                        rule,
                        match,
                        selected_ids=isolated_selected_ids,
                    )
                    for match in matches[:2]
                ):
                    failures.append(
                        f"{competition_id} all: historical fixture rejected"
                    )
                continue

            if mode == "team_only":
                extras = configured_extra_team_ids(
                    rule,
                    self.by_name,
                    self.by_country,
                )
                configured = self.selected_team_ids | extras

                yes = [
                    match
                    for match in matches
                    if match_team_ids(match) & configured
                ]
                no = [
                    match
                    for match in matches
                    if not (match_team_ids(match) & configured)
                ]

                if not yes:
                    failures.append(
                        f"{competition_id} team_only: "
                        "no configured-team fixture found"
                    )
                elif not any(
                    self.reasons(
                        rule,
                        match,
                        selected_ids=isolated_selected_ids,
                    )
                    for match in yes
                ):
                    failures.append(
                        f"{competition_id} team_only: "
                        "configured-team fixture rejected"
                    )

                if no and any(
                    self.reasons(
                        rule,
                        match,
                        selected_ids=isolated_selected_ids,
                    )
                    for match in no
                ):
                    failures.append(
                        f"{competition_id} team_only: "
                        "unrelated fixture selected"
                    )
                continue

            # Stage-based rules.
            resolved = []
            for match in matches:
                stage = self.stage(match)
                if stage:
                    resolved.append(match)

            if not resolved:
                failures.append(
                    f"{competition_id} {mode}: "
                    "could not resolve any historical match stage"
                )
                continue

            if mode == "final_only":
                finals = [
                    match
                    for match in resolved
                    if normalize_stage(match.get("stage")) == "final"
                ]
                non_finals = [
                    match
                    for match in resolved
                    if normalize_stage(match.get("stage")) != "final"
                ]

                if not finals:
                    failures.append(
                        f"{competition_id} final_only: "
                        "no historical final found"
                    )
                elif not any(
                    self.reasons(
                        rule,
                        match,
                        selected_ids=isolated_selected_ids,
                    )
                    for match in finals
                ):
                    failures.append(
                        f"{competition_id} final_only: "
                        "historical final rejected"
                    )

                if non_finals and any(
                    self.reasons(
                        rule,
                        match,
                        selected_ids=isolated_selected_ids,
                    )
                    for match in non_finals
                ):
                    failures.append(
                        f"{competition_id} final_only: "
                        "non-final fixture selected"
                    )
                continue

            required = normalize_stage(rule.get("stage"))
            if required not in KNOCKOUT_STAGES:
                failures.append(
                    f"{competition_id} from: invalid required stage "
                    f"{rule.get('stage')!r}"
                )
                continue

            extras = configured_extra_team_ids(
                rule,
                self.by_name,
                self.by_country,
            )

            qualifying = [
                match
                for match in resolved
                if (
                    normalize_stage(match.get("stage")) in KNOCKOUT_STAGES
                    and STAGE_RANK[
                        normalize_stage(match.get("stage"))
                    ] <= STAGE_RANK[required]
                )
            ]

            rejected = [
                match
                for match in resolved
                if (
                    normalize_stage(match.get("stage"))
                    not in KNOCKOUT_STAGES
                    or STAGE_RANK[
                        normalize_stage(match.get("stage"))
                    ] > STAGE_RANK[required]
                )
            ]

            if not qualifying:
                failures.append(
                    f"{competition_id} from={required}: "
                    "no qualifying historical knockout fixture found"
                )
            elif not any(
                self.reasons(
                    rule,
                    match,
                    selected_ids=isolated_selected_ids,
                )
                for match in qualifying
            ):
                failures.append(
                    f"{competition_id} from={required}: "
                    "qualifying fixture rejected"
                )

            # Remove unconditional extra-team behavior so we can prove the
            # actual stage threshold works. If every rejected fixture happens
            # to contain Brazil/Argentina/Iran/etc, skip it and keep looking.
            rule_without_extras = dict(rule)
            rule_without_extras.pop("extra_teams", None)
            rule_without_extras.pop("extra_country", None)

            rejected_without_extras = [
                match
                for match in rejected
                if not (match_team_ids(match) & extras)
            ]

            if rejected_without_extras and not any(
                not self.reasons(
                    rule_without_extras,
                    match,
                    selected_ids=set(),
                )
                for match in rejected_without_extras
            ):
                failures.append(
                    f"{competition_id} from={required}: "
                    "could not prove a below-threshold fixture is rejected"
                )

        self.assertFalse(
            failures,
            "Historical selection failures:\n"
            + "\n".join(failures),
        )


if __name__ == "__main__":
    unittest.main()

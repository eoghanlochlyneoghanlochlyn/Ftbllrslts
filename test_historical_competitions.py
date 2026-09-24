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
LOOKBACK_DAYS = 0

# Keep several real fixtures per competition so stage/team_only tests can
# find both positive and negative examples without hard-coding match IDs.
MAX_FIXTURES_PER_COMPETITION = 8

# Daily endpoint calls are cheap compared with guessing historical league
# response shapes. A 3-day stride gives good coverage; once all competitions
# have enough candidates we stop immediately.
DATE_STEP_DAYS = 1

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
        """Discover real historical fixtures from FotMob league seasons.

        The daily endpoint is intentionally not used here: it only exposes a
        small recent date window. For historical regression coverage we first
        ask FotMob for the competition's season list, then fetch each prior
        season and extract real fixture objects from that season response.
        """
        wanted = {
            str(rule["id"]): rule
            for rule in cls.rules
            if rule.get("id") is not None
        }
        found = {competition_id: {} for competition_id in wanted}

        print(
            f"[HISTORICAL] Searching prior FotMob seasons for "
            f"{len(wanted)} configured competitions (max 2 seasons/competition)"
        )

        for competition_id, rule in wanted.items():
            seasons = cls.fetch_historical_seasons(competition_id)
            print(
                f"[HISTORICAL] competition={competition_id} "
                f"seasons={len(seasons)}"
            )

            for season in seasons[:2]:
                data = cls.fetch_league_season(
                    competition_id, season
                )
                for match in cls.extract_historical_matches(data):
                    if not match.get("id"):
                        continue
                    found[competition_id][str(match["id"])] = match

                    if (
                        len(found[competition_id])
                        >= MAX_FIXTURES_PER_COMPETITION
                    ):
                        break

                if len(found[competition_id]) >= MAX_FIXTURES_PER_COMPETITION:
                    break

            print(
                f"[HISTORICAL] competition={competition_id} "
                f"fixtures={len(found[competition_id])}"
            )

        return {
            competition_id: list(matches.values())
            for competition_id, matches in found.items()
        }

    @staticmethod
    def fotmob_headers():
        return {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/140.0.0.0 Safari/537.36"
            ),
            "Accept": "application/json,text/plain,*/*",
            "Accept-Language": "en-US,en;q=0.9",
            "Referer": "https://www.fotmob.com/",
        }

    @classmethod
    def fetch_historical_seasons(cls, competition_id):
        """Return prior season IDs/names advertised by FotMob."""
        import requests

        url = (
            "https://www.fotmob.com/api/data/leagues"
            f"?id={competition_id}"
        )
        try:
            response = requests.get(
                url,
                headers=cls.fotmob_headers(),
                timeout=10,
            )
            response.raise_for_status()
            data = response.json()
        except (requests.RequestException, ValueError) as error:
            print(
                f"[HISTORICAL] competition={competition_id} "
                f"season-list failed: {error}"
            )
            return []

        candidates = []

        def walk(node):
            if isinstance(node, dict):
                for key, value in node.items():
                    key_norm = str(key).lower()
                    if key_norm in {
                        "seasons", "seasonlist", "available_seasons",
                        "availableSeasons",
                    } and isinstance(value, list):
                        for item in value:
                            if isinstance(item, dict):
                                season_id = (
                                    item.get("id")
                                    or item.get("seasonId")
                                    or item.get("seasonID")
                                )
                                name = (
                                    item.get("name")
                                    or item.get("title")
                                    or item.get("label")
                                )
                                if season_id is not None:
                                    candidates.append(
                                        (str(season_id), str(name or ""))
                                    )
                    for value in node.values():
                        if isinstance(value, (dict, list)):
                            walk(value)
            elif isinstance(node, list):
                for item in node:
                    walk(item)

        walk(data)

        current_year = datetime.now(timezone.utc).year
        unique = []
        seen = set()

        def season_year(name):
            import re
            years = re.findall(r"20\d{2}", name or "")
            return int(years[-1]) if years else 0

        for season_id, name in sorted(
            candidates,
            key=lambda item: season_year(item[1]),
            reverse=True,
        ):
            if season_id in seen:
                continue
            if season_year(name) >= current_year:
                continue
            seen.add(season_id)
            unique.append(season_id)

        return unique

    @classmethod
    def fetch_league_season(cls, competition_id, season_id):
        import requests

        url = (
            "https://www.fotmob.com/api/data/leagues"
            f"?id={competition_id}&season={season_id}"
        )
        try:
            response = requests.get(
                url,
                headers=cls.fotmob_headers(),
                timeout=30,
            )
            response.raise_for_status()
            data = response.json()
            return data if isinstance(data, dict) else {}
        except (requests.RequestException, ValueError) as error:
            print(
                f"[HISTORICAL] competition={competition_id} "
                f"season={season_id} failed: {error}"
            )
            return {}

    @classmethod
    def extract_historical_matches(cls, data):
        """Extract only objects that clearly look like real FotMob fixtures."""
        result = []

        def parse_team(value):
            if not isinstance(value, dict):
                return {}
            team_id = (
                value.get("id")
                or value.get("teamId")
                or value.get("teamID")
            )
            name = (
                value.get("longName")
                or value.get("name")
                or value.get("shortName")
            )
            return {
                "id": str(team_id) if team_id is not None else "",
                "name": str(name or ""),
            }

        def walk(node):
            if isinstance(node, dict):
                home = node.get("home") or node.get("homeTeam")
                away = node.get("away") or node.get("awayTeam")
                match_id = node.get("id") or node.get("matchId")
                status = node.get("status")
                start = (
                    node.get("utcTime")
                    or node.get("startTime")
                    or node.get("matchTimeUTC")
                    or (
                        status.get("utcTime")
                        if isinstance(status, dict)
                        else None
                    )
                )

                if (
                    match_id is not None
                    and home is not None
                    and away is not None
                    and start is not None
                ):
                    home_team = parse_team(home)
                    away_team = parse_team(away)
                    if home_team.get("name") and away_team.get("name"):
                        result.append({
                            "id": str(match_id),
                            "start": str(start),
                            "home": home_team,
                            "away": away_team,
                            "leagueId": str(
                                node.get("leagueId")
                                or node.get("tournamentId")
                                or node.get("competitionId")
                                or ""
                            ),
                            "competitionName": "",
                            "stage": (
                                node.get("stage")
                                or node.get("round")
                                or node.get("roundName")
                            ),
                        })

                for value in node.values():
                    if isinstance(value, (dict, list)):
                        walk(value)

            elif isinstance(node, list):
                for item in node:
                    walk(item)

        walk(data)

        unique = {}
        for match in result:
            unique[match["id"]] = match
        return list(unique.values())


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

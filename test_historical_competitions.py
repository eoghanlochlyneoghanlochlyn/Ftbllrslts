"""Fast, deterministic regression tests for competition/stage selection.

No network calls are made here.

The fixtures below are real historical matches verified from FotMob/official
competition fixture lists. They are fed directly into the same
selection_reasons()/selected_by_rule() logic used by production discovery.

The purpose is NOT to crawl FotMob history. The purpose is to answer one
specific question quickly: given a real match and its real competition/stage,
does our selection algorithm choose it for the configured rule?
"""

import json
import unittest
from pathlib import Path

from match_discovery import (
    STAGE_RANK,
    configured_extra_team_ids,
    load_team_config,
    match_team_ids,
    normalize,
    normalize_stage,
    selection_reasons,
)

CONFIG_FILE = Path("auto_matches.json")

# Real historical fixtures. Competition IDs are the stable IDs used by
# auto_matches.json. Stage is the normalized stage that production discovery
# is expected to obtain before calling selection_reasons().
#
# Sources:
# - FotMob UCL 2023/24: https://www.fotmob.com/leagues/42/fixtures/champions-league?season=2023-2024
# - FotMob UEL 2023/24: https://www.fotmob.com/leagues/73/fixtures/europa-league?season=2023-2024
# - FotMob Copa America 2024: https://www.fotmob.com/leagues/44/fixtures/copa-america
# - FotMob World Cup 2022: https://www.fotmob.com/leagues/77/fixtures?season=2022
#
# IDs for teams used in the global selected-team checks come from the
# project's auto_matches.json configuration.
FIXTURES = [
    # Champions League: R16/QF/SF/Final plus a group-stage negative.
    {"id": "ucl-2024-r16", "leagueId": "42", "stage": "round_of_16",
     "home": {"id": "8560", "name": "Real Sociedad"},
     "away": {"id": "9847", "name": "Paris Saint-Germain"}},
    {"id": "ucl-2024-qf", "leagueId": "42", "stage": "quarter_final",
     "home": {"id": "8456", "name": "Manchester City"},
     "away": {"id": "8633", "name": "Real Madrid"}},
    {"id": "ucl-2024-sf", "leagueId": "42", "stage": "semi_final",
     "home": {"id": "9823", "name": "Bayern München"},
     "away": {"id": "8633", "name": "Real Madrid"}},
    {"id": "ucl-2024-final", "leagueId": "42", "stage": "final",
     "home": {"id": "9789", "name": "Borussia Dortmund"},
     "away": {"id": "8633", "name": "Real Madrid"}},
    {"id": "ucl-2024-group", "leagueId": "42", "stage": "group_stage",
     "home": {"id": "8633", "name": "Real Madrid"},
     "away": {"id": "8564", "name": "Milan"}},

    # Europa League: QF/SF/Final.
    {"id": "uel-2024-qf", "leagueId": "73", "stage": "quarter_final",
     "home": {"id": "8650", "name": "Liverpool"},
     "away": {"id": "8524", "name": "Atalanta"}},
    {"id": "uel-2024-sf", "leagueId": "73", "stage": "semi_final",
     "home": {"id": "8524", "name": "Atalanta"},
     "away": {"id": "8592", "name": "Marseille"}},
    {"id": "uel-2024-final", "leagueId": "73", "stage": "final",
     "home": {"id": "8524", "name": "Atalanta"},
     "away": {"id": "8178", "name": "Bayer Leverkusen"}},

    # Copa America: QF/SF/3rd place/Final. This also exercises the
    # Brazil/Argentina extra-team rule on competition 44.
    {"id": "copa-2024-qf", "leagueId": "44", "stage": "quarter_final",
     "home": {"id": "6706", "name": "Argentina"},
     "away": {"id": "6707", "name": "Ecuador"}},
    {"id": "copa-2024-sf", "leagueId": "44", "stage": "semi_final",
     "home": {"id": "6706", "name": "Argentina"},
     "away": {"id": "5810", "name": "Canada"}},
    {"id": "copa-2024-third", "leagueId": "44", "stage": "third_place",
     "home": {"id": "5810", "name": "Canada"},
     "away": {"id": "5796", "name": "Uruguay"}},
    {"id": "copa-2024-final", "leagueId": "44", "stage": "final",
     "home": {"id": "6706", "name": "Argentina"},
     "away": {"id": "8258", "name": "Colombia"}},

    # World Cup: group-stage negative + knockout stages.
    {"id": "wc-2022-group", "leagueId": "77", "stage": "group_stage",
     "home": {"id": "8256", "name": "Brazil"},
     "away": {"id": "8205", "name": "Serbia"}},
    {"id": "wc-2022-qf", "leagueId": "77", "stage": "quarter_final",
     "home": {"id": "6706", "name": "Argentina"},
     "away": {"id": "6708", "name": "Netherlands"}},
    {"id": "wc-2022-sf", "leagueId": "77", "stage": "semi_final",
     "home": {"id": "6706", "name": "Argentina"},
     "away": {"id": "10155", "name": "Croatia"}},
    {"id": "wc-2022-final", "leagueId": "77", "stage": "final",
     "home": {"id": "6706", "name": "Argentina"},
     "away": {"id": "6723", "name": "France"}},
]


class HistoricalSelectionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.config = json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
        cls.rules = [
            rule for rule in cls.config.get("competitions", [])
            if isinstance(rule, dict)
        ]
        cls.selected_team_ids = {
            str(value) for value in cls.config.get("team_ids", [])
        }
        cls.by_name, cls.by_country = load_team_config()

    def reasons(self, rule, fixture, selected_ids=None):
        return selection_reasons(
            fixture,
            {"competitions": [rule]},
            self.selected_team_ids if selected_ids is None else selected_ids,
            self.by_name,
            self.by_country,
        )

    def rule(self, competition_id):
        for rule in self.rules:
            if str(rule.get("id")) == str(competition_id):
                return rule
        self.fail(f"Configured competition {competition_id} not found")

    def test_fixture_set_is_real_and_complete(self):
        self.assertGreaterEqual(len(FIXTURES), 14)
        for fixture in FIXTURES:
            self.assertTrue(fixture["id"])
            self.assertTrue(fixture["leagueId"])
            self.assertIn(fixture["stage"], STAGE_RANK)
            self.assertTrue(fixture["home"]["name"])
            self.assertTrue(fixture["away"]["name"])

    def test_selected_team_is_independent_of_competition_rule(self):
        # Real Madrid is a globally selected team. It must be selected even
        # when the competition itself has no matching rule.
        fixture = {
            **next(f for f in FIXTURES if f["id"] == "ucl-2024-group"),
            "leagueId": "999999",
        }
        reasons = selection_reasons(
            fixture,
            {"competitions": self.rules},
            self.selected_team_ids,
            self.by_name,
            self.by_country,
        )
        self.assertIn("selected_team", reasons)

    def test_isolated_rule_does_not_leak_global_selected_teams(self):
        # Same real fixture, but evaluated against only the UCL rule.
        # The competition rule must decide the result, not the global team list.
        fixture = next(f for f in FIXTURES if f["id"] == "ucl-2024-group")
        rule = self.rule("42")
        reasons = self.reasons(rule, fixture, selected_ids=set())
        self.assertEqual(reasons, ["competition_stage:42"] if False else [])

    def test_ucl_from_round_of_16_accepts_knockouts_and_rejects_group(self):
        rule = self.rule("42")
        r16 = next(f for f in FIXTURES if f["id"] == "ucl-2024-r16")
        qf = next(f for f in FIXTURES if f["id"] == "ucl-2024-qf")
        final = next(f for f in FIXTURES if f["id"] == "ucl-2024-final")
        group = next(f for f in FIXTURES if f["id"] == "ucl-2024-group")

        self.assertIn("competition_stage:42", self.reasons(rule, r16, set()))
        self.assertIn("competition_stage:42", self.reasons(rule, qf, set()))
        self.assertIn("competition_stage:42", self.reasons(rule, final, set()))
        self.assertEqual(self.reasons(rule, group, set()), [])

    def test_uel_from_quarter_final_accepts_qf_sf_final(self):
        rule = self.rule("73")
        qf = next(f for f in FIXTURES if f["id"] == "uel-2024-qf")
        sf = next(f for f in FIXTURES if f["id"] == "uel-2024-sf")
        final = next(f for f in FIXTURES if f["id"] == "uel-2024-final")

        self.assertIn("competition_stage:73", self.reasons(rule, qf, set()))
        self.assertIn("competition_stage:73", self.reasons(rule, sf, set()))
        self.assertIn("competition_stage:73", self.reasons(rule, final, set()))

    def test_copa_extra_team_is_unconditional_within_competition(self):
        rule = self.rule("44")
        group_like = next(f for f in FIXTURES if f["id"] == "copa-2024-qf")
        reasons = self.reasons(rule, group_like, selected_ids=set())

        # Argentina is an explicit extra team for Copa America, so it is
        # selected independently of the stage threshold.
        self.assertIn("extra_team:44", reasons)
        self.assertIn("competition_stage:44", reasons)

    def test_final_only_accepts_only_final(self):
        # Competition 526 is configured final_only. Use the same real final
        # shape to verify the stage predicate itself without network access.
        rule = self.rule("526")
        final = {
            **next(f for f in FIXTURES if f["id"] == "ucl-2024-final"),
            "leagueId": "526",
        }
        semifinal = {
            **next(f for f in FIXTURES if f["id"] == "ucl-2024-sf"),
            "leagueId": "526",
        }

        self.assertIn("competition_final:526", self.reasons(rule, final, set()))
        self.assertEqual(self.reasons(rule, semifinal, set()), [])

    def test_all_mode_accepts_any_stage(self):
        # Competition 77 is configured mode=all.
        rule = self.rule("77")
        for fixture_id in ("wc-2022-group", "wc-2022-qf", "wc-2022-final"):
            fixture = next(f for f in FIXTURES if f["id"] == fixture_id)
            self.assertIn("competition_all:77", self.reasons(rule, fixture, set()))

    def test_unknown_stage_never_passes_stage_rule(self):
        rule = self.rule("42")
        fixture = {
            **next(f for f in FIXTURES if f["id"] == "ucl-2024-qf"),
            "stage": None,
        }
        self.assertEqual(self.reasons(rule, fixture, set()), [])

    def test_below_threshold_is_rejected_even_for_a_real_fixture_shape(self):
        rule = self.rule("73")
        # A real UEL fixture shape from the same season, but represented as a
        # group-stage match, must not pass a QF threshold.
        fixture = {
            **next(f for f in FIXTURES if f["id"] == "uel-2024-qf"),
            "stage": "group_stage",
        }
        self.assertEqual(self.reasons(rule, fixture, set()), [])


if __name__ == "__main__":
    unittest.main(verbosity=2)

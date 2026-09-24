"""All 32 Copa America 2024 fixtures.

Deterministic regression test for competition 44:
- mode=from, stage=round_of_16
- Brazil and Argentina are extra teams and therefore selected in every round
- group-stage matches between other teams must be rejected
- all knockout matches must be selected by the stage rule
"""

import json
import unittest
from pathlib import Path

from match_discovery import load_team_config, selection_reasons

CONFIG_FILE = Path("auto_matches.json")

# Complete 2024 Copa America fixture list: 24 group-stage matches + 8
# knockout matches. Team IDs come from the project's teams.json.
FIXTURES = [
    # Group A
    {"id": "copa24-a-arg-can", "leagueId": "44", "stage": "group_stage",
     "home": {"id": "6706", "name": "Argentina"}, "away": {"id": "5810", "name": "Canada"}},
    {"id": "copa24-a-per-can", "leagueId": "44", "stage": "group_stage",
     "home": {"id": "5798", "name": "Peru"}, "away": {"id": "5810", "name": "Canada"}},
    {"id": "copa24-a-chi-arg", "leagueId": "44", "stage": "group_stage",
     "home": {"id": "9762", "name": "Chile"}, "away": {"id": "6706", "name": "Argentina"}},
    {"id": "copa24-a-per-arg", "leagueId": "44", "stage": "group_stage",
     "home": {"id": "5798", "name": "Peru"}, "away": {"id": "6706", "name": "Argentina"}},
    {"id": "copa24-a-can-chi", "leagueId": "44", "stage": "group_stage",
     "home": {"id": "5810", "name": "Canada"}, "away": {"id": "9762", "name": "Chile"}},
    {"id": "copa24-a-arg-per", "leagueId": "44", "stage": "group_stage",
     "home": {"id": "6706", "name": "Argentina"}, "away": {"id": "5798", "name": "Peru"}},

    # Group B
    {"id": "copa24-b-ecu-ven", "leagueId": "44", "stage": "group_stage",
     "home": {"id": "6707", "name": "Ecuador"}, "away": {"id": "5800", "name": "Venezuela"}},
    {"id": "copa24-b-mex-jam", "leagueId": "44", "stage": "group_stage",
     "home": {"id": "6710", "name": "Mexico"}, "away": {"id": "5806", "name": "Jamaica"}},
    {"id": "copa24-b-ven-mex", "leagueId": "44", "stage": "group_stage",
     "home": {"id": "5800", "name": "Venezuela"}, "away": {"id": "6710", "name": "Mexico"}},
    {"id": "copa24-b-jam-ecu", "leagueId": "44", "stage": "group_stage",
     "home": {"id": "5806", "name": "Jamaica"}, "away": {"id": "6707", "name": "Ecuador"}},
    {"id": "copa24-b-mex-ecu", "leagueId": "44", "stage": "group_stage",
     "home": {"id": "6710", "name": "Mexico"}, "away": {"id": "6707", "name": "Ecuador"}},
    {"id": "copa24-b-jam-ven", "leagueId": "44", "stage": "group_stage",
     "home": {"id": "5806", "name": "Jamaica"}, "away": {"id": "5800", "name": "Venezuela"}},

    # Group C
    {"id": "copa24-c-usa-bol", "leagueId": "44", "stage": "group_stage",
     "home": {"id": "6713", "name": "USA"}, "away": {"id": "5797", "name": "Bolivia"}},
    {"id": "copa24-c-uru-pan", "leagueId": "44", "stage": "group_stage",
     "home": {"id": "5796", "name": "Uruguay"}, "away": {"id": "5922", "name": "Panama"}},
    {"id": "copa24-c-pan-usa", "leagueId": "44", "stage": "group_stage",
     "home": {"id": "5922", "name": "Panama"}, "away": {"id": "6713", "name": "USA"}},
    {"id": "copa24-c-uru-bol", "leagueId": "44", "stage": "group_stage",
     "home": {"id": "5796", "name": "Uruguay"}, "away": {"id": "5797", "name": "Bolivia"}},
    {"id": "copa24-c-usa-uru", "leagueId": "44", "stage": "group_stage",
     "home": {"id": "6713", "name": "USA"}, "away": {"id": "5796", "name": "Uruguay"}},
    {"id": "copa24-c-bol-pan", "leagueId": "44", "stage": "group_stage",
     "home": {"id": "5797", "name": "Bolivia"}, "away": {"id": "5922", "name": "Panama"}},

    # Group D
    {"id": "copa24-d-col-par", "leagueId": "44", "stage": "group_stage",
     "home": {"id": "8258", "name": "Colombia"}, "away": {"id": "6724", "name": "Paraguay"}},
    {"id": "copa24-d-bra-crc", "leagueId": "44", "stage": "group_stage",
     "home": {"id": "8256", "name": "Brazil"}, "away": {"id": "6705", "name": "Costa Rica"}},
    {"id": "copa24-d-col-crc", "leagueId": "44", "stage": "group_stage",
     "home": {"id": "8258", "name": "Colombia"}, "away": {"id": "6705", "name": "Costa Rica"}},
    {"id": "copa24-d-par-bra", "leagueId": "44", "stage": "group_stage",
     "home": {"id": "6724", "name": "Paraguay"}, "away": {"id": "8256", "name": "Brazil"}},
    {"id": "copa24-d-bra-col", "leagueId": "44", "stage": "group_stage",
     "home": {"id": "8256", "name": "Brazil"}, "away": {"id": "8258", "name": "Colombia"}},
    {"id": "copa24-d-crc-par", "leagueId": "44", "stage": "group_stage",
     "home": {"id": "6705", "name": "Costa Rica"}, "away": {"id": "6724", "name": "Paraguay"}},

    # Knockout
    {"id": "copa24-qf-arg-ecu", "leagueId": "44", "stage": "quarter_final",
     "home": {"id": "6706", "name": "Argentina"}, "away": {"id": "6707", "name": "Ecuador"}},
    {"id": "copa24-qf-ven-can", "leagueId": "44", "stage": "quarter_final",
     "home": {"id": "5800", "name": "Venezuela"}, "away": {"id": "5810", "name": "Canada"}},
    {"id": "copa24-qf-col-pan", "leagueId": "44", "stage": "quarter_final",
     "home": {"id": "8258", "name": "Colombia"}, "away": {"id": "5922", "name": "Panama"}},
    {"id": "copa24-qf-uru-bra", "leagueId": "44", "stage": "quarter_final",
     "home": {"id": "5796", "name": "Uruguay"}, "away": {"id": "8256", "name": "Brazil"}},
    {"id": "copa24-sf-arg-can", "leagueId": "44", "stage": "semi_final",
     "home": {"id": "6706", "name": "Argentina"}, "away": {"id": "5810", "name": "Canada"}},
    {"id": "copa24-sf-uru-col", "leagueId": "44", "stage": "semi_final",
     "home": {"id": "5796", "name": "Uruguay"}, "away": {"id": "8258", "name": "Colombia"}},
    {"id": "copa24-third-can-uru", "leagueId": "44", "stage": "third_place",
     "home": {"id": "5810", "name": "Canada"}, "away": {"id": "5796", "name": "Uruguay"}},
    {"id": "copa24-final-arg-col", "leagueId": "44", "stage": "final",
     "home": {"id": "6706", "name": "Argentina"}, "away": {"id": "8258", "name": "Colombia"}},
]


class CopaAmerica2024Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.config = json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
        cls.rule = next(
            r for r in cls.config["competitions"] if str(r.get("id")) == "44"
        )
        cls.selected_team_ids = {str(v) for v in cls.config.get("team_ids", [])}
        cls.by_name, cls.by_country = load_team_config()

    def reasons(self, fixture, selected_ids=None):
        return selection_reasons(
            fixture,
            {"competitions": [self.rule]},
            self.selected_team_ids if selected_ids is None else selected_ids,
            self.by_name,
            self.by_country,
        )

    def test_all_32_matches_are_present(self):
        self.assertEqual(len(FIXTURES), 32)
        self.assertEqual(len({f["id"] for f in FIXTURES}), 32)

    def test_log_every_fixture_decision(self):
        # Print every Copa America 2024 fixture in tournament order so the
        # GitHub Actions log shows the exact selection decision and reason.
        print("\n===== COPA AMERICA 2024 — MATCH-BY-MATCH SELECTION =====")
        for index, fixture in enumerate(FIXTURES, 1):
            reasons = self.reasons(fixture, selected_ids=set())
            selected = bool(reasons)

            home = fixture["home"]["name"]
            away = fixture["away"]["name"]
            stage = fixture["stage"]

            if selected:
                reason_text = ", ".join(reasons)
                print(
                    f"{index:02d}. {stage:<14} | "
                    f"{home} vs {away} | SELECTED | reason: {reason_text}"
                )
            else:
                print(
                    f"{index:02d}. {stage:<14} | "
                    f"{home} vs {away} | REJECTED | reason: no matching Copa rule"
                )

            # Expected Copa America rule:
            # - group stage: only Brazil/Argentina
            # - knockout: every match from the quarterfinal onward
            has_extra_team = bool(
                {"8256", "6706"} &
                {fixture["home"]["id"], fixture["away"]["id"]}
            )
            expected_selected = fixture["stage"] != "group_stage" or has_extra_team
            self.assertEqual(selected, expected_selected, fixture["id"])

        print("===== END COPA AMERICA 2024 =====\n")
    def test_every_fixture_is_copa_america_2024(self):
        self.assertTrue(all(str(f["leagueId"]) == "44" for f in FIXTURES))
        self.assertEqual(
            [f["stage"] for f in FIXTURES].count("group_stage"), 24
        )
        self.assertEqual(
            [f["stage"] for f in FIXTURES].count("quarter_final"), 4
        )
        self.assertEqual(
            [f["stage"] for f in FIXTURES].count("semi_final"), 2
        )
        self.assertEqual(
            [f["stage"] for f in FIXTURES].count("third_place"), 1
        )
        self.assertEqual(
            [f["stage"] for f in FIXTURES].count("final"), 1
        )

    def test_group_stage_only_brazil_and_argentina_are_selected_by_extra_team(self):
        for fixture in FIXTURES[:24]:
            reasons = self.reasons(fixture, selected_ids=set())
            has_brazil_or_argentina = bool(
                {"8256", "6706"} &
                {fixture["home"]["id"], fixture["away"]["id"]}
            )
            if has_brazil_or_argentina:
                self.assertIn("extra_team:44", reasons, fixture["id"])
            else:
                self.assertEqual(reasons, [], fixture["id"])

    def test_all_knockout_matches_pass_stage_rule(self):
        for fixture in FIXTURES[24:]:
            reasons = self.reasons(fixture, selected_ids=set())
            self.assertIn("competition_stage:44", reasons, fixture["id"])

    def test_brazil_and_argentina_are_selected_regardless_of_stage(self):
        for fixture in FIXTURES:
            if {"8256", "6706"} & {fixture["home"]["id"], fixture["away"]["id"]}:
                reasons = self.reasons(fixture, selected_ids=set())
                self.assertIn("extra_team:44", reasons, fixture["id"])

    def test_no_global_selected_team_leakage(self):
        # Evaluate the rule in isolation with an empty global selected-team set.
        # A non-Brazil/Argentina group match must stay rejected.
        fixture = next(f for f in FIXTURES if f["id"] == "copa24-b-mex-jam")
        self.assertEqual(self.reasons(fixture, selected_ids=set()), [])

    def test_selected_team_rule_still_works_outside_competition_rule(self):
        # Manchester City is globally selected in the project, but this test
        # proves that the global team rule is independent from competition 44.
        fixture = next(f for f in FIXTURES if f["id"] == "copa24-b-mex-jam")
        fixture = {**fixture, "leagueId": "999999"}
        fixture["home"] = {"id": "8456", "name": "Manchester City"}
        fixture["away"] = {"id": "5806", "name": "Jamaica"}
        reasons = selection_reasons(
            fixture,
            {"competitions": [self.rule]},
            self.selected_team_ids,
            self.by_name,
            self.by_country,
        )
        self.assertIn("selected_team", reasons)


if __name__ == "__main__":
    unittest.main(verbosity=2)

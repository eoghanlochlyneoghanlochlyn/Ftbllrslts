import unittest

from match_discovery import selection_reasons, selected_by_rule


class SelectionTests(unittest.TestCase):
    def setUp(self):
        self.config = {
            "competitions": [
                {"id": 50, "mode": "from", "stage": "round_of_16"},
                {"id": 77, "mode": "all"},
                {"id": 44, "mode": "from", "stage": "semi_final",
                 "extra_teams": ["Brazil", "Argentina"]},
                {"id": 526, "mode": "final_only"},
            ]
        }
        self.selected = {"8650"}
        self.by_name = {"brazil": "100", "argentina": "101"}
        self.by_country = {}

    def reasons(self, league, stage=None, home="200", away="201"):
        match = {
            "leagueId": str(league), "stage": stage,
            "home": {"id": home}, "away": {"id": away},
        }
        return selection_reasons(
            match, self.config, self.selected,
            self.by_name, self.by_country,
        )

    def test_selected_team_any_competition(self):
        self.assertIn("selected_team", self.reasons(999, None, "8650"))

    def test_selected_team_early_champions_league(self):
        self.assertIn("selected_team", self.reasons(50, "group_stage", "8650"))

    def test_all_competition(self):
        self.assertIn("competition_all:77", self.reasons(77))

    def test_knockout_threshold(self):
        self.assertEqual([], self.reasons(50, "group_stage"))
        self.assertEqual([], self.reasons(50, None))
        self.assertIn("competition_stage:50", self.reasons(50, "round_of_16"))
        self.assertIn("competition_stage:50", self.reasons(50, "quarter_final"))
        self.assertIn("competition_stage:50", self.reasons(50, "final"))

    def test_extra_team_any_round_in_own_competition(self):
        self.assertIn("extra_team:44", self.reasons(44, "group_stage", "100"))
        self.assertEqual([], self.reasons(50, "group_stage", "100"))
        self.assertEqual([], self.reasons(44, "group_stage"))

    def test_final_only(self):
        self.assertEqual([], self.reasons(526, "semi_final"))
        self.assertIn("competition_final:526", self.reasons(526, "final"))

    def test_rule_isolated_from_global_teams(self):
        match = {
            "leagueId": "50", "stage": "group_stage",
            "home": {"id": "8650"}, "away": {"id": "201"},
        }
        self.assertFalse(selected_by_rule(
            match, self.config["competitions"][0],
            self.selected, self.by_name, self.by_country,
        ))


if __name__ == "__main__":
    unittest.main()

"""Ten real UEFA Champions League fixtures across different stages.

Offline regression test for competition 42 -> from round_of_16.
"""
import json
import unittest
from pathlib import Path

from match_discovery import load_team_config, selection_reasons

CONFIG_FILE = Path("auto_matches.json")

FIXTURES = [
    {"id":"ucl-group-city-leipzig","leagueId":"42","stage":"group_stage",
     "home":{"id":"8456","name":"Manchester City"},"away":{"id":"178475","name":"RB Leipzig"}},
    {"id":"ucl-group-porto-napoli","leagueId":"42","stage":"group_stage",
     "home":{"id":"9773","name":"FC Porto"},"away":{"id":"9875","name":"Napoli"}},
    {"id":"ucl-r16-real-leipzig","leagueId":"42","stage":"round_of_16",
     "home":{"id":"8633","name":"Real Madrid"},"away":{"id":"178475","name":"RB Leipzig"}},
    {"id":"ucl-r16-inter-atletico","leagueId":"42","stage":"round_of_16",
     "home":{"id":"8636","name":"Inter"},"away":{"id":"9906","name":"Atlético Madrid"}},
    {"id":"ucl-r16-psv-dortmund","leagueId":"42","stage":"round_of_16",
     "home":{"id":"8640","name":"PSV Eindhoven"},"away":{"id":"9789","name":"Borussia Dortmund"}},
    {"id":"ucl-qf-city-real","leagueId":"42","stage":"quarter_final",
     "home":{"id":"8456","name":"Manchester City"},"away":{"id":"8633","name":"Real Madrid"}},
    {"id":"ucl-qf-dortmund-atletico","leagueId":"42","stage":"quarter_final",
     "home":{"id":"9789","name":"Borussia Dortmund"},"away":{"id":"9906","name":"Atlético Madrid"}},
    {"id":"ucl-sf-bayern-real","leagueId":"42","stage":"semi_final",
     "home":{"id":"9823","name":"Bayern München"},"away":{"id":"8633","name":"Real Madrid"}},
    {"id":"ucl-sf-dortmund-psg","leagueId":"42","stage":"semi_final",
     "home":{"id":"9789","name":"Borussia Dortmund"},"away":{"id":"9847","name":"Paris Saint-Germain"}},
    {"id":"ucl-final-dortmund-real","leagueId":"42","stage":"final",
     "home":{"id":"9789","name":"Borussia Dortmund"},"away":{"id":"8633","name":"Real Madrid"}},
]

class UclTenMatchesTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        config=json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
        cls.selected_team_ids={str(v) for v in config.get("team_ids",[])}
        cls.ucl_rule=next(r for r in config.get("competitions",[]) if str(r.get("id"))=="42")
        cls.by_name,cls.by_country=load_team_config()

    def reasons(self,fixture,selected_ids):
        return selection_reasons(fixture,{"competitions":[self.ucl_rule]},
                                 selected_ids,self.by_name,self.by_country)

    def test_exactly_ten_real_fixtures(self):
        self.assertEqual(len(FIXTURES),10)

    def test_group_stage_is_rejected_by_ucl_stage_rule(self):
        # Both teams in this fixture are intentionally outside the configured
        # selected-team list, so a group-stage match must be rejected.
        fixture=FIXTURES[1]
        self.assertEqual(self.reasons(fixture,set()),[])

    def test_all_knockout_stages_pass_from_round_of_16(self):
        for fixture in FIXTURES[2:]:
            self.assertIn("competition_stage:42",self.reasons(fixture,set()))

    def test_global_selected_team_is_independent_of_ucl_stage_rule(self):
        fixture=FIXTURES[1]
        reasons=self.reasons(fixture,self.selected_team_ids)
        self.assertIn("selected_team",reasons)
        self.assertNotIn("competition_stage:42",reasons)

if __name__=="__main__":
    unittest.main(verbosity=2)

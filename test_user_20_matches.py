"""20 user-specified historical selection scenarios.

This is an isolated, OFFLINE rule test, not live FotMob stage extraction.
Stages below are test assumptions and must be independently checked against
FotMob before interpreting a stage-based PASS as an integration PASS.
No writes to matches.json and no Telegram messages.
"""
import json
import unittest
from pathlib import Path
from match_discovery import load_team_config, selection_reasons

FIXTURES = [
  {
    "id": "6050065",
    "home": {
      "id": "101614",
      "name": "Esteghlal"
    },
    "away": {
      "id": "",
      "name": "Al Sadd"
    },
    "leagueId": "525",
    "stage": None,
    "expected": True
  },
  {
    "id": "6050068",
    "home": {
      "id": "",
      "name": "Al Ahli"
    },
    "away": {
      "id": "102141",
      "name": "Pakhtakor Tashkent"
    },
    "leagueId": "525",
    "stage": None,
    "expected": False
  },
  {
    "id": "6050066",
    "home": {
      "id": "",
      "name": "Shabab Al Ahli"
    },
    "away": {
      "id": "176352",
      "name": "Tractor"
    },
    "leagueId": "525",
    "stage": None,
    "expected": True
  },
  {
    "id": "6054511",
    "home": {
      "id": "",
      "name": "Al Hussein"
    },
    "away": {
      "id": "",
      "name": "Al Seeb"
    },
    "leagueId": "9469",
    "stage": "group_stage",
    "expected": False
  },
  {
    "id": "6054591",
    "home": {
      "id": "",
      "name": "Al Jazira"
    },
    "away": {
      "id": "389880",
      "name": "Gol Gohar"
    },
    "leagueId": "9469",
    "stage": "group_stage",
    "expected": True
  },
  {
    "id": "5802946",
    "home": {
      "id": "8121",
      "name": "Angers"
    },
    "away": {
      "id": "8521",
      "name": "Brest"
    },
    "leagueId": "53",
    "stage": "regular_season",
    "expected": False
  },
  {
    "id": "5206271",
    "home": {
      "id": "8370",
      "name": "Rayo Vallecano"
    },
    "away": {
      "id": "9826",
      "name": "Crystal Palace"
    },
    "leagueId": "73",
    "stage": "semi_final",
    "expected": True
  },
  {
    "id": "5206268",
    "home": {
      "id": "8370",
      "name": "Rayo Vallecano"
    },
    "away": {
      "id": "9848",
      "name": "Strasbourg"
    },
    "leagueId": "73",
    "stage": "quarter_final",
    "expected": True
  },
  {
    "id": "5206261",
    "home": {
      "id": "8370",
      "name": "Rayo Vallecano"
    },
    "away": {
      "id": "8563",
      "name": "AEK Athens"
    },
    "leagueId": "73",
    "stage": "round_of_16",
    "expected": False
  },
  {
    "id": "5206177",
    "home": {
      "id": "8358",
      "name": "Freiburg"
    },
    "away": {
      "id": "10252",
      "name": "Aston Villa"
    },
    "leagueId": "42",
    "stage": "final",
    "expected": True
  },
  {
    "id": "5206175",
    "home": {
      "id": "8358",
      "name": "Freiburg"
    },
    "away": {
      "id": "10264",
      "name": "Braga"
    },
    "leagueId": "42",
    "stage": "semi_final",
    "expected": True
  },
  {
    "id": "5206166",
    "home": {
      "id": "8358",
      "name": "Freiburg"
    },
    "away": {
      "id": "9910",
      "name": "Celta Vigo"
    },
    "leagueId": "42",
    "stage": "quarter_final",
    "expected": True
  },
  {
    "id": "5161883",
    "home": {
      "id": "8468",
      "name": "Brann"
    },
    "away": {
      "id": "9857",
      "name": "Bologna"
    },
    "leagueId": "42",
    "stage": "playoff",
    "expected": False
  },
  {
    "id": "4947790",
    "home": {
      "id": "",
      "name": "Rangers"
    },
    "away": {
      "id": "",
      "name": "Ludogorets"
    },
    "leagueId": "42",
    "stage": "league_phase",
    "expected": False
  },
  {
    "id": "4932342",
    "home": {
      "id": "8564",
      "name": "Milan"
    },
    "away": {
      "id": "9888",
      "name": "Lecce"
    },
    "leagueId": "55",
    "stage": "regular_season",
    "expected": True
  },
  {
    "id": "4932346",
    "home": {
      "id": "6479",
      "name": "Pisa"
    },
    "away": {
      "id": "9804",
      "name": "Torino"
    },
    "leagueId": "55",
    "stage": "regular_season",
    "expected": False
  },
  {
    "id": "4935322",
    "home": {
      "id": "8524",
      "name": "Atalanta"
    },
    "away": {
      "id": "8543",
      "name": "Lazio"
    },
    "leagueId": "55",
    "stage": "regular_season",
    "expected": True
  },
  {
    "id": "4934509",
    "home": {
      "id": "8564",
      "name": "Milan"
    },
    "away": {
      "id": "9875",
      "name": "Napoli"
    },
    "leagueId": "55",
    "stage": "regular_season",
    "expected": True
  },
  {
    "id": "4934510",
    "home": {
      "id": "8636",
      "name": "Inter"
    },
    "away": {
      "id": "9857",
      "name": "Bologna"
    },
    "leagueId": "55",
    "stage": "regular_season",
    "expected": True
  },
  {
    "id": "4934511",
    "home": {
      "id": "9857",
      "name": "Bologna"
    },
    "away": {
      "id": "9875",
      "name": "Napoli"
    },
    "leagueId": "55",
    "stage": "regular_season",
    "expected": True
  }
]

class UserMatchSelectionTest(unittest.TestCase):
    def test_all_twenty_matches(self):
        config = json.loads(Path("auto_matches.json").read_text(encoding="utf-8"))
        selected_teams = {str(x) for x in config["team_ids"]}
        by_name, by_country = load_team_config()
        mismatches = []
        for index, match in enumerate(FIXTURES, 1):
            reasons = selection_reasons(match, config, selected_teams, by_name, by_country)
            actual = bool(reasons)
            expected = match["expected"]
            result = "PASS" if actual == expected else "MISMATCH"
            stage = match["stage"] or "unknown"
            print(
                f"[{index:02d}/20] {result} | {match['home']['name']} vs {match['away']['name']}"
                f" | id={match['id']} | competition={match['leagueId']} | stage={stage}"
                f" | actual={'SELECTED' if actual else 'REJECTED'}"
                f" | expected={'SELECTED' if expected else 'REJECTED'}"
                f" | reason={','.join(reasons) if reasons else 'no matching selection rule'}",
                flush=True,
            )
            if actual != expected:
                mismatches.append(match["id"])
        print(f"SUMMARY | total={len(FIXTURES)} | matched={len(FIXTURES)-len(mismatches)} | mismatched={len(mismatches)} | ids={mismatches}", flush=True)
        self.assertFalse(mismatches, f"Expected/actual differences for match IDs: {mismatches}")

if __name__ == "__main__":
    unittest.main(verbosity=2)

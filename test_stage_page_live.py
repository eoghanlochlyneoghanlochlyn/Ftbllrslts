"""Read-only live regression test for FotMob match-page stage fallback.

Run with: python -m unittest -v test_stage_page_live.py
No writes to matches.json or state.json.
"""
import unittest
from unittest.mock import patch

from match_discovery import (
    fetch_match_page_stage,
    fetch_matches_for_date,
    selection_reasons,
)


class LiveStagePageTests(unittest.TestCase):
    def test_historical_knockout_pages(self):
        # Historical real match IDs retained from the original fallback test.
        fixtures = {
            "4737599": "round_of_16",
            "3835589": "round_of_16",
        }
        for match_id, expected in fixtures.items():
            with self.subTest(match_id=match_id):
                actual = fetch_match_page_stage(match_id)
                self.assertEqual(
                    expected, actual,
                    f"FotMob match {match_id}: expected {expected}, got {actual}",
                )

    def test_historical_group_matches_not_knockout(self):
        # Pick actual Champions League fixtures from a historical
        # league-phase date, rather than guessing match IDs.
        fixtures = [
            match for match in fetch_matches_for_date("20251126")
            if str(match.get("leagueId")) == "42"
        ]
        self.assertGreaterEqual(
            len(fixtures), 2,
            "Historical daily endpoint returned fewer than 2 UCL matches; "
            "cannot validate group/league-phase false positives.",
        )
        for match in fixtures[:2]:
            match_id = match["id"]
            with self.subTest(group_match=match_id):
                actual = fetch_match_page_stage(match_id)
                self.assertNotIn(
                    actual,
                    {"round_of_32", "round_of_16", "quarter_final",
                     "semi_final", "final"},
                    f"League-phase match {match_id} falsely classified: {actual}",
                )


if __name__ == "__main__":
    unittest.main()

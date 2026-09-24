"""Exhaustive historical regression test for configured competition 10703."""

import unittest

from historical_competition_test_helpers import run_exhaustive_competition_test


class Competition10703ExhaustiveTests(unittest.TestCase):
    def test_every_match_of_latest_completed_season(self):
        run_exhaustive_competition_test(self, "10703")


if __name__ == "__main__":
    unittest.main(verbosity=2)

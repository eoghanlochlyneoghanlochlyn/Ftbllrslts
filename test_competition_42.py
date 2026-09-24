"""Exhaustive historical regression test for configured competition 42."""

import unittest

from historical_competition_test_helpers import run_exhaustive_competition_test


class Competition42ExhaustiveTests(unittest.TestCase):
    def test_every_match_of_latest_completed_season(self):
        run_exhaustive_competition_test(self, "42")


if __name__ == "__main__":
    unittest.main(verbosity=2)

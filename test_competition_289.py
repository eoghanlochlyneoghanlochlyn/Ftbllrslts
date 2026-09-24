"""Exhaustive historical regression test for configured competition 289."""

import unittest

from historical_competition_test_helpers import run_exhaustive_competition_test


class Competition289ExhaustiveTests(unittest.TestCase):
    def test_every_match_of_latest_completed_season(self):
        run_exhaustive_competition_test(self, "289")


if __name__ == "__main__":
    unittest.main(verbosity=2)

"""Synthetic regression tests for FotMob VAR goal-cancellation detection.

The fixtures mirror the FotMob event shape relevant to Netherlands-Germany
(match 5181825), where Virgil van Dijk's goal was later ruled out by VAR.

These tests do not call FotMob or Telegram. They exercise event_detector.py,
including the production case where the original goal was seen on an earlier
poll and the later poll contains only the VAR decision.
"""

import unittest

from event_detector import (
    detect_cancelled_goals,
    get_cancelled_var_events,
)


def fotmob_goal(
    *,
    minute=13,
    is_home=True,
    player_id=9991,
    player_name="Virgil van Dijk",
    react_key="goal-van-dijk-13",
):
    return {
        "type": "Goal",
        "reactKey": react_key,
        "isHome": is_home,
        "time": minute,
        "player": {
            "id": player_id,
            "name": player_name,
        },
    }


def fotmob_var(
    *,
    minute=13,
    is_home=True,
    player_id=9991,
    player_name="Virgil van Dijk",
    text="VAR: Goal ruled out - foul",
    react_key="var-van-dijk-13",
):
    return {
        "type": "VAR",
        "reactKey": react_key,
        "isHome": is_home,
        "time": minute,
        "player": {
            "id": player_id,
            "name": player_name,
        },
        "description": text,
    }


class VarCancellationTests(unittest.TestCase):

    def assert_one_cancelled(
        self,
        result,
        *,
        player_name="Virgil van Dijk",
        minute="13",
        reason="foul",
    ):
        self.assertEqual(
            len(result),
            1,
            f"Expected exactly one cancellation, got: {result}",
        )

        item = result[0]

        self.assertEqual(
            item["minute"],
            minute,
        )

        self.assertTrue(
            item["cancelled_by_var"]
        )

        self.assertEqual(
            item["goal_event"]["player"]["name"],
            player_name,
        )

        if reason is not None:
            self.assertEqual(
                item["cancel_reason"],
                reason,
            )

    def test_01_immediate_var_cancellation(self):
        goal = fotmob_goal()
        var = fotmob_var()

        result = detect_cancelled_goals(
            [goal, var],
            {},
        )

        self.assert_one_cancelled(result)

    def test_02_delayed_var_cancellation_30_minutes_later(self):
        goal = fotmob_goal(minute=13)
        var = fotmob_var(
            minute=30,
            text="VAR: Goal ruled out - foul",
        )

        result = detect_cancelled_goals(
            [goal, var],
            {},
        )

        self.assert_one_cancelled(result)

    def test_03_delayed_var_cancellation_70_minutes_later(self):
        goal = fotmob_goal(minute=13)
        var = fotmob_var(
            minute=70,
            text="VAR: Goal ruled out - foul",
        )

        result = detect_cancelled_goals(
            [goal, var],
            {},
        )

        self.assert_one_cancelled(result)

    def test_04_second_poll_uses_goal_saved_in_state(self):
        """
        Poll 1:
            FotMob shows the goal.

        Poll 2:
            The current event list contains only the later VAR decision.

        The stored goal must still be matched.
        """
        goal = fotmob_goal(
            minute=13,
            react_key="goal-seen-on-poll-1",
        )

        match_state = {
            "goals": [
                {
                    "event_key": "react:goal-seen-on-poll-1",
                    "player_id": 9991,
                    "player_name": "Virgil van Dijk",
                    "is_home": True,
                    "minute": "13",
                    "event": goal,
                    "cancelled": False,
                }
            ]
        }

        var = fotmob_var(
            minute=30,
            text="VAR: Goal ruled out - foul",
            react_key="var-seen-on-poll-2",
        )

        result = detect_cancelled_goals(
            [var],
            match_state,
        )

        self.assert_one_cancelled(result)

        self.assertEqual(
            result[0]["goal_key"],
            "react:goal-seen-on-poll-1",
        )

    def test_05_generic_var_review_must_not_cancel_goal(self):
        goal = fotmob_goal()
        var = fotmob_var(
            text="VAR: Goal check",
        )

        result = detect_cancelled_goals(
            [goal, var],
            {},
        )

        self.assertEqual(result, [])
        self.assertEqual(
            get_cancelled_var_events([var]),
            [],
        )

    def test_06_penalty_cancelled_is_not_goal_cancelled(self):
        goal = fotmob_goal()
        var = fotmob_var(
            text="VAR: Penalty cancelled",
        )

        result = detect_cancelled_goals(
            [goal, var],
            {},
        )

        self.assertEqual(result, [])
        self.assertEqual(
            get_cancelled_var_events([var]),
            [],
        )

    def test_07_wrong_team_cannot_cancel_goal(self):
        goal = fotmob_goal(
            is_home=True,
        )
        var = fotmob_var(
            is_home=False,
            text="VAR: Goal ruled out - foul",
        )

        result = detect_cancelled_goals(
            [goal, var],
            {},
        )

        self.assertEqual(result, [])

    def test_08_player_identity_resolves_delayed_cancellation(self):
        goal = fotmob_goal(
            minute=13,
            player_id=1234,
            player_name="Virgil van Dijk",
        )
        var = fotmob_var(
            minute=45,
            player_id=1234,
            player_name="Virgil van Dijk",
            text="VAR: Goal ruled out - foul",
        )

        result = detect_cancelled_goals(
            [goal, var],
            {},
        )

        self.assert_one_cancelled(result)

    def test_09_explicit_cancelled_goal_event(self):
        goal = fotmob_goal()
        goal["cancelled"] = True
        goal["description"] = "Goal cancelled - offside"

        result = detect_cancelled_goals(
            [goal],
            {},
        )

        self.assertEqual(
            len(result),
            1,
        )
        self.assertFalse(
            result[0]["cancelled_by_var"]
        )
        self.assertEqual(
            result[0]["cancel_reason"],
            "offside",
        )

    def test_10_two_goals_same_team_use_player_identity(self):
        first_goal = fotmob_goal(
            minute=10,
            player_id=111,
            player_name="First Player",
            react_key="goal-first",
        )

        second_goal = fotmob_goal(
            minute=25,
            player_id=222,
            player_name="Second Player",
            react_key="goal-second",
        )

        var = fotmob_var(
            minute=40,
            player_id=111,
            player_name="First Player",
            text="VAR: Goal ruled out - handball",
        )

        result = detect_cancelled_goals(
            [first_goal, second_goal, var],
            {},
        )

        self.assert_one_cancelled(
            result,
            player_name="First Player",
            minute="10",
            reason="handball",
        )

    def test_11_only_explicit_final_wording_counts(self):
        goal = fotmob_goal()

        for text in (
            "VAR",
            "VAR check",
            "VAR review",
            "VAR decision",
            "VAR: Goal checked",
            "VAR: Checking possible foul",
        ):
            with self.subTest(text=text):
                var = fotmob_var(text=text)

                self.assertEqual(
                    detect_cancelled_goals(
                        [goal, var],
                        {},
                    ),
                    [],
                )



    def test_12_tbd_scorer_is_updated_even_if_fotmob_changes_react_key(self):
        from event_detector import detect_updated_goals

        tbd_goal = fotmob_goal(
            minute=25,
            is_home=True,
            player_id=None,
            player_name="TBD",
            react_key="goal-original",
        )

        match_state = {
            "goals": [
                {
                    "event_key": "react:goal-original",
                    "player_id": None,
                    "player_name": "TBD",
                    "is_home": True,
                    "minute": "25",
                    "telegram_message_id": 500,
                    "needs_update": True,
                    "cancelled": False,
                    "event": tbd_goal,
                }
            ]
        }

        enriched_goal = fotmob_goal(
            minute=25,
            is_home=True,
            player_id=7777,
            player_name="Real Scorer",
            react_key="goal-rebuilt-with-scorer",
        )

        result = detect_updated_goals(
            match_state,
            [enriched_goal],
        )

        self.assertEqual(len(result), 1)
        self.assertEqual(
            result[0]["event_key"],
            "react:goal-original",
        )
        self.assertEqual(
            result[0]["_new_event_key"],
            "react:goal-rebuilt-with-scorer",
        )
        self.assertEqual(
            result[0]["player_name"],
            "Real Scorer",
        )
        self.assertEqual(
            result[0]["player_id"],
            7777,
        )


    def test_13_tbd_fallback_does_not_guess_between_two_same_minute_goals(self):
        from event_detector import detect_updated_goals

        goal_one = fotmob_goal(
            minute=25,
            is_home=True,
            player_id=None,
            player_name="TBD",
            react_key="goal-one",
        )
        goal_two = fotmob_goal(
            minute=25,
            is_home=True,
            player_id=None,
            player_name="TBD",
            react_key="goal-two",
        )

        match_state = {
            "goals": [
                {
                    "event_key": "react:goal-one",
                    "player_id": None,
                    "player_name": "TBD",
                    "is_home": True,
                    "minute": "25",
                    "telegram_message_id": 500,
                    "needs_update": True,
                    "cancelled": False,
                    "event": goal_one,
                },
                {
                    "event_key": "react:goal-two",
                    "player_id": None,
                    "player_name": "TBD",
                    "is_home": True,
                    "minute": "25",
                    "telegram_message_id": 501,
                    "needs_update": True,
                    "cancelled": False,
                    "event": goal_two,
                },
            ]
        }

        enriched_goal = fotmob_goal(
            minute=25,
            is_home=True,
            player_id=7777,
            player_name="Real Scorer",
            react_key="goal-rebuilt-with-scorer",
        )

        result = detect_updated_goals(
            match_state,
            [enriched_goal],
        )

        self.assertEqual(result, [])


    def test_14_tbd_fallback_rejects_wrong_team(self):
        from event_detector import detect_updated_goals

        tbd_goal = fotmob_goal(
            minute=25,
            is_home=True,
            player_id=None,
            player_name="TBD",
            react_key="goal-original",
        )

        match_state = {
            "goals": [
                {
                    "event_key": "react:goal-original",
                    "player_id": None,
                    "player_name": "TBD",
                    "is_home": True,
                    "minute": "25",
                    "telegram_message_id": 500,
                    "needs_update": True,
                    "cancelled": False,
                    "event": tbd_goal,
                }
            ]
        }

        enriched_goal = fotmob_goal(
            minute=25,
            is_home=False,
            player_id=7777,
            player_name="Real Scorer",
            react_key="goal-rebuilt-with-scorer",
        )

        result = detect_updated_goals(
            match_state,
            [enriched_goal],
        )

        self.assertEqual(result, [])


if __name__ == "__main__":
    unittest.main(verbosity=2)

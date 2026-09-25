"""Live Telegram integration tests for VAR and TBD logic."""

import os
import time
import unittest

from event_detector import detect_cancelled_goals, detect_updated_goals
from formatter import get_competition_display_name
from telegram_sender import send_telegram
import requests


def edit_telegram_test_message(message_id, text):
    token = os.getenv("TELEGRAMBOT")
    chat_id = os.getenv("TELEGRAMCHANNEL")
    response = requests.post(
        f"https://api.telegram.org/bot{token}/editMessageText",
        data={"chat_id": chat_id, "message_id": int(message_id), "text": text},
        timeout=30,
    )
    response.raise_for_status()
    data = response.json()
    if not data.get("ok"):
        raise RuntimeError(f"Telegram edit failed: {data}")
    return data



class TelegramLogicTests(unittest.TestCase):

    def setUp(self):
        if not os.getenv("TELEGRAMBOT") or not os.getenv("TELEGRAMCHANNEL"):
            self.skipTest("Telegram secrets are required.")

    def report(self, number, title, details):
        return send_telegram(
            f"🧪 تست زنده ربات — {number}\n{title}\n\n{details}"
        )

    def wait(self):
        time.sleep(1)

    def goal(
        self,
        minute=13,
        is_home=True,
        player_id=9991,
        player_name="Virgil van Dijk",
        react_key="goal-test",
    ):
        return {
            "type": "Goal",
            "reactKey": react_key,
            "isHome": is_home,
            "time": minute,
            "player": {"id": player_id, "name": player_name},
        }

    def var(
        self,
        minute=13,
        is_home=True,
        player_id=9991,
        player_name="Virgil van Dijk",
        text="VAR: Goal ruled out - foul",
        react_key="var-test",
    ):
        return {
            "type": "VAR",
            "reactKey": react_key,
            "isHome": is_home,
            "time": minute,
            "player": {"id": player_id, "name": player_name},
            "description": text,
        }

    def stored(self, goal, event_key, message_id=None, needs_update=False):
        return {
            "event_key": event_key,
            "player_id": goal["player"].get("id"),
            "player_name": goal["player"].get("name"),
            "is_home": goal.get("isHome"),
            "minute": str(goal.get("time")),
            "telegram_message_id": message_id,
            "needs_update": needs_update,
            "cancelled": False,
            "event": goal,
        }

    def test_00_group_display(self):
        grouped = {
            "league_fa": "لیگ ملت‌های اروپا",
            "group_info": {"name_fa": "گروه 2"},
            "round_info": {"name_fa": None},
        }
        knockout = {
            "league_fa": "جام جهانی",
            "group_info": {"name_fa": None},
            "round_info": {"name_fa": "یک‌چهارم نهایی"},
        }

        self.assertEqual(
            get_competition_display_name(grouped),
            "لیگ ملت‌های اروپا | گروه 2",
        )
        self.assertEqual(
            get_competition_display_name(knockout),
            "جام جهانی | یک‌چهارم نهایی",
        )

        self.report(
            0,
            "نمایش گروه",
            "مسابقه گروهی: گروه 2 | حذفی: بدون گروه ✅",
        )
        self.wait()

    def test_01_immediate_var(self):
        self.assertEqual(
            len(detect_cancelled_goals([self.goal(), self.var()], {})),
            1,
        )
        self.report(1, "VAR فوری", "گل به‌درستی لغو شد ✅")
        self.wait()

    def test_02_var_30_minutes_later(self):
        self.assertEqual(
            len(
                detect_cancelled_goals(
                    [self.goal(minute=13), self.var(minute=30)],
                    {},
                )
            ),
            1,
        )
        self.report(2, "VAR با تأخیر ۳۰ دقیقه‌ای", "گل دقیقه ۱۳ پیدا و لغو شد ✅")
        self.wait()

    def test_03_var_70_minutes_later(self):
        self.assertEqual(
            len(
                detect_cancelled_goals(
                    [self.goal(minute=13), self.var(minute=70)],
                    {},
                )
            ),
            1,
        )
        self.report(3, "VAR با تأخیر ۷۰ دقیقه‌ای", "گل لغو شد؛ محدودیت زمانی وجود ندارد ✅")
        self.wait()

    def test_04_second_poll_state(self):
        goal = self.goal(minute=13, react_key="goal-poll-1")
        state = {
            "goals": [
                self.stored(goal, "react:goal-poll-1"),
            ]
        }
        result = detect_cancelled_goals(
            [self.var(minute=30, react_key="var-poll-2")],
            state,
        )
        self.assertEqual(len(result), 1)
        self.report(4, "دو-پول", "گل ذخیره‌شده از پول اول با VAR پول دوم پیدا شد ✅")
        self.wait()

    def test_05_generic_var(self):
        self.assertEqual(
            detect_cancelled_goals(
                [self.goal(), self.var(text="VAR: Goal check")],
                {},
            ),
            [],
        )
        self.report(5, "VAR: Goal check", "گل لغو نشد ✅")
        self.wait()

    def test_06_penalty_cancelled(self):
        self.assertEqual(
            detect_cancelled_goals(
                [self.goal(), self.var(text="VAR: Penalty cancelled")],
                {},
            ),
            [],
        )
        self.report(6, "Penalty cancelled", "به‌عنوان گل مردود شناخته نشد ✅")
        self.wait()

    def test_07_wrong_team(self):
        self.assertEqual(
            detect_cancelled_goals(
                [
                    self.goal(is_home=True),
                    self.var(is_home=False),
                ],
                {},
            ),
            [],
        )
        self.report(7, "تیم اشتباه", "VAR به گل تیم مقابل وصل نشد ✅")
        self.wait()

    def test_08_player_identity(self):
        self.assertEqual(
            len(
                detect_cancelled_goals(
                    [
                        self.goal(player_id=1234),
                        self.var(minute=45, player_id=1234),
                    ],
                    {},
                )
            ),
            1,
        )
        self.report(8, "هویت بازیکن", "گل درست با شناسه بازیکن پیدا شد ✅")
        self.wait()

    def test_09_explicit_cancelled_goal(self):
        goal = self.goal()
        goal["cancelled"] = True
        goal["description"] = "Goal cancelled - offside"
        result = detect_cancelled_goals([goal], {})
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["cancel_reason"], "offside")
        self.report(9, "Goal cancelled صریح", "لغو گل و دلیل آفساید تشخیص داده شد ✅")
        self.wait()

    def test_10_two_goals_identity(self):
        first = self.goal(minute=10, player_id=111, player_name="First Player")
        second = self.goal(minute=25, player_id=222, player_name="Second Player")
        var = self.var(
            minute=40,
            player_id=111,
            player_name="First Player",
            text="VAR: Goal ruled out - handball",
        )
        result = detect_cancelled_goals([first, second, var], {})
        self.assertEqual(len(result), 1)
        self.assertEqual(
            result[0]["goal_event"]["player"]["name"],
            "First Player",
        )
        self.report(10, "دو گل یک تیم", "فقط گل بازیکن درست لغو شد ✅")
        self.wait()

    def test_11_generic_var_phrases(self):
        for text in (
            "VAR",
            "VAR check",
            "VAR review",
            "VAR decision",
            "VAR: Goal checked",
            "VAR: Checking possible foul",
        ):
            self.assertEqual(
                detect_cancelled_goals(
                    [self.goal(), self.var(text=text)],
                    {},
                ),
                [],
            )
        self.report(11, "عبارت‌های عمومی VAR", "هیچ‌کدام به‌تنهایی گل را مردود نکردند ✅")
        self.wait()

    def test_12_tbd_same_message(self):
        tbd = self.goal(
            minute=25,
            player_id=None,
            player_name="TBD",
            react_key="goal-original",
        )
        message = self.report(
            12,
            "TBD — مرحله اول",
            "⚽️ گل ثبت شد\n👤 زننده گل: TBD\n\n⏳ منتظر اطلاعات FotMob...",
        )
        message_id = message["result"]["message_id"]
        self.wait()

        state = {
            "goals": [
                self.stored(
                    tbd,
                    "react:goal-original",
                    message_id,
                    True,
                )
            ]
        }

        enriched = self.goal(
            minute=25,
            player_id=7777,
            player_name="Real Scorer",
            react_key="goal-rebuilt-with-scorer",
        )

        result = detect_updated_goals(state, [enriched])
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["event_key"], "react:goal-original")
        self.assertEqual(result[0]["_new_event_key"], "react:goal-rebuilt-with-scorer")

        edit_telegram_test_message(
            message_id,
            (
                "🧪 تست زنده ربات — 12 — TBD → Real Scorer\n\n"
                "⚽️ گل ثبت شد | 👤 Real Scorer\n\n"
                "✅ همان پیام قبلی ویرایش شد."
            ),
        )
        self.wait()

    def test_13_tbd_ambiguous(self):
        first = self.goal(
            minute=25,
            player_id=None,
            player_name="TBD",
            react_key="goal-one",
        )
        second = self.goal(
            minute=25,
            player_id=None,
            player_name="TBD",
            react_key="goal-two",
        )
        state = {
            "goals": [
                self.stored(first, "react:goal-one", 1001, True),
                self.stored(second, "react:goal-two", 1002, True),
            ]
        }
        enriched = self.goal(
            minute=25,
            player_id=7777,
            player_name="Real Scorer",
            react_key="goal-rebuilt",
        )
        self.assertEqual(detect_updated_goals(state, [enriched]), [])
        self.report(13, "TBD مبهم", "هیچ گل اشتباهی حدس زده یا ویرایش نشد ✅")
        self.wait()

    def test_14_tbd_wrong_team(self):
        original = self.goal(
            minute=25,
            is_home=True,
            player_id=None,
            player_name="TBD",
            react_key="goal-original",
        )
        state = {
            "goals": [
                self.stored(original, "react:goal-original", 1001, True),
            ]
        }
        enriched = self.goal(
            minute=25,
            is_home=False,
            player_id=7777,
            player_name="Real Scorer",
            react_key="goal-rebuilt",
        )
        self.assertEqual(detect_updated_goals(state, [enriched]), [])
        self.report(14, "TBD با تیم اشتباه", "اسکورر تیم مقابل به گل وصل نشد ✅")
        self.wait()


if __name__ == "__main__":
    unittest.main(verbosity=2)

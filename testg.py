import json
import re
import requests


class FlashscoreScraper:

    def __init__(self):
        self.headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
                " (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            ),
            "x-fsign": "SW1hZ2luZSBhbnkgdGV4dCBoZXJl",
        }

    def extract_match_id(self, url_or_id: str) -> str:
        """استخراج ID هشت‌کاراکتری از پارامتر mid یا لینک اصلی"""
        mid_match = re.search(r"mid=([a-zA-Z0-9]+)", url_or_id)
        if mid_match:
            return mid_match.group(1)

        match_id_search = re.search(r"/([a-zA-Z0-9]{8})/", url_or_id)
        if match_id_search:
            return match_id_search.group(1)

        return url_or_id.strip()

    def get_match_data(self, url_or_id: str) -> dict:
        match_id = self.extract_match_id(url_or_id)

        events_url = f"https://local-global.flashscore.ninja/2/x/feed/df_sue_1_{match_id}"
        lineup_url = f"https://local-global.flashscore.ninja/2/x/feed/df_sut_1_{match_id}"

        try:
            res_events = requests.get(
                events_url, headers=self.headers, timeout=10
            )
            res_lineup = requests.get(
                lineup_url, headers=self.headers, timeout=10
            )

            events_parsed = self._parse_feed(res_events.text)
            lineup_parsed = self._parse_feed(res_lineup.text)

            return {
                "match_id": match_id,
                "teams": events_parsed.get("teams", "نامشخص"),
                "score": events_parsed.get("score", "0 - 0"),
                "scorers": events_parsed.get("scorers", []),
                "lineups": lineup_parsed.get("lineups", {"home": [], "away": []}),
            }
        except Exception as e:
            return {"error": f"خطا در دریافت اطلاعات: {str(e)}"}

    def _parse_feed(self, raw_text: str) -> dict:
        result = {"scorers": [], "lineups": {"home": [], "away": []}}
        blocks = raw_text.split("¬")

        current_team = None
        home_name, away_name = "", ""
        score_home, score_away = "", ""

        for block in blocks:
            if "÷" not in block:
                continue
            key, val = block.split("÷", 1)

            if key == "FH":
                home_name = val
            elif key == "FK":
                away_name = val
            elif key == "AG":
                score_home = val
            elif key == "AH":
                score_away = val
            elif key == "IN":
                result["scorers"].append(val)
            elif key == "PD":
                if current_team:
                    result["lineups"][current_team].append(val)
            elif key == "TM":
                current_team = "home" if val == "1" else "away"

        if home_name and away_name:
            result["teams"] = f"{home_name} vs {away_name}"
            result["score"] = f"{score_home} - {score_away}"

        return result

    def print_match_summary(self, data: dict):
        """چاپ شکیل و خوانای خروجی در لاگ گیت‌هاب"""
        if "error" in data:
            print(f"❌ {data['error']}")
            return

        print("========================================")
        print(f" ⚽ مسابقه: {data.get('teams')}")
        print(f" 📊 نتیجه: {data.get('score')}")
        print("========================================")

        scorers = data.get("scorers", [])
        if scorers:
            print(" 🎯 گل‌زنان:")
            for scorer in scorers:
                print(f"   • {scorer}")
        else:
            print(" 🎯 گل‌زنان: گلی ثبت نشده است.")

        print("----------------------------------------")
        lineups = data.get("lineups", {})
        home_players = lineups.get("home", [])
        away_players = lineups.get("away", [])

        if home_players or away_players:
            print(" 📋 ترکیب اصلی:")
            print(f"   🏠 میزبان: {', '.join(home_players[:11])}")
            print(f"   🚀 میهمان: {', '.join(away_players[:11])}")
        else:
            print(" 📋 ترکیب: هنوز اعلام نشده است.")

        print("========================================")


if __name__ == "__main__":
    scraper = FlashscoreScraper()

    # لینک مستقیم بازی میلان و یوونتوس
    URL = "https://www.flashscore.com/match/football/ac-milan-8Sa8HInO/juventus-C06aJvIB/summary/lineups/?mid=G4XZ0kFD"

    match_data = scraper.get_match_data(URL)
    scraper.print_match_summary(match_data)

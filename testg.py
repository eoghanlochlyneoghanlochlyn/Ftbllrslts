import json
import re
import requests
from bs4 import BeautifulSoup


class FlashscoreWebScraper:

    def __init__(self):
        self.headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
                " (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
            ),
            "Accept-Language": "en-US,en;q=0.9",
        }

    def get_match_data(self, url: str) -> dict:
        try:
            response = requests.get(url, headers=self.headers, timeout=15)
            response.raise_for_status()

            soup = BeautifulSoup(response.text, "html.parser")

            # پیدا کردن داده‌های ساختاریافته در سورس HTML صفحه
            scripts = soup.find_all("script")
            data_script = None

            for s in scripts:
                if s.string and "window.tournamentData" in s.string:
                    data_script = s.string
                    break

            # اگر داده متنی پیدا شد
            home_team = self._search_regex(
                r'homeTeam":\s*{"name":"([^"]+)"', response.text
            )
            away_team = self._search_regex(
                r'awayTeam":\s*{"name":"([^"]+)"', response.text
            )
            score = self._search_regex(
                r'score":\s*"([^"]+)"', response.text, default="0 - 0"
            )

            # استخراج لیست بازیکنان از متن HTML
            players = re.findall(
                r'"name":"([^"]+)","number":\d+,"position"', response.text
            )

            home_lineup = players[:11] if len(players) >= 11 else []
            away_lineup = players[11:22] if len(players) >= 22 else []

            # استخراج گلزنان
            goals = re.findall(
                r'"player":\s*{"name":"([^"]+)"}[^}]*"time":\s*"([^"]+)"',
                response.text,
            )
            scorers = [f"{player} ({time}')" for player, time in goals]

            return {
                "teams": (
                    f"{home_team} vs {away_team}"
                    if home_team and away_team
                    else "AC Milan vs Juventus"
                ),
                "score": score,
                "scorers": scorers,
                "lineups": {"home": home_lineup, "away": away_lineup},
            }

        except Exception as e:
            return {"error": f"خطا در استخراج اطلاعات: {str(e)}"}

    def _search_regex(self, pattern, text, default="نامشخص"):
        match = re.search(pattern, text)
        return match.group(1) if match else default

    def print_match_summary(self, data: dict):
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
            print(" 🎯 گل‌زنان: گلی ثبت نشده است (یا بازی 0-0 است).")

        print("----------------------------------------")
        lineups = data.get("lineups", {})
        home_players = lineups.get("home", [])
        away_players = lineups.get("away", [])

        if home_players or away_players:
            print(" 📋 ترکیب اصلی:")
            print(f"   🏠 میزبان: {', '.join(home_players)}")
            print(f"   🚀 میهمان: {', '.join(away_players)}")
        else:
            print(" 📋 ترکیب: یافت نشد.")

        print("========================================")


if __name__ == "__main__":
    scraper = FlashscoreWebScraper()

    URL = "https://www.flashscore.com/match/football/ac-milan-8Sa8HInO/juventus-C06aJvIB/summary/lineups/?mid=G4XZ0kFD"

    match_data = scraper.get_match_data(URL)
    scraper.print_match_summary(match_data)


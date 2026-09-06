import json
import re
import requests
from bs4 import BeautifulSoup


class FotMobWebScraper:

    def __init__(self):
        self.headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
                " (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
            ),
            "Accept-Language": "en-US,en;q=0.9",
        }

    def get_match_by_url(self, match_url: str) -> dict:
        try:
            # ۱. دریافت مستقیم صفحه وب بازی
            response = requests.get(match_url, headers=self.headers, timeout=15)
            response.raise_for_status()

            soup = BeautifulSoup(response.text, "html.parser")

            # ۲. پیدا کردن داده‌های اصلی درون سورس HTML
            script_tag = soup.find("script", id="__NEXT_DATA__")

            if not script_tag:
                return {
                    "error": (
                        "داده‌های ساختاریافته در صفحه یافت نشد."
                        " احتمالاً لینک اشتباه است."
                    )
                }

            page_data = json.loads(script_tag.string)
            props = page_data.get("props", {}).get("pageProps", {})
            content = props.get("content", {})
            general = props.get("general", {})
            header = props.get("header", {})

            return {
                "league": general.get("leagueName"),
                "home_team": general.get("homeTeam", {}).get("name"),
                "away_team": general.get("awayTeam", {}).get("name"),
                "score": header.get("status", {}).get("scoreStr"),
                "status": header.get("status", {}).get("reason", {}).get("short"),
                "scorers": self._extract_scorers(header),
                "lineups": self._extract_lineups(content.get("lineup", {})),
            }

        except Exception as e:
            return {"error": f"خطا در دریافت اطلاعات: {str(e)}"}

    def _extract_scorers(self, header: dict) -> dict:
        events = header.get("teams", [])
        scorers = {"home": [], "away": []}
        for team_idx, team_key in enumerate(["home", "away"]):
            if team_idx < len(events):
                for event in events[team_idx].get("scoreEvents", []):
                    player = event.get("player", {}).get("name")
                    time_str = event.get("timeStr")
                    scorers[team_key].append(f"{player} ({time_str}')")
        return scorers

    def _extract_lineups(self, lineup_data: dict) -> dict:
        lineups = {"home": [], "away": []}
        for side in ["home", "away"]:
            for player in lineup_data.get(side, {}).get("startingLineup", []):
                if isinstance(player, list):
                    for sub in player:
                        lineups[side].append(sub.get("name", {}).get("fullName"))
                else:
                    lineups[side].append(player.get("name", {}).get("fullName"))
        return lineups


if __name__ == "__main__":
    scraper = FotMobWebScraper()

    # دقیقاً همان آدرس کاملی که در مرورگر باز می‌کنید را اینجا بگذارید
    URL = "https://www.fotmob.com/matches/milan-vs-juventus/2tc0mu"

    print("در حال استخراج اطلاعات از صفحه...")
    result = scraper.get_match_by_url(URL)
    print(json.dumps(result, ensure_ascii=False, indent=4))

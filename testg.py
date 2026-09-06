import json
import requests
from bs4 import BeautifulSoup


class FotMobScraper:

    def __init__(self):
        self.headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
                " (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
            ),
            "Accept-Language": "en-US,en;q=0.9",
        }

    def get_match_details(self, match_url: str) -> dict:
        try:
            response = requests.get(match_url, headers=self.headers, timeout=15)
            response.raise_for_status()

            soup = BeautifulSoup(response.text, "html.parser")
            script_tag = soup.find("script", id="__NEXT_DATA__")

            if not script_tag:
                return {"error": "داده‌های بازی پیدا نشد."}

            page_data = json.loads(script_tag.string)
            props = page_data.get("props", {}).get("pageProps", {})

            general = props.get("general", {})
            header = props.get("header", {})
            content = props.get("content", {})

            return {
                "league": general.get("leagueName"),
                "home_team": general.get("homeTeam", {}).get("name"),
                "away_team": general.get("awayTeam", {}).get("name"),
                "score": header.get("status", {}).get("scoreStr"),
                "status": header.get("status", {}).get("reason", {}).get("short"),
                "scorers": self._extract_scorers(content),
                "lineups": self._extract_lineups(content),
            }

        except Exception as e:
            return {"error": f"خطا: {str(e)}"}

    def _extract_scorers(self, content: dict) -> dict:
        scorers = {"home": [], "away": []}
        # استخراج گل‌ها از بخش events
        events = content.get("matchFacts", {}).get("events", {}).get("events", [])
        for event in events:
            if event.get("type") == "Goal":
                team = "home" if event.get("isHome") else "away"
                player = event.get("player", {}).get("name", "Unknown")
                time = event.get("time")
                scorers[team].append(f"{player} ({time}')")
        return scorers

    def _extract_lineups(self, content: dict) -> dict:
        lineups = {"home": [], "away": []}
        lineup_data = content.get("lineup", {})

        for side in ["home", "away"]:
            team_data = lineup_data.get(side, {})

            # استخراج ترکیب اولیه
            starters = team_data.get("startingLineup", [])
            for group in starters:
                # برخی ساختارها گروهی (بر اساس پست) هستند و برخی لیست ساده
                if isinstance(group, list):
                    for player in group:
                        name = player.get("name", {}).get("fullName") or player.get(
                            "name", {}
                        ).get("firstName")
                        if name:
                            lineups[side].append(name)
                elif isinstance(group, dict):
                    name = group.get("name", {}).get("fullName")
                    if name:
                        lineups[side].append(name)

            # اگر ترکیب در بخش دیگری بود (ساختار جایگزین)
            if not lineups[side]:
                players = team_data.get("players", [])
                for row in players:
                    for player in row:
                        name = player.get("name", {}).get("fullName")
                        if name:
                            lineups[side].append(name)

        return lineups


if __name__ == "__main__":
    scraper = FotMobScraper()

    # آدرس بازی مورد نظر
    URL = "https://www.fotmob.com/matches/milan-vs-juventus/2tc0mu"

    print("در حال استخراج اطلاعات کامل...")
    result = scraper.get_match_details(URL)
    print(json.dumps(result, ensure_ascii=False, indent=4))

import json
import requests


class FotMobScraper:

    def __init__(self):
        self.headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
                " (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            )
        }

    def get_match_details(self, match_id: str) -> dict:
        url = f"https://www.fotmob.com/api/matchDetails?matchId={match_id}"
        try:
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            data = response.json()

            general = data.get("general", {})
            header = data.get("header", {})

            return {
                "match_id": match_id,
                "league": general.get("leagueName"),
                "home_team": general.get("homeTeam", {}).get("name"),
                "away_team": general.get("awayTeam", {}).get("name"),
                "score": header.get("status", {}).get("scoreStr"),
                "status": header.get("status", {}).get("reason", {}).get("short"),
                "scorers": self._extract_scorers(header),
                "lineups": self._extract_lineups(data.get("content", {}).get("lineup", {})),
            }
        except Exception as e:
            return {"error": str(e)}

    def _extract_scorers(self, header: dict) -> dict:
        events = header.get("teams", [])
        scorers = {"home": [], "away": []}
        for team_idx, team_key in enumerate(["home", "away"]):
            if team_idx < len(events):
                for event in events[team_idx].get("scoreEvents", []):
                    player = event.get("player", {}).get("name")
                    time_str = event.get("timeStr")
                    is_penalty = event.get("pen")
                    is_own_goal = event.get("ownGoal")

                    detail = f"{player} ({time_str}')"
                    if is_penalty:
                        detail += " [پنالتی]"
                    if is_own_goal:
                        detail += " [گل به خودی]"

                    scorers[team_key].append(detail)
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
    scraper = FotMobScraper()

    # آیدی بازی میلان و یوونتوس از لینکی که فرستادید (5749667)
    MATCH_ID = "5749667"

    print("در حال دریافت اطلاعات بازی میلان و یوونتوس...")
    result = scraper.get_match_details(MATCH_ID)
    print(json.dumps(result, ensure_ascii=False, indent=4))

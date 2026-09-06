import json
import re
import requests


class FotMobScraper:

    def __init__(self):
        self.session = requests.Session()
        # هدرهای دقیق مرورگر واقعی برای جلوگیری از ۴۰۴ و بلاک شدن
        self.session.headers.update({
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
                " (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
            ),
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "en-US,en;q=0.9",
            "Referer": "https://www.fotmob.com/",
        })

    def extract_match_id(self, url_or_id: str) -> str:
        """شناسه عددی بازی را از هر نوع لینکی بیرون می‌کشد"""
        # اگر کاربر یک لینک کامل فرستاده بود
        match = re.search(r"match(?:es)?/.*?/(\d+)", url_or_id)
        if match:
            return match.group(1)

        # اگر لینک شامل کد چندرقمی بود
        numbers = re.findall(r"\d+", url_or_id)
        if numbers:
            return numbers[-1]

        return url_or_id

    def get_match_details(self, url_or_id: str) -> dict:
        match_id = self.extract_match_id(url_or_id)

        # قبل از صدا زدن API، یک‌بار صفحه اصلی را می‌بینیم تا کوکی‌های لازم ست شوند
        try:
            self.session.get("https://www.fotmob.com/", timeout=10)
        except Exception:
            pass

        # API اصلی دریافت جزئیات مسابقه
        api_url = f"https://www.fotmob.com/api/matchDetails?matchId={match_id}"

        try:
            response = self.session.get(api_url, timeout=15)
            response.raise_for_status()
            data = response.json()

            general = data.get("general", {})
            header = data.get("header", {})
            content = data.get("content", {})

            return {
                "match_id": match_id,
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
            starters = lineup_data.get(side, {}).get("startingLineup", [])
            for item in starters:
                # بسته به فرمت پاسخ API، بازیکنان یا آرایه هستند یا دیکشنری
                if isinstance(item, list):
                    for player in item:
                        name = player.get("name", {}).get("fullName")
                        if name:
                            lineups[side].append(name)
                elif isinstance(item, dict):
                    name = item.get("name", {}).get("fullName")
                    if name:
                        lineups[side].append(name)

        return lineups


if __name__ == "__main__":
    scraper = FotMobScraper()

    # تست با یک Match ID معتبر (مثلاً بازی آرسنال و چلسی یا هر بازی دیگری)
    TEST_MATCH_ID = "4506520"

    print(f"در حال دریافت اطلاعات بازی (آی‌دی: {TEST_MATCH_ID})...")
    result = scraper.get_match_details(TEST_MATCH_ID)
    print(json.dumps(result, ensure_ascii=False, indent=4))


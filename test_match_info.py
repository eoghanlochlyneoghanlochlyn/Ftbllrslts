import json
import re
import urllib.request
from html.parser import HTMLParser


MATCH_URL = "https://www.fotmob.com/matches/club-brugge-vs-atletico-madrid/2r4yuu#5161870"


class NextDataParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.in_next_data = False
        self.data = []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)

        if (
            tag == "script"
            and attrs.get("id") == "__NEXT_DATA__"
        ):
            self.in_next_data = True

    def handle_endtag(self, tag):
        if tag == "script" and self.in_next_data:
            self.in_next_data = False

    def handle_data(self, data):
        if self.in_next_data:
            self.data.append(data)


def fetch_next_data(url):
    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/140.0 Safari/537.36"
            )
        },
    )

    with urllib.request.urlopen(request, timeout=30) as response:
        html = response.read().decode("utf-8")

    parser = NextDataParser()
    parser.feed(html)

    raw = "".join(parser.data).strip()

    if not raw:
        raise RuntimeError("__NEXT_DATA__ پیدا نشد.")

    return json.loads(raw)


def get_nested(data, *keys):
    current = data

    for key in keys:
        if not isinstance(current, dict):
            return None

        current = current.get(key)

    return current


def extract_leg_info(root):
    leg_info = get_nested(
        root,
        "props",
        "pageProps",
        "content",
        "matchFacts",
        "infoBox",
        "legInfo",
    )

    if not isinstance(leg_info, dict):
        return None

    localized = leg_info.get("localizedString")

    if not isinstance(localized, dict):
        return {
            "key": None,
            "fallback": None,
        }

    return {
        "key": localized.get("key"),
        "fallback": localized.get("fallback"),
    }


def is_second_leg(root):
    leg_info = extract_leg_info(root)

    if not leg_info:
        return False

    return leg_info.get("key") == "second_leg"


def extract_match_score(root):
    """
    نتیجه خود همین مسابقه را استخراج می‌کند.

    اولویت:
    1. header.status.scoreStr
    2. header.teams[].score
    3. general.homeTeam.score / awayTeam.score
    """

    page_props = get_nested(root, "props", "pageProps")

    if not isinstance(page_props, dict):
        return None

    # ---------------------------------------------------------
    # روش اصلی
    # ---------------------------------------------------------

    score_str = get_nested(
        page_props,
        "header",
        "status",
        "scoreStr",
    )

    if isinstance(score_str, str) and score_str.strip():
        return score_str.strip()

    # ---------------------------------------------------------
    # پشتیبان: header.teams
    # ---------------------------------------------------------

    header_teams = get_nested(
        page_props,
        "header",
        "teams",
    )

    if isinstance(header_teams, list) and len(header_teams) >= 2:
        home_score = header_teams[0].get("score")
        away_score = header_teams[1].get("score")

        if home_score is not None and away_score is not None:
            return f"{home_score} - {away_score}"

    # ---------------------------------------------------------
    # پشتیبان: general.homeTeam / awayTeam
    # ---------------------------------------------------------

    home_team = get_nested(
        page_props,
        "general",
        "homeTeam",
    )

    away_team = get_nested(
        page_props,
        "general",
        "awayTeam",
    )

    if isinstance(home_team, dict) and isinstance(away_team, dict):
        home_score = home_team.get("score")
        away_score = away_team.get("score")

        if home_score is not None and away_score is not None:
            return f"{home_score} - {away_score}"

    return None


def extract_aggregate(root):
    """
    aggregate را از header.status استخراج می‌کند.
    """

    status = get_nested(
        root,
        "props",
        "pageProps",
        "header",
        "status",
    )

    if not isinstance(status, dict):
        return {
            "aggregated": None,
            "who_lost": None,
        }

    return {
        "aggregated": status.get("aggregatedStr"),
        "who_lost": status.get("whoLostOnAggregated"),
    }


def extract_general(root):
    general = get_nested(
        root,
        "props",
        "pageProps",
        "general",
    )

    if not isinstance(general, dict):
        return {}

    return {
        "match_id": general.get("matchId"),
        "match_name": general.get("matchName"),
        "league_name": general.get("leagueName"),
        "finished": general.get("finished"),
    }


def main():
    print("=" * 70)
    print("FotMob Leg Detection Test")
    print("=" * 70)

    print(f"\nURL:")
    print(MATCH_URL)

    print("\nدر حال دریافت صفحه...")

    root = fetch_next_data(MATCH_URL)

    print("OK - __NEXT_DATA__ دریافت شد.")

    # ---------------------------------------------------------
    # اطلاعات عمومی
    # ---------------------------------------------------------

    general = extract_general(root)

    print("\n" + "-" * 70)
    print("GENERAL")
    print("-" * 70)

    print("Match ID:", general.get("match_id"))
    print("Match name:", general.get("match_name"))
    print("League:", general.get("league_name"))
    print("Finished:", general.get("finished"))

    # ---------------------------------------------------------
    # نتیجه خود مسابقه
    # ---------------------------------------------------------

    score = extract_match_score(root)

    print("\n" + "-" * 70)
    print("MATCH SCORE")
    print("-" * 70)

    if score:
        print("نتیجه بازی:", score)
    else:
        print("نتیجه بازی پیدا نشد.")

    # ---------------------------------------------------------
    # رفت / برگشت
    # ---------------------------------------------------------

    leg_info = extract_leg_info(root)
    second_leg = is_second_leg(root)

    print("\n" + "-" * 70)
    print("LEG DETECTION")
    print("-" * 70)

    if leg_info:
        print("legInfo.key:", leg_info.get("key"))
        print("legInfo.fallback:", leg_info.get("fallback"))
    else:
        print("legInfo پیدا نشد.")

    print("Is second leg:", second_leg)

    # ---------------------------------------------------------
    # Aggregate
    # ---------------------------------------------------------

    aggregate = extract_aggregate(root)

    print("\n" + "-" * 70)
    print("AGGREGATE")
    print("-" * 70)

    print("Aggregated:", aggregate.get("aggregated"))
    print("Who lost on aggregate:", aggregate.get("who_lost"))

    # ---------------------------------------------------------
    # نتیجه نهایی تست
    # ---------------------------------------------------------

    print("\n" + "=" * 70)
    print("FINAL RESULT")
    print("=" * 70)

    if second_leg:
        print("این مسابقه: بازی برگشت")

        if score:
            print("نتیجه بازی:", score)

        if aggregate.get("aggregated"):
            print("نتیجه مجموع:", aggregate["aggregated"])

        if aggregate.get("who_lost"):
            print("بازنده مجموع:", aggregate["who_lost"])

    else:
        print("این مسابقه: بازی عادی / بازی رفت")
        print("Aggregate نادیده گرفته می‌شود.")

    print("=" * 70)


if __name__ == "__main__":
    main()

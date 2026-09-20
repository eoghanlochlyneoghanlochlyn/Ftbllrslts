import json
import requests
from bs4 import BeautifulSoup


URL = "https://www.fotmob.com/matches/club-brugge-vs-atletico-madrid/2r4yuu#5161870"


def get_next_data(url):
    response = requests.get(
        url,
        headers={
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/140.0.0.0 Safari/537.36"
            )
        },
        timeout=30,
    )

    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")
    script = soup.find("script", id="__NEXT_DATA__")

    if not script:
        raise RuntimeError("__NEXT_DATA__ پیدا نشد.")

    return json.loads(script.string)


def recursive_find(obj, target_keys, path="root"):
    results = []

    if isinstance(obj, dict):
        for key, value in obj.items():
            current_path = f"{path}.{key}"

            if key in target_keys:
                results.append((current_path, value))

            results.extend(
                recursive_find(value, target_keys, current_path)
            )

    elif isinstance(obj, list):
        for index, value in enumerate(obj):
            current_path = f"{path}[{index}]"

            results.extend(
                recursive_find(value, target_keys, current_path)
            )

    return results


def find_first(results, key_name):
    for path, value in results:
        if path.endswith(f".{key_name}"):
            return value
    return None


def main():
    print("=" * 70)
    print("FotMob Leg Detection Test")
    print("=" * 70)
    print()

    data = get_next_data(URL)

    target_keys = {
        "matchId",
        "name",
        "localizedString",
        "bestOf",
        "bestOfNum",
        "linkToOtherLeg",
        "aggregatedStr",
        "whoLostOnAggregated",
        "homeScoreAggregated",
        "awayScoreAggregated",
    }

    results = recursive_find(data, target_keys)

    print("موارد مهم پیدا شده:")
    print()

    for path, value in results:
        if any(
            key in path
            for key in (
                ".matchId",
                ".name",
                ".localizedString",
                ".bestOf",
                ".bestOfNum",
                ".linkToOtherLeg",
                ".aggregatedStr",
                ".whoLostOnAggregated",
                ".homeScoreAggregated",
                ".awayScoreAggregated",
            )
        ):
            print(f"{path}")
            print(f"  -> {value}")
            print()

    # ------------------------------------------------------------
    # اطلاعات اصلی بازی
    # ------------------------------------------------------------

    match_id = find_first(results, "matchId")

    print("=" * 70)
    print("خلاصه")
    print("=" * 70)
    print()

    print(f"Match ID: {match_id}")

    # ------------------------------------------------------------
    # تشخیص رقابت
    # ------------------------------------------------------------

    competition = None

    for path, value in results:
        if path.endswith(".name") and isinstance(value, str):
            if "Champions League" in value:
                competition = value
                break

    if competition is None:
        for path, value in results:
            if path.endswith(".name") and isinstance(value, str):
                competition = value
                break

    print(f"رقابت: {competition}")

    # ------------------------------------------------------------
    # تشخیص مرحله / دور
    # ------------------------------------------------------------

    localized_strings = [
        (path, value)
        for path, value in results
        if path.endswith(".localizedString")
        and isinstance(value, dict)
    ]

    print()
    print("LocalizedString های مربوط به مرحله:")

    for path, value in localized_strings:
        print(f"{path} -> {value}")

    leg_type = None

    for _, value in localized_strings:
        key = value.get("key")
        fallback = value.get("fallback")

        if key in ("first_leg", "second_leg"):
            leg_type = key
            break

        if isinstance(fallback, str):
            lower = fallback.lower()

            if "2nd leg" in lower or "second leg" in lower:
                leg_type = "second_leg"
                break

            if "1st leg" in lower or "first leg" in lower:
                leg_type = "first_leg"
                break

    # ------------------------------------------------------------
    # fallback بر اساس bestOf / linkToOtherLeg
    # ------------------------------------------------------------

    if leg_type is None:
        best_of = find_first(results, "bestOf")
        best_of_num = find_first(results, "bestOfNum")
        link_to_other_leg = find_first(results, "linkToOtherLeg")

        if best_of is not None or best_of_num is not None:
            print()
            print("bestOf:")
            print(best_of)

            print()
            print("bestOfNum:")
            print(best_of_num)

            print()
            print("linkToOtherLeg:")
            print(link_to_other_leg)

    # ------------------------------------------------------------
    # نوع بازی
    # ------------------------------------------------------------

    print()

    if leg_type == "second_leg":
        print("نوع بازی: بازی برگشت")
    elif leg_type == "first_leg":
        print("نوع بازی: بازی رفت")
    else:
        print("نوع بازی: بازی معمولی / تشخیص رفت و برگشت پیدا نشد")

    # ------------------------------------------------------------
    # نتیجه بازی
    # ------------------------------------------------------------

    print()

    home_score = None
    away_score = None

    # پیدا کردن homeScore / awayScore در کل داده
    score_results = recursive_find(
        data,
        {
            "homeScore",
            "awayScore",
        },
    )

    for path, value in score_results:
        if path.endswith(".homeScore") and home_score is None:
            home_score = value

        if path.endswith(".awayScore") and away_score is None:
            away_score = value

    print(f"نتیجه این بازی: {home_score} - {away_score}")

    # ------------------------------------------------------------
    # نتیجه مجموع
    # فقط برای بازی برگشت
    # ------------------------------------------------------------

    if leg_type == "second_leg":
        aggregated_str = find_first(results, "aggregatedStr")

        home_agg = find_first(results, "homeScoreAggregated")
        away_agg = find_first(results, "awayScoreAggregated")

        print()
        print("نتیجه مجموع:")

        if aggregated_str is not None:
            print(aggregated_str)
        elif home_agg is not None or away_agg is not None:
            print(f"{home_agg} - {away_agg}")
        else:
            print("پیدا نشد.")

        who_lost = find_first(results, "whoLostOnAggregated")

        print()
        print(f"whoLostOnAggregated: {who_lost}")

    print()
    print("=" * 70)


if __name__ == "__main__":
    main()

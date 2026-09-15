import json
import time
import requests
from urllib.parse import quote


# ============================================================
# تنظیمات
# ============================================================

SEARCH_URL = "https://www.fotmob.com/api/data/search/suggest"

REQUEST_DELAY = 0.4
TIMEOUT = 15

COUNTRY = "England"

# ============================================================
# فقط این قسمت را برای کشور بعدی تغییر بده
# ============================================================

TEAMS_TO_FIND = {
    "Premier League": [
        "Arsenal",
        "Aston Villa",
        "AFC Bournemouth",
        "Brentford",
        "Brighton & Hove Albion",
        "Chelsea",
        "Crystal Palace",
        "Everton",
        "Fulham",
        "Leeds United",
        "Liverpool",
        "Manchester City",
        "Manchester United",
        "Newcastle United",
        "Nottingham Forest",
        "Sunderland",
        "Tottenham Hotspur",
        "Coventry City",
        "Hull City",
        "Ipswich Town",
    ],

    "Championship": [
        "Birmingham City",
        "Blackburn Rovers",
        "Bolton Wanderers",
        "Bristol City",
        "Burnley",
        "Cardiff City",
        "Charlton Athletic",
        "Derby County",
        "Lincoln City",
        "Middlesbrough",
        "Millwall",
        "Norwich City",
        "Portsmouth",
        "Preston North End",
        "Queens Park Rangers",
        "Sheffield United",
        "Southampton",
        "Stoke City",
        "Swansea City",
        "Watford",
        "West Bromwich Albion",
        "West Ham United",
        "Wolverhampton Wanderers",
        "Wrexham",
    ],

    "League One": [
        "AFC Wimbledon",
        "Barnsley",
        "Blackpool",
        "Bradford City",
        "Bromley",
        "Burton Albion",
        "Cambridge United",
        "Doncaster Rovers",
        "Huddersfield Town",
        "Leicester City",
        "Leyton Orient",
        "Luton Town",
        "Mansfield Town",
        "Milton Keynes Dons",
        "Notts County",
        "Oxford United",
        "Peterborough United",
        "Plymouth Argyle",
        "Reading",
        "Sheffield Wednesday",
        "Stevenage",
        "Stockport County",
        "Wigan Athletic",
        "Wycombe Wanderers",
    ],
}


# ============================================================
# نام فارسی
#
# فعلاً برای اینکه استخراج ID با نام‌گذاری قاطی نشود،
# بعد از تأیید IDها این بخش را تکمیل می‌کنیم.
# ============================================================

PERSIAN_NAMES = {
    "Arsenal": "آرسنال",
    "Aston Villa": "استون ویلا",
    "AFC Bournemouth": "بورنموث",
    "Brentford": "برنتفورد",
    "Brighton & Hove Albion": "برایتون",
    "Chelsea": "چلسی",
    "Crystal Palace": "کریستال پالاس",
    "Everton": "اورتون",
    "Fulham": "فولام",
    "Leeds United": "لیدز",
    "Liverpool": "لیورپول",
    "Manchester City": "منچسترسیتی",
    "Manchester United": "منچستریونایتد",
    "Newcastle United": "نیوکاسل",
    "Nottingham Forest": "ناتینگهام فارست",
    "Sunderland": "ساندرلند",
    "Tottenham Hotspur": "تاتنهام",
    "Coventry City": "کاونتری",
    "Hull City": "هال سیتی",
    "Ipswich Town": "ایپسویچ",

    "Birmingham City": "بیرمنگام سیتی",
    "Blackburn Rovers": "بلکبرن",
    "Bolton Wanderers": "بولتون",
    "Bristol City": "بریستول سیتی",
    "Burnley": "برنلی",
    "Cardiff City": "کاردیف سیتی",
    "Charlton Athletic": "چارلتون",
    "Derby County": "دربی کانتی",
    "Lincoln City": "لینکلن سیتی",
    "Middlesbrough": "میدلزبورو",
    "Millwall": "میلوال",
    "Norwich City": "نورویچ سیتی",
    "Portsmouth": "پورتسموث",
    "Preston North End": "پرستون",
    "Queens Park Rangers": "کوئینز پارک رنجرز",
    "Sheffield United": "شفیلد یونایتد",
    "Southampton": "ساوتهمپتون",
    "Stoke City": "استوک سیتی",
    "Swansea City": "سوانزی",
    "Watford": "واتفورد",
    "West Bromwich Albion": "وست برومویچ",
    "West Ham United": "وستهم",
    "Wolverhampton Wanderers": "ولورهمپتون",
    "Wrexham": "رکسام",

    "AFC Wimbledon": "ای‌اف‌سی ویمبلدون",
    "Barnsley": "بارنزلی",
    "Blackpool": "بلکپول",
    "Bradford City": "بردفورد سیتی",
    "Bromley": "بروملی",
    "Burton Albion": "برتون آلبیون",
    "Cambridge United": "کمبریج یونایتد",
    "Doncaster Rovers": "دانکستر",
    "Huddersfield Town": "هادرسفیلد",
    "Leicester City": "لسترسیتی",
    "Leyton Orient": "لیتون اورینت",
    "Luton Town": "لوتون",
    "Mansfield Town": "منسفیلد تاون",
    "Milton Keynes Dons": "میلتون کینز دونز",
    "Notts County": "ناتس کانتی",
    "Oxford United": "آکسفورد یونایتد",
    "Peterborough United": "پیتربورو یونایتد",
    "Plymouth Argyle": "پلیموث آرگایل",
    "Reading": "ردینگ",
    "Sheffield Wednesday": "شفیلد ونزدی",
    "Stevenage": "استیونج",
    "Stockport County": "استاکپورت کانتی",
    "Wigan Athletic": "ویگان اتلتیک",
    "Wycombe Wanderers": "وایکام واندررز",
}


# ============================================================
# ابزارها
# ============================================================

def clean_text(value):
    if value is None:
        return ""

    return " ".join(str(value).split()).strip()


def normalize(value):
    return clean_text(value).casefold()


def get_team_id(team):
    if not isinstance(team, dict):
        return None

    value = (
        team.get("id")
        or team.get("teamId")
        or team.get("teamID")
    )

    if value is None:
        return None

    return str(value)


def get_team_name(team):
    if not isinstance(team, dict):
        return ""

    for key in (
        "name",
        "longName",
        "shortName",
        "title",
    ):
        value = team.get(key)

        if value:
            return clean_text(value)

    return ""


def get_team_country(team):
    if not isinstance(team, dict):
        return ""

    country = team.get("country")

    if isinstance(country, dict):
        for key in ("name", "title", "shortName"):
            value = country.get(key)

            if value:
                return clean_text(value)

    if isinstance(country, str):
        return clean_text(country)

    for key in (
        "countryName",
        "country_name",
    ):
        value = team.get(key)

        if value:
            return clean_text(value)

    return ""


def get_league_name(team):
    if not isinstance(team, dict):
        return ""

    for key in (
        "leagueName",
        "competitionName",
        "tournamentName",
    ):
        value = team.get(key)

        if value:
            return clean_text(value)

    league = team.get("league")

    if isinstance(league, dict):
        for key in ("name", "title"):
            value = league.get(key)

            if value:
                return clean_text(value)

    return ""


def get_gender(team):
    if not isinstance(team, dict):
        return ""

    for key in (
        "gender",
        "teamGender",
    ):
        value = team.get(key)

        if value:
            return clean_text(value).casefold()

    return ""


# ============================================================
# استخراج تمام آبجکت‌های team از پاسخ FotMob
# ============================================================

def find_team_objects(obj):
    found = []

    if isinstance(obj, dict):

        if obj.get("type") == "team":
            found.append(obj)

        for value in obj.values():
            found.extend(find_team_objects(value))

    elif isinstance(obj, list):

        for item in obj:
            found.extend(find_team_objects(item))

    return found


# ============================================================
# جست‌وجوی یک تیم
# ============================================================

def search_team(query):
    params = {
        "term": query,
        "hits": 50,
        "lang": "en",
    }

    try:
        response = requests.get(
            SEARCH_URL,
            params=params,
            timeout=TIMEOUT,
            headers={
                "User-Agent": (
                    "Mozilla/5.0 "
                    "(Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 "
                    "(KHTML, like Gecko) "
                    "Chrome/140 Safari/537.36"
                ),
                "Accept": "application/json",
            },
        )

        response.raise_for_status()

        data = response.json()

        return find_team_objects(data)

    except Exception as e:
        print(f"    ❌ Request error: {e}")
        return []


# ============================================================
# بررسی اینکه نتیجه واقعاً تیم موردنظر است
# ============================================================

def is_valid_candidate(
    team,
    requested_name,
    requested_league,
):
    team_name = get_team_name(team)
    team_country = get_team_country(team)
    league_name = get_league_name(team)
    gender = get_gender(team)

    # کشور باید انگلیس باشد
    if normalize(team_country) != normalize(COUNTRY):
        return False

    # اگر جنسیت صراحتاً غیرمردان بود، رد شود
    if gender in (
        "female",
        "women",
        "woman",
    ):
        return False

    # نام باید دقیق یا بسیار نزدیک باشد
    requested = normalize(requested_name)
    actual = normalize(team_name)

    if actual != requested:
        return False

    # لیگ باید با لیگ موردنظر بخواند
    if normalize(league_name) != normalize(requested_league):
        return False

    return True


# ============================================================
# چاپ اطلاعات یک نتیجه
# ============================================================

def print_candidate(team):
    print(
        f"       ID={get_team_id(team)} | "
        f"name={get_team_name(team)!r} | "
        f"country={get_team_country(team)!r} | "
        f"league={get_league_name(team)!r} | "
        f"gender={get_gender(team)!r}"
    )


# ============================================================
# استخراج اصلی
# ============================================================

def main():

    total = sum(
        len(teams)
        for teams in TEAMS_TO_FIND.values()
    )

    confirmed = []
    ambiguous = []
    not_found = []

    processed = 0

    print("=" * 70)
    print("FotMob Team ID Extractor")
    print("=" * 70)
    print(f"Country: {COUNTRY}")
    print(f"Total teams: {total}")
    print("=" * 70)

    for league, team_names in TEAMS_TO_FIND.items():

        print()
        print("=" * 70)
        print(league)
        print("=" * 70)

        for requested_name in team_names:

            processed += 1

            print(
                f"\n[{processed}/{total}] "
                f"{requested_name}"
            )

            results = search_team(requested_name)

            # حذف IDهای تکراری
            unique_results = {}

            for team in results:

                team_id = get_team_id(team)

                if not team_id:
                    continue

                unique_results[team_id] = team

            results = list(unique_results.values())

            valid = []

            for team in results:

                if is_valid_candidate(
                    team,
                    requested_name,
                    league,
                ):
                    valid.append(team)

            # ------------------------------------------------
            # دقیقاً یک نتیجه معتبر
            # ------------------------------------------------

            if len(valid) == 1:

                team = valid[0]

                team_id = get_team_id(team)
                team_name = get_team_name(team)

                persian = PERSIAN_NAMES.get(
                    requested_name,
                    requested_name,
                )

                item = {
                    "id": team_id,
                    "name": team_name,
                    "country": COUNTRY,
                    "persian": persian,
                }

                confirmed.append(item)

                print(
                    f"    ✅ {team_name} "
                    f"→ {team_id}"
                )

            # ------------------------------------------------
            # چند نتیجه معتبر
            # ------------------------------------------------

            elif len(valid) > 1:

                print(
                    f"    ⚠️ AMBIGUOUS "
                    f"({len(valid)} valid results)"
                )

                for team in valid:
                    print_candidate(team)

                ambiguous.append({
                    "requested": requested_name,
                    "league": league,
                    "results": valid,
                })

            # ------------------------------------------------
            # هیچ نتیجه معتبر
            # ------------------------------------------------

            else:

                print("    ❌ NOT FOUND")

                # اگر نتیجه‌ای وجود داشته ولی فیلتر شده،
                # چند نتیجه مرتبط را برای بررسی چاپ می‌کنیم.
                if results:

                    print(
                        "       Search results:"
                    )

                    for team in results[:10]:
                        print_candidate(team)

                not_found.append({
                    "requested": requested_name,
                    "league": league,
                    "results": results,
                })

            time.sleep(REQUEST_DELAY)

    # ========================================================
    # حذف موارد تکراری بر اساس ID
    # ========================================================

    unique_confirmed = {}

    for team in confirmed:
        unique_confirmed[team["id"]] = team

    confirmed = list(
        unique_confirmed.values()
    )

    # ========================================================
    # گزارش نهایی
    # ========================================================

    print()
    print()
    print("=" * 70)
    print("FINAL REPORT")
    print("=" * 70)

    print(f"Requested : {total}")
    print(f"Confirmed : {len(confirmed)}")
    print(f"Ambiguous : {len(ambiguous)}")
    print(f"Not found : {len(not_found)}")
    print("=" * 70)

    # ========================================================
    # خروجی آماده برای کپی در پروژه
    # ========================================================

    print()
    print("=" * 70)
    print("TEAMS =")
    print("=" * 70)

    print("TEAMS = [")

    for team in confirmed:

        print("    {")
        print(f'        "id": "{team["id"]}",')
        print(f'        "name": {team["name"]!r},')
        print(f'        "country": "{team["country"]}",')
        print(f'        "persian": {team["persian"]!r},')
        print("    },")

    print("]")

    # ========================================================
    # موارد مبهم
    # ========================================================

    if ambiguous:

        print()
        print("=" * 70)
        print("AMBIGUOUS TEAMS")
        print("=" * 70)

        for item in ambiguous:

            print(
                f'\n{item["requested"]} '
                f'({item["league"]})'
            )

            for team in item["results"]:
                print_candidate(team)

    # ========================================================
    # موارد پیدا نشده
    # ========================================================

    if not_found:

        print()
        print("=" * 70)
        print("NOT FOUND")
        print("=" * 70)

        for item in not_found:

            print(
                f'- {item["requested"]} '
                f'({item["league"]})'
            )

    # ========================================================
    # ذخیره JSON برای بررسی راحت‌تر
    # ========================================================

    output = {
        "country": COUNTRY,
        "requested": total,
        "confirmed": confirmed,
        "ambiguous": [
            {
                "requested": item["requested"],
                "league": item["league"],
                "results": item["results"],
            }
            for item in ambiguous
        ],
        "not_found": [
            {
                "requested": item["requested"],
                "league": item["league"],
                "results": item["results"],
            }
            for item in not_found
        ],
    }

    with open(
        "team_ids_result.json",
        "w",
        encoding="utf-8",
    ) as f:

        json.dump(
            output,
            f,
            ensure_ascii=False,
            indent=4,
        )

    print()
    print(
        "📁 Full result saved to "
        "team_ids_result.json"
    )


if __name__ == "__main__":
    main()

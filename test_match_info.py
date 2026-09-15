import json
import time
import requests


# ============================================================
# تنظیمات ثابت
# ============================================================

SEARCH_URL = "https://www.fotmob.com/api/data/search/suggest"

REQUEST_DELAY = 0.4
TIMEOUT = 15

COUNTRY = "England"


# ============================================================
# فقط این بخش برای هر کشور عوض می‌شود
# ============================================================

TEAMS_TO_FIND = [
    # Premier League
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

    # Championship
    "Birmingham City",
    "Blackburn Rovers",
    "Bristol City",
    "Charlton Athletic",
    "Coventry City",
    "Derby County",
    "Hull City",
    "Ipswich Town",
    "Leicester City",
    "Middlesbrough",
    "Millwall",
    "Norwich City",
    "Oxford United",
    "Portsmouth",
    "Preston North End",
    "Queens Park Rangers",
    "Sheffield United",
    "Sheffield Wednesday",
    "Southampton",
    "Stoke City",
    "Swansea City",
    "Watford",
    "West Bromwich Albion",
    "Wrexham",

    # League One
    "AFC Wimbledon",
    "Barnsley",
    "Blackpool",
    "Bradford City",
    "Bromley",
    "Burton Albion",
    "Cambridge United",
    "Doncaster Rovers",
    "Exeter City",
    "Huddersfield Town",
    "Leyton Orient",
    "Lincoln City",
    "Luton Town",
    "Mansfield Town",
    "Milton Keynes Dons",
    "Northampton Town",
    "Notts County",
    "Peterborough United",
    "Plymouth Argyle",
    "Reading",
    "Rotherham United",
    "Stevenage",
    "Stockport County",
    "Wigan Athletic",
    "Wycombe Wanderers",
]


# ============================================================
# نام فارسی
#
# این بخش فقط برای نمایش خروجی است و هیچ نقشی در پیدا کردن ID
# ندارد.
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

    "Birmingham City": "بیرمنگام سیتی",
    "Blackburn Rovers": "بلکبرن",
    "Bristol City": "بریستول سیتی",
    "Charlton Athletic": "چارلتون",
    "Coventry City": "کاونتری",
    "Derby County": "دربی کانتی",
    "Hull City": "هال سیتی",
    "Ipswich Town": "ایپسویچ",
    "Leicester City": "لسترسیتی",
    "Middlesbrough": "میدلزبورو",
    "Millwall": "میلوال",
    "Norwich City": "نورویچ",
    "Oxford United": "آکسفورد یونایتد",
    "Portsmouth": "پورتسموث",
    "Preston North End": "پرستون",
    "Queens Park Rangers": "کوئینز پارک رنجرز",
    "Sheffield United": "شفیلد یونایتد",
    "Sheffield Wednesday": "شفیلد ونزدی",
    "Southampton": "ساوتهمپتون",
    "Stoke City": "استوک سیتی",
    "Swansea City": "سوانزی",
    "Watford": "واتفورد",
    "West Bromwich Albion": "وست برومویچ",
    "Wrexham": "رکسام",

    "AFC Wimbledon": "ای‌اف‌سی ویمبلدون",
    "Barnsley": "بارنزلی",
    "Blackpool": "بلکپول",
    "Bradford City": "بردفورد سیتی",
    "Bromley": "بروملی",
    "Burton Albion": "برتون آلبیون",
    "Cambridge United": "کمبریج یونایتد",
    "Doncaster Rovers": "دانکستر",
    "Exeter City": "اکستر سیتی",
    "Huddersfield Town": "هادرسفیلد",
    "Leyton Orient": "لیتون اورینت",
    "Lincoln City": "لینکلن سیتی",
    "Luton Town": "لوتون",
    "Mansfield Town": "منسفیلد",
    "Milton Keynes Dons": "میلتون کینز دونز",
    "Northampton Town": "نورث‌همپتون",
    "Notts County": "ناتس کانتی",
    "Peterborough United": "پیتربورو یونایتد",
    "Plymouth Argyle": "پلیموث آرگایل",
    "Reading": "ردینگ",
    "Rotherham United": "روترهام یونایتد",
    "Stevenage": "استیونج",
    "Stockport County": "استاکپورت کانتی",
    "Wigan Athletic": "ویگان اتلتیک",
    "Wycombe Wanderers": "وایکام واندررز",
}


# ============================================================
# ابزارهای عمومی
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
        for key in (
            "name",
            "title",
            "shortName",
        ):
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
        for key in (
            "name",
            "title",
        ):
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
# استخراج تمام آبجکت‌های team
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
# جست‌وجوی FotMob
# ============================================================

def search_team(query):

    params = {
        "term": query,
        "hits": 50,
        "lang": "en",
    }

    headers = {
        "User-Agent": (
            "Mozilla/5.0 "
            "(Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 "
            "(KHTML, like Gecko) "
            "Chrome/140 Safari/537.36"
        ),
        "Accept": "application/json",
    }

    try:

        response = requests.get(
            SEARCH_URL,
            params=params,
            headers=headers,
            timeout=TIMEOUT,
        )

        response.raise_for_status()

        data = response.json()

        return find_team_objects(data)

    except Exception as e:

        print(f"    ❌ Request error: {e}")

        return []


# ============================================================
# تشخیص تیم اصلی مردان
# ============================================================

def is_women_team(team):

    name = normalize(get_team_name(team))
    gender = normalize(get_gender(team))

    women_markers = (
        "(w)",
        "women",
        "woman",
        "femen",
        "fem",
    )

    if any(marker in name for marker in women_markers):
        return True

    if gender in (
        "female",
        "women",
        "woman",
    ):
        return True

    return False


def is_youth_team(team):

    name = normalize(get_team_name(team))

    youth_markers = (
        " u21",
        " u23",
        " u18",
        " u19",
        " u17",
        " u16",
        " u20",
        " ii",
        " youth",
        "academy",
    )

    for marker in youth_markers:

        if marker in name:
            return True

    return False


# ============================================================
# امتیازدهی به نتیجه
#
# لیگ در اینجا هیچ نقشی ندارد.
# فقط برای انتخاب تیم اصلی از نام و مشخصات نتیجه استفاده می‌شود.
# ============================================================

def candidate_score(team, requested_name):

    score = 0

    actual_name = normalize(
        get_team_name(team)
    )

    requested = normalize(
        requested_name
    )

    # نام دقیق
    if actual_name == requested:
        score += 100

    # تیم اصلی
    if not is_women_team(team):
        score += 20

    if not is_youth_team(team):
        score += 20

    return score


# ============================================================
# انتخاب کاندیدای مناسب
# ============================================================

def select_candidate(results, requested_name):

    # حذف نتایج بدون ID
    candidates = []

    for team in results:

        if not get_team_id(team):
            continue

        candidates.append(team)

    # حذف زنان و تیم‌های پایه
    candidates = [
        team
        for team in candidates
        if not is_women_team(team)
        and not is_youth_team(team)
    ]

    if not candidates:
        return None, []

    # فقط نام دقیق
    exact = [
        team
        for team in candidates
        if normalize(
            get_team_name(team)
        ) == normalize(requested_name)
    ]

    if not exact:
        return None, candidates

    # امتیازدهی
    scored = []

    for team in exact:

        scored.append(
            (
                candidate_score(
                    team,
                    requested_name,
                ),
                team,
            )
        )

    scored.sort(
        key=lambda item: item[0],
        reverse=True,
    )

    best_score = scored[0][0]

    best = [
        team
        for score, team in scored
        if score == best_score
    ]

    # اگر چند تیم دقیقاً هم‌امتیاز باشند،
    # انتخاب خودکار خطرناک است.
    if len(best) > 1:
        return None, best

    return best[0], []


# ============================================================
# نمایش نتیجه
# ============================================================

def print_candidate(team):

    print(
        f"       "
        f"ID={get_team_id(team)} | "
        f"name={get_team_name(team)!r} | "
        f"country={get_team_country(team)!r} | "
        f"league={get_league_name(team)!r} | "
        f"gender={get_gender(team)!r}"
    )


# ============================================================
# برنامه اصلی
# ============================================================

def main():

    total = len(TEAMS_TO_FIND)

    confirmed = []
    ambiguous = []
    not_found = []

    print("=" * 70)
    print("FotMob Team ID Extractor")
    print("=" * 70)
    print(f"Country: {COUNTRY}")
    print(f"Total teams: {total}")
    print("=" * 70)

    for index, requested_name in enumerate(
        TEAMS_TO_FIND,
        start=1,
    ):

        print(
            f"[{index}/{total}] "
            f"{requested_name}"
        )

        results = search_team(
            requested_name
        )

        # حذف IDهای تکراری
        unique_results = {}

        for team in results:

            team_id = get_team_id(team)

            if team_id:
                unique_results[team_id] = team

        results = list(
            unique_results.values()
        )

        candidate, alternatives = select_candidate(
            results,
            requested_name,
        )

        # ----------------------------------------------------
        # CONFIRMED
        # ----------------------------------------------------

        if candidate is not None:

            team_id = get_team_id(candidate)
            team_name = get_team_name(candidate)

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

        # ----------------------------------------------------
        # AMBIGUOUS
        # ----------------------------------------------------

        elif alternatives:

            print(
                f"    ⚠️ AMBIGUOUS "
                f"({len(alternatives)} candidates)"
            )

            for team in alternatives:
                print_candidate(team)

            ambiguous.append({
                "requested": requested_name,
                "results": alternatives,
            })

        # ----------------------------------------------------
        # NOT FOUND
        # ----------------------------------------------------

        else:

            print("    ❌ NOT FOUND")

            if results:

                print(
                    "       Relevant results:"
                )

                for team in results[:10]:
                    print_candidate(team)

            not_found.append({
                "requested": requested_name,
                "results": results,
            })

        time.sleep(REQUEST_DELAY)

    # ========================================================
    # حذف IDهای تکراری از confirmed
    # ========================================================

    unique_confirmed = {}

    for team in confirmed:

        unique_confirmed[
            team["id"]
        ] = team

    confirmed = list(
        unique_confirmed.values()
    )

    # ========================================================
    # گزارش نهایی
    # ========================================================

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
    # خروجی TEAMS
    # ========================================================

    print()
    print("=" * 70)
    print("TEAMS = [")
    print("=" * 70)

    print("TEAMS = [")

    for team in confirmed:

        print("    {")

        print(
            f'        "id": '
            f'"{team["id"]}",'
        )

        print(
            f'        "name": '
            f'{team["name"]!r},'
        )

        print(
            f'        "country": '
            f'"{team["country"]}",'
        )

        print(
            f'        "persian": '
            f'{team["persian"]!r},'
        )

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
                f'\n{item["requested"]}'
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
                f'- {item["requested"]}'
            )

    # ========================================================
    # ذخیره نتیجه کامل در JSON
    # ========================================================

    output = {
        "country": COUNTRY,
        "requested": total,
        "confirmed": confirmed,
        "ambiguous": ambiguous,
        "not_found": not_found,
    }

    with open(
        "team_ids_result.json",
        "w",
        encoding="utf-8",
    ) as file:

        json.dump(
            output,
            file,
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

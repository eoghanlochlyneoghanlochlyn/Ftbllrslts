import requests


# ============================================================
# مسابقه‌ها
# ============================================================

MATCHES = [
    {
        "name": "مسابقه 5749667",
        "id": "5749667",
    },
    {
        "name": "مسابقه 588762",
        "id": "588762",
    },
]


# ============================================================
# تنظیمات
# ============================================================

URL = "https://www.fotmob.com/api/data/matchDetails"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/131.0.0.0 Safari/537.36"
    ),
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "en-US,en;q=0.9",
    "Referer": "https://www.fotmob.com/",
}


# ============================================================
# دریافت اطلاعات
# ============================================================

def get_match(match_id):

    try:

        response = requests.get(
            URL,
            params={"matchId": match_id},
            headers=HEADERS,
            timeout=30,
        )

        print(
            f"   ↳ HTTP {response.status_code}"
        )

        if response.status_code != 200:
            return None

        return response.json()

    except Exception as error:

        print(
            f"   ❌ خطا: {error}"
        )

        return None


# ============================================================
# جستجوی بازگشتی در JSON
# ============================================================

def find_keys(data, wanted_keys):

    results = []

    if isinstance(data, dict):

        for key, value in data.items():

            if key.lower() in wanted_keys:
                results.append(value)

            results.extend(
                find_keys(
                    value,
                    wanted_keys,
                )
            )

    elif isinstance(data, list):

        for item in data:

            results.extend(
                find_keys(
                    item,
                    wanted_keys,
                )
            )

    return results


# ============================================================
# پیدا کردن نام بازیکن
# ============================================================

def player_name(player):

    if not isinstance(player, dict):
        return str(player)

    for key in [
        "name",
        "playerName",
        "fullName",
        "shortName",
    ]:

        value = player.get(key)

        if isinstance(value, str) and value.strip():
            return value.strip()

    nested = player.get("player")

    if isinstance(nested, dict):
        return player_name(nested)

    return "بازیکن نامشخص"


# ============================================================
# استخراج بازیکنان از یک ساختار
# ============================================================

def extract_players(data):

    players = []

    if isinstance(data, list):

        for item in data:

            if isinstance(item, dict):

                name = player_name(item)

                if name != "بازیکن نامشخص":
                    players.append(name)

    elif isinstance(data, dict):

        name = player_name(data)

        if name != "بازیکن نامشخص":
            players.append(name)

    return players


# ============================================================
# نمایش نتیجه
# ============================================================

def show_score(data):

    print()
    print("📊 نتیجه:")

    score_data = find_keys(
        data,
        {
            "score",
            "current",
            "ftscore",
            "homeScore",
            "awayScore",
        },
    )

    if not score_data:

        print("   اطلاعات نتیجه پیدا نشد.")
        return

    found = False

    for item in score_data:

        if isinstance(item, dict):

            home = (
                item.get("home")
                or item.get("homeScore")
            )

            away = (
                item.get("away")
                or item.get("awayScore")
            )

            if home is not None or away is not None:

                print(
                    f"   ⚽ {home} - {away}"
                )

                found = True

    if not found:

        print(
            "   اطلاعات نتیجه در پاسخ وجود دارد "
            "اما ساختار آن هنوز مشخص نیست."
        )


# ============================================================
# نمایش ترکیب
# ============================================================

def show_lineups(data):

    print()
    print("👥 ترکیب تیم‌ها:")

    lineup_data = find_keys(
        data,
        {
            "lineup",
            "lineups",
            "players",
        },
    )

    all_players = []

    for item in lineup_data:

        players = extract_players(item)

        for player in players:

            if player not in all_players:
                all_players.append(player)

    if not all_players:

        print(
            "   ترکیب بازیکنان پیدا نشد."
        )

        return

    for number, player in enumerate(
        all_players,
        1,
    ):

        print(
            f"   {number}. {player}"
        )


# ============================================================
# نمایش گلزنان
# ============================================================

def show_goals(data):

    print()
    print("⚽ گلزنان:")

    event_data = find_keys(
        data,
        {
            "events",
            "goals",
            "goal",
            "matchfacts",
        },
    )

    goals = []

    def scan(value):

        if isinstance(value, dict):

            text = " ".join(
                str(value.get(key, ""))
                for key in [
                    "type",
                    "eventType",
                    "incidentType",
                    "action",
                ]
            ).lower()

            if "goal" in text:

                name = (
                    value.get("playerName")
                    or value.get("name")
                )

                if name:
                    goals.append(
                        str(name)
                    )

            for child in value.values():
                scan(child)

        elif isinstance(value, list):

            for child in value:
                scan(child)

    for item in event_data:
        scan(item)

    unique_goals = []

    for goal in goals:

        if goal not in unique_goals:
            unique_goals.append(goal)

    if not unique_goals:

        print(
            "   گلزنی پیدا نشد."
        )

        return

    for goal in unique_goals:

        print(
            f"   ⚽ {goal}"
        )


# ============================================================
# نمایش تعویض‌ها
# ============================================================

def show_substitutions(data):

    print()
    print("🔄 تعویض‌ها:")

    substitution_data = find_keys(
        data,
        {
            "substitution",
            "substitutions",
        },
    )

    substitutions = []

    def scan(value):

        if isinstance(value, dict):

            text = " ".join(
                str(value.get(key, ""))
                for key in [
                    "type",
                    "eventType",
                    "incidentType",
                    "action",
                ]
            ).lower()

            if (
                "substitution" in text
                or "sub" == text.strip()
            ):

                substitutions.append(value)

            for child in value.values():
                scan(child)

        elif isinstance(value, list):

            for child in value:
                scan(child)

    for item in substitution_data:
        scan(item)

    if not substitutions:

        print(
            "   تعویضی پیدا نشد."
        )

        return

    for substitution in substitutions:

        player_out = (
            substitution.get("playerOut")
            or substitution.get("outPlayer")
            or substitution.get("playerOff")
        )

        player_in = (
            substitution.get("playerIn")
            or substitution.get("inPlayer")
            or substitution.get("playerOn")
        )

        if isinstance(
            player_out,
            dict,
        ):
            player_out = player_name(
                player_out
            )

        if isinstance(
            player_in,
            dict,
        ):
            player_in = player_name(
                player_in
            )

        print(
            f"   🔄 {player_out or '?'} "
            f"⬅️ {player_in or '?'}"
        )


# ============================================================
# بررسی مسابقه
# ============================================================

def check_match(match):

    print()
    print("=" * 70)
    print(
        f"⚽ {match['name']}"
    )
    print(
        f"🆔 شناسه: {match['id']}"
    )
    print("=" * 70)

    data = get_match(
        match["id"]
    )

    if data is None:

        print(
            "❌ اطلاعات مسابقه دریافت نشد."
        )

        return

    if isinstance(data, dict):

        if data.get("error") is True:

            print(
                "❌ فوت‌موب برای این شناسه "
                "خطا برگرداند."
            )

            if data.get("message"):
                print(
                    f"   پیام: {data['message']}"
                )

            return

    print(
        "✅ اطلاعات مسابقه دریافت شد."
    )

    show_score(data)

    show_lineups(data)

    show_goals(data)

    show_substitutions(data)

    print()
    print("=" * 

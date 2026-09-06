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
    "User-Agent": "Mozilla/5.0",
    "Accept": "application/json",
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

        print(f"HTTP: {response.status_code}")

        if response.status_code != 200:
            return None

        return response.json()

    except Exception as error:
        print(f"خطا: {error}")
        return None


# ============================================================
# جستجوی بازگشتی یک کلید در JSON
# ============================================================

def find_values(data, keys):

    result = []

    if isinstance(data, dict):

        for key, value in data.items():

            if key.lower() in keys:
                result.append(value)

            result.extend(
                find_values(value, keys)
            )

    elif isinstance(data, list):

        for item in data:

            result.extend(
                find_values(item, keys)
            )

    return result


# ============================================================
# تبدیل اطلاعات بازیکن به نام
# ============================================================

def get_player_name(player):

    if isinstance(player, str):
        return player

    if not isinstance(player, dict):
        return None

    for key in [
        "name",
        "playerName",
        "fullName",
        "shortName",
    ]:

        value = player.get(key)

        if isinstance(value, str):
            return value

    nested = player.get("player")

    if isinstance(nested, dict):
        return get_player_name(nested)

    return None


# ============================================================
# نمایش ترکیب
# ============================================================

def show_lineups(data):

    print()
    print("👥 ترکیب:")

    values = find_values(
        data,
        {
            "lineup",
            "lineups",
        },
    )

    if not values:

        print("   ترکیب پیدا نشد.")
        return

    names = []

    for value in values:

        if isinstance(value, dict):

            for key in [
                "starters",
                "players",
                "startingPlayers",
                "bench",
                "substitutes",
            ]:

                players = value.get(key)

                if isinstance(players, list):

                    for player in players:

                        name = get_player_name(player)

                        if name and name not in names:
                            names.append(name)

        elif isinstance(value, list):

            for player in value:

                name = get_player_name(player)

                if name and name not in names:
                    names.append(name)

    if not names:

        print("   بازیکنی در ترکیب پیدا نشد.")
        return

    for name in names:
        print(f"   • {name}")


# ============================================================
# نمایش نتیجه
# ============================================================

def show_score(data):

    print()
    print("📊 نتیجه:")

    values = find_values(
        data,
        {
            "score",
        },
    )

    found = False

    for value in values:

        if not isinstance(value, dict):
            continue

        home = value.get("home")
        away = value.get("away")

        if home is not None and away is not None:

            print(f"   ⚽ {home} - {away}")
            found = True

    if not found:
        print("   نتیجه پیدا نشد.")


# ============================================================
# نمایش گلزنان
# ============================================================

def show_goals(data):

    print()
    print("⚽ گلزنان:")

    events = find_values(
        data,
        {
            "events",
            "goals",
            "incidents",
        },
    )

    names = []

    def scan(value):

        if isinstance(value, dict):

            text = ""

            for key in [
                "type",
                "eventType",
                "incidentType",
                "action",
                "event",
            ]:

                item = value.get(key)

                if item is not None:
                    text += " " + str(item).lower()

            if "goal" in text:

                for key in [
                    "playerName",
                    "name",
                    "player",
                    "scorer",
                ]:

                    player = value.get(key)

                    name = get_player_name(player)

                    if name and name not in names:
                        names.append(name)

            for child in value.values():
                scan(child)

        elif isinstance(value, list):

            for child in value:
                scan(child)

    for item in events:
        scan(item)

    if not names:

        print("   گلزنی پیدا نشد.")
        return

    for name in names:
        print(f"   ⚽ {name}")


# ============================================================
# نمایش تعویض‌ها
# ============================================================

def show_substitutions(data):

    print()
    print("🔄 تعویض‌ها:")

    events = find_values(
        data,
        {
            "events",
            "incidents",
            "substitutions",
        },
    )

    substitutions = []

    def scan(value):

        if isinstance(value, dict):

            text = ""

            for key in [
                "type",
                "eventType",
                "incidentType",
                "action",
            ]:

                item = value.get(key)

                if item is not None:
                    text += " " + str(item).lower()

            if "substitution" in text:

                substitutions.append(value)

            for child in value.values():
                scan(child)

        elif isinstance(value, list):

            for child in value:
                scan(child)

    for item in events:
        scan(item)

    if not substitutions:

        print("   تعویضی پیدا نشد.")
        return

    for item in substitutions:

        player_in = None
        player_out = None

        for key in [
            "playerIn",
            "inPlayer",
            "playerOn",
        ]:

            if key in item:
                player_in = get_player_name(
                    item[key]
                )
                break

        for key in [
            "playerOut",
            "outPlayer",
            "playerOff",
        ]:

            if key in item:
                player_out = get_player_name(
                    item[key]
                )
                break

        print(
            f"   🔄 "
            f"{player_out or '?'} "
            f"← "
            f"{player_in or '?'}"
        )


# ============================================================
# بررسی یک مسابقه
# ============================================================

def check_match(match):

    print()
    print("=" * 60)
    print(f"⚽ {match['name']}")
    print(f"🆔 {match['id']}")
    print("=" * 60)

    data = get_match(match["id"])

    if data is None:

        print("❌ اطلاعات دریافت نشد.")
        return

    if isinstance(data, dict):

        if data.get("error") is True:

            print("❌ فوت‌موب خطا برگرداند.")

            message = data.get("message")

            if message:
                print(f"پیام: {message}")

            return

    print("✅ اطلاعات دریافت شد.")

    show_score(data)

    show_lineups(data)

    show_goals(data)

    show_substitutions(data)

    print("=" * 60)


# ============================================================
# اجرای برنامه
# ============================================================

def main():

    print("=" * 60)
    print("⚽ آزمایش اطلاعات فوت‌موب")
    print("=" * 60)

    for match in MATCHES:
        check_match(match)

    print()
    print("🏁 پایان آزمایش")


if __name__ == "__main__":
    main()

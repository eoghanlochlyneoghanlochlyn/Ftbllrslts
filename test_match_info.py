import json
import requests


MATCH_ID = "6106264"

URL = f"https://www.fotmob.com/match/{MATCH_ID}"

HEADERS = {
    "User-Agent": "Mozilla/5.0"
}


print("=" * 60)
print("🔎 TEST FOTMOB LINEUP")
print("=" * 60)
print()

# ============================================================
# دریافت صفحه
# ============================================================

print("🌐 Requesting FotMob...")

response = requests.get(
    URL,
    headers=HEADERS,
    timeout=30
)

print("📡 HTTP STATUS:", response.status_code)

response.raise_for_status()

print("📏 HTML LENGTH:", len(response.text))
print()

# ============================================================
# استخراج __NEXT_DATA__
# ============================================================

marker = '<script id="__NEXT_DATA__" type="application/json">'

start = response.text.find(marker)

if start == -1:
    print("❌ NEXT_DATA NOT FOUND")
    raise SystemExit(1)

start += len(marker)

end = response.text.find("</script>", start)

if end == -1:
    print("❌ NEXT_DATA END NOT FOUND")
    raise SystemExit(1)

raw_json = response.text[start:end]

data = json.loads(raw_json)

print("✅ JSON OK")
print()

# ============================================================
# دسترسی به اطلاعات مسابقه
# ============================================================

page_props = (
    data
    .get("props", {})
    .get("pageProps", {})
)

general = page_props.get("general", {})

content = page_props.get("content", {})

lineup = content.get("lineup")

# ============================================================
# اطلاعات اصلی بازی
# ============================================================

print("=" * 60)
print("⚽ MATCH")
print("=" * 60)

print("Match ID:", general.get("matchId"))
print("Match:", general.get("matchName"))
print("League:", general.get("leagueName"))
print("Time:", general.get("matchTimeUTC"))
print("Started:", general.get("started"))
print("Finished:", general.get("finished"))
print("Coverage:", general.get("coverageLevel"))

print()

# ============================================================
# بررسی وجود ترکیب
# ============================================================

print("=" * 60)
print("👥 LINEUP")
print("=" * 60)

if lineup is None:

    print("❌ LINEUP NOT AVAILABLE")

else:

    print("Lineup available: YES")
    print()

    # --------------------------------------------------------
    # اطلاعات کلی ترکیب
    # --------------------------------------------------------

    print("Lineup ID:", lineup.get("matchId"))
    print("Lineup type:", lineup.get("lineupType"))
    print("Source:", lineup.get("source"))

    print()

    # --------------------------------------------------------
    # فیلترهای موجود
    # --------------------------------------------------------

    print("Available filters:")

    filters = lineup.get("availableFilters")

    if filters:

        print(filters)

    else:

        print("None")

    print()

    # --------------------------------------------------------
    # تیم میزبان
    # --------------------------------------------------------

    home = lineup.get("homeTeam")

    print("=" * 60)
    print("🏠 HOME TEAM")
    print("=" * 60)

    if home:

        print("Team:", home.get("name"))
        print("Team ID:", home.get("id"))
        print()

        print("Keys:")

        for key in home.keys():
            print(" -", key)

        print()

        # چاپ اطلاعات بازیکنان
        players = home.get("players")

        if players:

            print("Players:")

            for player in players:

                print(player)

        else:

            print("Players: NONE")

    else:

        print("HOME TEAM DATA NOT AVAILABLE")

    print()

    # --------------------------------------------------------
    # تیم مهمان
    # --------------------------------------------------------

    away = lineup.get("awayTeam")

    print("=" * 60)
    print("✈️ AWAY TEAM")
    print("=" * 60)

    if away:

        print("Team:", away.get("name"))
        print("Team ID:", away.get("id"))
        print()

        print("Keys:")

        for key in away.keys():
            print(" -", key)

        print()

        # چاپ اطلاعات بازیکنان
        players = away.get("players")

        if players:

            print("Players:")

            for player in players:

                print(player)

        else:

            print("Players: NONE")

    else:

        print("AWAY TEAM DATA NOT AVAILABLE")

# ============================================================
# پایان
# ============================================================

print()
print("=" * 60)
print("✅ TEST FINISHED")
print("=" * 60)

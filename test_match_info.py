import json
import requests


MATCH_ID = "6106264"

URL = f"https://www.fotmob.com/match/{MATCH_ID}"

HEADERS = {
    "User-Agent": "Mozilla/5.0"
}


print("=" * 60)
print("🔎 TEST FOTMOB MATCH DATA")
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

print("HTTP STATUS:", response.status_code)
print("HTML LENGTH:", len(response.text))
print()

response.raise_for_status()

html = response.text

# ============================================================
# استخراج NEXT_DATA
# ============================================================

marker = '<script id="__NEXT_DATA__" type="application/json">'

start = html.find(marker)

if start == -1:
    print("❌ NEXT_DATA NOT FOUND")
    raise SystemExit(1)

start += len(marker)

end = html.find("</script>", start)

if end == -1:
    print("❌ NEXT_DATA END NOT FOUND")
    raise SystemExit(1)

raw_json = html[start:end]

data = json.loads(raw_json)

print("✅ NEXT_DATA JSON OK")
print()

# ============================================================
# اطلاعات اصلی
# ============================================================

page_props = (
    data
    .get("props", {})
    .get("pageProps", {})
)

general = page_props.get("general", {})

content = page_props.get("content", {})

print("=" * 60)
print("⚽ MATCH")
print("=" * 60)

print("Match ID:", general.get("matchId"))
print("Match:", general.get("matchName"))
print("Started:", general.get("started"))
print("Finished:", general.get("finished"))

print()

# ============================================================
# بررسی lineup
# ============================================================

lineup = content.get("lineup")

print("=" * 60)
print("👥 LINEUP")
print("=" * 60)

if not lineup:

    print("❌ NO LINEUP")

else:

    print("Lineup type:", lineup.get("lineupType"))
    print("Source:", lineup.get("source"))
    print()

    home = lineup.get("homeTeam", {})
    away = lineup.get("awayTeam", {})

    # --------------------------------------------------------
    # تیم میزبان
    # --------------------------------------------------------

    print("HOME:", home.get("name"))
    print("HOME FORMATION:", home.get("formation"))

    starters = home.get("starters", [])
    subs = home.get("subs", [])

    print("HOME STARTERS:", len(starters))
    print("HOME SUBS:", len(subs))

    print()

    # --------------------------------------------------------
    # تیم مهمان
    # --------------------------------------------------------

    print("AWAY:", away.get("name"))
    print("AWAY FORMATION:", away.get("formation"))

    starters = away.get("starters", [])
    subs = away.get("subs", [])

    print("AWAY STARTERS:", len(starters))
    print("AWAY SUBS:", len(subs))

print()

# ============================================================
# جستجوی عبارت های مربوط به lineup در HTML
# ============================================================

print("=" * 60)
print("🔍 SEARCHING HTML FOR LINEUP DATA")
print("=" * 60)

keywords = [
    "lineupType",
    "starters",
    "substitutes",
    "bench",
    "predicted",
    "standard"
]

for keyword in keywords:

    count = html.count(keyword)

    print(f"{keyword}: {count}")

print()

# ============================================================
# ذخیره HTML
# ============================================================

with open(
    "fotmob_match_page.html",
    "w",
    encoding="utf-8"
) as f:

    f.write(html)

print("💾 HTML SAVED: fotmob_match_page.html")

print()

# ============================================================
# پایان
# ============================================================

print("=" * 60)
print("✅ TEST FINISHED")
print("=" * 60)

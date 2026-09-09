import json
import requests


MATCH_ID = "6106264"

URL = f"https://www.fotmob.com/match/{MATCH_ID}"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/140.0.0.0 Safari/537.36"
    ),
    "Accept": (
        "text/html,application/xhtml+xml,application/xml;"
        "q=0.9,image/avif,image/webp,*/*;q=0.8"
    ),
    "Accept-Language": "en-US,en;q=0.9",
    "Referer": "https://www.fotmob.com/",
}


print("=" * 70)
print("🔎 تست اطلاعات قبل از شروع بازی")
print("=" * 70)
print()

print(f"🆔 Match ID: {MATCH_ID}")
print(f"🌐 URL: {URL}")
print()

# ------------------------------------------------------------
# دریافت صفحه
# ------------------------------------------------------------

response = requests.get(
    URL,
    headers=HEADERS,
    timeout=30
)

print(f"📡 HTTP Status: {response.status_code}")
print(f"📏 HTML Length: {len(response.text)}")
print()

response.raise_for_status()

# ------------------------------------------------------------
# پیدا کردن __NEXT_DATA__
# ------------------------------------------------------------

start_marker = '<script id="__NEXT_DATA__" type="application/json">'
end_marker = "</script>"

start = response.text.find(start_marker)

if start == -1:
    print("❌ __NEXT_DATA__ پیدا نشد.")
    exit(1)

start += len(start_marker)

end = response.text.find(end_marker, start)

if end == -1:
    print("❌ پایان __NEXT_DATA__ پیدا نشد.")
    exit(1)

json_text = response.text[start:end]

print("✅ __NEXT_DATA__ پیدا شد.")
print()

# ------------------------------------------------------------
# تبدیل JSON
# ------------------------------------------------------------

data = json.loads(json_text)

print("✅ JSON با موفقیت خوانده شد.")
print()

# ------------------------------------------------------------
# pageProps
# ------------------------------------------------------------

page_props = (
    data
    .get("props", {})
    .get("pageProps", {})
)

print("=" * 70)
print("🧩 اطلاعات موجود در pageProps")
print("=" * 70)
print()

for key in page_props.keys():
    print(f"  • {key}")

print()

# ------------------------------------------------------------
# بخش‌های اصلی
# ------------------------------------------------------------

general = page_props.get("general", {})
header = page_props.get("header", {})
content = page_props.get("content", {})

# ------------------------------------------------------------
# اطلاعات کلی بازی
# ------------------------------------------------------------

print("=" * 70)
print("⚽ اطلاعات بازی")
print("=" * 70)
print()

print("Match ID:", general.get("matchId"))
print("نام بازی:", general.get("matchName"))
print("لیگ:", general.get("leagueName"))
print("زمان UTC:", general.get("matchTimeUTC"))
print("شروع شده:", general.get("started"))
print("تمام شده:", general.get("finished"))
print("سطح پوشش:", general.get("coverageLevel"))
print()

# ------------------------------------------------------------
# کلیدهای general
# ------------------------------------------------------------

print("=" * 70)
print("🔑 کلیدهای general")
print("=" * 70)
print()

for key in general.keys():
    print(f"  • {key}")

print()

# ------------------------------------------------------------
# کلیدهای header
# ------------------------------------------------------------

print("=" * 70)
print("🔑 کلیدهای header")
print("=" * 70)
print()

for key in header.keys():
    print(f"  • {key}")

print()

# ------------------------------------------------------------
# کلیدهای content
# ------------------------------------------------------------

print("=" * 70)
print("🔑 کلیدهای content")
print("=" * 70)
print()

for key in content.keys():
    print(f"  • {key}")

print()

# ------------------------------------------------------------
# بررسی lineup
# ------------------------------------------------------------

print("=" * 70)
print("👥 بررسی ترکیب")
print("=" * 70)
print()

lineup = content.get("lineup")

if lineup is None:
    print("❌ کلید lineup وجود ندارد.")

elif not lineup:
    print("⚠️ کلید lineup وجود دارد ولی خالی است.")

else:
    print("✅ اطلاعات lineup وجود دارد.")
    print()

    print("کلیدهای lineup:")

    for key in lineup.keys():
        print(f"  • {key}")

    print()

    home_lineup = lineup.get("homeTeam")
    away_lineup = lineup.get("awayTeam")

    print("میزبان:")
    print(home_lineup)
    print()

    print("مهمان:")
    print(away_lineup)
    print()

# ------------------------------------------------------------
# بررسی matchFacts
# ------------------------------------------------------------

print("=" * 70)
print("📋 بررسی matchFacts")
print("=" * 70)
print()

match_facts = content.get("matchFacts")

if match_facts is None:
    print("❌ matchFacts وجود ندارد.")

else:
    print("✅ matchFacts وجود دارد.")
    print()

    print("کلیدهای matchFacts:")

    for key in match_facts.keys():
        print(f"  • {key}")

    print()

# ------------------------------------------------------------
# بررسی stats
# ------------------------------------------------------------

print("=" * 70)
print("📊 بررسی آمار")
print("=" * 70)
print()

stats = content.get("stats")

if stats is None:
    print("❌ stats وجود ندارد.")

elif not stats:
    print("⚠️ stats وجود دارد ولی خالی است.")

else:
    print("✅ stats وجود دارد.")
    print()

    print("کلیدهای stats:")

    for key in stats.keys():
        print(f"  • {key}")

    print()

# ------------------------------------------------------------
# بررسی shotmap
# ------------------------------------------------------------

print("=" * 70)
print("🎯 بررسی shotmap")
print("=" * 70)
print()

shotmap = content.get("shotmap")

if shotmap is None:
    print("❌ shotmap وجود ندارد.")

elif not shotmap:
    print("⚠️ shotmap وجود دارد ولی خالی است.")

else:
    print("✅ shotmap وجود دارد.")

    if isinstance(shotmap, dict):
        print("کلیدها:")

        for key in shotmap.keys():
            print(f"  • {key}")

print()

# ------------------------------------------------------------
# ذخیره داده خام
# ------------------------------------------------------------

filename = "fotmob_match_pre_data.json"

with open(
    filename,
    "w",
    encoding="utf-8"
) as file:

    json.dump(
        data,
        file,
        ensure_ascii=False,
        indent=2
    )

print("=" * 70)
print(f"💾 داده خام ذخیره شد: {filename}")
print("=" * 70)
print()

print("✅ تست تمام شد.")

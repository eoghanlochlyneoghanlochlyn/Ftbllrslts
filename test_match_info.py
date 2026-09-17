import requests
import json
import re

MATCH_URL = "https://www.fotmob.com/matches/argentina-vs-france/1hox8a#3370572"

headers = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/140.0.0.0 Safari/537.36"
    )
}

response = requests.get(
    MATCH_URL,
    headers=headers,
    timeout=30
)

print("Status:", response.status_code)

if response.status_code != 200:
    print("❌ صفحه بازی دریافت نشد.")
    print(response.text[:2000])
    raise SystemExit

html = response.text

print("HTML length:", len(html))

match = re.search(
    r'<script id="__NEXT_DATA__" type="application/json">(.*?)</script>',
    html,
    re.DOTALL
)

if not match:
    print("❌ __NEXT_DATA__ داخل صفحه پیدا نشد.")
    raise SystemExit

data = json.loads(match.group(1))

print("✅ __NEXT_DATA__ پیدا شد.")
print("Top-level keys:", list(data.keys()))


# --------------------------------------------------------
# جستجوی شماره پیراهن داخل کل داده صفحه
# --------------------------------------------------------

target_keys = {
    "shirtNumber",
    "shirt_number",
    "shirtNo",
    "shirt_no",
    "jerseyNumber",
    "jersey_number",
    "jerseyNo",
    "jersey_no",
    "shirt",
    "number",
}


found_count = 0


def search_for_shirt_numbers(obj, path="root"):

    global found_count

    if isinstance(obj, dict):

        for key, value in obj.items():

            if key in target_keys:

                found_count += 1

                print("\n" + "=" * 80)
                print("🎯 SHIRT NUMBER FOUND")
                print("=" * 80)
                print("Path:", f"{path}.{key}")
                print("Key:", key)
                print(
                    "Value:",
                    json.dumps(
                        value,
                        ensure_ascii=False
                    )
                )

                # اطلاعات اطراف این شماره را هم چاپ می‌کنیم
                print("\nParent object:")

                print(
                    json.dumps(
                        obj,
                        ensure_ascii=False,
                        indent=2,
                        default=str
                    )
                )

            search_for_shirt_numbers(
                value,
                f"{path}.{key}"
            )

    elif isinstance(obj, list):

        for i, value in enumerate(obj):

            search_for_shirt_numbers(
                value,
                f"{path}[{i}]"
            )


print("\n🔎 Searching entire page data...")

search_for_shirt_numbers(data)


print("\n" + "=" * 80)
print("SEARCH FINISHED")
print("=" * 80)

if found_count == 0:
    print("❌ هیچ کلید شناخته‌شده‌ای برای شماره پیراهن پیدا نشد.")
else:
    print(
        f"✅ تعداد موارد پیدا شده: {found_count}"
    )

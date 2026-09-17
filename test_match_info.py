import requests
import json
import re

MATCH_ID = "5811755"

url = f"https://www.fotmob.com/matches/-/-/{MATCH_ID}"

headers = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/140.0.0.0 Safari/537.36"
    )
}

response = requests.get(
    url,
    headers=headers,
    timeout=30
)

print("Status:", response.status_code)

if response.status_code != 200:
    print("Response:")
    print(response.text[:2000])
    raise SystemExit

html = response.text

match = re.search(
    r'<script id="__NEXT_DATA__" type="application/json">(.*?)</script>',
    html,
    re.DOTALL
)

if not match:
    print("❌ __NEXT_DATA__ پیدا نشد.")
    raise SystemExit

data = json.loads(match.group(1))

print("\n✅ __NEXT_DATA__ پیدا شد.")

def find_keys(obj, target_keys, path="root"):
    if isinstance(obj, dict):
        for key, value in obj.items():

            if key in target_keys:
                print("\n" + "=" * 80)
                print(f"FOUND KEY: {key}")
                print(f"PATH: {path}.{key}")
                print("=" * 80)
                print(
                    json.dumps(
                        value,
                        ensure_ascii=False,
                        indent=2,
                        default=str
                    )
                )

            find_keys(
                value,
                target_keys,
                f"{path}.{key}"
            )

    elif isinstance(obj, list):
        for i, value in enumerate(obj):
            find_keys(
                value,
                target_keys,
                f"{path}[{i}]"
            )


target_keys = {
    "shirtNumber",
    "shirt_number",
    "shirtNo",
    "shirt_no",
    "number",
    "jerseyNumber",
    "jersey_number",
    "jerseyNo",
    "jersey_no"
}

find_keys(data, target_keys)

print("\n" + "=" * 80)
print("SEARCH FINISHED")
print("=" * 80)

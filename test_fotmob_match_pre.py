import json
import requests

MATCH_ID = "6106264"

URL = f"https://www.fotmob.com/match/{MATCH_ID}"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/140.0.0.0 Safari/537.36"
    )
}

print("TEST 1 - START")

response = requests.get(
    URL,
    headers=HEADERS,
    timeout=30
)

print("TEST 2 - STATUS:", response.status_code)
print("TEST 3 - HTML:", len(response.text))

response.raise_for_status()

print("TEST 4 - SEARCHING NEXT_DATA")

marker = '<script id="__NEXT_DATA__" type="application/json">'

position = response.text.find(marker)

if position == -1:
    print("TEST 5 - NEXT_DATA NOT FOUND")
    raise SystemExit(1)

print("TEST 5 - NEXT_DATA FOUND")

start = position + len(marker)

end = response.text.find(
    "</script>",
    start
)

if end == -1:
    print("TEST 6 - END NOT FOUND")
    raise SystemExit(1)

print("TEST 6 - JSON SECTION FOUND")

json_text = response.text[start:end]

print("TEST 7 - JSON LENGTH:", len(json_text))

try:
    data = json.loads(json_text)

except Exception as error:
    print("TEST 8 - JSON ERROR")
    print(error)
    raise

print("TEST 8 - JSON OK")

print("TEST 9 - TOP LEVEL KEYS:")
print(list(data.keys()))

props = data.get("props", {})

print("TEST 10 - PROPS KEYS:")
print(list(props.keys()))

page_props = props.get("pageProps", {})

print("TEST 11 - PAGEPROPS KEYS:")
print(list(page_props.keys()))

print("TEST 12 - DONE")

with open(
    "fotmob_match_pre_data.json",
    "w",
    encoding="utf-8"
) as file:

    json.dump(
        data,
        file,
        ensure_ascii=False,
        indent=2
    )

print("TEST 13 - FILE SAVED")

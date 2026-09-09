import json
import requests

MATCH_ID = "6106264"

print("=" * 60)
print("TEST STARTED")
print("=" * 60)

url = f"https://www.fotmob.com/match/{MATCH_ID}"

headers = {
    "User-Agent": "Mozilla/5.0"
}

print("Requesting:", url)

response = requests.get(
    url,
    headers=headers,
    timeout=30
)

print("HTTP STATUS:", response.status_code)
print("HTML LENGTH:", len(response.text))

if response.status_code != 200:
    print("ERROR: HTTP request failed")
    raise SystemExit(1)

print("HTTP request OK")

marker = '<script id="__NEXT_DATA__" type="application/json">'

start = response.text.find(marker)

print("NEXT_DATA POSITION:", start)

if start == -1:
    print("ERROR: NEXT_DATA not found")
    raise SystemExit(1)

start += len(marker)

end = response.text.find("</script>", start)

print("NEXT_DATA END:", end)

if end == -1:
    print("ERROR: NEXT_DATA end not found")
    raise SystemExit(1)

raw_json = response.text[start:end]

print("JSON LENGTH:", len(raw_json))

try:
    data = json.loads(raw_json)
except Exception as error:
    print("ERROR: JSON parsing failed")
    print(error)
    raise SystemExit(1)

print("JSON PARSED OK")

props = data.get("props", {})
page_props = props.get("pageProps", {})

print()
print("=" * 60)
print("PAGE PROPS")
print("=" * 60)

print(list(page_props.keys()))

general = page_props.get("general", {})

print()
print("=" * 60)
print("MATCH INFORMATION")
print("=" * 60)

print("Match ID:", general.get("matchId"))
print("Match name:", general.get("matchName"))
print("League:", general.get("leagueName"))
print("Time:", general.get("matchTimeUTC"))
print("Started:", general.get("started"))
print("Finished:", general.get("finished"))
print("Coverage:", general.get("coverageLevel"))

content = page_props.get("content", {})

print()
print("=" * 60)
print("CONTENT")
print("=" * 60)

print(list(content.keys()))

lineup = content.get("lineup")

print()
print("LINEUP:")

if lineup is None:
    print("NOT AVAILABLE")

elif lineup == {}:
    print("EMPTY")

else:
    print("AVAILABLE")
    print(list(lineup.keys()))

match_facts = content.get("matchFacts")

print()
print("MATCH FACTS:")

if match_facts is None:
    print("NOT AVAILABLE")
else:
    print("AVAILABLE")
    print(list(match_facts.keys()))

stats = content.get("stats")

print()
print("STATS:")

if stats is None:
    print("NOT AVAILABLE")
else:
    print("AVAILABLE")
    print(list(stats.keys()))

with open(
    "match_6106264_raw.json",
    "w",
    encoding="utf-8"
) as file:
    json.dump(
        data,
        file,
        ensure_ascii=False,
        indent=2
    )

print()
print("=" * 60)
print("RAW DATA SAVED")
print("=" * 60)

print("match_6106264_raw.json")

print()
print("TEST FINISHED")

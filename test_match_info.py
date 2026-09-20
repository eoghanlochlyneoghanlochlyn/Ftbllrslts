import json
import re
import xml.etree.ElementTree as ET

import requests

SITEMAP_URL = "https://www.fotmob.com/sitemap/en/matches.xml"

HEADERS = {
"User-Agent": (
"Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
"AppleWebKit/537.36 "
"(KHTML, like Gecko) "
"Chrome/131.0.0.0 Safari/537.36"
),
"Accept": (
"text/html,application/xhtml+xml,"
"application/xml;q=0.9,*/*;q=0.8"
),
"Accept-Language": "en-US,en;q=0.9",
"Referer": "https://www.fotmob.com/",
}

def get(url):
print()
print("=" * 80)
print("GET:", url)

```
response = requests.get(
    url,
    headers=HEADERS,
    timeout=30,
)

print("STATUS:", response.status_code)
print("FINAL URL:", response.url)
print("CONTENT TYPE:", response.headers.get("content-type"))
print("LENGTH:", len(response.text))

response.raise_for_status()

return response.text
```

def local_name(tag):
return tag.rsplit("}", 1)[-1]

def parse_sitemap(text):
root = ET.fromstring(text)

```
print()
print("ROOT:", local_name(root.tag))

sitemap_urls = []
match_urls = []

for element in root:
    element_name = local_name(element.tag)
    loc = None

    for child in element:
        if local_name(child.tag) == "loc":
            loc = (child.text or "").strip()
            break

    if not loc:
        continue

    if element_name == "sitemap":
        sitemap_urls.append(loc)

    elif element_name == "url":
        match_urls.append(loc)

print("CHILD SITEMAPS:", len(sitemap_urls))
print("DIRECT URLS:", len(match_urls))

if sitemap_urls:
    print()
    print("FIRST CHILD SITEMAPS:")

    for url in sitemap_urls[:10]:
        print(" ", url)

if match_urls:
    print()
    print("FIRST DIRECT URLS:")

    for url in match_urls[:10]:
        print(" ", url)

return sitemap_urls, match_urls
```

def extract_next_data(html):
pattern = re.compile(
r"""<script[^>]+id=["']**NEXT_DATA**["'][^>]*>(.*?)</script>""",
re.IGNORECASE | re.DOTALL,
)

```
match = pattern.search(html)

if not match:
    print()
    print("NO __NEXT_DATA__ FOUND")
    return None

raw = match.group(1).strip()

print()
print("__NEXT_DATA__ FOUND")
print("RAW LENGTH:", len(raw))

try:
    data = json.loads(raw)

except Exception as error:
    print("JSON ERROR:", error)
    return None

print("TOP LEVEL KEYS:")

if isinstance(data, dict):
    for key in data.keys():
        print(" ", key)

return data
```

def print_structure(
value,
path="root",
depth=0,
max_depth=3,
):
if depth > max_depth:
return

```
indent = "  " * depth

if isinstance(value, dict):
    print(
        f"{indent}{path} -> dict "
        f"({len(value)} keys)"
    )

    for key, child in list(value.items())[:40]:
        print_structure(
            child,
            f"{path}.{key}",
            depth + 1,
            max_depth,
        )

elif isinstance(value, list):
    print(
        f"{indent}{path} -> list "
        f"({len(value)} items)"
    )

    if value:
        print_structure(
            value[0],
            f"{path}[0]",
            depth + 1,
            max_depth,
        )

else:
    shown = repr(value)

    if len(shown) > 180:
        shown = shown[:180] + "..."

    print(
        f"{indent}{path} -> "
        f"{type(value).__name__}: {shown}"
    )
```

def find_values(
data,
wanted_keys,
path="root",
):
found = []

```
if isinstance(data, dict):

    for key, value in data.items():
        current_path = f"{path}.{key}"

        if key in wanted_keys:
            found.append(
                (
                    current_path,
                    value,
                )
            )

        found.extend(
            find_values(
                value,
                wanted_keys,
                current_path,
            )
        )

elif isinstance(data, list):

    for index, value in enumerate(data):
        found.extend(
            find_values(
                value,
                wanted_keys,
                f"{path}[{index}]",
            )
        )

return found
```

def main():
print("=" * 80)
print("FOTMOB DISCOVERY STRUCTURE TEST")
print("=" * 80)

```
# --------------------------------------------------------------
# 1. Main sitemap
# --------------------------------------------------------------

main_text = get(SITEMAP_URL)

sitemap_urls, direct_urls = parse_sitemap(
    main_text
)

match_url = None

# --------------------------------------------------------------
# 2. Find a real match URL
# --------------------------------------------------------------

if sitemap_urls:

    child_url = sitemap_urls[0]

    print()
    print("=" * 80)
    print("INSPECTING FIRST CHILD SITEMAP")
    print("=" * 80)

    child_text = get(child_url)

    child_sitemaps, child_match_urls = parse_sitemap(
        child_text
    )

    if child_match_urls:

        match_url = child_match_urls[0]

    elif child_sitemaps:

        print()
        print(
            "FIRST CHILD IS ITSELF A SITEMAP INDEX"
        )

        second_url = child_sitemaps[0]

        second_text = get(second_url)

        _, second_match_urls = parse_sitemap(
            second_text
        )

        if second_match_urls:

            match_url = second_match_urls[0]

        else:

            print(
                "NO MATCH URL FOUND IN SECOND LEVEL"
            )

            return

    else:

        print(
            "NO MATCH URL FOUND IN FIRST CHILD"
        )

        return

elif direct_urls:

    match_url = direct_urls[0]

else:

    print()
    print("NO SITEMAP URL FOUND")

    return

# --------------------------------------------------------------
# 3. Inspect real match page
# --------------------------------------------------------------

print()
print("=" * 80)
print("INSPECTING REAL MATCH PAGE")
print("=" * 80)

print("MATCH URL:")
print(match_url)

match_html = get(match_url)

# --------------------------------------------------------------
# 4. Extract __NEXT_DATA__
# --------------------------------------------------------------

data = extract_next_data(match_html)

if data is None:
    return

# --------------------------------------------------------------
# 5. Print structure
# --------------------------------------------------------------

print()
print("=" * 80)
print("NEXT DATA STRUCTURE")
print("=" * 80)

print_structure(
    data,
    max_depth=3,
)

# --------------------------------------------------------------
# 6. Search important keys
# --------------------------------------------------------------

print()
print("=" * 80)
print("IMPORTANT VALUES")
print("=" * 80)

wanted_keys = {
    "matchId",
    "matchID",
    "match_id",
    "homeTeam",
    "awayTeam",
    "matchTimeUTC",
    "matchTime",
    "startTime",
    "utcTime",
    "tournament",
    "league",
    "competition",
    "uniqueTournament",
    "leagueId",
    "tournamentId",
    "uniqueTournamentId",
    "competitionId",
    "parentLeagueId",
    "stage",
    "round",
    "roundName",
    "tournamentStage",
}

found = find_values(
    data,
    wanted_keys,
)

for path, value in found:

    if isinstance(value, (dict, list)):

        try:
            shown = json.dumps(
                value,
                ensure_ascii=False,
            )

        except Exception:

            shown = repr(value)

    else:

        shown = repr(value)

    if len(shown) > 1000:
        shown = shown[:1000] + "..."

    print()
    print(path)
    print(shown)

print()
print("=" * 80)
print("TEST FINISHED")
print("=" * 80)
```

if **name** == "**main**":
main()

import json
import re
import sys
from datetime import datetime, timedelta, timezone
from urllib.parse import urlparse

import requests
import xml.etree.ElementTree as ET

FOTMOB_BASE_URL = "https://www.fotmob.com"
SITEMAP_INDEX_URL = "https://www.fotmob.com/sitemap/en/matches.xml"

HEADERS = {
"User-Agent": (
"Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
"AppleWebKit/537.36 "
"(KHTML, like Gecko) "
"Chrome/131.0.0.0 Safari/537.36"
),
"Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
"Accept-Language": "en-US,en;q=0.9",
"Referer": "https://www.fotmob.com/",
"Cache-Control": "no-cache",
"Pragma": "no-cache",
}

SESSION = requests.Session()
SESSION.headers.update(HEADERS)

REQUEST_TIMEOUT = 30

def get_xml(url):
response = SESSION.get(url, timeout=REQUEST_TIMEOUT)
response.raise_for_status()
return response.text

def get_sitemap_urls(xml_text):
root = ET.fromstring(xml_text)

```
urls = []

for element in root.iter():
    if element.tag.endswith("loc") and element.text:
        urls.append(element.text.strip())

return urls
```

def extract_next_data(html):
match = re.search(
r'<script[^>]+id=["']**NEXT_DATA**["'][^>]*>(.*?)</script>',
html,
re.DOTALL | re.IGNORECASE,
)

```
if not match:
    return None

try:
    return json.loads(match.group(1))
except json.JSONDecodeError:
    return None
```

def get_page_props(root):
if not isinstance(root, dict):
return {}

```
props = root.get("props")

if not isinstance(props, dict):
    return {}

page_props = props.get("pageProps")

if not isinstance(page_props, dict):
    return {}

return page_props
```

def get_general(page_props):
general = page_props.get("general")

```
if isinstance(general, dict):
    return general

data = page_props.get("data")

if isinstance(data, dict):
    general = data.get("general")

    if isinstance(general, dict):
        return general

return {}
```

def get_content(page_props):
candidates = [
page_props.get("content"),
page_props.get("data", {}).get("content")
if isinstance(page_props.get("data"), dict)
else None,
page_props.get("match", {}).get("content")
if isinstance(page_props.get("match"), dict)
else None,
page_props.get("matchData"),
]

```
for candidate in candidates:
    if isinstance(candidate, dict):
        return candidate

return {}
```

def get_team_name(team):
if not isinstance(team, dict):
return None

```
for key in (
    "longName",
    "name",
    "shortName",
    "title",
):
    value = team.get(key)

    if value:
        return str(value)

return None
```

def get_team_id(team):
if not isinstance(team, dict):
return None

```
for key in (
    "id",
    "teamId",
    "teamID",
    "team_id",
):
    value = team.get(key)

    if value is not None:
        return str(value)

return None
```

def get_match_time(general, page_props):
for key in (
"matchTimeUTC",
"matchTime",
"startTime",
"utcTime",
"kickoff",
):
value = general.get(key)

```
    if value:
        return value

# Fallback: بعضی نسخه‌های صفحه ممکن است زمان را جای دیگری داشته باشند.
data = page_props.get("data")

if isinstance(data, dict):
    for key in (
        "matchTimeUTC",
        "matchTime",
        "startTime",
        "utcTime",
        "kickoff",
    ):
        value = data.get(key)

        if value:
            return value

return None
```

def parse_datetime(value):
if value is None:
return None

```
if isinstance(value, (int, float)):
    # FotMob normally uses an ISO string, but support Unix timestamps too.
    if value > 100000000000:
        value = value / 1000

    try:
        return datetime.fromtimestamp(value, tz=timezone.utc)
    except (ValueError, OSError, OverflowError):
        return None

if not isinstance(value, str):
    return None

value = value.strip()

if not value:
    return None

normalized = value.replace("Z", "+00:00")

try:
    parsed = datetime.fromisoformat(normalized)

    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)

    return parsed.astimezone(timezone.utc)

except ValueError:
    pass

# Fallback for common formats.
formats = (
    "%Y-%m-%dT%H:%M:%S.%fZ",
    "%Y-%m-%dT%H:%M:%SZ",
    "%Y-%m-%d %H:%M:%S",
)

for fmt in formats:
    try:
        return datetime.strptime(value, fmt).replace(tzinfo=timezone.utc)
    except ValueError:
        continue

return None
```

def extract_sitemap_timestamp(url):
"""
FotMob match sitemap URLs may contain a timestamp directly after
the match code, for example:

```
.../2grk20/2026-09-20T18:00:00Z

or:

.../2grk202026-09-20T18:00:00Z

This function only uses the timestamp as a candidate-ranking hint.
The final/authoritative time always comes from the match page
__NEXT_DATA__.general.matchTimeUTC.
"""

match = re.search(
    r"(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?Z)",
    url,
)

if not match:
    return None

return parse_datetime(match.group(1))
```

def canonicalize_match_url(url):
"""
Remove any timestamp suffix from a sitemap URL and keep the
canonical /matches/... URL.
"""

```
url = url.strip()

timestamp_match = re.search(
    r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?Z",
    url,
)

if timestamp_match:
    url = url[:timestamp_match.start()]

return url.rstrip("/")
```

def extract_match_id(general):
for key in (
"matchId",
"matchID",
"id",
):
value = general.get(key)

```
    if value is not None:
        return str(value)

return None
```

def extract_league_id(general):
for key in (
"leagueId",
"leagueID",
):
value = general.get(key)

```
    if value is not None:
        return str(value)

return None
```

def extract_parent_league_id(general):
for key in (
"parentLeagueId",
"parentLeagueID",
):
value = general.get(key)

```
    if value is not None:
        return str(value)

return None
```

def extract_stage(content):
match_facts = content.get("matchFacts")

```
if not isinstance(match_facts, dict):
    return None

info_box = match_facts.get("infoBox")

if not isinstance(info_box, dict):
    return None

tournament = info_box.get("Tournament")

if not isinstance(tournament, dict):
    return None

for key in (
    "roundName",
    "round",
    "stage",
    "name",
):
    value = tournament.get(key)

    if value:
        return str(value)

return None
```

def extract_match_info(url):
response = SESSION.get(url, timeout=REQUEST_TIMEOUT)
response.raise_for_status()

```
next_data = extract_next_data(response.text)

if not isinstance(next_data, dict):
    return None

page_props = get_page_props(next_data)

general = get_general(page_props)
content = get_content(page_props)

if not general:
    return None

home_team = general.get("homeTeam")
away_team = general.get("awayTeam")

match_time_raw = get_match_time(general, page_props)
match_time = parse_datetime(match_time_raw)

return {
    "match_id": extract_match_id(general),
    "match_time_utc": match_time.isoformat() if match_time else None,
    "match_time_raw": match_time_raw,
    "home_team": get_team_name(home_team),
    "away_team": get_team_name(away_team),
    "home_team_id": get_team_id(home_team),
    "away_team_id": get_team_id(away_team),
    "league_id": extract_league_id(general),
    "parent_league_id": extract_parent_league_id(general),
    "stage": extract_stage(content),
    "url": url,
}
```

def main():
now = datetime.now(timezone.utc)

```
# From now until exactly 24 hours from now.
window_start = now
window_end = now + timedelta(hours=24)

print("=" * 100)
print("FotMob - ALL MATCHES IN NEXT 24 HOURS")
print("=" * 100)
print()
print(f"Current UTC : {window_start.isoformat()}")
print(f"Window end  : {window_end.isoformat()}")
print()
print("SOURCE: FotMob website sitemap + match HTML + __NEXT_DATA__")
print("NO FotMob API ENDPOINT IS USED.")
print()

print("1) Reading FotMob matches sitemap...")

sitemap_xml = get_xml(SITEMAP_INDEX_URL)
child_sitemaps = get_sitemap_urls(sitemap_xml)

print(f"Child sitemaps found: {len(child_sitemaps)}")
print()

if not child_sitemaps:
    print("ERROR: No child sitemaps found.")
    sys.exit(1)

print("2) Collecting match URLs...")

candidates = {}

for index, child_url in enumerate(child_sitemaps, start=1):
    try:
        child_xml = get_xml(child_url)
        match_urls = get_sitemap_urls(child_xml)

    except Exception as exc:
        print(
            f"[WARNING] Failed child sitemap "
            f"{index}/{len(child_sitemaps)}: {exc}"
        )
        continue

    print(
        f"  sitemap {index:02d}/{len(child_sitemaps):02d}: "
        f"{len(match_urls)} URLs"
    )

    for raw_url in match_urls:
        canonical_url = canonicalize_match_url(raw_url)

        if "/matches/" not in canonical_url:
            continue

        sitemap_time = extract_sitemap_timestamp(raw_url)

        # If the sitemap itself gives us a timestamp, use it to
        # discard obviously irrelevant pages before requesting them.
        if sitemap_time is not None:
            if sitemap_time < window_start - timedelta(hours=2):
                continue

            if sitemap_time > window_end + timedelta(hours=2):
                continue

        candidates[canonical_url] = {
            "url": canonical_url,
            "sitemap_time": sitemap_time,
        }

print()
print(f"Candidate match pages: {len(candidates)}")
print()

if not candidates:
    print("No candidate match pages found.")
    sys.exit(0)

print("3) Reading candidate match pages...")
print()

matches = []

total = len(candidates)

for index, candidate in enumerate(candidates.values(), start=1):
    url = candidate["url"]

    print(f"[{index}/{total}] {url}")

    try:
        info = extract_match_info(url)

    except Exception as exc:
        print(f"    ERROR: {exc}")
        continue

    if not info:
        print("    ERROR: Could not extract __NEXT_DATA__/general.")
        continue

    match_time = parse_datetime(info.get("match_time_raw"))

    if match_time is None:
        print("    SKIP: matchTimeUTC not found.")
        continue

    if not (window_start <= match_time <= window_end):
        print(
            f"    SKIP: outside window "
            f"({match_time.isoformat()})"
        )
        continue

    matches.append(info)

    print(
        f"    FOUND: "
        f"{info.get('home_team')} vs {info.get('away_team')} | "
        f"{match_time.isoformat()} | "
        f"league={info.get('league_id')} | "
        f"stage={info.get('stage')}"
    )

matches.sort(
    key=lambda item: parse_datetime(item.get("match_time_utc"))
    or datetime.max.replace(tzinfo=timezone.utc)
)

print()
print("=" * 100)
print(f"FOUND {len(matches)} MATCHES IN NEXT 24 HOURS")
print("=" * 100)
print()

if not matches:
    print("No matches found in the next 24 hours.")
    return

for index, match in enumerate(matches, start=1):
    print(
        f"{index:03d}. "
        f"{match.get('home_team', '?')} "
        f"vs "
        f"{match.get('away_team', '?')}"
    )

    print(f"     Match ID       : {match.get('match_id')}")
    print(f"     Kickoff UTC    : {match.get('match_time_utc')}")
    print(f"     Home Team ID   : {match.get('home_team_id')}")
    print(f"     Away Team ID   : {match.get('away_team_id')}")
    print(f"     League ID      : {match.get('league_id')}")
    print(f"     Parent League  : {match.get('parent_league_id')}")
    print(f"     Stage          : {match.get('stage')}")
    print(f"     URL            : {match.get('url')}")
    print()

print("=" * 100)
print("JSON OUTPUT")
print("=" * 100)

print(
    json.dumps(
        matches,
        ensure_ascii=False,
        indent=2,
    )
)
```

if **name** == "**main**":
main()

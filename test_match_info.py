import re
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

import requests
from bs4 import BeautifulSoup


FOTMOB_URL = "https://www.fotmob.com/matches"
IRAN_TZ = ZoneInfo("Asia/Tehran")

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/140.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9",
}


def fetch_page(date_value):
    date_str = date_value.strftime("%Y%m%d")
    url = f"{FOTMOB_URL}?date={date_str}"

    print(f"Fetching: {url}")

    response = requests.get(
        url,
        headers=HEADERS,
        timeout=30,
        allow_redirects=True,
    )
    response.raise_for_status()

    print(f"HTTP: {response.status_code} | HTML: {len(response.text):,} bytes")
    return response.text


def clean_text(value):
    return re.sub(r"\s+", " ", value or "").strip()


def decode_rsc(text):
    return (
        text.replace(r"\/", "/")
        .replace(r'\"', '"')
        .replace(r"\\n", "
")
        .replace(r"\\", "\")
    )


def find_rsc_payloads(html):
    soup = BeautifulSoup(html, "html.parser")
    payloads = []

    for script in soup.find_all("script"):
        text = script.string or script.get_text()
        if not text:
            continue

        if "self.__next_f.push" in text or "/match/" in text:
            payloads.append(text)

    return payloads


def diagnostic_rsc(html):
    payloads = find_rsc_payloads(html)
    combined = decode_rsc("\n".join(payloads))

    print()
    print("-" * 100)
    print("RSC / NEXT.JS DIAGNOSTICS")
    print("-" * 100)
    print(f"Relevant script blocks: {len(payloads)}")
    print(f"Combined diagnostic text: {len(combined):,} chars")

    markers = (
        "self.__next_f.push",
        "/match/",
        "matchId",
        "homeTeam",
        "awayTeam",
        "tournament",
        "stage",
        "startTime",
        "utcTime",
    )

    for marker in markers:
        print(f"{marker}: {combined.count(marker)}")

    match_positions = [
        m.start()
        for m in re.finditer(r"/match/", combined)
    ]

    print(f"/match/ occurrences: {len(match_positions)}")

    if match_positions:
        print()
        print("SAMPLES AROUND /match/:")
        for index, position in enumerate(match_positions[:5], 1):
            start = max(0, position - 700)
            end = min(len(combined), position + 1400)
            snippet = clean_text(combined[start:end])
            print()
            print(f"--- SAMPLE {index} ---")
            print(snippet)
    else:
        print()
        print("No /match/ found in relevant script blocks.")

        for marker in ("matchId", "homeTeam", "awayTeam", "tournament"):
            position = combined.find(marker)
            if position != -1:
                start = max(0, position - 500)
                end = min(len(combined), position + 1500)
                print()
                print(f"--- SAMPLE AROUND {marker} ---")
                print(clean_text(combined[start:end]))

    print("-" * 100)
    print()


def extract_match_id(href):
    if not href:
        return None

    patterns = (
        r"/match/[^/?#]+(?:/[^/?#]+)?#(\d+)",
        r"/match/(?:[^/?#]+/)?(\d+)(?:[/?#]|$)",
        r"#(\d+)(?:$|[/?])",
    )

    for pattern in patterns:
        match = re.search(pattern, href)
        if match:
            return match.group(1)

    return None


def find_match_links(html):
    soup = BeautifulSoup(html, "html.parser")
    matches = {}

    for anchor in soup.find_all("a", href=True):
        href = anchor["href"]

        if "/match/" not in href:
            continue

        match_id = extract_match_id(href)

        if not match_id:
            continue

        current = anchor
        context = ""

        for _ in range(8):
            current = current.parent

            if current is None:
                break

            text = clean_text(current.get_text(" ", strip=True))

            if 20 <= len(text) <= 1000:
                context = text
                break

        item = {
            "id": match_id,
            "href": (
                href
                if href.startswith("http")
                else "https://www.fotmob.com" + href
            ),
            "anchor_text": clean_text(
                anchor.get_text(" ", strip=True)
            ),
            "context": context,
        }

        if (
            match_id not in matches
            or len(item["context"]) > len(matches[match_id]["context"])
        ):
            matches[match_id] = item

    return list(matches.values())


def parse_teams(anchor_text, context):
    text = clean_text(anchor_text)

    patterns = (
        r"\s+vs\.?\s+",
        r"\s+v\.?\s+",
        r"\s+[-–]\s+",
    )

    for pattern in patterns:
        parts = re.split(pattern, text, maxsplit=1, flags=re.I)

        if len(parts) == 2:
            return parts[0].strip(), parts[1].strip()

    text = clean_text(context)

    for pattern in patterns:
        parts = re.split(pattern, text, maxsplit=1, flags=re.I)

        if len(parts) == 2:
            return parts[0].strip(), parts[1].strip()

    return text or "نامشخص", ""


def find_stage(text):
    patterns = [
        r"Round of \d+",
        r"Quarter[- ]finals?",
        r"Semi[- ]finals?",
        r"Final",
        r"Group [A-Z0-9]+",
        r"Matchday \d+",
        r"Regular Season",
        r"Play[- ]offs?",
        r"Relegation Play[- ]off",
    ]

    for pattern in patterns:
        match = re.search(pattern, text, re.I)

        if match:
            return match.group(0)

    return "نامشخص"


def find_competition(context, home, away, stage):
    if not context:
        return "نامشخص"

    text = clean_text(context)

    for team in (home, away):
        if team and team != "نامشخص":
            text = re.sub(re.escape(team), " ", text, flags=re.I)

    if stage != "نامشخص":
        text = re.sub(re.escape(stage), " ", text, flags=re.I)

    text = re.sub(r"\b\d{1,2}:\d{2}\b", " ", text)
    text = re.sub(
        r"\b(?:Today|Tomorrow|Yesterday)\b",
        " ",
        text,
        flags=re.I,
    )
    text = re.sub(r"\b\d{1,3}\s*[-–]\s*\d{1,3}\b", " ", text)
    text = clean_text(text)

    return text or "نامشخص"


def parse_match(item):
    home, away = parse_teams(
        item["anchor_text"],
        item["context"],
    )

    combined = clean_text(
        f'{item["anchor_text"]} {item["context"]}'
    )

    stage = find_stage(combined)
    competition = find_competition(
        item["context"],
        home,
        away,
        stage,
    )

    return {
        "id": item["id"],
        "home": home,
        "away": away,
        "competition": competition,
        "stage": stage,
    }


def main():
    now = datetime.now(IRAN_TZ)
    end = now + timedelta(hours=24)

    dates = sorted({now.date(), end.date()})

    print("=" * 100)
    print("FOTMOB — ALL MATCHES NEXT 24 HOURS")
    print("HTML ONLY — NO API")
    print("=" * 100)
    print(f"IRAN NOW:   {now:%Y-%m-%d %H:%M:%S}")
    print(f"IRAN UNTIL: {end:%Y-%m-%d %H:%M:%S}")
    print()

    all_items = []

    for date_value in dates:
        try:
            html = fetch_page(
                datetime.combine(
                    date_value,
                    datetime.min.time(),
                )
            )

            diagnostic_rsc(html)

            items = find_match_links(html)

            print(f"HTML <a> match links found: {len(items)}")
            all_items.extend(items)

        except Exception as exc:
            print(
                f"ERROR for {date_value}: "
                f"{type(exc).__name__}: {exc}"
            )

    unique = {}

    for item in all_items:
        unique[item["id"]] = item

    matches = [
        parse_match(item)
        for item in unique.values()
    ]

    print()
    print("=" * 100)
    print(f"MATCHES FOUND AS HTML LINKS: {len(matches)}")
    print("=" * 100)
    print()

    for index, match in enumerate(matches, 1):
        print(f"{index:03d}. {match['home']}  vs  {match['away']}")
        print(f"     رقابت: {match['competition']}")
        print(f"     مرحله: {match['stage']}")
        print(f"     ID:     {match['id']}")
        print()


if __name__ == "__main__":
    main()

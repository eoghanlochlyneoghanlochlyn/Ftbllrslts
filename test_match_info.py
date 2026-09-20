import json
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
    "Accept": (
        "text/html,application/xhtml+xml,application/xml;"
        "q=0.9,image/avif,image/webp,*/*;q=0.8"
    ),
    "Accept-Language": "en-US,en;q=0.9",
}


def fetch_fotmob_page(date_value):
    date_str = date_value.strftime("%Y%m%d")

    url = f"{FOTMOB_URL}?date={date_str}"

    print()
    print("=" * 100)
    print(f"URL:")
    print(url)
    print("=" * 100)

    response = requests.get(
        url,
        headers=HEADERS,
        timeout=30,
        allow_redirects=True,
    )

    print(f"HTTP STATUS: {response.status_code}")
    print(f"FINAL URL:   {response.url}")
    print(f"HTML SIZE:   {len(response.text):,} bytes")

    response.raise_for_status()

    return response.text


def inspect_html(html):
    print()
    print("=" * 100)
    print("HTML STRUCTURE INSPECTION")
    print("=" * 100)

    soup = BeautifulSoup(html, "html.parser")

    print()
    print("TITLE:")
    print("-" * 100)

    if soup.title:
        print(soup.title.get_text(" ", strip=True))
    else:
        print("NO TITLE")

    print()
    print("SCRIPT TAGS:")
    print("-" * 100)

    scripts = soup.find_all("script")

    print(f"TOTAL SCRIPT TAGS: {len(scripts)}")

    for index, script in enumerate(scripts):
        script_id = script.get("id")
        script_type = script.get("type")
        text = script.string or script.get_text()

        if text is None:
            text = ""

        print(
            f"[SCRIPT {index}] "
            f"id={script_id!r} "
            f"type={script_type!r} "
            f"length={len(text):,}"
        )

    print()
    print("=" * 100)
    print("NEXT.JS / DATA SCRIPTS")
    print("=" * 100)

    candidates = []

    for index, script in enumerate(scripts):

        script_id = script.get("id") or ""
        script_type = script.get("type") or ""
        text = script.string or script.get_text()

        if not text:
            continue

        lower_text = text.lower()

        interesting = False

        if "__next_data__" in script_id.lower():
            interesting = True

        if "next" in script_id.lower():
            interesting = True

        if "buildid" in lower_text:
            interesting = True

        if "match" in lower_text:
            interesting = True

        if "fixture" in lower_text:
            interesting = True

        if "utcTime" in text:
            interesting = True

        if interesting:
            candidates.append(
                {
                    "index": index,
                    "id": script_id,
                    "type": script_type,
                    "text": text,
                }
            )

    print(f"INTERESTING SCRIPTS: {len(candidates)}")

    for item in candidates:

        print()
        print("-" * 100)
        print(
            f"SCRIPT INDEX: {item['index']} | "
            f"ID: {item['id']!r} | "
            f"TYPE: {item['type']!r} | "
            f"LENGTH: {len(item['text']):,}"
        )
        print("-" * 100)

        text = item["text"]

        # فقط اطراف کلیدهای مهم را چاپ می‌کنیم.
        patterns = [
            "__NEXT_DATA__",
            "buildId",
            "utcTime",
            "matchId",
            "homeTeam",
            "awayTeam",
            "matches",
            "fixtures",
        ]

        shown_positions = set()

        for pattern in patterns:

            for match in re.finditer(
                re.escape(pattern),
                text,
                flags=re.IGNORECASE,
            ):
                position = match.start()

                # از چاپ هزاران تکه مشابه جلوگیری می‌کنیم.
                bucket = position // 1000

                if bucket in shown_positions:
                    continue

                shown_positions.add(bucket)

                start = max(0, position - 500)
                end = min(len(text), position + 1500)

                snippet = text[start:end]

                print()
                print(f"### FOUND: {pattern}")
                print(f"### POSITION: {position}")
                print(snippet)

                # برای هر اسکریپت بیشتر از 5 محل نشان نده.
                if len(shown_positions) >= 5:
                    break

            if len(shown_positions) >= 5:
                break

    print()
    print("=" * 100)
    print("HTML ELEMENTS THAT CONTAIN 'MATCH'")
    print("=" * 100)

    # بررسی تگ‌هایی که مستقیماً در متن قابل مشاهده،
    # کلاس یا id آنها به match مربوط است.
    elements = soup.find_all(
        lambda tag: (
            tag.name in ("div", "section", "main", "article", "a")
            and (
                "match" in " ".join(tag.get("class", [])).lower()
                or "match" in str(tag.get("id", "")).lower()
            )
        )
    )

    print(f"MATCH-RELATED HTML ELEMENTS: {len(elements)}")

    for index, element in enumerate(elements[:100]):

        classes = element.get("class", [])
        element_id = element.get("id")

        text = element.get_text(" ", strip=True)

        print()
        print(
            f"[ELEMENT {index}] "
            f"<{element.name}> "
            f"id={element_id!r} "
            f"class={classes!r}"
        )

        if text:
            print(f"TEXT: {text[:500]}")

    print()
    print("=" * 100)
    print("RAW HTML SAMPLE")
    print("=" * 100)

    # فقط ابتدای HTML برای تشخیص ساختار کلی.
    print(html[:10000])


def inspect_json_candidates(html):
    print()
    print("=" * 100)
    print("JSON CANDIDATE INSPECTION")
    print("=" * 100)

    soup = BeautifulSoup(html, "html.parser")

    scripts = soup.find_all("script")

    for index, script in enumerate(scripts):

        text = script.string or script.get_text()

        if not text:
            continue

        text = text.strip()

        if not text:
            continue

        # بررسی JSON کامل
        if text.startswith("{") or text.startswith("["):

            try:
                data = json.loads(text)

            except Exception:
                continue

            print()
            print("-" * 100)
            print(
                f"VALID JSON SCRIPT: {index} | "
                f"TYPE: {script.get('type')!r} | "
                f"ID: {script.get('id')!r}"
            )
            print("-" * 100)

            print_json_structure(data)


def print_json_structure(obj, path="root", depth=0):
    """
    فقط ساختار JSON را چاپ می‌کند.
    خود داده‌های عظیم را چاپ نمی‌کند.
    """

    if depth > 5:
        return

    indent = "  " * depth

    if isinstance(obj, dict):

        keys = list(obj.keys())

        print(
            f"{indent}{path}: "
            f"DICT ({len(keys)} keys)"
        )

        for key in keys[:100]:

            value = obj[key]

            key_lower = str(key).lower()

            important = (
                "match" in key_lower
                or "fixture" in key_lower
                or "team" in key_lower
                or "utc" in key_lower
                or "time" in key_lower
                or "league" in key_lower
                or "event" in key_lower
                or "date" in key_lower
                or "content" in key_lower
                or "props" in key_lower
                or "page" in key_lower
                or "fallback" in key_lower
            )

            if important:
                print_json_structure(
                    value,
                    f"{path}.{key}",
                    depth + 1,
                )

    elif isinstance(obj, list):

        print(
            f"{indent}{path}: "
            f"LIST ({len(obj)} items)"
        )

        for i, value in enumerate(obj[:5]):

            print_json_structure(
                value,
                f"{path}[{i}]",
                depth + 1,
            )

    else:

        value_text = repr(obj)

        if len(value_text) > 300:
            value_text = value_text[:300] + "..."

        print(
            f"{indent}{path}: "
            f"{type(obj).__name__} = {value_text}"
        )


def search_raw_keywords(html):
    print()
    print("=" * 100)
    print("RAW HTML KEYWORD SEARCH")
    print("=" * 100)

    keywords = [
        "utcTime",
        "matchId",
        "homeTeam",
        "awayTeam",
        "home",
        "away",
        "matches",
        "fixtures",
        "fixture",
        "match",
        "timeTS",
        "startTime",
        "kickoff",
        "tournament",
        "league",
    ]

    lower_html = html.lower()

    for keyword in keywords:

        positions = [
            match.start()
            for match in re.finditer(
                re.escape(keyword.lower()),
                lower_html,
            )
        ]

        print(
            f"{keyword:15} -> "
            f"{len(positions)} occurrences"
        )

        if positions:

            # فقط اولین 3 محل.
            for position in positions[:3]:

                start = max(0, position - 300)
                end = min(len(html), position + 700)

                print()
                print(f"  POSITION {position}")
                print("  " + html[start:end].replace("\n", " ")[:1000])


def main():

    now_iran = datetime.now(IRAN_TZ)

    tomorrow = now_iran + timedelta(days=1)

    dates = [
        now_iran,
        tomorrow,
    ]

    print("=" * 100)
    print("FOTMOB HTML STRUCTURE DEBUG TEST")
    print("=" * 100)
    print(f"IRAN TIME: {now_iran:%Y-%m-%d %H:%M:%S}")
    print()

    for date_value in dates:

        try:

            html = fetch_fotmob_page(date_value)

            # ذخیره HTML خام برای بررسی در GitHub Actions
            filename = (
                f"fotmob_debug_"
                f"{date_value:%Y%m%d}.html"
            )

            with open(
                filename,
                "w",
                encoding="utf-8",
            ) as file:
                file.write(html)

            print()
            print(f"RAW HTML SAVED: {filename}")

            inspect_html(html)

            inspect_json_candidates(html)

            search_raw_keywords(html)

        except Exception as exc:

            print()
            print("=" * 100)
            print("ERROR")
            print("=" * 100)

            print(
                f"{type(exc).__name__}: {exc}"
            )

    print()
    print("=" * 100)
    print("DEBUG TEST FINISHED")
    print("=" * 100)


if __name__ == "__main__":
    main()

import re
import sys
from urllib.parse import urljoin

import requests

SITEMAP_URL = "https://www.fotmob.com/sitemap/en/matches.xml"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/131.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Referer": "https://www.fotmob.com/",
}

TIMEOUT = 20
SAMPLE_SIZE = 3


def get(url):
    response = requests.get(
        url,
        headers=HEADERS,
        timeout=TIMEOUT,
        allow_redirects=True,
    )
    response.raise_for_status()
    return response


def extract_urls(xml):
    return re.findall(r"<loc>\\s*(.*?)\\s*</loc>", xml, re.IGNORECASE)


def inspect_json_shape(value, path="root", depth=0, max_depth=4):
    if depth > max_depth:
        return

    if isinstance(value, dict):
        interesting = {
            key: type(item).__name__
            for key, item in value.items()
            if key in {
                "__NEXT_DATA__",
                "pageProps",
                "general",
                "content",
                "header",
                "matchId",
                "matchTimeUTC",
                "homeTeam",
                "awayTeam",
            }
        }

        if interesting:
            print(f"  {path}: {interesting}")

        for key, item in value.items():
            if key in {"pageProps", "general", "content", "header"}:
                inspect_json_shape(item, f"{path}.{key}", depth + 1, max_depth)

    elif isinstance(value, list):
        for index, item in enumerate(value[:3]):
            inspect_json_shape(item, f"{path}[{index}]", depth + 1, max_depth)


def extract_next_data(html):
    match = re.search(
        r'<script[^>]+id=["\']__NEXT_DATA__["\'][^>]*>(.*?)</script>',
        html,
        re.DOTALL | re.IGNORECASE,
    )

    if not match:
        return None

    try:
        import json
        return json.loads(match.group(1))
    except Exception:
        return None


def main():
    print("=" * 90)
    print("FotMob structure test")
    print("Goal: understand real match-page HTML before building the 2026-09-20 discovery")
    print("=" * 90)

    try:
        sitemap = get(SITEMAP_URL)
    except requests.RequestException as exc:
        print(f"ERROR: sitemap request failed: {exc}")
        sys.exit(1)

    print(f"Sitemap status : {sitemap.status_code}")
    print(f"Sitemap URL    : {sitemap.url}")
    print(f"Sitemap length : {len(sitemap.text):,}")
    print()

    urls = [
        url for url in extract_urls(sitemap.text)
        if "/matches/" in url
    ][:SAMPLE_SIZE]

    print(f"Sample match URLs: {len(urls)}")
    for index, url in enumerate(urls, 1):
        print(f"  {index}. {url}")

    if not urls:
        print("ERROR: No /matches/ URLs found in sitemap.")
        sys.exit(1)

    print()

    for index, url in enumerate(urls, 1):
        print("-" * 90)
        print(f"MATCH PAGE {index}")
        print(f"Requested URL : {url}")

        try:
            response = get(url)
        except requests.RequestException as exc:
            print(f"ERROR: {exc}")
            continue

        html = response.text

        print(f"Status        : {response.status_code}")
        print(f"Final URL     : {response.url}")
        print(f"HTML length   : {len(html):,}")
        print(f"__NEXT_DATA__ : {'YES' if '__NEXT_DATA__' in html else 'NO'}")
        print(f"matchFacts    : {'YES' if 'matchFacts' in html else 'NO'}")
        print(f"matchTimeUTC  : {'YES' if 'matchTimeUTC' in html else 'NO'}")
        print(f"homeTeam      : {'YES' if 'homeTeam' in html else 'NO'}")
        print(f"awayTeam      : {'YES' if 'awayTeam' in html else 'NO'}")

        data = extract_next_data(html)

        if data is None:
            print("NEXT_DATA parse: FAILED")
            continue

        print("NEXT_DATA parse: OK")
        inspect_json_shape(data)

    print()
    print("=" * 90)
    print("TEST COMPLETE")
    print("=" * 90)


if __name__ == "__main__":
    main()

import json
import re
import requests


MATCH_ID = "5795447"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 Chrome/131.0 Safari/537.36"
    )
}


def fetch_match_page(match_id):
    url = f"https://www.fotmob.com/match/{match_id}"

    response = requests.get(
        url,
        headers=HEADERS,
        timeout=20,
    )

    print("HTTP status:", response.status_code)

    html = response.text

    match = re.search(
        r'<script id="__NEXT_DATA__" type="application/json">(.*?)</script>',
        html,
        re.DOTALL,
    )

    if not match:
        print("__NEXT_DATA__ not found")
        return None

    return json.loads(match.group(1))


def main():
    data = fetch_match_page(MATCH_ID)

    if not data:
        return

    page = data["props"]["pageProps"]
    content = page.get("content", {})
    lineup = content.get("lineup")

    print()
    print("=" * 80)
    print("LINEUP RAW DATA")
    print("=" * 80)

    print(json.dumps(lineup, ensure_ascii=False, indent=2))

    print()
    print("=" * 80)
    print("CONTENT KEYS")
    print("=" * 80)

    print(list(content.keys()))

    print()
    print("=" * 80)
    print("PAGE KEYS")
    print("=" * 80)

    print(list(page.keys()))


if __name__ == "__main__":
    main()

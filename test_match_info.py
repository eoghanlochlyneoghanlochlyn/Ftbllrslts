import json
import re
import requests


MATCH_ID = "5881169"

URL = f"https://www.fotmob.com/match/{MATCH_ID}"


def fetch_page():
    response = requests.get(
        URL,
        headers={
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/140.0.0.0 Safari/537.36"
            )
        },
        timeout=30,
    )

    print("HTTP status:", response.status_code)

    response.raise_for_status()

    return response.text


def extract_next_data(html):
    match = re.search(
        r'<script id="__NEXT_DATA__" type="application/json">(.*?)</script>',
        html,
        re.DOTALL,
    )

    if not match:
        print("ERROR: __NEXT_DATA__ not found.")
        return None

    return json.loads(match.group(1))


def main():
    print("=" * 70)
    print("UNION BERLIN vs SCHALKE 04")
    print("Match ID:", MATCH_ID)
    print("=" * 70)

    html = fetch_page()
    data = extract_next_data(html)

    if not data:
        return

    content = (
        data
        .get("props", {})
        .get("pageProps", {})
        .get("content", {})
    )

    lineup = content.get("lineup")

    if not isinstance(lineup, dict):
        print("\nNO LINEUP OBJECT FOUND")
        return

    print("\nLINEUP OBJECT FOUND")
    print("-" * 70)

    print("lineupType:", repr(lineup.get("lineupType")))
    print("source:", repr(lineup.get("source")))
    print("matchId:", repr(lineup.get("matchId")))

    print("\nLINEUP KEYS:")
    print(list(lineup.keys()))

    home = lineup.get("homeTeam") or {}
    away = lineup.get("awayTeam") or {}

    print("\nHOME TEAM")
    print("-" * 70)
    print("ID:", home.get("id"))
    print("Name:", home.get("name"))
    print("Formation:", home.get("formation"))
    print("Starters:", len(home.get("starters") or []))
    print("Subs:", len(home.get("subs") or []))
    print("Coach:", home.get("coach"))

    print("\nAWAY TEAM")
    print("-" * 70)
    print("ID:", away.get("id"))
    print("Name:", away.get("name"))
    print("Formation:", away.get("formation"))
    print("Starters:", len(away.get("starters") or []))
    print("Subs:", len(away.get("subs") or []))
    print("Coach:", away.get("coach"))

    print("\nHOME STARTERS")
    print("-" * 70)

    for player in home.get("starters") or []:
        print(json.dumps(player, ensure_ascii=False, indent=2))

    print("\nAWAY STARTERS")
    print("-" * 70)

    for player in away.get("starters") or []:
        print(json.dumps(player, ensure_ascii=False, indent=2))

    print("\nFULL LINEUP JSON")
    print("-" * 70)

    print(
        json.dumps(
            lineup,
            ensure_ascii=False,
            indent=2,
        )
    )

    with open(
        "union_lineup_output.json",
        "w",
        encoding="utf-8",
    ) as f:
        json.dump(
            lineup,
            f,
            ensure_ascii=False,
            indent=2,
        )

    print("\n" + "=" * 70)
    print("TEST COMPLETED.")
    print("Saved: union_lineup_output.json")
    print("=" * 70)


if __name__ == "__main__":
    main()

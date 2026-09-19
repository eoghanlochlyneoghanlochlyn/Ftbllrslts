import json
import re

import requests


MATCH_ID = "5161863"

MATCH_URL = (
    "https://www.fotmob.com/matches/"
    "monaco-vs-paris-saint-germain/379cod#5161863"
)


def find_key(obj, target_key, path="root"):
    if isinstance(obj, dict):
        for key, value in obj.items():
            current_path = f"{path}.{key}"

            if key == target_key:
                yield current_path, value

            yield from find_key(value, target_key, current_path)

    elif isinstance(obj, list):
        for index, value in enumerate(obj):
            current_path = f"{path}[{index}]"
            yield from find_key(value, target_key, current_path)


def extract_next_data(html):
    match = re.search(
        r'<script id="__NEXT_DATA__" type="application/json">(.*?)</script>',
        html,
        re.DOTALL,
    )

    if not match:
        raise RuntimeError("__NEXT_DATA__ was not found.")

    return json.loads(match.group(1))


def print_json(title, value, limit=30000):
    print(f"\n========== {title} ==========")

    text = json.dumps(
        value,
        ensure_ascii=False,
        indent=2,
    )

    print(text[:limit])

    if len(text) > limit:
        print("\n... OUTPUT TRUNCATED ...")


def main():
    print("Match ID:", MATCH_ID)
    print("Match URL:", MATCH_URL)

    response = requests.get(
        MATCH_URL,
        timeout=45,
        headers={
            "User-Agent": "Mozilla/5.0",
        },
    )

    print("\nHTTP status:", response.status_code)
    print("Response length:", len(response.text))

    response.raise_for_status()

    data = extract_next_data(response.text)

    # ---------------------------------------------------------
    # Tournament
    # ---------------------------------------------------------

    print("\n\n========== TOURNAMENT ==========")

    tournament_results = list(find_key(data, "Tournament"))

    print("Tournament objects found:", len(tournament_results))

    for index, (path, value) in enumerate(tournament_results, 1):
        print(f"\n--- Tournament #{index} ---")
        print("Path:", path)

        if isinstance(value, dict):
            print_json("Tournament object", value)
        else:
            print("Value:", repr(value))

    # ---------------------------------------------------------
    # Round-related fields
    # ---------------------------------------------------------

    interesting_keys = (
        "round",
        "roundName",
        "roundId",
        "localizedKey",
        "stage",
        "stageName",
        "phase",
        "phaseName",
        "leg",
        "legNumber",
        "legName",
    )

    print("\n\n========== ROUND / STAGE / PHASE ==========")

    for key in interesting_keys:
        results = list(find_key(data, key))

        if not results:
            continue

        print(f"\n========== KEY: {key} ==========")
        print("Occurrences:", len(results))

        for path, value in results[:20]:
            print("\nPath:", path)
            print("Value:", repr(value))

    # ---------------------------------------------------------
    # InfoBox
    # ---------------------------------------------------------

    print("\n\n========== INFOBOX ==========")

    match_facts_results = list(find_key(data, "matchFacts"))

    print("matchFacts found:", len(match_facts_results))

    for path, value in match_facts_results[:5]:
        print("\nPath:", path)

        if not isinstance(value, dict):
            continue

        info_box = value.get("infoBox")

        if info_box is not None:
            print_json("infoBox", info_box)

    # ---------------------------------------------------------
    # DONE
    # ---------------------------------------------------------

    print("\n\n========== DONE ==========")


if __name__ == "__main__":
    main()

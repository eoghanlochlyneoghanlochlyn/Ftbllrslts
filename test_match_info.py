import json
import re

import requests


MATCH_ID = "5161863"
MATCH_URL = "https://www.fotmob.com/matches/monaco-vs-paris-saint-germain/379cod#5161863"


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


def print_matches(title, results, limit=10):
    print(f"\n========== {title} ==========")
    print("Found:", len(results))

    for index, (path, value) in enumerate(results[:limit], 1):
        print(f"\n--- {title} #{index} ---")
        print("Path:", path)

        if isinstance(value, (dict, list)):
            print(json.dumps(value, ensure_ascii=False, indent=2)[:12000])
        else:
            print("Value:", repr(value))


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

    print("\n========== NEXT_DATA ROOT KEYS ==========")
    print(list(data.keys()))

    print_matches("fixtureInfo", list(find_key(data, "fixtureInfo")))
    print_matches("activeRound", list(find_key(data, "activeRound")))
    print_matches("rounds", list(find_key(data, "rounds")))
    print_matches("roundName", list(find_key(data, "roundName")))
    print_matches("round", list(find_key(data, "round")))
    print_matches("stage", list(find_key(data, "stage")))
    print_matches("stageName", list(find_key(data, "stageName")))
    print_matches("phase", list(find_key(data, "phase")))
    print_matches("phaseName", list(find_key(data, "phaseName")))
    print_matches("leg", list(find_key(data, "leg")))
    print_matches("aggregate", list(find_key(data, "aggregate")))
    print_matches("playoff", list(find_key(data, "playoff")))
    print_matches("matchInfo", list(find_key(data, "matchInfo")))

    print("\n========== POSSIBLE COMPETITION/MATCH OBJECTS ==========")

    for key in (
        "header",
        "content",
        "matchFacts",
        "competition",
        "tournament",
        "fixture",
    ):
        results = list(find_key(data, key))

        if results:
            print(f"\nKEY {key}: {len(results)} occurrence(s)")

            for path, value in results[:5]:
                print("Path:", path)

                if isinstance(value, dict):
                    interesting = {
                        k: v
                        for k, v in value.items()
                        if any(
                            token in k.lower()
                            for token in (
                                "round",
                                "stage",
                                "phase",
                                "leg",
                                "aggregate",
                                "competition",
                                "tournament",
                                "fixture",
                            )
                        )
                    }

                    if interesting:
                        print(
                            json.dumps(
                                interesting,
                                ensure_ascii=False,
                                indent=2,
                            )[:8000]
                        )

    print("\n========== DONE ==========")


if __name__ == "__main__":
    main()

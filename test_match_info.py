import json
import re
import requests


MATCHES = {
    "Napoli-Bologna": {
        "id": "6106331",
        "url": "https://www.fotmob.com/matches/roma-vs-fenerbahce/2hxw0m#6106331",
    },
    "Pisa-Roma": {
        "id": "6106254",
        "url": "https://www.fotmob.com/matches/manchester-city-vs-paris-saint-germain/2rqiev#6106254",
    },
}


def extract_next_data(html):
    match = re.search(
        r'<script id="__NEXT_DATA__" type="application/json">(.*?)</script>',
        html,
        re.DOTALL,
    )

    if not match:
        return None

    try:
        return json.loads(match.group(1))
    except Exception:
        return None


def find_relevant_fields(node, path="root", results=None):
    if results is None:
        results = []

    if isinstance(node, dict):

        for key, value in node.items():

            key_lower = str(key).lower()

            if any(
                word in key_lower
                for word in (
                    "round",
                    "week",
                    "stage",
                    "matchday",
                    "match_day",
                    "roundnumber",
                    "roundname",
                    "weeknumber",
                    "weekname",
                    "stagename",
                )
            ):
                results.append(
                    {
                        "path": f"{path}.{key}",
                        "value": value,
                    }
                )

            if isinstance(value, (dict, list)):
                find_relevant_fields(
                    value,
                    f"{path}.{key}",
                    results,
                )

    elif isinstance(node, list):

        for index, item in enumerate(node):

            if isinstance(item, (dict, list)):
                find_relevant_fields(
                    item,
                    f"{path}[{index}]",
                    results,
                )

    return results


def main():

    for match_name, match_info in MATCHES.items():

        match_id = match_info["id"]
        url = match_info["url"]

        print()
        print("=" * 80)
        print(match_name)
        print(f"FotMob ID: {match_id}")
        print(f"URL: {url}")
        print("=" * 80)

        try:

            response = requests.get(
                url,
                headers={
                    "User-Agent": (
                        "Mozilla/5.0 "
                        "(Windows NT 10.0; Win64; x64) "
                        "AppleWebKit/537.36 "
                        "(KHTML, like Gecko) "
                        "Chrome/140.0 Safari/537.36"
                    )
                },
                timeout=30,
            )

            print(
                f"HTTP status: {response.status_code}"
            )

            print(
                f"Response length: {len(response.text)}"
            )

            if response.status_code != 200:
                print("صفحه معتبر دریافت نشد.")
                continue

        except Exception as exc:

            print(
                f"Request error: {exc}"
            )

            continue

        data = extract_next_data(
            response.text
        )

        if not isinstance(data, dict):

            print(
                "NEXT_DATA پیدا نشد."
            )

            continue

        results = find_relevant_fields(
            data
        )

        print()

        if not results:

            print(
                "هیچ فیلد مرتبط با "
                "round/week/stage/matchday پیدا نشد."
            )

            continue

        print(
            f"تعداد موارد پیدا شده: {len(results)}"
        )

        print()

        for item in results:

            print(
                f"PATH: {item['path']}"
            )

            print(
                "VALUE:"
            )

            try:

                print(
                    json.dumps(
                        item["value"],
                        ensure_ascii=False,
                        indent=2,
                    )
                )

            except Exception:

                print(
                    repr(item["value"])
                )

            print("-" * 80)


if __name__ == "__main__":
    main()

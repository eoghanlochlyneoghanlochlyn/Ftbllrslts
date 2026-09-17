import json
import re

import requests


MATCHES = [
    "https://www.fotmob.com/matches/esteghlal-vs-al-sadd/9ih3qny#6050065",
    "https://www.fotmob.com/matches/hapoel-beer-sheva-vs-dinamo-zagreb/3a0mfj#6112363",
    "https://www.fotmob.com/matches/brighton-hove-albion-vs-manchester-united/3goccs#6099329",
    "https://www.fotmob.com/matches/nottingham-forest-vs-aston-villa/3gke9k#5206176",
    "https://www.fotmob.com/matches/arsenal-vs-crystal-palace/36ytc8#5034192",
    "https://www.fotmob.com/matches/vissel-kobe-vs-al-sadd/2lxqo1w#5336423",
]


HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 "
        "(KHTML, like Gecko) "
        "Chrome/131.0.0.0 Safari/537.36"
    )
}


INTERESTING_KEYS = {
    "id",
    "name",
    "shortName",
    "slug",
    "tournamentId",
    "tournamentID",
    "leagueId",
    "leagueID",
    "uniqueTournamentId",
    "uniqueTournamentID",
    "competitionId",
    "competitionID",
    "seasonId",
    "seasonID",
    "stageId",
    "stageID",
    "roundId",
    "roundID",
    "parentTournament",
    "parent",
    "season",
    "stage",
    "round",
    "tournament",
    "league",
    "competition",
}


INTERESTING_NAMES = {
    "premier league",
    "europa league",
    "efl cup",
    "afc champions league elite",
    "afc champions league",
    "champions league",
    "final stage",
    "league phase",
    "knockout phase",
    "round of 16",
    "quarter-finals",
    "quarterfinals",
    "semi-finals",
    "semifinals",
    "final",
}


def extract_match_id(match_url):
    match = re.search(
        r"#(\d+)",
        match_url,
    )

    if match:
        return match.group(1)

    match = re.search(
        r"/matches/[^/]+/[^#]+",
        match_url,
    )

    if match:
        return match.group(0).split("/")[-1]

    return "unknown"


def fetch_next_data(match_url):
    response = requests.get(
        match_url,
        headers=HEADERS,
        timeout=30,
    )

    response.raise_for_status()

    html = response.text

    match = re.search(
        r'<script id="__NEXT_DATA__" type="application/json">(.*?)</script>',
        html,
        re.DOTALL,
    )

    if not match:
        raise RuntimeError(
            "__NEXT_DATA__ پیدا نشد."
        )

    return json.loads(
        match.group(1)
    )


def normalize_text(value):
    if not isinstance(
        value,
        str,
    ):
        return ""

    return (
        value
        .strip()
        .lower()
        .replace(
            "-",
            " ",
        )
        .replace(
            "_",
            " ",
        )
    )


def is_interesting_dict(data):
    if not isinstance(
        data,
        dict,
    ):
        return False

    keys = {
        str(key)
        for key in data.keys()
    }

    if keys.intersection(
        INTERESTING_KEYS
    ):
        return True

    for key, value in data.items():
        if isinstance(
            value,
            str,
        ):
            normalized = normalize_text(
                value
            )

            if normalized in INTERESTING_NAMES:
                return True

    return False


def compact_value(value):
    if isinstance(
        value,
        (
            str,
            int,
            float,
            bool,
        ),
    ) or value is None:
        return value

    if isinstance(
        value,
        list,
    ):
        return [
            compact_value(item)
            for item in value
        ]

    if isinstance(
        value,
        dict,
    ):
        result = {}

        for key, item in value.items():
            if (
                key in INTERESTING_KEYS
                or isinstance(
                    item,
                    (
                        str,
                        int,
                        float,
                        bool,
                    ),
                )
            ):
                result[key] = compact_value(
                    item
                )

        return result

    return str(value)


def print_interesting_objects(
    data,
    path="$",
    depth=0,
    max_depth=12,
):
    if depth > max_depth:
        return

    if isinstance(
        data,
        dict,
    ):

        if is_interesting_dict(
            data
        ):
            print()
            print("-" * 100)
            print(
                "PATH:",
                path,
            )
            print(
                "OBJECT:"
            )
            print(
                json.dumps(
                    compact_value(data),
                    ensure_ascii=False,
                    indent=2,
                )
            )

        for key, value in data.items():
            print_interesting_objects(
                value,
                path=f"{path}.{key}",
                depth=depth + 1,
                max_depth=max_depth,
            )

    elif isinstance(
        data,
        list,
    ):

        for index, value in enumerate(
            data
        ):
            print_interesting_objects(
                value,
                path=f"{path}[{index}]",
                depth=depth + 1,
                max_depth=max_depth,
            )


def find_named_objects(
    data,
    path="$",
    depth=0,
    max_depth=12,
):
    if depth > max_depth:
        return

    if isinstance(
        data,
        dict,
    ):

        matched_names = []

        for key, value in data.items():
            if not isinstance(
                value,
                str,
            ):
                continue

            normalized = normalize_text(
                value
            )

            if normalized in INTERESTING_NAMES:
                matched_names.append(
                    (
                        key,
                        value,
                    )
                )

        if matched_names:
            print()
            print("#" * 100)
            print(
                "NAMED OBJECT PATH:",
                path,
            )
            print(
                "MATCHED NAMES:",
                matched_names,
            )
            print(
                "FULL OBJECT:"
            )
            print(
                json.dumps(
                    data,
                    ensure_ascii=False,
                    indent=2,
                )
            )

        for key, value in data.items():
            find_named_objects(
                value,
                path=f"{path}.{key}",
                depth=depth + 1,
                max_depth=max_depth,
            )

    elif isinstance(
        data,
        list,
    ):

        for index, value in enumerate(
            data
        ):
            find_named_objects(
                value,
                path=f"{path}[{index}]",
                depth=depth + 1,
                max_depth=max_depth,
            )


def main():
    for index, match_url in enumerate(
        MATCHES,
        start=1,
    ):

        print()
        print()
        print("=" * 120)
        print(
            f"TEST {index}/{len(MATCHES)}"
        )
        print(
            "URL:",
            match_url,
        )
        print("=" * 120)

        try:
            data = fetch_next_data(
                match_url
            )

        except Exception as error:
            print(
                "ERROR:",
                repr(error),
            )
            continue

        print()
        print("========== ALL INTERESTING OBJECTS ==========")

        print_interesting_objects(
            data
        )

        print()
        print("========== OBJECTS WITH COMPETITION/STAGE NAMES ==========")

        find_named_objects(
            data
        )

        print()
        print("=" * 120)
        print(
            f"END TEST {index}"
        )
        print("=" * 120)


if __name__ == "__main__":
    main()

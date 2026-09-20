import json
import requests

from collections import defaultdict
from datetime import datetime
from zoneinfo import ZoneInfo


IRAN_TZ = ZoneInfo("Asia/Tehran")

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/140.0.0.0 Safari/537.36"
    )
}

TARGET_KEYS = (
    "stage",
    "round",
    "phase",
    "leg",
    "aggregate",
    "matchday",
    "matchweek",
    "tournamentstage",
)


def utc_to_iran(utc_time):
    if not utc_time:
        return "Unknown"

    try:
        dt = datetime.fromisoformat(utc_time.replace("Z", "+00:00"))
        return dt.astimezone(IRAN_TZ).strftime("%Y-%m-%d %H:%M")
    except Exception:
        return "Unknown"


def get_team_name(team):
    if not isinstance(team, dict):
        return "Unknown"

    return (
        team.get("longName")
        or team.get("name")
        or team.get("shortName")
        or "Unknown"
    )


def fetch_matches_for_date(date):
    url = f"https://www.fotmob.com/api/data/matches?date={date}"

    print()
    print(f"Downloading matches for {date}...")

    response = requests.get(url, headers=HEADERS, timeout=30)

    print("Status code:", response.status_code)
    response.raise_for_status()

    return response.json()


def load_target_competitions():
    with open("auto_matches.json", "r", encoding="utf-8") as file:
        config = json.load(file)

    return {
        str(item["id"]): item
        for item in config.get("competitions", [])
        if item.get("id") is not None
    }


def find_relevant_fields(value, path=""):
    found = []

    if isinstance(value, dict):
        for key, child in value.items():
            child_path = f"{path}.{key}" if path else key
            key_lower = str(key).lower()

            if any(target in key_lower for target in TARGET_KEYS):
                found.append((child_path, child))

            found.extend(find_relevant_fields(child, child_path))

    elif isinstance(value, list):
        for index, child in enumerate(value):
            found.extend(find_relevant_fields(child, f"{path}[{index}]"))

    return found


def clean_value(value):
    if isinstance(value, (dict, list)):
        return json.dumps(value, ensure_ascii=False, sort_keys=True)
    return str(value)


def main():
    now_iran = datetime.now(IRAN_TZ)
    date = now_iran.strftime("%Y%m%d")

    data = fetch_matches_for_date(date)
    target_competitions = load_target_competitions()

    total_matches = 0
    target_matches = 0
    competition_stage_values = defaultdict(set)
    printed_league_structures = set()
    printed_match_structures = set()

    for league in data.get("leagues", []):
        league_name = league.get("name", "Unknown League")
        league_id = (
            league.get("primaryId")
            or league.get("id")
            or league.get("leagueId")
            or league.get("competitionId")
        )

        league_id_str = str(league_id)

        for match in league.get("matches", []):
            total_matches += 1

            if league_id_str not in target_competitions:
                continue

            target_matches += 1
            stage = match.get("tournamentStage", "MISSING")
            competition_stage_values[league_id_str].add(str(stage))

            if league_id_str not in printed_league_structures:
                printed_league_structures.add(league_id_str)

                print()
                print("=" * 110)
                print(
                    f"TARGET COMPETITION: {league_name} "
                    f"(competition ID: {league_id_str})"
                )
                print("League-level relevant fields:")
                league_fields = find_relevant_fields(league)

                if league_fields:
                    for path, value in league_fields[:100]:
                        print(f"  {path} = {clean_value(value)}")
                else:
                    print("  NONE")

                print("League top-level keys:")
                print("  " + ", ".join(sorted(league.keys())))
                print("=" * 110)

            if len(printed_match_structures) < 20:
                match_key = (league_id_str, str(match.get("id")))
                if match_key not in printed_match_structures:
                    printed_match_structures.add(match_key)

                    print()
                    print(
                        f"Match: {get_team_name(match.get('home'))} vs "
                        f"{get_team_name(match.get('away'))} "
                        f"| id={match.get('id')}"
                    )
                    print(f"tournamentStage = {stage!r}")

                    match_fields = find_relevant_fields(match)

                    if match_fields:
                        print("Match-level relevant fields:")
                        for path, value in match_fields[:100]:
                            print(f"  {path} = {clean_value(value)}")
                    else:
                        print("Match-level relevant fields: NONE")

    print()
    print("=" * 110)
    print("TARGET COMPETITION STAGE MAPPING TEST")
    print("=" * 110)
    print("Iran now:", now_iran.strftime("%Y-%m-%d %H:%M:%S"))
    print("Date:", date)
    print("Total matches in endpoint:", total_matches)
    print("Target competitions configured:", len(target_competitions))
    print("Target matches found today:", target_matches)
    print("=" * 110)

    print()
    print("Observed tournamentStage values by target competition:")
    print("-" * 110)

    for competition_id, values in sorted(competition_stage_values.items()):
        config = target_competitions.get(competition_id, {})
        print(
            f"competition={competition_id} | "
            f"mode={config.get('mode')} | "
            f"configured_stage={config.get('stage')} | "
            f"values={sorted(values)}"
        )

    missing_targets = [
        competition_id
        for competition_id in target_competitions
        if competition_id not in competition_stage_values
    ]

    print()
    print("Configured competitions with no match today:")
    if missing_targets:
        print("  " + ", ".join(sorted(missing_targets)))
    else:
        print("  NONE")

    print()
    print("=" * 110)
    print("END OF TARGET STAGE MAPPING TEST")
    print("=" * 110)


if __name__ == "__main__":
    main()

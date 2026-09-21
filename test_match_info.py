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


def fetch_matches_for_date(date):
    url = f"https://www.fotmob.com/api/data/matches?date={date}"

    print()
    print(f"Downloading matches for {date}...")

    response = requests.get(url, headers=HEADERS, timeout=30)

    print("Status code:", response.status_code)
    response.raise_for_status()

    return response.json()


def clean(value):
    if isinstance(value, (dict, list)):
        return json.dumps(value, ensure_ascii=False, sort_keys=True)
    return str(value)


def utc_to_iran(value):
    if not value:
        return "Unknown"
    try:
        dt = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
        return dt.astimezone(IRAN_TZ).strftime("%Y-%m-%d %H:%M")
    except Exception:
        return "Unknown"


def collect_id_like(obj, prefix=""):
    result = {}

    if isinstance(obj, dict):
        for key, value in obj.items():
            key_text = str(key)
            path = f"{prefix}.{key_text}" if prefix else key_text

            if "id" in key_text.lower() and not isinstance(value, (dict, list)):
                result[path] = value

            if isinstance(value, (dict, list)):
                result.update(collect_id_like(value, path))

    elif isinstance(obj, list):
        for index, value in enumerate(obj):
            if isinstance(value, (dict, list)):
                result.update(collect_id_like(value, f"{prefix}[{index}]"))

    return result


def collect_named_objects(obj, names=("tournament", "league", "competition")):
    found = []

    if isinstance(obj, dict):
        for key, value in obj.items():
            if key.lower() in names and isinstance(value, dict):
                found.append((key, value))

            if isinstance(value, (dict, list)):
                found.extend(collect_named_objects(value, names))

    elif isinstance(obj, list):
        for value in obj:
            if isinstance(value, (dict, list)):
                found.extend(collect_named_objects(value, names))

    return found


def get_match_name(match):
    home = match.get("home", {})
    away = match.get("away", {})

    home_name = (
        home.get("longName")
        or home.get("name")
        or home.get("shortName")
        or "Unknown"
    )
    away_name = (
        away.get("longName")
        or away.get("name")
        or away.get("shortName")
        or "Unknown"
    )

    return f"{home_name} vs {away_name}"


def league_identity(league):
    identity = {
        "name": league.get("name"),
        "slug": league.get("slug"),
        "country": league.get("country"),
        "type": league.get("type"),
    }

    for key in (
        "id",
        "primaryId",
        "parentLeagueId",
        "leagueId",
        "competitionId",
        "tournamentId",
    ):
        if key in league:
            identity[key] = league[key]

    nested = collect_named_objects(league)
    for object_name, obj in nested:
        for key in (
            "id",
            "primaryId",
            "parentLeagueId",
            "leagueId",
            "competitionId",
            "tournamentId",
        ):
            if key in obj:
                identity[f"{object_name}.{key}"] = obj[key]

        for key in ("name", "slug", "country", "type"):
            if key in obj and f"{object_name}.{key}" not in identity:
                identity[f"{object_name}.{key}"] = obj[key]

    return identity


def main():
    now_iran = datetime.now(IRAN_TZ)
    date = now_iran.strftime("%Y%m%d")

    data = fetch_matches_for_date(date)
    leagues = data.get("leagues", [])
    total_matches = sum(len(league.get("matches", [])) for league in leagues)

    with open("auto_matches.json", "r", encoding="utf-8") as file:
        config = json.load(file)

    configured = []
    for item in config.get("competitions", []):
        if item.get("id") is not None:
            configured.append(item)

    configured_ids = {str(item["id"]) for item in configured}

    print()
    print("=" * 120)
    print("FOTMOB COMPETITION CANONICAL ID DISCOVERY")
    print("=" * 120)
    print("Iran now:", now_iran.strftime("%Y-%m-%d %H:%M:%S"))
    print("Date:", date)
    print("Leagues:", len(leagues))
    print("Total matches:", total_matches)
    print("Configured IDs:", ", ".join(sorted(configured_ids, key=lambda x: (len(x), x))))

    print()
    print("=" * 120)
    print("TODAY'S COMPETITIONS — CANONICAL ID STRUCTURE")
    print("=" * 120)

    all_records = []

    for league in leagues:
        matches = league.get("matches", [])
        identity = league_identity(league)

        # Also inspect the first match because some competition metadata lives there.
        if matches:
            match = matches[0]
            match_ids = collect_id_like(match)

            identity["sample_match_id"] = match.get("id")
            identity["sample_match"] = get_match_name(match)
            identity["sample_time_iran"] = utc_to_iran(
                match.get("startTime") or match.get("status", {}).get("utcTime")
            )
            identity["sample_tournamentStage"] = match.get("tournamentStage")
            identity["sample_match_id_fields"] = match_ids

            for object_name, obj in collect_named_objects(match):
                for key in (
                    "id",
                    "primaryId",
                    "parentLeagueId",
                    "leagueId",
                    "competitionId",
                    "tournamentId",
                ):
                    if key in obj:
                        identity[f"sample.{object_name}.{key}"] = obj[key]

                if "name" in obj:
                    identity[f"sample.{object_name}.name"] = obj["name"]

        all_records.append(identity)

        print()
        print("-" * 120)
        print(f"NAME: {identity.get('name')}")
        print(f"SLUG: {identity.get('slug')}")
        print(f"COUNTRY: {identity.get('country')}")
        print(f"TYPE: {identity.get('type')}")
        print(
            "IDS:",
            clean({
                k: v for k, v in identity.items()
                if "id" in k.lower()
            })
        )
        print(
            f"SAMPLE: {identity.get('sample_match')} | "
            f"{identity.get('sample_time_iran')} | "
            f"tournamentStage={identity.get('sample_tournamentStage')}"
        )

    print()
    print("=" * 120)
    print("CONFIGURED ID -> TODAY'S COMPETITION MATCHES")
    print("=" * 120)

    hits = defaultdict(list)

    for record in all_records:
        for key, value in record.items():
            if "id" not in key.lower() or value is None:
                continue

            if str(value) in configured_ids:
                hits[str(value)].append(
                    (record.get("name"), key, value, record.get("slug"))
                )

    for item in configured:
        configured_id = str(item["id"])
        print()
        print(
            f"CONFIGURED {configured_id} | "
            f"mode={item.get('mode')} | "
            f"stage={item.get('stage')} | "
            f"extra_country={item.get('extra_country')} | "
            f"extra_teams={item.get('extra_teams')}"
        )

        matches = hits.get(configured_id, [])
        if not matches:
            print("  -> NO DIRECT ID MATCH TODAY")
            continue

        seen = set()
        for name, key, value, slug in matches:
            marker = (name, key, str(value))
            if marker in seen:
                continue
            seen.add(marker)
            print(
                f"  -> {name} | {key}={value} | slug={slug}"
            )

    print()
    print("=" * 120)
    print("UNIQUE LEAGUE IDs SUMMARY")
    print("=" * 120)

    for record in sorted(all_records, key=lambda x: str(x.get("name") or "")):
        ids = {
            key: value
            for key, value in record.items()
            if "id" in key.lower() and value is not None
        }
        print(
            f"{record.get('name')} | "
            f"slug={record.get('slug')} | "
            f"ids={clean(ids)}"
        )

    print()
    print("=" * 120)
    print("IMPORTANT")
    print("=" * 120)
    print("This test does NOT call /api/matchDetails for individual matches.")
    print("It does NOT modify auto_matches.json.")
    print("It only discovers how configured IDs map to the competition objects")
    print("already returned by /api/data/matches for today's date.")


if __name__ == "__main__":
    main()

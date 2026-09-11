import json
import os

from datetime import datetime, timedelta
from zoneinfo import ZoneInfo


CACHE_FILE = "matches_cache.json"

IRAN_TIMEZONE = ZoneInfo("Asia/Tehran")

KEEP_FINISHED_DAYS = 3


def load_matches_cache():
    if not os.path.exists(CACHE_FILE):
        return {}

    try:
        with open(
            CACHE_FILE,
            "r",
            encoding="utf-8",
        ) as file:
            data = json.load(file)

        if isinstance(data, dict):
            return data

        return {}

    except Exception:
        return {}


def save_matches_cache(cache):
    temporary_file = f"{CACHE_FILE}.tmp"

    with open(
        temporary_file,
        "w",
        encoding="utf-8",
    ) as file:
        json.dump(
            cache,
            file,
            ensure_ascii=False,
            indent=2,
        )

    os.replace(
        temporary_file,
        CACHE_FILE,
    )


def get_match(cache, match_id):
    return cache.get(str(match_id))


def create_match_record(match):
    match_id = str(match["id"])

    return {
        "id": match_id,
        "date": match.get("date"),
        "league": match.get("league"),
        "home": match.get("home"),
        "away": match.get("away"),
        "home_id": match.get("home_id"),
        "away_id": match.get("away_id"),
        "utc_time": match.get("utc_time"),
        "iran_time": match.get("iran_time"),
        "status": match.get("status"),
        "score": match.get("score"),
        "url": match.get("url"),

        "pre_match_sent": False,
        "lineup_sent": False,
        "finished_sent": False,

        "sent_goal_ids": [],

        "last_status": match.get("status"),
        "last_score": match.get("score"),
    }


def update_match_record(existing, match):
    existing["date"] = match.get("date")
    existing["league"] = match.get("league")
    existing["home"] = match.get("home")
    existing["away"] = match.get("away")
    existing["home_id"] = match.get("home_id")
    existing["away_id"] = match.get("away_id")
    existing["utc_time"] = match.get("utc_time")
    existing["iran_time"] = match.get("iran_time")
    existing["status"] = match.get("status")
    existing["score"] = match.get("score")
    existing["url"] = match.get("url")

    existing["last_status"] = match.get("status")
    existing["last_score"] = match.get("score")

    return existing


def add_or_update_match(cache, match):
    match_id = str(match["id"])

    if match_id not in cache:
        cache[match_id] = create_match_record(match)
        return True

    update_match_record(
        cache[match_id],
        match,
    )

    return False


def parse_iran_datetime(value):
    if not value:
        return None

    try:
        return datetime.strptime(
            value,
            "%Y-%m-%d %H:%M",
        ).replace(
            tzinfo=IRAN_TIMEZONE
        )

    except Exception:
        return None


def remove_old_matches(cache):
    now = datetime.now(IRAN_TIMEZONE)

    cutoff_time = now - timedelta(
        days=KEEP_FINISHED_DAYS
    )

    cleaned_cache = {}

    removed_count = 0

    for match_id, match in cache.items():
        status = match.get("status")

        iran_time = parse_iran_datetime(
            match.get("iran_time")
        )

        should_remove = (
            status == "Finished"
            and iran_time is not None
            and iran_time < cutoff_time
        )

        if should_remove:
            removed_count += 1
            continue

        cleaned_cache[match_id] = match

    return cleaned_cache, removed_count

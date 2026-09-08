import os
import requests


# ============================================================
# تنظیمات
# ============================================================

API_KEY = os.getenv("BIGBALLS_API_KEY")

BASE_URL = "https://api.bigballsdata.com/v1"

HEADERS = {
    "Authorization": f"Bearer {API_KEY}"
}


# ============================================================
# درخواست به API
# ============================================================

def get_json(url, params=None):

    response = requests.get(
        url,
        headers=HEADERS,
        params=params,
        timeout=30
    )

    response.raise_for_status()

    return response.json()


# ============================================================
# دریافت اطلاعات پایه مسابقه
# ============================================================

def get_match_info(match_id):

    response = get_json(
        f"{BASE_URL}/stored/matches/{match_id}"
    )

    return response.get("data", {})


# ============================================================
# دریافت رویدادهای مسابقه
# ============================================================

def get_match_events(match_id):

    response = get_json(
        f"{BASE_URL}/matches/{match_id}/events",
        params={
            "sport": "football"
        }
    )

    return response.get("data", [])


# ============================================================
# دریافت ترکیب
# ============================================================

def get_match_lineups(match_id):

    response = get_json(
        f"{BASE_URL}/stored/matches/{match_id}/lineups"
    )

    data = response.get("data", {})
    meta = response.get("meta", {})

    return {
        "home": data.get("home", []),
        "away": data.get("away", []),
        "available": meta.get("available", False),
        "lineup_shape": meta.get("lineup_shape"),
        "formation": meta.get("formation", {})
    }


# ============================================================
# دریافت آمار مسابقه
# ============================================================

def get_match_stats(match_id):

    response = get_json(
        f"{BASE_URL}/stored/matches/{match_id}/stats"
    )

    data = response.get("data", {})

    return {
        "team_stats": data.get("team_stats", []),
        "players": data.get("players", [])
    }


# ============================================================
# دریافت تمام اطلاعات مسابقه
# ============================================================

def get_match_data(match_id):

    match = get_match_info(match_id)

    events = get_match_events(match_id)

    lineups = get_match_lineups(match_id)

    stats = get_match_stats(match_id)

    return {
        "match": match,
        "events": events,
        "lineups": lineups,
        "stats": stats
    }

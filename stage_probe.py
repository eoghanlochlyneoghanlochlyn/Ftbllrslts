import json
import re
from urllib.parse import quote

import requests

BASE = "https://www.fotmob.com"
IDS = [50, 44, 290, 289, 525, 9469, 526, 45, 42, 73, 10216, 78, 133]

HEADERS = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/140.0.0.0 Safari/537.36",
    "Accept": "application/json,text/plain,*/*",
    "Accept-Language": "en-US,en;q=0.9",
    "Referer": BASE + "/",
}

def clean(value):
    if value is None:
        return ""
    return re.sub(r"\s+", " ", str(value)).strip()

def request_json(url, params=None):
    r = requests.get(url, params=params, headers=HEADERS, timeout=30)
    print(f"HTTP {r.status_code} {r.url}")
    r.raise_for_status()
    data = r.json()
    if not isinstance(data, dict):
        raise RuntimeError("non-dict response")
    return data

def get_path(data, path):
    cur = data
    for key in path:
        if not isinstance(cur, dict) or key not in cur:
            return None
        cur = cur[key]
    return cur

def collect_stage_fields(node, path=()):
    found = []
    if isinstance(node, dict):
        for key, value in node.items():
            low = str(key).lower()
            new_path = path + (str(key),)
            if low in {"stage", "stagename", "tournamentstage", "roundname", "round"}:
                if isinstance(value, (str, int, float)):
                    found.append((".".join(new_path), value))
                elif isinstance(value, dict):
                    for subkey in ("name", "label", "value", "stage"):
                        if subkey in value and value[subkey] is not None:
                            found.append((".".join(new_path + (subkey,)), value[subkey]))
            if isinstance(value, (dict, list)):
                found.extend(collect_stage_fields(value, new_path))
    elif isinstance(node, list):
        for i, item in enumerate(node):
            found.extend(collect_stage_fields(item, path + (str(i),)))
    return found

def inspect_competition(league_id):
    print("=" * 100)
    print(f"COMPETITION {league_id}")
    print("=" * 100)

    data = request_json(f"{BASE}/api/data/leagues", {"id": league_id})

    details = data.get("details", {})
    seasons = data.get("seasons", [])
    print("top keys:", sorted(data.keys()))
    print("details.selectedSeason:", details.get("selectedSeason") if isinstance(details, dict) else None)
    print("seasons:")
    if isinstance(seasons, list):
        for s in seasons[:8]:
            if isinstance(s, dict):
                print("  ", s.get("id"), "|", s.get("name"))
            else:
                print("  ", s)

    overview = data.get("overview")
    print("overview type:", type(overview).__name__)
    print("overview keys:", sorted(overview.keys()) if isinstance(overview, dict) else None)

    playoff = overview.get("playoff") if isinstance(overview, dict) else None
    print("overview.playoff keys:", sorted(playoff.keys()) if isinstance(playoff, dict) else None)

    stage_fields = collect_stage_fields(data)
    print("stage-like fields (first 80):")
    for path, value in stage_fields[:80]:
        print("  ", path, "=", value)

    if isinstance(seasons, list):
        season_ids = []
        for s in seasons:
            if isinstance(s, dict):
                sid = s.get("id")
            else:
                sid = s
            if sid and str(sid) not in season_ids:
                season_ids.append(str(sid))

        for sid in season_ids[:3]:
            print("-" * 80)
            print("SEASON:", sid)
            try:
                season_data = request_json(
                    f"{BASE}/api/data/leagues",
                    {"id": league_id, "season": sid},
                )
            except Exception as exc:
                print("season request failed:", exc)
                continue

            ov = season_data.get("overview")
            po = ov.get("playoff") if isinstance(ov, dict) else None
            print("overview keys:", sorted(ov.keys()) if isinstance(ov, dict) else None)
            print("playoff keys:", sorted(po.keys()) if isinstance(po, dict) else None)

            rounds = po.get("rounds") if isinstance(po, dict) else None
            if isinstance(rounds, list):
                print("round count:", len(rounds))
                for idx, item in enumerate(rounds[:12]):
                    if not isinstance(item, dict):
                        continue
                    print(
                        "  ROUND",
                        idx,
                        "stage=", item.get("stage"),
                        "name=", item.get("name"),
                        "keys=", sorted(item.keys()),
                    )

            seasonal_stage_fields = collect_stage_fields(season_data)
            for path, value in seasonal_stage_fields[:50]:
                print("  STAGEFIELD", path, "=", value)

def main():
    for league_id in IDS:
        try:
            inspect_competition(league_id)
        except Exception as exc:
            print("ERROR:", league_id, repr(exc))

if __name__ == "__main__":
    main()

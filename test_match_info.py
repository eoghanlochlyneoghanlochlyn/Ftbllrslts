"""Read-only FotMob match report. Run: python test_match_info.py [match_id]"""
import json
import sys
import time
import requests

BASE = "https://www.fotmob.com"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/140.0.0.0 Safari/537.36",
    "Accept": "application/json,text/plain,*/*",
    "Referer": BASE + "/",
}


def show(value):
    return json.dumps(value, ensure_ascii=False, default=str)


def heading(title):
    print("\n" + "=" * 90)
    print(title)
    print("=" * 90)


def match_report(data, match_id):
    general = data.get("general") or {}
    header = data.get("header") or {}
    content = data.get("content") or {}
    facts = content.get("matchFacts") or {}
    lineup = content.get("lineup") or {}
    status = header.get("status") or {}

    heading("MATCH / COMPETITION / TEAMS")
    print("Match ID:", match_id)
    print("Competition:", general.get("leagueName") or header.get("leagueName") or "Not available")
    print("Competition ID:", general.get("leagueId") or header.get("leagueId") or "Not available")
    print("Round:", general.get("roundName") or general.get("round") or facts.get("round") or "Not available")
    for side in ("home", "away"):
        team = header.get("teams", {}).get(side, {}) if isinstance(header.get("teams"), dict) else {}
        lineup_team = lineup.get(side + "Team") or {}
        print(f"{side.upper()} TEAM:", team.get("name") or lineup_team.get("name") or "Not available",
              "| ID:", team.get("id") or lineup_team.get("id"))
    print("Kickoff UTC:", status.get("utcTime") or general.get("matchTimeUTC") or "Not available")
    print("Score:", status.get("scoreStr") or "Not available")
    print("Status:", show({k: status.get(k) for k in ("started", "finished", "ongoing", "cancelled", "reason", "liveTime", "halfs")}))

    heading("LINEUPS AND PLAYER RATINGS")
    print("Lineup type:", lineup.get("lineupType") or "Not available")
    for side in ("home", "away"):
        team = lineup.get(side + "Team") or {}
        print(f"\n{side.upper()}: {team.get('name', '?')} | Formation: {team.get('formation', '?')} | Team rating: {team.get('rating', 'N/A')}")
        for group in ("starters", "subs"):
            players = team.get(group) or []
            print(f"  {group.upper()} ({len(players)}):")
            for player in players:
                if not isinstance(player, dict):
                    continue
                performance = player.get("performance") or {}
                print(f"    #{player.get('shirtNumber', '-')} {player.get('name', '?')} "
                      f"| id={player.get('id')} | position={player.get('positionId', '-')} "
                      f"| rating={performance.get('rating', 'N/A')} "
                      f"| performance={show(performance)}")

    heading("MATCH EVENTS (CHRONOLOGICAL SOURCE ORDER)")
    event_lists = []
    for label, value in (
        ("content.matchFacts.events", facts.get("events")),
        ("content.events", content.get("events")),
        ("content.liveticker.events", (content.get("liveticker") or {}).get("events")),
    ):
        if isinstance(value, dict):
            value = value.get("events") or value.get("list")
        if isinstance(value, list) and value:
            event_lists.append((label, value))
    if not event_lists:
        print("No match-event list found in the known API paths.")
        print("matchFacts keys:", list(facts.keys()))
    else:
        for label, events in event_lists:
            print(f"\nSource: {label} | Total: {len(events)}")
            for i, event in enumerate(events, 1):
                if not isinstance(event, dict):
                    print(f"  [{i}] {show(event)}")
                    continue
                print(f"  [{i}] minute={event.get('time', event.get('minute', '?'))} "
                      f"type={event.get('type', event.get('eventType', '?'))} "
                      f"player={event.get('nameStr', event.get('playerName', event.get('name', '?')))} "
                      f"team={'HOME' if event.get('isHome') is True else 'AWAY' if event.get('isHome') is False else '?'} "
                      f"score={show(event.get('newScore'))} "
                      f"reactKey={event.get('reactKey')}")
                print("       RAW:", show(event))

    heading("TEAM MATCH STATISTICS")
    stats = content.get("stats") or {}
    periods = stats.get("Periods") or stats.get("periods") or {}
    print("Available periods:", list(periods.keys()) if isinstance(periods, dict) else type(periods).__name__)
    if isinstance(periods, dict):
        for period, period_data in periods.items():
            print(f"\nPERIOD: {period}")
            groups = period_data.get("stats") or [] if isinstance(period_data, dict) else []
            for group in groups:
                if not isinstance(group, dict):
                    continue
                print("\n ", group.get("title", group.get("key", "Other")))
                for item in group.get("stats") or []:
                    if isinstance(item, dict):
                        values = item.get("stats")
                        print(f"    {item.get('title', item.get('key', '?'))}: "
                              f"home={values[0] if isinstance(values, list) and len(values)>0 else 'N/A'} | "
                              f"away={values[1] if isinstance(values, list) and len(values)>1 else 'N/A'} "
                              f"| key={item.get('key')}")
    else:
        print("Raw stats:", show(stats))

    heading("PLAYER-SPECIFIC MATCH STATISTICS (IF EXPOSED)")
    player_stats = content.get("playerStats") or content.get("playerstats")
    if player_stats:
        print(show(player_stats))
    else:
        print("No dedicated playerStats section in this matchDetails response.")
        print("Player performance fields from lineups are printed above; season top scorers are not match stats.")

    heading("REPORT COMPLETE")


def main():
    match_id = sys.argv[1] if len(sys.argv) > 1 else "5868463"
    if not match_id.isdigit():
        raise SystemExit("Match ID must be numeric")
    url = f"{BASE}/api/data/matchDetails?matchId={match_id}"
    print("FOTMOB FULL MATCH REPORT TEST STARTED", flush=True)
    print("URL:", url)
    start = time.perf_counter()
    response = requests.get(url, headers=HEADERS, timeout=30)
    print(f"HTTP {response.status_code} | {time.perf_counter()-start:.3f}s | "
          f"Cache-Control: {response.headers.get('cache-control')} | Bytes: {len(response.content)}", flush=True)
    response.raise_for_status()
    data = response.json()
    if not isinstance(data, dict):
        raise ValueError("Expected JSON object from matchDetails")
    match_report(data, match_id)


if __name__ == "__main__":
    main()

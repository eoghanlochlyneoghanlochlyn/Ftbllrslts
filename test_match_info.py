from fotmob import get_match_snapshot


MATCHES = [
    "https://www.fotmob.com/matches/esteghlal-vs-al-sadd/9ih3qny#6050065",
    "https://www.fotmob.com/matches/hapoel-beer-sheva-vs-dinamo-zagreb/3a0mfj#6112363",
    "https://www.fotmob.com/matches/brighton-hove-albion-vs-manchester-united/3goccs#6099329",
]


def main():
    for match_url in MATCHES:

        print("\n")
        print("=" * 70)
        print("MATCH:")
        print(match_url)
        print("=" * 70)

        try:
            snapshot = get_match_snapshot(
                match_url
            )
        except Exception as error:
            print("ERROR:")
            print(error)
            continue

        print("\n========== TRANSLATION DEBUG ==========")

        print(
            "home:",
            snapshot.get("home")
        )

        print(
            "home_team_id:",
            snapshot.get("home_team_id")
        )

        print(
            "away:",
            snapshot.get("away")
        )

        print(
            "away_team_id:",
            snapshot.get("away_team_id")
        )

        print(
            "league:",
            snapshot.get("league")
        )

        print(
            "league_fa:",
            snapshot.get("league_fa")
        )

        print(
            "competition_id:",
            snapshot.get("competition_id")
        )

        print(
            "========================================")


if __name__ == "__main__":
    main()

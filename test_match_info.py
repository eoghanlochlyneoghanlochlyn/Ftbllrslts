from fotmob import get_match_snapshot


MATCHES = [
    "https://www.fotmob.com/matches/esteghlal-vs-al-sadd/9ih3qny#6050065",
    "https://www.fotmob.com/matches/hapoel-beer-sheva-vs-dinamo-zagreb/3a0mfj#6112363",
    "https://www.fotmob.com/matches/brighton-hove-albion-vs-manchester-united/3goccs#6099329",
    "https://www.fotmob.com/matches/nottingham-forest-vs-aston-villa/3gke9k#5206176",
    "https://www.fotmob.com/matches/arsenal-vs-crystal-palace/36ytc8#5034192",
    "https://www.fotmob.com/matches/vissel-kobe-vs-al-sadd/2lxqo1w#5336423",
]


def main():
    for index, match_url in enumerate(
        MATCHES,
        start=1,
    ):

        print("\n")
        print("=" * 70)
        print(f"TEST {index}/{len(MATCHES)}")
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

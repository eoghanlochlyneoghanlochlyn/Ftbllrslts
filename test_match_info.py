from fotmob import get_match_snapshot


MATCH_URL = (
    "https://www.fotmob.com/matches/"
    "osasuna-vs-real-sociedad/2dcesm#5125328"
)


def main():

    print("=" * 60)
    print("TEST TEAM ID")
    print("=" * 60)

    snapshot = get_match_snapshot(
        MATCH_URL
    )

    if not snapshot:
        print("❌ Snapshot دریافت نشد.")
        return

    print()
    print("🏠 HOME")
    print("-" * 60)
    print(
        f"Name: {snapshot.get('home')}"
    )
    print(
        f"ID:   {snapshot.get('home_team_id')}"
    )

    print()
    print("✈️ AWAY")
    print("-" * 60)
    print(
        f"Name: {snapshot.get('away')}"
    )
    print(
        f"ID:   {snapshot.get('away_team_id')}"
    )

    print()
    print("📦 HOME TEAM OBJECT")
    print("-" * 60)
    print(
        snapshot.get("home_team")
    )

    print()
    print("📦 AWAY TEAM OBJECT")
    print("-" * 60)
    print(
        snapshot.get("away_team")
    )

    print()
    print("=" * 60)
    print("END")
    print("=" * 60)


if __name__ == "__main__":
    main()

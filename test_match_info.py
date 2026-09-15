from team_translations import get_persian_team_name


def main():

    print("=" * 60)
    print("TEST TEAM TRANSLATION")
    print("=" * 60)

    tests = [
        (8560, "Real Sociedad"),
        (8371, "Osasuna"),
        (999999, "Real Sociedad"),
        (999999, "Unknown Team"),
    ]

    for team_id, team_name in tests:

        result = get_persian_team_name(
            team_id,
            team_name
        )

        print()
        print(f"ID:   {team_id}")
        print(f"Name: {team_name}")
        print(f"➡️    {result}")

    print()
    print("=" * 60)
    print("END")
    print("=" * 60)


if __name__ == "__main__":
    main()

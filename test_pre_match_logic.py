from datetime import datetime, timedelta, timezone


def evaluate_simulated_match(
    match_name,
    status,
    pre_match_sent,
    minutes_until_kickoff,
    official_lineup_available,
):
    print()
    print("-" * 70)
    print(f"Match: {match_name}")
    print(f"Status: {status}")
    print(f"Pre-match already sent: {pre_match_sent}")
    print(
        f"Minutes until kickoff: "
        f"{minutes_until_kickoff}"
    )
    print(
        f"Official lineups available: "
        f"{official_lineup_available}"
    )

    if pre_match_sent:
        decision = "ALREADY SENT"
        reason = "Pre-match message was already sent."

    elif status != "Upcoming":
        decision = "WAIT"
        reason = "Match is not Upcoming."

    elif official_lineup_available:
        decision = "SEND"
        reason = "Both official lineups are available."

    elif (
        minutes_until_kickoff >= 0
        and minutes_until_kickoff <= 60
    ):
        decision = "SEND"
        reason = "One hour or less remains until kickoff."

    else:
        decision = "WAIT"
        reason = (
            "Official lineups are unavailable and "
            "more than one hour remains."
        )

    print(f"Decision: {decision}")
    print(f"Reason: {reason}")

    return decision


def main():
    print("Pre-match Logic Simulation Test")
    print("=" * 70)

    match_name = "Chelsea 🆚 Hull City"

    print()
    print("SCENARIO 1: More than one hour before kickoff")
    evaluate_simulated_match(
        match_name=match_name,
        status="Upcoming",
        pre_match_sent=False,
        minutes_until_kickoff=180,
        official_lineup_available=False,
    )

    print()
    print("SCENARIO 2: Exactly 61 minutes before kickoff")
    evaluate_simulated_match(
        match_name=match_name,
        status="Upcoming",
        pre_match_sent=False,
        minutes_until_kickoff=61,
        official_lineup_available=False,
    )

    print()
    print("SCENARIO 3: Exactly 60 minutes before kickoff")
    evaluate_simulated_match(
        match_name=match_name,
        status="Upcoming",
        pre_match_sent=False,
        minutes_until_kickoff=60,
        official_lineup_available=False,
    )

    print()
    print("SCENARIO 4: 45 minutes before kickoff")
    evaluate_simulated_match(
        match_name=match_name,
        status="Upcoming",
        pre_match_sent=False,
        minutes_until_kickoff=45,
        official_lineup_available=False,
    )

    print()
    print("SCENARIO 5: 5 minutes before kickoff")
    evaluate_simulated_match(
        match_name=match_name,
        status="Upcoming",
        pre_match_sent=False,
        minutes_until_kickoff=5,
        official_lineup_available=False,
    )

    print()
    print("SCENARIO 6: Official lineups confirmed 180 minutes before kickoff")
    evaluate_simulated_match(
        match_name=match_name,
        status="Upcoming",
        pre_match_sent=False,
        minutes_until_kickoff=180,
        official_lineup_available=True,
    )

    print()
    print("SCENARIO 7: Official lineups confirmed 45 minutes before kickoff")
    evaluate_simulated_match(
        match_name=match_name,
        status="Upcoming",
        pre_match_sent=False,
        minutes_until_kickoff=45,
        official_lineup_available=True,
    )

    print()
    print("SCENARIO 8: Message already sent")
    evaluate_simulated_match(
        match_name=match_name,
        status="Upcoming",
        pre_match_sent=True,
        minutes_until_kickoff=45,
        official_lineup_available=True,
    )

    print()
    print("SCENARIO 9: Match is Live")
    evaluate_simulated_match(
        match_name=match_name,
        status="Live",
        pre_match_sent=False,
        minutes_until_kickoff=0,
        official_lineup_available=True,
    )

    print()
    print("SCENARIO 10: Kickoff time has passed")
    evaluate_simulated_match(
        match_name=match_name,
        status="Upcoming",
        pre_match_sent=False,
        minutes_until_kickoff=-5,
        official_lineup_available=False,
    )

    print()
    print("=" * 70)
    print("Simulation completed.")


if __name__ == "__main__":
    main()

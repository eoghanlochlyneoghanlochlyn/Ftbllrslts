from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from test_daily_matches import fetch_matches_for_date
from match_cache import (
    add_or_update_match,
    load_matches_cache,
    remove_old_matches,
    save_matches_cache,
)


def main():
    today = datetime.now(
        ZoneInfo("Asia/Tehran")
    ).date()

    dates = [
        today,
        today + timedelta(days=1),
    ]

    cache = load_matches_cache()

    new_matches = 0
    updated_matches = 0

    for current_date in dates:
        date_string = current_date.strftime("%Y%m%d")

        matches = fetch_matches_for_date(date_string)

        for match in matches:
            was_new = add_or_update_match(
                cache,
                match,
            )

            if was_new:
                new_matches += 1
            else:
                updated_matches += 1

    cache, removed_matches = remove_old_matches(
        cache
    )

    save_matches_cache(cache)

    print("")
    print("=" * 60)
    print("Match cache updated")
    print("=" * 60)
    print(f"New matches: {new_matches}")
    print(f"Updated matches: {updated_matches}")
    print(f"Removed old matches: {removed_matches}")
    print(f"Total cached matches: {len(cache)}")
    print("=" * 60)

    print("")
    print("Cached match IDs:")

    for match_id, match in cache.items():
        print(
            f"{match_id}: "
            f"{match['home']} 🆚 {match['away']} | "
            f"{match['status']}"
        )


if __name__ == "__main__":
    main()

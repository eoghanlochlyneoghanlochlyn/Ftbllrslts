from fotmob import fetch_match_page, extract_next_data


MATCH_ID = "6050065"


def find_keys(data, path=""):
    if isinstance(data, dict):
        for key, value in data.items():
            current_path = f"{path}.{key}" if path else str(key)

            key_text = str(key).lower()

            if (
                "round" in key_text
                or "week" in key_text
                or "stage" in key_text
            ):
                print("\n" + "=" * 100)
                print("PATH:")
                print(current_path)
                print("KEY:")
                print(repr(key))
                print("TYPE:")
                print(type(value).__name__)
                print("VALUE:")

                if isinstance(value, (dict, list)):
                    print(repr(value)[:10000])
                else:
                    print(repr(value))

            find_keys(value, current_path)

    elif isinstance(data, list):
        for index, item in enumerate(data):
            current_path = f"{path}[{index}]"
            find_keys(item, current_path)


def main():
    print("Fetching FotMob page...")
    print("Match ID:", MATCH_ID)

    html = fetch_match_page(MATCH_ID)

    if not html:
        print("ERROR: FotMob page could not be fetched.")
        return

    print("HTML length:", len(html))

    data = extract_next_data(html)

    if not isinstance(data, dict):
        print("ERROR: __NEXT_DATA__ could not be extracted.")
        return

    print("NEXT_DATA extracted successfully.")
    print("\nSearching for round / week / stage fields...")

    find_keys(data)

    print("\n" + "=" * 100)
    print("TEST FINISHED.")


if __name__ == "__main__":
    main()

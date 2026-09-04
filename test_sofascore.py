from curl_cffi import requests


EVENT_ID = 16995551

URL = f"https://www.sofascore.com/api/v1/event/{EVENT_ID}"


def main():
    print("Connecting to SofaScore...")

    response = requests.get(
        URL,
        impersonate="chrome"
    )

    print("Status:", response.status_code)

    print("\nResponse:")
    print(response.text[:5000])


if __name__ == "__main__":
    main()

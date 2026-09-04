from curl_cffi import requests

MATCH_ID = 4653711

URL = f"https://www.fotmob.com/api/data/matchDetails?matchId={MATCH_ID}"


def main():
    print("Connecting to FotMob...")

    response = requests.get(
        URL,
        impersonate="chrome"
    )

    print("Status:", response.status_code)

    print("\nResponse:")
    print(response.text[:5000])


if __name__ == "__main__":
    main()

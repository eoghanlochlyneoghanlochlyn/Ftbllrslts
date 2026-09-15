import requests


URL = "https://www.fotmob.com/api/leagues"


def main():
    print("در حال دریافت فهرست رقابت‌ها از FotMob...")

    try:
        response = requests.get(
            URL,
            headers={
                "User-Agent": "Mozilla/5.0"
            },
            timeout=20
        )

        print("Status:", response.status_code)

        if response.status_code != 200:
            print("خطا در دریافت اطلاعات")
            print(response.text[:1000])
            return

        data = response.json()

        print("\nنوع داده:", type(data))

        if isinstance(data, dict):
            print("کلیدهای اصلی:")
            for key in data.keys():
                print(" -", key)

        print("\n--- RAW DATA ---")
        print(data)

    except Exception as e:
        print("خطا:", repr(e))


if __name__ == "__main__":
    main()

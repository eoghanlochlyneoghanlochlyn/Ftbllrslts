print("========================================")
print("TEST STARTED")
print("========================================")

import requests

print("requests imported successfully")

url = "https://www.fotmob.com/match/6106264"

print("Requesting FotMob...")

response = requests.get(
    url,
    headers={
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/140.0.0.0 Safari/537.36"
        )
    },
    timeout=30
)

print("HTTP STATUS:", response.status_code)
print("HTML LENGTH:", len(response.text))

print("========================================")
print("TEST FINISHED")
print("========================================")

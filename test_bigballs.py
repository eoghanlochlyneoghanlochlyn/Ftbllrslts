import requests

API_KEY = "YOUR_API_KEY"

r = requests.get(
    "https://api.bigballsdata.com/v1/matches",
    headers={"Authorization": f"Bearer {API_KEY}"},
    params={
        "sport": "football",
        "status": "scheduled",
        "limit": 20
    }
)

print(r.status_code)
print(r.json())

import os
import requests

BOT_TOKEN = os.environ["TELEGRAMBOT"]
CHANNEL = os.environ["TELEGRAMCHANNEL"]

text = """<pre>Real Sociedad            Osasuna
────────────────────────────────────────
                         Jon Moncayola (4')
                         Mikel Oyarzabal (17' OG)
Beñat Turrientes (75')
Igor Zubeldia (90')</pre>"""

url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"

response = requests.post(
    url,
    data={
        "chat_id": CHANNEL,
        "text": text,
        "parse_mode": "HTML",
    },
)

print("Status:", response.status_code)
print("Response:", response.text)

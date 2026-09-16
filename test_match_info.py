import os
import requests

BOT_TOKEN = os.environ["TELEGRAMBOT"]
CHANNEL = os.environ["TELEGRAMCHANNEL"]

text = """🏆 جام حذفی اسپانیا
رئال سوسیداد 2 (4) 🆚 (3) 2 اوساسونا

<pre dir="ltr">رئال سوسیداد             اوساسونا
────────────────────────────────────────
                         Jon Moncayola (4')
                         Mikel Oyarzabal (17' OG)
Beñat Turrientes (75')
Igor Zubeldia (90')</pre>

🕐 1404/10/22 - 23:30 به وقت ایران"""

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

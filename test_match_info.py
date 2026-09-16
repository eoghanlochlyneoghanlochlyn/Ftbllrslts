import os
import requests
import json

BOT_TOKEN = os.environ["TELEGRAMBOT"]
CHANNEL = os.environ["TELEGRAMCHANNEL"]

rich_message = {
    "is_rtl": True,
    "blocks": [
        {
            "type": "paragraph",
            "text": "🏆 جام حذفی اسپانیا"
        },
        {
            "type": "paragraph",
            "text": "رئال سوسیداد 2 (4) 🆚 (3) 2 اوساسونا"
        },
        {
            "type": "table",
            "is_bordered": True,
            "is_compact": True,
            "cells": [
                [
                    {
                        "text": "رئال سوسیداد",
                        "is_header": True,
                        "align": "center"
                    },
                    {
                        "text": "اوساسونا",
                        "is_header": True,
                        "align": "center"
                    }
                ],
                [
                    {
                        "text": "",
                        "align": "right"
                    },
                    {
                        "text": "Jon Moncayola (4')",
                        "align": "left"
                    }
                ],
                [
                    {
                        "text": "",
                        "align": "right"
                    },
                    {
                        "text": "Mikel Oyarzabal (17' OG)",
                        "align": "left"
                    }
                ],
                [
                    {
                        "text": "Beñat Turrientes (75')",
                        "align": "right"
                    },
                    {
                        "text": "",
                        "align": "left"
                    }
                ],
                [
                    {
                        "text": "Igor Zubeldia (90')",
                        "align": "right"
                    },
                    {
                        "text": "",
                        "align": "left"
                    }
                ]
            ]
        },
        {
            "type": "paragraph",
            "text": "🕐 1404/10/22 - 23:30 به وقت ایران"
        }
    ]
}

url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendRichMessage"

response = requests.post(
    url,
    data={
        "chat_id": CHANNEL,
        "rich_message": json.dumps(rich_message, ensure_ascii=False),
    },
)

print("Status:", response.status_code)
print("Response:", response.text)

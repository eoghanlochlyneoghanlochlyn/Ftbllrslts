import os
import requests
import json

BOT_TOKEN = os.environ["TELEGRAMBOT"]
CHANNEL = os.environ["TELEGRAMCHANNEL"]

rich_message = {
    "blocks": [
        {
            "type": "paragraph",
            "text": {
                "type": "plain",
                "text": "🏆 جام حذفی اسپانیا"
            }
        },
        {
            "type": "paragraph",
            "text": {
                "type": "plain",
                "text": "رئال سوسیداد 2 (4) 🆚 (3) 2 اوساسونا"
            }
        },
        {
            "type": "table",
            "is_bordered": True,
            "is_compact": True,
            "cells": [
                [
                    {
                        "text": {
                            "type": "plain",
                            "text": "رئال سوسیداد"
                        },
                        "is_header": True,
                        "align": "center"
                    },
                    {
                        "text": {
                            "type": "plain",
                            "text": "اوساسونا"
                        },
                        "is_header": True,
                        "align": "center"
                    }
                ],
                [
                    {
                        "text": {
                            "type": "plain",
                            "text": ""
                        },
                        "align": "right"
                    },
                    {
                        "text": {
                            "type": "plain",
                            "text": "Jon Moncayola (4')"
                        },
                        "align": "left"
                    }
                ],
                [
                    {
                        "text": {
                            "type": "plain",
                            "text": ""
                        },
                        "align": "right"
                    },
                    {
                        "text": {
                            "type": "plain",
                            "text": "Mikel Oyarzabal (17' OG)"
                        },
                        "align": "left"
                    }
                ],
                [
                    {
                        "text": {
                            "type": "plain",
                            "text": "Beñat Turrientes (75')"
                        },
                        "align": "right"
                    },
                    {
                        "text": {
                            "type": "plain",
                            "text": ""
                        },
                        "align": "left"
                    }
                ],
                [
                    {
                        "text": {
                            "type": "plain",
                            "text": "Igor Zubeldia (90')"
                        },
                        "align": "right"
                    },
                    {
                        "text": {
                            "type": "plain",
                            "text": ""
                        },
                        "align": "left"
                    }
                ]
            ]
        },
        {
            "type": "paragraph",
            "text": {
                "type": "plain",
                "text": "🕐 1404/10/22 - 23:30 به وقت ایران"
            }
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

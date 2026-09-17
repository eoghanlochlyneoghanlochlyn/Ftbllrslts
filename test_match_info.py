import os
import requests
import json

BOT_TOKEN = os.environ["TELEGRAMBOT"]
CHANNEL = os.environ["TELEGRAMCHANNEL"]

real_sociedad_players = [
    "Álex Remiro",
    "Hamari Traoré",
    "Igor Zubeldia",
    "Robin Le Normand",
    "Aihen Muñoz",
    "Martín Zubimendi",
    "Beñat Turrientes",
    "Brais Méndez",
    "Takefusa Kubo",
    "Mikel Oyarzabal",
    "Alexander Sørloth",
]

osasuna_players = [
    "Sergio Herrera",
    "Jesús Areso",
    "David García",
    "Jorge Herrando",
    "Juan Cruz",
    "Lucas Torró",
    "Jon Moncayola",
    "Aimar Oroz",
    "Rubén García",
    "Ante Budimir",
    "Moi Gómez",
]

cells = [
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
    ]
]

for real_player, osasuna_player in zip(
    real_sociedad_players,
    osasuna_players
):
    cells.append(
        [
            {
                "text": real_player,
                "align": "right"
            },
            {
                "text": osasuna_player,
                "align": "left"
            }
        ]
    )

rich_message = {
    "is_rtl": True,
    "blocks": [
        {
            "type": "paragraph",
            "text": "🏆 ترکیب اصلی دو تیم"
        },
        {
            "type": "paragraph",
            "text": "رئال سوسیداد 🆚 اوساسونا"
        },
        {
            "type": "table",
            "is_bordered": True,
            "is_compact": False,
            "cells": cells
        }
    ]
}

url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendRichMessage"

response = requests.post(
    url,
    data={
        "chat_id": CHANNEL,
        "rich_message": json.dumps(
            rich_message,
            ensure_ascii=False
        ),
    },
)

print("Status:", response.status_code)
print("Response:", response.text)

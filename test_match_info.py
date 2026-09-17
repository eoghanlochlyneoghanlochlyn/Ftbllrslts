import os
import requests
import json

BOT_TOKEN = os.environ["TELEGRAMBOT"]
CHANNEL = os.environ["TELEGRAMCHANNEL"]

real_sociedad_starting = [
    "Unai Marrero",
    "Jon Aramburu",
    "Igor Zubeldia",
    "Duje Caleta-Car",
    "Sergio Gomez",
    "Ander Barrenetxea",
    "Jon Gorrotxategi",
    "Carlos Soler",
    "Takefusa Kubo",
    "Mikel Oyarzabal",
    "Luka Sucic",
]

osasuna_starting = [
    "Aitor Fernández",
    "Inigo Arguibide",
    "Flavien Boyomo",
    "Jorge Herrando",
    "Juan Cruz",
    "Enrique Barja",
    "Iker Munoz",
    "Jon Moncayola",
    "Abel Bretones",
    "Moi Gomez",
    "Raul Garcia",
]

real_sociedad_substitutes = [
    "Arsen Zakharyan",
    "Benat Turrientes",
    "Álvaro Odriozola",
    "Goncalo Guedes",
    "Orri Oskarsson",
    "Jon Martin",
    "Alex Remiro",
    "Aihen Munoz",
    "Aritz Elustondo",
    "Brais Méndez",
    "Pablo Marin",
]

osasuna_substitutes = [
    "Javi Galán",
    "Valentin Rosier",
    "Rubén Garcia",
    "Alejandro Catena",
    "Lucas Torro",
    "Ante Budimir",
    "Sergio Herrera",
    "Asier Osambela",
    "Aimar Oroz",
    "Sheraldo Becker",
    "Victor Munoz",
]

real_sociedad_subs_text = " | ".join(real_sociedad_substitutes)
osasuna_subs_text = " | ".join(osasuna_substitutes)

cells = [
    [
        {
            "text": (
                "رئال سوسیداد\n"
                "👔 Pellegrino Matarazzo\n"
                "📐 4-4-2"
            ),
            "is_header": True,
            "align": "center",
            "valign": "middle"
        },
        {
            "text": (
                "اوساسونا\n"
                "👔 Alessio Lisci\n"
                "📐 4-4-2"
            ),
            "is_header": True,
            "align": "center",
            "valign": "middle"
        }
    ]
]

for real_player, osasuna_player in zip(
    real_sociedad_starting,
    osasuna_starting
):
    cells.append(
        [
            {
                "text": real_player,
                "align": "right",
                "valign": "middle"
            },
            {
                "text": osasuna_player,
                "align": "left",
                "valign": "middle"
            }
        ]
    )

cells.append(
    [
        {
            "text": (
                "🔄 تعویضی‌ها\n"
                + real_sociedad_subs_text
            ),
            "align": "right",
            "valign": "top"
        },
        {
            "text": (
                "🔄 تعویضی‌ها\n"
                + osasuna_subs_text
            ),
            "align": "left",
            "valign": "top"
        }
    ]
)

rich_message = {
    "is_rtl": True,
    "blocks": [
        {
            "type": "paragraph",
            "text": "🏆 جام حذفی اسپانیا"
        },
        {
            "type": "paragraph",
            "text": "رئال سوسیداد 🆚 اوساسونا"
        },
        {
            "type": "paragraph",
            "text": "🕐 1404/10/22 - 23:30 به وقت ایران"
        },
        {
            "type": "table",
            "is_bordered": True,
            "is_striped": True,
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

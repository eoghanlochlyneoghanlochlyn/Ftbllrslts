import os
import requests


TELEGRAM_BOT_TOKEN = os.environ["TELEGRAMBOT"]
TELEGRAM_CHANNEL = os.environ["TELEGRAMCHANNEL"]


def send_rich_message(
    chat_id,
    rich_message,
):

    url = (
        f"https://api.telegram.org/bot"
        f"{TELEGRAM_BOT_TOKEN}/sendRichMessage"
    )

    response = requests.post(
        url,
        json={
            "chat_id": chat_id,
            "rich_message": rich_message,
        },
        timeout=30,
    )

    print(
        "Status:",
        response.status_code,
    )

    print(
        "Response:",
        response.text,
    )


# --------------------------------------------------------
# اطلاعات بازی
# --------------------------------------------------------

rich_message = {
    "is_rtl": True,
    "blocks": [

        {
            "type": "paragraph",
            "text": "🏆 جام حذفی اسپانیا",
        },

        {
            "type": "paragraph",
            "text": "رئال سوسیداد 2 (4) 🆚 (3) 2 اوساسونا",
        },

        {
            "type": "table",
            "is_bordered": True,
            "is_compact": False,
            "cells": [

                [
                    {
                        "text": "رئال سوسیداد",
                        "is_header": True,
                        "align": "center",
                    },
                    {
                        "text": "اوساسونا",
                        "is_header": True,
                        "align": "center",
                    },
                ],

                [
                    {
                        "text": "Benat Turrientes (75')",
                        "align": "center",
                    },
                    {
                        "text": "Mikel Oyarzabal (17')",
                        "align": "center",
                    },
                ],

                [
                    {
                        "text": "Igor Zubeldia (90')",
                        "align": "center",
                    },
                    {
                        "text": "Jon Moncayola (4')",
                        "align": "center",
                    },
                ],

            ],
        },

        {
            "type": "paragraph",
            "text": "🕐 1404/10/22 - 23:30 به وقت ایران",
        },

        {
            "type": "paragraph",
            "text": "🔘 رئال سوسیداد\n👔 Pellegrino Matarazzo\n📐 4-4-2",
        },

        {
            "type": "table",
            "is_bordered": True,
            "is_compact": False,
            "cells": [

                [
                    {
                        "text": "نمره",
                        "is_header": True,
                        "align": "center",
                    },
                    {
                        "text": "شماره",
                        "is_header": True,
                        "align": "center",
                    },
                    {
                        "text": "بازیکن",
                        "is_header": True,
                        "align": "center",
                    },
                    {
                        "text": "بازیکن",
                        "is_header": True,
                        "align": "center",
                    },
                    {
                        "text": "شماره",
                        "is_header": True,
                        "align": "center",
                    },
                    {
                        "text": "نمره",
                        "is_header": True,
                        "align": "center",
                    },
                ],

                [
                    {
                        "text": "8.5",
                        "align": "center",
                    },
                    {
                        "text": "13",
                        "align": "center",
                    },
                    {
                        "text": "Unai Marrero",
                        "align": "center",
                    },
                    {
                        "text": "Aitor Fernández",
                        "align": "center",
                    },
                    {
                        "text": "13",
                        "align": "center",
                    },
                    {
                        "text": "8.1",
                        "align": "center",
                    },
                ],

                [
                    {
                        "text": "7.3",
                        "align": "center",
                    },
                    {
                        "text": "2",
                        "align": "center",
                    },
                    {
                        "text": "Jon Aramburu",
                        "align": "center",
                    },
                    {
                        "text": "Inigo Arguibide",
                        "align": "center",
                    },
                    {
                        "text": "41",
                        "align": "center",
                    },
                    {
                        "text": "6.3",
                        "align": "center",
                    },
                ],

                [
                    {
                        "text": "7.8 ⚽️",
                        "align": "center",
                    },
                    {
                        "text": "5",
                        "align": "center",
                    },
                    {
                        "text": "Igor Zubeldia",
                        "align": "center",
                    },
                    {
                        "text": "Flavien Boyomo",
                        "align": "center",
                    },
                    {
                        "text": "22",
                        "align": "center",
                    },
                    {
                        "text": "6.8",
                        "align": "center",
                    },
                ],

                [
                    {
                        "text": "6.9",
                        "align": "center",
                    },
                    {
                        "text": "16",
                        "align": "center",
                    },
                    {
                        "text": "Duje Caleta-Car",
                        "align": "center",
                    },
                    {
                        "text": "Jorge Herrando",
                        "align": "center",
                    },
                    {
                        "text": "5",
                        "align": "center",
                    },
                    {
                        "text": "6.6",
                        "align": "center",
                    },
                ],

                [
                    {
                        "text": "7.5",
                        "align": "center",
                    },
                    {
                        "text": "17",
                        "align": "center",
                    },
                    {
                        "text": "Sergio Gomez",
                        "align": "center",
                    },
                    {
                        "text": "Juan Cruz",
                        "align": "center",
                    },
                    {
                        "text": "3",
                        "align": "center",
                    },
                    {
                        "text": "6.6",
                        "align": "center",
                    },
                ],

                [
                    {
                        "text": "7.2",
                        "align": "center",
                    },
                    {
                        "text": "7",
                        "align": "center",
                    },
                    {
                        "text": "Ander Barrenetxea",
                        "align": "center",
                    },
                    {
                        "text": "Enrique Barja",
                        "align": "center",
                    },
                    {
                        "text": "11",
                        "align": "center",
                    },
                    {
                        "text": "6.7",
                        "align": "center",
                    },
                ],

                [
                    {
                        "text": "6.2",
                        "align": "center",
                    },
                    {
                        "text": "4",
                        "align": "center",
                    },
                    {
                        "text": "Jon Gorrotxategi",
                        "align": "center",
                    },
                    {
                        "text": "Iker Munoz",
                        "align": "center",
                    },
                    {
                        "text": "8",
                        "align": "center",
                    },
                    {
                        "text": "7.5",
                        "align": "center",
                    },
                ],

                [
                    {
                        "text": "7.2",
                        "align": "center",
                    },
                    {
                        "text": "18",
                        "align": "center",
                    },
                    {
                        "text": "Carlos Soler",
                        "align": "center",
                    },
                    {
                        "text": "Jon Moncayola ⚽️",
                        "align": "center",
                    },
                    {
                        "text": "7",
                        "align": "center",
                    },
                    {
                        "text": "7.9",
                        "align": "center",
                    },
                ],

                [
                    {
                        "text": "6.7",
                        "align": "center",
                    },
                    {
                        "text": "14",
                        "align": "center",
                    },
                    {
                        "text": "Takefusa Kubo",
                        "align": "center",
                    },
                    {
                        "text": "Abel Bretones",
                        "align": "center",
                    },
                    {
                        "text": "23",
                        "align": "center",
                    },
                    {
                        "text": "7.1",
                        "align": "center",
                    },
                ],

                [
                    {
                        "text": "6.0 ⚽️ OG",
                        "align": "center",
                    },
                    {
                        "text": "10",
                        "align": "center",
                    },
                    {
                        "text": "Mikel Oyarzabal",
                        "align": "center",
                    },
                    {
                        "text": "Moi Gomez",
                        "align": "center",
                    },
                    {
                        "text": "16",
                        "align": "center",
                    },
                    {
                        "text": "5.7",
                        "align": "center",
                    },
                ],

                [
                    {
                        "text": "6.8",
                        "align": "center",
                    },
                    {
                        "text": "24",
                        "align": "center",
                    },
                    {
                        "text": "Luka Sucic",
                        "align": "center",
                    },
                    {
                        "text": "Raul Garcia",
                        "align": "center",
                    },
                    {
                        "text": "9",
                        "align": "center",
                    },
                    {
                        "text": "6.9",
                        "align": "center",
                    },
                ],

                [
                    {
                        "text": "ذخیره‌ها",
                        "is_header": True,
                        "align": "center",
                        "colspan": 3,
                    },
                    {
                        "text": "ذخیره‌ها",
                        "is_header": True,
                        "align": "center",
                        "colspan": 3,
                    },
                ],

                [
                    {
                        "text": "21. Arsen Zakharyan — 6.8\n8. Benat Turrientes — 8.4 ⚽️\n20. Álvaro Odriozola — 7.3\n11. Goncalo Guedes — 6.2\n9. Orri Oskarsson\n31. Jon Martin — 6.7\n1. Alex Remiro\n3. Aihen Munoz\n6. Aritz Elustondo\n23. Brais Méndez\n28. Pablo Marin",
                        "align": "center",
                        "colspan": 3,
                    },
                    {
                        "text": "20. Javi Galán — 6.2\n19. Valentin Rosier — 6.7\n14. Rubén Garcia — 6.4\n24. Alejandro Catena — 7.0\n6. Lucas Torro — 6.7\n17. Ante Budimir — 6.3\n1. Sergio Herrera\n29. Asier Osambela\n10. Aimar Oroz\n18. Sheraldo Becker\n21. Victor Munoz",
                        "align": "center",
                        "colspan": 3,
                    },
                ],

            ],
        },

        {
            "type": "paragraph",
            "text": "🔘 اوساسونا\n👔 Alessio Lisci\n📐 4-4-2",
        },

    ],
}


send_rich_message(
    TELEGRAM_CHANNEL,
    rich_message,
)

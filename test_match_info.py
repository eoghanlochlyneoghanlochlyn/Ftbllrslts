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
# پیام نهایی بازی
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
            "type": "table",
            "is_bordered": True,
            "is_compact": False,
            "cells": [

                [
                    {
                        "text": "🔘 رئال سوسیداد\n👔 Pellegrino Matarazzo\n📐 4-4-2",
                        "is_header": True,
                        "align": "center",
                    },
                    {
                        "text": "🔘 اوساسونا\n👔 Alessio Lisci\n📐 4-4-2",
                        "is_header": True,
                        "align": "center",
                    },
                ],

                [
                    {
                        "text": "13. Unai Marrero — 8.5",
                        "align": "center",
                    },
                    {
                        "text": "13. Aitor Fernández — 8.1",
                        "align": "center",
                    },
                ],

                [
                    {
                        "text": "2. Jon Aramburu — 7.3",
                        "align": "center",
                    },
                    {
                        "text": "41. Inigo Arguibide — 6.3",
                        "align": "center",
                    },
                ],

                [
                    {
                        "text": "5. Igor Zubeldia — 7.8 ⚽️",
                        "align": "center",
                    },
                    {
                        "text": "22. Flavien Boyomo — 6.8",
                        "align": "center",
                    },
                ],

                [
                    {
                        "text": "16. Duje Caleta-Car — 6.9",
                        "align": "center",
                    },
                    {
                        "text": "5. Jorge Herrando — 6.6",
                        "align": "center",
                    },
                ],

                [
                    {
                        "text": "17. Sergio Gomez — 7.5",
                        "align": "center",
                    },
                    {
                        "text": "3. Juan Cruz — 6.6",
                        "align": "center",
                    },
                ],

                [
                    {
                        "text": "7. Ander Barrenetxea — 7.2",
                        "align": "center",
                    },
                    {
                        "text": "11. Enrique Barja — 6.7",
                        "align": "center",
                    },
                ],

                [
                    {
                        "text": "4. Jon Gorrotxategi — 6.2",
                        "align": "center",
                    },
                    {
                        "text": "8. Iker Munoz — 7.5",
                        "align": "center",
                    },
                ],

                [
                    {
                        "text": "18. Carlos Soler — 7.2",
                        "align": "center",
                    },
                    {
                        "text": "7. Jon Moncayola — 7.9 ⚽️",
                        "align": "center",
                    },
                ],

                [
                    {
                        "text": "14. Takefusa Kubo — 6.7",
                        "align": "center",
                    },
                    {
                        "text": "23. Abel Bretones — 7.1",
                        "align": "center",
                    },
                ],

                [
                    {
                        "text": "10. Mikel Oyarzabal — 6.0 ⚽️ OG",
                        "align": "center",
                    },
                    {
                        "text": "16. Moi Gomez — 5.7",
                        "align": "center",
                    },
                ],

                [
                    {
                        "text": "24. Luka Sucic — 6.8",
                        "align": "center",
                    },
                    {
                        "text": "9. Raul Garcia — 6.9",
                        "align": "center",
                    },
                ],

                [
                    {
                        "text": "🔄 تعویضی‌ها\n21. Arsen Zakharyan — 6.8\n8. Benat Turrientes — 8.4 ⚽️\n20. Álvaro Odriozola — 7.3\n11. Goncalo Guedes — 6.2\n9. Orri Oskarsson\n31. Jon Martin — 6.7\n1. Alex Remiro\n3. Aihen Munoz\n6. Aritz Elustondo\n23. Brais Méndez\n28. Pablo Marin",
                        "align": "center",
                    },
                    {
                        "text": "🔄 تعویضی‌ها\n20. Javi Galán — 6.2\n19. Valentin Rosier — 6.7\n14. Rubén Garcia — 6.4\n24. Alejandro Catena — 7.0\n6. Lucas Torro — 6.7\n17. Ante Budimir — 6.3\n1. Sergio Herrera\n29. Asier Osambela\n10. Aimar Oroz\n18. Sheraldo Becker\n21. Victor Munoz",
                        "align": "center",
                    },
                ],

            ],
        },

    ],
}


send_rich_message(
    TELEGRAM_CHANNEL,
    rich_message,
)

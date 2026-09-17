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


rich_message = {
    "is_rtl": True,
    "blocks": [
        {
            "type": "paragraph",
            "text": "📊 آمار بازی",
        },
        {
            "type": "paragraph",
            "text": "رئال سوسیداد 2 (4) 🆚 (3) 2 اوساسونا",
        },
        {
            "type": "table",
            "is_bordered": True,
            "is_compact": False,
            "is_striped": True,
            "cells": [
                [
                    {
                        "text": "آمار",
                        "is_header": True,
                        "align": "center",
                    },
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
                        "text": "🎯 ایکس جی",
                        "align": "center",
                    },
                    {
                        "text": "3.96",
                        "align": "center",
                    },
                    {
                        "text": "0.55",
                        "align": "center",
                    },
                ],
                [
                    {
                        "text": "💥 شوت",
                        "align": "center",
                    },
                    {
                        "text": "30",
                        "align": "center",
                    },
                    {
                        "text": "13",
                        "align": "center",
                    },
                ],
                [
                    {
                        "text": "🥅 در چارچوب",
                        "align": "center",
                    },
                    {
                        "text": "9",
                        "align": "center",
                    },
                    {
                        "text": "5",
                        "align": "center",
                    },
                ],
                [
                    {
                        "text": "⚽️ مالکیت",
                        "align": "center",
                    },
                    {
                        "text": "69%",
                        "align": "center",
                    },
                    {
                        "text": "31%",
                        "align": "center",
                    },
                ],
                [
                    {
                        "text": "🔄 پاس",
                        "align": "center",
                    },
                    {
                        "text": "752",
                        "align": "center",
                    },
                    {
                        "text": "347",
                        "align": "center",
                    },
                ],
                [
                    {
                        "text": "✅ پاس دقیق",
                        "align": "center",
                    },
                    {
                        "text": "636 (85%)",
                        "align": "center",
                    },
                    {
                        "text": "228 (66%)",
                        "align": "center",
                    },
                ],
                [
                    {
                        "text": "🚩 کرنر",
                        "align": "center",
                    },
                    {
                        "text": "7",
                        "align": "center",
                    },
                    {
                        "text": "3",
                        "align": "center",
                    },
                ],
                [
                    {
                        "text": "⚠️ خطا",
                        "align": "center",
                    },
                    {
                        "text": "13",
                        "align": "center",
                    },
                    {
                        "text": "21",
                        "align": "center",
                    },
                ],
                [
                    {
                        "text": "🚫 آفساید",
                        "align": "center",
                    },
                    {
                        "text": "2",
                        "align": "center",
                    },
                    {
                        "text": "3",
                        "align": "center",
                    },
                ],
                [
                    {
                        "text": "🟨 کارت زرد",
                        "align": "center",
                    },
                    {
                        "text": "1",
                        "align": "center",
                    },
                    {
                        "text": "5",
                        "align": "center",
                    },
                ],
                [
                    {
                        "text": "🟥 کارت قرمز",
                        "align": "center",
                    },
                    {
                        "text": "0",
                        "align": "center",
                    },
                    {
                        "text": "0",
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

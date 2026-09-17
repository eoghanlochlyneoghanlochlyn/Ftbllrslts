import os

import requests


TELEGRAM_BOT_TOKEN = os.getenv(
    "TELEGRAMBOT"
)

TELEGRAM_CHANNEL = os.getenv(
    "TELEGRAMCHANNEL"
)


def send_telegram(text):
    if not TELEGRAM_BOT_TOKEN:
        raise RuntimeError(
            "TELEGRAMBOT environment variable is missing."
        )

    if not TELEGRAM_CHANNEL:
        raise RuntimeError(
            "TELEGRAMCHANNEL environment variable is missing."
        )

    url = (
        "https://api.telegram.org/"
        f"bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    )

    response = requests.post(
        url,
        data={
            "chat_id": TELEGRAM_CHANNEL,
            "text": text,
        },
        timeout=30,
    )

    print(
        "Telegram status:",
        response.status_code,
    )

    if not response.ok:
        print(response.text)

    response.raise_for_status()

    return response.json()


def send_rich_message(
    rich_message,
):

    if not TELEGRAM_BOT_TOKEN:
        raise RuntimeError(
            "TELEGRAMBOT environment variable is missing."
        )

    if not TELEGRAM_CHANNEL:
        raise RuntimeError(
            "TELEGRAMCHANNEL environment variable is missing."
        )

    url = (
        "https://api.telegram.org/"
        f"bot{TELEGRAM_BOT_TOKEN}/sendRichMessage"
    )

    response = requests.post(
        url,
        json={
            "chat_id": TELEGRAM_CHANNEL,
            "rich_message": rich_message,
        },
        timeout=30,
    )

    print(
        "Telegram Rich Message status:",
        response.status_code,
    )

    if not response.ok:
        print(response.text)

    response.raise_for_status()

    return response.json()


def split_message(
    message,
    max_length=4000,
):
    chunks = []

    remaining = message

    while len(remaining) > max_length:

        cut = remaining.rfind(
            "\n",
            0,
            max_length,
        )

        if cut == -1:
            cut = max_length

        chunks.append(
            remaining[:cut]
        )

        remaining = remaining[
            cut:
        ].lstrip()

    if remaining:
        chunks.append(remaining)

    return chunks


def send_long_message(message):
    chunks = split_message(message)

    for index, chunk in enumerate(
        chunks,
        1,
    ):

        print(
            f"Sending Telegram message "
            f"{index}/{len(chunks)}..."
        )

        send_telegram(chunk)

    return len(chunks)

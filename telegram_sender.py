import os

from telegram import Bot
from telegram.error import TelegramError


TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAMBOT")
TELEGRAM_CHANNEL = os.getenv("TELEGRAMCHANNEL")


async def send_telegram_message(text):
    if not TELEGRAM_BOT_TOKEN:
        print("ERROR: TELEGRAMBOT secret is not available.")
        return False

    if not TELEGRAM_CHANNEL:
        print("ERROR: TELEGRAMCHANNEL secret is not available.")
        return False

    if not text or not text.strip():
        print("ERROR: Telegram message is empty.")
        return False

    bot = Bot(
        token=TELEGRAM_BOT_TOKEN
    )

    try:
        sent_message = await bot.send_message(
            chat_id=TELEGRAM_CHANNEL,
            text=text,
        )

        print(
            "Telegram message sent successfully."
        )

        print(
            f"Telegram message ID: "
            f"{sent_message.message_id}"
        )

        return True

    except TelegramError as exc:
        print(
            f"Telegram error: {exc}"
        )

        return False

    except Exception as exc:
        print(
            f"Unexpected Telegram error: {exc}"
        )

        return False

    finally:
        await bot.shutdown()

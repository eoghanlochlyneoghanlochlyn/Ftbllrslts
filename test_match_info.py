import os
import asyncio
from telegram import Bot

BOT_TOKEN = os.environ["TELEGRAMBOT"]
CHANNEL_ID = os.environ["TELEGRAMCHANNEL"]


async def main():
    bot = Bot(BOT_TOKEN)

    me = await bot.get_me()

    print(f"Connected as @{me.username}")

    await bot.send_message(
        chat_id=CHANNEL_ID,
        text="""
✅ <b>Telegram Test Successful</b>

ربات با موفقیت به کانال متصل شد.

حالا آماده ارسال اطلاعات مسابقات FotMob هستیم.
""",
        parse_mode="HTML",
    )

    print("Message sent successfully.")


if __name__ == "__main__":
    asyncio.run(main())

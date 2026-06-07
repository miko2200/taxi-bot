from telegram import Bot
from telegram.ext import Application
from datetime import datetime
from zoneinfo import ZoneInfo
import asyncio

TOKEN = "8723525696:AAFAV08octm20i12U-jgW6N5Fr2fS5ZW0vk"
CHAT_ID = -1002475950058

async def send_message(context):
    date = datetime.now(
        ZoneInfo("Asia/Almaty")
    ).strftime("%d.%m.%Y")

    text = f"{date}\nТакси\n⬇️⬇️⬇️"

    await context.bot.send_message(
        chat_id=CHAT_ID,
        text=text
    )

app = Application.builder().token(TOKEN).build()

job_queue = app.job_queue

job_queue.run_daily(
    send_message,
    time=datetime.strptime("00:01", "%H:%M").time()
)

app.run_polling()
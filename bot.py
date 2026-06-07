from telegram.ext import (
    Application,
    ContextTypes,
    CommandHandler
)
from datetime import datetime, time
from zoneinfo import ZoneInfo
import random

TOKEN = "8723525696:AAGXtq7GhrnHyelPkWIaFsPyRbcJoiMRd8s"
CHAT_ID = -1002475950058

QUOTES = [
    "Успех любит дисциплину.",
    "Большие результаты складываются из маленьких действий.",
    "Делай сегодня то, за что завтра скажешь себе спасибо.",
    "Главное — двигаться вперёд.",
    "Каждое усилие имеет значение."
]


async def send_message(context: ContextTypes.DEFAULT_TYPE):
    date = datetime.now(
        ZoneInfo("Asia/Almaty")
    ).strftime("%d.%m.%Y")

    quote = random.choice(QUOTES)

    text = (
        f"{date}\n"
        f"Такси\n"
        f"⬇️⬇️⬇️\n\n"
        f"💡 Цитата дня:\n"
        f"{quote}"
    )

    await context.bot.send_message(
        chat_id=CHAT_ID,
        text=text
    )


async def status(update, context):
    now = datetime.now(
        ZoneInfo("Asia/Almaty")
    )

    await update.message.reply_text(
        f"✅ Бот работает\n"
        f"🕒 Время Астана: {now.strftime('%H:%M:%S')}\n"
        f"📅 Сегодня: {now.strftime('%d.%m.%Y')}"
    )


app = Application.builder().token(TOKEN).build()

app.add_handler(
    CommandHandler("status", status)
)

app.job_queue.run_daily(
    send_message,
    time=time(
        hour=10,
        minute=0,
        tzinfo=ZoneInfo("Asia/Almaty")
    )
)

print("Bot started")

app.run_polling()

from telegram.ext import Application, ContextTypes, CommandHandler
from datetime import datetime, time
from zoneinfo import ZoneInfo
import random

TOKEN = "Т8723525696:AAFh6A32bXW48_rqTzTDiQeUO6gvPu2Ebc0"
CHAT_ID = -1002475950058

QUOTES = [
    "Успех любит дисциплину.",
    "Большие результаты складываются из маленьких действий.",
    "Делай сегодня то, за что завтра скажешь себе спасибо.",
    "Главное — двигаться вперёд.",
    "Каждое усилие имеет значение.",
    "Порядок в мелочах даёт результат в большом.",
    "Стабильность начинается с простых ежедневных действий."
]


def get_taxi_text():
    date = datetime.now(
        ZoneInfo("Asia/Almaty")
    ).strftime("%d.%m.%Y")

    quote = random.choice(QUOTES)

    return (
        f"{date}\n"
        f"Такси\n"
        f"⬇️⬇️⬇️\n\n"
        f"💡 Цитата дня:\n"
        f"{quote}"
    )


async def send_message(context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(
        chat_id=CHAT_ID,
        text=get_taxi_text()
    )


async def status_command(update, context):
    now = datetime.now(ZoneInfo("Asia/Almaty"))

    await update.message.reply_text(
        f"✅ Бот работает\n"
        f"🕒 Время Астана: {now.strftime('%H:%M:%S')}\n"
        f"📅 Сегодня: {now.strftime('%d.%m.%Y')}"
    )


async def now_command(update, context):
    await context.bot.send_message(
        chat_id=CHAT_ID,
        text=get_taxi_text()
    )

    await update.message.reply_text(
        "✅ Сообщение отправлено в группу"
    )


app = Application.builder().token(TOKEN).build()

app.add_handler(CommandHandler("status", status_command))
app.add_handler(CommandHandler("now", now_command))

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

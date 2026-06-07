from telegram.ext import Application, ContextTypes
from datetime import datetime, time
from zoneinfo import ZoneInfo

TOKEN = "8723525696:AAE5cmEboXRyEkhPAS2H9MyWSnoYDWOJmOI"
CHAT_ID = -1002475950058


async def send_message(context: ContextTypes.DEFAULT_TYPE):
    date = datetime.now(
        ZoneInfo("Asia/Almaty")
    ).strftime("%d.%m.%Y")

    text = f"{date}\nТакси\n⬇️⬇️⬇️"

    await context.bot.send_message(
        chat_id=CHAT_ID,
        text=text
    )


app = Application.builder().token(TOKEN).build()

app.job_queue.run_daily(
    send_message,
    time=time(
        hour=0,
        minute=1,
        tzinfo=ZoneInfo("Asia/Almaty")
    )
)

print("Bot started")

app.run_polling()

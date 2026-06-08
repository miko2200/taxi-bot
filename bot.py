from telegram.ext import Application, ContextTypes, CommandHandler, MessageHandler, filters
from datetime import datetime, time
from zoneinfo import ZoneInfo
import random
import os
import json
import gspread
from google.oauth2.service_account import Credentials

TOKEN = "8723525696:AAFh6A32bXW48_rqTzTDiQeUO6gvPu2Ebc0"
CHAT_ID = -1002475950058

SPREADSHEET_ID = os.getenv("SPREADSHEET_ID")
SHEET_NAME = os.getenv("SHEET_NAME", "Лист1")
GOOGLE_CREDENTIALS = os.getenv("GOOGLE_CREDENTIALS")

QUOTES = [
    "Успех любит дисциплину.",
    "Большие результаты складываются из маленьких действий.",
    "Делай сегодня то, за что завтра скажешь себе спасибо.",
    "Главное — двигаться вперёд.",
    "Каждое усилие имеет значение."
]


def get_sheet():
    creds_dict = json.loads(GOOGLE_CREDENTIALS)
    scopes = ["https://www.googleapis.com/auth/spreadsheets"]
    creds = Credentials.from_service_account_info(creds_dict, scopes=scopes)
    client = gspread.authorize(creds)
    return client.open_by_key(SPREADSHEET_ID).worksheet(SHEET_NAME)


def get_taxi_text():
    date = datetime.now(ZoneInfo("Asia/Almaty")).strftime("%d.%m.%Y")
    quote = random.choice(QUOTES)

    return (
        f"{date}\n"
        f"Такси\n"
        f"⬇️⬇️⬇️\n\n"
        f"💡 Цитата дня:\n{quote}"
    )


async def send_message(context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(chat_id=CHAT_ID, text=get_taxi_text())


async def status_command(update, context):
    now = datetime.now(ZoneInfo("Asia/Almaty"))
    await update.message.reply_text(
        f"✅ Бот работает\n"
        f"🕒 Время Астана: {now.strftime('%H:%M:%S')}\n"
        f"📅 Сегодня: {now.strftime('%d.%m.%Y')}"
    )


async def now_command(update, context):
    await context.bot.send_message(chat_id=CHAT_ID, text=get_taxi_text())
    await update.message.reply_text("✅ Сообщение отправлено в группу")


def parse_taxi_message(text):
    data = {
        "Дата": "",
        "ФИО": "",
        "Сумма": "",
        "Kaspi": "",
        "Примечание": "-"
    }

    lines = text.splitlines()

    if not lines or lines[0].strip().lower() != "такси":
        return None

    for line in lines[1:]:
        if ":" not in line:
            continue

        key, value = line.split(":", 1)
        key = key.strip().lower()
        value = value.strip()

        if key in ["дата"]:
            data["Дата"] = value
        elif key in ["фио", "имя"]:
            data["ФИО"] = value
        elif key in ["сумма", "оплата"]:
            data["Сумма"] = value
        elif key in ["kaspi", "каспи", "номер"]:
            data["Kaspi"] = value
        elif key in ["примечание", "комментарий"]:
            data["Примечание"] = value or "-"

    if not data["Дата"] or not data["ФИО"] or not data["Сумма"] or not data["Kaspi"]:
        return "missing"

    return data


async def handle_group_message(update, context):
    if not update.message or not update.message.text:
        return

    parsed = parse_taxi_message(update.message.text)

    if parsed is None:
        return

    if parsed == "missing":
        await update.message.reply_text(
            "⚠️ Не хватает данных.\n\n"
            "Заполните так:\n"
            "Такси\n"
            "Дата: 08.06.2026\n"
            "ФИО: Иванов Иван\n"
            "Сумма: 2500\n"
            "Kaspi: 87011234567\n"
            "Примечание: перезаказ"
        )
        return

    now = datetime.now(ZoneInfo("Asia/Almaty"))

    sheet = get_sheet()
    sheet.append_row([
        parsed["Дата"],
        parsed["ФИО"],
        parsed["Сумма"],
        parsed["Kaspi"],
        parsed["Примечание"],
        update.effective_user.username or update.effective_user.full_name,
        now.strftime("%d.%m.%Y %H:%M:%S")
    ])

    await update.message.reply_text("✅ Заявка добавлена в таблицу")


app = Application.builder().token(TOKEN).build()

app.add_handler(CommandHandler("status", status_command))
app.add_handler(CommandHandler("now", now_command))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_group_message))

app.job_queue.run_daily(
    send_message,
    time=time(hour=10, minute=0, tzinfo=ZoneInfo("Asia/Almaty"))
)

print("Bot started")

app.run_polling()

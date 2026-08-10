import asyncio
import html
import json
import logging
import os
import random
import re
from datetime import datetime, time
from decimal import Decimal, InvalidOperation
from zoneinfo import ZoneInfo

import gspread
from google.oauth2.service_account import Credentials
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.constants import ChatType, ParseMode
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    filters,
)


logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger("httpx").setLevel(logging.WARNING)

TIMEZONE = ZoneInfo("Asia/Almaty")

# Секреты и настройки берутся из Variables на Railway.
TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = int(os.getenv("CHAT_ID", "-1002475950058"))
SPREADSHEET_ID = os.getenv("SPREADSHEET_ID")
SHEET_NAME = os.getenv("SHEET_NAME", "Лист1")
GOOGLE_CREDENTIALS = os.getenv("GOOGLE_CREDENTIALS")

KIDBURG_SHEET = "Kidburg"
YONDO_SHEET = "Yondo"

CHOOSE_ACTION, CHOOSE_SHEET, ENTER_AMOUNT, ENTER_DATE, ENTER_PAYER = range(5)

QUOTES = [
    "Успех любит дисциплину.",
    "Большие результаты складываются из маленьких действий.",
    "Делай сегодня то, за что завтра скажешь себе спасибо.",
    "Главное — двигаться вперёд.",
    "Каждое усилие имеет значение.",
]


def get_sheet(sheet_name: str):
    """Открывает указанный лист общей Google-таблицы."""
    if not SPREADSHEET_ID or not GOOGLE_CREDENTIALS:
        raise RuntimeError(
            "Не заданы SPREADSHEET_ID или GOOGLE_CREDENTIALS в Railway Variables"
        )

    creds_dict = json.loads(GOOGLE_CREDENTIALS)
    scopes = ["https://www.googleapis.com/auth/spreadsheets"]
    creds = Credentials.from_service_account_info(creds_dict, scopes=scopes)
    client = gspread.authorize(creds)
    return client.open_by_key(SPREADSHEET_ID).worksheet(sheet_name)


def append_row(sheet_name: str, values: list):
    """Синхронная запись в Google Sheets; вызывается через asyncio.to_thread."""
    worksheet = get_sheet(sheet_name)
    worksheet.append_row(values, value_input_option="RAW")


def get_taxi_text() -> str:
    today = datetime.now(TIMEZONE).strftime("%d.%m.%Y")
    quote = random.choice(QUOTES)
    return (
        f"{today}\n"
        "Такси\n"
        "⬇️⬇️⬇️\n\n"
        f"💡 Цитата дня:\n{quote}"
    )


def taxi_form_template() -> str:
    today = datetime.now(TIMEZONE).strftime("%d.%m.%Y")
    return (
        "Такси\n"
        f"Дата: {today}\n"
        "ФИО: Иванов Иван\n"
        "Сумма: 2500\n"
        "Kaspi: 87011234567\n"
        "Примечание: -"
    )


def main_menu() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("🚕 Шаблон такси", callback_data="action:taxi")],
            [InlineKeyboardButton("🛍 Добавить покупку", callback_data="action:purchase")],
        ]
    )


def sheet_menu() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("🎡 Kidburg", callback_data="sheet:Kidburg"),
                InlineKeyboardButton("🎮 Yondo", callback_data="sheet:Yondo"),
            ],
            [InlineKeyboardButton("⬅️ Назад", callback_data="action:back")],
        ]
    )


def taxi_menu() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("🛍 Добавить покупку", callback_data="action:purchase")],
            [InlineKeyboardButton("⬅️ В главное меню", callback_data="action:back")],
        ]
    )


def sender_name(update: Update) -> str:
    user = update.effective_user
    if not user:
        return "Неизвестно"
    if user.username:
        return f"@{user.username}"
    return user.full_name


def parse_amount(text: str):
    cleaned = text.lower()
    for token in ("тенге", "тг", "₸"):
        cleaned = cleaned.replace(token, "")
    cleaned = re.sub(r"\s+", "", cleaned).replace(",", ".")

    try:
        value = Decimal(cleaned)
    except InvalidOperation:
        return None

    if not value.is_finite() or value <= 0 or value > Decimal("1000000000"):
        return None

    if value == value.to_integral_value():
        return int(value)
    return float(value)


def parse_date(text: str):
    value = text.strip().lower()
    if value == "сегодня":
        return datetime.now(TIMEZONE).strftime("%d.%m.%Y")

    for date_format in ("%d.%m.%Y", "%d.%m.%y"):
        try:
            parsed = datetime.strptime(value, date_format)
            return parsed.strftime("%d.%m.%Y")
        except ValueError:
            continue
    return None


async def send_message(context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(chat_id=CHAT_ID, text=get_taxi_text())


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.pop("purchase", None)

    if update.effective_chat.type != ChatType.PRIVATE:
        await update.message.reply_text(
            "Покупки оформляются в личных сообщениях с ботом. "
            "Откройте бота в личке и нажмите /start."
        )
        return ConversationHandler.END

    await update.message.reply_text(
        "Здравствуйте! 👋\n\n"
        "🚕 Расходы на такси отправляйте в группу «Такси КБ».\n"
        "🛍 Остальные покупки оформляйте здесь, в личных сообщениях.\n\n"
        "Выберите нужное действие:",
        reply_markup=main_menu(),
    )
    return CHOOSE_ACTION


async def show_taxi_template(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    template = html.escape(taxi_form_template())
    await query.edit_message_text(
        "🚕 <b>Такси отправляйте в группу «Такси КБ»</b> одним сообщением "
        "по этому шаблону:\n\n"
        f"<pre>{template}</pre>\n"
        "Замените пример своими данными.",
        parse_mode=ParseMode.HTML,
        reply_markup=taxi_menu(),
    )
    return CHOOSE_ACTION


async def show_purchase_destinations(
    update: Update, context: ContextTypes.DEFAULT_TYPE
):
    query = update.callback_query
    await query.answer()
    context.user_data.pop("purchase", None)
    await query.edit_message_text(
        "🛍 Куда записать покупку?",
        reply_markup=sheet_menu(),
    )
    return CHOOSE_SHEET


async def back_to_main(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    context.user_data.pop("purchase", None)
    await query.edit_message_text(
        "Выберите нужное действие:",
        reply_markup=main_menu(),
    )
    return CHOOSE_ACTION


async def select_sheet(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    sheet_name = query.data.split(":", 1)[1]
    if sheet_name not in {KIDBURG_SHEET, YONDO_SHEET}:
        await query.edit_message_text("Неизвестный лист. Нажмите /start ещё раз.")
        return ConversationHandler.END

    context.user_data["purchase"] = {"sheet": sheet_name}
    await query.edit_message_text(
        f"Вы выбрали <b>{html.escape(sheet_name)}</b>.\n\n"
        "Введите сумму покупки, например: <code>12500</code>",
        parse_mode=ParseMode.HTML,
    )
    return ENTER_AMOUNT


async def receive_amount(update: Update, context: ContextTypes.DEFAULT_TYPE):
    amount = parse_amount(update.message.text)
    if amount is None:
        await update.message.reply_text(
            "⚠️ Не получилось распознать сумму. Введите только число, например: 12500"
        )
        return ENTER_AMOUNT

    context.user_data["purchase"]["amount"] = amount
    await update.message.reply_text(
        "Введите дату покупки в формате ДД.ММ.ГГГГ, например: 10.08.2026",
        reply_markup=InlineKeyboardMarkup(
            [[InlineKeyboardButton("📅 Сегодня", callback_data="date:today")]]
        ),
    )
    return ENTER_DATE


async def receive_date(update: Update, context: ContextTypes.DEFAULT_TYPE):
    purchase_date = parse_date(update.message.text)
    if purchase_date is None:
        await update.message.reply_text(
            "⚠️ Неверная дата. Введите её в формате ДД.ММ.ГГГГ, например: 10.08.2026"
        )
        return ENTER_DATE

    context.user_data["purchase"]["date"] = purchase_date
    await update.message.reply_text("Кто платил? Напишите имя и фамилию.")
    return ENTER_PAYER


async def receive_today(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    context.user_data["purchase"]["date"] = datetime.now(TIMEZONE).strftime(
        "%d.%m.%Y"
    )
    await query.edit_message_reply_markup(reply_markup=None)
    await query.message.reply_text("Кто платил? Напишите имя и фамилию.")
    return ENTER_PAYER


async def receive_payer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    payer = " ".join(update.message.text.split())
    if len(payer) < 2 or len(payer) > 100:
        await update.message.reply_text("⚠️ Укажите имя плательщика текстом.")
        return ENTER_PAYER

    purchase = context.user_data.get("purchase")
    if not purchase or not all(
        key in purchase for key in ("sheet", "amount", "date")
    ):
        await update.message.reply_text("Данные устарели. Нажмите /start и начните заново.")
        return ConversationHandler.END

    saved_at = datetime.now(TIMEZONE).strftime("%d.%m.%Y %H:%M:%S")
    row = [
        purchase["date"],
        purchase["amount"],
        payer,
        sender_name(update),
        saved_at,
    ]

    try:
        await asyncio.to_thread(append_row, purchase["sheet"], row)
    except Exception:
        logger.exception("Не удалось записать покупку в Google Sheets")
        await update.message.reply_text(
            "❌ Не удалось записать данные в таблицу. Проверьте доступ к листу "
            "и попробуйте отправить имя ещё раз."
        )
        return ENTER_PAYER

    sheet_name = purchase["sheet"]
    amount = purchase["amount"]
    purchase_date = purchase["date"]
    context.user_data.pop("purchase", None)

    await update.message.reply_text(
        "✅ Покупка добавлена в таблицу\n\n"
        f"Лист: {sheet_name}\n"
        f"Дата: {purchase_date}\n"
        f"Сумма: {amount} ₸\n"
        f"Кто платил: {payer}",
        reply_markup=main_menu(),
    )
    return CHOOSE_ACTION


async def cancel_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.pop("purchase", None)
    await update.message.reply_text(
        "Оформление отменено. Выберите действие:",
        reply_markup=main_menu(),
    )
    return CHOOSE_ACTION


async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    now = datetime.now(TIMEZONE)
    await update.message.reply_text(
        "✅ Бот работает\n"
        f"🕒 Время Астана: {now.strftime('%H:%M:%S')}\n"
        f"📅 Сегодня: {now.strftime('%d.%m.%Y')}"
    )


async def now_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(chat_id=CHAT_ID, text=get_taxi_text())
    await update.message.reply_text("✅ Сообщение отправлено в группу")


def parse_taxi_message(text: str):
    data = {
        "Дата": "",
        "ФИО": "",
        "Сумма": "",
        "Kaspi": "",
        "Примечание": "-",
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

        if key == "дата":
            data["Дата"] = value
        elif key in {"фио", "имя"}:
            data["ФИО"] = value
        elif key in {"сумма", "оплата"}:
            data["Сумма"] = value
        elif key in {"kaspi", "каспи", "номер"}:
            data["Kaspi"] = value
        elif key in {"примечание", "комментарий"}:
            data["Примечание"] = value or "-"

    if not all((data["Дата"], data["ФИО"], data["Сумма"], data["Kaspi"])):
        return "missing"
    return data


async def handle_group_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if (
        not update.message
        or not update.message.text
        or update.effective_chat.type not in {ChatType.GROUP, ChatType.SUPERGROUP}
    ):
        return

    parsed = parse_taxi_message(update.message.text)
    if parsed is None:
        return

    if parsed == "missing":
        await update.message.reply_text(
            "⚠️ Не хватает данных.\n\n"
            "Заполните так:\n"
            f"{taxi_form_template()}"
        )
        return

    now = datetime.now(TIMEZONE)
    row = [
        parsed["Дата"],
        parsed["ФИО"],
        parsed["Сумма"],
        parsed["Kaspi"],
        parsed["Примечание"],
        sender_name(update),
        now.strftime("%d.%m.%Y %H:%M:%S"),
    ]

    try:
        await asyncio.to_thread(append_row, SHEET_NAME, row)
    except Exception:
        logger.exception("Не удалось записать такси в Google Sheets")
        await update.message.reply_text(
            "❌ Не удалось добавить заявку в таблицу. Попробуйте ещё раз позже."
        )
        return

    await update.message.reply_text("✅ Заявка добавлена в таблицу")


async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
    logger.error("Ошибка при обработке Telegram update", exc_info=context.error)


def build_app() -> Application:
    if not TOKEN:
        raise RuntimeError("Добавьте BOT_TOKEN в Railway Variables")

    app = Application.builder().token(TOKEN).build()

    purchase_conversation = ConversationHandler(
        entry_points=[CommandHandler("start", start_command)],
        states={
            CHOOSE_ACTION: [
                CallbackQueryHandler(show_taxi_template, pattern=r"^action:taxi$"),
                CallbackQueryHandler(
                    show_purchase_destinations, pattern=r"^action:purchase$"
                ),
                CallbackQueryHandler(back_to_main, pattern=r"^action:back$"),
            ],
            CHOOSE_SHEET: [
                CallbackQueryHandler(
                    select_sheet, pattern=r"^sheet:(Kidburg|Yondo)$"
                ),
                CallbackQueryHandler(back_to_main, pattern=r"^action:back$"),
            ],
            ENTER_AMOUNT: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, receive_amount)
            ],
            ENTER_DATE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, receive_date),
                CallbackQueryHandler(receive_today, pattern=r"^date:today$"),
            ],
            ENTER_PAYER: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, receive_payer)
            ],
        },
        fallbacks=[
            CommandHandler("start", start_command),
            CommandHandler("cancel", cancel_command),
        ],
        allow_reentry=True,
    )

    app.add_handler(purchase_conversation)
    app.add_handler(CommandHandler("status", status_command))
    app.add_handler(CommandHandler("now", now_command))
    app.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, handle_group_message)
    )
    app.add_error_handler(error_handler)

    app.job_queue.run_daily(
        send_message,
        time=time(hour=10, minute=0, tzinfo=TIMEZONE),
    )
    return app


if __name__ == "__main__":
    logger.info("Bot started")
    build_app().run_polling()

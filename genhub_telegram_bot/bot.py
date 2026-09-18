import logging
import os
import sqlite3
from datetime import datetime, timezone
from typing import Optional

from dotenv import load_dotenv
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    filters,
)

load_dotenv()
TOKEN = os.getenv("BOT_TOKEN")
ADMIN_CHAT_ID = os.getenv("ADMIN_CHAT_ID")
DB_PATH = os.getenv("DB_PATH", "genhub.db")

if not TOKEN:
    raise RuntimeError("BOT_TOKEN is missing. Add it to your .env file.")

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

NAME, SERVICE, DETAILS, BUDGET = range(4)


def db_connect():
    connection = sqlite3.connect(DB_PATH)
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS requests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            telegram_user_id INTEGER NOT NULL,
            username TEXT,
            name TEXT NOT NULL,
            service TEXT NOT NULL,
            details TEXT NOT NULL,
            budget TEXT,
            created_at TEXT NOT NULL
        )
        """
    )
    return connection


def save_request(user_id: int, username: Optional[str], name: str, service: str, details: str, budget: str):
    with db_connect() as connection:
        connection.execute(
            """
            INSERT INTO requests
            (telegram_user_id, username, name, service, details, budget, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (user_id, username, name, service, details, budget, datetime.now(timezone.utc).isoformat()),
        )


def main_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🛠 Our Services", callback_data="services")],
        [InlineKeyboardButton("💼 Hire Talent", callback_data="hire")],
        [InlineKeyboardButton("🚀 Join as Freelancer", callback_data="freelancer")],
        [InlineKeyboardButton("📩 Contact Team", callback_data="contact")],
    ])


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "👋 Welcome to GenHub Works!\n\n"
        "Your hub for digital services, freelance opportunities, and skilled talent.\n\n"
        "Choose an option below to get started."
    )
    await update.message.reply_text(text, reply_markup=main_menu())


async def services(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text(
        "🛠 Our Services\n\n"
        "• Social media management\n"
        "• Digital marketing\n"
        "• Graphic design\n"
        "• Video editing\n"
        "• Website and app development\n"
        "• Content writing\n"
        "• SEO and more",
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Main Menu", callback_data="menu")]]),
    )


async def freelancer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text(
        "🚀 To join as a freelancer, send your profile details to our team.\n\n"
        "Please use /contact and include your skills, experience, portfolio link, and preferred services.",
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Main Menu", callback_data="menu")]]),
    )


async def contact(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text(
        "📩 Contact Team\n\n"
        "Use /hire to submit a service requirement, or send a message to the official GenHub Works contact account.",
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Main Menu", callback_data="menu")]]),
    )


async def menu_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text(
        "Choose an option below to get started.", reply_markup=main_menu()
    )


async def hire_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    if update.callback_query:
        query = update.callback_query
        await query.answer()
        await query.message.reply_text("💼 Great! What is your name?")
    else:
        await update.message.reply_text("💼 Great! What is your name?")
    return NAME


async def get_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["name"] = update.message.text.strip()
    await update.message.reply_text(
        "Which service do you need?\n\n"
        "Example: Social media management, website development, video editing"
    )
    return SERVICE


async def get_service(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["service"] = update.message.text.strip()
    await update.message.reply_text("Describe your requirement in a few sentences.")
    return DETAILS


async def get_details(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["details"] = update.message.text.strip()
    await update.message.reply_text("What is your approximate budget? Type 'not decided' if unsure.")
    return BUDGET


async def get_budget(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["budget"] = update.message.text.strip()
    user = update.effective_user
    data = context.user_data
    save_request(
        user_id=user.id,
        username=user.username,
        name=data["name"],
        service=data["service"],
        details=data["details"],
        budget=data["budget"],
    )

    admin_text = (
        "📥 New GenHub Works request\n\n"
        f"Name: {data['name']}\n"
        f"Username: @{user.username if user.username else 'not available'}\n"
        f"Service: {data['service']}\n"
        f"Details: {data['details']}\n"
        f"Budget: {data['budget']}\n"
        f"Telegram ID: {user.id}"
    )

    if ADMIN_CHAT_ID:
        try:
            await context.bot.send_message(chat_id=int(ADMIN_CHAT_ID), text=admin_text)
        except Exception:
            logger.exception("Could not notify admin")

    await update.message.reply_text(
        "✅ Thanks! Your requirement has been submitted.\n"
        "Our team will review it and contact you soon.",
        reply_markup=main_menu(),
    )
    context.user_data.clear()
    return ConversationHandler.END


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    await update.message.reply_text("Cancelled. Use /start whenever you want to begin again.")
    return ConversationHandler.END


async def unknown(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Please use /start to open the GenHub Works menu.")


def build_application():
    application = Application.builder().token(TOKEN).build()

    hire_conversation = ConversationHandler(
        entry_points=[
            CommandHandler("hire", hire_start),
            CallbackQueryHandler(hire_start, pattern="^hire$"),
        ],
        states={
            NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_name)],
            SERVICE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_service)],
            DETAILS: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_details)],
            BUDGET: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_budget)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    application.add_handler(CommandHandler("start", start))
    application.add_handler(hire_conversation)
    application.add_handler(CallbackQueryHandler(services, pattern="^services$"))
    application.add_handler(CallbackQueryHandler(freelancer, pattern="^freelancer$"))
    application.add_handler(CallbackQueryHandler(contact, pattern="^contact$"))
    application.add_handler(CallbackQueryHandler(menu_callback, pattern="^menu$"))
    application.add_handler(MessageHandler(filters.COMMAND, unknown))
    return application


if __name__ == "__main__":
    logger.info("Starting GenHub Works bot")
    build_application().run_polling(allowed_updates=Update.ALL_TYPES)

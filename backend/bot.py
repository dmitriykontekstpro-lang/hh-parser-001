from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler
from backend.config import config
from backend.tasks import run_scraper_task
import logging
import asyncio

logger = logging.getLogger(__name__)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=(
            "🤖 *HH Scraper Bot активен!*\n\n"
            "Команды:\n"
            "/run — запустить парсинг прямо сейчас\n"
            "/status — состояние системы\n"
        ),
        parse_mode='Markdown'
    )

async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=(
            "✅ *Система работает*\n\n"
            f"Интервал запуска: каждые {config.HH_SEARCH_INTERVAL_HOURS} ч.\n"
            "Используйте /run для ручного запуска."
        ),
        parse_mode='Markdown'
    )

async def run_now(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="🚀 Запускаю парсинг вручную... Это займет несколько минут."
    )
    try:
        count = await run_scraper_task()
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=f"✅ Парсинг завершен. Новых вакансий: *{count}*",
            parse_mode='Markdown'
        )
    except Exception as e:
        logger.error(f"Error in manual run: {e}")
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=f"❌ Ошибка: {e}"
        )

def create_bot():
    app = ApplicationBuilder().token(config.TELEGRAM_BOT_TOKEN).build()
    app.add_handler(CommandHandler('start', start))
    app.add_handler(CommandHandler('status', status))
    app.add_handler(CommandHandler('run', run_now))
    return app

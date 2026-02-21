from telegram import Update, BotCommand
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler
from backend.config import config
from backend.tasks import run_scraper_task
from backend.status_checker import check_vacancy_status_task
import logging

logger = logging.getLogger(__name__)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=(
            "🤖 *HH Scraper Bot*\n\n"
            "Доступные команды:\n\n"
            "🔍 /find — найти новые вакансии прямо сейчас\n"
            "🗂 /check — проверить статус вакансий (архив)\n"
            "📊 /status — состояние системы\n"
        ),
        parse_mode='Markdown'
    )


async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=(
            "✅ *Система работает*\n\n"
            "📅 *Расписание:*\n"
            "• Парсинг вакансий: 09:00 и 18:00 МСК\n"
            "• Проверка архива: 01:00 и 14:00 МСК\n\n"
            "🔍 /find — запустить парсинг вручную\n"
            "🗂 /check — проверить архив вручную"
        ),
        parse_mode='Markdown'
    )


async def find_vacancies(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Runs the scraper task manually."""
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="🔍 Запускаю поиск новых вакансий... Это займет несколько минут."
    )
    try:
        count = await run_scraper_task()
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=f"✅ Поиск завершен. Новых вакансий: *{count}*",
            parse_mode='Markdown'
        )
    except Exception as e:
        logger.error(f"Error in /find: {e}")
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=f"❌ Ошибка при поиске: {e}"
        )


async def check_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Runs the vacancy status checker manually."""
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="🗂 Запускаю проверку статуса вакансий... Это займет несколько минут."
    )
    try:
        archived = await check_vacancy_status_task()
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=f"✅ Проверка завершена. В архиве: *{archived}*",
            parse_mode='Markdown'
        )
    except Exception as e:
        logger.error(f"Error in /check: {e}")
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=f"❌ Ошибка при проверке: {e}"
        )


async def post_init(application):
    """Set bot command menu."""
    await application.bot.set_my_commands([
        BotCommand("find",   "🔍 Найти новые вакансии"),
        BotCommand("check",  "🗂 Проверить статус вакансий"),
        BotCommand("status", "📊 Состояние системы"),
        BotCommand("start",  "🤖 Справка"),
    ])


def create_bot():
    app = (
        ApplicationBuilder()
        .token(config.TELEGRAM_BOT_TOKEN)
        .post_init(post_init)
        .build()
    )
    app.add_handler(CommandHandler('start',  start))
    app.add_handler(CommandHandler('status', status))
    app.add_handler(CommandHandler('find',   find_vacancies))
    app.add_handler(CommandHandler('check',  check_status))
    # Keep old /run as alias for /find
    app.add_handler(CommandHandler('run',    find_vacancies))
    return app

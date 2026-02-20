from telegram import Update, Bot
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler, filters
from backend.config import config
import logging

# Setup logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(chat_id=update.effective_chat.id, text="SEARCH_BOT Active! Use /status to check.")

async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # TODO: Fetch stats from DB
    await context.bot.send_message(chat_id=update.effective_chat.id, text="System is running. Scheduled updates at 09:00 and 18:00.")

async def run_now(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(chat_id=update.effective_chat.id, text="Triggering manual run...")
    # This needs to trigger the scraping task. 
    # We might need a shared object or queue for this.
    # For now, just a placeholder acknowledgement.
    from backend.main import trigger_scraping_job # Circular import risk?
    # Better to have a callback.

def create_bot():
    app = ApplicationBuilder().token(config.TELEGRAM_BOT_TOKEN).build()
    
    app.add_handler(CommandHandler('start', start))
    app.add_handler(CommandHandler('status', status))
    app.add_handler(CommandHandler('run', run_now))
    
    return app

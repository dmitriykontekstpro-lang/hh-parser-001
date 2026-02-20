import logging
import asyncio
from fastapi import FastAPI
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from backend.tasks import run_scraper_task
from backend.config import config
from backend.bot import create_bot
from telegram.ext import Application

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()
scheduler = AsyncIOScheduler()
bot_app: Application = None

@app.on_event("startup")
async def startup_event():
    # 1. Start Scheduler
    job_kwargs = dict(
        max_instances=1,        # Never run 2 tasks in parallel
        coalesce=True,          # Skip missed runs
        misfire_grace_time=600  # 10 min grace
    )
    # 9:00 Moscow (UTC+3 = 06:00 UTC)
    scheduler.add_job(run_scraper_task, "cron", hour=6, minute=0, **job_kwargs)
    # 18:00 Moscow (UTC+3 = 15:00 UTC)
    scheduler.add_job(run_scraper_task, "cron", hour=15, minute=0, **job_kwargs)
    scheduler.start()
    logger.info("Scheduler: runs at 09:00 and 18:00 Moscow time.")
    logger.info("Scheduler started.")

    # 2. Start Telegram Bot
    if config.TELEGRAM_BOT_TOKEN:
        global bot_app
        bot_app = create_bot()
        await bot_app.initialize()
        await bot_app.start()
        await bot_app.updater.start_polling()
        logger.info("Telegram Bot started.")

@app.on_event("shutdown")
async def shutdown_event():
    scheduler.shutdown()
    if bot_app:
        await bot_app.updater.stop()
        await bot_app.stop()
        await bot_app.shutdown()

@app.get("/")
def read_root():
    return {"status": "running", "service": "HH Scraper Cloud"}

@app.post("/trigger")
async def trigger_run():
    # Run in background
    asyncio.create_task(run_scraper_task())
    return {"status": "Triggered manual run"}

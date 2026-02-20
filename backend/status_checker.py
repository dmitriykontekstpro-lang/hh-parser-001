import asyncio
import random
import logging
from playwright.async_api import async_playwright
from fake_useragent import UserAgent
from backend.database import get_vacancies_without_status, update_vacancy_status
from backend.config import config
from telegram import Bot

logger = logging.getLogger(__name__)

ARCHIVE_TEXT = "Вакансия в архиве"


async def check_vacancy_status_task():
    """
    Runs through all vacancies with empty status_vacancy.
    Visits each URL via Playwright and checks if 'Вакансия в архиве' is on the page.
    If yes → sets status_vacancy = 'archiv'.
    If not found → leaves field empty (does nothing).
    Runs twice a day: 01:00 and 14:00 Moscow time.
    """
    logger.info("=" * 50)
    logger.info("STATUS CHECK TASK STARTED")
    logger.info("=" * 50)

    vacancies = get_vacancies_without_status(limit=200)

    if not vacancies:
        logger.info("No vacancies without status. Nothing to check.")
        return

    logger.info(f"Found {len(vacancies)} vacancies to check.")

    ua = UserAgent()
    archived_count = 0
    errors = 0

    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            args=[
                '--no-sandbox',
                '--disable-setuid-sandbox',
                '--disable-blink-features=AutomationControlled',
                '--disable-gpu',
            ]
        )
        context = await browser.new_context(
            user_agent=ua.random,
            viewport={'width': 1920, 'height': 1080},
            locale='ru-RU',
            timezone_id='Europe/Moscow'
        )
        await context.add_init_script(
            "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
        )
        page = await context.new_page()

        try:
            for item in vacancies:
                vacancy_id = item['id']
                link = item['vacancy_link']

                try:
                    logger.info(f"Checking: {link}")
                    await page.goto(link, wait_until='domcontentloaded', timeout=30000)
                    await asyncio.sleep(random.uniform(1, 2.5))

                    # Check for archive text on page
                    content = await page.content()
                    if ARCHIVE_TEXT in content:
                        update_vacancy_status(vacancy_id, "archiv")
                        archived_count += 1
                        logger.info(f"  → ARCHIVED: {link}")
                    else:
                        logger.info(f"  → Active: {link}")
                        # Leave status_vacancy empty — do nothing

                except Exception as e:
                    logger.error(f"Error checking {link}: {e}")
                    errors += 1
                    continue

        finally:
            await browser.close()

    summary = (
        f"🗂 *Проверка статуса вакансий завершена*\n\n"
        f"Проверено: {len(vacancies)}\n"
        f"В архиве: *{archived_count}*\n"
        f"Ошибок: {errors}"
    )
    logger.info(f"STATUS CHECK DONE. Archived: {archived_count}, Errors: {errors}")

    # Notify via Telegram
    if config.TELEGRAM_BOT_TOKEN and config.TELEGRAM_CHAT_ID:
        try:
            bot = Bot(token=config.TELEGRAM_BOT_TOKEN)
            await bot.send_message(
                chat_id=config.TELEGRAM_CHAT_ID,
                text=summary,
                parse_mode='Markdown'
            )
        except Exception as e:
            logger.error(f"Telegram notify failed: {e}")

    return archived_count

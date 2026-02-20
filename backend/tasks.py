import logging
from backend.database import get_search_queries, get_stop_words, vacancy_exists, insert_vacancy
from backend.scraper import HHScraper
from backend.config import config
from telegram import Bot

logger = logging.getLogger(__name__)


async def run_scraper_task():
    """
    Main 4-step scraping pipeline:
    1. Get search queries from Supabase (search_queries_hhnew)
    2. For each query: collect all links from all search pages, filter by stop words
    3. Remove duplicates (check vacancies_hhnew table)
    4. Parse full details for new links and save to Supabase
    """
    logger.info("=" * 50)
    logger.info("SCRAPER TASK STARTED")
    logger.info("=" * 50)

    # Step 1: Load settings from Supabase
    queries = get_search_queries()
    stop_words = get_stop_words()

    logger.info(f"Queries: {queries}")
    logger.info(f"Stop words: {stop_words}")

    if not queries:
        msg = "No active search queries found. Add them to search_queries_hhnew table."
        logger.warning(msg)
        await _notify(msg)
        return 0

    scraper = HHScraper()
    new_vacancies_count = 0
    errors = 0
    telegram_summary = []

    for query in queries:
        logger.info(f"\n--- Processing query: '{query}' ---")
        try:
            # Step 2: Collect links from ALL pages, with stop-word filtering on titles
            all_links = await scraper.get_search_links(query, stop_words=stop_words)

            if not all_links:
                logger.info(f"No links found for '{query}'")
                continue

            # Step 3: Filter out already existing vacancies (deduplication)
            new_links = [link for link in all_links if not vacancy_exists(link)]
            logger.info(
                f"Query '{query}': {len(all_links)} total, "
                f"{len(all_links) - len(new_links)} duplicates removed, "
                f"{len(new_links)} new."
            )

            if not new_links:
                logger.info(f"All vacancies for '{query}' already in DB. Skipping.")
                continue

            # Step 4: Parse full details in batches of 10
            chunk_size = 10
            for i in range(0, len(new_links), chunk_size):
                chunk = new_links[i:i + chunk_size]
                logger.info(f"Batch {i // chunk_size + 1}: scraping {len(chunk)} vacancies...")

                scraped_data = await scraper.scrape_vacancies_batch(chunk)

                for data in scraped_data:
                    title = data.get('parameters_json', {}).get('title', 'Без названия')
                    company = data.get('parameters_json', {}).get('company', '')

                    # Save to Supabase
                    record = {
                        "vacancy_link": data['link'],
                        "raw_text": data['raw_text'],
                        "parameters_json": data['parameters_json'],
                        "parsing_date_time": data['parsing_date_time']
                    }

                    res = insert_vacancy(record)
                    if res:
                        new_vacancies_count += 1
                        telegram_summary.append(f"• [{title}]({data['link']}) — {company}")
                        logger.info(f"Saved: {title}")
                    else:
                        errors += 1
                        logger.error(f"Failed to save: {data['link']}")

        except Exception as e:
            logger.error(f"Error processing query '{query}': {e}")
            errors += 1

    # Send Telegram summary
    summary_text = (
        f"✅ *Парсинг завершен*\n\n"
        f"Новых вакансий: *{new_vacancies_count}*\n"
        f"Ошибок: {errors}\n"
    )
    if telegram_summary:
        summary_text += "\n*Последние найденные:*\n" + "\n".join(telegram_summary[:10])

    await _notify(summary_text)

    logger.info(f"TASK DONE. New: {new_vacancies_count}, Errors: {errors}")
    return new_vacancies_count


async def _notify(text: str):
    """Sends a message to Telegram."""
    if not config.TELEGRAM_BOT_TOKEN or not config.TELEGRAM_CHAT_ID:
        return
    try:
        bot = Bot(token=config.TELEGRAM_BOT_TOKEN)
        await bot.send_message(
            chat_id=config.TELEGRAM_CHAT_ID,
            text=text,
            parse_mode='Markdown',
            disable_web_page_preview=True
        )
    except Exception as e:
        logger.error(f"Telegram notification failed: {e}")

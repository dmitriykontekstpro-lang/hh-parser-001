import logging
from backend.database import get_search_queries, get_stop_words, vacancy_exists, insert_vacancy
from backend.scraper import HHScraper
from backend.config import config
from telegram import Bot

logger = logging.getLogger(__name__)


async def run_scraper_task():
    """
    Sequential scraping pipeline — one query at a time:

    For EACH query from search_queries_hhnew:
      1. Collect links from all search pages (with stop-word filter)
      2. Remove duplicates (check vacancies_hhnew)
      3. Parse full details for each new link
      4. Save to Supabase IMMEDIATELY after parsing
      → Then move to next query

    This ensures data is saved progressively, even if the task is interrupted.
    """
    logger.info("=" * 50)
    logger.info("SCRAPER TASK STARTED")
    logger.info("=" * 50)

    queries = get_search_queries()
    stop_words = get_stop_words()

    logger.info(f"Queries ({len(queries)}): {queries}")
    logger.info(f"Stop words ({len(stop_words)}): {stop_words[:10]}...")

    if not queries:
        await _notify("⚠️ Нет активных поисковых запросов в search_queries_hhnew.")
        return 0

    scraper = HHScraper()
    total_new = 0
    total_errors = 0
    all_summary = []

    for idx, query in enumerate(queries, 1):
        logger.info(f"\n{'='*40}")
        logger.info(f"[{idx}/{len(queries)}] Query: '{query}'")
        logger.info(f"{'='*40}")

        query_new = 0
        query_errors = 0

        try:
            # Step 1: Collect links (all pages, with stop-word filtering)
            links = await scraper.get_search_links(query, stop_words=stop_words)

            if not links:
                logger.info(f"No links found for '{query}'. Next.")
                continue

            # Step 2: Deduplicate against Supabase
            new_links = [link for link in links if not vacancy_exists(link)]
            logger.info(
                f"'{query}': {len(links)} found, "
                f"{len(links) - len(new_links)} already in DB, "
                f"{len(new_links)} new."
            )

            if not new_links:
                logger.info(f"All vacancies for '{query}' already saved. Next.")
                continue

            # Step 3+4: Parse details and save EACH vacancy immediately
            chunk_size = 10
            for i in range(0, len(new_links), chunk_size):
                chunk = new_links[i:i + chunk_size]
                logger.info(f"Batch {i // chunk_size + 1}: parsing {len(chunk)} vacancies...")

                scraped = await scraper.scrape_vacancies_batch(chunk)

                for data in scraped:
                    title = data.get('parameters_json', {}).get('title', 'Без названия')
                    company = data.get('parameters_json', {}).get('company', '')

                    record = {
                        "vacancy_link": data['link'],
                        "raw_text": data['raw_text'],
                        "parameters_json": data['parameters_json'],
                        "parsing_date_time": data['parsing_date_time']
                    }

                    res = insert_vacancy(record)
                    if res:
                        query_new += 1
                        logger.info(f"  ✅ Saved: {title} — {company}")
                    else:
                        query_errors += 1
                        logger.error(f"  ❌ Failed: {data['link']}")

            # Summary for this query
            if query_new > 0:
                all_summary.append(f"• *{query}*: +{query_new} вакансий")

            # Notify after each query
            await _notify(
                f"🔍 Запрос *\"{query}\"* выполнен.\n"
                f"Найдено и сохранено: *{query_new}* вакансий"
            )

            logger.info(f"[{idx}/{len(queries)}] Done: '{query}' → new={query_new}, errors={query_errors}")

        except Exception as e:
            logger.error(f"Error processing '{query}': {e}")
            query_errors += 1

        total_new += query_new
        total_errors += query_errors

    # Final Telegram report
    text = (
        f"✅ *Парсинг завершен*\n\n"
        f"Запросов обработано: {len(queries)}\n"
        f"Новых вакансий: *{total_new}*\n"
        f"Ошибок: {total_errors}\n"
    )
    if all_summary:
        text += "\n*По запросам:*\n" + "\n".join(all_summary[:15])

    await _notify(text)

    logger.info(f"TASK DONE. Total new: {total_new}, errors: {total_errors}")
    return total_new


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

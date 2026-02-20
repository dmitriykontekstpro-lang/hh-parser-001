import asyncio
import logging
from backend.database import get_search_queries, get_stop_words, vacancy_exists, insert_vacancy
from backend.scraper import HHScraper
from backend.config import config
from telegram import Bot

logger = logging.getLogger(__name__)

async def run_scraper_task():
    """Main scraping task."""
    logger.info("Starting Scraper Task...")
    
    # 1. Get Settings
    queries = get_search_queries()
    stop_words = get_stop_words()
    
    if not queries:
        logger.warning("No active search queries found. Exiting task.")
        return 0

    scraper = HHScraper()
    new_vacancies_count = 0
    total_processed = 0
    errors = 0
    
    telegram_summary = []

    # 2. Iterate Queries
    for query in queries:
        logger.info(f"Searching for: {query}")
        try:
            # Step 1: Get Links
            links = await scraper.get_search_links(query)
            if not links:
                continue

            # Step 2: Filter existing
            new_links = []
            for link in links:
                if not vacancy_exists(link):
                    new_links.append(link)
            
            logger.info(f"Found {len(links)} links, {len(new_links)} are new.")
            
            if not new_links:
                continue
                
            # Step 3: Scrape details in batch
            # Process in chunks of 10 to be safe
            chunk_size = 10
            for i in range(0, len(new_links), chunk_size):
                chunk = new_links[i:i + chunk_size]
                scraped_data = await scraper.scrape_vacancies_batch(chunk)
                
                # Step 4: Process Results
                for data in scraped_data:
                    title = data.get('parameters_json', {}).get('title', '')
                    company = data.get('parameters_json', {}).get('company', '')
                    
                    # Stop word check
                    if any(sw.lower() in title.lower() for sw in stop_words):
                        logger.info(f"Filtered by stop word: {title}")
                        continue
                        
                    # Insert
                    # Prepare for insertion
                    record = {
                        "vacancy_link": data['link'],
                        "raw_text": data['raw_text'],
                        "parameters_json": data['parameters_json'],
                        "parsing_date_time": data['parsing_date_time']
                    }
                    
                    res = insert_vacancy(record)
                    if res:
                        new_vacancies_count += 1
                        telegram_summary.append(f"[{title}]({data['link']}) - {company}")
                    else:
                        errors += 1
                
        except Exception as e:
            logger.error(f"Error processing query {query}: {e}")
            errors += 1
            
    # 3. Notify via Telegram
    if config.TELEGRAM_BOT_TOKEN and config.TELEGRAM_CHAT_ID:
        try:
            bot = Bot(token=config.TELEGRAM_BOT_TOKEN)
            message = (f"Job Scraper Run Complete.\n"
                       f"New Vacancies: {new_vacancies_count}\n"
                       f"Errors: {errors}\n\n")
            
            # Send first 10
            if telegram_summary:
                message += "Latest:\n" + "\n".join(telegram_summary[:10])
                
            await bot.send_message(chat_id=config.TELEGRAM_CHAT_ID, text=message, parse_mode='Markdown')
        except Exception as e:
            logger.error(f"Telegram notification failed: {e}")

    logger.info(f"Task Complete. New: {new_vacancies_count}, Errors: {errors}")
    return new_vacancies_count

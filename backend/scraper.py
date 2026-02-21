import asyncio
import random
import logging
from typing import List, Dict
from urllib.parse import quote
from playwright.async_api import async_playwright
from fake_useragent import UserAgent
from datetime import datetime


def _is_blocked_by_stop_words(title: str, stop_words: List[str]) -> bool:
    """
    Returns True if the vacancy title should be EXCLUDED.

    Rule: A vacancy is blocked if its title contains the EXACT PHRASE from
    the stop_words_hhnew.word column:
    - All words must be present ADJACENT (next to each other)
    - In the SAME ORDER as in Supabase
    - In the SAME FORM (but case-insensitive)

    Examples (stop word = "Директор по маркетингу"):
      "Директор по маркетингу"         → BLOCKED ✓
      "Зам. директор по маркетингу"    → BLOCKED ✓ (phrase is contained)
      "директор по маркетингу (CMO)"   → BLOCKED ✓ (case-insensitive)
      "Директор маркетингу"            → NOT blocked ✗ (words not adjacent)
      "По маркетингу директор"         → NOT blocked ✗ (wrong order)
    """
    title_lower = title.lower()
    for phrase in stop_words:
        phrase = phrase.strip()
        if not phrase:
            continue
        if phrase.lower() in title_lower:
            return True
    return False


logger = logging.getLogger(__name__)


class HHScraper:
    def __init__(self):
        self.ua = UserAgent()
        self.base_url = "https://hh.ru"

    async def _create_browser(self, playwright):
        """Creates a browser with anti-detection settings."""
        browser = await playwright.chromium.launch(
            headless=True,
            args=[
                '--disable-blink-features=AutomationControlled',
                '--no-sandbox',
                '--disable-setuid-sandbox',
                '--disable-infobars',
                '--disable-accelerated-2d-canvas',
                '--disable-gpu',
            ]
        )
        context = await browser.new_context(
            user_agent=self.ua.random,
            viewport={'width': 1920, 'height': 1080},
            locale='ru-RU',
            timezone_id='Europe/Moscow'
        )
        await context.add_init_script(
            "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
        )
        return browser, context

    def _query_to_slug(self, query: str) -> str:
        """
        Converts query like "Python разработчик" to URL slug like "python-razrabotchik".
        HH.ru accepts translit or just Russian in the URL path.
        We use the search endpoint instead and pass query as text param.
        """
        return quote(query)

    async def get_search_links(self, query: str, stop_words: List[str] = None) -> List[str]:
        """
        Stage 1: Scrapes ALL vacancy links from search results for a given query.
        Paginates through all pages automatically.
        Filters out vacancies whose TITLES contain stop words.
        Returns clean list of unique links.
        """
        if stop_words is None:
            stop_words = []

        all_links = []
        page_num = 0
        slug = self._query_to_slug(query)

        async with async_playwright() as p:
            browser, context = await self._create_browser(p)
            page = await context.new_page()

            try:
                while True:
                    # Build URL: /search/vacancy?text=QUERY&page=N&area=113 (Russia)
                    url = f"{self.base_url}/search/vacancy?text={slug}&page={page_num}&area=113"
                    logger.info(f"[Stage 1] Page {page_num}: {url}")

                    await page.goto(url, wait_until='domcontentloaded', timeout=60000)
                    await asyncio.sleep(random.uniform(2, 4))
                    await page.mouse.wheel(0, 800)

                    # Get all vacancy cards on this page
                    items = await page.query_selector_all('a[data-qa="serp-item__title"]')

                    if not items:
                        logger.info(f"[Stage 1] No more vacancies on page {page_num}. Done.")
                        break

                    page_links_added = 0
                    for item in items:
                        # Get title for stop word filtering BEFORE saving link
                        title_el = await item.query_selector('span') or item
                        title = await item.inner_text() if item else ""
                        title = title.strip()

                        # Apply stop word filter (exact phrase match)
                        if _is_blocked_by_stop_words(title, stop_words):
                            logger.info(f"[Filter] Skipped by stop word: '{title}'")
                            continue

                        link = await item.get_attribute('href')
                        if link:
                            # Clean URL params (keep only base vacancy URL)
                            link = link.split('?')[0].strip()
                            if link not in all_links:
                                all_links.append(link)
                                page_links_added += 1

                    logger.info(
                        f"[Stage 1] Page {page_num}: found {len(items)} items, "
                        f"added {page_links_added} after filtering."
                    )

                    # Check if there's a next page
                    next_btn = await page.query_selector('a[data-qa="pager-next"]')
                    if not next_btn:
                        logger.info("[Stage 1] No next page button. All pages scraped.")
                        break

                    page_num += 1
                    await asyncio.sleep(random.uniform(1, 2))

            except Exception as e:
                logger.error(f"[Stage 1] Error scraping search for '{query}': {e}")
            finally:
                await browser.close()

        logger.info(f"[Stage 1] Total links collected for '{query}': {len(all_links)}")
        return all_links

    async def scrape_vacancies_batch(self, links: List[str]) -> List[Dict]:
        """
        Stage 2: For each link, opens the vacancy page and extracts full details.
        Returns list of dicts with raw_text and parameters_json.
        """
        results = []
        if not links:
            return []

        async with async_playwright() as p:
            browser, context = await self._create_browser(p)
            page = await context.new_page()

            try:
                for link in links:
                    try:
                        logger.info(f"[Stage 2] Scraping: {link}")
                        await page.goto(link, wait_until='domcontentloaded', timeout=45000)
                        await asyncio.sleep(random.uniform(1.5, 3))

                        # Captcha check
                        if await page.query_selector("text='Введите код'") or \
                           await page.query_selector("text='Enter captcha'"):
                            logger.error("[Stage 2] CAPTCHA detected! Skipping batch.")
                            break

                        # Extract fields
                        title = ""
                        title_el = await page.query_selector('h1[data-qa="vacancy-title"]')
                        if title_el:
                            title = (await title_el.inner_text()).strip()

                        description = ""
                        desc_el = await page.query_selector('div[data-qa="vacancy-description"]')
                        if desc_el:
                            description = (await desc_el.inner_text()).strip()

                        salary = None
                        for sal_sel in [
                            '[data-qa="vacancy-salary-compensation-type-net"]',
                            '[data-qa="vacancy-salary-compensation-type-gross"]',
                            '[data-qa="vacancy-salary"]'
                        ]:
                            sal_el = await page.query_selector(sal_sel)
                            if sal_el:
                                salary = (await sal_el.inner_text()).strip()
                                break

                        company = None
                        comp_el = await page.query_selector('a[data-qa="vacancy-company-name"]')
                        if comp_el:
                            company = (await comp_el.inner_text()).strip()

                        experience = None
                        exp_el = await page.query_selector('span[data-qa="vacancy-experience"]')
                        if exp_el:
                            experience = (await exp_el.inner_text()).strip()

                        raw_text = "\n".join(filter(None, [title, salary, company, experience, "", description]))

                        results.append({
                            "link": link,
                            "raw_text": raw_text,
                            "parameters_json": {
                                "title": title,
                                "salary": salary,
                                "company": company,
                                "experience": experience,
                                "url": link
                            },
                            "parsing_date_time": datetime.utcnow().isoformat()
                        })

                    except Exception as e:
                        logger.error(f"[Stage 2] Error scraping {link}: {e}")
                        continue

            except Exception as e:
                logger.error(f"[Stage 2] Batch error: {e}")
            finally:
                await browser.close()

        return results

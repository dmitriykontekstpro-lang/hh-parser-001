import asyncio
import random
import logging
from typing import List, Optional, Dict
from playwright.async_api import async_playwright, Page, BrowserContext
from fake_useragent import UserAgent
from datetime import datetime
import json

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class HHScraper:
    def __init__(self):
        self.ua = UserAgent()
        self.base_url = "https://hh.ru"

    async def _create_context(self, playwright) -> BrowserContext:
        """Creates a browser context with anti-detection settings."""
        user_agent = self.ua.random
        
        browser = await playwright.chromium.launch(
            headless=True,
            args=[
                '--disable-blink-features=AutomationControlled',
                '--no-sandbox',
                '--disable-setuid-sandbox',
                '--disable-infobars',
                '--window-position=0,0',
                '--ignore-certificate-errors',
                '--disable-accelerated-2d-canvas',
                '--disable-gpu',
            ]
        )
        
        context = await browser.new_context(
            user_agent=user_agent,
            viewport={'width': 1920, 'height': 1080},
            locale='ru-RU',
            timezone_id='Europe/Moscow'
        )
        
        await context.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        
        return context, browser

    async def get_search_links(self, query: str, pages: int = 2) -> List[str]:
        """Scrapes vacancy links from search results."""
        links = []
        async with async_playwright() as p:
            context, browser = await self._create_context(p)
            page = await context.new_page()
            
            try:
                for page_num in range(pages):
                    url = f"{self.base_url}/search/vacancy?text={query}&page={page_num}&area=113"
                    logger.info(f"Navigating to search page {page_num}: {url}")
                    
                    await page.goto(url, wait_until='domcontentloaded', timeout=60000)
                    await asyncio.sleep(random.uniform(2, 4))
                    
                    # Scroll
                    await page.mouse.wheel(0, 500)
                    
                    # Extract links
                    elements = await page.query_selector_all('a[data-qa="serp-item__title"]')
                    
                    if not elements:
                        logger.warning(f"No vacancies found on page {page_num}")
                        break
                        
                    for el in elements:
                        link = await el.get_attribute('href')
                        if link:
                            link = link.split('?')[0]
                            links.append(link)
                            
                    logger.info(f"Found {len(elements)} links on page {page_num}")
                    
            except Exception as e:
                logger.error(f"Error scraping search {query}: {e}")
            finally:
                await browser.close()
                
        return list(set(links))

    async def scrape_vacancies_batch(self, links: List[str]) -> List[Dict]:
        """Scrapes a batch of vacancy links reusing the browser."""
        results = []
        if not links:
            return []

        async with async_playwright() as p:
            context, browser = await self._create_context(p)
            page = await context.new_page()
            
            try:
                for link in links:
                    try:
                        logger.info(f"Scraping vacancy: {link}")
                        await page.goto(link, wait_until='domcontentloaded', timeout=45000)
                        await asyncio.sleep(random.uniform(1.5, 3.5))

                        # Check for captcha or verify title exists
                        if await page.query_selector("text='Enter captcha'"):
                             logger.error("CAPTCHA detected, aborting batch")
                             break

                        # Extract Data
                        title = await page.inner_text('h1[data-qa="vacancy-title"]') if await page.query_selector('h1[data-qa="vacancy-title"]') else "No Title"
                        description = await page.inner_text('div[data-qa="vacancy-description"]') if await page.query_selector('div[data-qa="vacancy-description"]') else ""
                        
                        # Try both net and gross selectors for salary
                        salary_net = await page.query_selector('span[data-qa="vacancy-salary-compensation-type-net"]')
                        salary_gross = await page.query_selector('span[data-qa="vacancy-salary-compensation-type-gross"]')
                        salary = await salary_net.inner_text() if salary_net else (await salary_gross.inner_text() if salary_gross else None)
                        
                        company = await page.inner_text('a[data-qa="vacancy-company-name"]') if await page.query_selector('a[data-qa="vacancy-company-name"]') else None
                        experience = await page.inner_text('span[data-qa="vacancy-experience"]') if await page.query_selector('span[data-qa="vacancy-experience"]') else None

                        raw_text = f"{title}\n{salary or ''}\n{company or ''}\n\n{description}"
                        
                        params = {
                            "title": title,
                            "salary": salary,
                            "company": company,
                            "experience": experience,
                            "url": link
                        }
                        
                        results.append({
                            "link": link,
                            "raw_text": raw_text,
                            "parameters_json": params,
                            "parsing_date_time": datetime.utcnow().isoformat()
                        })
                        
                    except Exception as e:
                        logger.error(f"Error scraping {link}: {e}")
                        continue
                        
            except Exception as e:
                logger.error(f"Batch scraping error: {e}")
            finally:
                await browser.close()
                
        return results

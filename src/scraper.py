import asyncio
import random
import logging
from typing import Optional, Dict, Any, Callable
from playwright.async_api import async_playwright, Browser, Page, BrowserContext
import config
from src.parser import parse_product_page, extract_product_id

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class TikTokScraper:
    """
    TikTok Shop scraper using Playwright with stealth mode
    
    NOTE: Due to TikTok's CAPTCHA protection, this scraper:
    1. Runs browser in non-headless mode (visible browser)
    2. Uses stealth techniques to avoid detection
    3. May require manual CAPTCHA solving on first run
    """
    
    def __init__(self):
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.playwright = None
        self.page: Optional[Page] = None  # Reuse single page
    
    async def __aenter__(self):
        """Async context manager entry"""
        await self.start()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self.close()
    
    async def start(self):
        """Start browser with persistent context to remember cookies"""
        self.playwright = await async_playwright().start()
        
        logger.info("Starting browser with persistent context")
        logger.info("NOTE: Browser will stay open to maintain session cookies")
        
        # Use persistent context to save cookies/session
        # This way, once CAPTCHA is solved, it stays solved
        user_data_dir = config.SCRAPING_CONFIG['user_data_dir']
        
        # Setup proxy (HTTP with auth is supported!)
        proxy_config = None
        if config.PROXY_TYPE == "http":
            proxy_config = {
                "server": f"http://{config.PROXY_SERVER}:{config.PROXY_PORT}",
                "username": config.PROXY_USERNAME,
                "password": config.PROXY_PASSWORD,
            }
            logger.info(f"Using HTTP proxy: {config.PROXY_SERVER}:{config.PROXY_PORT}")
        
        self.context = await self.playwright.chromium.launch_persistent_context(
            user_data_dir,
            headless=config.SCRAPING_CONFIG['headless'],
            proxy=proxy_config,
            args=[
                '--disable-blink-features=AutomationControlled',
                '--disable-dev-shm-usage',
                '--no-sandbox',
            ],
            viewport={'width': 1920, 'height': 1080},
            locale='en-US',
            timezone_id='America/New_York',
            user_agent=random.choice(config.USER_AGENTS),
        )
        
        # Import cookies from file if exists (from real browser)
        import json
        from pathlib import Path
        cookies_file = Path(config.BASE_DIR) / "cookies.json"
        if cookies_file.exists():
            logger.info("Loading cookies from cookies.json...")
            try:
                with open(cookies_file, 'r') as f:
                    cookies = json.load(f)
                
                # Convert cookie format if needed
                if isinstance(cookies, list) and len(cookies) > 0:
                    # Fix Cookie Editor format for Playwright
                    playwright_cookies = []
                    for cookie in cookies:
                        # Convert to Playwright format
                        pc = {
                            'name': cookie['name'],
                            'value': cookie['value'],
                            'domain': cookie['domain'],
                            'path': cookie['path'],
                        }
                        
                        # Handle sameSite (null -> omit, or convert to valid value)
                        if cookie.get('sameSite'):
                            # Capitalize first letter for Playwright
                            same_site = str(cookie['sameSite']).capitalize()
                            if same_site in ['Strict', 'Lax', 'None']:
                                pc['sameSite'] = same_site
                        
                        # Handle expiration
                        if 'expirationDate' in cookie and cookie['expirationDate']:
                            pc['expires'] = cookie['expirationDate']
                        
                        # Handle secure/httpOnly
                        if 'secure' in cookie:
                            pc['secure'] = cookie['secure']
                        if 'httpOnly' in cookie:
                            pc['httpOnly'] = cookie['httpOnly']
                        
                        playwright_cookies.append(pc)
                    
                    await self.context.add_cookies(playwright_cookies)
                    logger.info(f"✅ Loaded {len(playwright_cookies)} cookies from file!")
                else:
                    logger.warning("Empty or invalid cookies file")
            except Exception as e:
                logger.error(f"Failed to load cookies: {e}")
        
        # Create single reusable page
        self.page = await self.context.new_page()
    
    async def close(self):
        """Close browser and playwright"""
        if self.context:
            await self.context.close()
        if self.playwright:
            await self.playwright.stop()
    
    async def fetch_product(self, url: str, max_retries: int = None) -> Dict[str, Any]:
        """
        Fetch a single product page and extract data
        
        Args:
            url: Product URL
            max_retries: Maximum retry attempts (defaults to config)
        
        Returns:
            Dict with product data or error info
        """
        if max_retries is None:
            max_retries = config.SCRAPING_CONFIG['max_retries']
        
        product_id = extract_product_id(url)
        
        for attempt in range(max_retries):
            try:
                # Reuse existing page instead of creating new one
                logger.info(f"Fetching (attempt {attempt + 1}/{max_retries}): {url}")
                
                # Navigate to page
                response = await self.page.goto(url, wait_until='domcontentloaded', timeout=60000)
                
                if not response or response.status != 200:
                    logger.warning(f"Non-200 status for {url}")
                    if attempt < max_retries - 1:
                        await asyncio.sleep(3)
                        continue
                
                # Check for CAPTCHA
                title = await self.page.title()
                if 'security' in title.lower() or 'captcha' in title.lower():
                    logger.warning(f"CAPTCHA detected! Page title: {title}")
                    logger.warning("Please solve CAPTCHA manually in the browser window...")
                    
                    # Wait for user to solve CAPTCHA (check for title change)
                    for wait_attempt in range(60):  # Wait up to 60 seconds
                        await asyncio.sleep(1)
                        new_title = await self.page.title()
                        if 'security' not in new_title.lower() and 'captcha' not in new_title.lower():
                            logger.info("CAPTCHA appears to be solved! Continuing...")
                            break
                    else:
                        logger.error("CAPTCHA not solved in time")
                        continue
                
                # Wait for product content to load
                await asyncio.sleep(3)
                
                # Get page content
                html_content = await self.page.content()
                
                # Parse content
                parsed_data = parse_product_page(html_content)
                
                # Validate required fields
                if not parsed_data['title']:
                    logger.warning(f"No title found for {url}")
                    if attempt < max_retries - 1:
                        await asyncio.sleep(2)
                        continue
                
                if parsed_data['sold_count'] is None:
                    logger.warning(f"No sold count found for {url}")
                
                # Random delay before next request
                delay = random.uniform(
                    config.SCRAPING_CONFIG['delay_min'],
                    config.SCRAPING_CONFIG['delay_max']
                )
                await asyncio.sleep(delay)
                
                return {
                    'product_id': product_id,
                    'product_url': url,
                    'product_title': parsed_data['title'],
                    'sold_count': parsed_data['sold_count'],
                    'price': parsed_data.get('price'),
                    'status': 'success' if parsed_data['sold_count'] is not None else 'no_sold_count',
                    'error_message': None
                }
                
            except Exception as e:
                logger.error(f"Error fetching {url} (attempt {attempt + 1}): {str(e)}")
                
                if attempt < max_retries - 1:
                    await asyncio.sleep(3)
                    continue
                else:
                    return {
                        'product_id': product_id,
                        'product_url': url,
                        'product_title': None,
                        'sold_count': None,
                        'price': None,
                        'status': 'error',
                        'error_message': str(e)
                    }
        
        return {
            'product_id': product_id,
            'product_url': url,
            'product_title': None,
            'sold_count': None,
            'price': None,
            'status': 'error',
            'error_message': 'All retries failed'
        }
    
    async def fetch_products(
        self,
        urls: list,
        on_progress: Optional[Callable[[int, int], Any]] = None,
    ) -> list:
        """
        Fetch multiple products sequentially

        Args:
            urls: List of product URLs
            on_progress: Optional callback(completed_count, total) after each URL
                (also called once at start with (0, total)).

        Returns:
            List of product data dicts
        """
        results = []
        total = len(urls)
        if on_progress:
            on_progress(0, total)

        for idx, url in enumerate(urls, 1):
            logger.info(f"Progress: {idx}/{total}")

            result = await self.fetch_product(url)
            results.append(result)
            if on_progress:
                on_progress(idx, total)

            # Progress indicator
            if idx % 10 == 0:
                success_count = sum(1 for r in results if r['status'] == 'success')
                logger.info(f"Processed {idx}/{total} - Success: {success_count}")

        return results

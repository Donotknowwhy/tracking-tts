import asyncio
import random
import logging
from typing import Optional, Dict, Any, Callable
from playwright.async_api import async_playwright, Browser, Page, BrowserContext
import config
from src.parser import parse_product_page, extract_product_id

# ─── SadCaptcha auto-solve helpers ─────────────────────────────────────────────

def _sadcaptcha_available() -> bool:
    return bool(getattr(config, "SADCAPTCHA_API_KEY", ""))


async def _try_solve_captcha(page: Page) -> bool:
    """
    Attempt to auto-solve CAPTCHA on the given page using SadCaptcha API.
    Returns True if solved (page is no longer a CAPTCHA page), False otherwise.
    Safe to call even when API key is not set (returns False immediately).
    """
    api_key = getattr(config, "SADCAPTCHA_API_KEY", "") or ""
    if not api_key:
        return False

    try:
        from tiktok_captcha_solver import AsyncPlaywrightSolver

        proxy_str = getattr(config, "PROXY_URL", None)
        solver = AsyncPlaywrightSolver(page, api_key, proxy=proxy_str)
        for attempt in range(3):
            try:
                logger.info("SadCaptcha: attempting solve (attempt %s/3)…", attempt + 1)
                await solver.solve_captcha_if_present(captcha_detect_timeout=15, retries=1)
                await asyncio.sleep(3)
                new_title = await page.title()
                if not _page_title_is_captcha(new_title):
                    logger.info("SadCaptcha: CAPTCHA cleared!")
                    return True
                logger.warning("SadCaptcha: CAPTCHA still present after attempt %s", attempt + 1)
            except Exception as e:
                logger.warning("SadCaptcha attempt %s error: %s", attempt + 1, e)
                await asyncio.sleep(2)
        return False
    except Exception as e:
        logger.warning("Failed to init SadCaptcha solver: %s", e)
        return False

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ─── Stealth / fingerprint helpers ────────────────────────────────────────────

import random
import time
import math

_STEALTH_CHROME_ARGS = [
    '--disable-blink-features=AutomationControlled',
    '--disable-dev-shm-usage',
    '--no-sandbox',
    '--disable-setuid-sandbox',
    '--disable-features=IsolateOrigins,AutomationDetector,AutomationImplied',
    '--no-first-run',
    '--no-zygote',
    '--disable-background-networking',
    '--disable-background-timer-throttling',
    '--disable-backgrounding-occluded-windows',
    '--disable-client-side-phishing-detection',
    '--disable-default-apps',
    '--disable-extensions',
    '--disable-hang-monitor',
    '--disable-popup-blocking',
    '--disable-prompt-on-repost',
    '--disable-sync',
    '--disable-translate',
    '--enable-features=NetworkService,NetworkServiceInProcess',
    '--force-color-profile=srgb',
    '--metrics-recording-only',
    '--password-store=basic',
]

_VIEWPORT_POOL = [
    {'width': 1920, 'height': 1080},
    {'width': 1366, 'height': 768},
    {'width': 1440, 'height': 900},
    {'width': 1536, 'height': 864},
    {'width': 1280, 'height': 720},
]

_LOCALE_POOL = ['en-US', 'en-GB', 'en-CA']

_TIMEZONE_POOL = [
    'America/New_York',
    'America/Chicago',
    'America/Los_Angeles',
    'America/Denver',
]


def _gauss_delay(min_sec: float, max_sec: float) -> float:
    """Gaussian-like delay: mean=(min+max)/2, clamped to [min, max]."""
    mean = (min_sec + max_sec) / 2
    std = (max_sec - min_sec) / 6
    delay = random.gauss(mean, std)
    return max(min_sec, min(max_sec, delay))


def _random_viewport() -> dict:
    return random.choice(_VIEWPORT_POOL)


def _random_locale() -> str:
    return random.choice(_LOCALE_POOL)


def _random_timezone() -> str:
    return random.choice(_TIMEZONE_POOL)


# ─── CAPTCHA helper ────────────────────────────────────────────────────────────

def _page_title_is_captcha(title: str) -> bool:
    t = (title or "").lower()
    return "security" in t or "captcha" in t


class CaptchaError(Exception):
    """Raised when TikTok blocks with CAPTCHA during scraping."""

    def __init__(self, url: str, title: str):
        self.url = url
        self.title = title
        super().__init__(f"CAPTCHA block on {url} (title: {title})")


class TikTokScraper:
    """
    TikTok Shop scraper using Playwright with stealth mode
    
    NOTE: Due to TikTok's CAPTCHA protection, this scraper:
    1. Runs browser in headless or visible mode (configurable)
    2. Uses stealth techniques to avoid detection
    3. May require manual CAPTCHA solving on first run
    4. Supports concurrent fetching (configurable concurrency per job)
    """
    
    def __init__(self, user_data_dir: str = None):
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.playwright = None
        self._user_data_dir = user_data_dir or config.SCRAPING_CONFIG['user_data_dir']
    
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
        user_data_dir = self._user_data_dir
        
        # Setup proxy (HTTP with auth is supported!)
        proxy_config = None
        if config.PROXY_TYPE == "http":
            proxy_config = {
                "server": f"http://{config.PROXY_SERVER}:{config.PROXY_PORT}",
                "username": config.PROXY_USERNAME,
                "password": config.PROXY_PASSWORD,
            }
            logger.info(f"Using HTTP proxy: {config.PROXY_SERVER}:{config.PROXY_PORT}")
        
        # Randomize fingerprint per browser launch
        viewport = _random_viewport()
        locale = _random_locale()
        timezone = _random_timezone()
        user_agent = random.choice(config.USER_AGENTS)

        logger.info(
            "Launching browser — viewport=%s locale=%s tz=%s ua=%s",
            viewport, locale, timezone,
            user_agent[:60],
        )

        self.context = await self.playwright.chromium.launch_persistent_context(
            user_data_dir,
            headless=config.SCRAPING_CONFIG['headless'],
            proxy=proxy_config,
            args=_STEALTH_CHROME_ARGS,
            viewport=viewport,
            locale=locale,
            timezone_id=timezone,
            user_agent=user_agent,
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
                        
                        # sameSite: Cookie-Editor / Chrome export dùng strict|lax|no_restriction;
                        # Playwright cần Strict|Lax|None (None = cross-site).
                        ss = cookie.get("sameSite")
                        if ss is not None and ss != "":
                            sl = str(ss).strip().lower().replace("-", "_")
                            _ss_map = {
                                "strict": "Strict",
                                "lax": "Lax",
                                "none": "None",
                                "no_restriction": "None",
                            }
                            pw_ss = _ss_map.get(sl)
                            if not pw_ss:
                                cap = str(ss).strip().capitalize()
                                if cap in ("Strict", "Lax", "None"):
                                    pw_ss = cap
                            if pw_ss:
                                pc["sameSite"] = pw_ss
                        
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
    
    async def close(self):
        """Close browser and playwright"""
        if self.context:
            await self.context.close()
        if self.playwright:
            await self.playwright.stop()
    
    async def fetch_product(self, page: Page, url: str, max_retries: int = None) -> Dict[str, Any]:
        """
        Fetch a single product page and extract data
        
        Args:
            page: Playwright Page instance (one per concurrent fetch)
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
                logger.info(f"Fetching (attempt {attempt + 1}/{max_retries}): {url}")
                
                # Navigate to page
                response = await page.goto(url, wait_until='domcontentloaded', timeout=60000)
                
                if not response or response.status != 200:
                    logger.warning(f"Non-200 status for {url}")
                    if attempt < max_retries - 1:
                        await asyncio.sleep(3)
                        continue
                
                # CAPTCHA: thử auto-solve trước (SadCaptcha API).
                # Nếu không có API key hoặc fail → fallback: chờ tay (headless=False) hoặc fail ngay.
                title = await page.title()
                if _page_title_is_captcha(title):
                    headless = bool(config.SCRAPING_CONFIG.get("headless", True))
                    logger.warning(f"CAPTCHA detected! Page title: {title}")

                    # 1) Thử auto-solve với SadCaptcha trên page hiện tại
                    if _sadcaptcha_available():
                        auto_solved = await _try_solve_captcha(page)
                        if auto_solved:
                            logger.info("CAPTCHA auto-solved — continuing…")
                        else:
                            logger.warning("SadCaptcha could not solve CAPTCHA.")
                    else:
                        # Không có API key
                        auto_solved = False

                    # 2) Nếu chưa solve được
                    if not auto_solved:
                        if headless:
                            logger.warning(
                                "CAPTCHA unsolved (headless=True) — dừng job."
                            )
                            raise CaptchaError(url, title)

                        # Fallback: chờ người giải tay trên cửa sổ browser
                        wait_max = max(
                            60,
                            int(config.SCRAPING_CONFIG.get("captcha_wait_seconds", 600)),
                        )
                        logger.info(
                            "headless=False: waiting up to %s s for manual solve…",
                            wait_max,
                        )
                        solved = False
                        for _ in range(wait_max):
                            await asyncio.sleep(1)
                            new_title = await page.title()
                            if not _page_title_is_captcha(new_title):
                                logger.info("CAPTCHA manually solved — continuing…")
                                solved = True
                                break
                        if not solved:
                            logger.error("CAPTCHA unsolved after max wait — failing job.")
                            raise CaptchaError(url, title)
                
                # Wait for product content to load (human-like delay)
                await asyncio.sleep(_gauss_delay(2, 5))

                # Get page content
                html_content = await page.content()

                # Parse content
                parsed_data = parse_product_page(html_content)

                # Validate required fields
                if not parsed_data['title']:
                    logger.warning(f"No title found for {url}")
                    if attempt < max_retries - 1:
                        await asyncio.sleep(_gauss_delay(2, 5))
                        continue

                if parsed_data['sold_count'] is None:
                    logger.warning(f"No sold count found for {url}")

                # Random delay before next request (human-like)
                delay = _gauss_delay(
                    config.SCRAPING_CONFIG['delay_min'],
                    config.SCRAPING_CONFIG['delay_max'],
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

            except CaptchaError:
                # Do NOT retry CAPTCHA — re-raise immediately so the job aborts
                # instead of wasting time on retries that will also hit CAPTCHA.
                raise

            except Exception as e:
                logger.error(f"Error fetching {url} (attempt {attempt + 1}): {str(e)}")

                if attempt < max_retries - 1:
                    await asyncio.sleep(_gauss_delay(3, 8))
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
        Fetch multiple products with controlled concurrency (semaphore-based).

        Args:
            urls: List of product URLs
            on_progress: Optional callback(completed_count, total) after each URL
                (also called once at start with (0, total)).

        Returns:
            List of product data dicts
        """
        total = len(urls)
        if on_progress:
            on_progress(0, total)
        
        concurrency = config.SCRAPING_CONFIG.get('concurrency', 3)
        semaphore = asyncio.Semaphore(concurrency)
        results = [None] * total
        completed = 0
        completed_lock = asyncio.Lock()

        async def fetch_with_limit(idx: int, url: str) -> None:
            nonlocal completed
            async with semaphore:
                # Create a new page for this fetch
                page = await self.context.new_page()
                try:
                    result = await self.fetch_product(page, url)
                    results[idx] = result
                finally:
                    await page.close()
                
                async with completed_lock:
                    completed += 1
                    if on_progress:
                        on_progress(completed, total)
                    if completed % 10 == 0 or completed == total:
                        success_count = sum(1 for r in results if r and r.get('status') == 'success')
                        logger.info(f"Processed {completed}/{total} - Success: {success_count}")

        tasks = [fetch_with_limit(i, url) for i, url in enumerate(urls)]
        await asyncio.gather(*tasks)
        
        return results

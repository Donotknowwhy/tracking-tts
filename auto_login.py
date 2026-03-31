"""
Automatic TikTok login with email/password
Fully automated - no manual steps required
"""

import asyncio
from playwright.async_api import async_playwright, Page
import config
from pathlib import Path
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def auto_login_tiktok(email: str, password: str) -> bool:
    """
    Automatically login to TikTok with email/password
    
    Args:
        email: TikTok account email
        password: TikTok account password
    
    Returns:
        True if login successful, False otherwise
    """
    browser_profile = config.SCRAPING_CONFIG['user_data_dir']
    
    logger.info("Starting automatic TikTok login...")
    
    async with async_playwright() as p:
        context = await p.chromium.launch_persistent_context(
            browser_profile,
            headless=False,
            args=['--disable-blink-features=AutomationControlled'],
            viewport={'width': 1280, 'height': 900},
        )
        
        page = context.pages[0] if context.pages else await context.new_page()
        
        try:
            # Navigate to TikTok login page
            logger.info("Navigating to TikTok login page...")
            await page.goto('https://www.tiktok.com/login/phone-or-email/email', 
                          wait_until='domcontentloaded', timeout=60000)
            
            await asyncio.sleep(3)
            
            # Fill email
            logger.info("Entering email...")
            email_selectors = [
                'input[name="email"]',
                'input[type="text"]',
                'input[placeholder*="email" i]',
                'input[placeholder*="Email" i]',
            ]
            
            email_filled = False
            for selector in email_selectors:
                try:
                    await page.wait_for_selector(selector, timeout=5000)
                    await page.fill(selector, email)
                    email_filled = True
                    logger.info("✅ Email entered")
                    break
                except:
                    continue
            
            if not email_filled:
                logger.error("❌ Could not find email input field")
                return False
            
            await asyncio.sleep(1)
            
            # Fill password
            logger.info("Entering password...")
            password_selectors = [
                'input[name="password"]',
                'input[type="password"]',
            ]
            
            password_filled = False
            for selector in password_selectors:
                try:
                    await page.wait_for_selector(selector, timeout=5000)
                    await page.fill(selector, password)
                    password_filled = True
                    logger.info("✅ Password entered")
                    break
                except:
                    continue
            
            if not password_filled:
                logger.error("❌ Could not find password input field")
                return False
            
            await asyncio.sleep(1)
            
            # Click login button
            logger.info("Clicking login button...")
            login_button_selectors = [
                'button[type="submit"]',
                'button:has-text("Log in")',
                'button:has-text("Login")',
                '[data-e2e="login-button"]',
            ]
            
            login_clicked = False
            for selector in login_button_selectors:
                try:
                    await page.click(selector, timeout=5000)
                    login_clicked = True
                    logger.info("✅ Login button clicked")
                    break
                except:
                    continue
            
            if not login_clicked:
                logger.error("❌ Could not find login button")
                return False
            
            # Wait for login to complete
            logger.info("Waiting for login to complete...")
            await asyncio.sleep(10)
            
            # Check if login successful
            current_url = page.url
            title = await page.title()
            
            if 'login' in current_url.lower():
                logger.error("❌ Still on login page - login may have failed")
                logger.error(f"   Current URL: {current_url}")
                logger.error(f"   Page title: {title}")
                
                # Check for error messages
                page_text = await page.inner_text('body')
                if 'incorrect' in page_text.lower() or 'wrong' in page_text.lower():
                    logger.error("   Error: Incorrect credentials")
                elif 'verification' in page_text.lower() or 'code' in page_text.lower():
                    logger.error("   Error: 2FA/verification required")
                    logger.error("   Please use manual login: python setup_login.py")
                
                return False
            
            logger.info("✅ Login successful!")
            logger.info(f"   Current URL: {current_url}")
            logger.info(f"   Page title: {title}")
            
            # Test TikTok Shop access
            logger.info("Testing TikTok Shop access...")
            test_url = "https://www.tiktok.com/shop"
            await page.goto(test_url, wait_until='domcontentloaded', timeout=30000)
            await asyncio.sleep(3)
            
            shop_title = await page.title()
            logger.info(f"Shop page title: {shop_title}")
            
            # Keep browser open for a moment
            logger.info("Login complete! Keeping browser open for 5 seconds...")
            await asyncio.sleep(5)
            
            await context.close()
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Login failed: {e}")
            await context.close()
            return False

async def check_login_status() -> bool:
    """
    Check if already logged in to TikTok
    
    Returns:
        True if logged in, False otherwise
    """
    browser_profile = config.SCRAPING_CONFIG['user_data_dir']
    
    if not Path(browser_profile).exists():
        return False
    
    logger.info("Checking existing login status...")
    
    async with async_playwright() as p:
        context = await p.chromium.launch_persistent_context(
            browser_profile,
            headless=True,
        )
        
        page = context.pages[0] if context.pages else await context.new_page()
        
        try:
            await page.goto('https://www.tiktok.com/', timeout=20000)
            await asyncio.sleep(2)
            
            # Check if logged in by looking for profile elements
            page_content = await page.content()
            
            # Simple heuristic: logged in users won't see "Log in" button prominently
            is_logged_in = 'login' not in page_content.lower()[:5000]
            
            await context.close()
            
            return is_logged_in
            
        except Exception as e:
            logger.error(f"Error checking login status: {e}")
            await context.close()
            return False

if __name__ == '__main__':
    import sys
    
    if len(sys.argv) < 3:
        print("Usage: python auto_login.py <email> <password>")
        print()
        print("Example:")
        print("  python auto_login.py user@example.com mypassword123")
        print()
        print("This will automatically login to TikTok and save the session.")
        sys.exit(1)
    
    email = sys.argv[1]
    password = sys.argv[2]
    
    print("="*80)
    print("🔐 Automatic TikTok Login")
    print("="*80)
    print(f"Email: {email}")
    print(f"Password: {'*' * len(password)}")
    print()
    
    success = asyncio.run(auto_login_tiktok(email, password))
    
    if success:
        print()
        print("="*80)
        print("✅ LOGIN SUCCESSFUL!")
        print("="*80)
        print()
        print("Session saved. You can now run:")
        print("  python auto_track.py product_urls.txt")
        print()
    else:
        print()
        print("="*80)
        print("❌ LOGIN FAILED")
        print("="*80)
        print()
        print("Possible reasons:")
        print("  1. Incorrect email/password")
        print("  2. 2FA enabled (need manual login)")
        print("  3. TikTok requires verification")
        print()
        print("Try manual login instead:")
        print("  python setup_login.py")
        print()

"""
Browser launcher - keeps browser open for manual login
"""

import asyncio
from playwright.async_api import async_playwright
import config
from pathlib import Path

async def open_browser_for_login():
    """
    Opens browser and keeps it open
    """
    print("="*80)
    print("🔐 Opening Browser for TikTok Login")
    print("="*80)
    print()
    
    browser_profile = config.SCRAPING_CONFIG['user_data_dir']
    
    if Path(browser_profile).exists():
        print("⚠️  Found existing browser profile.")
        print("   Browser will open with existing session.")
    else:
        print("🆕 Creating new browser profile...")
    
    print()
    print("🌐 Opening Chrome for Testing...")
    print("   Browser will stay open for 10 MINUTES")
    print("   Press Ctrl+C in terminal when done")
    print()
    
    async with async_playwright() as p:
        # Setup HTTP proxy (supported by Playwright!)
        proxy_config = None
        if config.PROXY_TYPE == "http":
            proxy_config = {
                "server": f"http://{config.PROXY_SERVER}:{config.PROXY_PORT}",
                "username": config.PROXY_USERNAME,
                "password": config.PROXY_PASSWORD,
            }
            print(f"🌐 Using HTTP proxy: {config.PROXY_SERVER}:{config.PROXY_PORT}")
        
        # Launch persistent browser
        context = await p.chromium.launch_persistent_context(
            browser_profile,
            headless=False,
            proxy=proxy_config,
            args=[
                '--disable-blink-features=AutomationControlled',
                '--enable-gpu',
                '--disable-dev-shm-usage',
            ],
            viewport={'width': 1280, 'height': 900},
        )
        
        page = context.pages[0] if context.pages else await context.new_page()
        
        print("📱 Navigating to TikTok...")
        await page.goto('https://www.tiktok.com/', wait_until='domcontentloaded')
        await asyncio.sleep(3)
        
        print()
        print("="*80)
        print("✅ BROWSER OPENED!")
        print("="*80)
        print()
        print("🔍 TO CHECK PROXY:")
        print("   1. Open new tab in browser")
        print("   2. Go to: https://ipinfo.io")
        print("   3. Check IP: should be 74.81.53.51 (US)")
        print()
        print("👤 TO LOGIN TIKTOK:")
        print("   1. Click 'Log in' button")
        print("   2. Login with your TikTok US account")
        print("   3. Complete verification")
        print()
        print("⏱️  Browser will stay open for 10 MINUTES")
        print("   Press Ctrl+C when done to save session")
        print()
        
        # Keep browser open for 10 minutes
        try:
            for i in range(600, 0, -60):
                mins = i // 60
                print(f"⏳ Time remaining: {mins} minute(s)...")
                await asyncio.sleep(60)
        except KeyboardInterrupt:
            print()
            print("⚠️  Ctrl+C detected - saving session...")
        
        print()
        print("💾 Saving session...")
        await asyncio.sleep(2)
        
        await context.close()
    
    print()
    print("="*80)
    print("✅ SESSION SAVED!")
    print("="*80)
    print()
    print("Session location:")
    print(f"  {browser_profile}/")
    print()
    print("Next: Run tracking with saved session:")
    print("  python auto_track.py product_urls.txt")
    print()

if __name__ == '__main__':
    try:
        asyncio.run(open_browser_for_login())
    except KeyboardInterrupt:
        print("\n✅ Done!")

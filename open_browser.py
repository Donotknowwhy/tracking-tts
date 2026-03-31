"""
Quick browser launcher - Opens browser for TikTok login
No input prompts - runs automatically
"""

import asyncio
from playwright.async_api import async_playwright
import config
from pathlib import Path

async def open_browser_for_login():
    """
    Opens browser for TikTok login
    Waits 3 minutes for user to login
    Session auto-saved
    """
    print("="*80)
    print("🔐 Opening Browser for TikTok Login")
    print("="*80)
    print()
    
    browser_profile = config.SCRAPING_CONFIG['user_data_dir']
    
    # Check if already logged in
    if Path(browser_profile).exists():
        print("⚠️  Found existing browser profile.")
        print("   Browser will open with existing session.")
        print()
    
    print("🌐 Opening Chrome for Testing...")
    print()
    
    async with async_playwright() as p:
        # Launch persistent browser
        context = await p.chromium.launch_persistent_context(
            browser_profile,
            headless=False,
            args=[
                '--disable-blink-features=AutomationControlled',
            ],
            viewport={'width': 1280, 'height': 900},
        )
        
        page = context.pages[0] if context.pages else await context.new_page()
        
        # Navigate to TikTok
        print("📱 Navigating to TikTok...")
        await page.goto('https://www.tiktok.com/', wait_until='domcontentloaded')
        await asyncio.sleep(2)
        
        print()
        print("="*80)
        print("👤 PLEASE LOGIN TO TIKTOK IN THE BROWSER")
        print("="*80)
        print()
        print("Steps:")
        print("  1. Click 'Log in' button")
        print("  2. Login with your TikTok US account")
        print("  3. Complete any verification if needed")
        print("  4. Wait for homepage to load")
        print()
        print("⏱️  Browser will stay open for 3 minutes...")
        print("   Close this terminal when done (Ctrl+C)")
        print()
        
        # Wait 3 minutes for login
        for i in range(180, 0, -30):
            print(f"⏳ Time remaining: {i} seconds...")
            await asyncio.sleep(30)
        
        print()
        print("🔍 Verifying login status...")
        
        # Test with TikTok Shop
        test_url = "https://www.tiktok.com/shop"
        await page.goto(test_url, wait_until='domcontentloaded')
        await asyncio.sleep(3)
        
        title = await page.title()
        if 'security' in title.lower():
            print("⚠️  Security check detected.")
            print("   May need manual verification.")
        else:
            print("✅ TikTok Shop accessible!")
        
        print()
        print("Closing browser in 5 seconds...")
        await asyncio.sleep(5)
        
        await context.close()
    
    print()
    print("="*80)
    print("✅ SESSION SAVED!")
    print("="*80)
    print()
    print("Session saved to:")
    print(f"  {browser_profile}/")
    print()
    print("Now you can run:")
    print("  python auto_track.py product_urls.txt")
    print()
    print("="*80)

if __name__ == '__main__':
    asyncio.run(open_browser_for_login())

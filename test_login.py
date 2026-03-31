"""
Test login setup - Auto-opens browser for login
"""

import asyncio
from playwright.async_api import async_playwright
import config
from pathlib import Path

async def test_login():
    """Test TikTok login with persistent browser"""
    
    print("="*80)
    print("🔐 TikTok Login Test")
    print("="*80)
    print()
    print("Opening browser for TikTok login...")
    print("Browser will stay open for 60 seconds.")
    print()
    print("Please:")
    print("  1. Login to tiktok.com")
    print("  2. Navigate to TikTok Shop")
    print("  3. Verify you can browse products")
    print()
    
    browser_profile = config.SCRAPING_CONFIG['user_data_dir']
    
    async with async_playwright() as p:
        # Launch persistent browser
        print(f"📂 Browser profile: {browser_profile}")
        print()
        
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
        print("📱 Opening tiktok.com...")
        await page.goto('https://www.tiktok.com/', wait_until='domcontentloaded')
        
        print()
        print("="*80)
        print("👤 PLEASE LOGIN IN THE BROWSER")
        print("="*80)
        print()
        print("Steps:")
        print("  1. Click 'Log in' in the browser")
        print("  2. Login with your TikTok account")
        print("  3. Wait for homepage to load")
        print()
        print("Browser will stay open for 60 seconds...")
        print("(Enough time to login)")
        print()
        
        # Wait 60 seconds for user to login
        for i in range(12):  # 12 x 5 = 60 seconds
            await asyncio.sleep(5)
            if i % 2 == 0:  # Every 10 seconds
                print(f"⏳ {60 - (i * 5)} seconds remaining...")
        
        print()
        print("🧪 Testing TikTok Shop access...")
        
        # Test TikTok Shop
        test_url = "https://www.tiktok.com/shop/pdp/1732128313499292514"
        await page.goto(test_url, wait_until='domcontentloaded', timeout=60000)
        
        await asyncio.sleep(5)
        
        title = await page.title()
        print(f"Page title: {title}")
        
        if 'security' in title.lower():
            print("⚠️  Still seeing Security Check")
            print("   This might resolve after login settles")
        else:
            print("✅ Page loaded successfully!")
        
        # Get page text to check for sold count
        try:
            page_text = await page.inner_text('body')
            
            import re
            sold_matches = re.findall(r'[\d,\.]+[KkMm]?\+?\s*(?:sold|units)', page_text[:5000], re.IGNORECASE)
            
            if sold_matches:
                print(f"✅ Found sold counts: {sold_matches[:3]}")
            else:
                print("⚠️  No sold count found yet")
        except Exception as e:
            print(f"⚠️  Error checking page: {e}")
        
        print()
        print("Keeping browser open for 10 more seconds...")
        await asyncio.sleep(10)
        
        await context.close()
    
    print()
    print("="*80)
    print("✅ TEST COMPLETED")
    print("="*80)
    print()
    print(f"Session saved to: {browser_profile}/")
    print()
    print("Now you can run the tool:")
    print("  python auto_track.py product_urls.txt")
    print()

if __name__ == '__main__':
    asyncio.run(test_login())

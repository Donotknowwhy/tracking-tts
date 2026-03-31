"""
Simple test script with Playwright persistent context
This will open a visible browser where you can solve CAPTCHA manually once
"""

import asyncio
from playwright.async_api import async_playwright
import random

USER_AGENTS = [
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
]

async def test_tiktok():
    print("Starting browser...")
    print("NOTE: A browser window will open. Please solve any CAPTCHA if prompted.")
    print()
    
    async with async_playwright() as p:
        # Launch persistent browser context (saves cookies)
        context = await p.chromium.launch_persistent_context(
            './browser_data',
            headless=False,
            args=[
                '--disable-blink-features=AutomationControlled',
            ],
            viewport={'width': 1920, 'height': 1080},
            locale='en-US',
            user_agent=USER_AGENTS[0],
        )
        
        # Get or create page
        if context.pages:
            page = context.pages[0]
        else:
            page = await context.new_page()
        
        # Navigate to TikTok Shop product
        url = "https://www.tiktok.com/shop/pdp/1732128313499292514"
        print(f"Navigating to: {url}")
        
        await page.goto(url, wait_until='domcontentloaded', timeout=60000)
        
        # Check title
        title = await page.title()
        print(f"Page title: {title}")
        
        if 'security' in title.lower():
            print("\n⚠️  CAPTCHA detected!")
            print("Please solve the CAPTCHA in the browser window.")
            print("Waiting 60 seconds for you to solve it...")
            
            # Wait for title to change
            for i in range(60):
                await asyncio.sleep(1)
                new_title = await page.title()
                if 'security' not in new_title.lower():
                    print(f"\n✅ CAPTCHA solved! New title: {new_title}")
                    break
                if i % 10 == 0 and i > 0:
                    print(f"  Still waiting... ({i}s elapsed)")
        
        # Wait a bit more for content to load
        print("\nWaiting for page to fully load...")
        await asyncio.sleep(5)
        
        # Get full HTML
        html = await page.content()
        
        # Save to file
        with open('debug_playwright.html', 'w', encoding='utf-8') as f:
            f.write(html)
        
        print(f"\n✅ HTML saved to: debug_playwright.html")
        print(f"   HTML length: {len(html)} characters")
        
        # Try to find sold count on page
        page_text = await page.inner_text('body')
        
        # Search for "sold" keyword
        import re
        sold_matches = re.findall(r'[\d,\.]+[KkMm]?\+?\s*(?:sold|units|Sold)', page_text, re.IGNORECASE)
        
        if sold_matches:
            print(f"\n🔍 Found potential sold counts:")
            for match in sold_matches[:5]:
                print(f"   - {match}")
        else:
            print(f"\n⚠️  No 'sold' text found on page")
            print(f"\n📄 First 500 chars of page text:")
            print(page_text[:500])
        
        print("\nKeeping browser open for 10 more seconds for you to inspect...")
        await asyncio.sleep(10)
        
        await context.close()
        print("\n✅ Done!")

if __name__ == '__main__':
    asyncio.run(test_tiktok())

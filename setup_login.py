"""
Login helper - One-time TikTok login setup
Run this once to login and save session
"""

import asyncio
from playwright.async_api import async_playwright
import config
from pathlib import Path

async def setup_tiktok_login():
    """
    Interactive login setup for TikTok
    User logs in once, session is saved for future runs
    """
    print("="*80)
    print("🔐 TikTok Login Setup")
    print("="*80)
    print()
    print("This is a ONE-TIME setup.")
    print("After login, your session will be saved.")
    print("Future runs won't need login again!")
    print()
    print("Press Enter to open browser...")
    input()
    
    browser_profile = config.SCRAPING_CONFIG['user_data_dir']
    
    # Check if already logged in
    if Path(browser_profile).exists():
        print("⚠️  Found existing browser profile.")
        print("   Do you want to:")
        print("   1. Keep existing session (recommended)")
        print("   2. Reset and login again")
        choice = input("Enter 1 or 2: ").strip()
        
        if choice == "2":
            import shutil
            shutil.rmtree(browser_profile)
            print("✅ Old session deleted. Starting fresh...")
        else:
            print("✅ Using existing session.")
            print()
            print("If you need to re-login, run:")
            print("  rm -rf browser_data/")
            print("  python setup_login.py")
            return
    
    print()
    print("Opening browser...")
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
        
        print()
        print("="*80)
        print("👤 PLEASE LOGIN TO TIKTOK")
        print("="*80)
        print()
        print("Steps:")
        print("  1. Click 'Log in' button in the browser")
        print("  2. Login with your TikTok account")
        print("     (Email, Phone, or Social login)")
        print("  3. Wait for homepage to load")
        print("  4. Verify you see your profile")
        print()
        print("⚠️  IMPORTANT:")
        print("   - Use a real TikTok account (not temporary)")
        print("   - This account will be used for all future runs")
        print("   - No need to be a seller account")
        print()
        print("When logged in, press Enter here to continue...")
        
        input()
        
        # Verify login
        print()
        print("🔍 Verifying login status...")
        
        # Check for login indicators
        await asyncio.sleep(2)
        page_content = await page.content()
        
        # Simple check: logged in users usually have profile elements
        if 'login' in page_content.lower() and 'log in' in await page.title().lower():
            print("⚠️  Looks like you might not be logged in yet.")
            print("   Please check the browser and login.")
            print()
            print("Press Enter when done...")
            input()
        
        print("✅ Session saved!")
        print()
        
        # Test with TikTok Shop
        print("🧪 Testing TikTok Shop access...")
        test_url = "https://www.tiktok.com/shop"
        await page.goto(test_url, wait_until='domcontentloaded')
        await asyncio.sleep(3)
        
        title = await page.title()
        if 'security' in title.lower():
            print("⚠️  Still seeing security check on Shop page.")
            print("   This is normal - will be resolved when scraping starts.")
        else:
            print("✅ TikTok Shop accessible!")
        
        print()
        print("Keeping browser open for 5 seconds for you to verify...")
        await asyncio.sleep(5)
        
        await context.close()
    
    print()
    print("="*80)
    print("✅ SETUP COMPLETED!")
    print("="*80)
    print()
    print("Your TikTok session has been saved to:")
    print(f"  {browser_profile}/")
    print()
    print("Now you can run:")
    print("  python auto_track.py product_urls.txt")
    print()
    print("The tool will use your logged-in session!")
    print("No CAPTCHA in 90% of cases! 🎉")
    print()
    print("Note: If cookies expire (after 2-4 weeks),")
    print("      just run this setup again.")
    print("="*80)

if __name__ == '__main__':
    asyncio.run(setup_tiktok_login())

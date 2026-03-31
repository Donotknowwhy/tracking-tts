"""
Quick test with cookies - Tests if cookies work for bypassing CAPTCHA
"""

import asyncio
import sys
from src.scraper import TikTokScraper

async def test_with_cookies(url: str):
    """Test scraping with cookies loaded"""
    print("="*80)
    print("🧪 Testing TikTok Scraping with Cookies")
    print("="*80)
    print()
    print(f"URL: {url}")
    print()
    
    async with TikTokScraper() as scraper:
        print("Fetching product...")
        result = await scraper.fetch_product(url)
        
        print()
        print("="*80)
        print("📊 RESULT:")
        print("="*80)
        print()
        print(f"Status: {result['status']}")
        print(f"Product ID: {result['product_id']}")
        print(f"Title: {result['product_title']}")
        print(f"Sold Count: {result['sold_count']}")
        print(f"Price: {result.get('price', 'N/A')}")
        
        if result['status'] == 'error':
            print(f"Error: {result['error_message']}")
        
        print()
        print("="*80)
        
        if result['status'] == 'success' and result['sold_count']:
            print("✅ SUCCESS! Cookies working!")
        elif result['status'] == 'success':
            print("⚠️  Partial success (no sold count)")
        else:
            print("❌ FAILED - Check for CAPTCHA")
        
        print("="*80)

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python test_cookies.py <product_url>")
        print()
        print("Example:")
        print("  python test_cookies.py https://www.tiktok.com/view/product/1732275855990363066")
        sys.exit(1)
    
    url = sys.argv[1]
    asyncio.run(test_with_cookies(url))

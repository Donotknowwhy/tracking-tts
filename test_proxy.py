"""
Test SOCKS5 proxy connection
"""

import asyncio
import httpx

async def test_proxy():
    proxy_url = "socks5://xhdd6lei:kkWcjgqlMXbgxTcK@74.81.53.51:43997"
    
    print("="*80)
    print("Testing SOCKS5 Proxy")
    print("="*80)
    print(f"Proxy: 74.81.53.51:43997")
    print(f"Username: xhdd6lei")
    print()
    
    # Test 1: Check IP without proxy
    print("1️⃣ Test WITHOUT proxy (your current IP):")
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get('https://api.ipify.org?format=json')
            data = response.json()
            print(f"   ✅ Your IP: {data['ip']}")
            print(f"   Location: (checking...)")
            
            # Get location
            loc_response = await client.get(f"http://ip-api.com/json/{data['ip']}")
            loc_data = loc_response.json()
            print(f"   Location: {loc_data.get('city')}, {loc_data.get('regionName')}, {loc_data.get('country')}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    print()
    
    # Test 2: Check IP with proxy
    print("2️⃣ Test WITH SOCKS5 proxy:")
    try:
        async with httpx.AsyncClient(proxy=proxy_url, timeout=20.0) as client:
            response = await client.get('https://api.ipify.org?format=json')
            data = response.json()
            print(f"   ✅ Proxy IP: {data['ip']}")
            
            # Get location
            loc_response = await client.get(f"http://ip-api.com/json/{data['ip']}")
            loc_data = loc_response.json()
            print(f"   Location: {loc_data.get('city')}, {loc_data.get('regionName')}, {loc_data.get('country')}")
            
            if loc_data.get('countryCode') == 'US':
                print(f"   ✅ Proxy is from United States! 🇺🇸")
            else:
                print(f"   ⚠️  Proxy is NOT from US (Country: {loc_data.get('country')})")
    except Exception as e:
        print(f"   ❌ Proxy connection failed: {e}")
    
    print()
    
    # Test 3: Test speed
    print("3️⃣ Test proxy speed:")
    try:
        import time
        async with httpx.AsyncClient(proxy=proxy_url, timeout=30.0) as client:
            start = time.time()
            response = await client.get('https://www.google.com')
            elapsed = time.time() - start
            
            print(f"   ✅ Response time: {elapsed:.2f}s")
            print(f"   Status: {response.status_code}")
            
            if elapsed < 2:
                print(f"   ✅ Speed: Fast")
            elif elapsed < 5:
                print(f"   ⚠️  Speed: Medium")
            else:
                print(f"   ⚠️  Speed: Slow (may cause timeouts)")
    except Exception as e:
        print(f"   ❌ Speed test failed: {e}")
    
    print()
    
    # Test 4: Test TikTok Shop access
    print("4️⃣ Test TikTok Shop access through proxy:")
    try:
        async with httpx.AsyncClient(
            proxy=proxy_url, 
            timeout=30.0,
            follow_redirects=True
        ) as client:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.9',
            }
            
            url = "https://www.tiktok.com/shop/pdp/1732128313499292514"
            response = await client.get(url, headers=headers)
            
            print(f"   Status: {response.status_code}")
            print(f"   Title check: {'Security Check' in response.text}")
            
            if 'Security Check' in response.text:
                print(f"   ⚠️  CAPTCHA detected (expected with httpx)")
                print(f"   → Need to use real browser (Playwright) to pass CAPTCHA")
            else:
                print(f"   ✅ Page loaded successfully!")
                
    except Exception as e:
        print(f"   ❌ TikTok access failed: {e}")
    
    print()
    print("="*80)
    print("Test completed!")
    print("="*80)

if __name__ == '__main__':
    asyncio.run(test_proxy())

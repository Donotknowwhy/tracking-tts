# TikTok Shop Product Tracking - Proxy Setup Guide

## Problem: SOCKS5 Proxy với Authentication

TikTok Shop US requires proxy to avoid geo-blocking, but:
- Playwright không hỗ trợ SOCKS5 với username/password
- httpx có thể bypass nhưng TikTok có CAPTCHA khi detect headless requests

## Solution Options

### Option 1: SSH Tunnel (Recommended)

Setup local SOCKS5 proxy without auth:

```bash
# Run this in a separate terminal
ssh -D 1080 -N xhdd6lei@74.81.53.51 -p 43997
# Enter password: kkWcjgqlMXbgxTcK
```

Then update `config.py`:
```python
PROXY_CONFIG = {
    "server": "socks5://127.0.0.1:1080"  # No auth needed
}
```

### Option 2: Use proxychains (Mac)

```bash
brew install proxychains-ng

# Edit /opt/homebrew/etc/proxychains.conf
# Add line:
socks5 74.81.53.51 43997 xhdd6lei kkWcjgqlMXbgxTcK

# Run scraper with proxychains
proxychains4 python main.py test --url "..."
```

### Option 3: Browser MCP (Integrated with Cursor)

Use Cursor's built-in browser automation:
- Handles proxies automatically
- Full JavaScript rendering
- Can handle CAPTCHAs

### Option 4: Manual Browser + Cookie Export

1. Open browser with proxy
2. Login/solve CAPTCHA once
3. Export cookies
4. Use cookies in scraper

## Current Status

Using **Playwright with headless=False** to:
1. Avoid CAPTCHA detection
2. Allow manual CAPTCHA solving if needed
3. Working without proxy for now (need to add SSH tunnel)

## Next Steps

1. Test if TikTok Shop US blocks non-US IPs
2. If yes, setup SSH tunnel (Option 1)
3. If CAPTCHA persists, may need Option 3 or 4

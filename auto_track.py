#!/usr/bin/env python3
"""
🚀 ONE-COMMAND AUTOMATED TRACKING

Usage:
    python auto_track.py urls.txt

What it does:
    1. Auto-login to TikTok (if credentials provided)
    2. Runs snapshot 1 (t1)
    3. Waits 3 hours automatically
    4. Runs snapshot 2 (t2)
    5. Analyzes and exports CSV
    
All in one command! No need to run twice manually.
"""

import asyncio
import sys
import argparse
from pathlib import Path

# Import from run_automated
sys.path.insert(0, str(Path(__file__).parent))

from run_automated import run_automated_tracking
import config

async def ensure_login():
    """Check login status and auto-login if credentials provided"""
    from auto_login import check_login_status, auto_login_tiktok
    
    # Check if already logged in
    is_logged_in = await check_login_status()
    
    if is_logged_in:
        print("✅ Found existing TikTok session!")
        return True
    
    # Try auto-login if credentials provided
    if config.TIKTOK_EMAIL and config.TIKTOK_PASSWORD:
        print("🔐 No session found. Attempting auto-login...")
        success = await auto_login_tiktok(config.TIKTOK_EMAIL, config.TIKTOK_PASSWORD)
        
        if success:
            print("✅ Auto-login successful!")
            return True
        else:
            print("❌ Auto-login failed. Please login manually:")
            print("   python setup_login.py")
            return False
    
    # No credentials and not logged in
    print("⚠️  No TikTok session found and no credentials configured.")
    print()
    print("Options:")
    print("  1. Setup credentials in .env file (recommended)")
    print("  2. Or login manually: python setup_login.py")
    print()
    
    return False

def main():
    parser = argparse.ArgumentParser(
        description="One-command automated TikTok Shop tracking"
    )
    parser.add_argument("urls_file", help="Path to product URL file")
    parser.add_argument(
        "interval_hours",
        nargs="?",
        type=float,
        default=3.0,
        help="Hours between snapshot 1 and 2 (default: 3.0)",
    )
    parser.add_argument(
        "--proxy",
        type=str,
        default=None,
        help=(
            "Override proxy at runtime. Supported: "
            "http://host:port:user:pass or http://user:pass@host:port"
        ),
    )
    args = parser.parse_args()

    if args.proxy:
        try:
            config.apply_proxy(args.proxy)
            print(f"🌐 Using runtime proxy: {config.PROXY_SERVER}:{config.PROXY_PORT}")
        except Exception as e:
            print(f"❌ Invalid proxy format: {e}")
            sys.exit(1)
    
    # Check if browser profile exists
    browser_profile = Path('browser_data')
    
    if not browser_profile.exists() or not any(browser_profile.iterdir()):
        print()
        print("="*80)
        print("⚠️  NO TIKTOK SESSION FOUND")
        print("="*80)
        print()
        print("For best results (90% no CAPTCHA), please login first:")
        print()
        print("  python setup_login.py")
        print()
        print("This is a one-time setup that takes 2 minutes.")
        print()
        print("Or continue without login (may encounter CAPTCHAs):")
        choice = input("Continue without login? (y/N): ").strip().lower()
        
        if choice != 'y':
            print()
            print("Please run: python setup_login.py")
            print("Then try again!")
            sys.exit(0)
        
        print()
        print("⚠️  Continuing without login...")
        print("   You may need to solve CAPTCHAs manually during scraping.")
        print()
    else:
        print()
        print("✅ Found TikTok session! (90% CAPTCHA-free)")
        print()
    
    urls_file = args.urls_file
    interval_hours = args.interval_hours
    
    # Check/setup login first
    if not asyncio.run(ensure_login()):
        print("❌ Login required. Please setup credentials or login manually.")
        sys.exit(1)
    
    print(f"""
╔═══════════════════════════════════════════════════════════════╗
║                                                               ║
║   🚀 TikTok Shop AUTOMATED Tracking                          ║
║                                                               ║
╚═══════════════════════════════════════════════════════════════╝

📁 Input file: {urls_file}
⏱️  Interval: {interval_hours} hours
🤖 Mode: FULLY AUTOMATED

This will run for {interval_hours} hours total.
Keep this terminal open!

Press Ctrl+C to cancel.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
""")
    
    try:
        asyncio.run(run_automated_tracking(urls_file, interval_hours))
    except KeyboardInterrupt:
        print("\n\n⚠️  Tracking cancelled by user")
        sys.exit(0)

if __name__ == '__main__':
    main()

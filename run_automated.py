"""
Automated scheduler for TikTok Shop tracking
This runs snapshot 1, waits 3 hours, then automatically runs snapshot 2
"""

import asyncio
import logging
from datetime import datetime, timedelta
import sys
from pathlib import Path
from typing import Any, Callable, Optional

sys.path.insert(0, str(Path(__file__).parent))

import config
from src.database import Database
from src.proxy_check import is_http_proxy_configured, verify_http_proxy
from src.scraper import TikTokScraper, CaptchaError
from src.analyzer import compute_growth, extract_keywords
from src.exporter import export_to_csv, export_to_excel, export_snapshot_to_excel, print_summary

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def read_urls_from_file(filepath: str) -> list:
    """Read product URLs from text file, resolving any mobile/short URLs to desktop."""
    from src.parser import resolve_tiktok_mobile_url

    with open(filepath, 'r', encoding='utf-8') as f:
        raw_urls = [line.strip() for line in f if line.strip() and not line.startswith('#')]
    resolved = [resolve_tiktok_mobile_url(u) for u in raw_urls]
    return resolved

async def run_snapshot(
    urls: list,
    session_id: int,
    snapshot_order: int,
    on_progress: Optional[Callable[[int, int], Any]] = None,
    profile_dir: Optional[str] = None,
    adspower_profile_id: Optional[str] = None,
):
    """Run a snapshot: fetch all products and save to database"""
    db = Database()
    
    logger.info(f"Starting snapshot {snapshot_order} for session {session_id}")
    logger.info(f"Total products to fetch: {len(urls)}")

    async with TikTokScraper(user_data_dir=profile_dir, adspower_profile_id=adspower_profile_id) as scraper:
        try:
            results = await scraper.fetch_products(urls, on_progress=on_progress)
        except CaptchaError as exc:
            logger.error("CAPTCHA block — aborting snapshot: %s", exc)
            raise
    
    logger.info("Saving results to database...")
    
    success_count = 0
    error_count = 0
    
    for result in results:
        db.save_snapshot(
            session_id=session_id,
            product_id=result['product_id'],
            product_url=result['product_url'],
            product_title=result['product_title'],
            sold_count=result['sold_count'],
            price=result.get('price'),
            snapshot_order=snapshot_order,
            status=result['status'],
            error_message=result.get('error_message')
        )
        
        if result['status'] == 'success':
            success_count += 1
        else:
            error_count += 1
    
    logger.info(f"Snapshot {snapshot_order} completed: {success_count} success, {error_count} errors")

    # Export snapshot report right after each snapshot
    snapshot_rows = db.get_snapshot(session_id, snapshot_order=snapshot_order)
    snapshot_excel = export_snapshot_to_excel(snapshot_rows, session_id, snapshot_order)
    logger.info(f"✅ Snapshot {snapshot_order} Excel Report: {snapshot_excel}")
    
    return success_count, error_count, snapshot_excel

def run_analysis(session_id: int):
    """Run analysis: compute growth and extract keywords"""
    db = Database()
    
    logger.info(f"Running analysis for session {session_id}")
    
    snapshots_t1 = db.get_snapshot(session_id, snapshot_order=1)
    snapshots_t2 = db.get_snapshot(session_id, snapshot_order=2)
    
    if not snapshots_t1 or not snapshots_t2:
        logger.error("Missing snapshots!")
        return
    
    logger.info(f"Snapshot 1: {len(snapshots_t1)} products")
    logger.info(f"Snapshot 2: {len(snapshots_t2)} products")
    
    # Compute growth
    analysis_results = compute_growth(snapshots_t1, snapshots_t2)
    
    if not analysis_results:
        logger.error("No valid comparison data!")
        return
    
    logger.info(f"Analysis completed: {len(analysis_results)} products compared")
    
    # Save analysis
    db.save_analysis(session_id, analysis_results)

    sess = db.get_session(session_id)
    seo_raw = (sess or {}).get("seo_keywords") or ""
    win_raw = (sess or {}).get("win_keywords") or ""

    # Extract keywords
    keywords_results = extract_keywords(
        analysis_results,
        seo_keywords_raw=seo_raw,
        win_keywords_raw=win_raw,
    )
    
    if keywords_results:
        db.save_keywords(session_id, keywords_results)
        logger.info(f"Extracted {len(keywords_results)} keywords")
    
    # Export to CSV
    products_csv, keywords_csv = export_to_csv(
        analysis_results,
        keywords_results,
        session_id
    )
    excel_report = export_to_excel(
        analysis_results,
        keywords_results,
        session_id
    )
    
    logger.info(f"✅ Products CSV: {products_csv}")
    logger.info(f"✅ Keywords CSV: {keywords_csv}")
    logger.info(f"✅ Excel Report: {excel_report}")
    
    # Print summary
    print_summary(analysis_results, keywords_results)
    
    # Update session status
    db.update_session_status(session_id, 'completed')
    
    logger.info("Analysis complete!")

async def run_automated_tracking(urls_file: str, interval_hours: float = None):
    """
    Fully automated tracking workflow:
    1. Run snapshot 1
    2. Wait X hours
    3. Automatically run snapshot 2
    4. Generate reports
    
    Args:
        urls_file: Path to file with product URLs
        interval_hours: Hours to wait between snapshots (default from config)
    """
    if interval_hours is None:
        interval_hours = config.TRACKING_CONFIG['check_interval_hours']
    
    # Read URLs
    urls = read_urls_from_file(urls_file)
    logger.info(f"Loaded {len(urls)} URLs from {urls_file}")
    
    # Create session
    db = Database()
    session_id = db.create_session(
        check_interval_hours=interval_hours,
        total_products=len(urls)
    )
    
    logger.info(f"Created session ID: {session_id}")

    if is_http_proxy_configured():
        logger.info("Verifying HTTP proxy…")
        ok, proxy_err = verify_http_proxy()
        if not ok:
            logger.error("Proxy check failed: %s", proxy_err)
            db.update_session_status(session_id, "failed")
            print("\n❌ Proxy không hoạt động:", proxy_err)
            return
    
    print("\n" + "="*80)
    print("🚀 STARTING AUTOMATED TRACKING")
    print("="*80)
    print(f"Session ID: {session_id}")
    print(f"Total products: {len(urls)}")
    print(f"Interval: {interval_hours} hours")
    print("="*80 + "\n")
    
    # === SNAPSHOT 1 ===
    logger.info("=" * 50)
    logger.info("SNAPSHOT 1 - Starting...")
    logger.info("=" * 50)
    
    success1, errors1, snapshot1_excel = await run_snapshot(urls, session_id, snapshot_order=1)

    if len(urls) > 0 and success1 == 0:
        logger.error("Snapshot 1: no successful fetches; aborting (session %s).", session_id)
        db.update_session_status(session_id, "failed")
        print("\n❌ Dừng: không lấy được dữ liệu cho bất kỳ URL nào ở snapshot 1. Kiểm tra proxy, mạng hoặc URL.")
        return

    next_check = datetime.now() + timedelta(hours=interval_hours)
    
    print("\n" + "="*80)
    print("✅ SNAPSHOT 1 COMPLETED")
    print("="*80)
    print(f"Success: {success1}/{len(urls)}")
    print(f"Errors: {errors1}")
    print(f"Snapshot report: {snapshot1_excel}")
    print(f"\n⏰ Next check at: {next_check.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"⏳ Waiting {interval_hours} hours...")
    print("="*80 + "\n")
    
    # === WAIT ===
    wait_seconds = interval_hours * 3600
    
    # Show countdown every 15 minutes
    interval_seconds = 900  # 15 minutes
    elapsed = 0
    
    while elapsed < wait_seconds:
        remaining = wait_seconds - elapsed
        remaining_hours = remaining / 3600
        remaining_mins = (remaining % 3600) / 60
        
        if elapsed > 0:
            logger.info(f"⏳ Time remaining: {remaining_hours:.1f} hours ({remaining_mins:.0f} minutes)")
        
        # Sleep for interval or remaining time, whichever is shorter
        sleep_time = min(interval_seconds, remaining)
        await asyncio.sleep(sleep_time)
        elapsed += sleep_time
    
    # === SNAPSHOT 2 ===
    logger.info("=" * 50)
    logger.info("SNAPSHOT 2 - Starting...")
    logger.info("=" * 50)
    
    success2, errors2, snapshot2_excel = await run_snapshot(urls, session_id, snapshot_order=2)

    if len(urls) > 0 and success2 == 0:
        logger.error("Snapshot 2: no successful fetches; aborting analysis (session %s).", session_id)
        db.update_session_status(session_id, "failed")
        print("\n❌ Dừng: không lấy được dữ liệu cho bất kỳ URL nào ở snapshot 2. Kiểm tra proxy, mạng hoặc URL.")
        return

    print("\n" + "="*80)
    print("✅ SNAPSHOT 2 COMPLETED")
    print("="*80)
    print(f"Success: {success2}/{len(urls)}")
    print(f"Errors: {errors2}")
    print(f"Snapshot report: {snapshot2_excel}")
    print("="*80 + "\n")
    
    # === ANALYSIS ===
    logger.info("=" * 50)
    logger.info("RUNNING ANALYSIS...")
    logger.info("=" * 50)
    
    run_analysis(session_id)
    
    print("\n" + "="*80)
    print("🎉 AUTOMATED TRACKING COMPLETED!")
    print("="*80)
    print(f"Session ID: {session_id}")
    print(f"Duration: {interval_hours} hours")
    print(f"\n📊 Check results in: data/output/")
    print("="*80 + "\n")

if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Automated TikTok Shop Tracking')
    parser.add_argument('-i', '--input', required=True, help='Input file with product URLs')
    parser.add_argument('--interval', type=float, default=None,
                       help='Check interval in hours (default: 3.0)')
    
    args = parser.parse_args()
    
    asyncio.run(run_automated_tracking(args.input, args.interval))

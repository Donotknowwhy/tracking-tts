#!/usr/bin/env python3
"""
TikTok Shop Product Tracking Tool - Main Entry Point
"""

import asyncio
import argparse
import logging
from pathlib import Path
from datetime import datetime, timedelta
import sys
from typing import Any, Callable, Optional

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

import config
from src.database import Database
from src.scraper import TikTokScraper
from src.analyzer import compute_growth, extract_keywords, filter_results
from src.exporter import export_to_csv, export_to_excel, export_snapshot_to_excel, print_summary

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def read_urls_from_file(filepath: str) -> list:
    """Read product URLs from text file"""
    with open(filepath, 'r', encoding='utf-8') as f:
        urls = [line.strip() for line in f if line.strip() and not line.startswith('#')]
    return urls

async def run_snapshot(
    urls: list,
    session_id: int,
    snapshot_order: int,
    on_progress: Optional[Callable[[int, int], Any]] = None,
):
    """
    Run a snapshot: fetch all products and save to database
    
    Args:
        urls: List of product URLs
        session_id: Database session ID
        snapshot_order: 1 for first snapshot, 2 for second
        on_progress: Optional callback(completed, total) during fetch
    """
    db = Database()
    
    logger.info(f"Starting snapshot {snapshot_order} for session {session_id}")
    logger.info(f"Total products to fetch: {len(urls)}")
    
    async with TikTokScraper() as scraper:
        results = await scraper.fetch_products(urls, on_progress=on_progress)
    
    # Save to database
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
    """
    Run analysis: compute growth and extract keywords
    
    Args:
        session_id: Database session ID
    """
    db = Database()
    
    logger.info(f"Running analysis for session {session_id}")
    
    # Get snapshots
    snapshots_t1 = db.get_snapshot(session_id, snapshot_order=1)
    snapshots_t2 = db.get_snapshot(session_id, snapshot_order=2)
    
    if not snapshots_t1:
        logger.error("No snapshot 1 found!")
        return
    
    if not snapshots_t2:
        logger.error("No snapshot 2 found!")
        return
    
    logger.info(f"Snapshot 1: {len(snapshots_t1)} products")
    logger.info(f"Snapshot 2: {len(snapshots_t2)} products")
    
    # Compute growth
    analysis_results = compute_growth(snapshots_t1, snapshots_t2)
    
    if not analysis_results:
        logger.error("No valid comparison data!")
        return
    
    logger.info(f"Analysis completed: {len(analysis_results)} products compared")
    
    # Save analysis to database
    db.save_analysis(session_id, analysis_results)

    sess = db.get_session(session_id)
    seo_raw = (sess or {}).get("seo_keywords") or ""

    # Extract keywords
    keywords_results = extract_keywords(
        analysis_results,
        seo_keywords_raw=seo_raw,
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

def main():
    parser = argparse.ArgumentParser(description='TikTok Shop Product Tracking Tool')
    
    subparsers = parser.add_subparsers(dest='command', help='Command to run')
    
    # Command: start
    start_parser = subparsers.add_parser('start', help='Start a new tracking session')
    start_parser.add_argument('-i', '--input', required=True, help='Input file with product URLs')
    start_parser.add_argument('--interval', type=float, default=3.0, 
                             help='Check interval in hours (default: 3.0)')
    
    # Command: snapshot2
    snap2_parser = subparsers.add_parser('snapshot2', help='Run second snapshot and analyze')
    snap2_parser.add_argument('-s', '--session-id', type=int, required=True, 
                             help='Session ID from first snapshot')
    
    # Command: test
    test_parser = subparsers.add_parser('test', help='Test fetch a single URL')
    test_parser.add_argument('-u', '--url', required=True, help='Product URL to test')
    
    args = parser.parse_args()
    
    if args.command == 'start':
        # Check browser profile
        browser_profile = Path('browser_data')
        
        if not browser_profile.exists() or not any(browser_profile.iterdir()):
            print()
            print("="*80)
            print("⚠️  RECOMMENDATION: Login to TikTok first")
            print("="*80)
            print()
            print("For 90% CAPTCHA-free scraping, login once:")
            print("  python setup_login.py")
            print()
            print("This takes 2 minutes and greatly improves success rate!")
            print()
            choice = input("Continue without login? (y/N): ").strip().lower()
            
            if choice != 'y':
                print()
                print("Please run: python setup_login.py")
                sys.exit(0)
            
            print()
            print("⚠️  Continuing without login (may encounter CAPTCHAs)...")
            print()
        
        # Read URLs
        urls = read_urls_from_file(args.input)
        logger.info(f"Loaded {len(urls)} URLs from {args.input}")
        
        # Create session
        db = Database()
        session_id = db.create_session(
            check_interval_hours=args.interval,
            total_products=len(urls)
        )
        
        logger.info(f"Created session ID: {session_id}")
        logger.info(f"Check interval: {args.interval} hours")
        
        # Run first snapshot
        success, errors, snapshot_excel = asyncio.run(run_snapshot(urls, session_id, snapshot_order=1))
        
        # Calculate when to run second snapshot
        next_check = datetime.now() + timedelta(hours=args.interval)
        
        print("\n" + "="*80)
        print("✅ FIRST SNAPSHOT COMPLETED")
        print("="*80)
        print(f"Session ID: {session_id}")
        print(f"Products fetched: {success}/{len(urls)} successful")
        print(f"Errors: {errors}")
        print(f"Snapshot report: {snapshot_excel}")
        print(f"\n⏰ Run second snapshot at: {next_check.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"\nCommand:")
        print(f"  python main.py snapshot2 --session-id {session_id}")
        print("="*80)
    
    elif args.command == 'snapshot2':
        db = Database()
        
        # Get session info
        session = db.get_session(args.session_id)
        if not session:
            logger.error(f"Session {args.session_id} not found!")
            return
        
        # Get URLs from first snapshot
        snapshots_t1 = db.get_snapshot(args.session_id, snapshot_order=1)
        urls = [s['product_url'] for s in snapshots_t1]
        
        logger.info(f"Running second snapshot for session {args.session_id}")
        logger.info(f"Re-fetching {len(urls)} products")
        
        # Run second snapshot
        success, errors, snapshot_excel = asyncio.run(
            run_snapshot(urls, args.session_id, snapshot_order=2)
        )
        
        logger.info(f"Second snapshot completed: {success} success, {errors} errors")
        logger.info(f"Snapshot 2 report: {snapshot_excel}")
        
        # Run analysis
        run_analysis(args.session_id)
    
    elif args.command == 'test':
        # Test fetch single URL
        async def test_fetch():
            async with TikTokScraper() as scraper:
                result = await scraper.fetch_product(args.url)
                
                print("\n" + "="*80)
                print("TEST FETCH RESULT")
                print("="*80)
                print(f"Product ID: {result['product_id']}")
                print(f"Title: {result['product_title']}")
                print(f"Sold Count: {result['sold_count']}")
                print(f"Price: {result.get('price')}")
                print(f"Status: {result['status']}")
                if result.get('error_message'):
                    print(f"Error: {result['error_message']}")
                print("="*80)
        
        asyncio.run(test_fetch())
    
    else:
        parser.print_help()

if __name__ == '__main__':
    main()

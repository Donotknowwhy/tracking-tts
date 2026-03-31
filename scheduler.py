"""
Background scheduler - Run tracking sessions in background with APScheduler
Can schedule multiple sessions to run at specific times
"""

import asyncio
import logging
from datetime import datetime, timedelta
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent))

try:
    from apscheduler.schedulers.asyncio import AsyncIOScheduler
    from apscheduler.triggers.date import DateTrigger
except ImportError:
    print("ERROR: APScheduler not installed!")
    print("Install with: pip install apscheduler")
    sys.exit(1)

import config
from src.database import Database
from src.scraper import TikTokScraper
from src.analyzer import compute_growth, extract_keywords
from src.exporter import export_to_csv, export_to_excel, print_summary

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class TrackingScheduler:
    def __init__(self):
        self.scheduler = AsyncIOScheduler()
        self.db = Database()
    
    async def run_snapshot(self, urls: list, session_id: int, snapshot_order: int):
        """Run a snapshot"""
        logger.info(f"[Session {session_id}] Running snapshot {snapshot_order}")
        
        async with TikTokScraper() as scraper:
            results = await scraper.fetch_products(urls)
        
        success_count = 0
        for result in results:
            self.db.save_snapshot(
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
        
        logger.info(f"[Session {session_id}] Snapshot {snapshot_order} done: {success_count} success")
        return success_count
    
    def run_analysis_sync(self, session_id: int):
        """Run analysis (sync wrapper for scheduler)"""
        logger.info(f"[Session {session_id}] Running analysis")
        
        snapshots_t1 = self.db.get_snapshot(session_id, snapshot_order=1)
        snapshots_t2 = self.db.get_snapshot(session_id, snapshot_order=2)
        
        analysis_results = compute_growth(snapshots_t1, snapshots_t2)
        self.db.save_analysis(session_id, analysis_results)
        
        keywords_results = extract_keywords(analysis_results)
        self.db.save_keywords(session_id, keywords_results)
        
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
        
        logger.info(f"[Session {session_id}] ✅ Results: {products_csv}")
        logger.info(f"[Session {session_id}] ✅ Excel: {excel_report}")
        
        self.db.update_session_status(session_id, 'completed')
        
        # Print summary
        print_summary(analysis_results, keywords_results)
    
    def schedule_tracking(self, urls_file: str, interval_hours: float = None):
        """
        Schedule automated tracking
        
        Args:
            urls_file: Path to URLs file
            interval_hours: Hours between snapshots
        """
        if interval_hours is None:
            interval_hours = config.TRACKING_CONFIG['check_interval_hours']
        
        # Read URLs
        with open(urls_file, 'r') as f:
            urls = [line.strip() for line in f if line.strip()]
        
        # Create session
        session_id = self.db.create_session(
            check_interval_hours=interval_hours,
            total_products=len(urls)
        )
        
        logger.info(f"Scheduled session {session_id}: {len(urls)} products, {interval_hours}h interval")
        
        # Schedule snapshot 1 (now)
        now = datetime.now()
        self.scheduler.add_job(
            lambda: asyncio.create_task(self.run_snapshot(urls, session_id, 1)),
            trigger=DateTrigger(run_date=now),
            id=f"session_{session_id}_snapshot1"
        )
        
        # Schedule snapshot 2 (after interval)
        snapshot2_time = now + timedelta(hours=interval_hours)
        self.scheduler.add_job(
            lambda: asyncio.create_task(self.run_snapshot(urls, session_id, 2)),
            trigger=DateTrigger(run_date=snapshot2_time),
            id=f"session_{session_id}_snapshot2"
        )
        
        # Schedule analysis (a few seconds after snapshot 2)
        analysis_time = snapshot2_time + timedelta(seconds=10)
        self.scheduler.add_job(
            lambda: self.run_analysis_sync(session_id),
            trigger=DateTrigger(run_date=analysis_time),
            id=f"session_{session_id}_analysis"
        )
        
        logger.info(f"✅ Scheduled:")
        logger.info(f"   Snapshot 1: {now.strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info(f"   Snapshot 2: {snapshot2_time.strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info(f"   Analysis:   {analysis_time.strftime('%Y-%m-%d %H:%M:%S')}")
        
        return session_id
    
    def start(self):
        """Start the scheduler"""
        logger.info("Starting scheduler...")
        self.scheduler.start()
        logger.info("Scheduler started! Press Ctrl+C to stop")
    
    async def run_forever(self):
        """Keep running until interrupted"""
        try:
            # Keep event loop running
            while True:
                await asyncio.sleep(60)  # Check every minute
        except KeyboardInterrupt:
            logger.info("Shutting down...")
            self.scheduler.shutdown()

async def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Background scheduler for TikTok Shop tracking')
    parser.add_argument('-i', '--input', required=True, help='Input file with product URLs')
    parser.add_argument('--interval', type=float, default=None,
                       help='Check interval in hours (default: 3.0)')
    
    args = parser.parse_args()
    
    scheduler = TrackingScheduler()
    
    # Schedule tracking
    session_id = scheduler.schedule_tracking(args.input, args.interval)
    
    print("\n" + "="*80)
    print("🤖 BACKGROUND SCHEDULER STARTED")
    print("="*80)
    print(f"Session ID: {session_id}")
    print(f"Tracking will run automatically!")
    print(f"\n💡 This terminal must stay open.")
    print(f"   Press Ctrl+C to stop scheduler")
    print("="*80 + "\n")
    
    # Start scheduler
    scheduler.start()
    
    # Keep running
    await scheduler.run_forever()

if __name__ == '__main__':
    asyncio.run(main())

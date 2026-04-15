import sqlite3
from datetime import datetime
from typing import Optional, List, Dict, Any
from pathlib import Path
import config

class Database:
    def __init__(self, db_path: Path = config.DB_PATH):
        self.db_path = db_path
        self.init_database()
    
    def get_connection(self):
        """Get database connection"""
        return sqlite3.connect(self.db_path)
    
    def init_database(self):
        """Initialize database schema"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Sessions table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sessions (
                session_id INTEGER PRIMARY KEY AUTOINCREMENT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                check_interval_hours REAL,
                total_products INTEGER,
                status TEXT DEFAULT 'in_progress',
                seo_keywords TEXT,
                win_keywords TEXT
            )
        """)
        
        # Snapshots table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS snapshots (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id INTEGER,
                product_id TEXT,
                product_url TEXT,
                product_title TEXT,
                sold_count INTEGER,
                price TEXT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                snapshot_order INTEGER,
                status TEXT DEFAULT 'success',
                error_message TEXT,
                FOREIGN KEY (session_id) REFERENCES sessions(session_id)
            )
        """)
        
        # Analysis results table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS analysis (
                session_id INTEGER,
                product_id TEXT,
                product_url TEXT,
                product_title TEXT,
                sold_t1 INTEGER,
                sold_t2 INTEGER,
                delta INTEGER,
                growth_rate REAL,
                rank_by_growth INTEGER,
                PRIMARY KEY (session_id, product_id),
                FOREIGN KEY (session_id) REFERENCES sessions(session_id)
            )
        """)

        self._migrate_drop_rank_by_delta(cursor)
        self._migrate_sessions_seo_keywords(cursor)
        self._migrate_sessions_win_keywords(cursor)

        # Keywords table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS keywords (
                session_id INTEGER,
                keyword TEXT,
                keyword_type TEXT,
                frequency INTEGER,
                rank INTEGER,
                keyword_bucket TEXT DEFAULT 'niche',
                win_ratio REAL DEFAULT 0.0,
                keyword_win_check INTEGER DEFAULT 0,
                PRIMARY KEY (session_id, keyword),
                FOREIGN KEY (session_id) REFERENCES sessions(session_id)
            )
        """)

        self._migrate_keywords_bucket(cursor)
        self._migrate_keywords_win_ratio(cursor)

        # Jobs table (web UI job tracking)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS jobs (
                job_id TEXT PRIMARY KEY,
                session_id INTEGER,
                job_name TEXT,
                status TEXT DEFAULT 'queued',
                message TEXT,
                total_urls INTEGER,
                processed_urls INTEGER,
                interval_hours REAL,
                remaining_seconds INTEGER,
                seo_keywords TEXT,
                win_keywords TEXT,
                created_at TIMESTAMP,
                started_at TIMESTAMP,
                completed_at TIMESTAMP,
                cancel_requested INTEGER DEFAULT 0,
                cancel_requested_at TIMESTAMP,
                snapshot1_success INTEGER,
                snapshot1_errors INTEGER,
                snapshot1_report TEXT,
                snapshot2_success INTEGER,
                snapshot2_errors INTEGER,
                snapshot2_report TEXT,
                FOREIGN KEY (session_id) REFERENCES sessions(session_id)
            )
        """)
        self._migrate_jobs_urls(cursor)

        conn.commit()
        conn.close()

    def _migrate_drop_rank_by_delta(self, cursor):
        """Remove legacy rank_by_delta column (merged into rank_by_growth). SQLite 3.35+."""
        cursor.execute("PRAGMA table_info(analysis)")
        cols = [row[1] for row in cursor.fetchall()]
        if cols and 'rank_by_delta' in cols:
            try:
                cursor.execute("ALTER TABLE analysis DROP COLUMN rank_by_delta")
            except sqlite3.OperationalError:
                pass

    def _migrate_sessions_seo_keywords(self, cursor):
        cursor.execute("PRAGMA table_info(sessions)")
        cols = [row[1] for row in cursor.fetchall()]
        if cols and "seo_keywords" not in cols:
            try:
                cursor.execute("ALTER TABLE sessions ADD COLUMN seo_keywords TEXT")
            except sqlite3.OperationalError:
                pass

    def _migrate_sessions_win_keywords(self, cursor):
        cursor.execute("PRAGMA table_info(sessions)")
        cols = [row[1] for row in cursor.fetchall()]
        if cols and "win_keywords" not in cols:
            try:
                cursor.execute("ALTER TABLE sessions ADD COLUMN win_keywords TEXT")
            except sqlite3.OperationalError:
                pass

    def _migrate_keywords_bucket(self, cursor):
        cursor.execute("PRAGMA table_info(keywords)")
        cols = [row[1] for row in cursor.fetchall()]
        if cols and "keyword_bucket" not in cols:
            try:
                cursor.execute(
                    "ALTER TABLE keywords ADD COLUMN keyword_bucket TEXT DEFAULT 'niche'"
                )
            except sqlite3.OperationalError:
                pass

    def _migrate_keywords_win_ratio(self, cursor):
        cursor.execute("PRAGMA table_info(keywords)")
        cols = [row[1] for row in cursor.fetchall()]
        if cols and "win_ratio" not in cols:
            try:
                cursor.execute(
                    "ALTER TABLE keywords ADD COLUMN win_ratio REAL DEFAULT 0.0"
                )
            except sqlite3.OperationalError:
                pass
        if cols and "keyword_win_check" not in cols:
            try:
                cursor.execute(
                    "ALTER TABLE keywords ADD COLUMN keyword_win_check INTEGER DEFAULT 0"
                )
            except sqlite3.OperationalError:
                pass

    def _migrate_jobs_urls(self, cursor):
        cursor.execute("PRAGMA table_info(jobs)")
        cols = [row[1] for row in cursor.fetchall()]
        if cols and "urls" not in cols:
            try:
                cursor.execute("ALTER TABLE jobs ADD COLUMN urls TEXT")
            except sqlite3.OperationalError:
                pass

    def create_session(
        self,
        check_interval_hours: float,
        total_products: int,
        seo_keywords: Optional[str] = None,
        win_keywords: Optional[str] = None,
    ) -> int:
        """Create a new tracking session"""
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO sessions (check_interval_hours, total_products, seo_keywords, win_keywords)
            VALUES (?, ?, ?, ?)
        """, (check_interval_hours, total_products, seo_keywords, win_keywords))
        
        session_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return session_id
    
    def save_snapshot(self, session_id: int, product_id: str, product_url: str,
                     product_title: str, sold_count: Optional[int],
                     snapshot_order: int, price: Optional[str] = None,
                     status: str = 'success', error_message: Optional[str] = None):
        """Save a product snapshot"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO snapshots 
            (session_id, product_id, product_url, product_title, sold_count, 
             price, snapshot_order, status, error_message)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (session_id, product_id, product_url, product_title, sold_count,
              price, snapshot_order, status, error_message))
        
        conn.commit()
        conn.close()
    
    def get_snapshot(self, session_id: int, snapshot_order: int) -> List[Dict[str, Any]]:
        """Get all products from a specific snapshot"""
        conn = self.get_connection()
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT * FROM snapshots
            WHERE session_id = ? AND snapshot_order = ?
            ORDER BY id
        """, (session_id, snapshot_order))
        
        rows = cursor.fetchall()
        conn.close()
        
        return [dict(row) for row in rows]
    
    def save_analysis(self, session_id: int, analysis_data: List[Dict[str, Any]]):
        """Save analysis results"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        for item in analysis_data:
            cursor.execute("""
                INSERT OR REPLACE INTO analysis
                (session_id, product_id, product_url, product_title,
                 sold_t1, sold_t2, delta, growth_rate, rank_by_growth)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                session_id,
                item['product_id'],
                item['product_url'],
                item['product_title'],
                item['sold_t1'],
                item['sold_t2'],
                item['delta'],
                item['growth_rate'],
                item['rank_by_growth'],
            ))
        
        conn.commit()
        conn.close()
    
    def save_keywords(self, session_id: int, keywords_data: List[Dict[str, Any]]):
        """Save extracted keywords"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        for item in keywords_data:
            cursor.execute("""
                INSERT OR REPLACE INTO keywords
                (session_id, keyword, keyword_type, frequency, rank, keyword_bucket, win_ratio, keyword_win_check)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                session_id,
                item['keyword'],
                item['keyword_type'],
                item['frequency'],
                item['rank'],
                item.get('keyword_bucket', 'niche'),
                item.get('win_ratio', 0.0),
                1 if item.get('keyword_win_check') else 0,
            ))
        
        conn.commit()
        conn.close()
    
    def get_analysis(self, session_id: int) -> List[Dict[str, Any]]:
        """Get analysis results for a session"""
        conn = self.get_connection()
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT * FROM analysis
            WHERE session_id = ?
            ORDER BY (rank_by_growth IS NULL), rank_by_growth, delta DESC
        """, (session_id,))
        
        rows = cursor.fetchall()
        conn.close()
        
        return [dict(row) for row in rows]
    
    def get_keywords(self, session_id: int) -> List[Dict[str, Any]]:
        """Get keywords for a session"""
        conn = self.get_connection()
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT * FROM keywords
            WHERE session_id = ?
            ORDER BY rank
        """, (session_id,))
        
        rows = cursor.fetchall()
        conn.close()
        
        return [dict(row) for row in rows]
    
    def update_session_status(self, session_id: int, status: str):
        """Update session status"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            UPDATE sessions
            SET status = ?
            WHERE session_id = ?
        """, (status, session_id))
        
        conn.commit()
        conn.close()
    
    def get_session(self, session_id: int) -> Optional[Dict[str, Any]]:
        """Get session info"""
        conn = self.get_connection()
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT * FROM sessions WHERE session_id = ?
        """, (session_id,))
        
        row = cursor.fetchone()
        conn.close()
        
        return dict(row) if row else None

    def save_job(self, job_id: str, job_data: Dict[str, Any]):
        """Save or update job metadata to database"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Extract snapshot metadata
        snap1 = job_data.get("snapshot1") or {}
        snap2 = job_data.get("snapshot2") or {}
        
        urls_text = job_data.get("urls_raw")
        if urls_text is None:
            urls_text = job_data.get("urls")

        cursor.execute("""
            INSERT OR REPLACE INTO jobs (
                job_id, session_id, job_name, status, message,
                total_urls, processed_urls, interval_hours, remaining_seconds,
                seo_keywords, win_keywords, urls,
                created_at, started_at, completed_at,
                cancel_requested, cancel_requested_at,
                snapshot1_success, snapshot1_errors, snapshot1_report,
                snapshot2_success, snapshot2_errors, snapshot2_report
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            job_id,
            job_data.get("session_id"),
            job_data.get("job_name"),
            job_data.get("status"),
            job_data.get("message"),
            job_data.get("total_urls"),
            job_data.get("processed_urls"),
            job_data.get("interval_hours"),
            job_data.get("remaining_seconds"),
            job_data.get("seo_keywords"),
            job_data.get("win_keywords"),
            urls_text,
            self._dt_to_str(job_data.get("created_at")),
            self._dt_to_str(job_data.get("started_at")),
            self._dt_to_str(job_data.get("completed_at")),
            1 if job_data.get("cancel_requested") else 0,
            self._dt_to_str(job_data.get("cancel_requested_at")),
            snap1.get("success"),
            snap1.get("errors"),
            snap1.get("report"),
            snap2.get("success"),
            snap2.get("errors"),
            snap2.get("report"),
        ))
        
        conn.commit()
        conn.close()

    def get_job(self, job_id: str) -> Optional[Dict[str, Any]]:
        """Get job metadata from database"""
        conn = self.get_connection()
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM jobs WHERE job_id = ?", (job_id,))
        row = cursor.fetchone()
        conn.close()
        
        if not row:
            return None
        
        job = dict(row)
        if "urls" in job:
            job["urls_raw"] = job.pop("urls") or ""
        # Reconstruct nested snapshot dicts
        job["snapshot1"] = {
            "success": job.pop("snapshot1_success", None),
            "errors": job.pop("snapshot1_errors", None),
            "report": job.pop("snapshot1_report", None),
        }
        job["snapshot2"] = {
            "success": job.pop("snapshot2_success", None),
            "errors": job.pop("snapshot2_errors", None),
            "report": job.pop("snapshot2_report", None),
        }
        job["cancel_requested"] = bool(job.get("cancel_requested"))
        # Parse timestamps
        for k in ["created_at", "started_at", "completed_at", "cancel_requested_at"]:
            if job.get(k):
                job[k] = self._str_to_dt(job[k])
        return job

    def get_all_jobs(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get recent jobs from database"""
        conn = self.get_connection()
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT * FROM jobs
            ORDER BY created_at DESC
            LIMIT ?
        """, (limit,))
        
        rows = cursor.fetchall()
        conn.close()
        
        jobs = []
        for row in rows:
            job = dict(row)
            if "urls" in job:
                job["urls_raw"] = job.pop("urls") or ""
            job["snapshot1"] = {
                "success": job.pop("snapshot1_success", None),
                "errors": job.pop("snapshot1_errors", None),
                "report": job.pop("snapshot1_report", None),
            }
            job["snapshot2"] = {
                "success": job.pop("snapshot2_success", None),
                "errors": job.pop("snapshot2_errors", None),
                "report": job.pop("snapshot2_report", None),
            }
            job["cancel_requested"] = bool(job.get("cancel_requested"))
            for k in ["created_at", "started_at", "completed_at", "cancel_requested_at"]:
                if job.get(k):
                    job[k] = self._str_to_dt(job[k])
            jobs.append(job)
        
        return jobs

    def _dt_to_str(self, dt) -> Optional[str]:
        """Convert datetime to ISO string for DB storage"""
        if dt is None:
            return None
        if isinstance(dt, datetime):
            return dt.isoformat()
        return str(dt)

    def _str_to_dt(self, s: Optional[str]):
        """Convert ISO string to datetime"""
        if not s:
            return None
        try:
            return datetime.fromisoformat(s)
        except:
            return None


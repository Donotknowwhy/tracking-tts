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
                status TEXT DEFAULT 'in_progress'
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
                rank_by_delta INTEGER,
                rank_by_growth INTEGER,
                PRIMARY KEY (session_id, product_id),
                FOREIGN KEY (session_id) REFERENCES sessions(session_id)
            )
        """)
        
        # Keywords table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS keywords (
                session_id INTEGER,
                keyword TEXT,
                keyword_type TEXT,
                frequency INTEGER,
                rank INTEGER,
                PRIMARY KEY (session_id, keyword),
                FOREIGN KEY (session_id) REFERENCES sessions(session_id)
            )
        """)
        
        conn.commit()
        conn.close()
    
    def create_session(self, check_interval_hours: float, total_products: int) -> int:
        """Create a new tracking session"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO sessions (check_interval_hours, total_products)
            VALUES (?, ?)
        """, (check_interval_hours, total_products))
        
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
                 sold_t1, sold_t2, delta, growth_rate, rank_by_delta, rank_by_growth)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                session_id,
                item['product_id'],
                item['product_url'],
                item['product_title'],
                item['sold_t1'],
                item['sold_t2'],
                item['delta'],
                item['growth_rate'],
                item['rank_by_delta'],
                item['rank_by_growth']
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
                (session_id, keyword, keyword_type, frequency, rank)
                VALUES (?, ?, ?, ?, ?)
            """, (
                session_id,
                item['keyword'],
                item['keyword_type'],
                item['frequency'],
                item['rank']
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
            ORDER BY rank_by_delta
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

"""
Export snapshot 1 data to CSV immediately
"""

import sqlite3
import csv
from pathlib import Path
import config

def export_snapshot1():
    """Export snapshot 1 data"""
    conn = sqlite3.connect(config.DB_PATH)
    cursor = conn.cursor()
    
    # Get snapshot 1 data
    cursor.execute('''
        SELECT 
            product_id,
            product_url,
            product_title,
            sold_count,
            price,
            timestamp
        FROM snapshots
        WHERE session_id = 1 AND snapshot_order = 1
        ORDER BY sold_count DESC
    ''')
    
    rows = cursor.fetchall()
    
    if not rows:
        print("❌ No snapshot 1 data found!")
        return
    
    # Export to CSV
    output_file = config.OUTPUT_DIR / "snapshot_1_raw_data.csv"
    
    with open(output_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        
        # Header
        writer.writerow([
            'Product ID',
            'Product URL',
            'Product Title',
            'Sold Count (t1)',
            'Price',
            'Timestamp'
        ])
        
        # Data rows
        for row in rows:
            writer.writerow(row)
    
    conn.close()
    
    print("="*80)
    print("✅ SNAPSHOT 1 DATA EXPORTED!")
    print("="*80)
    print()
    print(f"File: {output_file}")
    print(f"Total products: {len(rows)}")
    print()
    
    # Print summary
    print("📊 SUMMARY:")
    print("-"*80)
    for idx, row in enumerate(rows, 1):
        product_id, url, title, sold, price, timestamp = row
        print(f"{idx}. {title[:60]}...")
        print(f"   Sold (t1): {sold}")
        print(f"   URL: {url}")
        print()
    
    print("="*80)

if __name__ == '__main__':
    export_snapshot1()

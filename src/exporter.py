import csv
from datetime import datetime
from typing import List, Dict, Any
import config
from openpyxl import Workbook
from openpyxl.styles import Font, Alignment, PatternFill
from openpyxl.utils import get_column_letter

def export_to_csv(analysis_results: List[Dict[str, Any]], 
                  keywords_results: List[Dict[str, Any]],
                  session_id: int) -> tuple:
    """
    Export analysis and keywords to CSV files
    
    Args:
        analysis_results: Product analysis data
        keywords_results: Keyword extraction data
        session_id: Session ID for filename
    
    Returns:
        Tuple of (products_csv_path, keywords_csv_path)
    """
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    # Products CSV
    products_csv = config.OUTPUT_DIR / f"products_session_{session_id}_{timestamp}.csv"
    
    with open(products_csv, 'w', newline='', encoding='utf-8') as f:
        if analysis_results:
            fieldnames = [
                'rank',
                'product_url',
                'product_title',
                'sold_t1',
                'sold_t2',
                'sold_delta',
                'growth_rate_percent',
                'rank_by_growth'
            ]
            
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            
            for row in analysis_results:
                writer.writerow({
                    'rank': row['rank_by_delta'],
                    'product_url': row['product_url'],
                    'product_title': row['product_title'],
                    'sold_t1': row['sold_t1'],
                    'sold_t2': row['sold_t2'],
                    'sold_delta': row['delta'],
                    'growth_rate_percent': f"{row['growth_rate']:.2%}",
                    'rank_by_growth': row.get('rank_by_growth', 'N/A')
                })
    
    # Keywords CSV
    keywords_csv = config.OUTPUT_DIR / f"keywords_session_{session_id}_{timestamp}.csv"
    
    with open(keywords_csv, 'w', newline='', encoding='utf-8') as f:
        if keywords_results:
            fieldnames = ['rank', 'keyword', 'keyword_type', 'frequency']
            
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            
            for row in keywords_results:
                writer.writerow(row)
    
    return str(products_csv), str(keywords_csv)

def export_to_excel(analysis_results: List[Dict[str, Any]],
                    keywords_results: List[Dict[str, Any]],
                    session_id: int) -> str:
    """
    Export analysis and keywords to an easy-to-read Excel workbook.
    """
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    excel_path = config.OUTPUT_DIR / f"report_session_{session_id}_{timestamp}.xlsx"

    wb = Workbook()
    ws_products = wb.active
    ws_products.title = "Products"

    product_headers = [
        "Rank",
        "Product URL",
        "Product Title",
        "Sold T1",
        "Sold T2",
        "Sold Delta",
        "Growth Rate (%)",
        "Rank by Growth"
    ]
    ws_products.append(product_headers)

    for row in analysis_results:
        ws_products.append([
            row["rank_by_delta"],
            row["product_url"],
            row["product_title"],
            row["sold_t1"],
            row["sold_t2"],
            row["delta"],
            f"{row['growth_rate'] * 100:.2f}%",
            row.get("rank_by_growth", "N/A"),
        ])

    ws_keywords = wb.create_sheet("Keywords")
    keyword_headers = ["Rank", "Keyword", "Type", "Frequency"]
    ws_keywords.append(keyword_headers)

    for kw in keywords_results:
        ws_keywords.append([
            kw["rank"],
            kw["keyword"],
            kw["keyword_type"],
            kw["frequency"],
        ])

    for ws in [ws_products, ws_keywords]:
        header_fill = PatternFill(start_color="1F4E78", end_color="1F4E78", fill_type="solid")
        for idx, _ in enumerate(ws[1], start=1):
            cell = ws.cell(row=1, column=idx)
            cell.font = Font(bold=True, color="FFFFFF")
            cell.alignment = Alignment(horizontal="center", vertical="center")
            cell.fill = header_fill

        ws.freeze_panes = "A2"

        for col in ws.columns:
            max_len = max(len(str(cell.value)) if cell.value is not None else 0 for cell in col)
            width = min(max(max_len + 2, 12), 60)
            col_letter = get_column_letter(col[0].column)
            ws.column_dimensions[col_letter].width = width

    wb.save(excel_path)
    return str(excel_path)


def export_snapshot_to_excel(snapshot_rows: List[Dict[str, Any]],
                             session_id: int,
                             snapshot_order: int) -> str:
    """
    Export a single snapshot (t1 or t2) to an easy-to-read Excel workbook.
    """
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    excel_path = config.OUTPUT_DIR / (
        f"snapshot_{snapshot_order}_session_{session_id}_{timestamp}.xlsx"
    )

    wb = Workbook()
    ws = wb.active
    ws.title = f"Snapshot {snapshot_order}"

    headers = [
        "Product URL",
        "Product Title",
        "Sold Count",
        "Price",
        "Status",
        "Error Message",
        "Timestamp",
    ]
    ws.append(headers)

    for row in snapshot_rows:
        ws.append([
            row.get("product_url"),
            row.get("product_title"),
            row.get("sold_count"),
            row.get("price"),
            row.get("status"),
            row.get("error_message"),
            row.get("timestamp"),
        ])

    header_fill = PatternFill(start_color="1F4E78", end_color="1F4E78", fill_type="solid")
    for idx, _ in enumerate(ws[1], start=1):
        cell = ws.cell(row=1, column=idx)
        cell.font = Font(bold=True, color="FFFFFF")
        cell.alignment = Alignment(horizontal="center", vertical="center")
        cell.fill = header_fill

    ws.freeze_panes = "A2"
    for col in ws.columns:
        max_len = max(len(str(cell.value)) if cell.value is not None else 0 for cell in col)
        width = min(max(max_len + 2, 12), 70)
        col_letter = get_column_letter(col[0].column)
        ws.column_dimensions[col_letter].width = width

    wb.save(excel_path)
    return str(excel_path)

def print_summary(analysis_results: List[Dict[str, Any]], 
                  keywords_results: List[Dict[str, Any]]):
    """Print summary to console"""
    print("\n" + "="*80)
    print("📊 ANALYSIS SUMMARY")
    print("="*80)
    
    print(f"\n🏆 TOP 10 PRODUCTS BY GROWTH (Delta):\n")
    
    for i, product in enumerate(analysis_results[:10], 1):
        print(f"{i}. {product['product_title'][:60]}")
        print(f"   Sold: {product['sold_t1']} → {product['sold_t2']} "
              f"(+{product['delta']}, {product['growth_rate']:.1%} growth)")
        print(f"   URL: {product['product_url']}")
        print()
    
    print("\n" + "-"*80)
    print(f"\n🔑 TOP 10 KEYWORDS:\n")
    
    for kw in keywords_results[:10]:
        print(f"{kw['rank']}. {kw['keyword']} "
              f"({kw['keyword_type']}) - {kw['frequency']} occurrences")
    
    print("\n" + "="*80)

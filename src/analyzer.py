from typing import List, Dict, Any, Optional, Set
from datetime import datetime, timezone
import re
from collections import Counter
import config
from src.parser import clean_title


def parse_seo_blocklist(raw: Optional[str]) -> Set[str]:
    """
    Tách danh sách từ khóa user cho là chỉ để tối ưu SEO (mỗi dòng / dấu phẩy / chấm phẩy).
    So khớp không phân biệt hoa thường.
    """
    if not raw or not str(raw).strip():
        return set()
    parts = re.split(r"[\n,;]+", str(raw))
    return {p.strip().lower() for p in parts if p.strip()}


def classify_keyword_bucket(keyword: str, seo_set: Set[str]) -> str:
    """
    Trả về 'seo' nếu cụm hoặc bất kỳ từ nào trong cụm khớp danh sách SEO; ngược lại 'niche'.
    """
    if not seo_set:
        return "niche"
    k = keyword.strip().lower()
    if k in seo_set:
        return "seo"
    for tok in k.split():
        if tok in seo_set:
            return "seo"
    return "niche"


def parse_win_keywords(raw: Optional[str]) -> List[str]:
    """
    Parse danh sách keyword user muốn kiểm tra mức độ win.
    Chuẩn hóa theo clean_title để đảm bảo so khớp với title đã clean.
    """
    if not raw or not str(raw).strip():
        return []
    parts = re.split(r"[\n,;]+", str(raw))
    seen: set[str] = set()
    out: List[str] = []
    for p in parts:
        item = p.strip()
        if not item:
            continue
        norm = clean_title(item)
        if not norm:
            continue
        if norm in seen:
            continue
        seen.add(norm)
        out.append(norm)
    return out


def _parse_db_timestamp(value: Any) -> Optional[datetime]:
    """
    Parse timestamp SQLite (thường là string). Nếu không có tzinfo thì coi như UTC.
    """
    if value is None:
        return None
    s = str(value).strip()
    if not s:
        return None
    try:
        dt = datetime.fromisoformat(s.replace(" ", "T", 1))
    except ValueError:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt

def compute_growth(snapshots_t1: List[Dict[str, Any]], 
                   snapshots_t2: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Compute growth metrics by comparing two snapshots
    
    Args:
        snapshots_t1: First snapshot (t1)
        snapshots_t2: Second snapshot (t2)
    
    Returns:
        List of analysis results with growth metrics
    """
    # Create mapping: product_id -> snapshot data
    t1_map = {s['product_id']: s for s in snapshots_t1 if s['status'] == 'success'}
    t2_map = {s['product_id']: s for s in snapshots_t2 if s['status'] == 'success'}
    
    results = []
    
    # Compare products that exist in both snapshots
    for product_id in t1_map.keys():
        if product_id not in t2_map:
            continue
        
        t1_data = t1_map[product_id]
        t2_data = t2_map[product_id]
        
        sold_t1 = t1_data['sold_count']
        sold_t2 = t2_data['sold_count']
        
        # Skip if either sold count is None
        if sold_t1 is None or sold_t2 is None:
            continue
        
        # Compute metrics
        delta = sold_t2 - sold_t1
        growth_rate = delta / max(sold_t1, 1)
        
        results.append({
            'product_id': product_id,
            'product_url': t1_data['product_url'],
            'product_title': t1_data['product_title'],
            'sold_t1': sold_t1,
            'sold_t2': sold_t2,
            'delta': delta,
            'growth_rate': growth_rate,
            'rank_by_growth': None,
            'scanned_at_t1': t1_data.get('timestamp'),
            'scanned_at_t2': t2_data.get('timestamp'),
        })
    
    # Rank by growth = volume change (delta) descending; ties: lower % growth ranks higher.
    # Only delta >= 0 get a rank (negative deltas: e.g. shop ban / data anomaly — no rank).
    eligible = [r for r in results if r['delta'] >= 0]
    eligible_sorted = sorted(
        eligible,
        key=lambda x: (-x['delta'], x['growth_rate']),
    )
    for rank, item in enumerate(eligible_sorted, 1):
        item['rank_by_growth'] = rank

    # Stable display order: ranked first, then unranked (typically delta < 0)
    results.sort(
        key=lambda x: (
            x['rank_by_growth'] is None,
            x['rank_by_growth'] if x['rank_by_growth'] is not None else 0,
            -x['delta'],
        )
    )

    return results

def extract_keywords(
    analysis_results: List[Dict[str, Any]],
    top_n: int = None,
    seo_keywords_raw: Optional[str] = None,
    win_keywords_raw: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """
    Extract keywords from top-performing products.

    Args:
        analysis_results: Analysis results sorted by rank
        top_n: Number of top products to extract keywords from (defaults to config)
        seo_keywords_raw: Text từ user — các từ/cụm coi là SEO template để tách cột niche

    Returns:
        List of keyword rows with keyword_seo / keyword_niche (một trong hai có giá trị), type, rank
    """
    if top_n is None:
        top_n = config.TRACKING_CONFIG['top_n_keywords']

    seo_set = parse_seo_blocklist(seo_keywords_raw)
    win_keywords = parse_win_keywords(win_keywords_raw)
    win_keywords_set = set(win_keywords)

    # Precompute evaluation products for "win" criteria.
    # - time_ok: t2 - t1 > 6h (chỉ cần như ý kiến của bạn)
    # - delta filters: delta > 20, delta > 5
    eval_products: List[Dict[str, Any]] = []
    for r in analysis_results:
        title = r.get("product_title") or ""
        title_clean = clean_title(title)
        if not title_clean:
            continue

        delta = r.get("delta")
        if delta is None:
            continue

        t1 = _parse_db_timestamp(r.get("scanned_at_t1"))
        t2 = _parse_db_timestamp(r.get("scanned_at_t2"))
        time_ok = False
        if t1 and t2:
            time_ok = (t2 - t1).total_seconds() / 3600.0 > 6.0

        eval_products.append(
            {
                "title": title_clean,
                "delta": delta,
                "time_ok": time_ok,
            }
        )

    # Decide win flags for each user-provided keyword.
    # - condition1: appears in >= 2 products with delta > 20
    # - condition2: appears in >= 10 products with delta > 5 AND total occurrences >= 10
    win_map: Dict[str, bool] = {}
    for kw in win_keywords:
        cond1_products = 0
        cond2_products = 0
        cond2_occurrences = 0
        for p in eval_products:
            if not p["time_ok"]:
                continue
            if kw not in p["title"]:
                continue
            if p["delta"] > 20:
                cond1_products += 1
            if p["delta"] > 5:
                cond2_products += 1
                cond2_occurrences += p["title"].count(kw)

        win_map[kw] = (cond1_products >= 2) or (
            cond2_products >= 10 and cond2_occurrences >= 10
        )
    
    # Filter: only products with meaningful delta
    filtered = [
        r for r in analysis_results 
        if r['delta'] >= config.TRACKING_CONFIG['min_delta_threshold']
    ]
    
    # Take top N by delta
    top_products = sorted(filtered, key=lambda x: x['delta'], reverse=True)[:top_n]
    
    if not top_products:
        return []
    
    # Collect all keywords
    unigrams = Counter()
    bigrams = Counter()
    trigrams = Counter()
    
    for product in top_products:
        title = product['product_title']
        if not title:
            continue
        
        # Clean title
        cleaned = clean_title(title)
        
        # Tokenize
        words = cleaned.split()
        
        # Remove stopwords
        words = [
            w for w in words 
            if w not in config.KEYWORD_CONFIG['generic_stopwords']
            and len(w) >= config.KEYWORD_CONFIG['min_word_length']
        ]
        
        # Extract n-grams
        # Unigrams (1-word)
        for word in words:
            unigrams[word] += 1
        
        # Bigrams (2-word)
        for i in range(len(words) - 1):
            bigram = f"{words[i]} {words[i+1]}"
            bigrams[bigram] += 1
        
        # Trigrams (3-word)
        if config.KEYWORD_CONFIG['max_ngram_size'] >= 3:
            for i in range(len(words) - 2):
                trigram = f"{words[i]} {words[i+1]} {words[i+2]}"
                trigrams[trigram] += 1
    
    # Combine all keywords
    all_keywords = []
    
    # Add unigrams
    for keyword, freq in unigrams.most_common(10):
        all_keywords.append({
            'keyword': keyword,
            'keyword_type': 'unigram',
            'frequency': freq,
            'rank': 0  # Will be set later
        })
    
    # Add bigrams
    for keyword, freq in bigrams.most_common(10):
        all_keywords.append({
            'keyword': keyword,
            'keyword_type': 'bigram',
            'frequency': freq,
            'rank': 0
        })
    
    # Add trigrams
    for keyword, freq in trigrams.most_common(10):
        all_keywords.append({
            'keyword': keyword,
            'keyword_type': 'trigram',
            'frequency': freq,
            'rank': 0
        })
    
    # Sort by frequency and assign ranks
    all_keywords = sorted(all_keywords, key=lambda x: x['frequency'], reverse=True)
    for rank, item in enumerate(all_keywords[:10], 1):  # Top 10 overall
        item['rank'] = rank

    top = all_keywords[:10]

    # Attach SEO bucket + win flag to extracted keywords.
    for item in top:
        kw = item["keyword"]
        bucket = classify_keyword_bucket(kw, seo_set)
        item["keyword_bucket"] = bucket
        item["keyword_seo"] = kw if bucket == "seo" else ""
        item["keyword_niche"] = kw if bucket == "niche" else ""
        item["keyword_win_check"] = (
            win_map.get(kw) if kw in win_keywords_set else ""
        )

    # Ensure user win-keywords are present in output rows.
    existing_keywords = {it["keyword"] for it in top}
    extra_items: List[Dict[str, Any]] = []
    for kw in win_keywords:
        if kw in existing_keywords:
            continue

        freq = 0
        any_found = False
        for product in top_products:
            cleaned_title = clean_title(product.get("product_title") or "")
            if kw not in cleaned_title:
                continue
            any_found = True
            freq += cleaned_title.count(kw)

        # Infer keyword_type by token count (consistent with sheet).
        tok_count = len(kw.split())
        if tok_count == 1:
            keyword_type = "unigram"
        elif tok_count == 2:
            keyword_type = "bigram"
        elif tok_count == 3:
            keyword_type = "trigram"
        else:
            keyword_type = "phrase"

        bucket = classify_keyword_bucket(kw, seo_set)
        extra_items.append(
            {
                "keyword": kw,
                "keyword_type": keyword_type,
                "frequency": freq,
                "rank": 0,
                "keyword_bucket": bucket,
                "keyword_seo": kw if bucket == "seo" else "",
                "keyword_niche": kw if bucket == "niche" else "",
                "keyword_win_check": win_map.get(kw, False),
                # If user keyword never appears in the extracted pool, keep it but let freq drive rank.
                "_any_found": any_found,
            }
        )

    out_items = top + extra_items
    out_items = sorted(out_items, key=lambda x: x.get("frequency", 0), reverse=True)
    for rank, item in enumerate(out_items, start=1):
        item["rank"] = rank

    # Drop internal helper key.
    for item in out_items:
        item.pop("_any_found", None)

    return out_items

def filter_results(analysis_results: List[Dict[str, Any]],
                   min_delta: int = None) -> List[Dict[str, Any]]:
    """
    Filter analysis results based on threshold
    
    Args:
        analysis_results: Raw analysis results
        min_delta: Minimum delta threshold (defaults to config)
    
    Returns:
        Filtered results
    """
    if min_delta is None:
        min_delta = config.TRACKING_CONFIG['min_delta_threshold']
    
    return [r for r in analysis_results if r['delta'] >= min_delta]

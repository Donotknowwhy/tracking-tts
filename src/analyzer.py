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

def _extract_ngrams(title: str, min_word_len: int, stopwords: set, max_ngram: int):
    """
    Extract n-grams (contiguous phrases) from a title.
    Returns list of (phrase, type) tuples.
    """
    cleaned = clean_title(title)
    words = cleaned.split()
    # Remove stopwords and short words
    words = [
        w for w in words
        if w not in stopwords and len(w) >= min_word_len
    ]
    phrases = []
    # Unigrams
    for w in words:
        phrases.append((w, 'unigram'))
    # Bigrams
    for i in range(len(words) - 1):
        phrases.append((f"{words[i]} {words[i+1]}", 'bigram'))
    # Trigrams
    if max_ngram >= 3:
        for i in range(len(words) - 2):
            phrases.append((f"{words[i]} {words[i+1]} {words[i+2]}", 'trigram'))
    return phrases


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
        win_keywords_raw: Text từ user — các từ/cụm muốn kiểm tra mức độ win

    Returns:
        List of keyword rows with keyword_seo / keyword_niche (một trong hai có giá trị), type, rank
    """
    if top_n is None:
        top_n = config.TRACKING_CONFIG['top_n_keywords']

    seo_set = parse_seo_blocklist(seo_keywords_raw)
    win_keywords = parse_win_keywords(win_keywords_raw)
    win_keywords_set = set(win_keywords)

    min_word_len = config.KEYWORD_CONFIG['min_word_length']
    stopwords = config.KEYWORD_CONFIG['generic_stopwords']
    max_ngram = config.KEYWORD_CONFIG['max_ngram_size']

    # ─── Pass 1: Build phrase -> {products} and phrase -> {growing_products} ─
    # Using ALL products in analysis_results (not just top N) for accurate A/B ratio
    phrase_to_products: Dict[str, set] = {}
    phrase_to_growing: Dict[str, set] = {}  # products with delta > 0
    phrase_total_delta: Dict[str, float] = {}  # for avg_delta tiebreaker

    for r in analysis_results:
        title = r.get("product_title") or ""
        if not title:
            continue
        product_id = r.get("product_id") or id(title)  # fallback to title-based id
        delta = r.get("delta") or 0
        is_growing = delta > 0

        ngrams = _extract_ngrams(title, min_word_len, stopwords, max_ngram)
        seen_phrases: set = set()  # deduplicate within same product

        for phrase, _ in ngrams:
            if phrase in seen_phrases:
                continue
            seen_phrases.add(phrase)

            if phrase not in phrase_to_products:
                phrase_to_products[phrase] = set()
                phrase_to_growing[phrase] = set()
                phrase_total_delta[phrase] = 0.0

            phrase_to_products[phrase].add(product_id)
            if is_growing:
                phrase_to_growing[phrase].add(product_id)
            phrase_total_delta[phrase] += delta

    # ─── Pass 2: Compute win metrics for all phrases ───────────────────────────
    all_keywords_data: Dict[str, Dict[str, Any]] = {}
    for phrase, products in phrase_to_products.items():
        A = len(products)
        B = len(phrase_to_growing[phrase])
        win_ratio = (B / A) if A > 0 else 0.0
        avg_delta = (phrase_total_delta[phrase] / A) if A > 0 else 0.0

        # Determine keyword_type from token count
        tok_count = len(phrase.split())
        if tok_count == 1:
            keyword_type = "unigram"
        elif tok_count == 2:
            keyword_type = "bigram"
        elif tok_count == 3:
            keyword_type = "trigram"
        else:
            keyword_type = "phrase"

        all_keywords_data[phrase] = {
            "keyword": phrase,
            "keyword_type": keyword_type,
            "frequency": A,  # unique products count
            "A": A,
            "B": B,
            "win_ratio": win_ratio,
            "keyword_win_check": win_ratio > 0.05,
            "avg_delta": avg_delta,
        }

    # ─── Pass 3: Filter to top N by delta + extract from those products ────────
    # Get top N products by delta for keyword extraction (phrase pool)
    filtered = [
        r for r in analysis_results
        if r.get('delta', 0) >= config.TRACKING_CONFIG['min_delta_threshold']
    ]
    top_products = sorted(filtered, key=lambda x: x.get('delta', 0), reverse=True)[:top_n]

    if not top_products:
        return []

    # Extract phrases from top products to determine which phrases to include in output
    # (Only include phrases that appear in at least 1 top product)
    top_product_phrases: set = set()
    for product in top_products:
        title = product.get("product_title") or ""
        ngrams = _extract_ngrams(title, min_word_len, stopwords, max_ngram)
        for phrase, _ in ngrams:
            top_product_phrases.add(phrase)

    # ─── Pass 4: Add win_keywords (user-provided) even if not in top products ──
    for kw in win_keywords:
        if kw not in all_keywords_data:
            tok_count = len(kw.split())
            if tok_count == 1:
                keyword_type = "unigram"
            elif tok_count == 2:
                keyword_type = "bigram"
            elif tok_count == 3:
                keyword_type = "trigram"
            else:
                keyword_type = "phrase"
            all_keywords_data[kw] = {
                "keyword": kw,
                "keyword_type": keyword_type,
                "frequency": 0,
                "A": 0,
                "B": 0,
                "win_ratio": 0.0,
                "keyword_win_check": False,
                "avg_delta": 0.0,
            }

    # ─── Pass 5: Build final list (phrases from top products + user win_keywords) ─
    out_items: List[Dict[str, Any]] = []

    # Add phrases that appear in top products
    for phrase, data in all_keywords_data.items():
        if phrase in top_product_phrases or phrase in win_keywords_set:
            out_items.append(data.copy())

    # Sort by frequency desc, then avg_delta desc
    out_items.sort(key=lambda x: (-x["frequency"], -x["avg_delta"]))

    # Assign rank and SEO bucket
    for rank, item in enumerate(out_items, start=1):
        kw = item["keyword"]
        bucket = classify_keyword_bucket(kw, seo_set)
        item["rank"] = rank
        item["keyword_bucket"] = bucket
        item["keyword_seo"] = kw if bucket == "seo" else ""
        item["keyword_niche"] = kw if bucket == "niche" else ""

        # Override win_check for user-provided keywords
        if kw in win_keywords_set:
            item["keyword_win_check"] = item.get("keyword_win_check", False)

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

import re
from typing import Optional, Dict, Any
from bs4 import BeautifulSoup

def extract_product_id(url: str) -> str:
    """
    Extract product ID from TikTok Shop URL
    
    Supports multiple URL formats:
    - https://www.tiktok.com/shop/pdp/1732128313499292514 → 1732128313499292514
    - https://www.tiktok.com/shop/pdp/vintage-style.../1732128311479866210 → 1732128311479866210
    - https://www.tiktok.com/view/product/1732275855990363066 → 1732275855990363066
    """
    # Extract numeric ID (typically 16-19 digits)
    match = re.search(r'/(\d{16,19})(?:\?|$)', url)
    if match:
        return match.group(1)
    
    # Fallback: use full URL as ID
    return url

def parse_sold_count(text: str) -> Optional[int]:
    """
    Parse sold count from various formats
    
    Examples:
    - "1234 sold" → 1234
    - "1.2K sold" → 1200
    - "10K+ sold" → 10000
    - "1.5M sold" → 1500000
    - "Sold: 1,234" → 1234
    - "193 đã được bán" → 193 (Vietnamese format)
    """
    if not text:
        return None
    
    # Clean text
    text = text.strip().lower()
    
    # Pattern 1: number + K/M + "sold"
    # Matches: "1234 sold", "1.2k sold", "10k+ sold"
    match = re.search(r'([\d,\.]+)([km]?)\+?\s*(?:sold|units)', text, re.IGNORECASE)
    
    if not match:
        # Pattern 2: "Sold: 1,234"
        match = re.search(r'sold:?\s*([\d,\.]+)([km]?)', text, re.IGNORECASE)
    
    if not match:
        # Pattern 3: Vietnamese format "193 đã được bán"
        match = re.search(r'([\d,\.]+)([km]?)\+?\s*(?:đã được bán|đã bán)', text, re.IGNORECASE)
    
    if not match:
        # Pattern 4: Just number near "sold" keyword (more relaxed)
        # Look for sold/units keyword, then find nearest number within 50 chars
        sold_pos = text.find('sold')
        if sold_pos == -1:
            sold_pos = text.find('đã được bán')
        if sold_pos == -1:
            sold_pos = text.find('đã bán')
        
        if sold_pos >= 0:
            # Search ±50 chars around "sold" keyword
            start = max(0, sold_pos - 50)
            end = min(len(text), sold_pos + 50)
            snippet = text[start:end]
            match = re.search(r'([\d,\.]+)([km]?)', snippet, re.IGNORECASE)
    
    if not match:
        return None
    
    try:
        # Extract number and suffix
        number_str = match.group(1).replace(',', '')
        number = float(number_str)
        suffix = match.group(2).upper() if len(match.groups()) > 1 else ''
        
        # Apply multiplier
        if suffix == 'K':
            return int(number * 1000)
        elif suffix == 'M':
            return int(number * 1000000)
        else:
            return int(number)
    except (ValueError, IndexError):
        return None

def parse_product_page(html_content: str) -> Dict[str, Any]:
    """
    Parse product page HTML to extract key information
    
    Returns:
        Dict with keys: title, sold_count, price, etc.
    """
    soup = BeautifulSoup(html_content, 'html.parser')
    
    result = {
        'title': None,
        'sold_count': None,
        'price': None,
    }
    
    # Extract title
    # Try multiple selectors
    title_selectors = [
        'h1[class*="title"]',
        'h1[data-testid*="title"]',
        '[class*="ProductTitle"]',
        'h1',
    ]
    
    for selector in title_selectors:
        title_elem = soup.select_one(selector)
        if title_elem:
            result['title'] = title_elem.get_text(strip=True)
            break
    
    # Extract sold count - try multiple methods
    sold_count = None
    
    # Method 1: Try JSON data in script tags
    import json
    import re
    
    script_tags = soup.find_all('script', type='application/json')
    for script in script_tags:
        try:
            json_text = script.string
            if not json_text:
                continue
            
            # Priority 1: Look for sold_count inside "product_info" or "product_model" context
            # Pattern: "product_info":{..."product_model":{..."sold_count":"193"...}}
            product_context = re.search(
                r'"product_(?:info|model)"[^}]*?"sold_count"\s*:\s*"?(\d+)"?',
                json_text,
                re.IGNORECASE | re.DOTALL
            )
            if product_context:
                sold_count = int(product_context.group(1))
                break
            
            # Priority 2: Look for sold_count near product_id (within 500 chars)
            product_id_matches = re.finditer(r'"product_id"\s*:\s*"(\d{16,19})"', json_text)
            for match in product_id_matches:
                start = match.start()
                # Search ±500 chars around product_id
                snippet = json_text[max(0, start-500):min(len(json_text), start+500)]
                sold_match = re.search(r'"sold_count"\s*:\s*"?(\d+)"?', snippet, re.IGNORECASE)
                if sold_match:
                    sold_count = int(sold_match.group(1))
                    break
            
            if sold_count:
                break
            
        except Exception:
            continue
    
    # Method 2: Search all visible text for sold pattern (fallback)
    if sold_count is None:
        page_text = soup.get_text()
        sold_count = parse_sold_count(page_text)
    
    result['sold_count'] = sold_count
    
    # Extract price
    price_selectors = [
        '[class*="price"]',
        '[data-testid*="price"]',
        '[class*="Price"]',
    ]
    
    for selector in price_selectors:
        price_elem = soup.select_one(selector)
        if price_elem:
            result['price'] = price_elem.get_text(strip=True)
            break
    
    return result

def clean_title(title: str) -> str:
    """Clean product title for keyword extraction"""
    if not title:
        return ""
    
    # Remove emojis and special characters
    title = re.sub(r'[^\w\s-]', ' ', title)
    
    # Remove extra whitespace
    title = re.sub(r'\s+', ' ', title)
    
    # Lowercase
    title = title.lower().strip()
    
    return title

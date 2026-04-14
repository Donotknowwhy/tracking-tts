import re
import logging
from typing import Optional, Dict, Any

from bs4 import BeautifulSoup
import httpx

logger = logging.getLogger(__name__)

# ─── Mobile URL Resolution ───────────────────────────────────────────────────


def resolve_tiktok_mobile_url(url: str, timeout: float = 15.0) -> str:
    """
    Resolve a TikTok mobile/short URL to its desktop product URL WITHOUT
    opening a browser. Uses an HTTP HEAD (fallback GET) request that follows
    redirects, then extracts the product ID and reconstructs the clean
    desktop view URL.

    Handles:
      - https://vm.tiktok.com/ZT98vDUPn87fB-bDQBF/   (short link redirect chain)
      - https://www.tiktok.com/view/product/...       (already desktop — returned as-is)

    Returns the resolved desktop URL or the original URL if resolution fails.
    """
    url = url.strip()
    if not url:
        return url

    # Already a desktop view URL — return as-is
    if "/view/product/" in url or "/shop/pdp/" in url:
        logger.info("Desktop URL (unchanged): %s", url)
        return url

    # Only try to resolve vm.tiktok.com short links (non-browser, no CAPTCHA)
    if "vm.tiktok.com" not in url:
        logger.info("Non-TikTok URL (unchanged): %s", url)
        return url

    logger.info("Resolving mobile URL: %s", url)
    resolved = _resolve_via_http(url, timeout=timeout)
    if resolved:
        logger.info("  → Desktop URL: %s", resolved)
    else:
        logger.warning("  → Resolution failed, using original: %s", url)
    return resolved if resolved else url


def _resolve_via_http(url: str, timeout: float) -> Optional[str]:
    """
    Issue an HTTP HEAD (fallback GET) with full redirect following to obtain
    the final URL after all redirects, then reconstruct the clean desktop URL.
    """
    try:
        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            ),
            "Accept": "*/*",
            "Accept-Language": "en-US,en;q=0.9",
        }

        # Use stream=True + follow_redirects so we never download the body.
        # We only read the final URL from .url after the redirect chain completes.
        with httpx.Client(timeout=timeout, follow_redirects=True, trust_env=False) as client:
            # HEAD avoids downloading body; TikTok should honour it for redirects
            resp = client.head(url, headers=headers)

            # Some hosts/CDNs block HEAD — fall back to GET but stop after headers
            if resp.status_code in (405, 400, 405):
                resp = client.get(url, headers=headers, stream=True)

            final_url = str(resp.url)

        # If we got a valid desktop URL, return it
        if "/view/product/" in final_url or "/shop/pdp/" in final_url:
            return final_url

        # Otherwise extract product ID from the final URL and build desktop link
        pid = _extract_pid_from_url(final_url)
        if pid:
            return f"https://www.tiktok.com/view/product/{pid}"
        return None

    except Exception:
        return None


def _extract_pid_from_url(url: str) -> Optional[str]:
    """Extract 16-19 digit product ID from any TikTok URL."""
    match = re.search(r"/(\d{16,19})(?:\?|$)", url)
    if match:
        return match.group(1)
    return None


# ─── Product ID ─────────────────────────────────────────────────────────────


def extract_product_id(url: str) -> str:
    """
    Extract product ID from TikTok Shop URL

    Supports multiple URL formats:
    - https://www.tiktok.com/shop/pdp/1732128313499292514 → 1732128313499292514
    - https://www.tiktok.com/shop/pdp/vintage-style.../1732128311479866210 → 1732128311479866210
    - https://www.tiktok.com/view/product/1732275855990363066 → 1732275855990363066
    """
    match = re.search(r"/(\d{16,19})(?:\?|$)", url)
    if match:
        return match.group(1)
    return url


# ─── Title (TikTok Shop PDP / view/product DOM) ───────────────────────────────


def _parse_title_tiktok_shop(soup: BeautifulSoup) -> Optional[str]:
    """
    Title: <span data-fmp="true" class="... text-color-UIText1Display ...">...</span>
    """
    el = soup.select_one('span[data-fmp="true"][class*="text-color-UIText1Display"]')
    if el:
        text = el.get_text(strip=True)
        return text if text else None
    el = soup.select_one('span[data-fmp="true"]')
    if el and "text-color-UIText1Display" in (el.get("class") or []):
        text = el.get_text(strip=True)
        return text if text else None
    return None


def _parse_title_fallback(soup: BeautifulSoup) -> Optional[str]:
    """Legacy selectors when TikTok changes class names."""
    for selector in (
        'h1[class*="title"]',
        'h1[data-testid*="title"]',
        '[class*="ProductTitle"]',
        "h1",
    ):
        title_elem = soup.select_one(selector)
        if title_elem:
            t = title_elem.get_text(strip=True)
            if t:
                return t
    return None


# ─── Price (UIText1 spans: discounted + non-discounted) ─────────────────────


def _is_price_uitext1_span(class_attr: Any) -> bool:
    """Current price uses text-color-UIText1; strikethrough old price uses UIText3 — skip UIText3."""
    if not class_attr:
        return False
    if isinstance(class_attr, list):
        joined = " ".join(class_attr)
    else:
        joined = str(class_attr)
    if "text-color-UIText3" in joined:
        return False
    return "text-color-UIText1" in joined


def _is_price_part_span(class_attr: Any) -> bool:
    """
    Price parts ($ and decimals) can use font-medium class instead of UIText1.
    Include font-sans font-medium spans as price parts (but skip UIText3 strikethrough).
    """
    if not class_attr:
        return False
    if isinstance(class_attr, list):
        joined = " ".join(class_attr)
    else:
        joined = str(class_attr)
    if "text-color-UIText3" in joined:
        return False
    return "text-color-UIText1" in joined or "font-medium" in joined


def _parse_price_tiktok_shop(soup: BeautifulSoup) -> Optional[float]:
    """
    Price blocks live in div.flex...items-baseline with nested spans:
      <span class="text-color-UIText1 ...">$</span>
      <span class="text-color-UIText1 ...">20</span>
      <span class="text-color-UIText1 ...">.<!-- -->31</span>
    Strikethrough uses text-color-UIText3 — excluded.

    Also handles spans that use font-medium class instead of UIText1 for
    the dollar sign and decimal parts (e.g. class="font-sans font-medium").

    Works for:
      - Sale: -52% + $20.31 + $42.30 struck — we only sum price part spans in the row.
      - No sale: only UIText1 price spans.
    """
    candidates = soup.find_all(
        "div",
        class_=lambda c: _class_has_all(c, ("flex", "items-baseline")),
    )
    for div in candidates:
        spans = div.find_all("span", class_=lambda c: _is_price_part_span(c))
        if not spans:
            continue
        raw = "".join(s.get_text(strip=True) for s in spans)
        raw = raw.replace("$", "").replace(",", "").strip()
        # Handle HTML comments in decimal parts like ".<!-- -->31"
        raw = re.sub(r'<!--.*?-->', '', raw)
        if not raw:
            continue
        try:
            return float(raw)
        except ValueError:
            continue
    return None


def _class_has_all(class_attr: Any, needles: tuple) -> bool:
    if not class_attr:
        return False
    if isinstance(class_attr, list):
        s = " ".join(class_attr)
    else:
        s = str(class_attr)
    return all(n in s for n in needles)


def _parse_price_fallback(soup: BeautifulSoup) -> Optional[str]:
    """Return raw price string for backward compatibility if float parse fails elsewhere."""
    for selector in ('[class*="price"]', '[data-testid*="price"]', '[class*="Price"]'):
        price_elem = soup.select_one(selector)
        if price_elem:
            t = price_elem.get_text(strip=True)
            if t:
                return t
    return None


# ─── Sold count (span with "… sold") + JSON fallback ────────────────────────


def _parse_sold_count_tiktok_shop(soup: BeautifulSoup) -> Optional[int]:
    """
    Case A — rating row + sold:
      ... <span class="...SmallText1-Regular text-color-UIText2">66 sold</span>
    Case B — only sold:
      <span class="...SmallText1-Regular text-color-UIText2">8 sold</span>

    Take the number from any span whose text contains 'sold' (case-insensitive).
    """
    for span in soup.find_all("span"):
        text = span.get_text(strip=True)
        if not text or "sold" not in text.lower():
            continue
        # Prefer explicit "N sold" / "N.Nk sold"
        m = re.search(
            r"([\d,\.]+)\s*([km]?)\+?\s*sold",
            text,
            re.IGNORECASE,
        )
        if m:
            return _int_from_sold_match(m)
        # Single integer before "sold"
        m = re.search(r"(\d+)\s*sold", text, re.IGNORECASE)
        if m:
            return int(m.group(1))
    return None


def _int_from_sold_match(m: re.Match) -> int:
    number_str = m.group(1).replace(",", "")
    number = float(number_str)
    suffix = (m.group(2) or "").upper()
    if suffix == "K":
        return int(number * 1000)
    if suffix == "M":
        return int(number * 1000000)
    return int(number)


def parse_sold_count(text: str) -> Optional[int]:
    """
    Parse sold count from free text (fallback when DOM selectors miss).

    Examples:
    - "1234 sold" → 1234
    - "1.2K sold" → 1200
    - "193 đã được bán" → 193
    """
    if not text:
        return None

    text = text.strip().lower()

    match = re.search(r"([\d,\.]+)([km]?)\+?\s*(?:sold|units)", text, re.IGNORECASE)
    if not match:
        match = re.search(r"sold:?\s*([\d,\.]+)([km]?)", text, re.IGNORECASE)
    if not match:
        match = re.search(
            r"([\d,\.]+)([km]?)\+?\s*(?:đã được bán|đã bán)", text, re.IGNORECASE
        )
    if not match:
        sold_pos = text.find("sold")
        if sold_pos == -1:
            sold_pos = text.find("đã được bán")
        if sold_pos == -1:
            sold_pos = text.find("đã bán")
        if sold_pos >= 0:
            snippet = text[max(0, sold_pos - 50) : min(len(text), sold_pos + 50)]
            match = re.search(r"([\d,\.]+)([km]?)", snippet, re.IGNORECASE)

    if not match:
        return None

    try:
        number_str = match.group(1).replace(",", "")
        number = float(number_str)
        suffix = match.group(2).upper() if len(match.groups()) > 1 else ""
        if suffix == "K":
            return int(number * 1000)
        if suffix == "M":
            return int(number * 1000000)
        return int(number)
    except (ValueError, IndexError):
        return None


def _parse_sold_count_json_scripts(soup: BeautifulSoup) -> Optional[int]:
    """Legacy: sold_count inside application/json script tags."""
    script_tags = soup.find_all("script", type="application/json")
    for script in script_tags:
        json_text = script.string
        if not json_text:
            continue
        try:
            product_context = re.search(
                r'"product_(?:info|model)"[^}]*?"sold_count"\s*:\s*"?(\d+)"?',
                json_text,
                re.IGNORECASE | re.DOTALL,
            )
            if product_context:
                return int(product_context.group(1))
            for match in re.finditer(r'"product_id"\s*:\s*"(\d{16,19})"', json_text):
                start = match.start()
                snippet = json_text[max(0, start - 500) : min(len(json_text), start + 500)]
                sold_match = re.search(r'"sold_count"\s*:\s*"?(\d+)"?', snippet, re.IGNORECASE)
                if sold_match:
                    return int(sold_match.group(1))
        except Exception:
            continue
    return None


# ─── Main entry ───────────────────────────────────────────────────────────────


def parse_product_page(html_content: str) -> Dict[str, Any]:
    """
    Parse TikTok Shop product HTML.

    Priority:
      1. DOM patterns documented for TikTok Shop (title / price UIText1 / sold span).
      2. JSON-in-script and text fallbacks for older or partial HTML.

    Returns:
        dict with keys: title (str|None), sold_count (int|None), price (float|str|None).
        ``price`` is float when parsed from UIText1 spans; str when only fallback text exists.
    """
    soup = BeautifulSoup(html_content, "html.parser")

    result: Dict[str, Any] = {
        "title": None,
        "sold_count": None,
        "price": None,
    }

    # Title
    result["title"] = _parse_title_tiktok_shop(soup) or _parse_title_fallback(soup)

    # Price (prefer numeric from UIText1)
    price_float = _parse_price_tiktok_shop(soup)
    if price_float is not None:
        result["price"] = price_float
    else:
        result["price"] = _parse_price_fallback(soup)

    # Sold
    sold = _parse_sold_count_tiktok_shop(soup)
    if sold is None:
        sold = _parse_sold_count_json_scripts(soup)
    if sold is None:
        sold = parse_sold_count(soup.get_text())
    result["sold_count"] = sold

    return result


def clean_title(title: str) -> str:
    """Clean product title for keyword extraction."""
    if not title:
        return ""
    title = re.sub(r"[^\w\s-]", " ", title)
    title = re.sub(r"\s+", " ", title)
    return title.lower().strip()

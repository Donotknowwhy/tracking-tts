import os
from pathlib import Path
from urllib.parse import urlparse, unquote

# Project paths
BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
OUTPUT_DIR = DATA_DIR / "output"
DB_PATH = DATA_DIR / "tracking.db"

# Create directories if not exist
DATA_DIR.mkdir(exist_ok=True)
OUTPUT_DIR.mkdir(exist_ok=True)

# Proxy configuration (default)
# You can override at runtime using:
#   - environment variable: TTS_PROXY
#   - CLI flag: --proxy in auto_track.py
PROXY_SERVER = "191.101.251.108"
PROXY_PORT = 20826
PROXY_USERNAME = "KgVOxvHW"
PROXY_PASSWORD = "8BYAZdC83i37"
PROXY_TYPE = "http"


def _build_proxy_url() -> str:
    return f"{PROXY_TYPE}://{PROXY_USERNAME}:{PROXY_PASSWORD}@{PROXY_SERVER}:{PROXY_PORT}"


PROXY_URL = _build_proxy_url()


def apply_proxy(proxy_input: str) -> None:
    """
    Apply proxy settings dynamically from a string.

    Supported formats:
    1) http://host:port:user:pass
    2) http://user:pass@host:port
    3) host:port:user:pass  (defaults to http)
    """
    global PROXY_SERVER, PROXY_PORT, PROXY_USERNAME, PROXY_PASSWORD, PROXY_TYPE, PROXY_URL

    raw = (proxy_input or "").strip()
    if not raw:
        raise ValueError("Empty proxy input")

    # Format: host:port:user:pass
    if "://" not in raw and raw.count(":") >= 3:
        parts = raw.split(":")
        if len(parts) != 4:
            raise ValueError("Invalid proxy format. Expected host:port:user:pass")
        host, port_str, username, password = parts
        PROXY_TYPE = "http"
        PROXY_SERVER = host.strip()
        PROXY_PORT = int(port_str.strip())
        PROXY_USERNAME = username.strip()
        PROXY_PASSWORD = password.strip()
        PROXY_URL = _build_proxy_url()
        return

    # Format: http://host:port:user:pass
    if "://" in raw and "@" not in raw:
        parsed = urlparse(raw)
        if not parsed.scheme:
            raise ValueError("Proxy must include scheme, e.g. http://...")

        segments = (parsed.netloc or "").split(":")
        if len(segments) == 4:
            host, port_str, username, password = segments
            PROXY_TYPE = parsed.scheme
            PROXY_SERVER = host.strip()
            PROXY_PORT = int(port_str.strip())
            PROXY_USERNAME = unquote(username.strip())
            PROXY_PASSWORD = unquote(password.strip())
            PROXY_URL = _build_proxy_url()
            return

    # Format: http://user:pass@host:port
    parsed = urlparse(raw)
    if not parsed.scheme or not parsed.hostname or not parsed.port:
        raise ValueError("Invalid proxy URL")

    PROXY_TYPE = parsed.scheme
    PROXY_SERVER = parsed.hostname
    PROXY_PORT = int(parsed.port)
    PROXY_USERNAME = unquote(parsed.username or "")
    PROXY_PASSWORD = unquote(parsed.password or "")
    PROXY_URL = _build_proxy_url()

# Scraping configuration
SCRAPING_CONFIG = {
    "delay_min": 3,          # Minimum delay between requests (seconds)
    "delay_max": 8,          # Maximum delay between requests (seconds)
    "max_retries": 3,        # Max retry attempts per product
    "timeout": 30000,        # Page load timeout (milliseconds)
    "headless": True,        # True: chạy ngầm; False: bật cửa sổ (debug/CAPTCHA)
    "user_data_dir": str(BASE_DIR / "browser_data"),  # Persistent browser profile
}

# Tracking configuration
TRACKING_CONFIG = {
    "check_interval_hours": 3,    # Time between t1 and t2
    "min_delta_threshold": 5,     # Minimum delta to consider meaningful
    "top_n_keywords": 10,         # Number of top keywords to extract
}

# Keyword extraction
KEYWORD_CONFIG = {
    "min_word_length": 2,
    "max_ngram_size": 3,  # Extract 1-word, 2-word, 3-word phrases
    "generic_stopwords": {
        # Basic stopwords
        'the', 'a', 'an', 'for', 'with', 'and', 'or', 'in', 'on', 'at',
        # Generic quality words
        'new', 'hot', 'sale', 'best', 'top', 'free', 'shipping',
        'high', 'quality', 'premium', 'great', 'perfect',
        # Time
        '2024', '2025', '2026', 'latest',
        # Size/fit
        'size', 'fit', 'large', 'small', 'medium', 'xl', 'xxl',
        # Generic categories (too broad)
        'product', 'item', 'gift', 'pack', 'set',
        # Promotional
        'discount', 'deal', 'offer', 'limited',
    }
}

# TikTok Login Configuration (Optional)
# If provided, tool will automatically login to TikTok
# This eliminates 90% of CAPTCHAs
TIKTOK_EMAIL = None     # Set to "your_email@example.com" or keep None
TIKTOK_PASSWORD = None  # Set to "your_password" or keep None

# Alternative: Use .env file for security
# Create .env file with:
#   TIKTOK_EMAIL=your_email@example.com
#   TIKTOK_PASSWORD=your_password
from pathlib import Path
if Path('.env').exists():
    from dotenv import load_dotenv
    load_dotenv()
    TIKTOK_EMAIL = os.getenv('TIKTOK_EMAIL', TIKTOK_EMAIL)
    TIKTOK_PASSWORD = os.getenv('TIKTOK_PASSWORD', TIKTOK_PASSWORD)

# Optional proxy override from env
runtime_proxy = os.getenv("TTS_PROXY")
if runtime_proxy:
    apply_proxy(runtime_proxy)
USER_AGENTS = [
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
]

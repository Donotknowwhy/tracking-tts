"""
HTTP proxy sanity check — same config as TikTokScraper (config.PROXY_URL).
"""
from __future__ import annotations

import config


def is_http_proxy_configured() -> bool:
    return bool(getattr(config, "PROXY_TYPE", None) == "http" and getattr(config, "PROXY_SERVER", None))


def verify_http_proxy(timeout: float = 15.0) -> tuple[bool, str | None]:
    """
    Returns (ok, error_message).
    If ok is True, error_message is None.
    When no HTTP proxy is configured, returns (True, None).
    """
    if not is_http_proxy_configured():
        return True, None
    try:
        import httpx
    except ImportError:
        return False, "Thiếu thư viện httpx (pip install httpx)."
    try:
        with httpx.Client(proxy=config.PROXY_URL, timeout=timeout, verify=True) as client:
            r = client.get("https://api.ipify.org?format=json")
            if r.status_code != 200:
                return False, f"HTTP {r.status_code} khi kiểm tra proxy"
            return True, None
    except Exception as e:
        msg = str(e).strip()
        if len(msg) > 400:
            msg = msg[:400] + "…"
        return False, msg or "Không kết nối được qua proxy"

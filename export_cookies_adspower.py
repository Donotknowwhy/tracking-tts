#!/usr/bin/env python3
"""
Lấy toàn bộ cookie (kể cả HttpOnly) từ profile AdsPower qua CDP.
Không cần gói trả phí API cookies của AdsPower.

Cách dùng:
  1. Đảm bảo AdsPower đang chạy, API key / port đúng trong config bên dưới.
  2. Profile đã login TikTok ít nhất một lần.
  3. Chạy: ./venv/bin/python export_cookies_adspower.py

Script sẽ: start browser → connect Playwright CDP → ghi cookies.json → stop browser.
"""
from __future__ import annotations

import asyncio
import json
import os
import sys
from pathlib import Path

import httpx
from playwright.async_api import async_playwright

# Cùng host/port/key như AdsPower → Automation → API (hoặc env)
ADSPOWER_BASE = os.getenv("ADSPOWER_BASE", "http://127.0.0.1:50325")
ADSPOWER_TOKEN = os.getenv("ADSPOWER_API_KEY", "").strip() or "5d30dd29e3288ee5d5b29c0880eda29b00898c40ee69101d"
# Profile đã login TikTok
PROFILE_ID = os.getenv("ADSPOWER_PROFILE_ID", "k1bgmfvh").strip()
OUT_FILE = Path(__file__).resolve().parent / "cookies.json"


def _to_cookie_editor_row(c: dict) -> dict:
    """Playwright cookie -> format gần Cookie-Editor / scraper."""
    row = {
        "name": c["name"],
        "value": c["value"],
        "domain": c["domain"],
        "path": c.get("path") or "/",
        "secure": bool(c.get("secure")),
        "httpOnly": bool(c.get("httpOnly")),
    }
    exp = c.get("expires")
    if exp and exp > 0:
        row["expirationDate"] = exp
    ss = c.get("sameSite")
    if ss:
        s = str(ss).lower()
        if s == "none":
            row["sameSite"] = "no_restriction"
        elif s in ("lax", "strict"):
            row["sameSite"] = s
        else:
            row["sameSite"] = s
    return row


async def main() -> int:
    headers = {"Authorization": f"Bearer {ADSPOWER_TOKEN}"}
    async with httpx.AsyncClient(timeout=60.0) as client:
        r = await client.post(
            f"{ADSPOWER_BASE}/api/v2/browser-profile/start",
            headers=headers,
            json={"profile_id": PROFILE_ID, "last_opened_tabs": "0", "proxy_detection": "0"},
        )
        data = r.json()
        if data.get("code") != 0:
            print("Start browser failed:", data, file=sys.stderr)
            return 1
        ws = (data.get("data") or {}).get("ws", {}).get("puppeteer")
        if not ws:
            print("No puppeteer ws in response:", data, file=sys.stderr)
            return 1

    try:
        async with async_playwright() as p:
            browser = await p.chromium.connect_over_cdp(ws)
            contexts = browser.contexts
            if not contexts:
                print("No browser contexts", file=sys.stderr)
                return 1
            ctx = contexts[0]
            raw = await ctx.cookies()
            # Chỉ giữ domain TikTok (tránh file quá lớn / lỗi add_cookies)
            tiktok = [
                c
                for c in raw
                if "tiktok" in (c.get("domain") or "").lower()
                or "byteoversea" in (c.get("domain") or "").lower()
                or "ttwstatic" in (c.get("domain") or "").lower()
            ]
            if not tiktok:
                tiktok = raw
                print("Warning: no tiktok* domain filter match, exporting all cookies", file=sys.stderr)

            rows = [_to_cookie_editor_row(c) for c in tiktok]
            OUT_FILE.write_text(json.dumps(rows, indent=2), encoding="utf-8")
            print(f"Wrote {len(rows)} cookies to {OUT_FILE}")
    finally:
        async with httpx.AsyncClient(timeout=30.0) as client:
            await client.post(
                f"{ADSPOWER_BASE}/api/v2/browser-profile/stop",
                headers=headers,
                json={"profile_id": PROFILE_ID},
            )

    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))

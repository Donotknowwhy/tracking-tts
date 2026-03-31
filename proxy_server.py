"""
Setup local HTTP proxy that forwards to SOCKS5
Run this first before using the scraper
"""

import asyncio
import aiohttp
from aiohttp import web
from aiohttp_socks import ProxyConnector
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# SOCKS5 proxy config
SOCKS5_URL = "socks5://xhdd6lei:kkWcjgqlMXbgxTcK@74.81.53.51:43997"

# Local HTTP proxy config
LOCAL_HOST = '127.0.0.1'
LOCAL_PORT = 8888

async def proxy_handler(request):
    """Forward HTTP requests through SOCKS5 proxy"""
    target_url = request.match_info.get('url', '')
    
    if not target_url:
        return web.Response(text="No URL provided", status=400)
    
    # Decode URL
    import urllib.parse
    target_url = urllib.parse.unquote(target_url)
    
    logger.info(f"Proxying request to: {target_url}")
    
    try:
        # Create connector with SOCKS5 proxy
        connector = ProxyConnector.from_url(SOCKS5_URL)
        
        async with aiohttp.ClientSession(connector=connector) as session:
            # Forward headers
            headers = dict(request.headers)
            headers.pop('Host', None)
            
            # Make request through SOCKS5
            async with session.get(target_url, headers=headers, timeout=30) as response:
                content = await response.read()
                
                return web.Response(
                    body=content,
                    status=response.status,
                    headers=dict(response.headers)
                )
    
    except Exception as e:
        logger.error(f"Proxy error: {e}")
        return web.Response(text=f"Proxy error: {str(e)}", status=500)

async def start_proxy_server():
    """Start local HTTP proxy server"""
    app = web.Application()
    app.router.add_get('/proxy/{url:.*}', proxy_handler)
    
    runner = web.AppRunner(app)
    await runner.setup()
    
    site = web.TCPSite(runner, LOCAL_HOST, LOCAL_PORT)
    await site.start()
    
    logger.info(f"Local HTTP proxy started at http://{LOCAL_HOST}:{LOCAL_PORT}")
    logger.info(f"Forwarding to SOCKS5: {SOCKS5_URL.split('@')[1]}")
    logger.info("Press Ctrl+C to stop")
    
    # Keep running
    try:
        await asyncio.Event().wait()
    except KeyboardInterrupt:
        logger.info("Shutting down proxy server...")

if __name__ == '__main__':
    asyncio.run(start_proxy_server())

"""Local article responses for deterministic integration tests."""

import asyncio
from collections import Counter
from dataclasses import dataclass, field

import pytest
from aiohttp import web

PARAGRAPH = (
    "The newspaper project has moved its command line tool into an installed Python package. "
    "Readers can download articles and retain the extracted content and metadata. "
    "The package includes the downloader so it works outside the source checkout. "
)
ARTICLE_HTML = (
    '<html lang="en"><head><title>Package news</title>'
    '<meta name="description" content="A packaging update">'
    '<meta name="author" content="Jane Example">'
    '<meta property="article:published_time" content="2026-11-12T12:00:00Z">'
    '<meta property="og:image" content="https://example.com/image.jpg">'
    "</head><body><article><h1>Package news</h1>"
    + "".join("<p>" + PARAGRAPH + "</p>" for _ in range(4))
    + "</article></body></html>"
)


@dataclass
class ArticleServer:
    url: str = ""
    requests: Counter = field(default_factory=Counter)
    active: int = 0
    peak: int = 0
    started: asyncio.Event = field(default_factory=asyncio.Event)


@pytest.fixture
async def article_server():
    state = ArticleServer()

    async def handle(request):
        name = request.match_info["name"]
        state.requests[name] += 1
        state.started.set()
        state.active += 1
        state.peak = max(state.peak, state.active)
        try:
            await asyncio.sleep(0.03 if name != "timeout" else 0.3)
            if name in {"missing", "retry", "unavailable"}:
                status = 404 if name == "missing" else 503
                if name != "retry" or state.requests[name] == 1:
                    return web.Response(status=status)
            if name == "empty":
                return web.Response(text="<html><body></body></html>")
            if name == "oversize":
                return web.Response(text="x" * 4096)
            return web.Response(text=ARTICLE_HTML, content_type="text/html")
        finally:
            state.active -= 1

    app = web.Application()
    app.router.add_get("/{name}", handle)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "127.0.0.1", 0)
    await site.start()
    state.url = f"http://127.0.0.1:{runner.addresses[0][1]}"
    try:
        yield state
    finally:
        await runner.cleanup()

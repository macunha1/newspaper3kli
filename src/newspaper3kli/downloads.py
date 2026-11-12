"""Bounded asynchronous HTTP downloads with extraction outside the event loop."""

import asyncio
import logging
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path

import aiohttp

from .articles import extract_article
from .storage import save_article

logger = logging.getLogger(__name__)
RETRYABLE_STATUSES = frozenset({429, 500, 502, 503, 504})


@dataclass(frozen=True, slots=True)
class DownloadOptions:
    output_path: Path
    concurrency: int = 8
    per_host: int = 2
    timeout: float = 30.0
    retries: int = 2
    keep_html: bool = False
    use_nlp: bool = True
    max_response_bytes: int = 10 * 1024 * 1024


@dataclass(slots=True)
class DownloadSummary:
    succeeded: int = 0
    failed: int = 0


async def fetch_html(session: aiohttp.ClientSession, url: str, options: DownloadOptions) -> str:
    for attempt in range(options.retries + 1):
        try:
            async with session.get(url) as response:
                response.raise_for_status()
                content = bytearray()
                async for chunk in response.content.iter_chunked(64 * 1024):
                    content.extend(chunk)
                    if len(content) > options.max_response_bytes:
                        raise ValueError(f"Response exceeds {options.max_response_bytes} bytes")
                return content.decode(response.charset or "utf-8", errors="replace")
        except aiohttp.ClientResponseError as error:
            if error.status not in RETRYABLE_STATUSES or attempt == options.retries:
                raise
        except aiohttp.ClientConnectionError, TimeoutError:
            if attempt == options.retries:
                raise
        await asyncio.sleep(min(0.25 * 2**attempt, 5.0))
    raise AssertionError("Retry loop must return or raise")


def _extract_and_save(html: str, url: str, options: DownloadOptions) -> None:
    article = extract_article(html, url, keep_html=options.keep_html, use_nlp=options.use_nlp)
    save_article(article, options.output_path)


async def download_articles(
    urls: Sequence[str], options: DownloadOptions, *, verify_ssl: bool = True
) -> DownloadSummary:
    summary = DownloadSummary()
    if not urls:
        return summary
    pending = iter(dict.fromkeys(urls))
    connector = aiohttp.TCPConnector(limit=options.concurrency, limit_per_host=options.per_host, ssl=verify_ssl)
    async with aiohttp.ClientSession(
        connector=connector,
        timeout=aiohttp.ClientTimeout(total=options.timeout),
        headers={"User-Agent": "newspaper3kli/0.1.1"},
        cookie_jar=aiohttp.DummyCookieJar(),
        trust_env=True,
    ) as session:

        async def worker() -> None:
            for url in pending:
                try:
                    html = await fetch_html(session, url, options)
                    await asyncio.to_thread(_extract_and_save, html, url, options)
                except (
                    aiohttp.ClientError,
                    TimeoutError,
                    ValueError,
                    LookupError,
                    OSError,
                    ImportError,
                ) as error:
                    logger.error("URL %s failed: %s", url, error)
                    summary.failed += 1
                else:
                    summary.succeeded += 1

        async with asyncio.TaskGroup() as group:
            for _ in range(min(options.concurrency, len(urls))):
                group.create_task(worker())
    return summary

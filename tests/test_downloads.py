"""Verify concurrency and failure handling over a real local HTTP server."""

import asyncio
import json
import sys
import threading

import pytest

from newspaper3kli import downloads
from newspaper3kli.downloads import DownloadOptions, download_articles


@pytest.mark.parametrize("concurrency,per_host", [(2, 8), (8, 2)])
async def test_concurrency_is_bounded(article_server, tmp_path, concurrency, per_host):
    urls = [f"{article_server.url}/{index}" for index in range(8)]
    result = await download_articles(urls, DownloadOptions(tmp_path, concurrency=concurrency, per_host=per_host))

    assert result.succeeded == 8
    assert result.failed == 0
    assert article_server.peak == 2
    assert len(list(tmp_path.glob("*.json"))) == 8


async def test_duplicate_urls_are_only_downloaded_once(article_server, tmp_path):
    url = f"{article_server.url}/article"
    result = await download_articles([url, url], DownloadOptions(tmp_path))
    assert result.succeeded == 1
    assert article_server.requests["article"] == 1


async def test_transient_error_is_retried(article_server, tmp_path):
    result = await download_articles([f"{article_server.url}/retry"], DownloadOptions(tmp_path, retries=1))
    assert result.succeeded == 1
    assert article_server.requests["retry"] == 2


async def test_retry_limit_is_respected(article_server, tmp_path):
    result = await download_articles([f"{article_server.url}/unavailable"], DownloadOptions(tmp_path, retries=1))
    assert result.failed == 1
    assert article_server.requests["unavailable"] == 2


async def test_extraction_does_not_block_event_loop(monkeypatch, article_server, tmp_path):
    started = threading.Event()
    release = threading.Event()

    def extract(html, url, options):
        started.set()
        release.wait(timeout=2)

    monkeypatch.setattr(downloads, "_extract_and_save", extract)
    task = asyncio.create_task(download_articles([f"{article_server.url}/article"], DownloadOptions(tmp_path)))
    try:
        assert await asyncio.wait_for(asyncio.to_thread(started.wait, 2), timeout=3)
        assert not task.done()
    finally:
        release.set()
        await task


async def test_permanent_error_does_not_retry_or_stop_batch(article_server, tmp_path, caplog):
    result = await download_articles(
        [f"{article_server.url}/missing", f"{article_server.url}/article"], DownloadOptions(tmp_path)
    )
    assert (result.succeeded, result.failed) == (1, 1)
    assert article_server.requests["missing"] == 1
    assert "404" in caplog.text


@pytest.mark.parametrize("path", ["timeout", "oversize", "empty", "unavailable"])
async def test_failures_are_reported(article_server, tmp_path, path):
    options = DownloadOptions(tmp_path, retries=0, timeout=0.1, max_response_bytes=3000)
    result = await download_articles([f"{article_server.url}/{path}"], options)
    assert (result.succeeded, result.failed) == (0, 1)
    assert not list(tmp_path.iterdir())


async def test_invalid_url_is_reported(tmp_path):
    result = await download_articles(["not a url"], DownloadOptions(tmp_path, retries=0))
    assert result.failed == 1


async def test_cancellation_propagates(article_server, tmp_path):
    task = asyncio.create_task(download_articles([f"{article_server.url}/timeout"], DownloadOptions(tmp_path)))
    async with asyncio.timeout(2):
        await article_server.started.wait()
    task.cancel()
    with pytest.raises(asyncio.CancelledError):
        await task


@pytest.mark.parametrize("failure", [False, True])
async def test_installed_cli_download(article_server, tmp_path, failure):
    path = "missing" if failure else "article"
    process = await asyncio.create_subprocess_exec(
        sys.executable,
        "-m",
        "newspaper3kli",
        "-o",
        str(tmp_path),
        f"{article_server.url}/{path}",
        cwd=tmp_path,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    _, stderr = await asyncio.wait_for(process.communicate(), timeout=30)
    assert process.returncode == (1 if failure else 0), stderr.decode()
    if not failure:
        (metadata_path,) = tmp_path.glob("*.json")
        assert json.loads(metadata_path.read_text())["keywords"]

"""Compare sequential and concurrent downloads against a delayed local server."""

import argparse
import asyncio
import json
import platform
from pathlib import Path
from statistics import median
from tempfile import TemporaryDirectory
from time import perf_counter

from aiohttp import web

from newspaper3kli.articles import extract_article
from newspaper3kli.downloads import DownloadOptions, download_articles

HTML = (
    "<html lang='en'><head><title>Benchmark article</title></head><body><article>"
    + "<p>This benchmark exercises asynchronous downloads with local HTTP responses. "
    "The command extracts article text and metadata before saving the results. "
    "Connection reuse and bounded workers let network requests overlap safely.</p>" * 4 + "</article></body></html>"
)


async def benchmark(articles: int, latency: float, concurrency: int, samples: int) -> dict[str, str | int | float]:
    async def handle(request: web.Request) -> web.Response:
        await asyncio.sleep(latency)
        return web.Response(text=HTML, content_type="text/html")

    app = web.Application()
    app.router.add_get("/{article}", handle)
    runner = web.AppRunner(app)
    await runner.setup()
    try:
        await web.TCPSite(runner, "127.0.0.1", 0).start()
        port = runner.addresses[0][1]
        urls = [f"http://127.0.0.1:{port}/{index}" for index in range(articles)]
        extract_article(HTML, urls[0])  # Warm extraction caches before timing either mode.
        measurements: dict[int, list[float]] = {1: [], concurrency: []}
        with TemporaryDirectory(prefix="newspaper3kli-benchmark-") as directory:
            for sample in range(samples):
                for workers in (1, concurrency):
                    output = Path(directory) / f"{sample}-{workers}"
                    output.mkdir()
                    options = DownloadOptions(output, concurrency=workers, per_host=workers, retries=0)
                    started = perf_counter()
                    summary = await download_articles(urls, options)
                    measurements[workers].append(perf_counter() - started)
                    if summary.failed or summary.succeeded != articles:
                        raise RuntimeError("Benchmark did not save every article")
        sequential = median(measurements[1])
        concurrent = median(measurements[concurrency])
        return {
            "python": platform.python_version(),
            "articles": articles,
            "latency_seconds": latency,
            "concurrency": concurrency,
            "samples": samples,
            "sequential_seconds": round(sequential, 3),
            "concurrent_seconds": round(concurrent, 3),
            "speedup": round(sequential / concurrent, 2),
        }
    finally:
        await runner.cleanup()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--articles", type=int, default=24)
    parser.add_argument("--latency", type=float, default=0.05)
    parser.add_argument("--concurrency", type=int, default=8)
    parser.add_argument("--samples", type=int, default=3)
    args = parser.parse_args()
    if args.articles < 1 or args.latency < 0 or args.concurrency < 2 or args.samples < 1:
        parser.error("articles/samples must be positive, latency nonnegative, and concurrency at least 2")
    print(json.dumps(asyncio.run(benchmark(args.articles, args.latency, args.concurrency, args.samples)), indent=2))


if __name__ == "__main__":
    main()

"""Command parsing and process startup for newspaper3kli."""

import argparse
import asyncio
import logging
import math
import os
import sys
from collections.abc import Sequence
from pathlib import Path


class Arguments(argparse.Namespace):
    urls: list[str]
    output: Path | None
    verify_ssl: bool
    keep_html: bool
    concurrency: int
    per_host: int
    timeout: float
    retries: int
    no_nlp: bool


def positive_integer(value: str) -> int:
    number = int(value)
    if number <= 0:
        raise argparse.ArgumentTypeError("must be a positive integer")
    return number


def nonnegative_integer(value: str) -> int:
    number = int(value)
    if number < 0:
        raise argparse.ArgumentTypeError("must be zero or a positive integer")
    return number


def positive_timeout(value: str) -> float:
    number = float(value)
    if not math.isfinite(number) or number <= 0:
        raise argparse.ArgumentTypeError("must be a finite, positive number")
    return number


def parse_arguments(argv: Sequence[str] | None = None) -> Arguments:
    parser = argparse.ArgumentParser(prog="newspaper3kli")
    parser.add_argument("urls", nargs="*", help="URLs to download (reads standard input when omitted)")
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        help="Output directory (default: $XDG_DOWNLOAD_DIR/newspaper3k or ~/Downloads/newspaper3k)",
    )
    parser.add_argument(
        "-u",
        "--disable-verify-ssl",
        action="store_false",
        dest="verify_ssl",
        help="Disable SSL certificate verification.",
    )
    parser.add_argument("--keep-html", action="store_true", help="Save article content with HTML.")
    parser.add_argument("-j", "--concurrency", type=positive_integer, default=8, help="Concurrent workers (default: 8)")
    parser.add_argument("--per-host", type=positive_integer, default=2, help="Connections per host (default: 2)")
    parser.add_argument(
        "--timeout", type=positive_timeout, default=30.0, help="Request timeout in seconds (default: 30)"
    )
    parser.add_argument(
        "--retries", type=nonnegative_integer, default=2, help="Retries for transient errors (default: 2)"
    )
    parser.add_argument("--no-nlp", action="store_true", help="Skip keyword generation for faster extraction.")
    return parser.parse_args(argv, namespace=Arguments())


def main() -> int:
    args = parse_arguments()
    # Parsing --help should not import the HTTP client or extraction dependencies.
    from .downloads import DownloadOptions, download_articles

    urls = args.urls
    if not urls and not sys.stdin.isatty():
        urls = [line.strip() for line in sys.stdin if line.strip()]

    downloads_path = Path(os.environ.get("XDG_DOWNLOAD_DIR", Path.home() / "Downloads"))
    output_path = args.output if args.output else downloads_path / "newspaper3k"
    options = DownloadOptions(
        output_path=output_path,
        concurrency=args.concurrency,
        per_host=args.per_host,
        timeout=args.timeout,
        retries=args.retries,
        keep_html=args.keep_html,
        use_nlp=not args.no_nlp,
    )
    logging.basicConfig(format="%(levelname)s: %(message)s", level=logging.WARNING)
    try:
        output_path.mkdir(parents=True, exist_ok=True)
        summary = asyncio.run(download_articles(urls, options, verify_ssl=args.verify_ssl))
    except OSError as error:
        logging.getLogger(__name__).error("Cannot write output to %s: %s", output_path, error)
        return 1
    except KeyboardInterrupt:
        return 130
    return 1 if summary.failed else 0

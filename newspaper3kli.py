#!/usr/bin/env python3

import argparse
import asyncio
import itertools
import os
import sys

from lib.http_client import HttpClient


async def task(http_client, url):
    """
    Tiny asynchronous function to download content using http_client
    """
    http_client.get_text(url)


def parse_arguments():

    parser = argparse.ArgumentParser()

    parser.add_argument('urls',
                        nargs='*',
                        default=[],
                        help="URL to download content from (single download)")

    parser.add_argument('--url',
                        type=str,
                        default=None,
                        help="Enter the URLs to download content from.")

    parser.add_argument('-r', '--redirects',
                        action='store_true',
                        help="Flag to enable follow redirects in web pages.")

    parser.add_argument('-o', '--output',
                        type=str,
                        default=None,
                        help="Output path to store the results")

    parser.add_argument('-u', '--unverified',
                        action='store_false',
                        default=False,
                        help="Select to allow unverified SSL certificates.")

    parser.add_argument('-m', '--max_retries',
                        type=int,
                        default=0,
                        help=("Set the max number of retries (default 0 to fail"
                              " on first retry)."))

    parser.add_argument('-b', '--backoff',
                        type=float,
                        default=0,
                        help="Set the backoff factor (default 0).")

    return parser.parse_args()


def main():
    args = parse_arguments()
    urls = [line.replace("\r", "").replace("\n", "") for line in sys.stdin] \
        if not sys.stdin.isatty() \
        else args.urls

    output_path = (args.output or
                   os.path.join(os.path.dirname(os.path.realpath(__file__)),
                                "output"))

    loop = asyncio.get_event_loop()

    args = [(HttpClient(verify=not args.unverified,
                        follow_redirects=args.redirects,
                        output_path=output_path),
             url) for url in urls]

    tasks = itertools.starmap(task, args)
    loop.run_until_complete(asyncio.gather(*tasks))
    loop.close()


if __name__ == '__main__':
    main()

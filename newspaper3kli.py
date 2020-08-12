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

    parser.add_argument('-o', '--output',
                        type=str,
                        default=None,
                        help=('Output path to store the results.'
                              'Defaults to "Downloads" directory'))

    parser.add_argument('-u', '--disable-verify-ssl',
                        action='store_false',
                        help="Flag to disable SSL certificate verification.")

    parser.add_argument('--keep-html',
                        action='store_true',
                        help="Flag to save content with HTML.")

    return parser.parse_args()


def main():
    args = parse_arguments()
    urls = [line.replace("\r", "").replace("\n", "") for line in sys.stdin] \
        if not sys.stdin.isatty() \
        else args.urls

    output_path = (args.output or
                   # fallback to ${HOME}/Downloads whether using XDG or not
                   os.path.join(os.getenv("XDG_DOWNLOAD_DIR",
                                          os.path.join(os.getenv("HOME"),
                                                       "Downloads")),
                                "newspaper3k"))

    if not os.path.exists(output_path):
        os.makedirs(output_path)

    loop = asyncio.get_event_loop()

    args = [(HttpClient(verify=args.disable_verify_ssl,
                        keep_html=args.keep_html,
                        output_path=output_path),
             url) for url in urls]

    tasks = itertools.starmap(task, args)
    loop.run_until_complete(asyncio.gather(*tasks))
    loop.close()


if __name__ == '__main__':
    main()

# Newspaper3kli

Download articles from URL arguments or a Unix pipeline. Requires Python 3.15.2+.

## Install

```bash
python -m pip install newspaper3kli
newspaper3kli --help
```

To install this checkout, run `python -m pip install .`. The installed command is
`newspaper3kli`; `python -m newspaper3kli` provides the same interface.
Use a virtual environment to keep dependencies separate from system packages.
See [the pip installation guide](docs/pip-install.md) for setup, upgrades, and
installation from source (no Nix or uv required).

With Nix (flakes enabled), build and install the standalone CLI from this checkout:

```bash
nix run . -- --help
nix profile install .
newspaper3kli --help
```

Nix supplies Python and the dependencies from `uv.lock`; no system Python or
activated virtual environment is required. The profile exposes `newspaper3kli`.
See [the Nix installation guide](docs/nix-build.md) for setup and usage.

## Usage

```bash
newspaper3kli --output articles https://example.com/article
cat urls.txt | newspaper3kli --output articles --concurrency 8
```

Explicit URL arguments take precedence over piped input. Empty lines and duplicate
URLs are ignored.

| Option | Default | Purpose |
| --- | --- | --- |
| `-o`, `--output` | Downloads directory | Directory for saved articles |
| `-j`, `--concurrency` | `8` | Concurrent download/extraction workers |
| `--per-host` | `2` | Simultaneous connections per host |
| `--timeout` | `30` | Seconds per HTTP attempt |
| `--retries` | `2` | Retries for transient HTTP and connection failures |
| `--keep-html` | Off | Preserve extracted HTML instead of plain text |
| `--no-nlp` | Off | Skip generated keywords for faster processing |
| `-u`, `--disable-verify-ssl` | Off | Disable TLS certificate verification |

## Output

The default directory is `$XDG_DOWNLOAD_DIR/newspaper3k`, falling back to
`~/Downloads/newspaper3k`. Each article produces a UTF-8 pair:

- `<title>-<url-hash>.html`: extracted text, or HTML with `--keep-html`.
- `<title>-<url-hash>.json`: title, keywords, authors, image URLs, description,
  publication date, and source URL.

URL hashes prevent identical titles from overwriting each other. Responses are
limited to 10 MiB. No NLTK models or image downloads are required.

Exit codes: `0` for success, `1` if any article fails, `2` for invalid arguments,
and `130` when interrupted. Other articles continue after a failed URL.

## Credits

Built with [Newspaper4k](https://github.com/AndyTheFactory/newspaper4k) and
[aiohttp](https://docs.aiohttp.org/en/stable/). Originally inspired by
[dsynkov's newspaper-bulk](https://github.com/dsynkov/newspaper-bulk).

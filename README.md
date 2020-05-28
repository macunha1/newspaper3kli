# Newspaper3kli

_Newspaper3kli_ stands for the "kommand-line" interface over
[Newspaper3k](https://newspaper.readthedocs.io/en/latest/).

A tiny layer on top of Newspaper3k with support for Unix-like
executions and parallelism (using asyncio) to download bulks of
articles faster.

## Requirements

In addition to the requirements, make sure you have `nltk`'s
`punkt` package installed (via `nlkt.download()` in
interactive Python) for Newspaper3k's `article.nlp()` to work
properly.

## Installation

While the setupscript for setuptools isn't ready you can install it
manually using

```bash
# assuming your OS has pip3 as default
pip3 install -r requirements.txt
ln -s ${PWD}/newspaper3kli.py /usr/local/bin/newspaper3kli
# for the user path only (considering you already have it in $PATH)
ln -s ${PWD}/newspaper3kli.py ${HOME}/.local/bin/newspaper3kli
```

## Usage

Overview of available parameters

```
usage: newspaper3kli [-h] [--url URL] [-r] [-o OUTPUT] [-u] [-m MAX_RETRIES]
                     [-b BACKOFF]
                     [urls [urls ...]]

positional arguments:
  urls                  URL to download content from (single download)

optional arguments:
  -h, --help            show this help message and exit
  --url URL             Enter the URLs to download content from.
  -r, --redirects       Flag to enable follow redirects in web pages.
  -o OUTPUT, --output OUTPUT
                        Output path to store the results
  -u, --unverified      Select to allow unverified SSL certificates.
  -m MAX_RETRIES, --max_retries MAX_RETRIES
                        Set the max number of retries (default 0 to fail on
                        first retry).
  -b BACKOFF, --backoff BACKOFF
                        Set the backoff factor (default 0).
```

## Executing

### Passing URLs from the terminal

```bash
newspaper3kli https://hello.world/article/2020 \
    https://hello.world/article/2019
```

### Reading from a txt file

TXT is the simplest file format for reading with Newspaper3kli.

Assuming the txt file has the following content (line delimited URLs):

```
https://hello.world/article/2020
https://hello.world/article/2019
```

```bash
cat /path/to/this/file.txt | newspaper3kli
```

### Reading from a CSV file

CSV parsing will depend in a tool like `awk` or `cut` to split the columns.

Content sample

```csv
url,tags,date
https://hello.world/article/2020,some|thing,2020-01-01T00:00:00
https://hello.world/article/2019,some|thing,2019-01-01T00:00:00
```

Processing

```bash
# note that $1 corresponds to the URLs column number, change to yours
cat /path/to/this/file.csv | awk -F, 'NR==50{ print $1 }' | newspaper3kli
```

For any other character-delimited content, simple change from -F, (comma)
to the desired format, e.g.: -F\t for TSV

### Output path

When no path is specified through `--output` parameter, the default path is
`output` inside Newspaper3kli's directory. Files are created according to
Article's name, and are stored in pairs:

- JSON for metadata;
- HTML for content;

## Credits

Thanks to [dsynkov](https://github.com/dsynkov/) for the work at
[newspaper-bulk](https://github.com/dsynkov/newspaper-bulk). The source of
inspiration and some code for this project.

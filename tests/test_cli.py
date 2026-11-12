"""Exercise CLI inputs without network access or NLTK datasets."""

import io
import sys
from unittest.mock import AsyncMock

import pytest

from newspaper3kli import cli, downloads
from newspaper3kli.downloads import DownloadSummary


@pytest.fixture
def client(monkeypatch):
    downloader = AsyncMock(return_value=DownloadSummary())
    monkeypatch.setattr(downloads, "download_articles", downloader)
    return downloader


def test_positional_urls_take_precedence_over_stdin(monkeypatch, tmp_path, client):
    output = tmp_path / "articles"
    monkeypatch.setattr(
        sys, "argv", ["newspaper3kli", "-o", str(output), "https://example.com/one", "https://example.com/two"]
    )
    monkeypatch.setattr(sys, "stdin", io.StringIO("https://example.com/ignored\n"))

    assert cli.main() == 0

    urls, options = client.call_args.args
    assert urls == ["https://example.com/one", "https://example.com/two"]
    assert options.output_path == output
    assert options.keep_html is False
    assert client.call_args.kwargs == {"verify_ssl": True}
    assert output.is_dir()


def test_piped_urls_and_options(monkeypatch, tmp_path, client):
    monkeypatch.setattr(sys, "argv", ["newspaper3kli", "--output", str(tmp_path), "-u", "--keep-html"])
    monkeypatch.setattr(sys, "stdin", io.StringIO("https://example.com/one\r\n\n  \nhttps://example.com/two\n"))

    assert cli.main() == 0

    urls, options = client.call_args.args
    assert urls == ["https://example.com/one", "https://example.com/two"]
    assert options.output_path == tmp_path
    assert options.keep_html is True
    assert client.call_args.kwargs == {"verify_ssl": False}


@pytest.mark.parametrize("xdg_downloads", [None, "custom-downloads"])
def test_default_output_directory(monkeypatch, tmp_path, client, xdg_downloads):
    monkeypatch.setenv("HOME", str(tmp_path))
    if xdg_downloads is None:
        monkeypatch.delenv("XDG_DOWNLOAD_DIR", raising=False)
        downloads = tmp_path / "Downloads"
    else:
        downloads = tmp_path / xdg_downloads
        monkeypatch.setenv("XDG_DOWNLOAD_DIR", str(downloads))
    monkeypatch.setattr(sys, "argv", ["newspaper3kli"])
    monkeypatch.setattr(sys, "stdin", io.StringIO(""))

    assert cli.main() == 0

    assert (downloads / "newspaper3k").is_dir()
    assert client.call_args.args[0] == []
    assert client.call_args.args[1].output_path == downloads / "newspaper3k"


def test_terminal_without_urls_does_not_read_stdin(monkeypatch, tmp_path, client):
    class Terminal:
        def isatty(self):
            return True

    stdin = Terminal()
    monkeypatch.setattr(sys, "stdin", stdin)
    monkeypatch.setattr(sys, "argv", ["newspaper3kli", "-o", str(tmp_path)])

    assert cli.main() == 0

    assert client.call_args.args[0] == []


def test_main_can_be_called_twice(monkeypatch, tmp_path, client):
    monkeypatch.setattr(sys, "argv", ["newspaper3kli", "-o", str(tmp_path), "https://example.com/article"])

    assert cli.main() == 0
    assert cli.main() == 0
    assert client.await_count == 2


@pytest.mark.parametrize(
    "arguments",
    [
        ["--concurrency", "0"],
        ["--per-host", "-1"],
        ["--timeout", "nan"],
        ["--timeout", "inf"],
        ["--timeout", "0"],
        ["--retries", "-1"],
    ],
)
def test_rejects_invalid_limits(arguments):
    with pytest.raises(SystemExit) as error:
        cli.parse_arguments(arguments)
    assert error.value.code == 2


def test_download_controls():
    args = cli.parse_arguments(["-j", "12", "--per-host", "3", "--timeout", "5", "--retries", "0", "--no-nlp"])
    assert (args.concurrency, args.per_host, args.timeout, args.retries, args.no_nlp) == (12, 3, 5.0, 0, True)


def test_failed_download_returns_failure_status(monkeypatch, tmp_path, client):
    monkeypatch.setattr(sys, "argv", ["newspaper3kli", "-o", str(tmp_path), "https://example.com/missing"])
    client.return_value = DownloadSummary(failed=1)
    assert cli.main() == 1


def test_output_directory_failure(monkeypatch, tmp_path, client):
    output = tmp_path / "file"
    output.write_text("occupied")
    monkeypatch.setattr(sys, "argv", ["newspaper3kli", "-o", str(output)])
    monkeypatch.setattr(sys, "stdin", io.StringIO(""))
    assert cli.main() == 1
    client.assert_not_awaited()

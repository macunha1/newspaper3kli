"""Exercise real extraction, keyword generation and saved output."""

import json
from unittest.mock import Mock

import pytest

from newspaper3kli.articles import extract_article
from newspaper3kli.storage import save_article

from .conftest import ARTICLE_HTML, PARAGRAPH


@pytest.mark.parametrize("keep_html", [False, True])
@pytest.mark.parametrize("use_nlp", [False, True])
def test_extracts_and_saves_article(tmp_path, keep_html, use_nlp):
    article = extract_article(ARTICLE_HTML, "https://example.com/article", keep_html=keep_html, use_nlp=use_nlp)
    save_article(article, tmp_path)

    (content_path,) = tmp_path.glob("*.html")
    (metadata_path,) = tmp_path.glob("*.json")
    content = content_path.read_text(encoding="utf-8")
    assert PARAGRAPH.strip() in content
    assert ("<p>" in content) is keep_html
    metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    assert metadata["title"] == "Package news"
    assert metadata["authors"] == ["Jane Example"]
    assert metadata["description"] == "A packaging update"
    assert metadata["date"].startswith("2026-11-12T12:00:00")
    assert "https://example.com/image.jpg" in metadata["images"]
    assert metadata["url"] == "https://example.com/article"
    assert bool(metadata["keywords"]) is use_nlp
    assert set(metadata) == {"title", "keywords", "authors", "images", "description", "date", "url"}


def test_empty_article_is_an_error():
    with pytest.raises(ValueError, match="No article text"):
        extract_article("<html><body></body></html>", "https://example.com/empty")


def test_extraction_never_follows_meta_refresh(monkeypatch):
    from newspaper import network

    html = ARTICLE_HTML.replace(
        "<head>", '<head><meta http-equiv="refresh" content="0; url=https://example.com/other">'
    )
    fetch = Mock(side_effect=AssertionError("Extraction must not make HTTP requests"))
    monkeypatch.setattr(network, "get_html", fetch)
    article = extract_article(html, "https://example.com/article")
    assert article.metadata["title"] == "Package news"
    fetch.assert_not_called()


def test_same_titles_do_not_overwrite_each_other(tmp_path):
    for url in ["https://example.com/one", "https://example.com/two"]:
        save_article(extract_article(ARTICLE_HTML, url), tmp_path)
    assert len(list(tmp_path.glob("*.html"))) == 2
    assert len(list(tmp_path.glob("*.json"))) == 2


@pytest.mark.parametrize("title", ["", "../", "記事" * 200])
def test_filename_fallback_and_length(tmp_path, title):
    article = extract_article(ARTICLE_HTML, "https://example.com/article")
    article.metadata["title"] = title
    save_article(article, tmp_path)
    (path,) = tmp_path.glob("*.json")
    assert len(path.name.encode("utf-8")) <= 255
    assert json.loads(path.read_text())["title"] == title

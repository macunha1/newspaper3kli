"""Translate Newspaper4k extraction into the CLI's saved article format."""

import warnings
from dataclasses import dataclass
from typing import TypedDict

# Newspaper4k warns about its optional sentence tokenizer at import time. Our
# keyword-only NLP path uses its built-in tokenizer and never requests summaries.
with warnings.catch_warnings():
    warnings.filterwarnings(
        "ignore", message="nltk is not installed\\.", category=UserWarning, module="newspaper.parsers"
    )
    from newspaper import Article, Config
    from newspaper.article import ArticleException


class ArticleMetadata(TypedDict):
    title: str
    keywords: list[str]
    authors: list[str]
    images: list[str]
    description: str
    date: str | None
    url: str


@dataclass(frozen=True, slots=True)
class ExtractedArticle:
    content: str
    metadata: ArticleMetadata


def extract_article(html: str, url: str, *, keep_html: bool = False, use_nlp: bool = True) -> ExtractedArticle:
    config = Config()
    # Only the async HTTP client owns network access. Image URLs are still extracted.
    config.fetch_images = False
    config.follow_meta_refresh = False
    config.keep_article_html = keep_html
    # Summaries are not part of our output. Disabling them retains keyword extraction
    # and avoids NLTK, model downloads and unused sentence scoring.
    config.max_summary_sent = 0
    article = Article(url, config=config)
    try:
        article.download(input_html=html, ignore_read_more=True)
        article.parse()
    except ArticleException as error:
        raise ValueError(str(error)) from error
    if not article.text:
        raise ValueError("No article text could be extracted")
    if use_nlp:
        article.nlp()

    metadata: ArticleMetadata = {
        "title": article.title,
        "keywords": list(article.keywords),
        "authors": list(article.authors),
        "images": sorted(set(article.images) | ({article.meta_img} if article.meta_img else set())),
        "description": article.meta_description,
        "date": article.publish_date.isoformat() if article.publish_date else None,
        "url": url,
    }
    return ExtractedArticle(article.article_html if keep_html else article.text, metadata)

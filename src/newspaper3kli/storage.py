"""Write extracted content and metadata to an explicitly selected directory."""

import json
from hashlib import sha256
from pathlib import Path

from .articles import ExtractedArticle


def save_article(article: ExtractedArticle, output_path: Path) -> None:
    title = "".join(character for character in article.metadata["title"] if character.isalnum() or character == " ")
    title = title.strip().replace(" ", "-") or "article"
    # Keep filenames within common filesystem limits, including multibyte titles.
    title = title.encode("utf-8")[:160].decode("utf-8", errors="ignore")
    digest = sha256(article.metadata["url"].encode("utf-8")).hexdigest()[:12]
    stem = output_path / f"{title}-{digest}"
    Path(f"{stem}.html").write_text(article.content, encoding="utf-8")
    Path(f"{stem}.json").write_text(json.dumps(article.metadata, ensure_ascii=False), encoding="utf-8")

import json
import logging
import os
import requests

from newspaper import Article
from newspaper.article import ArticleException
from requests.exceptions import (ConnectionError,
                                 InvalidSchema,
                                 MissingSchema,
                                 TooManyRedirects,
                                 HTTPError)

logger = logging.getLogger(__name__)


class HttpClient:
    """Class responsible for the Http requests"""

    def __init__(self,
                 output_path: str,
                 verify: bool = True,
                 keep_html: bool = False):
        self.verify = verify

        self.keep_html = keep_html
        self.output_path = output_path

    def get_text(self, url):
        fake_user_agent = ("Mozilla/5.0 (Linux; U; Android 2.2) "
                           "AppleWebKit/533.1 (KHTML, like Gecko) "
                           "Version/4.0 Mobile Safari/533.1")

        try:
            # TODO: Include support for cookies (better scrapping)
            response = requests.get(url,
                                    verify=self.verify,
                                    headers={'User-Agent':
                                             fake_user_agent})

            response.raise_for_status()

            article = Article(url, keep_article_html=self.keep_html)
            article.download(input_html=response.text)

            article.parse()
            article.nlp()

            raw_path = self.build_filepath(title=article.title)

            with open("%s.html" % raw_path, "w") as htmldesc:
                htmldesc.write(article.article_html or article.text)

            with open("%s.json" % raw_path, "w") as metadata:
                json.dump({
                    'title': article.title,
                    'keywords': article.keywords,
                    'authors': article.authors,
                    'images': article.images,
                    'description': article.meta_description,
                    'date': article.publish_date.isoformat(),
                    'url': url
                }, metadata)

        except (ConnectionError,
                InvalidSchema,
                MissingSchema,
                HTTPError,
                TooManyRedirects,
                ArticleException) as e:
            logger.error("URL %s with error %s", url, str(e))

    def build_filepath(self, title):
        filename = "".join([c for c in title
                            if c.isalpha() or c.isdigit()
                            or c == ' ']) \
            .rstrip() \
            .replace(" ", "-")

        return os.path.join(self.output_path,
                            filename)

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
                                 RetryError)

logger = logging.getLogger(__name__)


class HttpClient:
    """Class responsible for the Http requests"""

    def __init__(self,
                 verify: bool,
                 follow_redirects: bool,
                 output_path: str):
        self.verify = verify
        self.follow_redirects = follow_redirects

        self.output_path = output_path

    def get_text(self, url):
        fake_user_agent = ("Mozilla/5.0 (Linux; U; Android 2.2) "
                           "AppleWebKit/533.1 (KHTML, like Gecko) "
                           "Version/4.0 Mobile Safari/533.1")

        try:
            response = requests.get(url,
                                    allow_redirects=self.follow_redirects,
                                    verify=self.verify,
                                    headers={'User-Agent':
                                             fake_user_agent})

            response.raise_for_status()

            article = Article(url, keep_article_html=True)
            article.download(input_html=response.text)

            article.parse()
            article.nlp()

            filename = "".join([c for c in article.title
                                if c.isalpha() or c.isdigit()
                                or c == ' ']) \
                .rstrip() \
                .replace(" ", "-")

            raw_path = os.path.join(self.output_path,
                                    filename)

            with open("%s.html" % raw_path, "w") as htmldesc:
                htmldesc.write(article.article_html)

            with open("%s.json" % raw_path, "w") as metadata:
                json.dump({
                    'title': article.title,
                    'keywords': article.keywords,
                    'url': url
                }, metadata)

        except (ConnectionError,
                InvalidSchema,
                MissingSchema,
                requests.exceptions.HTTPError,
                TooManyRedirects,
                ArticleException,
                RetryError) as e:
            logger.error("URL %s with error %s", url, str(e))

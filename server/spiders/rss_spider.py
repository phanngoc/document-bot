import scrapy
from scrapy.linkextractors import LinkExtractor
from bs4 import BeautifulSoup
import html2text
from urllib.parse import urlparse
import json
import csv
import html
import datetime
from elasticsearch import Elasticsearch
import feedparser
# Thêm thư viện để xử lý ngày tháng
from email.utils import parsedate_to_datetime
from typing import List, Dict
from elasticsearch_utils import index_documents_with_embeddings
from scrapy import Item, Field

# Get the current date and time
now = datetime.datetime.now()

class RssItem(Item):
    url = Field()
    title = Field()
    description = Field()
    pubDate = Field()

class RssSpider(scrapy.Spider):
    name = "rss_spider"
    folder_csv = "data_temp/rss_data/"
    def __init__(self, start_url=None, max_urls=500, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.start_urls = [start_url] if start_url else []
        self.allowed_domains = [urlparse(start_url).hostname] if start_url else []
        self.max_urls = max_urls
        self.crawled_urls = 0
        self.processed_links = set()  # Tập hợp để lưu trữ các liên kết đã xử lý

    def parse(self, response):
        if self.crawled_urls >= self.max_urls:
            return
        self.crawled_urls += 1

        feed = feedparser.parse(response.text)
        if feed.bozo == 0:  # Check if the feed is parsed correctly
            for entry in feed.entries:
                link = entry.link if 'link' in entry else 'No link'
                if link not in self.processed_links:
                    self.processed_links.add(link)
                    title = html.unescape(entry.title) if 'title' in entry else 'No title'
                    description = html.unescape(entry.description) if 'description' in entry else 'No description'
                    pub_date = entry.published if 'published' in entry else 'No pubDate'

                    yield RssItem(url=link, title=title, description=description, pubDate=pub_date)
                else:
                    continue

            return

        # Extract text content and convert to Markdown format
        soup = BeautifulSoup(response.text, 'html.parser')
        rss_links = soup.find_all('a', href=lambda href: href and '.rss' in href)
        for rss_link in rss_links:
            if rss_link:
                rss_url = rss_link.get('href')
                yield response.follow(rss_url, callback=self.parse)

    def closed(self, reason):
        self.logger.info(f'Spider closed: {reason}')


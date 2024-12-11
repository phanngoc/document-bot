import scrapy
from scrapy.linkextractors import LinkExtractor
from bs4 import BeautifulSoup
import sqlite3
import html2text
from urllib.parse import urlparse

class LinkSpider(scrapy.Spider):
    name = "link_spider"

    def __init__(self, start_url=None, assistant_id=None, max_urls=500, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.start_urls = [start_url] if start_url else []
        self.allowed_domains = [urlparse(start_url).hostname] if start_url else []
        self.assistant_id = assistant_id
        self.max_urls = max_urls
        self.crawled_urls = 0
        self.connection = sqlite3.connect('../chatbot.db')
        self.cursor = self.connection.cursor()

    def parse(self, response):
        if self.crawled_urls >= self.max_urls:
            return
        self.crawled_urls += 1

        # Check if the URL already exists in the database
        self.cursor.execute("SELECT 1 FROM pages WHERE url = ?", (response.url,))
        if self.cursor.fetchone():
            self.logger.info(f"URL already exists in the database: {response.url}")
            return

        # Extract text content and convert to Markdown format
        soup = BeautifulSoup(response.text, 'html.parser')
        article_content = soup.select_one('article.md-content__inner.md-typeset')
        if article_content:
            soup = article_content
        text_content = html2text.html2text(str(soup))
       
        print('parse:url:', response.url)
        # Save the current page's text content
        yield {
            'url': response.url,
            'text_content': text_content,
            'assistant_id': self.assistant_id  # Include the assistant_id
        }

        # Extract all links on the current page
        link_extractor = LinkExtractor()
        links = link_extractor.extract_links(response)
        
        # Follow each link and call the same parse method
        for link in links:
            yield response.follow(link.url, callback=self.parse)

    def closed(self, reason):
        self.connection.close()

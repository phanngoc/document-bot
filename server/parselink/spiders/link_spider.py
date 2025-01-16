import scrapy
from scrapy.linkextractors import LinkExtractor
from bs4 import BeautifulSoup
import sqlite3
import html2text
from urllib.parse import urlparse
import json

from model import Assistant

class LinkSpider(scrapy.Spider):
    name = "link_spider"

    def __init__(self, start_url=None, assistant_id=None, max_urls=500, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.start_urls = [start_url] if start_url else []
        self.allowed_domains = [urlparse(start_url).hostname] if start_url else []
        self.assistant_id = assistant_id
        assistant = Assistant.get(Assistant.id == assistant_id)
        self.css_selector = assistant.css_selector
        self.max_urls = max_urls
        self.crawled_urls = 0
        self.connection = sqlite3.connect("../chatbot.db")
        self.cursor = self.connection.cursor()

        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS pages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            url TEXT UNIQUE,
            text_content JSON,
            assistant_id INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (assistant_id) REFERENCES assistants(id)
            )
        ''')
        self.cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_url ON pages (url)
        ''')

        self.connection.commit()

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

        try:
            template_data = json.loads(self.css_selector)
        except json.JSONDecodeError as e:
            self.logger.error(f"Error decoding JSON from css_selector: {e}")
            return

        content_insert = {}
        # Loop through key-value pairs in the template data
        for key, value in template_data.items():
            if soup.select_one(value['css_selector']):
                content_insert[key] = soup.select_one(value['css_selector']).get_text()
        # text_content = html2text.html2text(str(soup))
       
        print('parse:url:', response.url)
        # Save the current page's text content

        text_content_json = json.dumps(content_insert)
        self.cursor.execute('''
            INSERT OR REPLACE INTO pages (url, text_content, assistant_id, created_at) VALUES (?, ?, ?, CURRENT_TIMESTAMP)
        ''', (response.url, text_content_json, self.assistant_id))
        self.connection.commit()

        yield {
            'url': response.url,
            'text_content': content_insert,
            'assistant_id': self.assistant_id  # Include the assistant_id
        }

        # Extract all links on the current page
        link_extractor = LinkExtractor()
        links = link_extractor.extract_links(response)
        
        # Follow each link and call the same parse method
        for link in links:
            yield response.follow(link.url, callback=self.parse)

    def closed(self, reason):
        print('closed:reason:', reason)
        assistant = Assistant.get(Assistant.id == self.assistant_id)
        assistant.is_crawled = True
        assistant.save()
        self.connection.close()
